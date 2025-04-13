import random
import matplotlib.pyplot as plt
from collections import defaultdict
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Pauli

from main import qhash_quantum_walk

# Use the existing qhash_quantum_walk function

def find_probability_distribution(num_bits: int = 3, num_simulations: int = 1024):
    # Generate all possible 3-bit inputs (0 to 7)
    inputs = []
    for _ in range(num_simulations):
        L = list(range(num_bits))
        n = random.randint(0, 64)
        inputs.append(bytearray([l + n for l in L]))
    
    # Dictionary to count occurrences of hash results (using defaultdict to avoid KeyError)
    hash_counts = defaultdict(int)

    # Run simulations for each input and count the hash results
    for input_data in inputs:
        for _ in range(num_simulations):
            result = qhash_quantum_walk(input_data)
            hash_counts[result.hex()] += 1  # Store hash result in hexadecimal format

    # Calculate probability distribution
    total_counts = sum(hash_counts.values())
    probability_distribution = {key: count / total_counts for key, count in hash_counts.items()}
    print(probability_distribution)

    return probability_distribution

if __name__ == "__main__":
    probability_distribution = find_probability_distribution(num_bits=10, num_simulations=30)

    # Collect hashes and probabilities for plotting
    hashes = list(probability_distribution.keys())
    probabilities = list(probability_distribution.values())

    # Plotting the bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(hashes, probabilities)
    plt.xticks(rotation=90, fontsize=8)  # Rotate the x-axis labels to fit
    plt.ylabel("Probability")
    plt.title("Hash Probabilities")
    plt.tight_layout()
    plt.show()
