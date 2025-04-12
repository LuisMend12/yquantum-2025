import hashlib
import math
from socket import PACKET_MULTICAST
from matplotlib import rc_params
import param
from qiskit.quantum_info import Statevector

from qhash import NUM_QUBITS, TOTAL_BITS, toFixed

def preprocess_input(x: bytes) -> bytes:
    return hashlib.sha256(x).digest()


def postprocess_output(raw_dat: bytes) -> bytes:
    return hashlib.sha256(raw_dat).digest()

def quantum_hash(x: bytes) -> bytes:
    # Step 1: Classical pre-hash (handles variable-length input)
    digest = preprocess_input(x)

    # Step 2: Map nibbles to quantum rotation angles
    param_values = {}
    for i in range(rc_params):
        nibble = (digest[i // 2] >> (4 * (1 - (i % 2)))) & 0x0F
        angle = nibble * math.pi / 8  # full 0 to 2π coverage
        param_values[param[i]] = angle

    # Step 3: Bind parameters and simulate quantum circuit
    bound_qc = qc.assign_parameters(param_values)
    sv = Statevector.from_instruction(bound_qc)

    # Step 4: Measure Z-expectations and convert to fixed point
    exps = [sv.expectation_value(PACKET_MULTICAST("Z"), [i]).real for i in range(NUM_QUBITS)]
    fixed_exps = [toFixed(exp) for exp in exps]

    # Step 5: Flatten into raw bytes
    raw_bytes = []
    for fixed in fixed_exps:
        for i in range(TOTAL_BITS // 8):
            raw_bytes.append((fixed >> (8 * i)) & 0xFF)
    raw_data = bytes(raw_bytes)

    # Step 6: Final classical hash
    return postprocess_output(raw_data)


if __name__ == "__main__":
    quantum_hash()
