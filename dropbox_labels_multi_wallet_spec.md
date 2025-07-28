# Implementation Plan for Dropbox Labeling and Multi-Wallet Display

## 1. Dropbox Labeling Feature

### Overview
Implement a Dropbox-based label sync feature similar to Trezor Suite's implementation, allowing users to sync their wallet labels across devices using encrypted storage in Dropbox. This will support both regular wallets and hardware wallets (especially Trezor) with proper encryption standards.

### Implementation Steps

1. **Create Dropbox Labels Plugin** (`electrum_dash/plugins/dropbox_labels/`)
   - Create new plugin directory with `__init__.py`, `dropbox_labels.py`, and `qt.py`
   - Implement OAuth2 authentication flow for Dropbox
   - Use AES-256-GCM encryption (matching Trezor Suite's implementation)
   - Store encrypted labels in `/Apps/Electrum-Dash/` folder in Dropbox
   - Support `.mtdt` file format for compatibility with Trezor Suite

2. **Implement SLIP-0015 Support for Trezor Integration**
   - Add SLIP-0015 key derivation for Trezor hardware wallets
   - Implement master key derivation using CipherKeyValue (SLIP-0011)
   - Generate account-specific keys for each BIP44 account
   - Use HMAC to derive filenames and encryption keys
   - Store files as hex-encoded account fingerprint with `.mtdt` extension

3. **Modify Existing Labels Infrastructure**
   - Refactor `electrum_dash/plugins/labels/labels.py` to create a base class for label sync providers
   - Extract common encryption/decryption logic into a shared module
   - Support multiple label sync backends (existing server, Dropbox, Google Drive, local)
   - Add provider-specific encryption methods (standard vs SLIP-0015)

4. **Add Dropbox API Integration**
   - Use `dropbox` Python package for API communication
   - Implement file upload/download for label sync
   - Handle OAuth2 token storage securely in wallet configuration
   - Add conflict resolution for simultaneous edits
   - Support reading existing Trezor Suite label files from `/Apps/TREZOR/`

5. **Hardware Wallet Integration**
   - Add Trezor confirmation dialog for label encryption/decryption
   - Implement "ask_on_encrypt" and "ask_on_decrypt" parameters per SLIP-0015
   - Cache master key in memory with timeout for better UX
   - Support other hardware wallets with their specific encryption methods

6. **Update GUI Components**
   - Add Dropbox option to label sync settings in `electrum_dash/gui/qt/settings_dialog.py`
   - Create OAuth authorization dialog
   - Show sync status in status bar
   - Add manual sync button
   - Add import option for existing Trezor Suite labels
   - Show hardware wallet confirmation prompts when needed

7. **Security Considerations**
   - For software wallets: Derive encryption key from wallet's master public key
   - For hardware wallets: Use SLIP-0015 key derivation
   - Never store OAuth tokens in plaintext
   - Implement secure token refresh mechanism
   - Add option to export/backup encrypted label files
   - Ensure compatibility with Trezor Suite's security model

## 2. Multi-Wallet Display (Multiple BIP44 Accounts)

### Overview
Enable display and management of multiple BIP44 accounts (different derivation paths) within a single wallet interface, allowing users to organize funds in separate "accounts" from the same seed.

### Implementation Steps

1. **Extend Wallet Structure**
   - Modify `electrum_dash/wallet.py` to support multiple keystores with different derivation paths
   - Create new `MultiAccountWallet` class that manages multiple `BIP32_KeyStore` instances
   - Each account uses a different BIP44 account index (m/44'/5'/0', m/44'/5'/1', etc.)

2. **Update Database Schema**
   - Modify `electrum_dash/wallet_db.py` to store multiple account configurations
   - Add account metadata (name, color, creation date)
   - Ensure backward compatibility with existing single-account wallets

3. **GUI Updates for Account Management**
   - Add account switcher dropdown in main window toolbar
   - Create "Add Account" dialog for creating new BIP44 accounts
   - Display aggregate balance across all accounts in status bar
   - Add account overview screen showing all accounts and balances

4. **Modify Address Generation**
   - Update address generation to respect current account context
   - Ensure receiving addresses are generated from the correct account
   - Update change address logic for transactions

5. **Transaction Management**
   - Allow sending from specific accounts or combined accounts
   - Update coin selection to respect account boundaries (optional mixing)
   - Show account labels in transaction history

6. **Account Discovery**
   - Implement BIP44 account discovery algorithm on wallet restore
   - Scan for used accounts up to a gap limit
   - Show discovered accounts during restoration process

### Technical Details

**Dependencies to Add:**
- `dropbox>=11.36.0` - For Dropbox API integration
- `requests-oauthlib>=1.3.1` - For OAuth2 flow
- `pycryptodome>=3.15.0` - For AES-256-GCM encryption (if not already present)

**File Structure Changes:**
```
electrum_dash/plugins/
├── dropbox_labels/
│   ├── __init__.py
│   ├── dropbox_labels.py
│   ├── qt.py
│   ├── auth.py
│   └── slip15.py (SLIP-0015 implementation)
└── labels/
    ├── base.py (new - extracted base class)
    └── ... (existing files)
```

**Configuration Changes:**
- Add `dropbox_oauth_token` to wallet config
- Add `label_sync_provider` setting (server/dropbox/gdrive/local)
- Add `label_encryption_method` setting (standard/slip15)
- Add `multi_account_enabled` flag
- Store account metadata in `accounts` section
- Add `trezor_label_master_key` cache with expiry

**Trezor Suite Compatibility:**
- File format: `.mtdt` extension
- Dropbox locations: 
  - Trezor Suite: `/Apps/TREZOR/`
  - Electrum-Dash: `/Apps/Electrum-Dash/`
- Encryption: AES-256-GCM with SLIP-0015 key derivation
- File naming: Hex-encoded account fingerprint + `.mtdt`

**UI Flow for Dropbox:**
1. User enables Dropbox sync in settings
2. OAuth authorization popup opens
3. User authorizes in browser
4. Token stored encrypted in wallet
5. Initial sync performed
6. Background sync on label changes

**UI Flow for Multi-Account:**
1. User clicks "Add Account" button
2. Dialog shows next available account index
3. User can set custom account name
4. New account created with next derivation path
5. Account appears in dropdown selector
6. User can switch between accounts freely

### Implementation Priority and Phases

**Phase 1: Basic Dropbox Integration**
- Implement OAuth2 flow and basic file operations
- Add standard encryption for software wallets
- Create UI for enabling/disabling Dropbox sync

**Phase 2: Trezor Suite Compatibility**
- Implement SLIP-0015 key derivation
- Add hardware wallet support with device confirmations
- Enable import of existing Trezor Suite labels
- Test cross-compatibility with Trezor Suite

**Phase 3: Multi-Account Support**
- Implement multiple BIP44 account management
- Update UI to show account switcher
- Add account discovery on wallet restore

**Phase 4: Advanced Features**
- Add Google Drive support
- Implement conflict resolution UI
- Add batch operations for labels
- Create backup/export functionality

This implementation plan provides a secure, user-friendly way to add both Dropbox labeling and multi-wallet display features to Electrum-Dash, with full compatibility for Trezor Suite labels and support for hardware wallet security models.