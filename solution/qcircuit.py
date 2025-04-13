from qiskit import QuantumCircuit
from main import NUM_WALK_STEPS, TOTAL_QUBITS, preprocess_input
import math
from qiskit.quantum_info import Statevector


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
    print(qc)


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
            result = qhash_quantum_walk(input_data)
        except Exception as e:
            print(f"Error: {e}")
