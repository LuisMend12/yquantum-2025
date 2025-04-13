from qiskit import QuantumCircuit
from qiskit.quantum_info import Pauli, Statevector
import numpy as np

def simple_quantum_hash(input_bytes: bytes):
    num_qubits = len(input_bytes)
    qc = QuantumCircuit(num_qubits)
    for i in range(num_qubits):
        angle = (input_bytes[i] / 255) * np.pi  # scale to [0, π]
        qc.ry(angle, i)

    sv = Statevector.from_instruction(qc)
    exp_vals = [sv.expectation_value(Pauli("Z"), [i]).real for i in range(num_qubits)]

    # Map each expectation value from [-1, 1] to an 8-bit integer in [0, 255].
    output_bytes = bytearray([min(int(((val + 1) / 2) * 256), 255) for val in exp_vals])

    return bytes(output_bytes)

if __name__ == '__main__':
    input_data_n5 = b'This is a test input of 32 bytes for N=5'
    output_hash_n5 = simple_quantum_hash(input_data_n5)
    print(f"Input (N=5, {len(input_data_n5)} bytes): {input_data_n5}")
    print(f"Output (N=5, {len(output_hash_n5)} bytes): {output_hash_n5.hex()}")

    input_data_n6 = b'This is a longer test input of 64 bytes for N=6' * 2
    output_hash_n6 = simple_quantum_hash(input_data_n6)
    print(f"Input (N=6, {len(input_data_n6)} bytes): {input_data_n6}")
    print(f"Output (N=6, {len(output_hash_n6)} bytes): {output_hash_n6.hex()}")
