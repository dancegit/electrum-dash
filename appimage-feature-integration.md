# AppImage Feature Integration Guide

## Ensuring New Features are Included in AppImage Build

This guide ensures that the Dropbox labeling and multi-wallet display features from the recent implementation spec are properly included in the AppImage build.

### Pre-Build Checklist

Before building the AppImage, verify these components exist:

#### 1. Dropbox Labeling Feature Files
Check for the plugin structure (when implemented):
```bash
# Expected structure
electrum_dash/plugins/dropbox_labels/
├── __init__.py
├── dropbox_labels.py
├── qt.py
├── auth.py
└── slip15.py
```

#### 2. Required Dependencies
Add to `contrib/deterministic-build/requirements.txt` if not present:
```
dropbox>=11.36.0
requests-oauthlib>=1.3.1
```

Note: pycryptodome should already be included for AES-256-GCM encryption.

#### 3. Multi-Wallet Display Code
Verify modifications in:
- `electrum_dash/wallet.py` - MultiAccountWallet class
- `electrum_dash/wallet_db.py` - Multiple account support
- `electrum_dash/gui/qt/` - UI components for account switching

### Build Verification Steps

After building the AppImage, verify features are included:

```bash
# Extract AppImage to inspect contents (optional)
./dist/Dash-Electrum-*.AppImage --appimage-extract

# Check for Dropbox plugin
ls squashfs-root/usr/lib/python3.10/site-packages/electrum_dash/plugins/

# Check for required dependencies
./dist/Dash-Electrum-*.AppImage -c "import dropbox; print(dropbox.__version__)"

# Clean up extracted files
rm -rf squashfs-root/
```

### Testing Feature Availability

1. **Run the AppImage**:
   ```bash
   ./dist/Dash-Electrum-*.AppImage -v
   ```

2. **Check Plugin Loading**:
   - Look for plugin initialization messages in verbose output
   - Navigate to Tools → Plugins to see available plugins

3. **Feature-Specific Tests**:
   - Dropbox Labels: Should appear in Preferences → Label Sync
   - Multi-Wallet: Should show account management options

### Troubleshooting Missing Features

If features don't appear in the AppImage:

1. **Check Plugin Registration**:
   Ensure plugins are registered in `electrum_dash/plugins/__init__.py`

2. **Verify Import Paths**:
   ```python
   # In the AppImage
   ./dist/Dash-Electrum-*.AppImage -c "
   import sys
   for path in sys.path:
       print(path)
   "
   ```

3. **Check for Import Errors**:
   ```bash
   ./dist/Dash-Electrum-*.AppImage -c "
   try:
       from electrum_dash.plugins import dropbox_labels
       print('Dropbox plugin importable')
   except Exception as e:
       print(f'Import error: {e}')
   "
   ```

### Development Workflow

For iterative development with AppImage:

1. Make code changes
2. Run quick build: `./build-appimage-test.sh`
3. Test specific feature
4. Repeat as needed

### Notes on Current Implementation Status

As of the latest master branch:
- The implementation spec for Dropbox labeling and multi-wallet display has been documented
- Actual implementation may be in progress or on feature branches
- The AppImage will include whatever code is present in the current branch

To build with a specific feature branch:
```bash
git checkout feature/dropbox-labels-multi-wallet  # or appropriate branch name
git merge master  # Include latest master changes
./build-appimage-test.sh
```