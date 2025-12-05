# Playwright CDP Controller
# Connect to Orbita browser via CDP using Playwright

import os
import asyncio
import subprocess
import socket
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not installed. Run: pip install playwright")


@dataclass
class BrowserInstance:
    """Running browser instance."""
    process: subprocess.Popen
    profile_id: str
    debug_port: int
    profile_path: str
    browser: Optional[Any] = None
    context: Optional[Any] = None
    page: Optional[Any] = None


class PlaywrightCDP:
    """
    Control Orbita browser via Playwright CDP connection.
    
    Benefits:
    - No ChromeDriver needed
    - No WebDriver detection
    - Playwright's powerful API
    - Auto-wait, better selectors
    """
    
    ORBITA_PATH = "trinhduyet/orbita-browser/chrome.exe"
    EXTENSIONS_DIR = "extensions"
    
    def __init__(self, orbita_path: str = None, extensions_dir: str = None):
        self.orbita_path = orbita_path or self.ORBITA_PATH
        self.extensions_dir = extensions_dir or self.EXTENSIONS_DIR
        self.instances: Dict[str, BrowserInstance] = {}
        self._playwright = None
        self._next_port = 9222
    
    def _find_free_port(self, start_port: int = 9222) -> int:
        """Find available port."""
        port = start_port
        while port < 65535:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except OSError:
                port += 1
        raise RuntimeError("No free port")
    
    def _get_extension_paths(self) -> List[str]:
        """Get extension paths including stealth."""
        paths = []
        if os.path.isdir(self.extensions_dir):
            for name in os.listdir(self.extensions_dir):
                ext_path = os.path.join(self.extensions_dir, name)
                if os.path.isdir(ext_path):
                    paths.append(os.path.abspath(ext_path))
        return paths
    
    def _wait_for_cdp(self, port: int, timeout: float = 15) -> bool:
        """Wait for CDP to be ready."""
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
    
    async def launch(
        self,
        profile_id: str,
        profile_path: str,
        debug_port: int = None,
        headless: bool = False
    ) -> Optional[Page]:
        """
        Launch Orbita and connect via Playwright CDP.
        
        Args:
            profile_id: Unique identifier
            profile_path: Browser profile path
            debug_port: CDP port (auto if None)
            headless: Headless mode
            
        Returns:
            Playwright Page object
        """
        if not PLAYWRIGHT_AVAILABLE:
            print("Playwright not available")
            return None
        
        # Check if already running
        if profile_id in self.instances:
            inst = self.instances[profile_id]
            if inst.process.poll() is None and inst.page:
                return inst.page
            else:
                await self.close(profile_id)
        
        # Find port
        if debug_port is None:
            debug_port = self._find_free_port(self._next_port)
            self._next_port = debug_port + 1
        
        # Build command
        chrome_path = os.path.abspath(self.orbita_path)
        profile_abs = os.path.abspath(profile_path)
        
        args = [
            chrome_path,
            f"--user-data-dir={profile_abs}",
            f"--remote-debugging-port={debug_port}",
            "--remote-allow-origins=*",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--force-dark-mode",
        ]
        
        # Extensions
        ext_paths = self._get_extension_paths()
        if ext_paths:
            args.append(f"--load-extension={','.join(ext_paths)}")
        
        if headless:
            args.append("--headless=new")
        
        try:
            # Launch browser process
            process = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for CDP
            if not self._wait_for_cdp(debug_port, timeout=15):
                process.terminate()
                print(f"CDP not ready on port {debug_port}")
                return None
            
            # Connect Playwright
            if not self._playwright:
                self._playwright = await async_playwright().start()
            
            browser = await self._playwright.chromium.connect_over_cdp(
                f"http://127.0.0.1:{debug_port}"
            )
            
            # Get existing context and page
            contexts = browser.contexts
            if contexts:
                context = contexts[0]
                pages = context.pages
                page = pages[0] if pages else await context.new_page()
            else:
                context = await browser.new_context()
                page = await context.new_page()
            
            # Store instance
            instance = BrowserInstance(
                process=process,
                profile_id=profile_id,
                debug_port=debug_port,
                profile_path=profile_abs,
                browser=browser,
                context=context,
                page=page
            )
            self.instances[profile_id] = instance
            
            print(f"Launched {profile_id} with Playwright CDP on port {debug_port}")
            return page
            
        except Exception as e:
            print(f"Launch error: {e}")
            return None
    
    async def close(self, profile_id: str) -> bool:
        """Close browser instance."""
        if profile_id not in self.instances:
            return False
        
        inst = self.instances[profile_id]
        
        try:
            if inst.browser:
                await inst.browser.close()
        except:
            pass
        
        try:
            inst.process.terminate()
            inst.process.wait(timeout=5)
        except:
            try:
                inst.process.kill()
            except:
                pass
        
        del self.instances[profile_id]
        return True
    
    async def close_all(self) -> int:
        """Close all instances."""
        count = 0
        for pid in list(self.instances.keys()):
            if await self.close(pid):
                count += 1
        
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        
        return count
    
    def get_page(self, profile_id: str) -> Optional[Page]:
        """Get page for profile."""
        inst = self.instances.get(profile_id)
        return inst.page if inst else None
    
    def is_running(self, profile_id: str) -> bool:
        """Check if profile is running."""
        if profile_id not in self.instances:
            return False
        return self.instances[profile_id].process.poll() is None
