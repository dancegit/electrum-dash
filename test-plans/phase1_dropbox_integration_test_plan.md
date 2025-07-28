# Phase 1: Basic Dropbox Integration Test Plan

## Overview
This test plan covers the basic Dropbox integration functionality for Electrum-Dash, focusing on OAuth2 authentication, basic file operations, and standard encryption for software wallets.

## Test Scope

### 1. OAuth2 Authentication Flow Testing

#### 1.1 Successful OAuth Flow
- **Test ID**: AUTH-001
- **Description**: Verify successful OAuth2 authentication flow
- **Test Steps**:
  1. User initiates Dropbox sync in settings
  2. OAuth authorization popup opens
  3. User authorizes in browser
  4. Callback is handled correctly
  5. Token is stored encrypted in wallet config
- **Expected Results**:
  - Authorization URL is correctly generated with proper scopes
  - Browser opens to Dropbox authorization page
  - Redirect URI is handled properly
  - Access token is received and stored
  - User sees success message
- **Test Type**: Integration

#### 1.2 OAuth Flow Cancellation
- **Test ID**: AUTH-002
- **Description**: Verify proper handling when user cancels OAuth
- **Test Steps**:
  1. User initiates Dropbox sync
  2. User cancels authorization in browser
  3. Application handles cancellation
- **Expected Results**:
  - No token is stored
  - User sees appropriate cancellation message
  - Settings remain unchanged
- **Test Type**: Integration

#### 1.3 Invalid OAuth Response
- **Test ID**: AUTH-003
- **Description**: Test handling of invalid OAuth responses
- **Test Cases**:
  - Missing access token
  - Invalid token format
  - Network errors during token exchange
- **Expected Results**:
  - Appropriate error messages shown
  - No partial state stored
  - User can retry authorization
- **Test Type**: Unit/Integration

#### 1.4 Token Refresh
- **Test ID**: AUTH-004
- **Description**: Verify automatic token refresh mechanism
- **Test Steps**:
  1. Simulate expired token
  2. Attempt API operation
  3. Verify refresh flow
- **Expected Results**:
  - Token is automatically refreshed
  - Operation continues without user intervention
  - New token is stored encrypted
- **Test Type**: Unit

### 2. Token Storage Security

#### 2.1 Encrypted Token Storage
- **Test ID**: SEC-001
- **Description**: Verify OAuth tokens are never stored in plaintext
- **Test Steps**:
  1. Complete OAuth flow
  2. Examine wallet configuration file
  3. Verify token encryption
- **Expected Results**:
  - Token is encrypted using wallet's encryption key
  - Raw token never appears in config files
  - Token can be decrypted only with wallet password
- **Test Type**: Security/Unit

#### 2.2 Token Deletion on Disable
- **Test ID**: SEC-002
- **Description**: Verify tokens are removed when sync is disabled
- **Test Steps**:
  1. Enable Dropbox sync
  2. Disable Dropbox sync
  3. Check token storage
- **Expected Results**:
  - Token is completely removed from storage
  - No residual authentication data remains
- **Test Type**: Unit

### 3. Basic File Operations

#### 3.1 File Upload
- **Test ID**: FILE-001
- **Description**: Test uploading encrypted label files to Dropbox
- **Test Steps**:
  1. Create labels in wallet
  2. Trigger sync operation
  3. Verify file upload to Dropbox
- **Expected Results**:
  - File is created in `/Apps/Electrum-Dash/` folder
  - File contains encrypted data
  - Upload confirmation received
- **Test Type**: Integration

#### 3.2 File Download
- **Test ID**: FILE-002
- **Description**: Test downloading and decrypting label files
- **Test Steps**:
  1. Place encrypted file in Dropbox
  2. Trigger sync operation
  3. Verify labels are imported
- **Expected Results**:
  - File is downloaded successfully
  - Labels are decrypted correctly
  - Local labels are updated
- **Test Type**: Integration

#### 3.3 File Conflict Resolution
- **Test ID**: FILE-003
- **Description**: Test handling of simultaneous edits
- **Test Steps**:
  1. Modify labels on two devices
  2. Sync both devices
  3. Verify conflict resolution
- **Expected Results**:
  - Conflicts are detected
  - Most recent changes are preserved
  - User is notified of conflicts
- **Test Type**: Integration

### 4. Standard Encryption (Software Wallets)

#### 4.1 AES-256-GCM Encryption
- **Test ID**: ENC-001
- **Description**: Verify correct AES-256-GCM encryption implementation
- **Test Steps**:
  1. Create test labels
  2. Encrypt using standard method
  3. Verify encryption parameters
- **Expected Results**:
  - 256-bit key is used
  - GCM mode is properly implemented
  - Authentication tag is included
  - Random IV for each encryption
- **Test Type**: Unit

#### 4.2 Key Derivation
- **Test ID**: ENC-002
- **Description**: Test encryption key derivation from wallet master public key
- **Test Steps**:
  1. Generate test wallet
  2. Derive encryption key
  3. Verify key consistency
- **Expected Results**:
  - Key is deterministically derived
  - Same wallet produces same key
  - Different wallets produce different keys
- **Test Type**: Unit

#### 4.3 Encryption/Decryption Round Trip
- **Test ID**: ENC-003
- **Description**: Verify data integrity through encryption/decryption
- **Test Data**:
  - Empty labels
  - Single label
  - 100+ labels
  - Special characters in labels
  - Unicode labels
- **Expected Results**:
  - All data is recovered exactly
  - No data corruption
  - Special characters preserved
- **Test Type**: Unit

### 5. UI Integration

#### 5.1 Settings Dialog
- **Test ID**: UI-001
- **Description**: Test Dropbox option in label sync settings
- **Test Steps**:
  1. Open settings dialog
  2. Navigate to label sync
  3. Select Dropbox option
- **Expected Results**:
  - Dropbox option is visible
  - Selection triggers OAuth flow
  - Status is displayed correctly
- **Test Type**: UI/Manual

#### 5.2 Sync Status Display
- **Test ID**: UI-002
- **Description**: Verify sync status in status bar
- **Test Steps**:
  1. Enable Dropbox sync
  2. Trigger sync operation
  3. Monitor status bar
- **Expected Results**:
  - Sync status is visible
  - Progress is shown during sync
  - Errors are displayed clearly
- **Test Type**: UI/Manual

#### 5.3 Manual Sync Button
- **Test ID**: UI-003
- **Description**: Test manual sync functionality
- **Test Steps**:
  1. Click manual sync button
  2. Verify sync operation
- **Expected Results**:
  - Sync starts immediately
  - UI feedback provided
  - Success/failure indicated
- **Test Type**: UI/Manual

### 6. Error Handling

#### 6.1 Network Errors
- **Test ID**: ERR-001
- **Description**: Test handling of network failures
- **Test Cases**:
  - No internet connection
  - Timeout during upload
  - Dropbox API errors
- **Expected Results**:
  - Graceful error handling
  - User-friendly error messages
  - Retry mechanism available
- **Test Type**: Integration

#### 6.2 Invalid File Format
- **Test ID**: ERR-002
- **Description**: Test handling of corrupted/invalid files
- **Test Steps**:
  1. Place invalid file in Dropbox folder
  2. Attempt sync
- **Expected Results**:
  - Error is logged
  - Sync continues with other files
  - User notified of issue
- **Test Type**: Unit

### 7. Performance Testing

#### 7.1 Sync Performance
- **Test ID**: PERF-001
- **Description**: Test sync performance with various label counts
- **Test Cases**:
  - 10 labels
  - 100 labels
  - 1000 labels
- **Metrics**:
  - Sync time
  - Memory usage
  - CPU usage
- **Expected Results**:
  - Linear scaling with label count
  - Acceptable performance for 100+ labels
- **Test Type**: Performance

## Test Data Requirements

### Test Wallets
- Software wallet with no labels
- Software wallet with existing labels
- Wallet with special characters in labels
- Wallet with 100+ labels

### Test Environment
- Local Dropbox API test environment
- Mock Dropbox API for unit tests
- Real Dropbox account for integration tests

## Automation Strategy

### Unit Tests
- Mock Dropbox API calls
- Test encryption/decryption functions
- Test key derivation
- Test error handling

### Integration Tests
- Use test Dropbox account
- Automated OAuth flow testing
- End-to-end sync testing

### Manual Tests
- UI interaction tests
- Visual verification
- User experience validation

## Success Criteria
- All test cases pass
- Code coverage >80% for new code
- No security vulnerabilities identified
- Performance meets requirements (sync <5s for 100 labels)
- All error conditions handled gracefully

## Test Execution Schedule
1. Unit tests: Run on every commit
2. Integration tests: Run on PR creation
3. Manual tests: Run before release
4. Security tests: Run weekly
5. Performance tests: Run nightly