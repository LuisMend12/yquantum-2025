import numpy as np
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Statevector, Pauli

def quantum_hash_iterative_v5(input_bytes):
    """
    A purely quantum hash function processing input in 20-bit chunks using Statevector.
    Input: an array of 2^N bytes (N >= 5).
    Output: 32 bytes (256 bits).
    Uses 20 qubits.
    """
    input_bits = np.unpackbits(np.frombuffer(input_bytes, dtype=np.uint8))
    padding_needed = 20 - (len(input_bits) % 20) if len(input_bits) % 20 != 0 else 0
    input_bits = np.pad(input_bits, (0, padding_needed), 'constant')

    n_qubits = 20
    qr = QuantumRegister(n_qubits, 'q')

    current_state = Statevector.from_int(0, dims=2**n_qubits) # Start with |0...0>

    num_steps = 64 # Number of steps in the quantum operation per block

    for i in range(0, len(input_bits), 20):
        chunk = input_bits[i:i+20]

        qc_block = QuantumCircuit(qr)

        # Encode input bits as rotations (Ry by pi if bit is 1)
        for j in range(20):
            if chunk[j]:
                qc_block.ry(np.pi, qr[j])

        # Perform a quantum operation
        for _ in range(num_steps):
            for j in range(n_qubits):
                qc_block.h(qr[j])
            for j in range(0, n_qubits - 1, 2):
                qc_block.cx(qr[j], qr[j+1])
            for j in range(1, n_qubits - 1, 2):
                qc_block.cx(qr[j], qr[j+1])
            if n_qubits > 1:
                qc_block.cx(qr[n_qubits - 1], qr[0]) # Wrap around

        current_state = current_state.evolve(qc_block)

    # After processing all blocks, get expectation values
    expectation_values = []
    for i in range(n_qubits):
        expectation_values.append(current_state.expectation_value(Pauli("X", i)).real)
        expectation_values.append(current_state.expectation_value(Pauli("Y", i)).real)
        expectation_values.append(current_state.expectation_value(Pauli("Z", i)).real)

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
    input_data_n5 = b'This is a test input of 32 bytes for N=5'
    output_hash_n5 = quantum_hash_iterative_v5(input_data_n5)
    print(f"Input (N=5, {len(input_data_n5)} bytes): {input_data_n5}")
    print(f"Output (N=5, {len(output_hash_n5)} bytes): {output_hash_n5.hex()}")

    input_data_n6 = b'This is a longer test input of 64 bytes for N=6' * 2
    output_hash_n6 = quantum_hash_iterative_v5(input_data_n6)
    print(f"Input (N=6, {len(input_data_n6)} bytes): {input_data_n6}")
    print(f"Output (N=6, {len(output_hash_n6)} bytes): {output_hash_n6.hex()}")
