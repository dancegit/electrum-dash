"""
SLIP-0015: Symmetric Key Derivation From HD Wallet Master Node
Implementation for Trezor hardware wallet label encryption

Based on: https://github.com/satoshilabs/slips/blob/master/slip-0015.md
"""

import hashlib
import hmac
from typing import Tuple, Optional, Dict, Any
from enum import Enum

from electrum_dash.logging import Logger
from electrum_dash.bip32 import BIP32Node
from electrum_dash.crypto import sha256


class SLIP15Purpose(Enum):
    """SLIP-0015 defined purposes"""
    LABELS = "Labels"
    
    
class SLIP15:
    """
    Implements SLIP-0015 symmetric key derivation for hardware wallets.
    
    This allows deriving encryption keys from the HD wallet master node
    in a deterministic way, enabling secure label storage that can only
    be decrypted by the hardware wallet.
    """
    
    # SLIP-0015 constants
    DOMAIN = b"SLIP-0015"
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self._key_cache = {}  # Cache derived keys with timeout
        
    def derive_master_key(self, hw_device, passphrase: str = "") -> bytes:
        """
        Derive master encryption key using hardware wallet's CipherKeyValue.
        
        Args:
            hw_device: Hardware wallet device instance (Trezor, etc.)
            passphrase: Optional passphrase
            
        Returns:
            32-byte master encryption key
        """
        # CipherKeyValue parameters per SLIP-0015 specification
        # Path MUST be m/10015'/0' according to the official SLIP-0015 implementation
        path = [10015 | 0x80000000, 0 | 0x80000000]  # m/10015'/0' in integer format
        key = "Enable labeling?"  # Exact string from SLIP-0015 spec
        # Value MUST be this exact hex sequence per SLIP-0015
        value = bytes.fromhex("fedcba98765432100123456789abcdeffedcba98765432100123456789abcdef")
        
        # For Trezor, we need to use the client's encrypt_keyvalue method
        try:
            client = self._get_client(hw_device)
            
            # Use Trezor's encrypt_keyvalue method
            # This will show confirmation on device if ask_on_encrypt=True
            master_key = client.encrypt_keyvalue(
                n=path,
                key=key,
                value=value,
                ask_on_encrypt=True,
                ask_on_decrypt=True
            )
            
            # The result should be 32 bytes
            if len(master_key) != 32:
                raise ValueError(f"Invalid master key length: {len(master_key)}")
                
            return master_key
            
        except Exception as e:
            self.logger.error(f"Failed to derive master key: {e}")
            raise
    
    def _get_client(self, hw_device):
        """Get the actual Trezor client from the device."""
        # Handle different device types
        if hasattr(hw_device, 'get_client'):
            return hw_device.get_client()
        elif hasattr(hw_device, 'client'):
            return hw_device.client
        else:
            raise ValueError("Unable to get client from hardware device")
    
    def derive_account_key(self, master_key: bytes, purpose: SLIP15Purpose, 
                          account_index: int) -> Tuple[bytes, bytes]:
        """
        Derive account-specific encryption key and filename.
        
        Args:
            master_key: 32-byte master key from hardware wallet
            purpose: SLIP-0015 purpose (e.g., LABELS)
            account_index: BIP44 account index (0, 1, 2, ...)
            
        Returns:
            Tuple of (encryption_key, filename_key) - both 32 bytes
        """
        # Derive encryption key
        encryption_key = self._derive_key(
            master_key,
            purpose.value,
            account_index,
            "Encryption"
        )
        
        # Derive filename key  
        filename_key = self._derive_key(
            master_key,
            purpose.value,
            account_index,
            "Filename"
        )
        
        return encryption_key, filename_key
    
    def _derive_key(self, master_key: bytes, purpose: str, 
                   account_index: int, key_type: str) -> bytes:
        """
        Derive a specific key using HMAC-SHA256.
        
        Args:
            master_key: Master key from hardware wallet
            purpose: Purpose string (e.g., "Labels")
            account_index: Account index
            key_type: "Encryption" or "Filename"
            
        Returns:
            32-byte derived key
        """
        # Build the message for HMAC
        message = f"{purpose}/{account_index}/{key_type}".encode('utf-8')
        
        # Derive key using HMAC-SHA256
        derived = hmac.new(master_key, message, hashlib.sha256).digest()
        
        return derived
    
    def get_filename(self, filename_key: bytes, account_index: int) -> str:
        """
        Generate filename for storing encrypted labels.
        
        Args:
            filename_key: 32-byte filename key
            account_index: Account index
            
        Returns:
            Hex-encoded filename with .mtdt extension
        """
        # Generate account fingerprint
        fingerprint_data = f"account/{account_index}".encode('utf-8')
        fingerprint = hmac.new(filename_key, fingerprint_data, hashlib.sha256).digest()
        
        # Return hex-encoded filename
        return fingerprint.hex() + ".mtdt"
    
    def cache_key(self, key_id: str, key: bytes, timeout: int = 300):
        """
        Cache a derived key with timeout.
        
        Args:
            key_id: Unique identifier for the key
            key: Key to cache
            timeout: Timeout in seconds (default 5 minutes)
        """
        import time
        self._key_cache[key_id] = {
            'key': key,
            'expires': time.time() + timeout
        }
    
    def get_cached_key(self, key_id: str) -> Optional[bytes]:
        """
        Get a cached key if not expired.
        
        Args:
            key_id: Unique identifier for the key
            
        Returns:
            Cached key or None if expired/not found
        """
        import time
        cached = self._key_cache.get(key_id)
        if cached and cached['expires'] > time.time():
            return cached['key']
        elif cached:
            # Remove expired key
            del self._key_cache[key_id]
        return None
    
    def clear_cache(self):
        """Clear all cached keys."""
        self._key_cache.clear()


class TrezorLabelEncryption:
    """
    High-level interface for Trezor label encryption using SLIP-0015.
    """
    
    def __init__(self, hw_device):
        """
        Initialize with hardware wallet device.
        
        Args:
            hw_device: Hardware wallet device instance
        """
        self.hw_device = hw_device
        self.slip15 = SLIP15()
        self.logger = Logger.get_logger(__name__)
        
    def get_label_keys(self, account_index: int = 0, 
                      use_cache: bool = True) -> Tuple[bytes, str]:
        """
        Get encryption key and filename for labels.
        
        Args:
            account_index: BIP44 account index
            use_cache: Whether to use cached master key
            
        Returns:
            Tuple of (encryption_key, filename)
        """
        cache_key = f"master_key_{self.hw_device.get_client().features.device_id}"
        
        # Try to get cached master key
        master_key = None
        if use_cache:
            master_key = self.slip15.get_cached_key(cache_key)
        
        # Derive master key if not cached
        if master_key is None:
            self.logger.info("Deriving master key from hardware wallet...")
            master_key = self.slip15.derive_master_key(self.hw_device)
            
            # Cache it
            if use_cache:
                self.slip15.cache_key(cache_key, master_key)
        
        # Derive account-specific keys
        encryption_key, filename_key = self.slip15.derive_account_key(
            master_key,
            SLIP15Purpose.LABELS,
            account_index
        )
        
        # Generate filename
        filename = self.slip15.get_filename(filename_key, account_index)
        
        return encryption_key, filename
    
    def is_available(self) -> bool:
        """Check if hardware wallet supports SLIP-0015."""
        try:
            # Check if device has cipher_key_value method
            return hasattr(self.hw_device, 'cipher_key_value')
        except:
            return False