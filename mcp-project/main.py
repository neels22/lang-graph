# server.py
from mcp.server.fastmcp import FastMCP
from typing import List, Optional, Dict, Any
import random
from dataclasses import dataclass
from datetime import datetime
import httpx

# Create an MCP server
mcp = FastMCP("Student Management System")

# Global variable to store the authentication token
auth_token: Optional[str] = None

@mcp.tool()
def login(username: str, password: str) -> Dict[str, Any]:
    """Login to get authentication token"""
    global auth_token
    
    try:
        # Prepare the form data for login
        login_data = {
            'grant_type': '',
            'username': username,
            'password': password,
            'scope': '',
            'client_id': '',
            'client_secret': ''
        }
        
        response = httpx.post(
            'http://127.0.0.1:8000/auth/login',
            data=login_data,
            headers={
                'accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            timeout=10.0
        )
        
        response.raise_for_status()
        login_response = response.json()
        
        # Store the token globally for future API calls
        if 'access_token' in login_response:
            auth_token = login_response['access_token']
            return {
                "success": True,
                "message": "Login successful",
                "token_type": login_response.get('token_type', 'bearer'),
                "token_preview": f"{auth_token[:20]}..." if auth_token else None
            }
        else:
            return {"success": False, "error": "No access token in response"}
            
    except httpx.RequestError as e:
        return {"success": False, "error": f"Connection failed: {str(e)}"}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"HTTP {e.response.status_code}: {e.response.text}"}

@mcp.tool()
def get_products(skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    """Get products from the API with pagination (requires authentication)"""
    global auth_token
    
    # Check if we have an authentication token
    if not auth_token:
        return {
            "error": "Not authenticated. Please login first using the login tool.",
            "suggestion": "Call login(username='neel', password='neel') first"
        }
    
    try:
        response = httpx.get(
            'http://127.0.0.1:8000/api/v1/products/',
            params={
                'skip': skip,
                'limit': limit
            },
            headers={
                'accept': 'application/json',
                # 'Authorization': f'Bearer {auth_token}'
            },
            timeout=10.0
        )
        
        response.raise_for_status()
        return {
            "success": True,
            "data": response.json()
        }
        
    except httpx.RequestError as e:
        return {"success": False, "error": f"Connection failed: {str(e)}"}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            # Token might be expired, clear it
            auth_token = None
            return {
                "success": False, 
                "error": "Authentication failed. Token may be expired. Please login again.",
                "suggestion": "Call login(username='neel', password='neel') again"
            }
        return {"success": False, "error": f"HTTP {e.response.status_code}: {e.response.text}"}

@mcp.tool()
def logout() -> Dict[str, str]:
    """Logout and clear the authentication token"""
    global auth_token
    auth_token = None
    return {"success": True, "message": "Logged out successfully"}

@mcp.tool()
def get_auth_status() -> Dict[str, Any]:
    """Check current authentication status"""
    global auth_token
    return {
        "authenticated": auth_token is not None,
        "token_preview": f"{auth_token[:20]}..." if auth_token else None
    }

if __name__ == "__main__":
    mcp.run()