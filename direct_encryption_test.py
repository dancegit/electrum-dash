#!/usr/bin/env python3
"""
Direct test of encryption module without full Electrum dependencies
"""

import sys
import os

# Bypass the main electrum_dash import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'electrum_dash', 'plugins', 'dropbox_labels'))

# Now we can import directly
from encryption import AESGCMEncryption, TrezorSuiteFormat
from auth import DropboxOAuth2

def test_encryption():
    """Test the encryption implementation"""
    print("\n=== Testing AES-256-GCM Encryption ===")
    
    # Test 1: Constants
    print(f"✓ KEY_SIZE: {AESGCMEncryption.KEY_SIZE} bytes (expected: 32)")
    print(f"✓ NONCE_SIZE: {AESGCMEncryption.NONCE_SIZE} bytes (expected: 12)")
    print(f"✓ TAG_SIZE: {AESGCMEncryption.TAG_SIZE} bytes (expected: 16)")
    
    # Test 2: Nonce generation
    nonce = AESGCMEncryption.generate_nonce()
    print(f"✓ Generated nonce: {len(nonce)} bytes")
    
    # Test 3: Encryption/Decryption
    key = os.urandom(32)
    plaintext = b"Test message for Dropbox labels"
    
    try:
        ciphertext, nonce, tag = AESGCMEncryption.encrypt(key, plaintext)
        print(f"✓ Encryption successful: {len(ciphertext)} bytes ciphertext, {len(tag)} bytes tag")
        
        decrypted = AESGCMEncryption.decrypt(key, ciphertext, nonce, tag)
        print(f"✓ Decryption successful: {decrypted == plaintext}")
    except Exception as e:
        print(f"✗ Encryption/Decryption failed: {e}")
        return False
    
    # Test 4: Label packing
    labels = {
        "address1": "Label 1",
        "address2": "Label 2 with unicode: 🚀"
    }
    
    try:
        packed = TrezorSuiteFormat.pack_labels(labels, key)
        print(f"✓ Label packing successful: {len(packed)} bytes")
        
        unpacked = TrezorSuiteFormat.unpack_labels(packed, key)
        print(f"✓ Label unpacking successful: {unpacked == labels}")
    except Exception as e:
        print(f"✗ Label packing/unpacking failed: {e}")
        return False
    
    return True


def test_oauth():
    """Test the OAuth2 implementation"""
    print("\n=== Testing OAuth2 Implementation ===")
    
    try:
        # Test initialization
        oauth = DropboxOAuth2("test_app_key")
        print(f"✓ OAuth2 initialized with app_key: {oauth.app_key}")
        print(f"✓ Redirect URI: {oauth.redirect_uri}")
        
        # Test PKCE generation
        verifier, challenge = oauth.generate_pkce_params()
        print(f"✓ PKCE verifier length: {len(verifier)} (should be 43-128)")
        print(f"✓ PKCE challenge generated (base64url encoded)")
        
        # Test authorization URL
        auth_url = oauth.get_authorization_url()
        print(f"✓ Authorization URL generated: {auth_url[:50]}...")
        
        return True
    except Exception as e:
        print(f"✗ OAuth2 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Direct Dropbox Plugin Tests")
    print("=" * 60)
    
    encryption_ok = test_encryption()
    oauth_ok = test_oauth()
    
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"Encryption tests: {'PASSED' if encryption_ok else 'FAILED'}")
    print(f"OAuth2 tests: {'PASSED' if oauth_ok else 'FAILED'}")
    print("=" * 60)
    
    return encryption_ok and oauth_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)