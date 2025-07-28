"""
Dropbox API Mocking Framework
Provides comprehensive mocks for Dropbox API endpoints
"""

import json
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests_mock


class DropboxAPIMocks:
    """Mock implementations of Dropbox API endpoints"""
    
    # Base URLs
    API_BASE = "https://api.dropboxapi.com/2"
    CONTENT_BASE = "https://content.dropboxapi.com/2"
    
    # Test data
    TEST_FOLDER = "/electrum-dash-wallets"
    TEST_ENCRYPTED_FILE = "/electrum-dash-wallets/wallet_encrypted_001.dat"
    
    @classmethod
    def mock_account_info(cls) -> Dict:
        """Mock /users/get_current_account response"""
        return {
            "account_id": "dbid:test_account_456",
            "name": {
                "given_name": "Test",
                "surname": "User",
                "familiar_name": "Test",
                "display_name": "Test User"
            },
            "email": "test@example.com",
            "email_verified": True,
            "profile_photo_url": "https://example.com/photo.jpg",
            "disabled": False,
            "country": "US",
            "locale": "en",
            "referral_link": "https://db.tt/test123",
            "is_paired": False,
            "account_type": {
                ".tag": "basic"
            }
        }
    
    @classmethod
    def mock_space_usage(cls) -> Dict:
        """Mock /users/get_space_usage response"""
        return {
            "used": 1024 * 1024 * 500,  # 500 MB
            "allocation": {
                ".tag": "individual",
                "allocated": 1024 * 1024 * 1024 * 2  # 2 GB
            }
        }
    
    @classmethod
    def mock_folder_metadata(cls, path: str = TEST_FOLDER) -> Dict:
        """Mock folder metadata response"""
        return {
            ".tag": "folder",
            "name": path.split('/')[-1],
            "path_lower": path.lower(),
            "path_display": path,
            "id": f"id:{hashlib.md5(path.encode()).hexdigest()[:10]}",
            "shared_folder_id": None,
            "sharing_info": None
        }
    
    @classmethod
    def mock_file_metadata(cls, path: str, size: int = 1024,
                          content_hash: Optional[str] = None) -> Dict:
        """Mock file metadata response"""
        if content_hash is None:
            content_hash = hashlib.sha256(path.encode()).hexdigest()
        
        return {
            ".tag": "file",
            "name": path.split('/')[-1],
            "path_lower": path.lower(),
            "path_display": path,
            "id": f"id:{hashlib.md5(path.encode()).hexdigest()[:10]}",
            "client_modified": datetime.utcnow().isoformat() + "Z",
            "server_modified": datetime.utcnow().isoformat() + "Z",
            "rev": f"rev_{hashlib.md5(path.encode()).hexdigest()[:8]}",
            "size": size,
            "content_hash": content_hash,
            "is_downloadable": True,
            "has_explicit_shared_members": False
        }
    
    @classmethod
    def mock_list_folder_response(cls, path: str = TEST_FOLDER,
                                 include_files: bool = True) -> Dict:
        """Mock /files/list_folder response"""
        entries = []
        
        # Add some test wallet files if requested
        if include_files and path == cls.TEST_FOLDER:
            for i in range(3):
                entries.append(cls.mock_file_metadata(
                    f"{path}/wallet_encrypted_{i:03d}.dat",
                    size=2048 + i * 512
                ))
        
        return {
            "entries": entries,
            "cursor": f"cursor_{hashlib.md5(path.encode()).hexdigest()[:16]}",
            "has_more": False
        }
    
    @classmethod
    def mock_upload_response(cls, path: str, content: bytes) -> Dict:
        """Mock /files/upload response"""
        content_hash = hashlib.sha256(content).hexdigest()
        return cls.mock_file_metadata(path, len(content), content_hash)
    
    @classmethod
    def mock_download_response(cls, path: str) -> bytes:
        """Mock file download content"""
        # Return mock encrypted wallet data
        mock_data = {
            "encrypted": True,
            "version": 1,
            "data": base64.b64encode(
                f"Mock encrypted wallet data for {path}".encode()
            ).decode(),
            "salt": base64.b64encode(b"mock_salt_12345").decode(),
            "iterations": 10000
        }
        return json.dumps(mock_data).encode()
    
    @classmethod
    def mock_delete_response(cls, path: str) -> Dict:
        """Mock /files/delete response"""
        return cls.mock_file_metadata(path)
    
    @classmethod
    def mock_create_folder_response(cls, path: str) -> Dict:
        """Mock /files/create_folder response"""
        return cls.mock_folder_metadata(path)
    
    @classmethod
    def mock_error_response(cls, error_type: str = "path_not_found") -> Dict:
        """Mock API error responses"""
        errors = {
            "path_not_found": {
                "error": {
                    ".tag": "path",
                    "path": {
                        ".tag": "not_found"
                    }
                },
                "error_summary": "path/not_found/.."
            },
            "invalid_access_token": {
                "error": {
                    ".tag": "invalid_access_token"
                },
                "error_summary": "invalid_access_token/.."
            },
            "insufficient_space": {
                "error": {
                    ".tag": "path",
                    "reason": {
                        ".tag": "insufficient_space"
                    }
                },
                "error_summary": "path/insufficient_space/.."
            },
            "rate_limited": {
                "error": {
                    ".tag": "too_many_requests",
                    "retry_after": 60
                },
                "error_summary": "too_many_requests/.."
            }
        }
        return errors.get(error_type, errors["path_not_found"])
    
    @classmethod
    def setup_mock_endpoints(cls, adapter: requests_mock.Adapter,
                           authorized: bool = True,
                           simulate_errors: Optional[List[str]] = None):
        """Set up all Dropbox API mock endpoints"""
        
        if simulate_errors is None:
            simulate_errors = []
        
        # Helper to check authorization
        def check_auth(request):
            if not authorized:
                return (401, {}, json.dumps(cls.mock_error_response("invalid_access_token")))
            if "Authorization" not in request.headers:
                return (401, {}, json.dumps(cls.mock_error_response("invalid_access_token")))
            return None
        
        # Account info endpoint
        def account_info_callback(request, context):
            auth_error = check_auth(request)
            if auth_error:
                context.status_code, _, response = auth_error
                return response
            
            context.status_code = 200
            return json.dumps(cls.mock_account_info())
        
        adapter.register_uri(
            'POST',
            f"{cls.API_BASE}/users/get_current_account",
            text=account_info_callback
        )
        
        # Space usage endpoint
        adapter.register_uri(
            'POST',
            f"{cls.API_BASE}/users/get_space_usage",
            json=cls.mock_space_usage() if authorized else cls.mock_error_response("invalid_access_token"),
            status_code=200 if authorized else 401
        )
        
        # List folder endpoint
        def list_folder_callback(request, context):
            auth_error = check_auth(request)
            if auth_error:
                context.status_code, _, response = auth_error
                return response
            
            data = json.loads(request.text)
            path = data.get("path", "")
            
            if "path_not_found" in simulate_errors and path != cls.TEST_FOLDER:
                context.status_code = 409
                return json.dumps(cls.mock_error_response("path_not_found"))
            
            context.status_code = 200
            return json.dumps(cls.mock_list_folder_response(path))
        
        adapter.register_uri(
            'POST',
            f"{cls.API_BASE}/files/list_folder",
            text=list_folder_callback
        )
        
        # Upload endpoint
        def upload_callback(request, context):
            auth_error = check_auth(request)
            if auth_error:
                context.status_code, _, response = auth_error
                return response
            
            if "insufficient_space" in simulate_errors:
                context.status_code = 409
                return json.dumps(cls.mock_error_response("insufficient_space"))
            
            # Parse Dropbox-API-Arg header
            api_arg = json.loads(request.headers.get("Dropbox-API-Arg", "{}"))
            path = api_arg.get("path", "/unknown")
            
            context.status_code = 200
            return json.dumps(cls.mock_upload_response(path, request.body))
        
        adapter.register_uri(
            'POST',
            f"{cls.CONTENT_BASE}/files/upload",
            text=upload_callback
        )
        
        # Download endpoint
        def download_callback(request, context):
            auth_error = check_auth(request)
            if auth_error:
                context.status_code, _, response = auth_error
                return response
            
            api_arg = json.loads(request.headers.get("Dropbox-API-Arg", "{}"))
            path = api_arg.get("path", "")
            
            if "path_not_found" in simulate_errors and path != cls.TEST_ENCRYPTED_FILE:
                context.status_code = 409
                return json.dumps(cls.mock_error_response("path_not_found"))
            
            context.status_code = 200
            # Return mock file content
            return cls.mock_download_response(path)
        
        adapter.register_uri(
            'POST', 
            f"{cls.CONTENT_BASE}/files/download",
            content=download_callback
        )
        
        # Delete endpoint
        adapter.register_uri(
            'POST',
            f"{cls.API_BASE}/files/delete_v2",
            json=cls.mock_delete_response(cls.TEST_ENCRYPTED_FILE) if authorized else cls.mock_error_response("invalid_access_token"),
            status_code=200 if authorized else 401
        )
        
        # Create folder endpoint
        def create_folder_callback(request, context):
            auth_error = check_auth(request)
            if auth_error:
                context.status_code, _, response = auth_error
                return response
            
            data = json.loads(request.text)
            path = data.get("path", "/unknown")
            
            context.status_code = 200
            return json.dumps(cls.mock_create_folder_response(path))
        
        adapter.register_uri(
            'POST',
            f"{cls.API_BASE}/files/create_folder_v2", 
            text=create_folder_callback
        )
        
        # Rate limiting simulation
        if "rate_limited" in simulate_errors:
            # Override all endpoints with rate limit error
            for method in ['POST']:
                for url in [f"{cls.API_BASE}/users/get_current_account",
                           f"{cls.API_BASE}/files/list_folder",
                           f"{cls.CONTENT_BASE}/files/upload",
                           f"{cls.CONTENT_BASE}/files/download"]:
                    adapter.register_uri(
                        method,
                        url,
                        json=cls.mock_error_response("rate_limited"),
                        status_code=429,
                        headers={"Retry-After": "60"}
                    )