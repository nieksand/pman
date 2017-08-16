import unittest

import util

class UtilTest(unittest.TestCase):

    def test_make_salt(self):
        # quickie check on length and minimal byte variety
        s = util.make_salt()
        self.assertEqual(len(s), 18)
        self.assertGreater(len(set(s)), 4)

    def test_encrypt_decrypt(self):
        # roundtrip to ensure we can recover original plaintext
        password = b'potato'
        salt = util.make_salt()
        plain_text = b'the cat meows twice at midnight'

        cipher_text = util.encrypt(password, salt, plain_text)
        deciphered_text = util.decrypt(password, salt, cipher_text)

        self.assertEqual(plain_text, deciphered_text)


if __name__ == '__main__':
    unittest.main()
