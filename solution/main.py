import math
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Pauli


NUM_POSITION_QUBITS = 4  # for 16 positions
NUM_WALK_STEPS = 64 #gotta check this
TOTAL_QUBITS = NUM_POSITION_QUBITS + 1  # +1 coin qubit


def preprocess_input(data: bytearray, size: int = 32) -> bytearray:
    if len(data) > size:
        reduced = bytearray(size)
        for i in range(len(data)):
            reduced[i % size] ^= data[i]
        return reduced
    elif len(data) < size:
        return data + bytearray([0] * (size - len(data)))
    return data


def qhash_quantum_walk(input_data: bytearray) -> bytes:
    original_size = len(input_data)
    data = preprocess_input(input_data)

    qc = QuantumCircuit(TOTAL_QUBITS)
    coin = 0
    pos_qubits = list(range(1, TOTAL_QUBITS))

    # Start walker roughly centered
    center = len(pos_qubits) // 2
    qc.x(pos_qubits[center])

    for step in range(NUM_WALK_STEPS):
        byte_val = sum([data[(step + i) % len(data)] for i in range(4)]) % 256
        theta = (byte_val % 256) * math.pi / 128  # in [0, 2π]
        qc.ry(theta, coin)

        for i in reversed(range(len(pos_qubits))):
            qc.cx(coin, pos_qubits[i])

    sv = Statevector.from_instruction(qc)

    # Collect expectations
    hash_bytes = bytearray()
    for i in pos_qubits:
        z_op = Pauli("I" * i + "Z" + "I" * (TOTAL_QUBITS - i - 1))
        x_op = Pauli("I" * i + "X" + "I" * (TOTAL_QUBITS - i - 1))

        z_val = sv.expectation_value(z_op).real
        x_val = sv.expectation_value(x_op).real

        hash_bytes.append(int((z_val + 1) / 2 * 255))
        hash_bytes.append(int((x_val + 1) / 2 * 255))

    while len(hash_bytes) < original_size:
        hash_bytes.extend(hash_bytes)

    return bytes(hash_bytes[:original_size])
# Testing the optimized function

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
            result = qhash_quantum_walk(input_data)
            print(f"\nProcessing input: {list(input_data)} (size: {len(input_data)} bytes)")
            print(f"qhash Result (hex): {result.hex()} (size: {len(result)} bytes)")

            
        except Exception as e:
            print(f"Error: {e}")
