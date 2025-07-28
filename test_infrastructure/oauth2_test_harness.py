"""
OAuth2 Test Harness for Dropbox Integration
Provides utilities for testing OAuth2 authentication flows
"""

import json
import time
import urllib.parse
from typing import Dict, Optional, Tuple
from unittest.mock import MagicMock, patch
import requests_mock
import pytest


class OAuth2TestHarness:
    """Test harness for OAuth2 authentication flows"""
    
    # Test OAuth2 credentials
    TEST_CLIENT_ID = "test_client_id_12345"
    TEST_CLIENT_SECRET = "test_client_secret_67890"
    TEST_REDIRECT_URI = "http://localhost:43782/auth"
    
    # Test tokens
    TEST_ACCESS_TOKEN = "test_access_token_abcdef"
    TEST_REFRESH_TOKEN = "test_refresh_token_xyz789"
    TEST_AUTH_CODE = "test_auth_code_qwerty"
    
    # Dropbox OAuth2 endpoints
    DROPBOX_AUTH_URL = "https://www.dropbox.com/oauth2/authorize"
    DROPBOX_TOKEN_URL = "https://api.dropboxapi.com/oauth2/token"
    
    @classmethod
    def mock_auth_response(cls, success: bool = True) -> Dict:
        """Generate mock OAuth2 authorization response"""
        if success:
            return {
                "code": cls.TEST_AUTH_CODE,
                "state": "test_state_123"
            }
        else:
            return {
                "error": "access_denied",
                "error_description": "User denied access"
            }
    
    @classmethod
    def mock_token_response(cls, success: bool = True, 
                           include_refresh: bool = True) -> Dict:
        """Generate mock OAuth2 token response"""
        if success:
            response = {
                "access_token": cls.TEST_ACCESS_TOKEN,
                "token_type": "bearer",
                "expires_in": 14400,  # 4 hours
                "uid": "test_user_123",
                "account_id": "dbid:test_account_456"
            }
            if include_refresh:
                response["refresh_token"] = cls.TEST_REFRESH_TOKEN
            return response
        else:
            return {
                "error": "invalid_grant",
                "error_description": "Invalid authorization code"
            }
    
    @classmethod
    def mock_refresh_token_response(cls, success: bool = True) -> Dict:
        """Generate mock refresh token response"""
        if success:
            return {
                "access_token": f"{cls.TEST_ACCESS_TOKEN}_refreshed",
                "token_type": "bearer", 
                "expires_in": 14400
            }
        else:
            return {
                "error": "invalid_grant",
                "error_description": "Refresh token is invalid or expired"
            }
    
    @classmethod
    def create_mock_oauth2_server(cls, adapter: requests_mock.Adapter):
        """Set up mock OAuth2 server endpoints"""
        
        # Mock authorization endpoint
        def auth_callback(request, context):
            # This would normally redirect to Dropbox login
            params = urllib.parse.parse_qs(request.query)
            if params.get('client_id', [''])[0] == cls.TEST_CLIENT_ID:
                context.status_code = 302
                context.headers['Location'] = f"{cls.TEST_REDIRECT_URI}?code={cls.TEST_AUTH_CODE}&state={params.get('state', [''])[0]}"
            else:
                context.status_code = 400
            return ""
        
        adapter.register_uri(
            'GET',
            cls.DROPBOX_AUTH_URL,
            text=auth_callback
        )
        
        # Mock token endpoint
        def token_callback(request, context):
            data = urllib.parse.parse_qs(request.text)
            
            # Check for authorization code flow
            if data.get('grant_type', [''])[0] == 'authorization_code':
                if (data.get('code', [''])[0] == cls.TEST_AUTH_CODE and
                    data.get('client_id', [''])[0] == cls.TEST_CLIENT_ID and
                    data.get('client_secret', [''])[0] == cls.TEST_CLIENT_SECRET):
                    context.status_code = 200
                    return cls.mock_token_response(success=True)
                else:
                    context.status_code = 400
                    return cls.mock_token_response(success=False)
            
            # Check for refresh token flow
            elif data.get('grant_type', [''])[0] == 'refresh_token':
                if (data.get('refresh_token', [''])[0] == cls.TEST_REFRESH_TOKEN and
                    data.get('client_id', [''])[0] == cls.TEST_CLIENT_ID and
                    data.get('client_secret', [''])[0] == cls.TEST_CLIENT_SECRET):
                    context.status_code = 200
                    return cls.mock_refresh_token_response(success=True)
                else:
                    context.status_code = 400
                    return cls.mock_refresh_token_response(success=False)
            
            context.status_code = 400
            return {"error": "unsupported_grant_type"}
        
        adapter.register_uri(
            'POST',
            cls.DROPBOX_TOKEN_URL,
            json=token_callback
        )
    
    @classmethod
    def simulate_user_authorization(cls, client_id: str, redirect_uri: str,
                                   state: Optional[str] = None,
                                   approve: bool = True) -> Tuple[str, Dict]:
        """Simulate user going through OAuth2 authorization flow"""
        auth_params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri
        }
        if state:
            auth_params["state"] = state
        
        # Build authorization URL
        auth_url = f"{cls.DROPBOX_AUTH_URL}?{urllib.parse.urlencode(auth_params)}"
        
        if approve and client_id == cls.TEST_CLIENT_ID:
            # Simulate successful authorization
            callback_params = {
                "code": cls.TEST_AUTH_CODE
            }
            if state:
                callback_params["state"] = state
            callback_url = f"{redirect_uri}?{urllib.parse.urlencode(callback_params)}"
            return callback_url, callback_params
        else:
            # Simulate denial
            callback_params = {
                "error": "access_denied",
                "error_description": "User denied access"
            }
            callback_url = f"{redirect_uri}?{urllib.parse.urlencode(callback_params)}"
            return callback_url, callback_params
    
    @classmethod
    def verify_token_request(cls, request_data: Dict) -> bool:
        """Verify OAuth2 token request parameters"""
        required_params = ['grant_type', 'code', 'client_id', 
                          'client_secret', 'redirect_uri']
        
        for param in required_params:
            if param not in request_data:
                return False
        
        return (request_data['grant_type'] == 'authorization_code' and
                request_data['client_id'] == cls.TEST_CLIENT_ID and
                request_data['client_secret'] == cls.TEST_CLIENT_SECRET)
    
    @classmethod
    def create_expired_token(cls) -> Dict:
        """Create an expired access token for testing"""
        return {
            "access_token": f"{cls.TEST_ACCESS_TOKEN}_expired",
            "token_type": "bearer",
            "expires_in": -1,  # Already expired
            "created_at": time.time() - 20000  # Created 5+ hours ago
        }


# Pytest fixtures for easy test setup
@pytest.fixture
def oauth2_harness():
    """Provide OAuth2 test harness"""
    return OAuth2TestHarness()


@pytest.fixture
def mock_dropbox_oauth2():
    """Set up complete mock Dropbox OAuth2 server"""
    with requests_mock.Mocker() as m:
        OAuth2TestHarness.create_mock_oauth2_server(m)
        yield m


@pytest.fixture
def oauth2_test_credentials():
    """Provide test OAuth2 credentials"""
    return {
        "client_id": OAuth2TestHarness.TEST_CLIENT_ID,
        "client_secret": OAuth2TestHarness.TEST_CLIENT_SECRET,
        "redirect_uri": OAuth2TestHarness.TEST_REDIRECT_URI
    }