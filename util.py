"""
Utility routines for vault manipulation.
"""
from typing import Tuple, IO
import base64
import getpass
import hashlib
import os

from cryptography import fernet

import vault

def get_password(prompt: str = 'Password: ') -> bytes:
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
    return fernet.Fernet(key).encrypt(data)

def decrypt(password: bytes, salt: bytes, data: bytes) -> bytes:
    """Decrypt bytes using Fernet."""
    key = derive_key(password, salt)
    return fernet.Fernet(key).decrypt(data)

def load_vault(fp: IO[bytes], vpass: bytes) -> Tuple[vault.Vault, bytes]:
    """Load existing vault."""
    salt = fp.read(18)
    v_enc = fp.read()

    try:
        v_raw = decrypt(vpass, salt, v_enc)
    except fernet.InvalidToken as ex:
        raise RuntimeError('incorrect decryption key') from ex

    v = vault.Vault()
    v.loads(v_raw.decode('utf8'))
    return (v, salt)

def save_vault(fp: IO[bytes], vpass: bytes, salt: bytes, v: vault.Vault) -> None:
    """Save vault."""
    v_raw = v.dumps().encode()
    v_enc = encrypt(vpass, salt, v_raw)
    fp.write(salt)
    fp.write(v_enc)
