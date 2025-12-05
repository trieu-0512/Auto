# Geolocation Manager - Sync GPS location with IP address
# Automatically fetches geolocation from IP and applies to browser

import requests
import json
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class GeoLocation:
    """Geolocation data from IP lookup."""
    latitude: float
    longitude: float
    accuracy: float = 100.0
    city: str = ""
    country: str = ""
    timezone: str = ""
    ip: str = ""


class GeolocationManager:
    """
    Manager for syncing browser geolocation with IP address.
    Uses free IP geolocation APIs to get coordinates from proxy IP.
    """
    
    # Free IP geolocation APIs (no API key required)
    GEOIP_APIS = [
        "http://ip-api.com/json/{ip}",
        "https://ipapi.co/{ip}/json/",
        "https://ipwho.is/{ip}",
    ]
    
    def __init__(self):
        self.cache: Dict[str, GeoLocation] = {}
    
    def get_location_from_ip(self, ip: str = None, proxy: str = None) -> Optional[GeoLocation]:
        """
        Get geolocation from IP address.
        
        Args:
            ip: IP address to lookup (if None, uses current public IP)
            proxy: Proxy string to use for request and get its IP location
            
        Returns:
            GeoLocation object or None if failed
        """
        # Check cache first
        cache_key = ip or proxy or "current"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # If proxy provided, extract IP or use proxy to get public IP
        if proxy and not ip:
            ip = self._get_ip_from_proxy(proxy)
        
        # Try each API until one works
        for api_url in self.GEOIP_APIS:
            try:
                url = api_url.format(ip=ip if ip else "")
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    location = self._parse_api_response(data, api_url)
                    if location:
                        self.cache[cache_key] = location
                        return location
            except Exception as e:
                print(f"GeoIP API error ({api_url}): {e}")
                continue
        
        return None
    
    def _get_ip_from_proxy(self, proxy: str) -> Optional[str]:
        """Extract IP from proxy string or get public IP through proxy."""
        # Parse proxy format: host:port or host:port:user:pass
        parts = proxy.split(":")
        if len(parts) >= 2:
            host = parts[0]
            # If host is already an IP, return it
            if self._is_valid_ip(host):
                return host
            
            # Otherwise, make request through proxy to get public IP
            try:
                port = parts[1]
                proxy_url = f"http://{proxy}" if len(parts) == 2 else f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
                proxies = {"http": proxy_url, "https": proxy_url}
                response = requests.get("https://api.ipify.org?format=json", proxies=proxies, timeout=10)
                if response.status_code == 200:
                    return response.json().get("ip")
            except:
                pass
        
        return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Check if string is a valid IP address."""
        parts = ip.split(".")
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False
    
    def _parse_api_response(self, data: Dict, api_url: str) -> Optional[GeoLocation]:
        """Parse response from different GeoIP APIs."""
        try:
            # ip-api.com format
            if "ip-api.com" in api_url:
                if data.get("status") == "success":
                    return GeoLocation(
                        latitude=data.get("lat", 0),
                        longitude=data.get("lon", 0),
                        city=data.get("city", ""),
                        country=data.get("country", ""),
                        timezone=data.get("timezone", ""),
                        ip=data.get("query", "")
                    )
            
            # ipapi.co format
            elif "ipapi.co" in api_url:
                if "error" not in data:
                    return GeoLocation(
                        latitude=data.get("latitude", 0),
                        longitude=data.get("longitude", 0),
                        city=data.get("city", ""),
                        country=data.get("country_name", ""),
                        timezone=data.get("timezone", ""),
                        ip=data.get("ip", "")
                    )
            
            # ipwho.is format
            elif "ipwho.is" in api_url:
                if data.get("success", False):
                    return GeoLocation(
                        latitude=data.get("latitude", 0),
                        longitude=data.get("longitude", 0),
                        city=data.get("city", ""),
                        country=data.get("country", ""),
                        timezone=data.get("timezone", {}).get("id", ""),
                        ip=data.get("ip", "")
                    )
        except Exception as e:
            print(f"Error parsing GeoIP response: {e}")
        
        return None
    
    def get_chrome_geolocation_args(self, location: GeoLocation) -> list:
        """
        Get Chrome command line arguments for geolocation override.
        
        Note: Chrome doesn't support geolocation via command line.
        Use CDP (Chrome DevTools Protocol) instead.
        """
        return []
    
    def get_cdp_geolocation_override(self, location: GeoLocation) -> Dict:
        """
        Get CDP command for geolocation override.
        Use with Selenium's execute_cdp_cmd.
        
        Returns:
            Dict with CDP parameters for Emulation.setGeolocationOverride
        """
        return {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "accuracy": location.accuracy
        }
    
    def apply_geolocation_to_driver(self, driver, location: GeoLocation) -> bool:
        """
        Apply geolocation override to Selenium WebDriver.
        
        Args:
            driver: Selenium WebDriver instance
            location: GeoLocation to apply
            
        Returns:
            True if successful
        """
        try:
            # Use Chrome DevTools Protocol to override geolocation
            driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "accuracy": location.accuracy
            })
            
            # Also override timezone if available
            if location.timezone:
                driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {
                    "timezoneId": location.timezone
                })
            
            print(f"Geolocation set to: {location.latitude}, {location.longitude} ({location.city}, {location.country})")
            return True
        except Exception as e:
            print(f"Error setting geolocation: {e}")
            return False
    
    def apply_geolocation_to_preferences(self, preferences_path: str, location: GeoLocation) -> bool:
        """
        Apply geolocation to Chrome Preferences file (for Orbita/Gologin).
        
        Args:
            preferences_path: Path to Preferences JSON file
            location: GeoLocation to apply
            
        Returns:
            True if successful
        """
        try:
            with open(preferences_path, 'r', encoding='utf-8') as f:
                prefs = json.load(f)
            
            # Update gologin section with geolocation
            if "gologin" not in prefs:
                prefs["gologin"] = {}
            
            prefs["gologin"]["geolocation"] = {
                "mode": "allow",
                "latitude": location.latitude,
                "longitude": location.longitude,
                "accuracy": location.accuracy
            }
            
            # Also set timezone if available
            if location.timezone:
                prefs["gologin"]["timezone"] = {
                    "id": location.timezone
                }
            
            # Align WebRTC public IP with detected IP to avoid leaks
            if "webRTC" not in prefs["gologin"]:
                prefs["gologin"]["webRTC"] = {}
            prefs["gologin"]["webRTC"].update({
                "mode": "public",
                "enabled": True,
                "customize": True,
                "fillBasedOnIp": True,
                "publicIp": location.ip or ""
            })
            
            with open(preferences_path, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, indent=2)
            
            print(f"Preferences updated with geolocation: {location.latitude}, {location.longitude}")
            return True
        except Exception as e:
            print(f"Error updating preferences: {e}")
            return False
