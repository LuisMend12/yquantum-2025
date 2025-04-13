from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Pauli
from qiskit_aer import Aer
import math
import numpy as np

from prev_work.qhash import quantum_hash

TOTAL_QUBITS = 20
COIN_QUBITS = list(range(4))
POSITION_QUBITS = list(range(4, 20))

def expectation_to_byte(exp_val):
    # Expectation is in [-1, 1], convert to [0, 255]
    return int((exp_val + 1) / 2 * 255)

def quantum_hash_with_expectations(input_data):
    """
    Improved quantum hash using expectation values instead of probabilities.
    """
    # Convert to binary string if needed
    if not all(bit in '01' for bit in input_data):
        binary_input = ''.join(format(ord(char), '08b') for char in input_data)
    else:
        binary_input = input_data

    # Pad if too short
    if len(binary_input) < len(COIN_QUBITS) * 2:
        binary_input = binary_input.ljust(len(COIN_QUBITS) * 2, '0')

    # Build the quantum circuit
    qc = QuantumCircuit(TOTAL_QUBITS)
    chunks = [binary_input[i:i+2] for i in range(0, len(binary_input), 2)]

    # Step 1: Encode input using coin qubits
    for i, chunk in enumerate(chunks):
        for j, bit in enumerate(chunk):
            idx = j % len(COIN_QUBITS)
            if bit == '1':
                qc.h(COIN_QUBITS[idx])
            else:
                qc.rx(math.pi / 2, COIN_QUBITS[idx])
        for c in COIN_QUBITS:
            for p in POSITION_QUBITS:
                qc.cx(c, p)

    # Step 2: Global mixing
    for i in range(TOTAL_QUBITS):
        qc.ry(math.pi / 4, i)
    for i in range(TOTAL_QUBITS - 1):
        qc.cx(i, i + 1)
    for i in range(TOTAL_QUBITS):
        qc.h(i)

    # Step 3: Simulate
    backend = Aer.get_backend('statevector_simulator')
    result = backend.run(qc).result()
    state = result.get_statevector()

    # Step 4: Compute expectations for Z and X
    hash_bytes = bytearray()
    for i in range(TOTAL_QUBITS):
        # Z expectation
        z_op = Pauli('I' * i + 'Z' + 'I' * (TOTAL_QUBITS - i - 1))
        z_val = state.expectation_value(z_op).real
        hash_bytes.append(expectation_to_byte(z_val))
        
        # X expectation
        x_op = Pauli('I' * i + 'X' + 'I' * (TOTAL_QUBITS - i - 1))
        x_val = state.expectation_value(x_op).real
        hash_bytes.append(expectation_to_byte(x_val))

    # Step 5: Return 256-bit (32-byte) hash
    return bytes(hash_bytes[:32])




# Simple command-line interface
if __name__ == "__main__":
    try:
        print("===== Quantum Hash Generator =====")
        print("Enter text or binary data to hash (binary must contain only 0s and 1s):")

        input_data = input("> ")
        print("\nProcessing input...")

        try:
            hash_result = quantum_hash(input_data)
            print(f"\nQuantum Hash Result: {hash_result}")
        except Exception as e:
            print(f"\nError generating hash: {e}")

    except Exception as e:
        print(f"Program error: {e}")