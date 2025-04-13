import math
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import Statevector
from qiskit.quantum_info.operators import Pauli
from qiskit_aer import Aer
import numpy as np



TOTAL_QUBITS = 20
COIN_QUBITS = list(range(4))        # 4 qubits for coin control
POSITION_QUBITS = list(range(4, 20))  # 16 qubits for entangled positions

def quantum_hash(input_data):
    """
    Quantum hash function with 20 qubits. No classical hash. Pure quantum logic.
    """
    # Step 1: Convert to binary if input is text
    if not all(bit in '01' for bit in input_data):
        print(f"Converting text to binary...")
        binary_input = ''.join(format(ord(char), '08b') for char in input_dataa)
        print(f"Binary representation: {binary_input}")
    else:
        binary_input = input_data

    if len(binary_input) < len(COIN_QUBITS) * 2:
        binary_input = binary_input.ljust(len(COIN_QUBITS) * 2, '0')

    print(f"Processing {len(binary_input)} bits...")

    # Step 2: Build the circuit
    qc = QuantumCircuit(TOTAL_QUBITS)
    chunks = [binary_input[i:i+2] for i in range(0, len(binary_input), 2)]

    # Step 3: Apply input-driven gates
    for i, chunk in enumerate(chunks):
        for j, bit in enumerate(chunk):
            idx = j % len(COIN_QUBITS)
            if bit == '1':
                qc.h(COIN_QUBITS[idx])
            else:
                qc.rx(math.pi / 2, COIN_QUBITS[idx])
        # Entangle coin qubits with position qubits
        for c in COIN_QUBITS:
            for p in POSITION_QUBITS:
                qc.cx(c, p)

    # Step 4: Mixing layer
    for i in range(TOTAL_QUBITS):
        qc.ry(math.pi / 4, i)
    for i in range(TOTAL_QUBITS - 1):
        qc.cx(i, i + 1)

    # Step 5: Final Hadamard layer
    for i in range(TOTAL_QUBITS):
        qc.h(i)

    # Step 6: Simulate and extract statevector
    backend = Aer.get_backend('statevector_simulator')
    result = backend.run(qc).result()
    state = result.get_statevector()
    probabilities = np.abs(state) ** 2

    # Step 7: Extract top state indices and map to hex
    top_indices = np.argsort(probabilities)[-8:]
    hex_digest = ''.join(format(idx ^ int(probabilities[idx] * 1000), '04x') for idx in top_indices)

    # Step 8: Truncate to 16 characters
    return hex_digest[:16]




NUM_QUBITS = 16
NUM_LAYERS = 2

# build the parameterized quantum circuit.
qc = QuantumCircuit(NUM_QUBITS)
params = []
for l in range(NUM_LAYERS):
    # add parameterized RY rotation gates
    for i in range(NUM_QUBITS):
        theta = Parameter(f"theta_ry_{l}_{i}")
        params.append(theta)
        qc.ry(theta, i)
    # add parameterized RX rotation gates
    for i in range(NUM_QUBITS):
        theta = Parameter(f"theta_rz_{l}_{i}")
        params.append(theta)
        qc.rz(theta, i)
    # add CNOT entangling gates
    for i in range(NUM_QUBITS - 1):
        qc.cx(i, i + 1)
num_params = len(params)

# Quantum simulation portion of the qhash
# x - 256-bit byte array
# returns the hash value as a 256-bit byte array
def qhash(x: bytes) -> bytes:
    # create a dictionary mapping each parameter to its value.
    param_values = {}
    for i in range(num_params):
        # extract a nibble (4 bits) from the hash
        nibble = (x[i // 2] >> (4 * (1 - (i % 2)))) & 0x0F
        # scale it to use as a rotation angle parameter
        value = nibble * math.pi / 8
        param_values[params[i]] = value

    # bind the parameters to the circuit.
    bound_qc = qc.assign_parameters(param_values)

    # prepare the state vector from the bound circuit
    sv = Statevector.from_instruction(bound_qc)
    # calculate the qubit expectations on the Z axis
    exps = [sv.expectation_value(Pauli("Z"), [i]).real for i in range(NUM_QUBITS)]
    # convert the expectations to the fixed-point values
    fixed_exps = [toFixed(exp) for exp in exps]

    # pack the fixed-point results into a byte list.
    data = []
    for fixed in fixed_exps:
        for i in range(TOTAL_BITS // 8):
            data.append((fixed >> (8 * i)) & 0xFF)

    return bytes(data)
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