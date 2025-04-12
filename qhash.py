from qiskit import QuantumCircuit
from qiskit_aer import Aer
import hashlib
import numpy as np

# Define qubit allocations - reduced for simplicity
TOTAL_QUBITS = 8
COIN_QUBITS = list(range(2))  # 2 qubits for coin toss
POSITION_QUBITS = list(range(2, 8))  # 6 qubits for position

def quantum_hash(input_data):
    """
    Quantum hash function that automatically converts text to binary.
    Works with both text strings and binary strings as input.
    
    Args:
        input_data (str): Either text or binary string to hash
        
    Returns:
        str: 16-character (64-bit) hash value
    """
    # Step 1: Convert to binary if input is text
    if not all(bit in '01' for bit in input_data):
        print(f"Converting text to binary...")
        binary_input = ''.join(format(ord(char), '08b') for char in input_data)
        print(f"Binary representation: {binary_input}")
    else:
        binary_input = input_data
    
    # Step 2: Ensure we have enough data
    if len(binary_input) < 8:
        binary_input = binary_input.ljust(8, '0')
    
    print(f"Processing {len(binary_input)} bits of binary data...")
    
    # Step 3: Initialize quantum circuit
    qc = QuantumCircuit(TOTAL_QUBITS)
    
    # Step 4: Process input in chunks
    chunks = [binary_input[i:i+2] for i in range(0, min(len(binary_input), 16), 2)]
    
    # Step 5: Apply quantum operations
    for chunk in chunks:
        # Apply coin operator
        for i, bit in enumerate(chunk):
            idx = i % len(COIN_QUBITS)
            if bit == '1':
                qc.h(COIN_QUBITS[idx])  # Hadamard gate
            elif bit == '0':
                qc.rx(1.57, COIN_QUBITS[idx])  # Rotation gate
        
        # Apply position shift operator
        for c in COIN_QUBITS:
            for p in POSITION_QUBITS:
                qc.cx(c, p)
    
    # Step 6: Add final mixing layer
    for i in range(TOTAL_QUBITS):
        qc.h(i)
    
    # Step 7: Get statevector from the quantum circuit
    print("Calculating quantum state...")
    backend = Aer.get_backend('statevector_simulator')
    job = backend.run(qc)
    result = job.result()
    statevector = result.get_statevector()
    
    # Step 8: Create deterministic output from quantum state
    probabilities = np.abs(statevector) ** 2
    top_indices = np.argsort(probabilities)[-8:]
    output_string = ''.join([format(idx, '08b') for idx in top_indices])
    
    # Step 9: Generate final hash using SHA-256
    print("Generating final hash...")
    final_hash = hashlib.sha256(output_string.encode()).hexdigest()[:16]
    
    return final_hash

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