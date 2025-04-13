import unittest
from main import qhash_quantum_walk  # Replace with actual module name if needed


class TestQuantumHashFunction(unittest.TestCase):
    def test_output_type_and_size(self):
        """Check that the output is of type bytes and matches input size."""
        input_data = bytearray([1, 2, 3, 4, 5, 8])
        output = qhash_quantum_walk(input_data)
        self.assertIsInstance(output, bytes)
        self.assertEqual(len(output), len(input_data))

    def test_hash_determinism(self):
        """Ensure that the same input always produces the same hash."""
        input_data = bytearray([1, 2, 3, 4, 5, 8])
        hash1 = qhash_quantum_walk(input_data)
        hash2 = qhash_quantum_walk(input_data)
        self.assertEqual(hash1, hash2)

    def test_avalanche_effect(self):
        """Test that small changes in input cause big changes in output (avalanche effect)."""
        input_data = bytearray([1, 2, 3, 4, 5, 8])
        modified_data = bytearray(input_data)
        modified_data[0] ^= 1  # Flip the first bit

        hash1 = qhash_quantum_walk(input_data)
        hash2 = qhash_quantum_walk(modified_data)

        # Compare how many bytes differ
        diff_count = sum(b1 != b2 for b1, b2 in zip(hash1, hash2))
        self.assertGreater(diff_count, len(hash1) // 2, "Not enough bytes changed in avalanche test")

if __name__ == '__main__':
    unittest.main()
