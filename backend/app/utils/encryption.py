from cryptography.fernet import Fernet
import base64
import os
import logging
from pathlib import Path

logger = logging.getLogger('app')

class EncryptionError(Exception):
    """Base exception for encryption related errors"""
    pass

class CredentialEncryption:
    def __init__(self):
        self.key_file = Path('config/encryption.key')
        self.key = self._load_or_generate_key()
        self.cipher_suite = Fernet(self.key)

    def _load_or_generate_key(self) -> bytes:
        """Load existing key or generate a new one"""
        try:
            if self.key_file.exists():
                with open(self.key_file, 'rb') as f:
                    return base64.urlsafe_b64decode(f.read())
            else:
                # Generate new key
                key = Fernet.generate_key()
                # Ensure directory exists
                self.key_file.parent.mkdir(parents=True, exist_ok=True)
                # Save key
                with open(self.key_file, 'wb') as f:
                    f.write(base64.urlsafe_b64encode(key))
                logger.info("Generated new encryption key")
                return key
        except Exception as e:
            logger.error(f"Error handling encryption key: {str(e)}")
            raise EncryptionError(f"Failed to handle encryption key: {str(e)}")

    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        try:
            if not data:
                return ''
            # Convert string to bytes, encrypt, and return as string
            encrypted = self.cipher_suite.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            raise EncryptionError(f"Failed to encrypt data: {str(e)}")

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        try:
            if not encrypted_data:
                return ''
            # Convert from string to bytes, decrypt, and return as string
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher_suite.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption error: {str(e)}")
            raise EncryptionError(f"Failed to decrypt data: {str(e)}")

    def rotate_key(self) -> None:
        """Generate new key and re-encrypt all stored credentials"""
        try:
            # TODO: Implement key rotation
            # This would involve:
            # 1. Generate new key
            # 2. Decrypt all stored credentials with old key
            # 3. Encrypt all credentials with new key
            # 4. Update stored key
            pass
        except Exception as e:
            logger.error(f"Key rotation error: {str(e)}")
            raise EncryptionError(f"Failed to rotate encryption key: {str(e)}")

    def secure_string(self, s: str) -> str:
        """Return a masked version of a string for logging"""
        if not s:
            return ''
        return f"{s[:2]}...{s[-2:]}" if len(s) > 4 else '****' 