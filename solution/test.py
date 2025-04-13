import unittest
from main import qhash_quantum_walk  # Replace with actual module name if needed

class TestQuantumHashFunction(unittest.TestCase):
    
    def test_output_type_and_size(self):
        """Check that the output is of type bytes and matches input size."""
        input_data = bytearray([1, 2, 3, 4, 5, 8])
        output = qhash_quantum_walk(input_data)
        # Check that output is of type bytes
        self.assertIsInstance(output, bytes)
        # Check that the output size is the same as input size
        self.assertEqual(len(output), len(input_data))

    def test_input_output_size_consistency(self):
        """Ensure the size of the input is the same as the size of the output hash."""
        inputs = [
            bytearray([1, 2, 3, 4, 5, 8]),
            bytearray([10, 20, 30, 40, 50, 60]),
            bytearray([255, 255, 255, 255, 255, 255]),
            bytearray([0, 0, 0, 0, 0, 0]),
            bytearray([1, 1, 1, 1, 1, 1, 1, 1]),
        ]
        
        for input_data in inputs:
            output = qhash_quantum_walk(input_data)
            # Check that the size of the output is the same as the input size
            self.assertEqual(len(input_data), len(output), f"Input size and output size do not match for input: {input_data}")

    def test_hash_determinism(self):
        """Ensure that the same input always produces the same hash."""
        input_data = bytearray([1, 2, 3, 4, 5, 8])
        hash1 = qhash_quantum_walk(input_data)
        hash2 = qhash_quantum_walk(input_data)
        # Check that the hash for the same input is always the same
        self.assertEqual(hash1, hash2)

    def test_avalanche_effect(self):
        """Test that small changes in input cause big changes in output (avalanche effect)."""
        inputs = [
            bytearray([1, 2, 3, 4, 5, 8]),
            bytearray([5, 6, 7, 8, 9, 10]),
            bytearray([10, 20, 30, 40, 50, 60]),
            bytearray([255, 255, 255, 255, 255, 255]),
        ]
        
        for input_data in inputs:
            # Create a modified version of the input data
            modified_data = bytearray(input_data)
            modified_data[0] ^= 1  # Flip the first bit to create a small change

            # Generate hashes for both the original and modified data
            hash1 = qhash_quantum_walk(input_data)
            hash2 = qhash_quantum_walk(modified_data)

            # Compare how many bytes differ between the two hashes
            diff_count = sum(b1 != b2 for b1, b2 in zip(hash1, hash2))
            
            # Ensure more than half of the bytes have changed (avalanche effect)
            self.assertGreater(diff_count, len(hash1) // 2, f"Avalanche effect failed for input: {input_data}")

    def test_collision_resistance(self):
        """Test that two different inputs produce different hashes (collision resistance)."""
        inputs = [
            bytearray([1, 2, 3, 4, 5, 8]),
            bytearray([1, 2, 3, 4, 5, 9]),  # Slightly different input
            bytearray([5, 6, 7, 8, 9, 10]),
            bytearray([10, 20, 30, 40, 50, 60]),
            bytearray([255, 255, 255, 255, 255, 255]),
            bytearray([0, 0, 0, 0, 0, 0])
        ]
        
        # Compare all pairs of inputs to ensure no collisions
        for i in range(len(inputs)):
            for j in range(i + 1, len(inputs)):
                input_data1 = inputs[i]
                input_data2 = inputs[j]
                
                # Generate hashes for both inputs
                hash1 = qhash_quantum_walk(input_data1)
                hash2 = qhash_quantum_walk(input_data2)

                # Ensure that the hashes are different for different inputs (collision resistance)
                self.assertNotEqual(hash1, hash2, f"Collision detected between inputs: {input_data1} and {input_data2}")

if __name__ == '__main__':
    unittest.main()
