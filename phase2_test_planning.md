# Phase 2 Test Planning - Trezor Suite Compatibility

## Overview
Phase 2 focuses on hardware wallet integration and Trezor Suite compatibility, implementing SLIP-0015 key derivation and .mtdt file format support.

## Test Scope for Phase 2

### 1. SLIP-0015 Key Derivation Testing

#### Test Cases:
- **SLIP-001**: Verify master key derivation using CipherKeyValue
- **SLIP-002**: Test account-specific key generation
- **SLIP-003**: Verify HMAC filename generation
- **SLIP-004**: Test hex-encoded account fingerprint generation
- **SLIP-005**: Validate key derivation matches Trezor Suite

#### Test Data Needed:
- Known test vectors from Trezor Suite
- Multiple BIP44 account paths
- Expected .mtdt filenames

### 2. Hardware Wallet Integration Testing

#### Trezor Device Tests:
- **HW-001**: Test CipherKeyValue call with user confirmation
- **HW-002**: Verify "ask_on_encrypt" parameter handling
- **HW-003**: Verify "ask_on_decrypt" parameter handling  
- **HW-004**: Test master key caching with timeout
- **HW-005**: Test device disconnection handling

#### Other Hardware Wallets:
- **HW-006**: Ledger compatibility check
- **HW-007**: KeepKey compatibility check
- **HW-008**: Fallback to standard encryption for unsupported devices

### 3. .mtdt File Format Testing

#### File Format Tests:
- **FMT-001**: Verify .mtdt file structure matches Trezor Suite
- **FMT-002**: Test file naming (hex fingerprint + .mtdt)
- **FMT-003**: Verify file location (/Apps/TREZOR/ compatibility)
- **FMT-004**: Test cross-compatibility with actual Trezor Suite files
- **FMT-005**: Verify bidirectional sync (read/write Trezor files)

### 4. Multi-Account Support Testing

#### Account Management:
- **MA-001**: Test multiple BIP44 account creation
- **MA-002**: Verify separate encryption keys per account
- **MA-003**: Test account discovery on restore
- **MA-004**: Verify account-specific label storage
- **MA-005**: Test switching between accounts

### 5. Integration Testing

#### End-to-End Tests:
- **E2E-001**: Complete flow with Trezor device
- **E2E-002**: Import existing Trezor Suite labels
- **E2E-003**: Export labels readable by Trezor Suite
- **E2E-004**: Multi-device sync verification
- **E2E-005**: Conflict resolution between devices

## Test Environment Requirements

### Hardware:
- Trezor One device
- Trezor Model T device
- Ledger Nano S/X (optional)
- KeepKey (optional)

### Software:
- Trezor Suite installed for comparison
- Test Dropbox account with existing .mtdt files
- Multiple test wallets with different accounts

### Test Data:
```
/Apps/TREZOR/
├── a1b2c3d4e5f6.mtdt  # Account 0 labels
├── f6e5d4c3b2a1.mtdt  # Account 1 labels
└── 1a2b3c4d5e6f.mtdt  # Account 2 labels
```

## Security Test Focus

### Hardware Wallet Security:
- No private keys in memory
- User confirmation for all operations
- Secure communication with device
- No key material logged

### SLIP-0015 Compliance:
- Correct key derivation path
- Proper HMAC usage
- No key reuse between accounts
- Deterministic but unpredictable filenames

## Performance Benchmarks

### Target Metrics:
- Hardware wallet operation: <3s per encryption/decryption
- Account switching: <1s
- Label sync with 100+ labels: <5s
- Multi-account discovery: <10s for 10 accounts

## Test Automation Strategy

### Unit Tests:
- Mock hardware wallet responses
- Test SLIP-0015 algorithm independently
- Verify .mtdt file parsing/generation

### Integration Tests:
- Use hardware wallet simulators where possible
- Test with real Trezor Suite files
- Automated Dropbox sync testing

### Manual Tests:
- Physical hardware wallet testing
- Cross-application compatibility
- User experience validation

## Success Criteria for Phase 2

1. **SLIP-0015 Compliance**: 100% match with Trezor Suite key derivation
2. **File Compatibility**: Can read/write Trezor Suite .mtdt files
3. **Hardware Support**: Works with Trezor One/T, graceful fallback for others
4. **Multi-Account**: Supports 10+ accounts with separate keys
5. **Security**: No key material exposure, proper user confirmations
6. **Performance**: Meets all benchmark targets

## Risk Areas

1. **Hardware Communication**: Device connection issues
2. **Compatibility**: Trezor Suite format changes
3. **Performance**: Hardware operations may be slow
4. **User Experience**: Too many confirmation prompts

## Phase 2 Test Schedule

1. **Week 1**: SLIP-0015 implementation testing
2. **Week 2**: Hardware wallet integration
3. **Week 3**: .mtdt format and compatibility
4. **Week 4**: Multi-account support
5. **Week 5**: End-to-end integration testing
6. **Week 6**: Performance and security validation

---
*Phase 2 Test Plan prepared by Tester Agent*
*Ready for implementation once Phase 1 is complete*