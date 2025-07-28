"""
Configuration for Dropbox Labels plugin
"""

# Dropbox App Configuration
# These should be set to your actual Dropbox app credentials
# For development, you can create an app at https://www.dropbox.com/developers/apps

DROPBOX_APP_KEY = "your_app_key_here"
DROPBOX_APP_SECRET = None  # Not needed for PKCE flow

# OAuth2 Configuration
OAUTH_REDIRECT_URI = "http://localhost:43682/dropbox-auth"
OAUTH_REDIRECT_PORT = 43682

# File paths
DROPBOX_FOLDER = "/Apps/Electrum-Dash/"
TREZOR_FOLDER = "/Apps/TREZOR/"  # For importing Trezor Suite labels

# Encryption settings
USE_HARDWARE_ENCRYPTION = True  # Use hardware wallet for encryption when available
ENCRYPTION_TIMEOUT = 300  # Cache hardware encryption key for 5 minutes