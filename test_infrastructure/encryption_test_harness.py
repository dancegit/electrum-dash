"""
Encryption/Decryption Test Harness
Provides utilities for testing wallet encryption and decryption
"""

import os
import json
import base64
import hashlib
from typing import Dict, Tuple, Optional, Any, List
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import pytest


class EncryptionTestHarness:
    """Test harness for wallet encryption/decryption functionality"""
    
    # Test constants
    TEST_PASSWORD = "test_wallet_password_123"
    TEST_SALT_SIZE = 16
    TEST_IV_SIZE = 16
    TEST_KEY_SIZE = 32  # 256 bits for AES-256
    TEST_ITERATIONS = 10000
    
    # Test wallet data
    TEST_WALLET_DATA = {
        "version": 1,
        "wallet_type": "standard",
        "seed": "test seed phrase here",
        "private_keys": ["key1", "key2", "key3"],
        "addresses": ["address1", "address2", "address3"],
        "labels": {
            "address1": "Main wallet",
            "address2": "Savings"
        }
    }
    
    @classmethod
    def generate_salt(cls, size: int = None) -> bytes:
        """Generate a random salt for testing"""
        size = size or cls.TEST_SALT_SIZE
        return os.urandom(size)
    
    @classmethod
    def generate_iv(cls, size: int = None) -> bytes:
        """Generate a random IV for testing"""
        size = size or cls.TEST_IV_SIZE
        return os.urandom(size)
    
    @classmethod
    def derive_key(cls, password: str, salt: bytes, 
                   iterations: int = None) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        iterations = iterations or cls.TEST_ITERATIONS
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=cls.TEST_KEY_SIZE,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        
        return kdf.derive(password.encode('utf-8'))
    
    @classmethod
    def encrypt_data(cls, data: Any, password: str,
                    salt: Optional[bytes] = None,
                    iv: Optional[bytes] = None,
                    iterations: Optional[int] = None) -> Dict[str, str]:
        """Encrypt data with AES-256-CBC"""
        # Generate salt and IV if not provided
        salt = salt or cls.generate_salt()
        iv = iv or cls.generate_iv()
        iterations = iterations or cls.TEST_ITERATIONS
        
        # Serialize data
        if isinstance(data, (dict, list)):
            plaintext = json.dumps(data).encode('utf-8')
        else:
            plaintext = str(data).encode('utf-8')
        
        # Derive key
        key = cls.derive_key(password, salt, iterations)
        
        # Pad plaintext to block size (16 bytes for AES)
        block_size = 16
        padding_length = block_size - (len(plaintext) % block_size)
        plaintext += bytes([padding_length]) * padding_length
        
        # Encrypt
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        
        # Return encrypted data with metadata
        return {
            "encrypted": True,
            "version": 1,
            "algorithm": "AES-256-CBC",
            "salt": base64.b64encode(salt).decode('utf-8'),
            "iv": base64.b64encode(iv).decode('utf-8'),
            "iterations": iterations,
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8')
        }
    
    @classmethod
    def decrypt_data(cls, encrypted_data: Dict[str, Any], 
                    password: str) -> Any:
        """Decrypt data encrypted with encrypt_data"""
        if not encrypted_data.get("encrypted"):
            raise ValueError("Data is not marked as encrypted")
        
        # Decode base64 values
        salt = base64.b64decode(encrypted_data["salt"])
        iv = base64.b64decode(encrypted_data["iv"])
        ciphertext = base64.b64decode(encrypted_data["ciphertext"])
        iterations = encrypted_data.get("iterations", cls.TEST_ITERATIONS)
        
        # Derive key
        key = cls.derive_key(password, salt, iterations)
        
        # Decrypt
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        plaintext_padded = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Remove padding
        padding_length = plaintext_padded[-1]
        plaintext = plaintext_padded[:-padding_length]
        
        # Deserialize
        try:
            return json.loads(plaintext.decode('utf-8'))
        except json.JSONDecodeError:
            return plaintext.decode('utf-8')
    
    @classmethod
    def create_corrupted_data(cls, encrypted_data: Dict[str, Any],
                            corruption_type: str = "ciphertext") -> Dict[str, Any]:
        """Create corrupted encrypted data for error testing"""
        corrupted = encrypted_data.copy()
        
        if corruption_type == "ciphertext":
            # Corrupt the ciphertext
            ciphertext = base64.b64decode(corrupted["ciphertext"])
            corrupted_bytes = bytearray(ciphertext)
            corrupted_bytes[len(corrupted_bytes)//2] ^= 0xFF  # Flip bits
            corrupted["ciphertext"] = base64.b64encode(bytes(corrupted_bytes)).decode('utf-8')
            
        elif corruption_type == "salt":
            # Change the salt
            corrupted["salt"] = base64.b64encode(os.urandom(16)).decode('utf-8')
            
        elif corruption_type == "iv":
            # Change the IV
            corrupted["iv"] = base64.b64encode(os.urandom(16)).decode('utf-8')
            
        elif corruption_type == "missing_field":
            # Remove a required field
            del corrupted["salt"]
            
        elif corruption_type == "wrong_version":
            # Set unsupported version
            corrupted["version"] = 999
        
        return corrupted
    
    @classmethod
    def verify_encryption_strength(cls, encrypted_data: Dict[str, Any]) -> Dict[str, bool]:
        """Verify encryption parameters meet security requirements"""
        checks = {
            "has_salt": "salt" in encrypted_data,
            "salt_length": len(base64.b64decode(encrypted_data.get("salt", ""))) >= 16,
            "has_iv": "iv" in encrypted_data,
            "iv_length": len(base64.b64decode(encrypted_data.get("iv", ""))) >= 16,
            "iterations_sufficient": encrypted_data.get("iterations", 0) >= 10000,
            "algorithm_secure": encrypted_data.get("algorithm") == "AES-256-CBC"
        }
        checks["all_passed"] = all(checks.values())
        return checks
    
    @classmethod
    def generate_test_cases(cls) -> List[Tuple[str, Any, str]]:
        """Generate various test cases for encryption/decryption"""
        return [
            ("simple_string", "Hello, World!", cls.TEST_PASSWORD),
            ("wallet_data", cls.TEST_WALLET_DATA, cls.TEST_PASSWORD),
            ("empty_data", {}, cls.TEST_PASSWORD),
            ("unicode_data", {"message": "Hello 世界 🌍"}, cls.TEST_PASSWORD),
            ("large_data", {"data": "x" * 10000}, cls.TEST_PASSWORD),
            ("special_chars", {"path": "/home/user/wallet!@#$%^&*()"}, "P@ssw0rd!#$"),
        ]


# Pytest fixtures
@pytest.fixture
def encryption_harness():
    """Provide encryption test harness"""
    return EncryptionTestHarness()


@pytest.fixture
def encrypted_wallet_data():
    """Provide pre-encrypted wallet data for testing"""
    return EncryptionTestHarness.encrypt_data(
        EncryptionTestHarness.TEST_WALLET_DATA,
        EncryptionTestHarness.TEST_PASSWORD
    )


@pytest.fixture
def encryption_test_cases():
    """Provide various test cases"""
    return EncryptionTestHarness.generate_test_cases()