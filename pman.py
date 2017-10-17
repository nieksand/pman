#!/usr/local/bin/python3
"""
Niek's password manager.
"""
import datetime
import os
import os.path
import signal
import sys

import vault
import util

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

    return (cmd, dict(zip(cmd_args[cmd], sys.argv[2:])))


def cmd_init(vfname: str) -> None:
    """Create new empty vault."""
    while True:
        vpass = util.get_password('vault key? ')
        confirm = util.get_password('vault key? ')
        if vpass == confirm:
            break
        print('\npasswords do not match\n')

    v = vault.Vault()
    try:
        with open(vfname, 'xb') as fp:
            util.save_vault(fp, vpass, util.make_salt(), v)
    except FileExistsError:
        print('\nvault with that name already exists\n', file=sys.stderr)
        sys.exit(1)

    print(f'\ninitialized new vault: {vfname}\n')
    fullpath = os.path.abspath(vfname)
    print(f'you will want: export PMAN_VAULT={fullpath}\n')


def cmd_list(v: vault.Vault) -> None:
    """List vault contents."""
    print('\nVault contents')
    print('--------------')
    for k in v.list():
        cred = v.get(k)
        age = (datetime.datetime.utcnow() - vault.parse_dt(cred['modified'])).days
        print(f"{k:<20} - u={cred['username']:<30} d={cred['description']:<40} ({age} days)")
    print('--------------')


def cmd_set(vfname: str, vpass: bytes, salt: str, v: vault.Vault) -> None:
    """Create or update vault entry."""
    try:
        d = {}
        d['credname'] = input(f'{"credential:":<20}')
        d['username'] = input(f'{"username:":<20}')

        while True:
            d['password'] = util.get_password(f'{"password:":<20}').decode('utf-8')
            pass_confirm = util.get_password(f'{"password:":<20}').decode('utf-8')
            if d['password'] == pass_confirm:
                break
            print('\npasswords do not match\n')

        d['description'] = input(f'{"description:":<20}')

    except EOFError:
        print('\ncancelled')

    credname = d['credname']
    if credname in v.list():
        print(f'\nreplacing: {v.get(credname)}\n')

    v.set(**d)
    with open(vfname, 'wb') as fp:
        util.save_vault(fp, vpass, salt, v)


def cmd_get(v: vault.Vault, credname: str) -> None:
    """Get vault entry."""
    try:
        cred = v.get(credname)
        print(f"{credname:<20} - u={cred['username']} p={cred['password']} d={cred['description']}")
    except KeyError:
        print('\ncredential not found\n')


def cmd_search(v: vault.Vault, substr: str) -> None:
    """Search vault credential names."""
    print('\nSearch results')
    print('---------------')
    for k in v.search(substr):
        cred = v.get(k)
        age = (datetime.datetime.utcnow() - vault.parse_dt(cred['modified'])).days
        print(f"{k:<20} - u={cred['username']:<30} d={cred['description']:<40} ({age} days)")
    print('---------------')


def cmd_remove(vfname: str, vpass: bytes, salt: str, v: vault.Vault, credname: str) -> None:
    """Remove vault entry."""
    try:
        print(f'\nremoving: {v.get(credname)}\n')
        v.remove(credname)
        with open(vfname, 'wb') as fp:
            util.save_vault(fp, vpass, salt, v)
    except KeyError:
        print('credential not found')


def cmd_rekey(v: vault.Vault, vfname: str) -> None:
    """Change secret key and salt on vault."""
    while True:
        newpass = util.get_password('new vault key? ')
        confirm = util.get_password('new vault key? ')
        if newpass == confirm:
            break
        print('\npasswords do not match\n')

    new_salt = util.make_salt()
    with open(vfname, 'wb') as fp:
        util.save_vault(fp, newpass, new_salt, v)
    print('vault key changed')


def signal_handler(signum, frame):
    """Handle SIGINT gracefully."""
    print('\n\n  -- cancelled!\n')
    exit(1)


def main():
    cmd, args = parse_args()

    # no stacktrace on ctrl-c
    signal.signal(signal.SIGINT, signal_handler)

    # only cmd not requiring vault
    if cmd == 'init':
        cmd_init(**args)
        sys.exit(0)

    # PMAN_VAULT environment var dictates location
    if 'PMAN_VAULT' not in os.environ:
        print('\nPMAN_VAULT environment variable must point to vault file\n', file=sys.stderr)
        sys.exit(1)

    vpass = util.get_password('vault key? ')
    vfname = os.environ['PMAN_VAULT']

    try:
        with open(vfname, 'rb') as fp:
            v, salt = util.load_vault(fp, vpass)
    except Exception as e:
        print(f'\nunable to load vault: {e}\n')
        sys.exit(1)

    if cmd == 'list':
        cmd_list(v)
    elif cmd == 'set':
        cmd_set(vfname, vpass, salt, v)
    elif cmd == 'get':
        cmd_get(v, **args)
    elif cmd == 'search':
        cmd_search(v, **args)
    elif cmd == 'remove':
        cmd_remove(vfname, vpass, salt, v, **args)
    elif cmd == 'rekey':
        cmd_rekey(v, vfname)
    else:
        raise RuntimeError('unhandled command')


if __name__ == '__main__':
    main()
