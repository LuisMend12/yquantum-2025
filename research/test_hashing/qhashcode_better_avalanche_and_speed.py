import math
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import Statevector
from qiskit.quantum_info.operators import Pauli

NUM_QUBITS = 16 # Increased number of qubits
NUM_LAYERS = 8

# build the parameterized quantum circuit.
qc_param = QuantumCircuit(NUM_QUBITS)
params = []
for l in range(NUM_LAYERS):
    # add parameterized RY rotation gates
    for i in range(NUM_QUBITS):
        theta = Parameter(f"theta_ry_{l}_{i}")
        params.append(theta)
        qc_param.ry(theta, i)
    # add parameterized RZ rotation gates (Corrected from RX to RZ)
    for i in range(NUM_QUBITS):
        theta = Parameter(f"theta_rz_{l}_{i}")
        params.append(theta)
        qc_param.rz(theta, i)
    # add parameterized RX rotation gates
    for i in range(NUM_QUBITS):
        theta = Parameter(f"theta_rx_{l}_{i}")
        params.append(theta)
        qc_param.rx(theta, i)
    # add CNOT entangling gates (Ring topology)
    for i in range(NUM_QUBITS):
        qc_param.cx(i, (i + 1) % NUM_QUBITS)
    # add input-dependent CZ gates
    global processed_input # Expecting this to be set in qhash function
    if 'processed_input' in globals():
        for i in range(NUM_QUBITS):
            input_bit_index = (l * NUM_QUBITS + i) % 256 # Assuming 32 bytes (256 bits) of processed input
            byte_index = input_bit_index // 8
            bit_in_byte = input_bit_index % 8
            if byte_index < len(processed_input) and ((processed_input[byte_index] >> bit_in_byte) & 1):
                qc_param.cz(i, (i + 1) % NUM_QUBITS)

num_params = len(params)

def preprocess_input(data: bytes) -> bytes:
    target_size = 32
    input_size = len(data)
    if input_size == target_size:
        return data
    elif input_size < target_size:
        padding_size = target_size - input_size
        padding = bytearray([0] * (padding_size - 2))
        padding.extend(input_size.to_bytes(2, byteorder='big')) # Encode original length in last 2 bytes
        return data + bytes(padding)
    else: # input_size > target_size
        # Simple reduction: XOR all 32-byte chunks
        reduced_data = bytearray([0] * target_size)
        for i in range(0, input_size, target_size):
            chunk = data[i:i+target_size]
            chunk_bytes = bytearray(chunk)
            if len(chunk_bytes) < target_size:
                chunk_bytes.extend([0] * (target_size - len(chunk_bytes)))
            for j in range(target_size):
                reduced_data[j] ^= chunk_bytes[j]
        return bytes(reduced_data)

# Quantum simulation portion of the qhash
# x - byte array
# returns the hash value as a byte array with the same size as input
def qhash_variable_output_v7(x: bytes) -> bytes:
    original_input_size = len(x)
    global processed_input
    processed_input = preprocess_input(x)

    # create a dictionary mapping each parameter to its value.
    param_values = {}
    param_index = 0
    for l in range(NUM_LAYERS):
        for i in range(NUM_QUBITS):
            # RY parameter
            byte_index = param_index // 2 % len(processed_input)
            bit_index = (param_index % 2) * 4
            nibble = (processed_input[byte_index] >> bit_index) & 0x0F
            value = nibble * math.pi / 8
            param_values[params[param_index]] = value
            param_index += 1
        for i in range(NUM_QUBITS):
            # RZ parameter
            byte_index = param_index // 2 % len(processed_input)
            bit_index = (param_index % 2) * 4
            nibble = (processed_input[byte_index] >> bit_index) & 0x0F
            value = nibble * math.pi / 8
            param_values[params[param_index]] = value
            param_index += 1
        for i in range(NUM_QUBITS):
            # RX parameter
            byte_index = param_index // 2 % len(processed_input)
            bit_index = (param_index % 2) * 4
            nibble = (processed_input[byte_index] >> bit_index) & 0x0F
            value = nibble * math.pi / 8
            param_values[params[param_index]] = value
            param_index += 1

    # bind the parameters to the circuit.
    bound_qc = qc_param.assign_parameters(param_values)

    # prepare the state vector from the bound circuit
    sv = Statevector.from_instruction(bound_qc)
    # calculate the qubit expectations on the Z and X axes
    expectation_bytes = bytearray()
    for i in range(NUM_QUBITS):
        z_op = Pauli("I" * i + "Z" + "I" * (NUM_QUBITS - i - 1))
        z_val = sv.expectation_value(z_op).real
        expectation_bytes.append(int((z_val + 1) / 2 * 255))

        x_op = Pauli("I" * i + "X" + "I" * (NUM_QUBITS - i - 1))
        x_val = sv.expectation_value(x_op).real
        expectation_bytes.append(int((x_val + 1) / 2 * 255))

    # Resize the output to match the original input size using repetition or truncation
    output = bytearray()
    if len(expectation_bytes) >= original_input_size:
        output = expectation_bytes[:original_input_size]
    else:
        num_repeats = math.ceil(original_input_size / len(expectation_bytes))
        for _ in range(num_repeats):
            output.extend(expectation_bytes)
        output = output[:original_input_size]

    return bytes(output)

# Simple command-line interface
if __name__ == "__main__":
    print("===== Quantum Hash Generator (Variable Output Size - v8) =====")

    test_inputs_bytearray = [ bytearray([0, 0, 1, 0, 0, 0]), bytearray([1, 1, 1, 1, 1, 1]) ]

    print("\n--- Testing qhash_variable_output_v7 (16 Qubits, 8 Layers, Z and X Expectation, Ring Entanglement, Input-Dependent CZs) ---")
    for input_data_bytes in test_inputs_bytearray:
        print(f"\nProcessing input: {list(input_data_bytes)} (size: {len(input_data_bytes)} bytes)")
        try:
            hash_result = qhash_variable_output_v7(input_data_bytes)
            print(f"qhash Result (hex): {hash_result.hex()} (size: {len(hash_result)} bytes)")
            print(f"Output size matches input size: {len(hash_result)} == {len(input_data_bytes)}")

            # Test avalanche effect (very basic)
            if len(input_data_bytes) > 0:
                input_modified = bytearray(input_data_bytes)
                input_modified[0] = input_modified[0] ^ 1
                hash_result_modified = qhash_variable_output_v7(bytes(input_modified))
                if hash_result != hash_result_modified:
                    print("Avalanche effect observed (first byte changed, hashes differ).")
                else:
                    print("No avalanche effect observed (first byte changed, hashes are the same).")
            else:
                print("Cannot test avalanche on empty input.")

        except Exception as e:
            print(f"Error in qhash: {e}")


if __name__ == "__main__":
    test_inputs = [
            bytearray([1, 2, 3, 4, 5, 8]),
            bytearray([5, 6, 7, 8, 9, 10]),
            bytearray([10, 20, 30, 40, 50, 60]),
            bytearray([255, 255, 255, 255, 255, 255]),
            bytearray([1, 1, 1, 1, 1, 1, 1, 1]),
            bytearray([255] * 16),
            bytearray([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]),
            bytearray(b'\x01\x02\x03\x04\x05\x08'), #[1, 2, 3, 4, 5, 8]
            bytearray(b'\x00\x02\x03\x04\x05\x08') #[0, 2, 3, 4, 5, 8]
    ]

    print("\n--- Testing Optimized qhash_quantum_walk ---")
    for input_data in test_inputs:
        try:
            # Perform the quantum walk hash on the input data
            result = qhash_variable_output_v7(input_data)
            print(f"\nProcessing input: {list(input_data)} (size: {len(input_data)} bytes)")
            print(f"qhash Result (hex): {result.hex()} (size: {len(result)} bytes)")

            
        except Exception as e:
            print(f"Error: {e}")