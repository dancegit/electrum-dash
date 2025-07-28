# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Electrum-Dash is a lightweight Dash cryptocurrency wallet forked from the original Electrum Bitcoin wallet. It supports Dash-specific features like PrivateSend, InstantSend, and masternode management (DIP3).

The codebase is written in Python 3.10+ and uses Qt5 for the desktop GUI and Kivy for mobile interfaces.

## Common Development Commands

### Running the Application

```bash
# Run from source (development mode)
./electrum-dash

# Run with testnet
./electrum-dash --testnet

# Run GUI
./electrum-dash gui

# Run daemon
./electrum-dash daemon -d
```

### Testing

```bash
# Run tests using tox
tox

# Run tests directly with pytest
python -m pytest -v

# Run specific test module
python -m pytest electrum_dash/tests/test_dash_tx.py -v
```

### Building

```bash
# Build source distribution
python setup.py sdist --format=zip,gztar

# Build for specific platforms (uses Docker containers)
./contrib/dash/build.sh

# Build AppImage for Linux
./contrib/dash/actions/script-linux.sh

# Build DMG for macOS
./contrib/dash/actions/script-osx.sh

# Build Windows installer
./contrib/dash/actions/script-wine.sh

# Build Android APK
./contrib/dash/actions/script-linux-apk.sh
```

### Development Tools

```bash
# Format/lint code (if available)
# Note: Check for ruff, black, or flake8 configurations

# Update translations
./contrib/make_locale

# Generate protobuf files (if needed)
protoc --proto_path=electrum_dash/ --python_out=electrum_dash/ electrum_dash/paymentrequest.proto
```

## Architecture Overview

### Core Components

1. **electrum_dash/**: Main package directory
   - `wallet.py`: Core wallet functionality
   - `network.py`: Network communication with Electrum servers
   - `blockchain.py`: Blockchain header validation and SPV
   - `transaction.py`: Transaction creation and parsing
   - `keystore.py`: Key management (HD wallets, hardware wallets)
   - `storage.py` & `wallet_db.py`: Wallet persistence

2. **Dash-Specific Modules**:
   - `dash_tx.py`: Dash transaction types (ProTx, special transactions)
   - `dash_ps.py` & `dash_ps_wallet.py`: PrivateSend mixing functionality
   - `dash_net.py`: Dash P2P network communication
   - `protx.py` & `protx_list.py`: Masternode (ProTx) management
   - `dash_msg.py`: Dash-specific network messages

3. **GUI Components**:
   - `gui/qt/`: Qt5 desktop interface
   - `gui/kivy/`: Kivy mobile interface
   - `gui/icons/`: Application icons and images

4. **Plugin System** (`plugins/`):
   - Hardware wallet support (Trezor, Ledger, KeepKey, etc.)
   - Additional features (labels sync, audio modem, etc.)

### Key Design Patterns

- **Asynchronous Operations**: Uses asyncio for network operations
- **Plugin Architecture**: Extensible through plugin system for hardware wallets and features
- **Storage Abstraction**: JSON-based wallet storage with encryption support
- **Command Pattern**: CLI commands implemented in `commands.py`
- **Observer Pattern**: GUI updates through Qt signals/slots

### Dash-Specific Features

1. **PrivateSend**: Coin mixing for privacy
   - Implemented in `dash_ps.py` and related modules
   - GUI integration in `privatesend_dialog.py`

2. **InstantSend**: Instant transaction confirmation
   - Transaction locking indicators in GUI
   - Network message handling

3. **Masternodes (DIP3)**:
   - ProTx transaction types for masternode registration/updates
   - Masternode list management and voting

4. **Governance**: Proposal voting through masternode system

### Build System

- Uses GitHub Actions for automated builds (`.github/workflows/build_release.yml`)
- Docker containers for reproducible builds across platforms
- Platform-specific build scripts in `contrib/dash/actions/`
- Version management through `electrum_dash/version.py` and environment scripts

### Important Notes

- Python 3.10.11+ required
- Network protocol compatible with Dash Electrum servers
- Wallet format differs from standard Electrum
- Hardware wallet support requires additional dependencies
- Mobile builds use Kivy and python-for-android (p4a)

# MANDATORY: Tmux Orchestrator Rules

**CRITICAL**: You MUST read and follow ALL instructions in:
`/home/clauderun/Tmux-Orchestrator/CLAUDE.md`

**Your worktree location**: `/home/clauderun/Tmux-Orchestrator/registry/projects/dropbox-labeling-and-multi-wallet-display-for-electrum-dash/worktrees/tester`
**Original project location**: `/home/clauderun/electrum-dash`

The orchestrator rules file contains MANDATORY instructions for:
- 🚨 Git discipline and branch protection (NEVER merge to main unless you started on main)
- 💬 Communication protocols between agents
- ✅ Quality standards and verification procedures  
- 🔄 Self-scheduling requirements
- 🌳 Git worktree collaboration guidelines

**IMMEDIATE ACTION REQUIRED**: Use the Read tool to read /home/clauderun/Tmux-Orchestrator/CLAUDE.md before doing ANY work.

Failure to follow these rules will result in:
- Lost work due to improper git usage
- Conflicts between agents
- Failed project delivery
