from cryptography.fernet import Fernet
from django.conf import settings

def get_cipher():
    return Fernet(settings.ENCRYPTION_KEY)

def encrypt_message(message):
    return get_cipher().encrypt(message.encode()).decode()

def decrypt_message(encrypted_text):
    return get_cipher().decrypt(encrypted_text.encode()).decode()
