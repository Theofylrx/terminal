"""Encryption utilities for sensitive data storage."""

import os
from cryptography.fernet import Fernet
from typing import Optional


class EncryptionManager:
    """
    Manages encryption/decryption of sensitive data using Fernet (symmetric encryption).

    CRITICAL SECURITY NOTES:
    - The encryption key MUST be stored securely (environment variable, AWS Secrets Manager, etc.)
    - NEVER commit the encryption key to version control
    - Use different keys for development, staging, and production
    - Rotate keys periodically and re-encrypt data
    """

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption manager.

        Args:
            encryption_key: Base64-encoded Fernet key. If None, reads from ENCRYPTION_KEY env var.

        Raises:
            ValueError: If no encryption key provided
        """
        if encryption_key is None:
            encryption_key = os.getenv("ENCRYPTION_KEY")

        if not encryption_key:
            raise ValueError(
                "Encryption key not provided. Set ENCRYPTION_KEY environment variable or pass key to constructor."
            )

        self.fernet = Fernet(encryption_key.encode())

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: The string to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""

        encrypted_bytes = self.fernet.encrypt(plaintext.encode())
        return encrypted_bytes.decode()

    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            encrypted_text: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails (wrong key or corrupted data)
        """
        if not encrypted_text:
            return ""

        decrypted_bytes = self.fernet.decrypt(encrypted_text.encode())
        return decrypted_bytes.decode()

    @staticmethod
    def generate_key() -> str:
        """
        Generate a new Fernet encryption key.

        Returns:
            Base64-encoded encryption key

        Usage:
            >>> key = EncryptionManager.generate_key()
            >>> print(f"ENCRYPTION_KEY={key}")
            # Save this to your .env file or secrets manager
        """
        return Fernet.generate_key().decode()


# Global encryption manager instance (initialized on first use)
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """
    Get the global encryption manager instance (singleton pattern).

    Returns:
        EncryptionManager instance

    Raises:
        ValueError: If ENCRYPTION_KEY environment variable not set
    """
    global _encryption_manager

    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()

    return _encryption_manager


def encrypt_string(plaintext: str) -> str:
    """
    Convenience function to encrypt a string using the global encryption manager.

    Args:
        plaintext: String to encrypt

    Returns:
        Encrypted string
    """
    manager = get_encryption_manager()
    return manager.encrypt(plaintext)


def decrypt_string(encrypted_text: str) -> str:
    """
    Convenience function to decrypt a string using the global encryption manager.

    Args:
        encrypted_text: Encrypted string

    Returns:
        Decrypted plaintext
    """
    manager = get_encryption_manager()
    return manager.decrypt(encrypted_text)


# Example usage and key generation script
if __name__ == "__main__":
    print("🔐 Encryption Key Generator")
    print("=" * 50)
    print("\nGenerating new encryption key...")

    key = EncryptionManager.generate_key()

    print(f"\n✅ Generated key:")
    print(f"\nENCRYPTION_KEY={key}")
    print("\n⚠️  IMPORTANT SECURITY NOTES:")
    print("1. Save this key to your .env file")
    print("2. NEVER commit this key to version control")
    print("3. Use different keys for dev/staging/production")
    print("4. Store production keys in AWS Secrets Manager or similar")
    print("5. If you lose this key, encrypted data CANNOT be recovered")

    # Test encryption
    print("\n" + "=" * 50)
    print("Testing encryption/decryption...")

    os.environ["ENCRYPTION_KEY"] = key
    manager = EncryptionManager()

    test_data = "my-secret-api-key-12345"
    encrypted = manager.encrypt(test_data)
    decrypted = manager.decrypt(encrypted)

    print(f"\nOriginal:  {test_data}")
    print(f"Encrypted: {encrypted}")
    print(f"Decrypted: {decrypted}")
    print(f"\n✅ Encryption test {'PASSED' if test_data == decrypted else 'FAILED'}")
