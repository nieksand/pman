import hashlib
import base64
import getpass
import os
from typing import Tuple

from cryptography.fernet import Fernet

import vault

def get_password(prompt: str='Password: ') -> bytes:
    """Prompt user for crypto password."""
    return getpass.getpass(prompt).encode()

def make_salt() -> bytes:
    """Generate a strong salt."""
    return os.urandom(18)

def derive_key(password: bytes, salt: bytes) -> bytes:
    """Convert password into key for Fernet encryption."""
    key = hashlib.pbkdf2_hmac('sha256', password, salt, 2_000_000)
    return base64.urlsafe_b64encode(key)

def encrypt(password: bytes, salt: bytes, data: bytes) -> bytes:
    """Encrypt bytes using Fernet."""
    key = derive_key(password, salt)
    return Fernet(key).encrypt(data)

def decrypt(password: bytes, salt: bytes, data: bytes) -> bytes:
    """Decrypt bytes using Fernet."""
    key = derive_key(password, salt)
    return Fernet(key).decrypt(data)

def load_vault(vpass: bytes, vfname: str) -> Tuple[vault.Vault, bytes]:
    """Load existing vault."""
    with open(vfname, 'rb') as fp:
        salt = fp.read(18)
        v_enc = fp.read()

    try:
        v_raw = decrypt(vpass, salt, v_enc)
    except cryptography.fernet.InvalidToken:
        print('\nincorrect decryption key\n', file=sys.stderr)
        sys.exit(1)

    v = vault.Vault()
    v.loads(v_raw)
    return (v, salt)

def save_vault(vpass: bytes, v: vault.Vault, salt: bytes, vfname: str, oflag: str='wb') -> None:
    """Save vault."""
    v_raw = v.dumps().encode()
    v_enc = encrypt(vpass, salt, v_raw)
    with open(vfname, oflag) as fp:
        fp.write(salt)
        fp.write(v_enc)
