#!/bin/bash
# Test Runner Script with Virtual Environment
# Ensures tests run with proper dependencies

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -d "test-venv" ]; then
    echo -e "${GREEN}Activating test virtual environment...${NC}"
    source test-venv/bin/activate
else
    echo -e "${RED}Virtual environment not found! Please run setup first.${NC}"
    exit 1
fi

# Function to run tests
run_tests() {
    local category=$1
    local options=$2
    
    echo -e "${YELLOW}Running $category tests...${NC}"
    
    if [ "$category" == "all" ]; then
        python run_tests.py $options
    else
        python run_tests.py --categories $category $options
    fi
}

# Parse command line arguments
CATEGORY="all"
PARALLEL=true
INSTALL_DEPS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --category|-c)
            CATEGORY="$2"
            shift 2
            ;;
        --no-parallel)
            PARALLEL=false
            shift
            ;;
        --install-deps)
            INSTALL_DEPS=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --category, -c <name>  Test category to run (unit, dash_specific, wallet, network, integration)"
            echo "  --no-parallel          Disable parallel test execution"
            echo "  --install-deps         Install/update test dependencies"
            echo "  --help, -h             Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Install dependencies if requested
if [ "$INSTALL_DEPS" = true ]; then
    echo -e "${YELLOW}Installing/updating test dependencies...${NC}"
    pip install --upgrade pytest pytest-cov pytest-html pytest-json-report pytest-xdist pytest-mock responses requests-mock
fi

# Build options string
OPTIONS=""
if [ "$PARALLEL" = false ]; then
    OPTIONS="$OPTIONS --no-parallel"
fi

# Create test directories if they don't exist
mkdir -p test-results test-metrics .test-config

# Run the tests
echo -e "${GREEN}Starting test execution...${NC}"
echo "Category: $CATEGORY"
echo "Parallel: $PARALLEL"
echo ""

run_tests "$CATEGORY" "$OPTIONS"

# Check exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}"
else
    echo -e "\n${RED}✗ Some tests failed!${NC}"
fi

# Deactivate virtual environment
deactivate

exit $EXIT_CODE