import unittest
import vault

class TestVault(unittest.TestCase):
    def test_init(self):
        # starts with nothing
        v = vault.Vault()
        ks = v.list()
        self.assertEqual(len(ks), 0, 'new vault not empty')

    def test_list(self):
        # list results are sorted
        v = vault.Vault()
        v.set('b', username='Bob')
        v.set('a', username='Andy')
        v.set('c', username='Cathy')
        ks = v.list()
        self.assertEqual(ks, ['a', 'b', 'c'], 'list not sorted')

    def test_set(self):
        # check auto-created datetime fields
        v = vault.Vault()
        v.set('d', username='David')
        d = v.get('d')
        cre = d['created']
        mod = d['modified']
        self.assertEqual(cre, mod, 'new entry created/modified mismatch')

        # hack datetime fields to be further in past
        hack = '1982-03-28 13:00:00'
        d['created'] = hack
        d['modified'] = hack

        # updating entry should maintain created but bump modified
        v.set('d', username='Edward')
        d = v.get('d')
        self.assertEqual(d['created'], hack, 'created changed')
        self.assertNotEqual(d['modified'], hack, 'created unchanged')

    def test_get(self):
        # existing credential exists
        v = vault.Vault()
        v.set('e', username='Edward', extra='potato')
        e = v.get('e')
        self.assertEqual(len(e), 4)
        self.assertIn('created', e, 'created missing')
        self.assertIn('modified', e, 'modified missing')
        self.assertEqual(e['username'], 'Edward', 'username missing')
        self.assertEqual(e['extra'], 'potato', 'extra data missing')

        # missing credential throws
        self.assertRaises(KeyError, v.get, 'nonexistent cred')

    def test_search(self):
        v = vault.Vault()
        v.set('meowmeow', username='Frederico')
        v.set('meowmix', username='Gregory')
        v.set('purrito', username='Howard')
        v.set('meowpurr', username='Ingrid')

        # match anywhere in string
        self.assertEqual(v.search('purr'), ['meowpurr', 'purrito'])
        # case insensitive
        self.assertEqual(v.search('PURR'), ['meowpurr', 'purrito'])
        # miss
        self.assertEqual(v.search('oink'), [])
        # empty substr matches all
        self.assertEqual(v.search(''), ['meowmeow', 'meowmix', 'meowpurr', 'purrito'])

    def test_remove(self):
        v = vault.Vault()
        v.set('j', username='John')

        # now you see it
        self.assertEqual(v.get('j')['username'], 'John')

        # now you don't
        v.remove('j')
        self.assertRaises(KeyError, v.get, 'j')

    def test_dump_load(self):
        # dump vault to string
        v1 = vault.Vault()
        v1.set('k', username='Kyle')
        v1.set('l', username='Linda')
        s = v1.dumps()

        # load vault from string
        v2 = vault.Vault()
        v2.loads(s)

        # content integrity
        self.assertEqual(v2.list(), ['k', 'l'])
        self.assertEqual(v2.get('k')['username'], 'Kyle')
        self.assertEqual(v2.get('l')['username'], 'Linda')


if __name__ == '__main__':
    unittest.main()
