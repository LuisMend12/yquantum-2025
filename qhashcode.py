import math
import hashlib
import struct
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import Statevector
from qiskit.quantum_info.operators import Pauli

NUM_QUBITS = 16
NUM_LAYERS = 8
qc_param = QuantumCircuit(NUM_QUBITS)
params = []

# Build parameterized quantum circuit with layer-dependent entanglement
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
        qc_param.cx(i, (i + l + 1) % NUM_QUBITS)  # Layer-dependent entanglement

num_params = len(params)

def preprocess_input(data: bytes) -> bytes:
    target_size = 32
    input_size = len(data)
    if input_size == target_size:
        return data
    elif input_size < target_size:
        padding_size = target_size - input_size
        padding = bytearray([0] * (padding_size - 2))
        padding.extend(input_size.to_bytes(2, byteorder='big'))
        return data + bytes(padding)
    else:
        reduced_data = bytearray([0] * target_size)
        for i in range(0, input_size, target_size):
            chunk = data[i:i + target_size]
            chunk_bytes = bytearray(chunk)
            if len(chunk_bytes) < target_size:
                chunk_bytes.extend([0] * (target_size - len(chunk_bytes)))
            for j in range(target_size):
                reduced_data[j] ^= chunk_bytes[j]
        return bytes(reduced_data)

def qhash_variable_output_optimized(x: bytes) -> bytes:
    original_input_size = len(x)
    processed_input = preprocess_input(x)
    nibbles = np.array([(b >> 4, b & 0x0F) for b in processed_input]).flatten()
    nibbles = np.resize(nibbles, num_params)
    
    # Optional: Add random phase offset based on input
    seed = int.from_bytes(hashlib.md5(x).digest(), 'big') % (2**32)
    np.random.seed(seed)
    offsets = np.random.uniform(0, math.pi / 4, size=num_params)
    angles = (nibbles * math.pi / 8 + offsets) % (2 * math.pi)

    param_values = dict(zip(params, angles))
    bound_qc = qc_param.assign_parameters(param_values)
    sv = Statevector.from_instruction(bound_qc)

    expectation_bytes = bytearray()
    for i in range(NUM_QUBITS):
        for axis in "ZXY":
            op = Pauli("I" * i + axis + "I" * (NUM_QUBITS - i - 1))
            val = sv.expectation_value(op).real
            expectation_bytes.append(int((val + 1) / 2 * 255))

    # Optional: Add pairwise ZZ expectation values
    for i in range(0, NUM_QUBITS - 1, 2):
        zz_op = Pauli("I" * i + "ZZ" + "I" * (NUM_QUBITS - i - 2))
        zz_val = sv.expectation_value(zz_op).real
        expectation_bytes.append(int((zz_val + 1) / 2 * 255))

    # Postprocessing with SHA-256 for stronger avalanche
    digest = hashlib.sha256(expectation_bytes).digest()
    if original_input_size <= 32:
        return digest[:original_input_size]
    else:
        repeats = math.ceil(original_input_size / 32)
        extended = (digest * repeats)[:original_input_size]
        return extended

# Simple CLI test harness
if __name__ == "__main__":
    print("===== Optimized Quantum Hash Generator =====")

    test_inputs = [
        bytearray([0, 0, 0, 0, 0, 0]),
        bytearray([1, 1, 1, 1, 1, 1]),
        bytearray([255, 255, 255, 255, 255, 255])
    ]

    for input_data in test_inputs:
        print(f"\nInput: {list(input_data)}")
        result = qhash_variable_output_optimized(input_data)
        print(f"Hash (hex): {result.hex()} | Size: {len(result)}")

        # Avalanche test
        if input_data:
            modified = bytearray(input_data)
            modified[0] ^= 1
            modified_result = qhash_variable_output_optimized(modified)
            print("Avalanche effect observed:" if result != modified_result else "No avalanche detected.")
