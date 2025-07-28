"""
Test Infrastructure Package
Provides comprehensive testing utilities for Dropbox integration
"""

from .oauth2_test_harness import (
    OAuth2TestHarness,
    oauth2_harness,
    mock_dropbox_oauth2,
    oauth2_test_credentials
)

from .dropbox_api_mocks import (
    DropboxAPIMocks
)

from .encryption_test_harness import (
    EncryptionTestHarness,
    encryption_harness,
    encrypted_wallet_data,
    encryption_test_cases
)

from .network_failure_simulator import (
    NetworkFailureSimulator,
    NetworkConditionContext,
    NetworkTestScenarios,
    network_simulator,
    timeout_network,
    flaky_network,
    slow_network
)

from .trezor_emulator import (
    TrezorDevice,
    TrezorEmulator,
    TrezorConfirmationFlow,
    SLIP0015,
    TrezorTestFixtures
)

from .hardware_wallet_test_harness import (
    HardwareWalletTestHarness,
    SLIP0015TestSuite,
    HardwareConfirmationTestSuite,
    CrossAppCompatibilityTests,
    HardwareWalletPerformanceTests,
    hardware_wallet_harness,
    trezor_device,
    slip0015_suite,
    confirmation_suite,
    performance_suite
)

__all__ = [
    # OAuth2
    'OAuth2TestHarness',
    'oauth2_harness',
    'mock_dropbox_oauth2',
    'oauth2_test_credentials',
    
    # Dropbox API
    'DropboxAPIMocks',
    
    # Encryption
    'EncryptionTestHarness', 
    'encryption_harness',
    'encrypted_wallet_data',
    'encryption_test_cases',
    
    # Network
    'NetworkFailureSimulator',
    'NetworkConditionContext',
    'NetworkTestScenarios',
    'network_simulator',
    'timeout_network',
    'flaky_network',
    'slow_network',
    
    # Hardware Wallet
    'TrezorDevice',
    'TrezorEmulator',
    'TrezorConfirmationFlow',
    'SLIP0015',
    'TrezorTestFixtures',
    'HardwareWalletTestHarness',
    'SLIP0015TestSuite',
    'HardwareConfirmationTestSuite',
    'CrossAppCompatibilityTests',
    'HardwareWalletPerformanceTests',
    'hardware_wallet_harness',
    'trezor_device',
    'slip0015_suite',
    'confirmation_suite',
    'performance_suite'
]