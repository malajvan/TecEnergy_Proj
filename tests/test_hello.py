# test_hello.py

import unittest
from software.code.hello import say_hello


class TestHello(unittest.TestCase):
    def test_say_hello(self):
        result = say_hello()
        self.assertEqual(result, "Hello, World!")


if __name__ == "__main__":
    unittest.main()
