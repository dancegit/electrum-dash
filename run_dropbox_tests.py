#!/usr/bin/env python3
"""
Test runner for Dropbox plugin tests
This runs tests without requiring full Electrum dependencies
"""

import sys
import os
import unittest
import tempfile
import shutil

# Add the project to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestAESGCMEncryption(unittest.TestCase):
    """Direct tests for AES-256-GCM encryption implementation"""
    
    def setUp(self):
        self.test_labels = {
            "XcQNDnq8p8K9WB2m1GEKuxkcLJCxRGmyGb": "Test Label 1",
            "XdRcRL9VzYucJpzHXyML3Tt6CTH8xgs4fo": "Test Label 2 with special chars: €$¢",
            "XeK81SFqDCQhwf2nhjuJ8iyD9Qtpro481g": "Unicode test: 测试标签 🚀"
        }
    
    def test_import_encryption_module(self):
        """Test that we can import the encryption module"""
        try:
            from electrum_dash.plugins.dropbox_labels.encryption import AESGCMEncryption, TrezorSuiteFormat
            self.assertTrue(True, "Successfully imported encryption modules")
        except ImportError as e:
            self.fail(f"Failed to import encryption module: {e}")
    
    def test_aes_gcm_constants(self):
        """Test AES-GCM constants are correct"""
        from electrum_dash.plugins.dropbox_labels.encryption import AESGCMEncryption
        
        self.assertEqual(AESGCMEncryption.KEY_SIZE, 32)  # 256 bits
        self.assertEqual(AESGCMEncryption.NONCE_SIZE, 12)  # 96 bits
        self.assertEqual(AESGCMEncryption.TAG_SIZE, 16)  # 128 bits
    
    def test_nonce_generation(self):
        """Test nonce generation"""
        from electrum_dash.plugins.dropbox_labels.encryption import AESGCMEncryption
        
        # Generate multiple nonces
        nonces = []
        for _ in range(10):
            nonce = AESGCMEncryption.generate_nonce()
            self.assertEqual(len(nonce), 12)
            self.assertIsInstance(nonce, bytes)
            nonces.append(nonce)
        
        # All should be unique
        self.assertEqual(len(nonces), len(set(nonces)))
    
    def test_encryption_decryption(self):
        """Test basic encryption/decryption"""
        from electrum_dash.plugins.dropbox_labels.encryption import AESGCMEncryption
        
        key = os.urandom(32)
        plaintext = b"Hello, Dropbox labels!"
        
        # Encrypt
        ciphertext, nonce, tag = AESGCMEncryption.encrypt(key, plaintext)
        
        # Verify outputs
        self.assertIsInstance(ciphertext, bytes)
        self.assertEqual(len(nonce), 12)
        self.assertEqual(len(tag), 16)
        self.assertNotEqual(ciphertext, plaintext)
        
        # Decrypt
        decrypted = AESGCMEncryption.decrypt(key, ciphertext, nonce, tag)
        self.assertEqual(decrypted, plaintext)
    
    def test_label_packing(self):
        """Test TrezorSuiteFormat label packing/unpacking"""
        from electrum_dash.plugins.dropbox_labels.encryption import TrezorSuiteFormat
        
        key = os.urandom(32)
        
        # Pack labels
        packed = TrezorSuiteFormat.pack_labels(self.test_labels, key)
        self.assertIsInstance(packed, bytes)
        
        # Unpack labels
        unpacked = TrezorSuiteFormat.unpack_labels(packed, key)
        self.assertEqual(unpacked, self.test_labels)
    
    def test_wrong_key_fails(self):
        """Test that decryption with wrong key fails"""
        from electrum_dash.plugins.dropbox_labels.encryption import AESGCMEncryption
        
        key1 = os.urandom(32)
        key2 = os.urandom(32)
        plaintext = b"Secret data"
        
        # Encrypt with key1
        ciphertext, nonce, tag = AESGCMEncryption.encrypt(key1, plaintext)
        
        # Try to decrypt with key2 - should fail
        with self.assertRaises(Exception):
            AESGCMEncryption.decrypt(key2, ciphertext, nonce, tag)


class TestDropboxOAuth2(unittest.TestCase):
    """Direct tests for OAuth2 implementation"""
    
    def test_import_auth_module(self):
        """Test that we can import the auth module"""
        try:
            from electrum_dash.plugins.dropbox_labels.auth import DropboxOAuth2
            self.assertTrue(True, "Successfully imported auth module")
        except ImportError as e:
            self.fail(f"Failed to import auth module: {e}")
    
    def test_oauth2_initialization(self):
        """Test OAuth2 handler initialization"""
        from electrum_dash.plugins.dropbox_labels.auth import DropboxOAuth2
        
        app_key = "test_app_key"
        oauth = DropboxOAuth2(app_key)
        
        self.assertEqual(oauth.app_key, app_key)
        self.assertEqual(oauth.redirect_uri, "http://localhost:43682/dropbox-auth")
    
    def test_pkce_generation(self):
        """Test PKCE parameter generation"""
        from electrum_dash.plugins.dropbox_labels.auth import DropboxOAuth2
        
        oauth = DropboxOAuth2("test_key")
        verifier, challenge = oauth.generate_pkce_params()
        
        # Verify verifier length (43-128 characters)
        self.assertGreaterEqual(len(verifier), 43)
        self.assertLessEqual(len(verifier), 128)
        
        # Verify challenge is base64url encoded
        self.assertIsInstance(challenge, str)
        self.assertNotIn("+", challenge)  # base64url doesn't use +
        self.assertNotIn("/", challenge)  # base64url doesn't use /
        self.assertNotIn("=", challenge)  # base64url has no padding


def run_tests():
    """Run all tests and report results"""
    print("=" * 70)
    print("Running Dropbox Plugin Tests")
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAESGCMEncryption))
    suite.addTests(loader.loadTestsFromTestCase(TestDropboxOAuth2))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)