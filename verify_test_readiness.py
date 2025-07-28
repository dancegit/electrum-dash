#!/usr/bin/env python3
"""Verify test infrastructure readiness"""

import sys
import os

print("=== Test Infrastructure Readiness Check ===")
print()

# Check virtual environment
if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("✓ Running in virtual environment")
else:
    print("✗ Not in virtual environment!")
    print("  Run: source test-venv/bin/activate")

# Check required modules
modules_to_check = [
    ('pytest', 'Test runner'),
    ('pytest_cov', 'Coverage plugin'),
    ('pytest_html', 'HTML reports'),
    ('xdist', 'Parallel execution'),
    ('requests_mock', 'API mocking'),
    ('responses', 'HTTP mocking'),
    ('cryptography', 'Encryption support')
]

print("\nModule availability:")
all_good = True
for module_name, description in modules_to_check:
    try:
        __import__(module_name)
        print(f"✓ {description} ({module_name})")
    except ImportError as e:
        print(f"✗ {description} ({module_name}) - {e}")
        all_good = False

# Check test files
print("\nTest files:")
test_dir = "electrum_dash/tests"
if os.path.exists(test_dir):
    test_files = [f for f in os.listdir(test_dir) if f.startswith('test_dropbox')]
    for test_file in sorted(test_files):
        print(f"✓ {test_file}")
else:
    print(f"✗ Test directory not found: {test_dir}")
    all_good = False

# Check infrastructure modules
print("\nTest infrastructure:")
try:
    sys.path.insert(0, '.')
    import test_infrastructure
    print("✓ Test infrastructure package loaded")
    
    # Try to instantiate key classes
    harness = test_infrastructure.OAuth2TestHarness()
    print("✓ OAuth2 test harness ready")
    
    mocks = test_infrastructure.DropboxAPIMocks()
    print("✓ Dropbox API mocks ready")
    
    enc = test_infrastructure.EncryptionTestHarness()
    print("✓ Encryption test harness ready")
    
    net = test_infrastructure.NetworkFailureSimulator()
    print("✓ Network failure simulator ready")
    
except Exception as e:
    print(f"✗ Infrastructure error: {e}")
    all_good = False

print("\n" + "="*40)
if all_good:
    print("✅ ALL SYSTEMS GO - Ready for test execution!")
else:
    print("❌ Issues detected - please fix before running tests")
    sys.exit(1)