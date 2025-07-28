"""
AES-256-GCM Encryption Module
Implements encryption compatible with Trezor Suite's label format
"""

import os
import json
from typing import Dict, Tuple, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


class AESGCMEncryption:
    """
    AES-256-GCM encryption/decryption for label data.
    Compatible with Trezor Suite's implementation.
    """
    
    # Constants matching Trezor Suite
    KEY_SIZE = 32  # 256 bits
    NONCE_SIZE = 12  # 96 bits for GCM
    TAG_SIZE = 16  # 128 bits
    
    @staticmethod
    def generate_nonce() -> bytes:
        """Generate a random nonce for GCM mode."""
        return os.urandom(AESGCMEncryption.NONCE_SIZE)
    
    @staticmethod
    def encrypt(key: bytes, plaintext: bytes, associated_data: Optional[bytes] = None) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypt data using AES-256-GCM.
        
        Args:
            key: 32-byte encryption key
            plaintext: Data to encrypt
            associated_data: Optional additional authenticated data
            
        Returns:
            Tuple of (ciphertext, nonce, tag)
        """
        if len(key) != AESGCMEncryption.KEY_SIZE:
            raise ValueError(f"Key must be {AESGCMEncryption.KEY_SIZE} bytes")
        
        nonce = AESGCMEncryption.generate_nonce()
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Add associated data if provided
        if associated_data:
            encryptor.authenticate_additional_data(associated_data)
        
        # Encrypt
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        
        return ciphertext, nonce, encryptor.tag
    
    @staticmethod
    def decrypt(key: bytes, ciphertext: bytes, nonce: bytes, tag: bytes, 
                associated_data: Optional[bytes] = None) -> bytes:
        """
        Decrypt data using AES-256-GCM.
        
        Args:
            key: 32-byte encryption key
            ciphertext: Encrypted data
            nonce: Nonce used for encryption
            tag: Authentication tag
            associated_data: Optional additional authenticated data
            
        Returns:
            Decrypted plaintext
            
        Raises:
            Exception: If decryption or authentication fails
        """
        if len(key) != AESGCMEncryption.KEY_SIZE:
            raise ValueError(f"Key must be {AESGCMEncryption.KEY_SIZE} bytes")
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Add associated data if provided
        if associated_data:
            decryptor.authenticate_additional_data(associated_data)
        
        # Decrypt
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return plaintext


class TrezorSuiteFormat:
    """
    Handle Trezor Suite's .mtdt file format for label storage.
    """
    
    VERSION = 1  # Format version
    
    @staticmethod
    def pack_labels(labels: Dict[str, str], encryption_key: bytes) -> bytes:
        """
        Pack labels into Trezor Suite format with encryption.
        
        Args:
            labels: Dict of address/tx -> label mappings
            encryption_key: 32-byte encryption key
            
        Returns:
            Encrypted binary data ready for .mtdt file
        """
        # Convert labels to JSON
        labels_json = json.dumps({
            'version': TrezorSuiteFormat.VERSION,
            'labels': labels
        }, separators=(',', ':'), ensure_ascii=False)
        
        plaintext = labels_json.encode('utf-8')
        
        # Encrypt with AES-256-GCM
        ciphertext, nonce, tag = AESGCMEncryption.encrypt(encryption_key, plaintext)
        
        # Pack into binary format: nonce || ciphertext || tag
        packed = nonce + ciphertext + tag
        
        return packed
    
    @staticmethod
    def unpack_labels(data: bytes, encryption_key: bytes) -> Dict[str, str]:
        """
        Unpack and decrypt labels from Trezor Suite format.
        
        Args:
            data: Encrypted binary data from .mtdt file
            encryption_key: 32-byte encryption key
            
        Returns:
            Dict of address/tx -> label mappings
            
        Raises:
            Exception: If decryption fails or format is invalid
        """
        # Extract components
        if len(data) < AESGCMEncryption.NONCE_SIZE + AESGCMEncryption.TAG_SIZE:
            raise ValueError("Invalid data format - too short")
        
        nonce = data[:AESGCMEncryption.NONCE_SIZE]
        tag = data[-AESGCMEncryption.TAG_SIZE:]
        ciphertext = data[AESGCMEncryption.NONCE_SIZE:-AESGCMEncryption.TAG_SIZE]
        
        # Decrypt
        plaintext = AESGCMEncryption.decrypt(
            encryption_key, ciphertext, nonce, tag
        )
        
        # Parse JSON
        labels_data = json.loads(plaintext.decode('utf-8'))
        
        # Validate version
        if labels_data.get('version') != TrezorSuiteFormat.VERSION:
            raise ValueError(f"Unsupported format version: {labels_data.get('version')}")
        
        return labels_data.get('labels', {})
    
    @staticmethod
    def derive_key_from_password(password: str, salt: bytes) -> bytes:
        """
        Derive encryption key from password using PBKDF2.
        Used for software wallets that don't support hardware encryption.
        
        Args:
            password: User password or wallet-derived secret
            salt: Salt for key derivation
            
        Returns:
            32-byte encryption key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password.encode('utf-8'))