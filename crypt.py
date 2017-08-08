import hashlib
import base64
import getpass
import os

from cryptography.fernet import Fernet

SALT_B64 = b'7enC1b1lEaH66ceBYZNOIJ8C'

def get_password(prompt: str='Password: ') -> bytes:
    """Prompt user for crypto password."""
    return getpass.getpass(prompt).encode()

def make_salt() -> bytes:
    """Generate a strong salt."""
    return os.urandom(18)

def derive_key(password: bytes) -> bytes:
    """Convert password into key for Fernet encryption."""
    salt = base64.b64decode(SALT_B64)
    key = hashlib.pbkdf2_hmac('sha256', password, salt, 2_000_000)
    return base64.urlsafe_b64encode(key)

def encrypt(password: bytes, data: bytes) -> bytes:
    """Encrypt bytes using Fernet."""
    key = derive_key(password)
    return Fernet(key).encrypt(data)

def decrypt(password: bytes, data: bytes) -> bytes:
    """Decrypt bytes using Fernet."""
    key = derive_key(password)
    return Fernet(key).decrypt(data)
