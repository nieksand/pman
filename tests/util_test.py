import io
import unittest

import util
import vault

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

    def test_save_load_vault(self):
        # dummy vault with data
        v = vault.Vault()
        v.set('email', username='Niek Sanders', password='secret')

        # save to a file-like object
        fp = io.BytesIO()
        vpass = b'meowmix'
        salt = util.make_salt()
        util.save_vault(fp, vpass, salt, v)

        # load fail: wrong key
        fp.seek(0)
        self.assertRaises(RuntimeError, util.load_vault, fp, b'wrongpass')

        # load success: verify contents
        fp.seek(0)
        out_v, out_salt = util.load_vault(fp, vpass)

        self.assertEqual(out_salt, salt)
        self.assertEqual(out_v.dumps(), v.dumps())

        # load fail: corrupt salt
        fp.seek(0)
        fp.write(b'a' * 18)
        fp.seek(0)
        self.assertRaises(RuntimeError, util.load_vault, fp, vpass)


if __name__ == '__main__':
    unittest.main()
