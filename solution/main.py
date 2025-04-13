import math
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Pauli

# Constants to define the number of qubits and steps for the quantum walk
NUM_POSITION_QUBITS = 4  # Number of position qubits for 16 possible positions
NUM_WALK_STEPS = 6  # Number of steps the quantum walker takes
TOTAL_QUBITS = NUM_POSITION_QUBITS + 1  # Total qubits, including the coin qubit

# Preprocess input data to match the expected size of the hash output
def preprocess_input(data: bytearray, size: int = 32) -> bytearray:
    """
    This function ensures the input data is of the required size.
    - If the input data is longer than the specified size, it reduces the size
      by performing an XOR operation on each byte.
    - If the input data is shorter than the specified size, it pads the data with
      zero bytes.
    """
    if len(data) > size:
        reduced = bytearray(size)
        # XOR each byte of the input with the reduced array size
        for i in range(len(data)):
            reduced[i % size] ^= data[i]
        return reduced
    elif len(data) < size:
        # Pad the input with zeros if it's too short
        return data + bytearray([0] * (size - len(data)))
    return data  # Return the data as is if it's already the correct size

# Main quantum walk-based hash function
def qhash_quantum_walk(input_data: bytearray) -> bytes:
    """
    This function performs a quantum walk to generate a hash from the input data.
    It initializes a quantum circuit with position and coin qubits, simulates the quantum walk,
    and collects the expectation values to form the final hash.
    """
    original_size = len(input_data)  # Store the original size of the input data
    data = preprocess_input(input_data)  # Preprocess the input to ensure correct size

    # Initialize the quantum circuit with the total number of qubits (position + coin qubit)
    qc = QuantumCircuit(TOTAL_QUBITS)
    coin = 0  # Coin qubit (used for flipping)
    pos_qubits = list(range(1, TOTAL_QUBITS))  # Position qubits (1 to TOTAL_QUBITS-1)

    # Start the quantum walker roughly centered by applying an X-gate on the center qubit
    center = len(pos_qubits) // 2
    qc.x(pos_qubits[center])  # Set the walker at the center position initially

    # Iterate over the quantum walk steps
    for step in range(NUM_WALK_STEPS):
        byte_val = data[step % len(data)]  # Get the current byte from the input data
        theta = (byte_val / 255.0) * 2 * math.pi #theta = (byte_val % 256) * math.pi / 128  # Map byte value to [0, 2π] for the RY rotation
        qc.ry(theta, coin)  # Apply an RY rotation on the coin qubit based on the byte value

        # Apply controlled-X gates to move the quantum walker (entangle position and coin)
        for i in reversed(range(len(pos_qubits))):
            qc.cx(coin, pos_qubits[i])  # Perform a controlled-X operation

    # Simulate the quantum circuit to obtain the state vector
    sv = Statevector.from_instruction(qc)

    # Collect the expectation values from the position qubits for both Z and X bases
    hash_bytes = bytearray()  # To store the resulting hash
    for i in pos_qubits:
        # Pauli-Z operator for the position qubit
        z_op = Pauli("I" * i + "Z" + "I" * (TOTAL_QUBITS - i - 1))
        # Pauli-X operator for the position qubit
        x_op = Pauli("I" * i + "X" + "I" * (TOTAL_QUBITS - i - 1))

        # Compute the expectation values for the Z and X operations on the position qubit
        z_val = sv.expectation_value(z_op).real  # Expectation value for the Z operator
        x_val = sv.expectation_value(x_op).real  # Expectation value for the X operator

        # Convert the expectation values to integers in the range [0, 255] for byte representation
        hash_bytes.append(int((z_val + 1) / 2 * 255))
        hash_bytes.append(int((x_val + 1) / 2 * 255))

    # Ensure the hash is at least the size of the original input
    while len(hash_bytes) < original_size:
        hash_bytes.extend(hash_bytes)  # Repeat the hash bytes to match the original size

    # Return the final hash, truncated to match the input size
    return bytes(hash_bytes[:original_size])


# if __name__ == "__main__":
#     test_inputs = [
#         bytearray([1, 2, 3, 4, 5, 8]),  # Example input 1
#         bytearray([1, 2, 3, 4, 5, 7]),  # Example input 2 (with a small change to check avalanche effect)
#     ]

#     print("\n--- Testing qhash_quantum_walk ---")
#     for input_data in test_inputs:
#         try:
#             # Perform the quantum walk hash on the input data
#             result = qhash_quantum_walk(input_data)
#             print(f"\nProcessing input: {list(input_data)} (size: {len(input_data)} bytes)")
#             print(f"qhash Result (hex): {result.hex()} (size: {len(result)} bytes)")

#             # Basic avalanche effect test
#             modified = bytearray(input_data)  # Modify the input to test avalanche effect
#             modified[0] ^= 1  # Flip the first bit
#             result2 = qhash_quantum_walk(modified)  # Hash the modified input
#             if result != result2:  # If the hashes are different, avalanche effect is observed
#                 print("Avalanche effect observed.")
#             else:
#                 print("No avalanche effect detected.")
#         except Exception as e:
#             print(f"Error: {e}")
