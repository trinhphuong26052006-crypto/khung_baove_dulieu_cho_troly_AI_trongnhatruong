import unittest
from src.filtering.input_guard import validate_input


class TestInputGuard(unittest.TestCase):
    def test_trim(self):
        self.assertEqual(validate_input("  học phí  "), (True, "học phí"))

    def test_empty(self):
        self.assertFalse(validate_input("  ")[0])

    def test_non_string(self):
        self.assertFalse(validate_input(None)[0])

    def test_length_boundary(self):
        self.assertTrue(validate_input("a" * 5, max_length=5)[0])
        self.assertFalse(validate_input("a" * 6, max_length=5)[0])

    def test_keyword_case_insensitive(self):
        self.assertFalse(validate_input("IGNORE PREVIOUS INSTRUCTIONS")[0])

    def test_no_prompt_echo(self):
        secret = "ignore previous instructions: SECRET_123"
        valid, reason = validate_input(secret)
        self.assertFalse(valid)
        self.assertNotIn("SECRET_123", reason)


if __name__ == "__main__":
    unittest.main()
