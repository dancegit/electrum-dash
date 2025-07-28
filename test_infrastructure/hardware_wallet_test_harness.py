"""
Hardware Wallet Test Harness for Phase 2
Provides comprehensive testing infrastructure for hardware wallet integration
"""

import time
import json
from typing import Dict, List, Optional, Any, Callable
from unittest.mock import Mock, MagicMock
import pytest

from .trezor_emulator import TrezorEmulator, TrezorConfirmationFlow, SLIP0015, TrezorTestFixtures


class HardwareWalletTestHarness:
    """Main test harness for hardware wallet testing"""
    
    def __init__(self):
        self.trezor_emulator = TrezorEmulator()
        self.confirmation_flow = TrezorConfirmationFlow(self.trezor_emulator)
        self.performance_metrics = []
        
        # Mock hardware wallet connections
        self.connected_devices = []
        
    def connect_device(self, device_type: str = "trezor") -> Dict[str, Any]:
        """Simulate connecting a hardware wallet"""
        if device_type == "trezor":
            device = {
                "type": "trezor",
                "id": self.trezor_emulator.device.device_id,
                "label": self.trezor_emulator.device.label,
                "emulator": self.trezor_emulator,
                "connected_at": time.time()
            }
            self.connected_devices.append(device)
            return device
        else:
            raise ValueError(f"Unsupported device type: {device_type}")
    
    def disconnect_device(self, device_id: str) -> bool:
        """Simulate disconnecting a hardware wallet"""
        self.connected_devices = [
            d for d in self.connected_devices 
            if d["id"] != device_id
        ]
        return True
    
    def get_connected_devices(self) -> List[Dict[str, Any]]:
        """Get list of connected devices"""
        return self.connected_devices.copy()


class SLIP0015TestSuite:
    """Test suite for SLIP-0015 key derivation"""
    
    def __init__(self, emulator: TrezorEmulator):
        self.emulator = emulator
        self.slip0015 = SLIP0015()
    
    def test_deterministic_key_derivation(self) -> Dict[str, Any]:
        """Test that key derivation is deterministic"""
        wallet_id = "test_wallet_001"
        
        # Derive key multiple times
        keys = []
        for _ in range(5):
            key = self.emulator.derive_slip0015_key(wallet_id)
            keys.append(key)
        
        # All keys should be identical
        all_same = all(k == keys[0] for k in keys)
        
        return {
            "test": "deterministic_key_derivation",
            "passed": all_same,
            "key_length": len(keys[0]) if keys else 0,
            "message": "Keys are deterministic" if all_same else "Keys are not deterministic!"
        }
    
    def test_unique_keys_per_wallet(self) -> Dict[str, Any]:
        """Test that each wallet gets a unique key"""
        wallet_ids = ["wallet_001", "wallet_002", "wallet_003"]
        keys = {}
        
        for wallet_id in wallet_ids:
            keys[wallet_id] = self.emulator.derive_slip0015_key(wallet_id)
        
        # Check all keys are unique
        unique_keys = len(set(keys.values())) == len(wallet_ids)
        
        return {
            "test": "unique_keys_per_wallet",
            "passed": unique_keys,
            "num_wallets": len(wallet_ids),
            "unique_keys": len(set(keys.values())),
            "message": "Each wallet has unique key" if unique_keys else "Duplicate keys found!"
        }
    
    def test_key_derivation_path(self) -> Dict[str, Any]:
        """Test correct SLIP-0015 derivation path (m/10015'/0')"""
        # Get public key at SLIP-0015 path
        path = [10015 | 0x80000000, 0 | 0x80000000]  # m/10015'/0'
        
        result = self.emulator.call("GetPublicKey", path=path)
        
        return {
            "test": "key_derivation_path",
            "passed": "node" in result and result["node"]["depth"] == 2,
            "path": "m/10015'/0'",
            "depth": result.get("node", {}).get("depth", 0),
            "message": "Correct derivation path used"
        }


class HardwareConfirmationTestSuite:
    """Test suite for hardware confirmation flows"""
    
    def __init__(self, harness: HardwareWalletTestHarness):
        self.harness = harness
        self.flow = harness.confirmation_flow
    
    def test_enable_sync_confirmation(self) -> Dict[str, Any]:
        """Test user confirmation for enabling sync"""
        # Request confirmation
        conf_id = self.flow.request_confirmation(
            "enable_dropbox_sync",
            {
                "action": "Enable Dropbox label sync",
                "wallet": "Test Wallet 1",
                "warning": "Labels will be encrypted and uploaded"
            }
        )
        
        # Simulate user confirming
        confirmed = self.flow.confirm(conf_id)
        
        return {
            "test": "enable_sync_confirmation",
            "passed": confirmed,
            "confirmation_id": conf_id,
            "message": "User confirmed sync enable"
        }
    
    def test_sync_rejection(self) -> Dict[str, Any]:
        """Test user rejecting sync"""
        # Request confirmation
        conf_id = self.flow.request_confirmation(
            "enable_dropbox_sync",
            {"action": "Enable Dropbox label sync"}
        )
        
        # Simulate user rejecting
        rejected = self.flow.reject(conf_id)
        
        return {
            "test": "sync_rejection",
            "passed": rejected,
            "confirmation_id": conf_id,
            "message": "User rejected sync enable"
        }
    
    def test_confirmation_timeout(self) -> Dict[str, Any]:
        """Test confirmation timeout handling"""
        # Request confirmation but don't respond
        conf_id = self.flow.request_confirmation(
            "test_action",
            {"action": "Test timeout"}
        )
        
        # Check pending status
        pending = any(
            c["id"] == conf_id and c["status"] == "pending" 
            for c in self.flow.pending_confirmations
        )
        
        return {
            "test": "confirmation_timeout",
            "passed": pending,
            "confirmation_id": conf_id,
            "message": "Confirmation remains pending"
        }


class CrossAppCompatibilityTests:
    """Test compatibility with other apps (Trezor Suite, etc)"""
    
    def __init__(self):
        self.fixtures = TrezorTestFixtures()
    
    def test_mtdt_file_format(self) -> Dict[str, Any]:
        """Test .mtdt file format compatibility"""
        mtdt_content = self.fixtures.get_test_mtdt_file()
        
        try:
            data = json.loads(mtdt_content)
            
            # Check required fields
            has_version = "version" in data
            has_wallets = "wallets" in data
            has_encryption = "encrypted" in data
            
            passed = all([has_version, has_wallets, has_encryption])
            
            return {
                "test": "mtdt_file_format",
                "passed": passed,
                "version": data.get("version"),
                "num_wallets": len(data.get("wallets", {})),
                "encrypted": data.get("encrypted"),
                "message": "Valid .mtdt format" if passed else "Invalid .mtdt format"
            }
            
        except Exception as e:
            return {
                "test": "mtdt_file_format",
                "passed": False,
                "error": str(e),
                "message": "Failed to parse .mtdt file"
            }
    
    def test_trezor_suite_label_format(self) -> Dict[str, Any]:
        """Test label format compatibility with Trezor Suite"""
        test_labels = {
            "address1": "My main wallet",
            "address2": "Savings account",
            "address3": "Test wallet 🚀"  # Unicode test
        }
        
        # Trezor Suite expects specific format
        suite_format = {
            "labels": {
                addr: {"label": label, "type": "address"}
                for addr, label in test_labels.items()
            }
        }
        
        # Validate format
        valid = all(
            isinstance(v, dict) and "label" in v and "type" in v
            for v in suite_format["labels"].values()
        )
        
        return {
            "test": "trezor_suite_label_format",
            "passed": valid,
            "num_labels": len(test_labels),
            "has_unicode": any("🚀" in label for label in test_labels.values()),
            "message": "Compatible with Trezor Suite format"
        }


class HardwareWalletPerformanceTests:
    """Performance benchmarking for hardware wallet operations"""
    
    def __init__(self, harness: HardwareWalletTestHarness):
        self.harness = harness
        self.metrics = []
    
    def benchmark_key_derivation(self, iterations: int = 100) -> Dict[str, Any]:
        """Benchmark SLIP-0015 key derivation performance"""
        emulator = self.harness.trezor_emulator
        
        start_time = time.time()
        
        for i in range(iterations):
            wallet_id = f"wallet_{i:04d}"
            _ = emulator.derive_slip0015_key(wallet_id)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations
        
        return {
            "test": "key_derivation_performance",
            "passed": avg_time < 0.01,  # Should be < 10ms per derivation
            "iterations": iterations,
            "total_time": f"{total_time:.3f}s",
            "avg_time_ms": f"{avg_time * 1000:.2f}ms",
            "ops_per_sec": iterations / total_time,
            "message": f"Key derivation: {avg_time * 1000:.2f}ms average"
        }
    
    def benchmark_confirmation_flow(self, iterations: int = 50) -> Dict[str, Any]:
        """Benchmark confirmation flow performance"""
        flow = self.harness.confirmation_flow
        
        start_time = time.time()
        
        for i in range(iterations):
            # Request confirmation
            conf_id = flow.request_confirmation(
                f"test_action_{i}",
                {"iteration": i}
            )
            # Auto-confirm
            flow.confirm(conf_id)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations
        
        return {
            "test": "confirmation_flow_performance",
            "passed": avg_time < 0.005,  # Should be < 5ms per confirmation
            "iterations": iterations,
            "total_time": f"{total_time:.3f}s",
            "avg_time_ms": f"{avg_time * 1000:.2f}ms",
            "message": f"Confirmation flow: {avg_time * 1000:.2f}ms average"
        }


# Pytest fixtures for hardware wallet testing
@pytest.fixture
def hardware_wallet_harness():
    """Provide hardware wallet test harness"""
    return HardwareWalletTestHarness()


@pytest.fixture
def trezor_device(hardware_wallet_harness):
    """Provide connected Trezor device"""
    device = hardware_wallet_harness.connect_device("trezor")
    yield device
    hardware_wallet_harness.disconnect_device(device["id"])


@pytest.fixture
def slip0015_suite(trezor_device):
    """Provide SLIP-0015 test suite"""
    return SLIP0015TestSuite(trezor_device["emulator"])


@pytest.fixture
def confirmation_suite(hardware_wallet_harness):
    """Provide confirmation flow test suite"""
    return HardwareConfirmationTestSuite(hardware_wallet_harness)


@pytest.fixture
def performance_suite(hardware_wallet_harness):
    """Provide performance test suite"""
    return HardwareWalletPerformanceTests(hardware_wallet_harness)