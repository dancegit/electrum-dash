#!/bin/bash
# Phase 1 Test Execution Script
# Executes OAuth2 and Dropbox integration tests

set -e

echo "==================================="
echo "Phase 1 Test Execution Starting"
echo "==================================="
echo "Time: $(date)"
echo ""

# Activate virtual environment
source test-venv/bin/activate

# Fetch latest changes
echo "Fetching latest changes..."
git fetch origin

# Function to run specific test category
run_test_category() {
    local category=$1
    local test_path=$2
    
    echo ""
    echo "Running $category tests..."
    echo "-----------------------------------"
    
    if [ -f "$test_path" ] || [ -d "$test_path" ]; then
        python -m pytest -v \
            -c .test-config/pytest.ini \
            --junitxml=test-results/${category}_$(date +%Y%m%d_%H%M%S).xml \
            --html=test-results/${category}_$(date +%Y%m%d_%H%M%S).html \
            --self-contained-html \
            "$test_path"
        
        echo "✓ $category tests completed"
    else
        echo "⚠ $category tests not found at: $test_path"
    fi
}

# Phase 1 Test Execution Order
echo ""
echo "Test Execution Plan:"
echo "1. OAuth2 Unit Tests"
echo "2. Encryption/Decryption Unit Tests" 
echo "3. Dropbox API Integration Tests"
echo "4. Network Failure Tests"
echo ""

# Run tests in order
run_test_category "oauth2_unit" "electrum_dash/tests/test_dropbox_oauth2.py"
run_test_category "encryption_unit" "electrum_dash/tests/test_dropbox_encryption.py"
run_test_category "dropbox_integration" "electrum_dash/tests/test_dropbox_integration.py"
run_test_category "network_failure" "electrum_dash/tests/test_dropbox_network.py"

# Generate summary report
echo ""
echo "==================================="
echo "Test Execution Summary"
echo "==================================="

# Count results
if [ -d "test-results" ]; then
    echo "Test reports generated in test-results/"
    ls -la test-results/*.xml 2>/dev/null | wc -l | xargs echo "XML reports:"
    ls -la test-results/*.html 2>/dev/null | wc -l | xargs echo "HTML reports:"
fi

echo ""
echo "Phase 1 test execution completed at $(date)"

# Deactivate virtual environment
deactivate