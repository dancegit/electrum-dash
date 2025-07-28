"""
Dropbox OAuth2 Authentication Module
Implements secure OAuth2 flow with PKCE for Dropbox integration
"""

import os
import secrets
import hashlib
import base64
import json
import time
from typing import Optional, Dict, Tuple
from urllib.parse import urlencode, parse_qs, urlparse
import webbrowser

from electrum_dash.logging import Logger
from electrum_dash.util import make_aiohttp_session


class DropboxOAuth2:
    """
    Handles OAuth2 authentication flow with Dropbox.
    Uses PKCE (Proof Key for Code Exchange) for enhanced security.
    """
    
    # Dropbox OAuth2 endpoints
    AUTHORIZE_URL = "https://www.dropbox.com/oauth2/authorize"
    TOKEN_URL = "https://api.dropboxapi.com/oauth2/token"
    
    def __init__(self, app_key: str, app_secret: Optional[str] = None, 
                 redirect_uri: str = "http://localhost:43682/dropbox-auth"):
        """
        Initialize OAuth2 handler.
        
        Args:
            app_key: Dropbox app key
            app_secret: Dropbox app secret (optional for PKCE flow)
            redirect_uri: OAuth2 redirect URI
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
        self.logger = Logger.get_logger(__name__)
        
        # PKCE parameters
        self.code_verifier = None
        self.code_challenge = None
        self.state = None
        
    def generate_pkce_params(self) -> Tuple[str, str]:
        """
        Generate PKCE code verifier and challenge.
        
        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode('utf-8').rstrip('=')
        
        # Generate code challenge (SHA256 of verifier)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    def get_authorization_url(self) -> str:
        """
        Generate the authorization URL for user to visit.
        
        Returns:
            Authorization URL string
        """
        # Generate PKCE parameters
        self.code_verifier, self.code_challenge = self.generate_pkce_params()
        
        # Generate state for CSRF protection
        self.state = base64.urlsafe_b64encode(
            secrets.token_bytes(16)
        ).decode('utf-8').rstrip('=')
        
        # Build authorization URL
        params = {
            'client_id': self.app_key,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'state': self.state,
            'code_challenge': self.code_challenge,
            'code_challenge_method': 'S256',
            'token_access_type': 'offline',  # For refresh token
        }
        
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str, state: str) -> Dict[str, any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from Dropbox
            state: State parameter for CSRF validation
            
        Returns:
            Dict containing access_token, refresh_token, etc.
            
        Raises:
            Exception: If state doesn't match or token exchange fails
        """
        # Validate state
        if state != self.state:
            raise Exception("Invalid state parameter - possible CSRF attack")
        
        # Prepare token exchange request
        data = {
            'code': code,
            'grant_type': 'authorization_code',
            'client_id': self.app_key,
            'redirect_uri': self.redirect_uri,
            'code_verifier': self.code_verifier,
        }
        
        # Include client secret if available
        if self.app_secret:
            data['client_secret'] = self.app_secret
        
        # Make token request
        async with make_aiohttp_session() as session:
            async with session.post(self.TOKEN_URL, data=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Token exchange failed: {error_text}")
                
                token_data = await response.json()
                
                # Add expiry timestamp
                if 'expires_in' in token_data:
                    token_data['expires_at'] = time.time() + token_data['expires_in']
                
                return token_data
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, any]:
        """
        Refresh an expired access token.
        
        Args:
            refresh_token: Refresh token from previous authentication
            
        Returns:
            Dict containing new access_token, etc.
        """
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.app_key,
        }
        
        if self.app_secret:
            data['client_secret'] = self.app_secret
        
        async with make_aiohttp_session() as session:
            async with session.post(self.TOKEN_URL, data=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Token refresh failed: {error_text}")
                
                token_data = await response.json()
                
                # Add expiry timestamp
                if 'expires_in' in token_data:
                    token_data['expires_at'] = time.time() + token_data['expires_in']
                
                return token_data
    
    def is_token_expired(self, token_data: Dict[str, any]) -> bool:
        """
        Check if access token is expired.
        
        Args:
            token_data: Token data dict with expires_at field
            
        Returns:
            True if token is expired or will expire in next 5 minutes
        """
        expires_at = token_data.get('expires_at', 0)
        # Consider expired if less than 5 minutes remaining
        return time.time() > (expires_at - 300)


class DropboxAuthServer:
    """
    Local HTTP server to handle OAuth2 redirect.
    Listens on localhost to receive the authorization code.
    """
    
    def __init__(self, port: int = 43682):
        """
        Initialize auth server.
        
        Args:
            port: Port to listen on (default 43682)
        """
        self.port = port
        self.auth_code = None
        self.auth_state = None
        self.error = None
        
    async def start_server(self):
        """
        Start local HTTP server to receive OAuth2 callback.
        This is a simplified version - in production, use aiohttp.web
        """
        # TODO: Implement actual HTTP server
        # For now, we'll use manual code entry in the GUI
        pass
    
    def get_auth_result(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Get authentication result.
        
        Returns:
            Tuple of (auth_code, state, error)
        """
        return self.auth_code, self.auth_state, self.error