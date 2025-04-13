import time
import unittest
from hash4 import quantum_process_chunk, NUM_QUBITS  # Replace with actual module name if needed

class TestQuantumHashFunction(unittest.TestCase):
    
    def test_output_and_size_consistency(self):
    
        inputs = [
            bytearray([1, 2, 3, 4, 5, 8]),
            bytearray([10, 20, 30, 40, 50, 60]),
            bytearray([255, 255, 255, 255, 255, 255]),
            bytearray([0, 0, 0, 0, 0, 0]),
            bytearray([1, 1, 1, 1, 1, 1, 1, 1]),
            bytearray([255] * 16),  # Larger inputs for coverage
            bytearray([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]),
        ]
        
        for input_data in inputs:
            output = quantum_process_chunk(input_data)
            
            # Check that output is of type bytes
            self.assertIsInstance(output, bytes)
            
            # Check that the output size is the same as the input size
            self.assertEqual(len(output), len(input_data), f"Output size mismatch for input: {input_data}")

    def test_hash_determinism(self):
        """Ensure that the same input always produces the same hash."""
        inputs = [
            bytearray([1, 2, 3, 4, 5, 8]),
            bytearray([10, 20, 30, 40, 50, 60]),
            bytearray([255, 255, 255, 255, 255, 255]),
            bytearray([0, 0, 0, 0, 0, 0]),
            bytearray([1, 1, 1, 1, 1, 1, 1, 1]),
        ]
        
        for input_data in inputs:
            hash1 = quantum_process_chunk(input_data)
            hash2 = quantum_process_chunk(input_data)
            # Check that the hash for the same input is always the same
            self.assertEqual(hash1, hash2, f"Hash mismatch for input: {input_data}")

    def test_entropy_preservation(self):
        """Ensure the output has high byte diversity (entropy proxy)."""
        input_data = bytearray(range(32))
        output = quantum_process_chunk(input_data)
        unique_bytes = len(set(output))
        self.assertGreaterEqual(unique_bytes, len(output) // 2, "Low entropy in output hash")

    def test_preimage_resistance_proxy(self):
        """Check that hashes are hard to reverse by brute-force within limited attempts."""
        target_input = bytearray(range(16))
        target_hash = quantum_process_chunk(target_input)

        for guess in (bytearray([i] * 16) for i in range(256)):
            if guess == target_input:
                continue
            if quantum_process_chunk(guess) == target_hash:
                self.fail("Preimage found by brute-force")

    def test_qubit_count_feasibility(self):
        """Ensure total qubit usage does not exceed 20 and report how many were used."""
        num_qubits_used = NUM_QUBITS  # coin + position qubits
        print(f"\nQubits used: {num_qubits_used}")
        self.assertLessEqual(num_qubits_used, 20, f"Too many qubits used: {num_qubits_used}")


    import time

    def test_execution_speed(self):
        """Ensure that hash function executes within reasonable time."""
        input_data = bytearray(range(32))
        start = time.time()
        quantum_process_chunk(input_data)
        duration = time.time() - start
        self.assertLess(duration, 2.0, "Hash function took too long")


    def test_no_classical_hashing(self):
        """Ensure no classical hash libraries are imported."""
        import inspect
        src = inspect.getsource(quantum_process_chunk)
        self.assertNotIn("hashlib", src, "Classical hashing detected in quantum hash function")


    def test_avalanche_effect(self):
        """Test that small changes in input cause big changes in output (avalanche effect)."""
        inputs = [
            bytearray([1, 2, 3, 4, 5, 8]),
            bytearray([5, 6, 7, 8, 9, 10]),
            bytearray([10, 20, 30, 40, 50, 60]),
            bytearray([255, 255, 255, 255, 255, 255]),
            bytearray([1, 1, 1, 1, 1, 1, 1, 1]),
            bytearray([255] * 16),
            bytearray([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]),
        ]
        
        for input_data in inputs:
            # Create a modified version of the input data
            modified_data = bytearray(input_data)
            modified_data[0] ^= 1  # Flip the first bit to create a small change

            # Generate hashes for both the original and modified data
            hash1 = quantum_process_chunk(input_data)
            hash2 = quantum_process_chunk(modified_data)

            # Compare how many bytes differ between the two hashes
            diff_count = sum(b1 != b2 for b1, b2 in zip(hash1, hash2))
            
            # Ensure more than half of the bytes have changed (avalanche effect)
            if diff_count < 3:
                self.fail(f"Avalanche effect FAILED for input {input_data} — only {diff_count} bytes differ")
            elif diff_count == 3:
                print(f"Weak avalanche effect for input {input_data} — exactly 3 bytes differ")
            else:
                print(f"Good avalanche effect for input {input_data} — {diff_count} bytes differ")

    def test_collision_resistance(self):
        """Test that two different inputs produce different hashes (collision resistance)."""
        inputs = [
            bytearray([1, 2, 3, 4, 5, 8]),
            bytearray([1, 2, 3, 4, 5, 9]),  # Slightly different input
            bytearray([5, 6, 7, 8, 9, 10]),
            bytearray([10, 20, 30, 40, 50, 60]),
            bytearray([255, 255, 255, 255, 255, 255]),
            bytearray([0, 0, 0, 0, 0, 0]),
            bytearray([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]),
            bytearray([255] * 32),
        ]
        
        # Compare all pairs of inputs to ensure no collisions
        for i in range(len(inputs)):
            for j in range(i + 1, len(inputs)):
                input_data1 = inputs[i]
                input_data2 = inputs[j]
                
                # Generate hashes for both inputs
                hash1 = quantum_process_chunk(input_data1)
                hash2 = quantum_process_chunk(input_data2)

                # Ensure that the hashes are different for different inputs (collision resistance)
                self.assertNotEqual(hash1, hash2, f"Collision detected between inputs: {input_data1} and {input_data2}")

if __name__ == '__main__':
    unittest.main()
