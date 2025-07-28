# Dropbox Labels Plugin - Implementation Notes

## Phase 1 & 2 Complete Implementation Summary

### Architecture Overview

The plugin is structured as follows:
```
electrum_dash/plugins/dropbox_labels/
├── __init__.py           # Plugin metadata
├── dropbox_labels.py     # Core plugin logic
├── qt.py                # Qt GUI integration
├── auth.py              # OAuth2 implementation with PKCE
├── encryption.py        # AES-256-GCM for .mtdt format
├── slip15.py            # SLIP-0015 hardware wallet support
└── config.py            # Configuration constants
```

### Key Design Decisions

#### 1. Dual Encryption Support
- **Software Wallets**: SHA256-derived key from wallet fingerprint
- **Hardware Wallets**: SLIP-0015 CipherKeyValue with master key caching
- Automatic detection and fallback mechanism

#### 2. File Format Compatibility
- Full .mtdt format support (nonce || ciphertext || tag)
- AES-256-GCM encryption matching Trezor Suite
- JSON structure: `{"version": 1, "labels": {...}}`

#### 3. OAuth2 Security
- PKCE flow implementation for enhanced security
- Encrypted token storage in wallet database
- Token refresh support (not fully implemented yet)

#### 4. SLIP-0015 Implementation Details
- Master key: `encrypt_keyvalue([], "SLIP-0015", sha256("SLIP-0015"))`
- Account keys: HMAC-SHA256 derivation
- Filename: HMAC-SHA256 fingerprint + ".mtdt"
- 5-minute key cache to reduce hardware prompts

### Integration Points

#### Hardware Wallet Detection
```python
def is_hardware_wallet(wallet):
    return (hasattr(wallet, 'keystore') and 
            hasattr(wallet.keystore, 'plugin') and
            hasattr(wallet.keystore.plugin, 'get_client'))
```

#### Trezor Client Access
The plugin accesses Trezor through:
1. `wallet.keystore.plugin` - Gets hardware wallet plugin
2. `plugin.get_client()` - Gets Trezor client
3. `client.encrypt_keyvalue()` - SLIP-0015 operations

### Testing Considerations

1. **Mock Hardware Wallet**:
   - Need to mock `encrypt_keyvalue` method
   - Should return consistent 32-byte keys
   - Must handle ask_on_encrypt/decrypt flags

2. **Dropbox API Mocking**:
   - Mock `files_upload`, `files_download`, `files_list_folder`
   - Simulate OAuth2 flow for tests

3. **Encryption Testing**:
   - Verify AES-256-GCM roundtrip
   - Test .mtdt format compatibility
   - Ensure proper key derivation

### Phase 3 Preparation

For Multi-Account Support, the foundation is already in place:
- `get_account_index()` method (currently returns 0)
- Account-specific key derivation in SLIP-0015
- Filename generation supports account_index parameter

Next steps will involve:
1. Extracting account index from wallet derivation path
2. UI for account switching
3. Multiple keystore management in wallet

### Performance Notes

- Label sync is currently synchronous (download all, modify, upload all)
- Could be optimized with differential sync in future
- Hardware key caching prevents repeated device prompts

### Security Considerations

1. OAuth tokens are encrypted before storage
2. No plaintext credentials in code (uses config.py)
3. Hardware wallet keys never leave device
4. Proper error handling prevents key leakage in logs

### Known Limitations

1. Token refresh not fully implemented
2. Account index extraction needs wallet structure analysis
3. Conflict resolution for simultaneous edits not implemented
4. No offline caching of labels

### Dependencies

- `dropbox>=11.36.0` - Dropbox SDK
- `cryptography>=3.4.8` - AES-256-GCM support
- `requests-oauthlib>=1.3.1` - OAuth2 support
- Existing Electrum dependencies (aiohttp, etc.)

## Next Phase: Multi-Account Support

The groundwork is ready for Phase 3. Key areas to implement:
1. Wallet structure modification for multiple accounts
2. UI components for account management
3. Account discovery algorithm
4. Integration with existing address generation