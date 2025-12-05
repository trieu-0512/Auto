# Property-based tests for Proxy Manager
# Feature: multi-profile-fingerprint-automation

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
import tempfile
import os
import shutil

from app.core.proxy_manager import ProxyManager, ProxyInfo


@pytest.fixture
def proxy_manager():
    """Create a ProxyManager with temp directory."""
    temp_dir = tempfile.mkdtemp()
    manager = ProxyManager(proxy_auth_dir=temp_dir)
    yield manager
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestProxyFormatValidation:
    """
    **Feature: multi-profile-fingerprint-automation, Property 13: Proxy Format Validation**
    **Validates: Requirements 4.1**
    
    For any proxy string, the validation function SHALL accept valid formats
    (host:port, host:port:user:pass) and reject invalid formats.
    """
    
    # Valid IP addresses
    valid_ips = st.from_regex(
        r'^(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])$',
        fullmatch=True
    )
    
    # Valid ports (1-65535)
    valid_ports = st.integers(min_value=1, max_value=65535).map(str)
    
    @given(
        ip=st.from_regex(r'^(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])$', fullmatch=True),
        port=st.integers(min_value=1, max_value=65535)
    )
    @settings(max_examples=100)
    def test_valid_proxy_without_auth(self, ip, port):
        """Test that valid host:port format is accepted."""
        manager = ProxyManager()
        proxy_string = f"{ip}:{port}"
        
        is_valid, error = manager.validate_proxy_format(proxy_string)
        
        assert is_valid, f"Should accept valid proxy: {proxy_string}, error: {error}"
    
    @given(
        ip=st.from_regex(r'^(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])$', fullmatch=True),
        port=st.integers(min_value=1, max_value=65535),
        username=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        password=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N')))
    )
    @settings(max_examples=100)
    def test_valid_proxy_with_auth(self, ip, port, username, password):
        """Test that valid host:port:user:pass format is accepted."""
        manager = ProxyManager()
        proxy_string = f"{ip}:{port}:{username}:{password}"
        
        is_valid, error = manager.validate_proxy_format(proxy_string)
        
        assert is_valid, f"Should accept valid proxy with auth: {proxy_string}, error: {error}"
    
    @given(
        invalid_host=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('L',))),
        port=st.integers(min_value=1, max_value=65535)
    )
    @settings(max_examples=50)
    def test_invalid_host_rejected(self, invalid_host, port):
        """Test that invalid hosts are rejected."""
        manager = ProxyManager()
        # Ensure it's not accidentally a valid hostname
        if '.' in invalid_host or invalid_host.isdigit():
            return
        
        proxy_string = f"{invalid_host}:{port}"
        
        is_valid, error = manager.validate_proxy_format(proxy_string)
        
        assert not is_valid, f"Should reject invalid host: {proxy_string}"
    
    def test_empty_proxy_rejected(self):
        """Test that empty proxy string is rejected."""
        manager = ProxyManager()
        
        is_valid, error = manager.validate_proxy_format("")
        assert not is_valid
        
        is_valid, error = manager.validate_proxy_format("   ")
        assert not is_valid
    
    def test_invalid_port_rejected(self):
        """Test that invalid ports are rejected."""
        manager = ProxyManager()
        
        # Port > 65535
        is_valid, _ = manager.validate_proxy_format("192.168.1.1:70000")
        assert not is_valid
        
        # Non-numeric port
        is_valid, _ = manager.validate_proxy_format("192.168.1.1:abc")
        assert not is_valid


class TestProxyAuthExtensionGeneration:
    """
    **Feature: multi-profile-fingerprint-automation, Property 14: Proxy Auth Extension Generation**
    **Validates: Requirements 4.3**
    
    For any proxy with authentication (user:pass), the system SHALL generate
    a valid proxy auth extension with correct credentials.
    """
    
    @given(
        ip=st.from_regex(r'^(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])$', fullmatch=True),
        port=st.integers(min_value=1, max_value=65535),
        username=st.text(min_size=1, max_size=15, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'),
        password=st.text(min_size=1, max_size=15, alphabet='abcdefghijklmnopqrstuvwxyz0123456789')
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_extension_generated_for_auth_proxy(self, proxy_manager, ip, port, username, password):
        """Test that extension is generated for authenticated proxy."""
        proxy = ProxyInfo(
            host=ip,
            port=str(port),
            username=username,
            password=password
        )
        
        ext_path = proxy_manager.generate_proxy_auth_extension(proxy)
        
        assert ext_path is not None
        assert os.path.isdir(ext_path)
        assert os.path.isfile(os.path.join(ext_path, "manifest.json"))
        assert os.path.isfile(os.path.join(ext_path, "background.js"))
        
        # Verify credentials in background.js
        with open(os.path.join(ext_path, "background.js"), 'r', encoding='utf-8') as f:
            content = f.read()
            assert username in content
            assert password in content
            assert ip in content
    
    def test_no_extension_for_non_auth_proxy(self, proxy_manager):
        """Test that no extension is generated for non-authenticated proxy."""
        proxy = ProxyInfo(host="192.168.1.1", port="8080")
        
        ext_path = proxy_manager.generate_proxy_auth_extension(proxy)
        
        assert ext_path is None


class TestProxyParsing:
    """Test proxy string parsing."""
    
    def test_parse_simple_proxy(self):
        """Test parsing simple host:port proxy."""
        manager = ProxyManager()
        
        proxy = manager.parse_proxy("192.168.1.1:8080")
        
        assert proxy is not None
        assert proxy.host == "192.168.1.1"
        assert proxy.port == "8080"
        assert proxy.username == ""
        assert proxy.password == ""
        assert not proxy.requires_auth
    
    def test_parse_auth_proxy(self):
        """Test parsing proxy with authentication."""
        manager = ProxyManager()
        
        proxy = manager.parse_proxy("192.168.1.1:8080:user:pass123")
        
        assert proxy is not None
        assert proxy.host == "192.168.1.1"
        assert proxy.port == "8080"
        assert proxy.username == "user"
        assert proxy.password == "pass123"
        assert proxy.requires_auth
    
    def test_parse_invalid_proxy(self):
        """Test parsing invalid proxy returns None."""
        manager = ProxyManager()
        
        assert manager.parse_proxy("invalid") is None
        assert manager.parse_proxy("") is None
        assert manager.parse_proxy("host:abc") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
