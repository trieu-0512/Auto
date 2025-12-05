# Automation Executor for running scripts with Selenium or Playwright CDP

import os
import time
import random
import json
import asyncio
from typing import Dict, Any, Optional, Callable, List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from app.core.script_manager import ScriptManager
from app.core.fingerprint_checker import FingerprintChecker


class AutomationExecutor:
    """Executor for running automation scripts."""
    
    ADDONS_DIR = "addons"
    
    def __init__(self, script_manager: ScriptManager = None):
        self.script_manager = script_manager or ScriptManager()
        self.fingerprint_checker = FingerprintChecker()
        self.running = False
        self.current_driver = None
        self.current_profile_id: str = ""
        self.log_callback: Optional[Callable[[str], None]] = None
        self.excel_data: Dict[str, str] = {}
    
    def set_log_callback(self, callback: Callable[[str], None]):
        """Set callback for logging messages."""
        self.log_callback = callback
    
    def log(self, message: str):
        """Log a message."""
        print(f"[Automation] {message}")
        if self.log_callback:
            self.log_callback(message)
    
    def load_addon_script(self, script_id: str) -> Optional[Dict]:
        """Load script from addons folder."""
        # Map script_id to addon file
        addon_files = {
            "reels_autopostvideo": "reels_autopostvideo.json",
            "instagram_postvideo": "instagram_postvideo.json",
            "gmail_login": "gmail.json",
        }
        
        filename = addon_files.get(script_id)
        if not filename:
            # Try direct filename
            filename = f"{script_id}.json"
        
        filepath = os.path.join(self.ADDONS_DIR, filename)
        if not os.path.exists(filepath):
            self.log(f"Addon script not found: {filepath}")
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.log(f"Error loading addon: {e}")
            return None

    def find_element(self, driver, locator: str, timeout: int = 10):
        """Find element using locator string."""
        if not locator:
            return None
        
        # Parse locator
        if locator.startswith("css:"):
            by = By.CSS_SELECTOR
            value = locator[4:]
        elif locator.startswith("xpath:"):
            by = By.XPATH
            value = locator[6:]
        else:
            # Try to find by text (button text, link text)
            try:
                element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{locator}')]"))
                )
                return element
            except:
                return None
        
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.log(f"Element not found: {locator}")
            return None
    
    def wait_random(self, min_sec: float = 1, max_sec: float = 3):
        """Wait random time to simulate human behavior."""
        wait_time = random.uniform(min_sec, max_sec)
        time.sleep(wait_time)
    
    def get_input_value(self, input_str: str, params: Dict = None) -> str:
        """Get actual input value, resolving excel: references."""
        if not input_str:
            return ""
        
        if input_str.startswith("excel:"):
            # Get from excel data or params
            col = input_str[6:]
            return self.excel_data.get(col, params.get(f"excel_{col}", ""))
        
        # Replace templated placeholders with params (e.g., {video_path})
        if params and "{" in input_str and "}" in input_str:
            try:
                return input_str.format(**params)
            except Exception:
                return input_str
        
        return input_str

    def load_automation_script(self, script_id: str) -> Optional[Dict]:
        """
        Load automation script from automation_scripts directory by script_id.
        """
        base_dir = "automation_scripts"
        for root, _, files in os.walk(base_dir):
            for fname in files:
                if fname.endswith(".json"):
                    path = os.path.join(root, fname)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if data.get("script_id") == script_id:
                            return data
                    except Exception:
                        continue
        return None
    
    def execute_step(self, driver, step: Dict, params: Dict = None) -> bool:
        """Execute a single automation step."""
        action = step.get("action", "")
        locator = step.get("locator", "")
        input_val = self.get_input_value(step.get("input", ""), params)
        desc = step.get("desc", "")
        
        self.log(f"Step: {desc} - Action: {action}")
        
        try:
            if action == "open_url":
                driver.get(input_val)
                self.wait_random(2, 4)
                return True
            
            elif action == "click":
                element = self.find_element(driver, locator)
                if element:
                    element.click()
                    self.wait_random(1, 2)
                    return True
                return False
            
            elif action == "enter_text":
                element = self.find_element(driver, locator)
                if element:
                    element.clear()
                    element.send_keys(input_val)
                    self.wait_random(0.5, 1)
                    return True
                return False
            
            elif action == "modeupload":
                # Handle file upload
                self.log("Upload mode - waiting for file input")
                self.wait_random(2, 3)
                return True
            
            elif action == "upload_paths_inputted":
                # Upload files from params
                file_path = params.get("upload_file", "")
                if file_path and os.path.exists(file_path):
                    file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                    file_input.send_keys(os.path.abspath(file_path))
                    self.wait_random(2, 4)
                return True
            
            elif action == "wait":
                # Wait for specified seconds
                wait_time = int(input_val) if input_val else 2
                self.log(f"Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                return True
            
            elif action == "upload_file":
                # Upload file from params
                file_path = ""
                
                # If input already resolved to a valid path, use it directly
                if input_val and os.path.exists(input_val):
                    file_path = input_val
                else:
                    param_key = input_val if input_val else "video_path"
                    file_path = params.get(param_key, "") if params else ""
                    if not file_path:
                        file_path = params.get("input_link", "") if params else ""
                
                if file_path and os.path.exists(file_path):
                    element = self.find_element(driver, locator, timeout=5)
                    if element:
                        element.send_keys(os.path.abspath(file_path))
                        self.log(f"Uploaded: {file_path}")
                        self.wait_random(2, 4)
                        return True
                    else:
                        # Try to find any file input
                        try:
                            file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                            file_input.send_keys(os.path.abspath(file_path))
                            self.log(f"Uploaded: {file_path}")
                            self.wait_random(2, 4)
                            return True
                        except:
                            self.log(f"Could not find file input")
                else:
                    self.log(f"File not found: {file_path}")
                return False
            
            elif action == "screenshot":
                # Take screenshot
                screenshot_name = input_val if input_val else "screenshot"
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                screenshot_dir = "data/screenshots"
                os.makedirs(screenshot_dir, exist_ok=True)
                screenshot_path = os.path.join(screenshot_dir, f"{screenshot_name}_{timestamp}.png")
                driver.save_screenshot(screenshot_path)
                self.log(f"Screenshot saved: {screenshot_path}")
                return True
            
            elif action == "scroll":
                # Scroll page
                pixels = int(input_val) if input_val else 500
                driver.execute_script(f"window.scrollBy(0, {pixels});")
                self.log(f"Scrolled {pixels}px")
                self.wait_random(1, 2)
                return True
            
            elif action == "fingerprint_check":
                # Kiểm tra fingerprint và xuất báo cáo
                profile_id = self.current_profile_id or "unknown"
                self.log(f"Bắt đầu kiểm tra fingerprint cho profile {profile_id}...")
                report = self.fingerprint_checker.check_fingerprint(driver, profile_id)
                
                # Log kết quả
                self.log(f"Kết quả: {report.get_summary()}")
                if report.has_critical_issues():
                    self.log("⚠️ CÓ VẤN ĐỀ NGHIÊM TRỌNG!")
                    for issue in report.issues:
                        if issue.severity == "critical":
                            self.log(f"  🔴 {issue.message}")
                else:
                    self.log("✅ Không có vấn đề nghiêm trọng")
                
                self.log(f"Báo cáo đã lưu tại: data/fingerprint_reports/")
                return True
            
            elif action == "quit":
                self.log("Script completed")
                return True
            
            else:
                self.log(f"Unknown action: {action}")
                return True
                
        except Exception as e:
            self.log(f"Step error: {e}")
            return False

    def execute_addon_script(
        self,
        driver,
        script_data: Dict,
        params: Dict = None,
        progress_callback: Callable[[int, int], None] = None
    ) -> bool:
        """Execute an addon script with steps."""
        steps = script_data.get("steps", [])
        if not steps:
            self.log("No steps in script")
            return False
        
        self.log(f"Executing: {script_data.get('description', 'Unknown script')}")
        
        total_steps = len(steps)
        for i, step in enumerate(steps):
            if not self.running:
                self.log("Execution stopped by user")
                break
            
            success = self.execute_step(driver, step, params)
            
            if progress_callback:
                progress_callback(i + 1, total_steps)
            
            if not success:
                self.log(f"Step {i+1} failed, continuing...")
        
        return True
    
    def execute_script(
        self,
        driver,
        script_id: str,
        params: Dict[str, Any],
        progress_callback: Callable[[int, int], None] = None,
        profile_id: str = ""
    ) -> bool:
        """Execute an automation script."""
        self.current_driver = driver
        self.current_profile_id = profile_id or params.get("profile_id", "unknown")
        self.running = True
        
        try:
            # Try to load addon script first
            addon_data = self.load_addon_script(script_id)
            if addon_data:
                return self.execute_addon_script(driver, addon_data, params, progress_callback)
            
            # Try to load automation script (JSON with steps)
            auto_data = self.load_automation_script(script_id)
            if auto_data:
                return self.execute_addon_script(driver, auto_data, params, progress_callback)
            
            # Fallback to built-in scripts
            self.log(f"Starting built-in script: {script_id}")
            
            if script_id == "auto_likelink":
                return self._execute_auto_like(driver, params, progress_callback)
            elif script_id == "auto_postwall":
                return self._execute_auto_postwall(driver, params, progress_callback)
            elif script_id == "addfriends":
                return self._execute_add_friends(driver, params, progress_callback)
            elif script_id == "auto_tuongtac_feed":
                return self._execute_tuongtac_feed(driver, params, progress_callback)
            else:
                self.log(f"Script not implemented: {script_id}")
                return False
                
        except Exception as e:
            self.log(f"Script error: {e}")
            return False
        finally:
            self.running = False
    
    def stop(self):
        """Stop current execution."""
        self.running = False
        self.log("Stopping automation...")
    
    # ==================== BUILT-IN SCRIPTS ====================
    
    def _execute_auto_like(self, driver, params: Dict, progress_callback) -> bool:
        """Execute auto like script."""
        file_path = params.get('input_link', 'like.txt')
        count = int(params.get('input_solan', 1))
        
        self.log(f"Auto like: {count} times from {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                links = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            self.log(f"File not found: {file_path}")
            return False
        
        for i, link in enumerate(links[:count]):
            if not self.running:
                break
            
            self.log(f"Liking {i+1}/{min(count, len(links))}: {link}")
            driver.get(link)
            self.wait_random(2, 4)
            
            try:
                like_btn = driver.find_element(By.XPATH, "//div[@aria-label='Thích' or @aria-label='Like']")
                like_btn.click()
                self.log(f"Liked: {link}")
            except:
                self.log(f"Could not like: {link}")
            
            if progress_callback:
                progress_callback(i + 1, min(count, len(links)))
            
            self.wait_random(3, 6)
        
        return True
    
    def _execute_auto_postwall(self, driver, params: Dict, progress_callback) -> bool:
        """Execute auto post to wall script."""
        count = int(params.get('input_solan', 1))
        delay = int(params.get('input_thoigian', 10))
        
        self.log(f"Auto post wall: {count} posts")
        driver.get("https://www.facebook.com")
        self.wait_random(3, 5)
        
        for i in range(count):
            if not self.running:
                break
            self.log(f"Posting {i+1}/{count}")
            if progress_callback:
                progress_callback(i + 1, count)
            time.sleep(delay)
        
        return True
    
    def _execute_add_friends(self, driver, params: Dict, progress_callback) -> bool:
        """Execute add friends script."""
        file_path = params.get('input_link', 'uid.txt')
        count = int(params.get('input_solan', 5))
        delay = int(params.get('input_thoigian', 20))
        
        self.log(f"Add friends: {count} from {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                uids = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            self.log(f"File not found: {file_path}")
            return False
        
        for i, uid in enumerate(uids[:count]):
            if not self.running:
                break
            
            self.log(f"Adding friend {i+1}/{min(count, len(uids))}: {uid}")
            driver.get(f"https://www.facebook.com/{uid}")
            self.wait_random(2, 4)
            
            if progress_callback:
                progress_callback(i + 1, min(count, len(uids)))
            time.sleep(delay)
        
        return True
    
    def _execute_tuongtac_feed(self, driver, params: Dict, progress_callback) -> bool:
        """Execute interact with feed script."""
        scroll_amount = int(params.get('input_solan', 5000))
        
        self.log(f"Interact feed: scroll {scroll_amount}px")
        driver.get("https://www.facebook.com")
        self.wait_random(3, 5)
        
        scrolled = 0
        while scrolled < scroll_amount and self.running:
            driver.execute_script("window.scrollBy(0, 500);")
            scrolled += 500
            self.wait_random(1, 2)
            
            if progress_callback:
                progress_callback(scrolled, scroll_amount)
        
        return True
    
    # ==================== INSTAGRAM REEL UPLOADER (Playwright CDP) ====================
    
    def execute_instagram_reel_upload(
        self,
        profile_id: str,
        profile_path: str,
        max_uploads: int = 1,
        random_order: bool = False,
        delay_min: int = 60,
        delay_max: int = 180,
        cdp_url: str = None,
        progress_callback: Callable[[int, int], None] = None
    ) -> dict:
        """
        Execute Instagram Reel upload using Playwright CDP.
        
        This uses Playwright CDP mode instead of Selenium for better anti-detection.
        Videos are loaded from data/instagram/{profile_id}/ folder.
        
        Args:
            profile_id: Profile ID (matches folder name in data/instagram/)
            profile_path: Browser profile path
            max_uploads: Maximum videos to upload
            random_order: Pick videos randomly or sequentially
            delay_min: Min delay between uploads (seconds)
            delay_max: Max delay between uploads (seconds)
            cdp_url: CDP WebSocket URL to connect to existing browser
            progress_callback: Progress callback (current, total)
        """
        self.log(f"🚀 Starting Instagram Reel Upload (Playwright)")
        self.log(f"   Profile: {profile_id}")
        self.log(f"   Max uploads: {max_uploads}")
        self.log(f"   Random order: {random_order}")
        self.log(f"   Delay: {delay_min}-{delay_max}s")
        
        try:
            # Import here to avoid circular imports
            from app.core.instagram_reel_uploader import run_instagram_upload_sync
            
            # Run synchronous wrapper
            results = run_instagram_upload_sync(
                profile_id=profile_id,
                profile_path=profile_path,
                max_uploads=max_uploads,
                random_order=random_order,
                delay_min=delay_min,
                delay_max=delay_max,
                cdp_url=cdp_url,
                log_callback=self.log,
                progress_callback=progress_callback
            )
            
            # Log results
            self.log(f"📊 Results: {results['success']}/{results['total']} uploaded")
            
            if progress_callback and results['total'] > 0:
                progress_callback(results['success'], results['total'])
            
            return results
            
        except ImportError as e:
            self.log(f"❌ Playwright not installed: {e}")
            self.log("   Run: pip install playwright")
            return {"total": 0, "success": 0, "failed": 0, "error": str(e)}
        except Exception as e:
            self.log(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return {"total": 0, "success": 0, "failed": 0, "error": str(e)}
    
    def is_instagram_upload_script(self, script_id: str) -> bool:
        """Check if script is Instagram upload script."""
        return script_id in ["instagram_upload_reel", "instagram_reel_upload"]
