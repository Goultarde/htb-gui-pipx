"""
HTB API Client
Base HTTP client with debug logging and TLS verification disabled.
"""

import requests
import urllib3
from typing import Any, Optional, Tuple

from config import config, API_V4, API_V5
from utils.debug import debug_request, debug_response, debug_log

# Disable SSL warnings (as requested)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HTBClient:
    """
    Base HTTP client for HackTheBox API.
    Handles authentication, requests, and debug logging.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False  # Disable TLS verification as requested
        debug_log("CLIENT", "HTBClient initialized (TLS verification disabled)")
    
    def _get_headers(self) -> dict:
        """Get request headers with authorization."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "HTB-Desktop-Client/1.0"
        }
        
        if config.api_token:
            headers["Authorization"] = f"Bearer {config.api_token}"
        
        return headers
    
    def get(self, endpoint: str, params: Optional[dict] = None, 
            version: str = "v4") -> Tuple[bool, Any]:
        """
        Make a GET request to the API.
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            version: API version ('v4' or 'v5')
        
        Returns:
            Tuple of (success, data/error_message)
        """
        base = API_V4 if version == "v4" else API_V5
        url = f"{base}{endpoint}"
        
        debug_request("GET", url)
        
        try:
            response = self.session.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=30
            )
            
            # Siempre comprobar status primero (429 = rate limit, etc.)
            if response.status_code >= 400:
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    try:
                        data = response.json()
                        error_msg = data.get('message', data.get('error', f'HTTP {response.status_code}'))
                    except Exception:
                        error_msg = f"HTTP {response.status_code}"
                else:
                    if response.status_code == 429:
                        error_msg = "Rate limit (429). Espera unos segundos antes de reintentar."
                    else:
                        error_msg = f"HTTP {response.status_code}"
                debug_response(response.status_code, url, error_msg)
                return False, error_msg
            
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                data = response.json()
                debug_response(response.status_code, url, data)
                return True, data
            else:
                # Binario (ej. archivo .ovpn) solo si 200
                debug_response(response.status_code, url,
                              f"Binary response ({len(response.content)} bytes)")
                return True, response.content
                
        except requests.exceptions.Timeout:
            debug_response(0, url, error="Request timeout")
            return False, "Request timeout"
        except requests.exceptions.ConnectionError as e:
            debug_response(0, url, error=f"Connection error: {e}")
            return False, f"Connection error: {e}"
        except Exception as e:
            debug_response(0, url, error=str(e))
            return False, str(e)
    
    def post(self, endpoint: str, data: Optional[dict] = None,
             version: str = "v4") -> Tuple[bool, Any]:
        """
        Make a POST request to the API.
        
        Args:
            endpoint: API endpoint (without base URL)
            data: JSON body data
            version: API version ('v4' or 'v5')
        
        Returns:
            Tuple of (success, data/error_message)
        """
        base = API_V4 if version == "v4" else API_V5
        url = f"{base}{endpoint}"
        
        debug_request("POST", url, data)
        
        try:
            response = self.session.post(
                url,
                headers=self._get_headers(),
                json=data,
                timeout=30
            )
            
            response_data = response.json()
            debug_response(response.status_code, url, response_data)
            
            if response.status_code >= 400:
                error_msg = response_data.get('message', f'HTTP {response.status_code}')
                return False, error_msg
            
            return True, response_data
            
        except requests.exceptions.Timeout:
            debug_response(0, url, error="Request timeout")
            return False, "Request timeout"
        except requests.exceptions.ConnectionError as e:
            debug_response(0, url, error=f"Connection error: {e}")
            return False, f"Connection error: {e}"
        except Exception as e:
            debug_response(0, url, error=str(e))
            return False, str(e)


# Global client instance
client = HTBClient()
