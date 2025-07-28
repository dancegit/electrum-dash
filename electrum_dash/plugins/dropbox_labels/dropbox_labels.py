import asyncio
import hashlib
import json
import os
import base64
from typing import Union, Optional, Dict, Any, Tuple, TYPE_CHECKING
from datetime import datetime, timezone
import hmac
import secrets

from electrum_dash.plugin import BasePlugin, hook
from electrum_dash.crypto import aes_encrypt_with_iv, aes_decrypt_with_iv
from electrum_dash.i18n import _
from electrum_dash.util import log_exceptions, ignore_exceptions
from electrum_dash.logging import Logger

# Dropbox imports
try:
    import dropbox
    from dropbox import DropboxOAuth2FlowNoRedirect
    from dropbox.files import WriteMode, GetMetadataError
    from dropbox.exceptions import ApiError, AuthError
    DROPBOX_AVAILABLE = True
except ImportError:
    DROPBOX_AVAILABLE = False
    
# Local imports
from .encryption import AESGCMEncryption, TrezorSuiteFormat
from .auth import DropboxOAuth2
from .config import DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_FOLDER, USE_HARDWARE_ENCRYPTION
from .slip15 import TrezorLabelEncryption, SLIP15Purpose

if TYPE_CHECKING:
    from electrum_dash.wallet import Abstract_Wallet


class DropboxLabelsPlugin(BasePlugin):
    """
    Plugin for syncing wallet labels with Dropbox.
    Supports both software wallets and hardware wallets (Trezor) with SLIP-0015.
    """
    
    def __init__(self, parent, config, name):
        BasePlugin.__init__(self, parent, config, name)
        self.wallets = {}
        self.dropbox_client = None
        self.dropbox_app_key = DROPBOX_APP_KEY
        self.dropbox_app_secret = DROPBOX_APP_SECRET
        self.dropbox_tokens = {}  # wallet_id -> oauth_token mapping
        self.auth_flow = None  # OAuth2 flow instance
        
    def encode(self, wallet: 'Abstract_Wallet', msg: str) -> str:
        """Encrypt and encode a message for storage"""
        password, iv, wallet_id = self.wallets[wallet]
        # For backward compatibility, still use old method for now
        # Will switch to AES-256-GCM when saving to Dropbox
        encrypted = aes_encrypt_with_iv(password, iv, msg.encode('utf8'))
        return base64.b64encode(encrypted).decode()
    
    def decode(self, wallet: 'Abstract_Wallet', message: str) -> str:
        """Decode and decrypt a message from storage"""
        password, iv, wallet_id = self.wallets[wallet]
        decoded = base64.b64decode(message)
        # For backward compatibility, still use old method for now
        decrypted = aes_decrypt_with_iv(password, iv, decoded)
        return decrypted.decode('utf8')
    
    def get_encryption_key(self, wallet: 'Abstract_Wallet') -> bytes:
        """Get AES-256 encryption key for Dropbox storage"""
        # Check if this is a hardware wallet
        if self.is_hardware_wallet(wallet) and USE_HARDWARE_ENCRYPTION:
            try:
                # Use SLIP-0015 for hardware wallets
                account_index = self.get_account_index(wallet)
                encryption_key, _ = self._get_hardware_keys(wallet, account_index)
                return encryption_key
            except Exception as e:
                self.logger.warning(f"Failed to use hardware encryption: {e}")
                # Fall back to software encryption
        
        # Software wallet or fallback
        password, _, _ = self.wallets[wallet]
        # Derive proper 256-bit key from password
        return hashlib.sha256(password).digest()
    
    def is_hardware_wallet(self, wallet: 'Abstract_Wallet') -> bool:
        """Check if wallet uses hardware device."""
        return (hasattr(wallet, 'keystore') and 
                hasattr(wallet.keystore, 'plugin') and
                hasattr(wallet.keystore.plugin, 'get_client'))
    
    def get_account_index(self, wallet: 'Abstract_Wallet') -> int:
        """Get BIP44 account index from wallet."""
        # Default to account 0
        # TODO: Extract actual account index from derivation path
        return 0
    
    def _get_hardware_keys(self, wallet: 'Abstract_Wallet', account_index: int) -> Tuple[bytes, str]:
        """Get encryption key and filename using hardware wallet."""
        hw_device = wallet.keystore.plugin
        trezor_encryption = TrezorLabelEncryption(hw_device)
        return trezor_encryption.get_label_keys(account_index)
    
    def get_wallet_id(self, wallet: 'Abstract_Wallet') -> str:
        """Get unique wallet identifier"""
        if wallet in self.wallets:
            return self.wallets[wallet][2]
        return None
    
    def get_dropbox_folder(self, wallet: 'Abstract_Wallet') -> str:
        """Get the Dropbox folder path for this wallet"""
        # Use configured folder from config
        return DROPBOX_FOLDER
    
    def get_label_filename(self, wallet: 'Abstract_Wallet', account_index: int = 0) -> str:
        """
        Get the filename for storing labels.
        For hardware wallets using SLIP-0015, this will be the hex-encoded account fingerprint.
        For software wallets, use wallet_id.
        """
        # Check if this is a hardware wallet
        if self.is_hardware_wallet(wallet) and USE_HARDWARE_ENCRYPTION:
            try:
                # Use SLIP-0015 filename generation
                _, filename = self._get_hardware_keys(wallet, account_index)
                return filename
            except Exception as e:
                self.logger.warning(f"Failed to get hardware filename: {e}")
                # Fall back to standard naming
        
        # Software wallet or fallback
        wallet_id = self.get_wallet_id(wallet)
        if not wallet_id:
            return None
            
        if account_index > 0:
            filename = f"{wallet_id}_account_{account_index}.mtdt"
        else:
            filename = f"{wallet_id}.mtdt"
        
        return filename
    
    @hook
    def set_label(self, wallet: 'Abstract_Wallet', item: str, label: str):
        """Hook called when a label is set"""
        if wallet not in self.wallets:
            return
        if not item:
            return
            
        # Queue label for sync
        asyncio.run_coroutine_threadsafe(
            self.sync_label(wallet, item, label),
            wallet.network.asyncio_loop
        )
    
    @ignore_exceptions
    @log_exceptions
    async def sync_label(self, wallet: 'Abstract_Wallet', item: str, label: str):
        """Sync a single label to Dropbox"""
        if not self.is_authenticated(wallet):
            self.logger.info("Dropbox not authenticated for wallet")
            return
            
        try:
            # For efficiency, we'll batch label updates
            # Download current labels, update, and re-upload
            labels = await self.pull_labels(wallet, force=False)
            
            # Update the specific label
            if label:
                labels[item] = label
            else:
                # Empty label means deletion
                labels.pop(item, None)
            
            # Re-upload all labels
            encryption_key = self.get_encryption_key(wallet)
            encrypted_data = TrezorSuiteFormat.pack_labels(labels, encryption_key)
            
            filename = self.get_label_filename(wallet)
            filepath = self.get_dropbox_folder(wallet) + filename
            
            dbx = self.get_dropbox_client(wallet)
            dbx.files_upload(
                encrypted_data,
                filepath,
                mode=WriteMode.overwrite,
                mute=True
            )
            
            self.logger.info(f"Synced label for {item}")
            
        except Exception as e:
            self.logger.error(f"Failed to sync label: {e}")
    
    async def push_labels(self, wallet: 'Abstract_Wallet'):
        """Push all labels to Dropbox"""
        if not self.is_authenticated(wallet):
            raise Exception("Dropbox not authenticated")
            
        if not DROPBOX_AVAILABLE:
            raise Exception("Dropbox package not installed")
            
        wallet_id = self.get_wallet_id(wallet)
        labels_data = {}
        
        # Collect all labels
        for key, value in wallet.get_all_labels().items():
            try:
                labels_data[key] = value
            except Exception as e:
                self.logger.info(f'Cannot encode label {repr(key)}: {e}')
                continue
        
        # Use AES-256-GCM for Dropbox storage
        encryption_key = self.get_encryption_key(wallet)
        encrypted_data = TrezorSuiteFormat.pack_labels(labels_data, encryption_key)
        
        # Upload to Dropbox
        filename = self.get_label_filename(wallet)
        filepath = self.get_dropbox_folder(wallet) + filename
        
        try:
            dbx = self.get_dropbox_client(wallet)
            dbx.files_upload(
                encrypted_data,
                filepath,
                mode=WriteMode.overwrite,
                mute=True
            )
            self.logger.info(f"Uploaded {len(labels_data)} labels to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to upload labels: {e}")
            raise
    
    async def pull_labels(self, wallet: 'Abstract_Wallet', force: bool = False):
        """Pull labels from Dropbox"""
        if not self.is_authenticated(wallet):
            raise Exception("Dropbox not authenticated")
            
        if not DROPBOX_AVAILABLE:
            raise Exception("Dropbox package not installed")
            
        filename = self.get_label_filename(wallet)
        filepath = self.get_dropbox_folder(wallet) + filename
        
        try:
            dbx = self.get_dropbox_client(wallet)
            
            # Download file
            metadata, response = dbx.files_download(filepath)
            encrypted_data = response.content
            
            # Decrypt labels
            encryption_key = self.get_encryption_key(wallet)
            labels = TrezorSuiteFormat.unpack_labels(encrypted_data, encryption_key)
            
            # Update wallet labels
            for key, value in labels.items():
                if force or not wallet.get_label(key):
                    wallet._set_label(key, value)
            
            self.logger.info(f"Downloaded {len(labels)} labels from {filepath}")
            return labels
            
        except ApiError as e:
            if isinstance(e.error, GetMetadataError) and e.error.is_path():
                # File doesn't exist yet
                self.logger.info(f"No labels file found at {filepath}")
                return {}
            else:
                self.logger.error(f"Failed to download labels: {e}")
                raise
    
    def is_authenticated(self, wallet: 'Abstract_Wallet') -> bool:
        """Check if wallet has valid Dropbox authentication"""
        wallet_id = self.get_wallet_id(wallet)
        if not wallet_id:
            return False
        return wallet_id in self.dropbox_tokens and self.dropbox_tokens[wallet_id]
    
    def get_dropbox_client(self, wallet: 'Abstract_Wallet') -> 'dropbox.Dropbox':
        """Get Dropbox client for wallet"""
        if not DROPBOX_AVAILABLE:
            raise Exception("Dropbox package not installed")
            
        wallet_id = self.get_wallet_id(wallet)
        token = self.dropbox_tokens.get(wallet_id)
        if not token:
            raise Exception("No Dropbox token available")
            
        return dropbox.Dropbox(token)
    
    def start_wallet(self, wallet: 'Abstract_Wallet'):
        """Initialize wallet for label sync"""
        if not wallet.network:
            return  # Offline mode
            
        mpk = wallet.get_fingerprint()
        if not mpk:
            return
            
        # Generate encryption keys (similar to existing labels plugin)
        mpk_bytes = mpk.encode('ascii')
        password = hashlib.sha1(mpk_bytes).hexdigest()[:32].encode('ascii')
        iv = hashlib.sha256(password).digest()[:16]
        wallet_id = hashlib.sha256(mpk_bytes).hexdigest()
        
        self.wallets[wallet] = (password, iv, wallet_id)
        
        # Load OAuth token if stored
        stored_token = wallet.db.get('dropbox_oauth_token')
        if stored_token:
            try:
                # Decrypt the stored token
                decrypted_token = self.decode(wallet, stored_token)
                self.dropbox_tokens[wallet_id] = decrypted_token
                # Start sync
                asyncio.run_coroutine_threadsafe(
                    self.pull_labels(wallet, False),
                    wallet.network.asyncio_loop
                )
            except Exception as e:
                self.logger.error(f"Failed to decrypt stored token: {e}")
    
    def stop_wallet(self, wallet: 'Abstract_Wallet'):
        """Clean up wallet resources"""
        wallet_data = self.wallets.pop(wallet, None)
        if wallet_data:
            wallet_id = wallet_data[2]
            self.dropbox_tokens.pop(wallet_id, None)
    
    def authenticate_dropbox(self, wallet: 'Abstract_Wallet') -> str:
        """
        Start OAuth2 authentication flow.
        Returns the authorization URL for user to visit.
        """
        if not DROPBOX_AVAILABLE:
            raise Exception("Dropbox package not installed")
            
        # For now, use simplified flow (without redirect)
        # In production, should use full OAuth2 with PKCE
        if not self.dropbox_app_key:
            # Default app key - should be configured
            self.dropbox_app_key = "your_app_key_here"
            
        self.auth_flow = DropboxOAuth2FlowNoRedirect(
            self.dropbox_app_key,
            use_pkce=True,
            token_access_type='offline'
        )
        
        authorize_url = self.auth_flow.start()
        return authorize_url
    
    def complete_authentication(self, wallet: 'Abstract_Wallet', auth_code: str) -> bool:
        """
        Complete OAuth2 authentication with the authorization code.
        Returns True if successful.
        """
        if not DROPBOX_AVAILABLE:
            return False
            
        try:
            oauth_result = self.auth_flow.finish(auth_code)
            access_token = oauth_result.access_token
            
            wallet_id = self.get_wallet_id(wallet)
            if wallet_id:
                self.dropbox_tokens[wallet_id] = access_token
                
                # Store encrypted token in wallet
                # Encrypt token before storage
                encrypted_token = self.encode(wallet, access_token)
                wallet.db.put('dropbox_oauth_token', encrypted_token)
                wallet.db.write()
                
                return True
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            
        return False
    
    def logout_dropbox(self, wallet: 'Abstract_Wallet'):
        """Remove Dropbox authentication for wallet"""
        wallet_id = self.get_wallet_id(wallet)
        if wallet_id:
            self.dropbox_tokens.pop(wallet_id, None)
            wallet.db.put('dropbox_oauth_token', None)
    
    async def import_trezor_suite_labels(self, wallet: 'Abstract_Wallet') -> Dict[str, str]:
        """
        Import existing labels from Trezor Suite.
        Looks in /Apps/TREZOR/ folder for compatible .mtdt files.
        """
        if not self.is_authenticated(wallet):
            raise Exception("Dropbox not authenticated")
            
        if not DROPBOX_AVAILABLE:
            raise Exception("Dropbox package not installed")
            
        if not self.is_hardware_wallet(wallet):
            raise Exception("This feature requires a hardware wallet")
            
        try:
            dbx = self.get_dropbox_client(wallet)
            
            # List files in Trezor Suite folder
            trezor_folder = "/Apps/TREZOR/"
            result = dbx.files_list_folder(trezor_folder)
            
            # Get encryption key for this wallet
            encryption_key = self.get_encryption_key(wallet)
            
            imported_labels = {}
            
            # Try to decrypt each .mtdt file
            for entry in result.entries:
                if entry.name.endswith('.mtdt'):
                    try:
                        # Download file
                        filepath = trezor_folder + entry.name
                        metadata, response = dbx.files_download(filepath)
                        encrypted_data = response.content
                        
                        # Try to decrypt with our key
                        labels = TrezorSuiteFormat.unpack_labels(encrypted_data, encryption_key)
                        
                        # If successful, these are our labels
                        imported_labels.update(labels)
                        self.logger.info(f"Successfully imported labels from {entry.name}")
                        
                    except Exception as e:
                        # This file is for a different wallet/account
                        self.logger.debug(f"Could not decrypt {entry.name}: {e}")
                        continue
            
            # Update wallet with imported labels
            for key, value in imported_labels.items():
                wallet._set_label(key, value)
            
            return imported_labels
            
        except Exception as e:
            self.logger.error(f"Failed to import Trezor Suite labels: {e}")
            raise