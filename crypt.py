import hashlib
import base64
import getpass
import os

from cryptography.fernet import Fernet

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
