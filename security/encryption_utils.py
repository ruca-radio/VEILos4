from cryptography.fernet import Fernet


def generate_key():
    """Generate a new encryption key."""
    return Fernet.generate_key()


def encrypt_data(key, data):
    """Encrypt string data with the given key."""
    fernet = Fernet(key)
    return fernet.encrypt(data.encode())


def decrypt_data(key, encrypted_data):
    """Decrypt data with the given key."""
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_data).decode()
