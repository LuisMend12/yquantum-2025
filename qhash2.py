import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, transpile
from qiskit.providers.basic_provider import BasicSimulator

def quantum_hash_iterative_v3(input_bytes):
    """
    A purely quantum hash function processing input in 20-bit chunks.
    Input: an array of 2^N bytes (N >= 5).
    Output: 32 bytes (256 bits).
    Uses 20 qubits.
    """
    input_bits = np.unpackbits(np.frombuffer(input_bytes, dtype=np.uint8))
    padding_needed = 20 - (len(input_bits) % 20) if len(input_bits) % 20 != 0 else 0
    input_bits = np.pad(input_bits, (0, padding_needed), 'constant')

    n_qubits = 20
    qr = QuantumRegister(n_qubits, 'q')
    qc = QuantumCircuit(qr)

    simulator = BasicSimulator()
    current_state = None # To carry state over

    num_steps = 64 # Number of steps in the quantum operation per block

    for i in range(0, len(input_bits), 20):
        chunk = input_bits[i:i+20]
        
        if current_state is not None:
            qc.initialize(current_state, qr)
        else:
            qc.reset(qr)

        # Encode input bits as rotations (Ry by pi if bit is 1)
        for j in range(20):
            if chunk[j]:
                qc.ry(np.pi, qr[j])

        # Perform a quantum operation
        for _ in range(num_steps):
            for j in range(n_qubits):
                qc.h(qr[j])
            for j in range(0, n_qubits - 1, 2):
                qc.cx(qr[j], qr[j+1])
            for j in range(1, n_qubits - 1, 2):
                qc.cx(qr[j], qr[j+1])
            if n_qubits > 1:
                qc.cx(qr[n_qubits - 1], qr[0]) # Wrap around

        # Get the statevector to carry over
        compiled_circuit = transpile(qc, simulator)
        job = simulator.run(compiled_circuit).result()
        current_state = job.get_statevector(qc).data
        
        qc.data.clear() # Clear quantum circuit for next chunk

    # After processing all blocks, get expectation values
    expectation_values = []
    for i in range(n_qubits):
        exp_x = job.get_expectation_value(qc, [["x", i]])
        exp_y = job.get_expectation_value(qc, [["y", i]])
        exp_z = job.get_expectation_value(qc, [["z", i]])
        expectation_values.extend([exp_x, exp_y, exp_z])

    # Quantize to 5 bits and concatenate
    output_bits = []
    for value in expectation_values:
        quantized_value = round((value + 1) * 31 / 2)
        binary = format(int(quantized_value), '05b')
        output_bits.extend([int(b) for b in binary])

    # Take the first 256 bits and convert to bytes
    output_bytes = bytearray()
    for i in range(0, 256, 8):
        byte_value = 0
        for j in range(8):
            if i + j < len(output_bits):
                if output_bits[i + j] == 1:
                    byte_value |= (1 << (7 - j))
        output_bytes.append(byte_value)

    return bytes(output_bytes)

if __name__ == '__main__':
    input_data_1 = b'This is a test input.' * 2
    hash_result_1 = quantum_hash_iterative_v3(input_data_1)
    print(f"Input 1: {input_data_1}")
    print(f"Hash 1: {hash_result_1.hex()}")

    input_data_2 = b'This is a slightly different input.' * 2
    hash_result_2 = quantum_hash_iterative_v3(input_data_2)
    print(f"Input 2: {input_data_2}")
    print(f"Hash 2: {hash_result_2.hex()}")
