#!/usr/local/bin/python3
import datetime
import os
import os.path
import sys

import cryptography

import vault
import crypt

def parse_args():
    """Parse command line args.

    Does minimal verification to ensure command and associated argument count
    are valid.  Terminates program otherwise.  Prints usage and terminate if no args
    given.
    """
    cmd_args = {
        'init':   ['vfname'],
        'list':   [],
        'set':    [],
        'get':    ['credname'],
        'search': ['substr'],
        'remove': ['credname'],
        'rekey':  [],
    }
    valid_cmds = sorted(cmd_args.keys())

    # must specify command
    if len(sys.argv) < 2:
        print(f'\nusage: {sys.argv[0]} [command] [args]\n')
        for c in valid_cmds:
            astr = ', '.join([f'<{v}>' for v in cmd_args[c]])
            print(f'    {c:<6} - {astr}')
        print()
        sys.exit(0)

    # command must be valid
    cmd = sys.argv[1]
    if cmd not in valid_cmds:
        print(f"\ninvalid command, expecting one of: {', '.join(valid_cmds)}\n")
        sys.exit(1)

    # correct command-specific arg count
    args_recv = len(sys.argv) - 2
    args_want = len(cmd_args[cmd])
    if args_recv != args_want:
        print(f"\nincorrect arg count for '{cmd}': got={args_recv}, expected={args_want}\n")
        astr = ', '.join([f'<{v}>' for v in cmd_args[cmd]])
        print(f'    {cmd:<6} - {astr}\n')
        sys.exit(1)

    return (cmd, dict( zip(cmd_args[cmd], sys.argv[2:]) ))


def load_vault(vpass, vfname):
    """Load existing vault."""
    with open(vfname, 'rb') as fp:
        salt = fp.read(18)
        v_enc = fp.read()

    try:
        v_raw = crypt.decrypt(vpass, v_enc)
    except cryptography.fernet.InvalidToken:
        print('\nincorrect decryption key\n', file=sys.stderr)
        sys.exit(1)

    v = vault.Vault()
    v.loads(v_raw)
    return (v, salt)


def save_vault(vpass, v, salt, vfname, oflag='wb'):
    """Save vault."""
    v_raw = v.dumps().encode()
    v_enc = crypt.encrypt(vpass, v_raw)
    with open(vfname, oflag) as fp:
        fp.write(salt)
        fp.write(v_enc)


def cmd_init(vfname):
    """Create new empty vault."""
    while True:
        vpass = crypt.get_password('vault key? ')
        confirm = crypt.get_password('vault key? ')
        if vpass == confirm:
            break
        print('\npasswords do not match\n')

    v = vault.Vault()
    try:
        salt = crypt.make_salt()
        save_vault(vpass, v, salt, vfname, 'xb')
    except FileExistsError:
        print('\nvault with that name already exists\n', file=sys.stderr)
        sys.exit(1)

    print(f'\ninitialized new vault: {vfname}\n')
    fullpath = os.path.abspath(vfname)
    print(f'you will want: export PMAN_VAULT={fullpath}\n')


def cmd_list(v):
    """List vault contents."""
    print('\nVault contents')
    print('--------------')
    for k in v.list():
        cred = v.get(k)
        age = (datetime.datetime.utcnow() - vault.parse_dt(cred['modified'])).days
        print(f"{k:<20} - u={cred['username']:<30} d={cred['description']:<40} ({age} days)")
    print('--------------')


def cmd_set(vpass, v):
    """Create or update vault entry."""
    try:
        d = {}
        d['credname'] = input(f'{"credential:":<20}')
        d['username'] = input(f'{"username:":<20}')

        while True:
            d['password'] = crypt.get_password(f'{"password:":<20}').decode('utf-8')
            pass_confirm = crypt.get_password(f'{"password:":<20}').decode('utf-8')
            if d['password'] == pass_confirm:
                break
            print('\npasswords do not match\n')

        d['description'] = input(f'{"description:":<20}')

    except EOFError:
        print('\ncancelled')

    v.set(**d)
    save_vault(vpass, v, salt, vfname)



def cmd_get(v, credname):
    """Get vault entry."""
    try:
        cred = v.get(credname)
        print(f"{credname:<20} - u={cred['username']} p={cred['password']} d={cred['description']}")
    except KeyError:
        print('credential not found')


def cmd_search(v, substr):
    """Search vault credential names."""
    print('\nSearch results')
    print('---------------')
    for k, cred in v.search(substr):
        age = (datetime.datetime.utcnow() - vault.parse_dt(cred['modified'])).days
        print(f"{k:<20} - u={cred['username']:<30} d={cred['description']:<40} ({age} days)")
    print('---------------')


def cmd_remove(vpass, v, credname):
    """Remove vault entry."""
    try:
        print('removing: ', v.get(credname))
        v.remove(credname)
        save_vault(vpass, v, salt, vfname)
    except KeyError:
        print('credential not found')


def cmd_rekey(v, vfname):
    """Change secret key and salt on vault."""
    while True:
        newpass = crypt.get_password('new vault key? ')
        confirm = crypt.get_password('new vault key? ')
        if newpass == confirm:
            break
        print('\npasswords do not match\n')

    new_salt = crypt.make_salt()
    save_vault(newpass, v, new_salt, vfname)
    print('vault key changed')


if __name__ == '__main__':
    cmd, args = parse_args()

    # only cmd not requiring vault
    if cmd == 'init':
        cmd_init(**args)
        sys.exit(0)

    # PMAN_VAULT environment var dictates location
    if 'PMAN_VAULT' not in os.environ:
        print('\nPMAN_VAULT environment variable must point to vault file\n', file=sys.stderr)
        sys.exit(1)

    vpass = crypt.get_password('vault key? ')
    vfname = os.environ['PMAN_VAULT']
    v, salt = load_vault(vpass, vfname)

    if cmd == 'list':
        cmd_list(v)
    elif cmd == 'set':
        cmd_set(vpass, v)
    elif cmd == 'get':
        cmd_get(v, **args)
    elif cmd == 'search':
        cmd_search(v, **args)
    elif cmd == 'remove':
        cmd_remove(vpass, v, **args)
    elif cmd == 'rekey':
        cmd_rekey(v, vfname)
    else:
        raise RuntimeError('unhandled command')
