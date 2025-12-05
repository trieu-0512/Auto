# CDP Browser Launcher
# Launch Orbita with remote debugging port for CDP control

import os
import subprocess
import time
import socket
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class BrowserInstance:
    """Running browser instance."""
    process: subprocess.Popen
    profile_id: str
    debug_port: int
    profile_path: str


class CDPBrowserLauncher:
    """
    Launch Orbita browser with CDP debugging enabled.
    """
    
    ORBITA_PATH = "trinhduyet/orbita-browser/chrome.exe"
    EXTENSIONS_DIR = "extensions"
    
    def __init__(self, orbita_path: str = None, extensions_dir: str = None):
        self.orbita_path = orbita_path or self.ORBITA_PATH
        self.extensions_dir = extensions_dir or self.EXTENSIONS_DIR
        self.instances: dict[str, BrowserInstance] = {}
        self._next_port = 9222
    
    def _find_free_port(self, start_port: int = 9222) -> int:
        """Find available port for debugging."""
        port = start_port
        while port < 65535:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except OSError:
                port += 1
        raise RuntimeError("No free port available")
    
    def _get_extension_paths(self) -> list[str]:
        """Get all extension paths including stealth."""
        paths = []
        if os.path.isdir(self.extensions_dir):
            for name in os.listdir(self.extensions_dir):
                ext_path = os.path.join(self.extensions_dir, name)
                if os.path.isdir(ext_path):
                    paths.append(os.path.abspath(ext_path))
        return paths
    
    def launch(
        self,
        profile_id: str,
        profile_path: str,
        debug_port: int = None,
        window_position: Tuple[int, int] = None,
        headless: bool = False
    ) -> Optional[BrowserInstance]:
        """
        Launch browser with CDP debugging enabled.
        
        Args:
            profile_id: Unique profile identifier
            profile_path: Path to profile directory
            debug_port: CDP debug port (auto-assign if None)
            window_position: (x, y) window position
            headless: Run in headless mode
            
        Returns:
            BrowserInstance or None if failed
        """
        # Check if already running
        if profile_id in self.instances:
            inst = self.instances[profile_id]
            if inst.process.poll() is None:
                print(f"Profile {profile_id} already running on port {inst.debug_port}")
                return inst
            else:
                del self.instances[profile_id]
        
        # Find free port
        if debug_port is None:
            debug_port = self._find_free_port(self._next_port)
            self._next_port = debug_port + 1
        
        # Build command
        chrome_path = os.path.abspath(self.orbita_path)
        profile_abs_path = os.path.abspath(profile_path)
        
        args = [
            chrome_path,
            f"--user-data-dir={profile_abs_path}",
            f"--remote-debugging-port={debug_port}",
            "--remote-allow-origins=*",
        ]
        
        # Window position
        if window_position:
            x, y = window_position
            args.append(f"--window-position={x},{y}")
        
        # Extensions
        ext_paths = self._get_extension_paths()
        if ext_paths:
            args.append(f"--load-extension={','.join(ext_paths)}")
        
        # Anti-detection flags
        args.extend([
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--force-dark-mode",
        ])
        
        # Headless
        if headless:
            args.append("--headless=new")
        
        try:
            # Launch process
            process = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for CDP to be ready
            if not self._wait_for_cdp(debug_port, timeout=15):
                process.terminate()
                print(f"CDP not ready on port {debug_port}")
                return None
            
            # Create instance
            instance = BrowserInstance(
                process=process,
                profile_id=profile_id,
                debug_port=debug_port,
                profile_path=profile_abs_path
            )
            self.instances[profile_id] = instance
            
            print(f"Launched {profile_id} with CDP on port {debug_port}")
            return instance
            
        except Exception as e:
            print(f"Launch error: {e}")
            return None
    
    def _wait_for_cdp(self, port: int, timeout: float = 15) -> bool:
        """Wait for CDP endpoint to be ready."""
        import urllib.request
        
        start = time.time()
        while time.time() - start < timeout:
            try:
                url = f"http://127.0.0.1:{port}/json/version"
                with urllib.request.urlopen(url, timeout=1) as resp:
                    if resp.status == 200:
                        return True
            except:
                pass
            time.sleep(0.5)
        return False
    
    def close(self, profile_id: str) -> bool:
        """Close browser instance."""
        if profile_id not in self.instances:
            return False
        
        instance = self.instances[profile_id]
        try:
            instance.process.terminate()
            instance.process.wait(timeout=5)
        except:
            try:
                instance.process.kill()
            except:
                pass
        
        del self.instances[profile_id]
        print(f"Closed {profile_id}")
        return True
    
    def close_all(self) -> int:
        """Close all browser instances."""
        count = 0
        for profile_id in list(self.instances.keys()):
            if self.close(profile_id):
                count += 1
        return count
    
    def get_instance(self, profile_id: str) -> Optional[BrowserInstance]:
        """Get browser instance by profile ID."""
        return self.instances.get(profile_id)
    
    def is_running(self, profile_id: str) -> bool:
        """Check if profile is running."""
        if profile_id not in self.instances:
            return False
        return self.instances[profile_id].process.poll() is None
