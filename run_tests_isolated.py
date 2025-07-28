#!/usr/bin/env python3
"""
Isolated test runner for Phase 1 tests
Runs tests without full electrum dependencies
"""

import sys
import os
import subprocess
import json
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_test_file(test_file, result_dir):
    """Run a single test file and capture results"""
    basename = os.path.basename(test_file).replace('.py', '')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"\n{'='*60}")
    print(f"Running: {basename}")
    print(f"{'='*60}")
    
    # Create mock electrum_dash module structure
    mock_setup = """
import sys
import os

# Create mock electrum_dash module
class MockModule:
    def __getattr__(self, name):
        if name == 'tests':
            return type('tests', (), {'ElectrumTestCase': type('ElectrumTestCase', (unittest.TestCase,), {})})()
        elif name == 'plugins':
            return type('plugins', (), {
                'dropbox_labels': type('dropbox_labels', (), {
                    'oauth': type('oauth', (), {'DropboxOAuth': object})(),
                    'encryption': type('encryption', (), {
                        'AESGCMEncryption': object,
                        'TrezorSuiteFormat': object
                    })(),
                    'sync': type('sync', (), {'DropboxSync': object})()
                })()
            })()
        return type(name, (), {})()

if 'electrum_dash' not in sys.modules:
    sys.modules['electrum_dash'] = MockModule()
    sys.modules['electrum_dash.tests'] = MockModule().tests
    sys.modules['electrum_dash.plugins'] = MockModule().plugins
    sys.modules['electrum_dash.plugins.dropbox_labels'] = MockModule().plugins.dropbox_labels
    sys.modules['electrum_dash.plugins.dropbox_labels.oauth'] = MockModule().plugins.dropbox_labels.oauth
    sys.modules['electrum_dash.plugins.dropbox_labels.encryption'] = MockModule().plugins.dropbox_labels.encryption
    sys.modules['electrum_dash.plugins.dropbox_labels.sync'] = MockModule().plugins.dropbox_labels.sync

import unittest
"""
    
    # Run test with mock setup
    cmd = [
        sys.executable, "-m", "pytest", "-v",
        "--tb=short",
        f"--junitxml={result_dir}/{basename}_{timestamp}.xml",
        f"--html={result_dir}/{basename}_{timestamp}.html",
        "--self-contained-html",
        "-c", ".test-config/pytest.ini",
        test_file
    ]
    
    # Set environment to include our test infrastructure
    env = os.environ.copy()
    env['PYTHONPATH'] = f"{os.getcwd()}:{env.get('PYTHONPATH', '')}"
    
    # Write mock setup to temp file
    setup_file = f"/tmp/mock_electrum_{basename}.py"
    with open(setup_file, 'w') as f:
        f.write(mock_setup)
    
    # Run pytest with setup
    result = subprocess.run(
        [sys.executable, "-c", f"exec(open('{setup_file}').read()); import subprocess; subprocess.run({cmd})"],
        capture_output=True,
        text=True,
        env=env
    )
    
    print(f"\nSTDOUT:\n{result.stdout}")
    if result.stderr:
        print(f"\nSTDERR:\n{result.stderr}")
    
    # Clean up
    if os.path.exists(setup_file):
        os.remove(setup_file)
    
    return {
        "test_file": basename,
        "return_code": result.returncode,
        "passed": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr
    }

def main():
    """Main test runner"""
    print("Phase 1 Test Execution - Isolated Runner")
    print(f"Started at: {datetime.now()}")
    
    # Ensure result directory exists
    result_dir = "test-results"
    os.makedirs(result_dir, exist_ok=True)
    
    # Test files to run
    test_files = [
        "electrum_dash/tests/test_dropbox_oauth.py",
        "electrum_dash/tests/test_dropbox_encryption.py",
        "electrum_dash/tests/test_dropbox_security.py",
        "electrum_dash/tests/test_dropbox_sync_integration.py"
    ]
    
    # Run each test
    results = []
    for test_file in test_files:
        if os.path.exists(test_file):
            result = run_test_file(test_file, result_dir)
            results.append(result)
        else:
            print(f"WARNING: Test file not found: {test_file}")
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST EXECUTION SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['passed'])
    failed_tests = total_tests - passed_tests
    
    print(f"Total test files: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    # Save summary
    summary = {
        "execution_time": datetime.now().isoformat(),
        "total_files": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "results": results
    }
    
    summary_file = f"{result_dir}/test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nDetailed results saved to: {summary_file}")
    
    return 0 if failed_tests == 0 else 1

if __name__ == "__main__":
    sys.exit(main())