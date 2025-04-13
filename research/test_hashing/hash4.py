import math
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import Statevector
from qiskit.quantum_info.operators import Pauli

NUM_QUBITS = 4
NUM_LAYERS = 8
CHUNK_SIZE = 32

# Build parameterized quantum circuit
qc_param = QuantumCircuit(NUM_QUBITS)
params = []
for l in range(NUM_LAYERS):
    for i in range(NUM_QUBITS):
        theta = Parameter(f"theta_ry_{l}_{i}")
        params.append(theta)
        qc_param.ry(theta, i)
    for i in range(NUM_QUBITS):
        theta = Parameter(f"theta_rz_{l}_{i}")
        params.append(theta)
        qc_param.rz(theta, i)
    for i in range(NUM_QUBITS):
        theta = Parameter(f"theta_rx_{l}_{i}")
        params.append(theta)
        qc_param.rx(theta, i)
    for i in range(NUM_QUBITS):
        qc_param.cx(i, (i + 1) % NUM_QUBITS)
    global processed_input
    if 'processed_input' in globals():
        for i in range(NUM_QUBITS):
            input_bit_index = (l * NUM_QUBITS + i) % (len(processed_input) * 8)
            byte_index = input_bit_index // 8
            bit_in_byte = input_bit_index % 8
            if byte_index < len(processed_input) and ((processed_input[byte_index] >> bit_in_byte) & 1):
                qc_param.cz(i, (i + 1) % NUM_QUBITS)

num_params = len(params)

def preprocess_input(data: bytes) -> bytes:
    target_size = CHUNK_SIZE
    input_size = len(data)
    if input_size == target_size:
        return data
    elif input_size < target_size:
        padding_size = target_size - input_size
        padding = bytearray([0] * (padding_size - 2))
        padding.extend(input_size.to_bytes(2, byteorder='big'))
        return data + bytes(padding)
    else:
        # Quantum-inspired input compression
        sliced = data[:target_size]
        feedback = bytearray()
        for i in range(target_size):
            j = (i * 17) % len(data)
            feedback.append(sliced[i] ^ data[j])
        return bytes(feedback)

def quantum_process_chunk(chunk: bytes, prev_hash: bytes = None) -> bytes:
    global processed_input
    if prev_hash is not None:
        mixed_chunk = bytearray()
        min_len = min(len(chunk), len(prev_hash))
        for i in range(min_len):
            mixed_chunk.append(chunk[i] ^ prev_hash[i])
        if len(chunk) > min_len:
            mixed_chunk.extend(chunk[min_len:])
        elif len(prev_hash) > min_len:
            mixed_chunk.extend(prev_hash[min_len:])
        processed_input = bytes(mixed_chunk)
    else:
        processed_input = chunk

    param_values = {}
    param_index = 0

    for l in range(NUM_LAYERS):
        for i in range(NUM_QUBITS):
            byte1 = processed_input[(param_index + i) % len(processed_input)]
            byte2 = processed_input[(param_index + i + NUM_QUBITS) % len(processed_input)]
            value = ((byte1 << 8) + byte2) * math.pi / 65536
            param_values[params[param_index]] = value
            param_index += 1

        for i in range(NUM_QUBITS):
            byte1 = processed_input[(param_index + i * 2) % len(processed_input)]
            byte2 = processed_input[(param_index + i * 2 + 1) % len(processed_input)]
            value = ((byte1 << 4) + byte2) * math.pi / 4096
            param_values[params[param_index]] = value
            param_index += 1

        for i in range(NUM_QUBITS):
            byte1 = processed_input[(param_index + i * 3) % len(processed_input)]
            byte2 = processed_input[(param_index + i * 3 + 1) % len(processed_input)]
            byte3 = processed_input[(param_index + i * 3 + 2) % len(processed_input)]
            value = ((byte1 + byte2 + byte3) % 256) * math.pi / 256
            param_values[params[param_index]] = value
            param_index += 1

    bound_qc = qc_param.assign_parameters(param_values)
    sv = Statevector.from_instruction(bound_qc)

    expectation_bytes = bytearray()
    for i in range(NUM_QUBITS):
        for axis in "ZXY":
            op = Pauli("I" * i + axis + "I" * (NUM_QUBITS - i - 1))
            val = sv.expectation_value(op).real
            expectation_bytes.append(int((val + 1) / 2 * 255))

    return bytes(expectation_bytes)

def qhash_variable_output_v8(x: bytes) -> bytes:
    original_input_size = len(x)
    if len(x) <= CHUNK_SIZE:
        hash_result = quantum_process_chunk(preprocess_input(x))
    else:
        chunks = [x[i:i+CHUNK_SIZE] for i in range(0, len(x), CHUNK_SIZE)]
        current_hash = None
        for i, chunk in enumerate(chunks):
            processed_chunk = preprocess_input(chunk)
            if i % 2 == 1:
                processed_chunk = processed_chunk[::-1]
            current_hash = quantum_process_chunk(processed_chunk, current_hash)
        hash_result = current_hash

    output = bytearray()
    if len(hash_result) >= original_input_size:
        output = hash_result[:original_input_size]
    else:
        expanded = bytearray(hash_result)
        while len(expanded) < original_input_size:
            feedback = bytearray()
            for i in range(len(expanded)):
                j = (i * 13) % len(expanded)
                feedback.append(expanded[i] ^ expanded[j])
            expanded.extend(feedback)
        output = expanded[:original_input_size]

    return bytes(output)

# Testing
if __name__ == "__main__":
    print("===== Quantum Hash Generator (Variable Output Size - v8, No SHA) =====")

    test_inputs = [
        bytearray([1, 2, 3, 4, 5, 8]),
        bytearray([5, 6, 7, 8, 9, 10]),
        bytearray([10, 20, 30, 40, 50, 60]),
        bytearray([255, 255, 255, 255, 255, 255]),
        bytearray([1, 1, 1, 1, 1, 1, 1, 1]),
        bytearray([255] * 16),
        bytearray([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]),
        bytearray(b'\x01\x02\x03\x04\x05\x08'),
        bytearray(b'\x00\x02\x03\x04\x05\x08')
    ]

    for input_data in test_inputs:
        print(f"\nInput: {input_data[:20]}... (size: {len(input_data)} bytes)")
        try:
            hash_result = qhash_variable_output_v8(input_data)
            print(f"Hash (hex): {hash_result.hex()}")
            print(f"Output size: {len(hash_result)} bytes (matches input)")

            if len(input_data) > 1:
                reversed_input = input_data[::-1]
                reversed_hash = qhash_variable_output_v8(reversed_input)
                if hash_result == reversed_hash:
                    print("Warning: Symmetric input produced identical output!")
                else:
                    print("Symmetric input test passed (different outputs)")

            if len(input_data) > 0:
                modified_input = bytearray(input_data)
                modified_input[0] ^= 1
                modified_hash = qhash_variable_output_v8(bytes(modified_input))
                diff_bits = sum(bin(a ^ b).count('1') for a, b in zip(hash_result, modified_hash))
                diff_percentage = diff_bits / (len(hash_result) * 8) * 100
                print(f"Avalanche effect: {diff_percentage:.1f}% bits changed")
        except Exception as e:
            print(f"Error: {e}")
