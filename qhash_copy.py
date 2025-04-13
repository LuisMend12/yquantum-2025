from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Pauli
from qiskit_aer import Aer
import math
import numpy as np

TOTAL_QUBITS = 20
COIN_QUBITS = list(range(4))
POSITION_QUBITS = list(range(4, 20))

def expectation_to_byte(exp_val):
    """Convert expectation value [-1, 1] to byte [0, 255]."""
    return int((exp_val + 1) / 2 * 255)

def quantum_hash(input_data):
    """Quantum hash function using expectations from quantum statevector."""
    # Ensure input_data is in byte array format
    if not isinstance(input_data, bytearray):
        raise ValueError("Input must be a byte array")

    # Convert byte array to binary string
    binary_input = ''.join(format(byte, '08b') for byte in input_data)

    # Pad binary input if needed (ensure it's multiple of 2)
    if len(binary_input) % 2 != 0:
        binary_input += '0'

    # Build the quantum circuit
    qc = QuantumCircuit(TOTAL_QUBITS)
    chunks = [binary_input[i:i+2] for i in range(0, len(binary_input), 2)]

    for chunk in chunks:
        for j, bit in enumerate(chunk):
            idx = j % len(COIN_QUBITS)
            if bit == '1':
                qc.h(COIN_QUBITS[idx])
            else:
                qc.rx(math.pi / 2, COIN_QUBITS[idx])

        for c in COIN_QUBITS:
            for p in POSITION_QUBITS:
                qc.cx(c, p)

    # Global mixing
    for i in range(TOTAL_QUBITS):
        qc.ry(math.pi / 4, i)
    for i in range(TOTAL_QUBITS - 1):
        qc.cx(i, i + 1)
    for i in range(TOTAL_QUBITS):
        qc.h(i)

    # Simulate and get statevector
    backend = Aer.get_backend('statevector_simulator')
    result = backend.run(qc).result()
    state = result.get_statevector()

    # Collect expectation values for Z and X operators
    hash_bytes = bytearray()
    for i in range(TOTAL_QUBITS):
        z_op = Pauli('I' * i + 'Z' + 'I' * (TOTAL_QUBITS - i - 1))
        z_val = state.expectation_value(z_op).real
        hash_bytes.append(expectation_to_byte(z_val))

        x_op = Pauli('I' * i + 'X' + 'I' * (TOTAL_QUBITS - i - 1))
        x_val = state.expectation_value(x_op).real
        hash_bytes.append(expectation_to_byte(x_val))

    return bytes(hash_bytes[:len(input_data)])  # Output matches input size
  # Output fixed at 256 bits (32 bytes)

  # Output matches input size
  # Fixed 256-bit hash


if __name__ == "__main__":
    print("===== Quantum Hash Generator (Expectation-based) =====")
    
    # Example input (array of bytes)
    input_data = bytearray([i % 256 for i in range(32)]) 



    try:
        result = quantum_hash(input_data)
        print(f"\nQuantum Hash (hex): {result.hex()}")
        print(f"Raw Bytes: {result}")
    except Exception as e:
        print(f"\nError: {e}")
