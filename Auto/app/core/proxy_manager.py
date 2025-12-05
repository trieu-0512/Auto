# Multi-Profile Fingerprint Automation
# Proxy Manager for proxy configuration and authentication

import os
import re
import json
from typing import Optional, Tuple, Dict
from dataclasses import dataclass


@dataclass
class ProxyInfo:
    """Parsed proxy information."""
    host: str
    port: str
    username: str = ""
    password: str = ""
    mode: str = "http"  # http, socks5
    
    @property
    def requires_auth(self) -> bool:
        """Check if proxy requires authentication."""
        return bool(self.username and self.password)
    
    @property
    def address(self) -> str:
        """Get proxy address (host:port)."""
        return f"{self.host}:{self.port}"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "mode": self.mode
        }


class ProxyManager:
    """
    Manager for proxy configuration and authentication extension generation.
    """
    
    # Regex patterns for proxy validation
    HOST_PATTERN = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$|^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    PORT_PATTERN = r'^([1-9]|[1-9][0-9]{1,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$'
    
    # Proxy format patterns
    # Format: host:port or host:port:user:pass
    PROXY_PATTERN = r'^([^:]+):(\d+)(?::([^:]+):(.+))?$'
    
    def __init__(self, proxy_auth_dir: str = "data/proxyauth"):
        """
        Initialize ProxyManager.
        
        Args:
            proxy_auth_dir: Directory to store proxy auth extensions
        """
        self.proxy_auth_dir = proxy_auth_dir
    
    def validate_proxy_format(self, proxy_string: str) -> Tuple[bool, Optional[str]]:
        """
        Validate proxy format.
        
        Args:
            proxy_string: Proxy string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not proxy_string or not proxy_string.strip():
            return False, "Proxy string is empty"
        
        proxy_string = proxy_string.strip()
        
        # Try to parse
        match = re.match(self.PROXY_PATTERN, proxy_string)
        if not match:
            return False, "Invalid proxy format. Expected: host:port or host:port:user:pass"
        
        host, port, username, password = match.groups()
        
        # Validate host
        if not re.match(self.HOST_PATTERN, host):
            return False, f"Invalid host: {host}"
        
        # Validate port
        if not re.match(self.PORT_PATTERN, port):
            return False, f"Invalid port: {port}"
        
        # If username provided, password must also be provided
        if username and not password:
            return False, "Password required when username is provided"
        
        return True, None
    
    def parse_proxy(self, proxy_string: str) -> Optional[ProxyInfo]:
        """
        Parse proxy string into ProxyInfo.
        
        Args:
            proxy_string: Proxy string to parse
            
        Returns:
            ProxyInfo or None if invalid
        """
        is_valid, error = self.validate_proxy_format(proxy_string)
        if not is_valid:
            return None
        
        match = re.match(self.PROXY_PATTERN, proxy_string.strip())
        if not match:
            return None
        
        host, port, username, password = match.groups()
        
        return ProxyInfo(
            host=host,
            port=port,
            username=username or "",
            password=password or ""
        )
    
    def generate_proxy_auth_extension(
        self,
        proxy: ProxyInfo,
        extension_name: str = None
    ) -> Optional[str]:
        """
        Generate proxy authentication extension.
        
        Args:
            proxy: ProxyInfo with authentication details
            extension_name: Optional custom extension name
            
        Returns:
            Path to generated extension or None if failed
        """
        if not proxy.requires_auth:
            return None
        
        # Create extension directory
        ext_name = extension_name or f"proxy_auth_{proxy.host}_{proxy.port}"
        ext_path = os.path.join(self.proxy_auth_dir, ext_name)
        os.makedirs(ext_path, exist_ok=True)
        
        # Generate manifest.json
        manifest = {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Proxy Auth Extension",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version": "22.0.0"
        }
        
        manifest_path = os.path.join(ext_path, "manifest.json")
        try:
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)
        except IOError as e:
            print(f"Error writing manifest: {e}")
            return None
        
        # Generate background.js
        background_js = f'''var config = {{
    mode: "fixed_servers",
    rules: {{
        singleProxy: {{
            scheme: "http",
            host: "{proxy.host}",
            port: parseInt({proxy.port})
        }},
        bypassList: ["localhost"]
    }}
}};

chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

function callbackFn(details) {{
    return {{
        authCredentials: {{
            username: "{proxy.username}",
            password: "{proxy.password}"
        }}
    }};
}}

chrome.webRequest.onAuthRequired.addListener(
    callbackFn,
    {{urls: ["<all_urls>"]}},
    ['blocking']
);
'''
        
        background_path = os.path.join(ext_path, "background.js")
        try:
            with open(background_path, 'w', encoding='utf-8') as f:
                f.write(background_js)
        except IOError as e:
            print(f"Error writing background.js: {e}")
            return None
        
        return ext_path
    
    def get_proxy_auth_extension_path(self, proxy: ProxyInfo) -> Optional[str]:
        """
        Get or create proxy auth extension path.
        
        Args:
            proxy: ProxyInfo
            
        Returns:
            Path to extension or None
        """
        if not proxy.requires_auth:
            return None
        
        ext_name = f"proxy_auth_{proxy.host}_{proxy.port}"
        ext_path = os.path.join(self.proxy_auth_dir, ext_name)
        
        # Check if already exists
        if os.path.isdir(ext_path):
            return ext_path
        
        # Generate new extension
        return self.generate_proxy_auth_extension(proxy, ext_name)
    
    def cleanup_proxy_auth_extension(self, proxy: ProxyInfo) -> bool:
        """
        Remove proxy auth extension.
        
        Args:
            proxy: ProxyInfo
            
        Returns:
            True if successful
        """
        import shutil
        
        ext_name = f"proxy_auth_{proxy.host}_{proxy.port}"
        ext_path = os.path.join(self.proxy_auth_dir, ext_name)
        
        if os.path.isdir(ext_path):
            try:
                shutil.rmtree(ext_path)
                return True
            except Exception as e:
                print(f"Error removing extension: {e}")
                return False
        
        return True
    
    def format_proxy_for_selenium(self, proxy: ProxyInfo) -> str:
        """
        Format proxy for Selenium argument.
        
        Args:
            proxy: ProxyInfo
            
        Returns:
            Formatted proxy string
        """
        if proxy.requires_auth:
            return f"{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
        return f"{proxy.host}:{proxy.port}"
