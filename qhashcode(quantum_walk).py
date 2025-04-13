import math
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Pauli


NUM_POSITION_QUBITS = 4  # for 16 positions
NUM_WALK_STEPS = 6
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
        byte_val = data[step % len(data)]
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


# === CLI Test ===
if __name__ == "__main__":
    test_inputs = [
        bytearray([1, 2, 3, 4, 5, 8]),
        bytearray([1, 2, 3, 4, 5, 7]),  # Small change to check avalanche
    ]

    print("\n--- Testing qhash_quantum_walk ---")
    for input_data in test_inputs:
        try:
            result = qhash_quantum_walk(input_data)
            print(f"\nProcessing input: {list(input_data)} (size: {len(input_data)} bytes)")
            print(f"qhash Result (hex): {result.hex()} (size: {len(result)} bytes)")

            # Basic avalanche test
            modified = bytearray(input_data)
            modified[0] ^= 1
            result2 = qhash_quantum_walk(modified)
            if result != result2:
                print("Avalanche effect observed.")
            else:
                print("No avalanche effect detected.")
        except Exception as e:
            print(f"Error: {e}")
