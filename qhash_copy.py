from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Pauli
from qiskit_aer import Aer
import math

TOTAL_QUBITS = 20
COIN_QUBITS = list(range(4))
POSITION_QUBITS = list(range(4, 20))

def expectation_to_byte(exp_val):
    """Convert expectation value [-1, 1] to byte [0, 255]."""
    return int((exp_val + 1) / 2 * 255)

def adjust_to_power_of_two_bytes(byte_array, min_power=5):
    """
    Adjusts a byte array to have length 2^N (N >= min_power).
    Pads with zeros or trims as necessary.
    """
    length = len(byte_array)
    target_power = max(min_power, math.ceil(math.log2(length)))
    target_length = 2 ** target_power

    if length < target_length:
        padded = byte_array + bytes(target_length - length)
    else:
        padded = byte_array[:target_length]

    return padded

def quantum_hash(input_bytes):
    """Quantum hash function using expectations from quantum statevector."""
    if not isinstance(input_bytes, (bytes, bytearray)):
        raise TypeError("Input must be a byte array.")

    # Ensure input length is 2^N (N ≥ 5)
    input_bytes = adjust_to_power_of_two_bytes(input_bytes)

    # Build the quantum circuit
    qc = QuantumCircuit(TOTAL_QUBITS)

    for byte in input_bytes:
        bits = format(byte, '08b')
        chunks = [bits[i:i+2] for i in range(0, 8, 2)]

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

    # Collect expectation values
    hash_bytes = bytearray()
    for i in range(TOTAL_QUBITS):
        z_op = Pauli('I' * i + 'Z' + 'I' * (TOTAL_QUBITS - i - 1))
        z_val = state.expectation_value(z_op).real
        hash_bytes.append(expectation_to_byte(z_val))

        x_op = Pauli('I' * i + 'X' + 'I' * (TOTAL_QUBITS - i - 1))
        x_val = state.expectation_value(x_op).real
        hash_bytes.append(expectation_to_byte(x_val))

    return bytes(hash_bytes[:32])  # Fixed 256-bit hash


if __name__ == "__main__":
    print("===== Quantum Hash Generator (Expectation-based) =====")

    try:
        hex_input = input("Enter hex-encoded byte string (e.g., 'a1b2c3'): \n> ")
        input_bytes = bytes.fromhex(hex_input)
        result = quantum_hash(input_bytes)

        print(f"\nQuantum Hash (hex): {result.hex()}")
        print(f"Raw Bytes: {result}")
    except Exception as e:
        print(f"\nError: {e}")
