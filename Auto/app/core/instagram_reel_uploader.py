# Instagram Reel Uploader
# Upload reels from profile folder with content management
# Uses Playwright CDP for anti-detection

import os
import asyncio
import random
import time
from typing import Optional, List, Tuple, Callable
from dataclasses import dataclass

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


@dataclass
class VideoContent:
    """Video file with its caption."""
    filename: str
    filepath: str
    caption: str
    line_number: int  # Line number in noidung.txt


class InstagramReelUploader:
    """
    Upload Instagram Reels from profile video folder.
    
    Structure:
    data/instagram/{profile_id}/
        ├── 00001.mp4
        ├── 00002.mp4
        └── noidung.txt (format: filename | caption)
    
    Uses Playwright CDP to connect to existing browser for anti-detection.
    """
    
    INSTAGRAM_URL = "https://www.instagram.com"
    DATA_DIR = "data/instagram"
    CDP_PORT_FILE = "data/cdp_ports.json"  # Store CDP ports for profiles
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.profile_id: Optional[str] = None
        self.log_callback: Optional[Callable[[str], None]] = None
    
    def set_log_callback(self, callback: Callable[[str], None]):
        """Set callback for logging messages."""
        self.log_callback = callback
    
    def log(self, message: str):
        """Log a message."""
        print(message)
        if self.log_callback:
            self.log_callback(message)
    
    async def start_with_cdp(self, cdp_url: str) -> bool:
        """Connect to existing browser via CDP."""
        if not PLAYWRIGHT_AVAILABLE:
            self.log("❌ Playwright not installed. Run: pip install playwright")
            return False
        
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
            
            # Get existing context or create new one
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
            else:
                self.context = await self.browser.new_context()
            
            # Get existing page or create new one
            pages = self.context.pages
            if pages:
                self.page = pages[0]
            else:
                self.page = await self.context.new_page()
            
            self.log(f"✅ Connected to browser via CDP: {cdp_url}")
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to connect via CDP: {e}")
            return False
    
    async def start_standalone(self, profile_path: str) -> bool:
        """Start standalone browser with profile (fallback if no CDP)."""
        if not PLAYWRIGHT_AVAILABLE:
            self.log("❌ Playwright not installed. Run: pip install playwright")
            return False
        
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with profile
            self.browser = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=profile_path,
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            
            # Get or create page
            pages = self.browser.pages
            if pages:
                self.page = pages[0]
            else:
                self.page = await self.browser.new_page()
            
            self.log(f"✅ Started browser with profile: {profile_path}")
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to start browser: {e}")
            return False
    
    async def stop(self):
        """Stop browser and cleanup."""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except:
            pass
        finally:
            self.browser = None
            self.context = None
            self.page = None
            self.playwright = None
    
    def get_video_folder(self, profile_id: str) -> str:
        """Get video folder path for profile."""
        return os.path.join(self.DATA_DIR, profile_id)
    
    def parse_content_file(self, folder_path: str) -> List[VideoContent]:
        """
        Parse noidung.txt file.
        
        Format: filename | caption
        Example: 00001.mp4 | This is my caption #hashtag
        """
        content_file = os.path.join(folder_path, "noidung.txt")
        videos = []
        
        if not os.path.exists(content_file):
            print(f"⚠️ Content file not found: {content_file}")
            return videos
        
        with open(content_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or '|' not in line:
                continue
            
            parts = line.split('|', 1)
            if len(parts) != 2:
                continue
            
            filename = parts[0].strip()
            caption = parts[1].strip()
            filepath = os.path.join(folder_path, filename)
            
            # Check if video file exists
            if os.path.exists(filepath):
                videos.append(VideoContent(
                    filename=filename,
                    filepath=filepath,
                    caption=caption,
                    line_number=i
                ))
        
        return videos
    
    def get_next_video(self, profile_id: str, random_order: bool = False) -> Optional[VideoContent]:
        """
        Get next video to upload.
        
        Args:
            profile_id: Profile ID (folder name)
            random_order: If True, pick random video; else pick first
        """
        folder = self.get_video_folder(profile_id)
        videos = self.parse_content_file(folder)
        
        if not videos:
            return None
        
        if random_order:
            return random.choice(videos)
        else:
            return videos[0]  # First video (sequential order)
    
    def remove_uploaded_video(self, video: VideoContent, folder_path: str) -> bool:
        """
        Remove video file and its line from noidung.txt after successful upload.
        """
        try:
            # Delete video file
            if os.path.exists(video.filepath):
                os.remove(video.filepath)
                print(f"🗑️ Deleted video: {video.filename}")
            
            # Remove line from noidung.txt
            content_file = os.path.join(folder_path, "noidung.txt")
            if os.path.exists(content_file):
                with open(content_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Remove the line containing this video
                new_lines = []
                for line in lines:
                    if not line.strip().startswith(video.filename):
                        new_lines.append(line)
                
                with open(content_file, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                
                print(f"📝 Removed from noidung.txt: {video.filename}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error removing video: {e}")
            return False
    
    async def is_logged_in(self) -> bool:
        """Check if logged into Instagram."""
        try:
            await self.page.goto(self.INSTAGRAM_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            
            # Check for logged-in indicators
            selectors = [
                'svg[aria-label="Home"]',
                'svg[aria-label="Trang chủ"]',  # Vietnamese
                'svg[aria-label="New post"]',
                'svg[aria-label="Bài viết mới"]',  # Vietnamese
                'a[href*="/direct/inbox"]'
            ]
            
            for sel in selectors:
                try:
                    if await self.page.locator(sel).count() > 0:
                        return True
                except:
                    continue
            
            return False
        except Exception as e:
            self.log(f"Login check error: {e}")
            return False
    
    async def upload_reel(self, video: VideoContent) -> bool:
        """
        Upload a single reel to Instagram.
        
        Args:
            video: VideoContent with file path and caption
        """
        abs_path = os.path.abspath(video.filepath)
        self.log(f"\n📤 Uploading: {video.filename}")
        self.log(f"📝 Caption: {video.caption[:50]}..." if len(video.caption) > 50 else f"📝 Caption: {video.caption}")
        
        try:
            # Go to Instagram
            await self.page.goto(self.INSTAGRAM_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            
            # Click Create/New post button (support multiple languages)
            create_selectors = [
                'svg[aria-label="New post"]',
                'svg[aria-label="Bài viết mới"]',  # Vietnamese
                'svg[aria-label="Nuevo post"]',  # Spanish
            ]
            
            clicked = False
            for sel in create_selectors:
                try:
                    create_btn = self.page.locator(sel).first
                    if await create_btn.count() > 0:
                        parent = create_btn.locator('xpath=ancestor::*[@role="button" or self::a or self::button or self::div[@tabindex]][1]')
                        await parent.click()
                        clicked = True
                        break
                except:
                    continue
            
            if not clicked:
                # Fallback JS click
                await self.page.evaluate('''
                    const selectors = ['svg[aria-label="New post"]', 'svg[aria-label="Bài viết mới"]'];
                    for (const sel of selectors) {
                        const btn = document.querySelector(sel);
                        if (btn) {
                            const parent = btn.closest('[role="button"], a, button, div[tabindex]');
                            if (parent) { parent.click(); break; }
                        }
                    }
                ''')
            
            await asyncio.sleep(2)
            
            # Select Reel option if shown
            try:
                reel_selectors = ['text=Reel', 'text=Thước phim']  # English, Vietnamese
                for sel in reel_selectors:
                    reel_btn = self.page.locator(sel).first
                    if await reel_btn.count() > 0:
                        await reel_btn.click()
                        await asyncio.sleep(1)
                        break
            except:
                pass
            
            # Upload video file
            file_input = self.page.locator('input[type="file"]').first
            await file_input.wait_for(timeout=10000)
            await file_input.set_input_files(abs_path)
            self.log("⏳ Video uploaded, processing...")
            
            # Wait for processing - look for Next button (multiple languages)
            next_selectors = [
                'div[role="button"]:has-text("Next")',
                'button:has-text("Next")',
                'div[role="button"]:has-text("Tiếp")',  # Vietnamese
                'button:has-text("Tiếp")',
            ]
            
            next_btn = None
            for sel in next_selectors:
                try:
                    btn = self.page.locator(sel).first
                    await btn.wait_for(timeout=120000)  # 2 minutes for processing
                    next_btn = btn
                    break
                except:
                    continue
            
            if not next_btn:
                self.log("❌ Could not find Next button")
                return False
            
            await asyncio.sleep(1)
            
            # Click Next (edit screen)
            await next_btn.click()
            await asyncio.sleep(2)
            
            # On edit screen - select Original aspect ratio
            try:
                crop_selectors = [
                    'svg[aria-label="Select crop"]',
                    'svg[aria-label="Chọn cắt"]',  # Vietnamese
                ]
                for sel in crop_selectors:
                    crop_btn = self.page.locator(sel).first
                    if await crop_btn.count() > 0:
                        await crop_btn.click()
                        await asyncio.sleep(1)
                        
                        # Select Original
                        original_selectors = ['text=Original', 'text=Gốc']
                        for orig_sel in original_selectors:
                            original_btn = self.page.locator(orig_sel).first
                            if await original_btn.count() > 0:
                                await original_btn.click()
                                await asyncio.sleep(0.5)
                                break
                        break
            except:
                pass
            
            # Click Next again (to caption screen)
            for sel in next_selectors:
                try:
                    next_btn2 = self.page.locator(sel).first
                    if await next_btn2.count() > 0:
                        await next_btn2.click()
                        break
                except:
                    continue
            await asyncio.sleep(2)
            
            # Enter caption
            if video.caption:
                try:
                    caption_selectors = [
                        'div[aria-label="Write a caption..."]',
                        'div[aria-label="Viết chú thích..."]',  # Vietnamese
                        'textarea[aria-label="Write a caption..."]',
                        'div[data-lexical-editor="true"]',
                        'div[contenteditable="true"]'
                    ]
                    
                    for sel in caption_selectors:
                        caption_input = self.page.locator(sel).first
                        if await caption_input.count() > 0:
                            await caption_input.click()
                            await asyncio.sleep(0.3)
                            # Type caption
                            await self.page.keyboard.type(video.caption, delay=10)
                            await asyncio.sleep(1)
                            break
                except Exception as e:
                    self.log(f"⚠️ Caption error: {e}")
            
            # Click Share
            share_selectors = [
                'div[role="button"]:has-text("Share")',
                'button:has-text("Share")',
                'div[role="button"]:has-text("Chia sẻ")',  # Vietnamese
                'button:has-text("Chia sẻ")',
            ]
            
            for sel in share_selectors:
                try:
                    share_btn = self.page.locator(sel).first
                    if await share_btn.count() > 0:
                        await share_btn.click()
                        break
                except:
                    continue
            
            self.log("⏳ Posting reel...")
            
            # Wait for upload completion
            await asyncio.sleep(20)
            
            # Check for success indicators
            success_texts = ["Reel shared", "Your reel has been shared", "shared", "Đã chia sẻ"]
            for text in success_texts:
                try:
                    if await self.page.locator(f'text="{text}"').count() > 0:
                        self.log("✅ Reel posted successfully!")
                        return True
                except:
                    continue
            
            # Check if returned to feed (also indicates success)
            await asyncio.sleep(3)
            home_selectors = ['svg[aria-label="Home"]', 'svg[aria-label="Trang chủ"]']
            for sel in home_selectors:
                try:
                    if await self.page.locator(sel).count() > 0:
                        self.log("✅ Reel likely posted successfully!")
                        return True
                except:
                    continue
            
            self.log("⚠️ Could not confirm upload")
            return False
            
        except Exception as e:
            self.log(f"❌ Upload error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def run(
        self,
        profile_id: str,
        profile_path: str,
        max_uploads: int = 1,
        random_order: bool = False,
        delay_between: Tuple[int, int] = (60, 180),
        cdp_url: str = None,
        progress_callback: Callable[[int, int], None] = None
    ) -> dict:
        """
        Run the reel upload process.
        
        Args:
            profile_id: Profile ID (matches folder in data/instagram/)
            profile_path: Browser profile path
            max_uploads: Maximum number of videos to upload
            random_order: Pick videos randomly or sequentially
            delay_between: (min, max) seconds delay between uploads
            cdp_url: CDP WebSocket URL to connect to existing browser
            progress_callback: Callback for progress updates (current, total)
            
        Returns:
            Results dict with success/fail counts
        """
        results = {
            "profile_id": profile_id,
            "total": 0,
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        self.profile_id = profile_id
        video_folder = self.get_video_folder(profile_id)
        
        # Check video folder exists
        if not os.path.exists(video_folder):
            self.log(f"❌ Video folder not found: {video_folder}")
            return results
        
        # Start browser
        self.log(f"\n{'='*50}")
        self.log(f"🚀 Starting Instagram Reel Uploader")
        self.log(f"📁 Profile: {profile_id}")
        self.log(f"📂 Video folder: {video_folder}")
        self.log(f"{'='*50}")
        
        # Connect to browser
        connected = False
        if cdp_url:
            connected = await self.start_with_cdp(cdp_url)
        
        if not connected:
            # Fallback to standalone browser
            connected = await self.start_standalone(profile_path)
        
        if not connected:
            self.log("❌ Failed to start browser")
            return results
        
        try:
            # Check login
            self.log("\n🔐 Checking Instagram login...")
            if not await self.is_logged_in():
                self.log("❌ Not logged in to Instagram!")
                self.log("Please login manually first.")
                return results
            
            self.log("✅ Logged in to Instagram")
            
            # Count available videos for progress
            available_videos = self.parse_content_file(video_folder)
            total_to_upload = min(max_uploads, len(available_videos))
            
            # Upload videos
            uploaded = 0
            while uploaded < max_uploads:
                # Get next video
                video = self.get_next_video(profile_id, random_order)
                
                if not video:
                    self.log("\n📭 No more videos to upload")
                    break
                
                results["total"] += 1
                
                # Upload
                success = await self.upload_reel(video)
                
                if success:
                    results["success"] += 1
                    results["details"].append({
                        "video": video.filename,
                        "status": "success"
                    })
                    
                    # Remove uploaded video and content line
                    self.remove_uploaded_video(video, video_folder)
                    uploaded += 1
                    
                    # Progress callback
                    if progress_callback:
                        progress_callback(uploaded, total_to_upload)
                else:
                    results["failed"] += 1
                    results["details"].append({
                        "video": video.filename,
                        "status": "failed"
                    })
                    # Don't remove failed videos - can retry later
                    break  # Stop on failure to avoid spam
                
                # Delay before next upload
                if uploaded < max_uploads:
                    remaining = self.get_next_video(profile_id, random_order)
                    if remaining:
                        delay = random.randint(*delay_between)
                        self.log(f"\n⏰ Waiting {delay}s before next upload...")
                        await asyncio.sleep(delay)
            
            # Summary
            self.log(f"\n{'='*50}")
            self.log(f"📊 Upload Summary")
            self.log(f"   Total: {results['total']}")
            self.log(f"   Success: {results['success']}")
            self.log(f"   Failed: {results['failed']}")
            self.log(f"{'='*50}")
            
        finally:
            await self.stop()
        
        return results


# ==================== INTEGRATION WITH APP ====================

async def run_instagram_upload_for_profile(
    profile_id: str,
    profile_path: str,
    max_uploads: int = 1,
    random_order: bool = False,
    delay_min: int = 60,
    delay_max: int = 180,
    cdp_url: str = None,
    log_callback: Callable[[str], None] = None,
    progress_callback: Callable[[int, int], None] = None
) -> dict:
    """
    Convenience function to run Instagram upload for a profile.
    Called from the main app.
    
    Args:
        profile_id: Profile ID (folder name in data/instagram/)
        profile_path: Browser profile path
        max_uploads: Max videos to upload
        random_order: Pick videos randomly or sequentially
        delay_min: Min delay between uploads (seconds)
        delay_max: Max delay between uploads (seconds)
        cdp_url: CDP WebSocket URL to connect to existing browser
        log_callback: Callback for log messages
        progress_callback: Callback for progress updates
    """
    uploader = InstagramReelUploader()
    
    if log_callback:
        uploader.set_log_callback(log_callback)
    
    return await uploader.run(
        profile_id=profile_id,
        profile_path=profile_path,
        max_uploads=max_uploads,
        random_order=random_order,
        delay_between=(delay_min, delay_max),
        cdp_url=cdp_url,
        progress_callback=progress_callback
    )


def run_instagram_upload_sync(
    profile_id: str,
    profile_path: str,
    max_uploads: int = 1,
    random_order: bool = False,
    delay_min: int = 60,
    delay_max: int = 180,
    cdp_url: str = None,
    log_callback: Callable[[str], None] = None,
    progress_callback: Callable[[int, int], None] = None
) -> dict:
    """
    Synchronous wrapper for Instagram upload.
    Use this from non-async code (like PyQt).
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(
            run_instagram_upload_for_profile(
                profile_id=profile_id,
                profile_path=profile_path,
                max_uploads=max_uploads,
                random_order=random_order,
                delay_min=delay_min,
                delay_max=delay_max,
                cdp_url=cdp_url,
                log_callback=log_callback,
                progress_callback=progress_callback
            )
        )
    finally:
        loop.close()


# ==================== CLI ====================

if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) < 3:
            print("Usage: python instagram_reel_uploader.py <profile_id> <profile_path> [max_uploads]")
            print("\nExample:")
            print("  python instagram_reel_uploader.py 27881089984286345394 profile/abc123 3")
            return
        
        profile_id = sys.argv[1]
        profile_path = sys.argv[2]
        max_uploads = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        
        results = await run_instagram_upload_for_profile(
            profile_id=profile_id,
            profile_path=profile_path,
            max_uploads=max_uploads
        )
        
        print(f"\nFinal Results: {results}")
    
    asyncio.run(main())
