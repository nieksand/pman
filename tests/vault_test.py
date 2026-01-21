from datetime import datetime, UTC
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

    def test_dt_helpers(self):
        s = vault.current_dt()
        self.assertEqual(len(s), 19)

        dt = vault.parse_dt(s)
        utc = datetime.now(UTC)
        self.assertGreaterEqual(utc, dt)

    def test_merge_add(self):
        # new keys from other vault are added
        v1 = vault.Vault()
        v1.set('a', username='Alice')

        v2 = vault.Vault()
        v2.set('b', username='Bob')

        actions = v1.merge(v2)
        self.assertEqual(actions, [('add', 'b', None, None)])
        self.assertEqual(v1.list(), ['a', 'b'])
        self.assertEqual(v1.get('b')['username'], 'Bob')

    def test_merge_update(self):
        # existing keys updated when other is newer
        v1 = vault.Vault()
        v1.set('a', username='Alice')
        v1.get('a')['modified'] = '2020-01-01 00:00:00'

        v2 = vault.Vault()
        v2.set('a', username='Alice-Updated')
        v2.get('a')['modified'] = '2025-01-01 00:00:00'

        actions = v1.merge(v2)
        self.assertEqual(actions, [('update', 'a', '2020-01-01 00:00:00', '2025-01-01 00:00:00')])
        self.assertEqual(v1.get('a')['username'], 'Alice-Updated')

    def test_merge_skip(self):
        # existing keys skipped when self is newer
        v1 = vault.Vault()
        v1.set('a', username='Alice')
        v1.get('a')['modified'] = '2025-01-01 00:00:00'

        v2 = vault.Vault()
        v2.set('a', username='Alice-Old')
        v2.get('a')['modified'] = '2020-01-01 00:00:00'

        actions = v1.merge(v2)
        self.assertEqual(actions, [('skip', 'a', '2025-01-01 00:00:00', '2020-01-01 00:00:00')])
        self.assertEqual(v1.get('a')['username'], 'Alice')

    def test_merge_identical(self):
        # identical credentials produce no action
        v1 = vault.Vault()
        v1.set('a', username='Alice')
        cred = v1.get('a')

        v2 = vault.Vault()
        v2.set('a', username='Alice')
        v2.get('a')['created'] = cred['created']
        v2.get('a')['modified'] = cred['modified']

        actions = v1.merge(v2)
        self.assertEqual(actions, [])
