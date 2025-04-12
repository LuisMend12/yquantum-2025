from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import hashlib

TOTAL_QUBITS = 20
COIN_QUBITS = list(range(4))  # 4 qubits for coin toss
POSITION_QUBITS = list(range(4, 16))  # 12 qubits for position
ANCILLA_QUBITS = list(range(16, 20))  # 4 qubits for ancillas

def initialize_circuit():
    """Initializes a quantum circuit with the required number of qubits."""
    qc = QuantumCircuit(TOTAL_QUBITS, TOTAL_QUBITS)
    return qc

def apply_coin_operator(qc, bit_chunk):
    """Applies quantum gates to the coin qubits based on the input chunk."""
    for i, bit in enumerate(bit_chunk):
        idx = i % len(COIN_QUBITS)
        if bit == '1':
            qc.h(COIN_QUBITS[idx])  # Hadamard gate
        elif bit == '0':
            qc.rx(1.57, COIN_QUBITS[idx])  # Rotation gate for bit '0'
        else:
            # For any unexpected characters, apply identity gate
            qc.id(COIN_QUBITS[idx])

def apply_position_shift_operator(qc):
    """Applies controlled operations to shift the position qubits."""
    # Entangle coin qubits with position qubits more efficiently
    for i, c in enumerate(COIN_QUBITS):
        # Each coin qubit controls a subset of position qubits
        target_qubits = POSITION_QUBITS[i::4]
        for p in target_qubits:
            qc.cx(c, p)
    
    # Apply controlled rotations to create diffusion
    for i in range(len(POSITION_QUBITS) - 2):
        qc.ccx(POSITION_QUBITS[i], POSITION_QUBITS[i + 1], POSITION_QUBITS[i + 2])
    
    # Add some phase kicks to increase complexity
    for i, qubit in enumerate(POSITION_QUBITS):
        if i % 3 == 0:
            qc.t(qubit)
        elif i % 3 == 1:
            qc.s(qubit)

def run_quantum_hash(input_string, chunk_size=8, shots=1024):
    """Executes the quantum hash function and returns the measured output."""
    # Ensure input is binary
    if not all(bit in '01' for bit in input_string):
        raise ValueError("Input must contain only '0' and '1' characters")
    
    qc = initialize_circuit()
    
    # Process input in chunks
    chunks = [input_string[i:i + chunk_size] for i in range(0, len(input_string), chunk_size)]
    
    # Apply operations for each chunk of the input string
    for chunk in chunks:
        apply_coin_operator(qc, chunk)
        apply_position_shift_operator(qc)
    
    # Add a final mixing layer
    for i in range(TOTAL_QUBITS):
        qc.h(i)
    
    # Measure all qubits
    qc.measure(range(TOTAL_QUBITS), range(TOTAL_QUBITS))
    
    # Run the circuit on the simulator using the updated API
    simulator = AerSimulator()
    result = simulator.run(qc, shots=shots).result()
    counts = result.get_counts()
    
    # Get the most frequent outcome
    measured = max(counts.items(), key=lambda x: x[1])[0]
    
    return measured

def reduce_to_64bit(measured_output):
    """Reduces the measured quantum output to a 64-bit hash using SHA-256."""
    digest = hashlib.sha256(measured_output.encode()).hexdigest()
    return digest[:16]  # Taking the first 16 characters (64 bits)

def quantum_hash(input_data, output_size=16):
    """Complete quantum hash function that takes any string input and returns a hash."""
    # Convert input to binary representation if it's not already
    if not all(bit in '01' for bit in input_data):
        binary_input = ''.join(format(ord(char), '08b') for char in input_data)
    else:
        binary_input = input_data
    
    # Ensure we have enough data to process (pad if necessary)
    if len(binary_input) < 64:
        binary_input = binary_input.ljust(64, '0')
    
    # Run the quantum circuit
    quantum_raw = run_quantum_hash(binary_input)
    
    # Process the output to get the final hash
    final_hash = reduce_to_64bit(quantum_raw)
    return final_hash[:output_size]  # Allow flexible hash size

# Example usage
if __name__ == "__main__":
    # Test with binary input
    binary_data = '1010101111001101110010110011001111000011110011001100110011001111001100111100'
    hash_result = quantum_hash(binary_data)
    print(f"Input: {binary_data[:20]}... (length: {len(binary_data)})")
    print(f"Quantum Hash: {hash_result}")
    
    # Test with text input
    text_data = "Hello, quantum world!"
    hash_result = quantum_hash(text_data)
    print(f"Input: '{text_data}'")
    print(f"Quantum Hash: {hash_result}")