#!/usr/bin/env python3
"""
Niek's password manager.
"""
from datetime import datetime, UTC
from typing import Any, Dict, Tuple
import argparse
import os
import os.path
import resource
import signal
import sys

import util
import vault

def parse_args() -> Tuple[str, Dict[str, str]]:
    """Parse command line args.

    Uses argparse for command and argument validation.
    Prints usage and terminates if no args given.
    """
    parser = argparse.ArgumentParser(prog='pman.py', description='Password manager')
    subparsers = parser.add_subparsers(dest='command')

    subparsers.add_parser('init').add_argument('vfname')
    subparsers.add_parser('list')
    subparsers.add_parser('set')
    subparsers.add_parser('get').add_argument('credname')
    subparsers.add_parser('search').add_argument('substr')
    subparsers.add_parser('remove').add_argument('credname')
    subparsers.add_parser('rekey')
    subparsers.add_parser('merge').add_argument('v2fname')

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    args_dict = {k: v for k, v in vars(args).items() if k != 'command'}
    return (args.command, args_dict)


def cmd_init(vfname: str) -> None:
    """Create new empty vault."""
    vpass = util.get_confirmed_password('vault key? ')
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
        age = (datetime.now(UTC) - vault.parse_dt(cred['modified'])).days
        print(f"{k:<20} - u={cred['username']:<30} d={cred['description']:<40} ({age} days)")
    print('--------------')


def cmd_set(vfname: str, vpass: bytes, salt: bytes, v: vault.Vault) -> None:
    """Create or update vault entry."""
    try:
        d = {}
        d['credname'] = input(f'{"credential:":<20}')
        d['username'] = input(f'{"username:":<20}')
        d['password'] = util.get_confirmed_password(f'{"password:":<20}').decode('utf-8')
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
        age = (datetime.now(UTC) - vault.parse_dt(cred['modified'])).days
        print(f"{k:<20} - u={cred['username']:<30} d={cred['description']:<40} ({age} days)")
    print('---------------')


def cmd_remove(vfname: str, vpass: bytes, salt: bytes, v: vault.Vault, credname: str) -> None:
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
    newpass = util.get_confirmed_password('new vault key? ')
    new_salt = util.make_salt()
    with open(vfname, 'wb') as fp:
        util.save_vault(fp, newpass, new_salt, v)
    print('vault key changed')


def cmd_merge(vfname: str, vpass: bytes, salt: bytes, v1: vault.Vault, v2fname: str) -> None:
    """Merge two vault files, keeping newest for conflicting keys."""
    # load second vault
    try:
        v2pass = util.get_password('second vault key? ')
        with open(v2fname, 'rb') as fp:
            v2, _salt = util.load_vault(fp, v2pass)
    except Exception as e:
        print(f'\nunable to load second vault: {e}\n')
        sys.exit(1)

    actions = v1.merge(v2)
    for action, key, v1_mod, v2_mod in actions:
        if action == 'add':
            print(f'add from v2: {key}')
        elif action == 'update':
            print(f'update from v2: {key} [v1={v1_mod}, v2={v2_mod}]')
        elif action == 'skip':
            print(f'skip from v2: {key} [v1={v1_mod}, v2={v2_mod}]')

    with open(vfname, 'wb') as fp:
        util.save_vault(fp, vpass, salt, v1)


def signal_handler(_signum: int, _frame: Any) -> None:
    """Handle SIGINT gracefully."""
    print('\n\n  -- cancelled!\n')
    sys.exit(1)


def main() -> None:
    """Main entry point."""
    cmd, args = parse_args()

    # no stacktrace on ctrl-c
    signal.signal(signal.SIGINT, signal_handler)

    # no core dumps
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

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
    elif cmd == 'merge':
        cmd_merge(vfname, vpass, salt, v, **args)
    else:
        raise RuntimeError('unhandled command')


if __name__ == '__main__':
    main()
