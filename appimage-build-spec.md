# AppImage Build Specification for Electrum-Dash

This document provides instructions for building an AppImage of Electrum-Dash to test recent feature changes, including the Dropbox labeling and multi-wallet display features.

## Overview

The AppImage build process creates a portable Linux application that includes all dependencies, allowing you to test Electrum-Dash without installation. This is particularly useful for testing new features before release.

## Prerequisites

### System Requirements
- Linux system (Ubuntu 20.04+ recommended)
- Docker installed and running
- At least 4GB of free disk space
- Git

### Docker Installation
If Docker is not installed:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect
```

## Quick Build Method

### 1. Using the Provided Build Script

The fastest way to build an AppImage is using the existing build infrastructure:

```bash
# From the project root directory
./contrib/dash/actions/script-linux.sh
```

This script will:
1. Build the Docker image if it doesn't exist
2. Create a source distribution
3. Build the AppImage
4. Output the file to `dist/Dash-Electrum-{version}-x86_64.AppImage`

### 2. Manual Docker Build Process

If you need more control over the build process:

```bash
# Build the Docker images
cd contrib/build-linux/appimage
docker build -t electrum-dash-build-appimage:1.0 .

cd ../sdist
docker build -t electrum-dash-build-sdist:1.0 .

# Return to project root
cd ../../..

# Create source distribution
docker run --rm \
    -v $(pwd):/opt \
    -w /opt/ \
    -t electrum-dash-build-sdist:1.0 \
    /opt/contrib/build-linux/sdist/build.sh

# Build AppImage
docker run --rm \
    -v $(pwd):/opt \
    -w /opt/contrib/build-linux/appimage \
    -t electrum-dash-build-appimage:1.0 ./build.sh
```

## Building with Feature Branch

To build an AppImage from a specific feature branch:

```bash
# Checkout the feature branch
git checkout feature/dropbox-labels-multi-wallet

# Merge latest master (if needed)
git merge master

# Run the build
./contrib/dash/actions/script-linux.sh
```

## Build Output

The AppImage will be created in the `dist/` directory:
- Filename: `Dash-Electrum-{version}-x86_64.AppImage`
- Size: Approximately 100-150MB
- Architecture: x86_64

## Running the AppImage

```bash
# Make it executable
chmod +x dist/Dash-Electrum-*.AppImage

# Run it
./dist/Dash-Electrum-*.AppImage

# Run with testnet
./dist/Dash-Electrum-*.AppImage --testnet

# Run with debug output
./dist/Dash-Electrum-*.AppImage -v
```

## Testing New Features

### Dropbox Labeling Feature
1. Run the AppImage
2. Go to Tools → Preferences → Label Sync
3. Select "Dropbox" as the sync provider
4. Follow OAuth authorization flow
5. Test label synchronization

### Multi-Wallet Display
1. Create or restore a wallet
2. Look for "Add Account" option in the wallet interface
3. Create multiple BIP44 accounts
4. Test switching between accounts

## Troubleshooting

### Docker Permission Issues
```bash
# If you get permission denied errors
sudo docker run ... # Use sudo temporarily
# Or fix Docker group permissions
sudo usermod -aG docker $USER
newgrp docker
```

### Build Failures
1. Clean previous builds:
   ```bash
   rm -rf dist/
   docker system prune -f
   ```

2. Check Docker images:
   ```bash
   docker images | grep electrum-dash
   ```

3. Rebuild Docker images:
   ```bash
   docker rmi electrum-dash-build-appimage:1.0
   docker rmi electrum-dash-build-sdist:1.0
   ```

### Missing Dependencies
If the AppImage fails to run due to missing libraries:
```bash
# Check which libraries are missing
ldd dist/Dash-Electrum-*.AppImage

# Run with library debug info
LD_DEBUG=libs ./dist/Dash-Electrum-*.AppImage
```

## Development Build Modifications

### Adding New Dependencies
If the new features require additional Python packages:

1. Add to `contrib/deterministic-build/requirements.txt`
2. Ensure packages are pinned to specific versions with hashes
3. Test the build process

### Including New Plugins
For the Dropbox labeling plugin:
1. Ensure `electrum_dash/plugins/dropbox_labels/` is included
2. Check that OAuth dependencies are in requirements
3. Verify plugin appears in the built AppImage

## Build Time Estimates
- First build (including Docker image creation): 20-30 minutes
- Subsequent builds: 10-15 minutes
- Factors affecting build time:
  - Internet speed (downloading dependencies)
  - CPU performance
  - Available RAM

## Verification

After building, verify the AppImage:

```bash
# Check file size (should be 100-150MB)
ls -lh dist/Dash-Electrum-*.AppImage

# Verify it's executable
file dist/Dash-Electrum-*.AppImage

# Test basic functionality
./dist/Dash-Electrum-*.AppImage version

# Check included Python version
./dist/Dash-Electrum-*.AppImage -c "import sys; print(sys.version)"
```

## Security Notes

- The AppImage includes all dependencies, making it larger but more portable
- Built on Ubuntu 20.04 for maximum compatibility
- Uses deterministic builds for reproducibility
- Includes cryptographic libraries for wallet operations

## Additional Resources

- [AppImage Documentation](https://appimage.org/)
- [Electrum-Dash GitHub](https://github.com/pshenmic/electrum-dash)
- [Build Workflow](.github/workflows/build_release.yml)