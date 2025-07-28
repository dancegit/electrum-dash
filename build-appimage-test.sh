#!/bin/bash
# Quick AppImage build script for testing Electrum-Dash with new features
# This script builds an AppImage including recent changes to master

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Electrum-Dash AppImage Builder ===${NC}"
echo "This script will build an AppImage for testing recent features"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker first:"
    echo "  sudo apt update && sudo apt install docker.io"
    echo "  sudo usermod -aG docker \$USER"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker daemon is not running${NC}"
    echo "Try: sudo systemctl start docker"
    exit 1
fi

# Get the current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${YELLOW}Current branch:${NC} $CURRENT_BRANCH"

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo -e "${YELLOW}Warning: You have uncommitted changes${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Ensure we have the latest master changes
echo -e "${GREEN}Fetching latest changes from master...${NC}"
git fetch origin master

# Option to merge master if not on master
if [ "$CURRENT_BRANCH" != "master" ]; then
    echo -e "${YELLOW}You're not on master branch${NC}"
    read -p "Would you like to merge latest master? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git merge origin/master --no-edit || {
            echo -e "${RED}Merge failed. Please resolve conflicts and try again.${NC}"
            exit 1
        }
    fi
fi

# Clean previous builds
echo -e "${GREEN}Cleaning previous builds...${NC}"
rm -rf dist/*.AppImage

# Check if Docker images exist
echo -e "${GREEN}Checking Docker images...${NC}"
if ! docker images | grep -q "electrum-dash-build-appimage"; then
    echo -e "${YELLOW}Docker images not found. They will be built automatically.${NC}"
fi

# Run the build
echo -e "${GREEN}Starting AppImage build...${NC}"
echo "This may take 10-30 minutes depending on your system..."
echo ""

# Execute the build script
if ./contrib/dash/actions/script-linux.sh; then
    echo ""
    echo -e "${GREEN}Build completed successfully!${NC}"
    
    # Find the built AppImage
    APPIMAGE=$(ls -1 dist/Dash-Electrum-*-x86_64.AppImage 2>/dev/null | head -n1)
    
    if [ -n "$APPIMAGE" ]; then
        echo -e "${GREEN}AppImage created:${NC} $APPIMAGE"
        echo ""
        echo "To run the AppImage:"
        echo "  chmod +x $APPIMAGE"
        echo "  ./$APPIMAGE"
        echo ""
        echo "To test with testnet:"
        echo "  ./$APPIMAGE --testnet"
        echo ""
        echo "To test new features:"
        echo "1. Dropbox Labels: Tools → Preferences → Label Sync → Dropbox"
        echo "2. Multi-Wallet: Look for 'Add Account' in wallet interface"
    else
        echo -e "${RED}Error: AppImage not found in dist/${NC}"
        exit 1
    fi
else
    echo -e "${RED}Build failed!${NC}"
    echo "Check the error messages above for details."
    exit 1
fi