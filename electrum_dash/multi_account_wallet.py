"""
Multi-Account Wallet Implementation
Extends wallet functionality to support multiple BIP44 accounts
"""

import threading
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict

from . import bitcoin
from .wallet import Deterministic_Wallet, Standard_Wallet
from .keystore import BIP32_KeyStore
from .transaction import Transaction
from .util import profiler
from .logging import get_logger

_logger = get_logger(__name__)


class AccountInfo:
    """Information about a single BIP44 account"""
    
    def __init__(self, index: int, name: str = None, keystore: BIP32_KeyStore = None):
        self.index = index
        self.name = name or f"Account {index}"
        self.keystore = keystore
        self.creation_time = None
        self.color = None  # For UI display
        self.balance = 0
        self.receiving_addresses = []
        self.change_addresses = []
        
    def to_dict(self) -> Dict:
        """Serialize account info for storage"""
        return {
            'index': self.index,
            'name': self.name,
            'creation_time': self.creation_time,
            'color': self.color,
        }
    
    @classmethod
    def from_dict(cls, data: Dict, keystore: BIP32_KeyStore = None):
        """Deserialize account info from storage"""
        account = cls(data['index'], data['name'], keystore)
        account.creation_time = data.get('creation_time')
        account.color = data.get('color')
        return account


class MultiAccountWallet(Deterministic_Wallet):
    """
    Multi-account wallet supporting multiple BIP44 accounts.
    Each account has its own derivation path: m/44'/5'/account'/change/address_index
    """
    
    wallet_type = 'multi_account'
    
    def __init__(self, db, storage, *, config):
        self.accounts = {}  # type: Dict[int, AccountInfo]
        self.current_account = 0
        self._account_lock = threading.RLock()
        
        # Initialize with existing accounts or create account 0
        self._load_accounts_from_db(db)
        
        super().__init__(db, storage, config=config)
        
        # Ensure we have at least one account
        if not self.accounts:
            self.add_account(0, "Main Account")
    
    def _load_accounts_from_db(self, db):
        """Load account information from database"""
        accounts_data = db.get('accounts', {})
        master_keystore = db.get('keystore')
        
        for account_index, account_data in accounts_data.items():
            account_index = int(account_index)
            
            # Create account-specific keystore
            if master_keystore:
                account_keystore = self._create_account_keystore(master_keystore, account_index)
                account = AccountInfo.from_dict(account_data, account_keystore)
                self.accounts[account_index] = account
    
    def _create_account_keystore(self, master_keystore_data: Dict, account_index: int) -> BIP32_KeyStore:
        """Create a keystore for a specific account"""
        # Create a copy of the master keystore with modified derivation path
        account_keystore_data = master_keystore_data.copy()
        
        # Modify the derivation path to include account index
        # Standard path: m/44'/5'/0' becomes m/44'/5'/account'
        derivation = account_keystore_data.get('derivation', "m/44'/5'/0'")
        
        # Replace the account part (third component) with our account index
        parts = derivation.split('/')
        if len(parts) >= 4 and parts[3].endswith("'"):
            parts[3] = f"{account_index}'"
            account_keystore_data['derivation'] = '/'.join(parts)
        
        # Create the keystore
        from .keystore import from_keystore
        return from_keystore(account_keystore_data)
    
    def add_account(self, account_index: int = None, name: str = None) -> int:
        """
        Add a new account to the wallet.
        
        Args:
            account_index: Specific account index, or None for next available
            name: Account name
            
        Returns:
            The account index that was created
        """
        with self._account_lock:
            if account_index is None:
                # Find next available account index
                account_index = max(self.accounts.keys(), default=-1) + 1
            
            if account_index in self.accounts:
                raise ValueError(f"Account {account_index} already exists")
            
            # Create account keystore
            master_keystore_data = self.db.get('keystore')
            if not master_keystore_data:
                raise ValueError("No master keystore found")
            
            account_keystore = self._create_account_keystore(master_keystore_data, account_index)
            
            # Create account info
            account = AccountInfo(account_index, name, account_keystore)
            self.accounts[account_index] = account
            
            # Save to database
            self._save_accounts_to_db()
            
            # Generate initial addresses for the new account
            self._generate_account_addresses(account_index)
            
            _logger.info(f"Added account {account_index}: {name}")
            return account_index
    
    def _save_accounts_to_db(self):
        """Save account information to database"""
        accounts_data = {}
        for account_index, account in self.accounts.items():
            accounts_data[str(account_index)] = account.to_dict()
        
        self.db.put('accounts', accounts_data)
        self.db.put('current_account', self.current_account)
    
    def _generate_account_addresses(self, account_index: int, count: int = 20):
        """Generate initial addresses for an account"""
        account = self.accounts.get(account_index)
        if not account or not account.keystore:
            return
        
        # Generate receiving addresses
        for i in range(count):
            try:
                address = self.derive_address(account_index, 0, i)  # change=0 for receiving
                account.receiving_addresses.append(address)
            except Exception as e:
                _logger.error(f"Failed to generate receiving address {i} for account {account_index}: {e}")
        
        # Generate change addresses
        for i in range(count):
            try:
                address = self.derive_address(account_index, 1, i)  # change=1 for change
                account.change_addresses.append(address)
            except Exception as e:
                _logger.error(f"Failed to generate change address {i} for account {account_index}: {e}")
    
    def derive_address(self, account_index: int, change: int, address_index: int) -> str:
        """
        Derive address for specific account, change, and address index.
        
        Args:
            account_index: BIP44 account index
            change: 0 for receiving, 1 for change
            address_index: Address index within the chain
            
        Returns:
            Bitcoin address string
        """
        account = self.accounts.get(account_index)
        if not account or not account.keystore:
            raise ValueError(f"Account {account_index} not found")
        
        # Use the account's keystore to derive the address
        pubkey = account.keystore.derive_pubkey(change, address_index)
        return bitcoin.pubkey_to_address(self.txin_type, pubkey)
    
    def get_current_account(self) -> int:
        """Get the currently active account index"""
        return self.current_account
    
    def set_current_account(self, account_index: int):
        """Set the currently active account"""
        if account_index not in self.accounts:
            raise ValueError(f"Account {account_index} does not exist")
        
        self.current_account = account_index
        self._save_accounts_to_db()
        _logger.info(f"Switched to account {account_index}")
    
    def get_account_info(self, account_index: int) -> Optional[AccountInfo]:
        """Get information about a specific account"""
        return self.accounts.get(account_index)
    
    def get_all_accounts(self) -> Dict[int, AccountInfo]:
        """Get all accounts"""
        return self.accounts.copy()
    
    def get_account_balance(self, account_index: int) -> int:
        """Get balance for a specific account"""
        account = self.accounts.get(account_index)
        if not account:
            return 0
        
        # Calculate balance from addresses belonging to this account
        balance = 0
        for addr in account.receiving_addresses + account.change_addresses:
            balance += self.get_addr_balance(addr)[0]  # confirmed balance
        
        return balance
    
    def get_total_balance(self) -> int:
        """Get total balance across all accounts"""
        total = 0
        for account_index in self.accounts:
            total += self.get_account_balance(account_index)
        return total
    
    def discover_accounts(self, gap_limit: int = 20) -> List[int]:
        """
        Discover used accounts by checking for transaction history.
        Implements BIP44 account discovery.
        
        Args:
            gap_limit: Number of consecutive empty accounts to check
            
        Returns:
            List of discovered account indices
        """
        discovered = []
        empty_count = 0
        account_index = 0
        
        while empty_count < gap_limit:
            # Check if this account has any transaction history
            if self._account_has_history(account_index):
                discovered.append(account_index)
                empty_count = 0
                
                # Create the account if it doesn't exist
                if account_index not in self.accounts:
                    self.add_account(account_index, f"Account {account_index}")
            else:
                empty_count += 1
            
            account_index += 1
        
        return discovered
    
    def _account_has_history(self, account_index: int) -> bool:
        """Check if an account has any transaction history"""
        # Generate a few addresses for this account and check for history
        try:
            for change in [0, 1]:  # receiving and change
                for addr_index in range(20):  # check first 20 addresses
                    try:
                        address = self.derive_address(account_index, change, addr_index)
                        if self.db.get_addr_history(address):
                            return True
                    except:
                        continue
        except:
            pass
        
        return False
    
    # Override wallet methods to work with current account
    
    def get_receiving_addresses(self, *, slice_start=None, slice_stop=None):
        """Get receiving addresses for current account"""
        account = self.accounts.get(self.current_account)
        if not account:
            return []
        
        addresses = account.receiving_addresses
        if slice_start is not None or slice_stop is not None:
            addresses = addresses[slice_start:slice_stop]
        
        return addresses
    
    def get_change_addresses(self, *, slice_start=None, slice_stop=None):
        """Get change addresses for current account"""
        account = self.accounts.get(self.current_account)
        if not account:
            return []
        
        addresses = account.change_addresses
        if slice_start is not None or slice_stop is not None:
            addresses = addresses[slice_start:slice_stop]
        
        return addresses
    
    def get_unused_address(self):
        """Get unused receiving address for current account"""
        account = self.accounts.get(self.current_account)
        if not account:
            return None
        
        # Find first unused address
        for addr in account.receiving_addresses:
            if not self.db.get_addr_history(addr):
                return addr
        
        # Generate new address if all are used
        new_index = len(account.receiving_addresses)
        try:
            new_addr = self.derive_address(self.current_account, 0, new_index)
            account.receiving_addresses.append(new_addr)
            return new_addr
        except Exception as e:
            _logger.error(f"Failed to generate new address: {e}")
            return None
    
    def is_account_address(self, address: str, account_index: int) -> bool:
        """Check if an address belongs to a specific account"""
        account = self.accounts.get(account_index)
        if not account:
            return False
        
        return address in (account.receiving_addresses + account.change_addresses)


# Register the multi-account wallet type
from .wallet import register_wallet_type, register_constructor

register_wallet_type('multi_account')
register_constructor('multi_account', MultiAccountWallet)