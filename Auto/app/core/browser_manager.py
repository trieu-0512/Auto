# Multi-Profile Fingerprint Automation
# Browser Manager for browser sessions

import os
import subprocess
from typing import Dict, Optional, Tuple, List, Any
from datetime import datetime

from app.data.profile_models import Profile
from app.core.profile_manager import ProfileManager
from app.core.geolocation_manager import GeolocationManager, GeoLocation
from app.core.fingerprint_generator import FingerprintGenerator

# Optional Selenium imports (for automation mode)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class BrowserManager:
    """
    Manager for browser sessions.
    Supports two modes:
    - Manual mode: Opens browser with subprocess (no automation control)
    - Automation mode: Uses Selenium WebDriver (requires matching ChromeDriver)
    """
    
    # Default Orbita browser path
    ORBITA_PATH = "trinhduyet/orbita-browser/chrome.exe"
    
    # Default window size (for single profile)
    DEFAULT_WINDOW_WIDTH = 800
    DEFAULT_WINDOW_HEIGHT = 600
    
    # Screen dimensions for position calculation
    SCREEN_WIDTH = 1920
    SCREEN_HEIGHT = 1080
    
    # Grid layout for batch mode: 5 columns x 2 rows = 10 profiles max
    GRID_COLS = 5
    GRID_ROWS = 2
    MAX_CONCURRENT_PROFILES = 10
    
    def __init__(
        self,
        profile_manager: ProfileManager = None,
        orbita_path: str = None,
        extensions_dir: str = "extensions"
    ):
        """
        Initialize BrowserManager.
        
        Args:
            profile_manager: ProfileManager instance
            orbita_path: Path to Orbita browser executable
            extensions_dir: Path to extensions directory
        """
        self.profile_manager = profile_manager or ProfileManager()
        self.orbita_path = orbita_path or self.ORBITA_PATH
        self.extensions_dir = extensions_dir
        self.geolocation_manager = GeolocationManager()
        self.fingerprint_generator = FingerprintGenerator()
        # Orbita browser version - update this when upgrading Orbita
        self.orbita_version = "129"
        # Store both subprocess processes and selenium drivers
        self.active_sessions: Dict[str, Any] = {}
        self.active_processes: Dict[str, subprocess.Popen] = {}
    
    def build_chrome_options(
        self,
        profile: Profile,
        window_position: Tuple[int, int] = None,
        extensions: List[str] = None
    ) -> ChromeOptions:
        """
        Build ChromeOptions with all required arguments.
        
        Args:
            profile: Profile to launch
            window_position: (x, y) window position
            extensions: List of extension names to load
            
        Returns:
            Configured ChromeOptions
        """
        options = ChromeOptions()
        
        # Set binary location - use absolute path
        options.binary_location = os.path.abspath(self.orbita_path)
        
        # Set user data directory - MUST be absolute path for Chrome to load profile data
        profile_abs_path = os.path.abspath(profile.path)
        options.add_argument(f"--user-data-dir={profile_abs_path}")
        
        # Set window position
        if window_position:
            x, y = window_position
            options.add_argument(f"--window-position={x},{y}")
        else:
            options.add_argument("--window-position=0,0")
        
        # Force dark mode
        options.add_argument("--force-dark-mode")
        
        # Load extensions
        extension_paths = self._get_extension_paths(extensions)
        if extension_paths:
            options.add_argument(f"--load-extension={','.join(extension_paths)}")
        
        # Anti-detection arguments
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-browser-side-navigation")
        options.add_argument("--disable-gpu")
        
        # Hide automation flags
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Set preferences to hide webdriver
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "webrtc.ip_handling_policy": "disable_non_proxied_udp",
            "webrtc.multiple_routes_enabled": False,
            "webrtc.nonproxied_udp_enabled": False
        }
        options.add_experimental_option("prefs", prefs)
        
        return options
    
    def _get_extension_paths(self, extensions: List[str] = None) -> List[str]:
        """
        Get full paths to extensions.
        
        Args:
            extensions: List of extension names
            
        Returns:
            List of full extension paths
        """
        paths = []
        
        if not extensions:
            # Load all extensions from directory
            if os.path.isdir(self.extensions_dir):
                for name in os.listdir(self.extensions_dir):
                    ext_path = os.path.join(self.extensions_dir, name)
                    if os.path.isdir(ext_path):
                        paths.append(os.path.abspath(ext_path))
        else:
            # Load specified extensions
            for name in extensions:
                ext_path = os.path.join(self.extensions_dir, name)
                if os.path.isdir(ext_path):
                    paths.append(os.path.abspath(ext_path))
        
        return paths
    
    def calculate_window_position(self, index: int) -> Tuple[int, int]:
        """
        Calculate non-overlapping window position.
        
        Args:
            index: Window index (0-based)
            
        Returns:
            (x, y) position tuple
        """
        # Calculate grid layout
        cols = self.SCREEN_WIDTH // self.DEFAULT_WINDOW_WIDTH
        if cols < 1:
            cols = 1
        
        rows = self.SCREEN_HEIGHT // self.DEFAULT_WINDOW_HEIGHT
        if rows < 1:
            rows = 1
        
        # Total positions in one screen
        positions_per_screen = cols * rows
        
        # Calculate position with offset for overflow
        screen_offset = index // positions_per_screen
        local_index = index % positions_per_screen
        
        row = local_index // cols
        col = local_index % cols
        
        # Add small offset for each screen cycle to avoid overlap
        x = col * self.DEFAULT_WINDOW_WIDTH + (screen_offset * 20)
        y = row * self.DEFAULT_WINDOW_HEIGHT + (screen_offset * 20)
        
        return (x, y)
    
    def launch_profile(
        self,
        profile_id: str,
        window_position: Tuple[int, int] = None,
        extensions: List[str] = None,
        use_selenium: bool = False,
        sync_geolocation: bool = True
    ) -> Optional[Any]:
        """
        Launch browser for profile.
        
        Args:
            profile_id: Profile ID to launch
            window_position: Optional window position
            extensions: Optional list of extensions
            use_selenium: If True, use Selenium (requires matching ChromeDriver)
                         If False, use subprocess (manual control only)
            sync_geolocation: If True, sync GPS location with proxy IP
            
        Returns:
            Process or WebDriver instance, or None if failed
        """
        # Get profile
        profile = self.profile_manager.get_profile(profile_id)
        if not profile or not profile.exists:
            print(f"Profile {profile_id} not found or missing")
            return None
        
        # Fix User Agent to match Orbita version
        self._fix_user_agent(profile)
        
        # Check if already running
        if profile_id in self.active_processes or profile_id in self.active_sessions:
            print(f"Profile {profile_id} is already running")
            return self.active_processes.get(profile_id) or self.active_sessions.get(profile_id)
        
        # Sync geolocation with proxy IP before launching
        if sync_geolocation:
            self._sync_geolocation_with_proxy(profile)
        
        if use_selenium and SELENIUM_AVAILABLE:
            return self._launch_with_selenium(profile, profile_id, window_position, extensions, sync_geolocation)
        else:
            return self._launch_with_subprocess(profile, profile_id, window_position, extensions)
    
    def _launch_with_subprocess(
        self,
        profile: Profile,
        profile_id: str,
        window_position: Tuple[int, int] = None,
        extensions: List[str] = None
    ) -> Optional[subprocess.Popen]:
        """
        Launch browser using subprocess (manual control mode).
        This opens the browser with profile data but without automation control.
        """
        try:
            # Build command line arguments
            chrome_path = os.path.abspath(self.orbita_path)
            profile_path = os.path.abspath(profile.path)
            
            args = [
                chrome_path,
                f"--user-data-dir={profile_path}",
            ]
            
            # Window position
            if window_position:
                x, y = window_position
                args.append(f"--window-position={x},{y}")
            else:
                args.append("--window-position=0,0")
            
            # Force dark mode
            args.append("--force-dark-mode")
            
            # Load extensions
            extension_paths = self._get_extension_paths(extensions)
            if extension_paths:
                args.append(f"--load-extension={','.join(extension_paths)}")
            
            # Additional arguments
            args.extend([
                "--no-first-run",
                "--no-default-browser-check",
            ])
            
            # Launch browser
            process = subprocess.Popen(args)
            
            # Store process
            self.active_processes[profile_id] = process
            
            # Update status
            self.profile_manager.update_profile_status(profile_id, "running")
            self.profile_manager.update_last_run(profile_id)
            
            print(f"Launched profile {profile_id} (subprocess mode)")
            return process
            
        except Exception as e:
            print(f"Error launching profile {profile_id}: {e}")
            self.profile_manager.update_profile_status(profile_id, "error")
            return None
    
    def _launch_with_selenium(
        self,
        profile: Profile,
        profile_id: str,
        window_position: Tuple[int, int] = None,
        extensions: List[str] = None,
        sync_geolocation: bool = True
    ) -> Optional[Any]:
        """
        Launch browser using Selenium WebDriver (automation mode).
        Requires matching ChromeDriver version.
        """
        if not SELENIUM_AVAILABLE:
            print("Selenium not available, falling back to subprocess")
            return self._launch_with_subprocess(profile, profile_id, window_position, extensions)
        
        try:
            # Build options
            options = self.build_chrome_options(profile, window_position, extensions)
            
            # Use chromedriver from project root
            chromedriver_path = os.path.abspath("chromedriver.exe")
            if not os.path.exists(chromedriver_path):
                # Try alternative path
                chromedriver_path = os.path.abspath("app/chromedriver")
            
            # Create WebDriver with Service
            if os.path.exists(chromedriver_path):
                service = Service(executable_path=chromedriver_path)
                driver = webdriver.Chrome(service=service, options=options)
            else:
                # Let Selenium find chromedriver in PATH
                driver = webdriver.Chrome(options=options)
            
            # Hide webdriver detection - CRITICAL for anti-detection
            self._apply_stealth_scripts(driver)
            
            # Apply geolocation override via CDP (for Selenium mode)
            if sync_geolocation:
                self._apply_geolocation_to_driver(driver, profile)
            
            # Store session
            self.active_sessions[profile_id] = driver
            
            # Update status
            self.profile_manager.update_profile_status(profile_id, "running")
            self.profile_manager.update_last_run(profile_id)
            
            print(f"Launched profile {profile_id} (Selenium mode)")
            return driver
            
        except Exception as e:
            print(f"Error launching profile {profile_id} with Selenium: {e}")
            print("Falling back to subprocess mode...")
            return self._launch_with_subprocess(profile, profile_id, window_position, extensions)
    
    def close_session(self, profile_id: str) -> bool:
        """
        Close browser session and update status.
        
        Args:
            profile_id: Profile ID to close
            
        Returns:
            True if successful
        """
        closed = False
        
        # Close subprocess if exists
        if profile_id in self.active_processes:
            try:
                process = self.active_processes[profile_id]
                process.terminate()
                process.wait(timeout=5)
            except Exception as e:
                print(f"Error closing process {profile_id}: {e}")
                try:
                    process.kill()
                except:
                    pass
            finally:
                del self.active_processes[profile_id]
                closed = True
        
        # Close Selenium session if exists
        if profile_id in self.active_sessions:
            try:
                driver = self.active_sessions[profile_id]
                driver.quit()
            except Exception as e:
                print(f"Error closing session {profile_id}: {e}")
            finally:
                del self.active_sessions[profile_id]
                closed = True
        
        if closed:
            self.profile_manager.update_profile_status(profile_id, "inactive")
        
        return closed
    
    def close_all_sessions(self) -> int:
        """
        Close all active sessions (both subprocess and Selenium).
        
        Returns:
            Number of sessions closed
        """
        count = 0
        # Get all profile IDs from both dictionaries
        profile_ids = set(list(self.active_sessions.keys()) + list(self.active_processes.keys()))
        
        for profile_id in profile_ids:
            if self.close_session(profile_id):
                count += 1
        
        return count
    
    def get_active_sessions(self) -> Dict[str, webdriver.Chrome]:
        """
        Get all active browser sessions.
        
        Returns:
            Dictionary of profile_id -> WebDriver
        """
        return self.active_sessions.copy()
    
    def get_session_count(self) -> int:
        """Get number of active sessions (both subprocess and Selenium)."""
        return len(self.active_sessions) + len(self.active_processes)
    
    def is_session_active(self, profile_id: str) -> bool:
        """Check if a session is active."""
        return profile_id in self.active_sessions or profile_id in self.active_processes
    
    def get_driver(self, profile_id: str) -> Optional[webdriver.Chrome]:
        """
        Get WebDriver for a profile.
        
        Args:
            profile_id: Profile ID
            
        Returns:
            WebDriver or None
        """
        return self.active_sessions.get(profile_id)
    
    def _sync_geolocation_with_proxy(self, profile: Profile) -> Optional[GeoLocation]:
        """
        Sync geolocation in Preferences file with proxy IP.
        This works for both subprocess and Selenium modes.
        
        Args:
            profile: Profile to sync
            
        Returns:
            GeoLocation if successful, None otherwise
        """
        try:
            # Get proxy from profile
            proxy = profile.proxy if hasattr(profile, 'proxy') else None
            
            if not proxy:
                print(f"No proxy configured for profile, using current IP for geolocation")
            
            # Get geolocation from IP
            location = self.geolocation_manager.get_location_from_ip(proxy=proxy)
            
            if location:
                # Update Preferences file
                preferences_path = os.path.join(profile.path, "Default", "Preferences")
                if os.path.exists(preferences_path):
                    self.geolocation_manager.apply_geolocation_to_preferences(
                        preferences_path, location
                    )
                    print(f"Synced geolocation: {location.city}, {location.country} ({location.latitude}, {location.longitude})")
                return location
            else:
                print("Could not get geolocation from IP")
                
        except Exception as e:
            print(f"Error syncing geolocation: {e}")
        
        return None
    
    def _apply_geolocation_to_driver(self, driver, profile: Profile) -> bool:
        """
        Apply geolocation override to Selenium WebDriver via CDP.
        
        Args:
            driver: Selenium WebDriver instance
            profile: Profile with proxy info
            
        Returns:
            True if successful
        """
        try:
            # Get proxy from profile
            proxy = profile.proxy if hasattr(profile, 'proxy') else None
            
            # Get geolocation from IP
            location = self.geolocation_manager.get_location_from_ip(proxy=proxy)
            
            if location:
                return self.geolocation_manager.apply_geolocation_to_driver(driver, location)
            
        except Exception as e:
            print(f"Error applying geolocation to driver: {e}")
        
        return False

    def _apply_stealth_scripts(self, driver) -> bool:
        """
        Apply stealth scripts to hide automation detection.
        Uses CDP to inject JavaScript that hides webdriver flags.
        
        Args:
            driver: Selenium WebDriver instance
            
        Returns:
            True if successful
        """
        try:
            # Use CDP to execute script before page loads
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    // Hide webdriver
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Hide automation flags
                    window.navigator.chrome = {
                        runtime: {},
                    };
                    
                    // Hide plugins length
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    
                    // Hide languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                    
                    // Overwrite permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                    
                    // Hide automation in user agent
                    Object.defineProperty(navigator, 'userAgent', {
                        get: () => navigator.userAgent.replace('HeadlessChrome', 'Chrome')
                    });
                """
            })
            
            print("Applied stealth scripts to hide automation")
            return True
            
        except Exception as e:
            print(f"Error applying stealth scripts: {e}")
            return False

    def _fix_user_agent(self, profile: Profile) -> bool:
        """
        Fix User Agent in profile to match Orbita browser version.
        
        Args:
            profile: Profile to fix
            
        Returns:
            True if successful
        """
        try:
            result = self.fingerprint_generator.update_user_agent(
                profile.path, 
                self.orbita_version
            )
            if result:
                print(f"Fixed User Agent to Chrome/{self.orbita_version}")
            return result
        except Exception as e:
            print(f"Error fixing User Agent: {e}")
            return False
