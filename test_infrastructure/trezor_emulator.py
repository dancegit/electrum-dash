"""
Trezor Device Emulator for Hardware Wallet Testing
Provides mock Trezor device responses and SLIP-0015 implementation
"""

import hashlib
import hmac
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json
import base64


@dataclass
class TrezorDevice:
    """Mock Trezor device state"""
    device_id: str = "test_trezor_device_001"
    label: str = "Test Trezor"
    initialized: bool = True
    pin_protection: bool = True
    passphrase_protection: bool = True
    firmware_version: Tuple[int, int, int] = (2, 4, 3)
    model: str = "T"  # Trezor Model T
    
    # Device state
    _pin_entered: bool = False
    _passphrase: Optional[str] = None
    _seed: Optional[bytes] = None


class SLIP0015:
    """Implementation of SLIP-0015 for deterministic key derivation"""
    
    @staticmethod
    def derive_wallet_encryption_key(master_node: bytes, passphrase: str = "") -> bytes:
        """
        Derive wallet encryption key according to SLIP-0015
        
        Path: m/10015'/0'
        Returns: 32-byte symmetric encryption key
        """
        # Mock implementation of SLIP-0015
        # In real implementation, this would use proper BIP32 derivation
        
        # Simulate BIP32 derivation at m/10015'/0'
        purpose = 10015 | 0x80000000  # Hardened
        coin_type = 0 | 0x80000000    # Hardened
        
        # Mock derivation using HMAC-SHA512
        data = b"SLIP-0015" + master_node + passphrase.encode('utf-8')
        derived = hmac.new(b"wallet-encryption-key", data, hashlib.sha512).digest()
        
        # Return first 32 bytes as symmetric key
        return derived[:32]
    
    @staticmethod
    def derive_label_encryption_key(master_node: bytes, wallet_id: str) -> bytes:
        """
        Derive label-specific encryption key
        
        Uses wallet ID to ensure unique keys per wallet
        """
        # Combine master key with wallet ID for unique derivation
        data = master_node + wallet_id.encode('utf-8')
        return hashlib.sha256(data).digest()


class TrezorEmulator:
    """Emulates Trezor device for testing"""
    
    def __init__(self):
        self.device = TrezorDevice()
        self.slip0015 = SLIP0015()
        
        # Test seed for consistent testing
        self.test_seed = bytes.fromhex(
            "5eb00bbddcf069084889a8ab9155568165f5c453ccb85e70811aaed6f6da5fc1"
            "9a5ac40b389cd370d086206dec8aa6c43daea6690f20ad3d8d48b2d2ce9e38e4"
        )
        
        # Response handlers
        self.handlers = {
            "Initialize": self._handle_initialize,
            "GetFeatures": self._handle_get_features,
            "GetPublicKey": self._handle_get_public_key,
            "SignMessage": self._handle_sign_message,
            "CipherKeyValue": self._handle_cipher_key_value,
            "GetAddress": self._handle_get_address,
        }
    
    def call(self, message_type: str, **kwargs) -> Dict[str, Any]:
        """Emulate Trezor device call"""
        handler = self.handlers.get(message_type)
        if not handler:
            raise ValueError(f"Unsupported message type: {message_type}")
        
        return handler(**kwargs)
    
    def _handle_initialize(self, **kwargs) -> Dict[str, Any]:
        """Handle device initialization"""
        return {
            "device_id": self.device.device_id,
            "initialized": self.device.initialized,
            "label": self.device.label,
            "pin_protection": self.device.pin_protection,
            "passphrase_protection": self.device.passphrase_protection,
        }
    
    def _handle_get_features(self, **kwargs) -> Dict[str, Any]:
        """Get device features"""
        return {
            "vendor": "trezor.io",
            "major_version": self.device.firmware_version[0],
            "minor_version": self.device.firmware_version[1],
            "patch_version": self.device.firmware_version[2],
            "device_id": self.device.device_id,
            "label": self.device.label,
            "initialized": self.device.initialized,
            "pin_protection": self.device.pin_protection,
            "passphrase_protection": self.device.passphrase_protection,
            "model": self.device.model,
            "capabilities": ["Capability_Bitcoin", "Capability_Crypto"],
        }
    
    def _handle_get_public_key(self, path: List[int], **kwargs) -> Dict[str, Any]:
        """Get public key for derivation path"""
        # Mock BIP32 derivation
        # In real implementation, this would derive from seed
        path_str = "/".join(str(p) for p in path)
        
        # Generate deterministic public key based on path
        mock_pubkey = hashlib.sha256(
            self.test_seed + path_str.encode('utf-8')
        ).digest()
        
        # Mock xpub generation
        xpub = base64.b64encode(mock_pubkey).decode('utf-8')
        
        return {
            "node": {
                "depth": len(path),
                "fingerprint": int.from_bytes(mock_pubkey[:4], 'big'),
                "child_num": path[-1] if path else 0,
                "chain_code": mock_pubkey,
                "public_key": mock_pubkey,
            },
            "xpub": f"xpub{xpub[:107]}",  # Mock xpub format
        }
    
    def _handle_sign_message(self, path: List[int], message: bytes, **kwargs) -> Dict[str, Any]:
        """Sign message with private key at path"""
        # Mock message signing
        # In real implementation, this would use actual key derivation
        
        # Derive mock private key
        path_str = "/".join(str(p) for p in path)
        private_key = hashlib.sha256(
            self.test_seed + path_str.encode('utf-8') + b"privkey"
        ).digest()
        
        # Mock signature (would use ECDSA in reality)
        signature = hmac.new(private_key, message, hashlib.sha256).digest()
        
        return {
            "signature": base64.b64encode(signature).decode('utf-8'),
            "address": self._derive_address(path),
        }
    
    def _handle_cipher_key_value(self, path: List[int], key: str, value: bytes, 
                                encrypt: bool = True, **kwargs) -> Dict[str, Any]:
        """Encrypt/decrypt value using derived key"""
        # This is used for SLIP-0015 encryption
        
        # Derive encryption key
        path_bytes = b"".join(p.to_bytes(4, 'big') for p in path)
        derived_key = hmac.new(
            self.test_seed + path_bytes,
            key.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        if encrypt:
            # Mock encryption (XOR for simplicity)
            result = bytes(a ^ b for a, b in zip(value, derived_key * (len(value) // 32 + 1)))
        else:
            # Mock decryption (same as encryption for XOR)
            result = bytes(a ^ b for a, b in zip(value, derived_key * (len(value) // 32 + 1)))
        
        return {
            "value": base64.b64encode(result).decode('utf-8'),
        }
    
    def _handle_get_address(self, path: List[int], **kwargs) -> Dict[str, Any]:
        """Get address for derivation path"""
        address = self._derive_address(path)
        return {
            "address": address,
        }
    
    def _derive_address(self, path: List[int]) -> str:
        """Derive mock address from path"""
        path_str = "/".join(str(p) for p in path)
        addr_hash = hashlib.sha256(
            self.test_seed + path_str.encode('utf-8') + b"address"
        ).digest()
        
        # Mock Dash address format
        return f"Xtest{base64.b32encode(addr_hash[:20]).decode('utf-8').lower()[:30]}"
    
    def get_master_public_key(self) -> bytes:
        """Get master public key for SLIP-0015 derivation"""
        return hashlib.sha256(self.test_seed + b"master_pubkey").digest()
    
    def derive_slip0015_key(self, wallet_id: str) -> bytes:
        """Derive SLIP-0015 encryption key for wallet"""
        master_pubkey = self.get_master_public_key()
        return self.slip0015.derive_label_encryption_key(master_pubkey, wallet_id)


class TrezorConfirmationFlow:
    """Mock Trezor confirmation flow for user interactions"""
    
    def __init__(self, emulator: TrezorEmulator):
        self.emulator = emulator
        self.pending_confirmations: List[Dict[str, Any]] = []
    
    def request_confirmation(self, action: str, details: Dict[str, Any]) -> str:
        """Request user confirmation on device"""
        confirmation_id = f"confirm_{len(self.pending_confirmations)}"
        
        self.pending_confirmations.append({
            "id": confirmation_id,
            "action": action,
            "details": details,
            "status": "pending"
        })
        
        return confirmation_id
    
    def confirm(self, confirmation_id: str) -> bool:
        """Simulate user confirming on device"""
        for conf in self.pending_confirmations:
            if conf["id"] == confirmation_id:
                conf["status"] = "confirmed"
                return True
        return False
    
    def reject(self, confirmation_id: str) -> bool:
        """Simulate user rejecting on device"""
        for conf in self.pending_confirmations:
            if conf["id"] == confirmation_id:
                conf["status"] = "rejected"
                return True
        return False


# Test fixtures
class TrezorTestFixtures:
    """Pre-generated test data for Trezor testing"""
    
    @staticmethod
    def get_test_wallets() -> List[Dict[str, Any]]:
        """Get test wallet configurations"""
        return [
            {
                "id": "wallet_001",
                "name": "Test Wallet 1",
                "device_id": "test_trezor_device_001",
                "xpub": "xpub6CUGRUonZSQ4TWtTMmzXdrXDtypWKiKpXi6p3zY3mjD",
            },
            {
                "id": "wallet_002", 
                "name": "Test Wallet 2",
                "device_id": "test_trezor_device_002",
                "xpub": "xpub6DUGRUonZSQ4TWtTMmzXdrXDtypWKiKpXi6p3zY3mjE",
            }
        ]
    
    @staticmethod
    def get_test_mtdt_file() -> bytes:
        """Get test .mtdt file content (Trezor Suite format)"""
        mtdt_data = {
            "version": "1.0",
            "wallets": {
                "wallet_001": {
                    "labels": {
                        "Xtest1234567890abcdef": "Main wallet",
                        "Xtest0987654321fedcba": "Savings",
                    }
                }
            },
            "encrypted": True,
            "algorithm": "AES-256-GCM"
        }
        
        return json.dumps(mtdt_data).encode('utf-8')