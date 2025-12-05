# Instagram Automation via Playwright CDP
# Auto post Reels to Instagram - No Selenium, No WebDriver detection

import asyncio
import os
import random
from typing import Optional, List
from dataclasses import dataclass

from app.core.playwright_cdp import PlaywrightCDP

try:
    from playwright.async_api import Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


@dataclass
class ReelConfig:
    """Configuration for posting a Reel."""
    video_path: str
    caption: str = ""
    cover_time: float = 0
    share_to_feed: bool = True
    hashtags: List[str] = None
    
    @property
    def full_caption(self) -> str:
        """Get caption with hashtags."""
        text = self.caption
        if self.hashtags:
            tags = " ".join(f"#{tag}" for tag in self.hashtags)
            text = f"{text}\n\n{tags}" if text else tags
        return text


class InstagramAutomation:
    """
    Instagram automation using Playwright CDP.
    No Selenium, no WebDriver detection.
    """
    
    INSTAGRAM_URL = "https://www.instagram.com"
    
    def __init__(self):
        self.cdp = PlaywrightCDP()
        self.page: Optional[Page] = None
        self.profile_id: Optional[str] = None
    
    async def start(self, profile_id: str, profile_path: str, debug_port: int = None) -> bool:
        """Start browser and connect via Playwright CDP."""
        if not PLAYWRIGHT_AVAILABLE:
            print("Playwright not installed. Run: pip install playwright")
            return False
        
        self.profile_id = profile_id
        self.page = await self.cdp.launch(
            profile_id=profile_id,
            profile_path=profile_path,
            debug_port=debug_port
        )
        
        return self.page is not None
    
    async def stop(self):
        """Stop browser."""
        if self.profile_id:
            await self.cdp.close(self.profile_id)
            self.page = None
            self.profile_id = None
    
    async def is_logged_in(self) -> bool:
        """Check if logged into Instagram."""
        await self.page.goto(self.INSTAGRAM_URL, wait_until="networkidle")
        await asyncio.sleep(2)
        
        # Check for login indicators
        selectors = [
            'svg[aria-label="Home"]',
            'a[href="/accounts/edit/"]',
            'svg[aria-label="New post"]'
        ]
        
        for sel in selectors:
            try:
                if await self.page.locator(sel).count() > 0:
                    return True
            except:
                pass
        
        return False
    
    async def login(self, username: str, password: str) -> bool:
        """Login to Instagram."""
        await self.page.goto(f"{self.INSTAGRAM_URL}/accounts/login/", wait_until="networkidle")
        await asyncio.sleep(2)
        
        # Accept cookies
        try:
            allow_btn = self.page.locator('button:has-text("Allow")')
            if await allow_btn.count() > 0:
                await allow_btn.click()
                await asyncio.sleep(1)
        except:
            pass
        
        # Enter credentials
        await self.page.fill('input[name="username"]', username)
        await asyncio.sleep(0.3)
        await self.page.fill('input[name="password"]', password)
        await asyncio.sleep(0.3)
        
        # Click login
        await self.page.click('button[type="submit"]')
        await asyncio.sleep(5)
        
        # Check for 2FA
        if await self.page.locator('input[name="verificationCode"]').count() > 0:
            print("2FA required - complete manually")
            await asyncio.sleep(30)
        
        return await self.is_logged_in()
    
    async def post_reel(self, config: ReelConfig) -> bool:
        """Post a Reel to Instagram."""
        if not os.path.exists(config.video_path):
            print(f"Video not found: {config.video_path}")
            return False
        
        abs_video_path = os.path.abspath(config.video_path)
        print(f"Posting reel: {abs_video_path}")
        
        # Go to Instagram
        await self.page.goto(self.INSTAGRAM_URL, wait_until="networkidle")
        await asyncio.sleep(2)
        
        # Click Create button
        create_clicked = False
        create_selectors = [
            'svg[aria-label="New post"]',
            '[aria-label="New post"]',
            'a[href="/create/select/"]'
        ]
        
        for sel in create_selectors:
            try:
                loc = self.page.locator(sel).first
                if await loc.count() > 0:
                    # Click parent element
                    await loc.locator('xpath=ancestor::*[@role="button" or self::a or self::button]').first.click()
                    create_clicked = True
                    break
            except:
                pass
        
        if not create_clicked:
            # Try JS click
            await self.page.evaluate('''
                const btn = document.querySelector('svg[aria-label="New post"]');
                if (btn) btn.closest('[role="button"], a, button').click();
            ''')
        
        await asyncio.sleep(2)
        
        # Select Reel if option shown
        try:
            reel_opt = self.page.locator('text=Reel').first
            if await reel_opt.count() > 0:
                await reel_opt.click()
                await asyncio.sleep(1)
        except:
            pass
        
        # Upload file
        try:
            # Wait for file input
            file_input = self.page.locator('input[type="file"]').first
            await file_input.wait_for(timeout=10000)
            await file_input.set_input_files(abs_video_path)
            print("Video uploaded, processing...")
        except Exception as e:
            print(f"Upload failed: {e}")
            return False
        
        # Wait for Next button
        try:
            next_btn = self.page.locator('button:has-text("Next"), div[role="button"]:has-text("Next")').first
            await next_btn.wait_for(timeout=60000)
            await next_btn.click()
            await asyncio.sleep(2)
        except:
            print("Next button not found")
            return False
        
        # Click Next again (to caption)
        try:
            await self.page.locator('button:has-text("Next"), div[role="button"]:has-text("Next")').first.click()
            await asyncio.sleep(2)
        except:
            pass
        
        # Enter caption
        if config.full_caption:
            try:
                caption_sel = 'textarea[aria-label="Write a caption..."], div[aria-label="Write a caption..."]'
                caption_input = self.page.locator(caption_sel).first
                await caption_input.click()
                await asyncio.sleep(0.3)
                await self.page.keyboard.type(config.full_caption, delay=20)
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Caption error: {e}")
        
        # Click Share
        try:
            share_btn = self.page.locator('button:has-text("Share"), div[role="button"]:has-text("Share")').first
            await share_btn.click()
            print("Posting...")
        except:
            print("Share button not found")
            return False
        
        # Wait for completion
        await asyncio.sleep(10)
        
        # Check success
        success_texts = ["Reel shared", "Your reel has been shared"]
        for text in success_texts:
            if await self.page.locator(f'text="{text}"').count() > 0:
                print("✅ Reel posted successfully!")
                return True
        
        # Check if back on feed
        await asyncio.sleep(3)
        if await self.page.locator('svg[aria-label="Home"]').count() > 0:
            print("✅ Reel likely posted")
            return True
        
        print("⚠️ Could not confirm post")
        return False
    
    async def post_multiple_reels(
        self,
        configs: List[ReelConfig],
        delay_between: tuple = (60, 120)
    ) -> dict:
        """Post multiple reels with delays."""
        results = {"total": len(configs), "success": 0, "failed": 0, "details": []}
        
        for i, config in enumerate(configs):
            print(f"\n--- Reel {i+1}/{len(configs)} ---")
            
            try:
                if await self.post_reel(config):
                    results["success"] += 1
                    results["details"].append({"video": config.video_path, "status": "success"})
                else:
                    results["failed"] += 1
                    results["details"].append({"video": config.video_path, "status": "failed"})
            except Exception as e:
                print(f"Error: {e}")
                results["failed"] += 1
                results["details"].append({"video": config.video_path, "status": "error", "error": str(e)})
            
            if i < len(configs) - 1:
                delay = random.randint(*delay_between)
                print(f"Waiting {delay}s...")
                await asyncio.sleep(delay)
        
        return results


# ==================== CONVENIENCE FUNCTIONS ====================

async def post_instagram_reel(
    profile_path: str,
    video_path: str,
    caption: str = "",
    hashtags: List[str] = None,
    profile_id: str = "default"
) -> bool:
    """
    Post a single reel to Instagram.
    
    Args:
        profile_path: Path to browser profile
        video_path: Path to video file
        caption: Post caption
        hashtags: List of hashtags (without #)
        profile_id: Profile identifier
    """
    automation = InstagramAutomation()
    
    try:
        if not await automation.start(profile_id, profile_path):
            print("Failed to start browser")
            return False
        
        if not await automation.is_logged_in():
            print("Not logged in to Instagram")
            return False
        
        config = ReelConfig(
            video_path=video_path,
            caption=caption,
            hashtags=hashtags or []
        )
        
        return await automation.post_reel(config)
        
    finally:
        await automation.stop()


# ==================== CLI ====================

if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) < 3:
            print("Usage: python instagram_automation.py <profile_path> <video_path> [caption]")
            print("\nExample:")
            print("  python instagram_automation.py profile/abc123 video.mp4 'My caption'")
            return
        
        profile_path = sys.argv[1]
        video_path = sys.argv[2]
        caption = sys.argv[3] if len(sys.argv) > 3 else ""
        
        success = await post_instagram_reel(
            profile_path=profile_path,
            video_path=video_path,
            caption=caption
        )
        
        print(f"\nResult: {'✅ Success' if success else '❌ Failed'}")
    
    asyncio.run(main())
