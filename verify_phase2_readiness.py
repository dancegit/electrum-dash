#!/usr/bin/env python3
"""
Phase 2 Hardware Wallet Test Infrastructure Verification
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== Phase 2 Hardware Wallet Test Infrastructure Check ===")
print()

# Check virtual environment
in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
print(f"{'✓' if in_venv else '✗'} Virtual environment active")

# Test infrastructure imports
try:
    import test_infrastructure
    print("✓ Test infrastructure package loaded")
    
    # Test Trezor emulator
    emulator = test_infrastructure.TrezorEmulator()
    print("✓ Trezor emulator initialized")
    
    # Test device features
    features = emulator.call("GetFeatures")
    print(f"✓ Trezor device ID: {features['device_id']}")
    print(f"✓ Firmware version: {features['major_version']}.{features['minor_version']}.{features['patch_version']}")
    
    # Test SLIP-0015 implementation
    slip0015 = test_infrastructure.SLIP0015()
    test_key = slip0015.derive_wallet_encryption_key(b"test_master_key")
    print(f"✓ SLIP-0015 key derivation working (key length: {len(test_key)} bytes)")
    
    # Test hardware wallet harness
    harness = test_infrastructure.HardwareWalletTestHarness()
    device = harness.connect_device("trezor")
    print(f"✓ Hardware wallet connected: {device['label']}")
    
    # Test confirmation flow
    conf_flow = test_infrastructure.TrezorConfirmationFlow(emulator)
    conf_id = conf_flow.request_confirmation("test", {"action": "test"})
    confirmed = conf_flow.confirm(conf_id)
    print(f"✓ Confirmation flow working: {confirmed}")
    
    # Test fixtures
    fixtures = test_infrastructure.TrezorTestFixtures()
    wallets = fixtures.get_test_wallets()
    print(f"✓ Test fixtures available: {len(wallets)} test wallets")
    
    # Test performance suite
    perf_tests = test_infrastructure.HardwareWalletPerformanceTests(harness)
    print("✓ Performance test suite ready")
    
    # Test compatibility tests
    compat_tests = test_infrastructure.CrossAppCompatibilityTests()
    print("✓ Cross-app compatibility tests ready")
    
    print("\n" + "="*50)
    print("✅ Phase 2 Infrastructure READY!")
    print("\nAvailable test suites:")
    print("- SLIP-0015 key derivation tests")
    print("- Hardware confirmation flow tests")
    print("- Cross-app compatibility tests (.mtdt files)")
    print("- Performance benchmarking")
    print("- Trezor device emulation")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)