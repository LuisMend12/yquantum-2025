import math
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Pauli

# Constants to define the number of qubits and steps for the quantum walk
NUM_POSITION_QUBITS = 4  # Number of position qubits for 16 possible positions
TOTAL_QUBITS = NUM_POSITION_QUBITS + 1  # Total qubits, including the coin qubit

# Preprocess input data to match the expected size of the hash output
def preprocess_input(data: bytearray, size: int = 32) -> bytearray:
    """
    Ensures the input data is of the required size.
    If too long, reduce by XORing bytes. If too short, pad with zeros.
    """
    if len(data) > size:
        reduced = bytearray(size)
        for i in range(len(data)):
            reduced[i % size] ^= data[i]
        return reduced
    return data.ljust(size, b'\x00')  # Pad with zeros if data is shorter than size

# Main quantum walk-based hash function
def qhash_quantum_walk(input_data: bytearray) -> bytes:
    """
    Performs a quantum walk to generate a hash from the input data.
    Initializes a quantum circuit, simulates the quantum walk,
    and collects the expectation values to form the final hash.
    """
    original_size = len(input_data)
    data = preprocess_input(input_data)

    NUM_WALK_STEPS = len(data) * 2  # Double the walk steps for better avalanche effect

    # Initialize quantum circuit with total qubits (coin + position)
    qc = QuantumCircuit(TOTAL_QUBITS)
    coin = 0  # Coin qubit (used for flipping)
    pos_qubits = list(range(1, TOTAL_QUBITS))  # Position qubits (1 to TOTAL_QUBITS-1)

    # Start the walker at the center position
    qc.x(pos_qubits[len(pos_qubits) // 2])

    # Quantum walk steps
    for step in range(NUM_WALK_STEPS):
        byte_val = data[step % len(data)]  # Loop over the data for longer walks
        theta = (byte_val / 255.0) * 2 * math.pi  # Map byte value to [0, 2π] for RY rotation
        qc.ry(theta, coin)  # Apply RY rotation based on byte value

        # Apply controlled-X gates to entangle position and coin
        for i in reversed(pos_qubits):
            qc.cx(coin, i)

    # Simulate the quantum circuit to obtain the state vector
    sv = Statevector.from_instruction(qc)

    # Collect expectation values from position qubits for Z and X bases
    hash_bytes = bytearray()
    for i in pos_qubits:
        # Expectation values for Pauli operators
        z_op = Pauli("I" * i + "Z" + "I" * (TOTAL_QUBITS - i - 1))
        x_op = Pauli("I" * i + "X" + "I" * (TOTAL_QUBITS - i - 1))

        # Calculate expectation values
        z_val = sv.expectation_value(z_op).real
        x_val = sv.expectation_value(x_op).real

        # Convert to byte representation
        hash_bytes.append(int((z_val + 1) / 2 * 255))
        hash_bytes.append(int((x_val + 1) / 2 * 255))

    # Trim hash to match the original size
    return bytes(hash_bytes[:original_size])

# Testing the optimized function
if __name__ == "__main__":
    test_inputs = [
        bytearray([1, 2, 3, 4, 5, 8, 10, 12]),  # Example input 1
        bytearray([1, 2, 3, 4, 5, 7]),  # Example input 2 (small change for avalanche effect)
    ]

    print("\n--- Testing Optimized qhash_quantum_walk ---")
    for input_data in test_inputs:
        try:
            # Perform the quantum walk hash on the input data
            result = qhash_quantum_walk(input_data)
            print(f"\nProcessing input: {list(input_data)} (size: {len(input_data)} bytes)")
            print(f"qhash Result (hex): {result.hex()} (size: {len(result)} bytes)")

            # Basic avalanche effect test
            modified = bytearray(input_data)  # Modify the input to test avalanche effect
            modified[0] ^= 1  # Flip the first bit
            result2 = qhash_quantum_walk(modified)  # Hash the modified input
            diff_count = sum([1 for a, b in zip(result, result2) if a != b])  # Count differing bytes

            if diff_count > len(result) // 2:  # Ensure enough bytes changed
                print("Avalanche effect observed.")
            else:
                print("No avalanche effect detected.")
        except Exception as e:
            print(f"Error: {e}")
