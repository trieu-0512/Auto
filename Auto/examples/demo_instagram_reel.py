# Demo: Post Instagram Reel using Playwright CDP
# No Selenium, no WebDriver detection

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.instagram_automation import InstagramAutomation, ReelConfig


async def demo_post_reel():
    """
    Demo posting a reel to Instagram using Playwright CDP.
    
    Prerequisites:
    1. pip install playwright
    2. Have a profile with Instagram already logged in
    3. Have a video file ready
    """
    
    # Configuration - EDIT THESE
    PROFILE_PATH = "profile/your_profile_id"  # Path to your browser profile
    VIDEO_PATH = "data/instagram/your_video.mp4"  # Path to video file
    CAPTION = "Check out this awesome reel! 🔥"
    HASHTAGS = ["reels", "viral", "trending", "fyp"]
    
    # Check paths
    if not os.path.exists(PROFILE_PATH):
        print(f"Profile not found: {PROFILE_PATH}")
        print("\nAvailable profiles:")
        if os.path.exists("profile"):
            for p in os.listdir("profile"):
                print(f"  - profile/{p}")
        return
    
    if not os.path.exists(VIDEO_PATH):
        print(f"Video not found: {VIDEO_PATH}")
        print("\nLooking for videos in data/instagram/...")
        if os.path.exists("data/instagram"):
            for root, dirs, files in os.walk("data/instagram"):
                for f in files:
                    if f.endswith(('.mp4', '.mov', '.webm')):
                        print(f"  - {os.path.join(root, f)}")
        return
    
    automation = InstagramAutomation()
    
    try:
        print("=" * 50)
        print("Instagram Reel Poster (Playwright CDP)")
        print("=" * 50)
        
        # Start browser
        print("\n[1] Starting browser with Playwright CDP...")
        profile_id = os.path.basename(PROFILE_PATH)
        
        if not await automation.start(profile_id, PROFILE_PATH):
            print("Failed to start browser")
            print("Make sure Playwright is installed: pip install playwright")
            return
        
        print("✓ Browser started")
        
        # Check login
        print("\n[2] Checking Instagram login...")
        if not await automation.is_logged_in():
            print("Not logged in!")
            print("Please login manually first, then run again.")
            input("Press Enter to close...")
            return
        
        print("✓ Logged in")
        
        # Post reel
        print("\n[3] Posting reel...")
        config = ReelConfig(
            video_path=VIDEO_PATH,
            caption=CAPTION,
            hashtags=HASHTAGS,
            share_to_feed=True
        )
        
        success = await automation.post_reel(config)
        
        print("\n" + "=" * 50)
        if success:
            print("✅ REEL POSTED SUCCESSFULLY!")
        else:
            print("❌ Failed to post reel")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\nCancelled")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n[4] Closing...")
        await automation.stop()
        print("Done!")


async def demo_post_multiple_reels():
    """
    Demo posting multiple reels from a folder.
    """
    
    # Configuration - EDIT THESE
    PROFILE_PATH = "profile/your_profile_id"
    VIDEO_FOLDER = "data/instagram/videos"
    CAPTION_TEMPLATE = "New reel! 🎬"
    HASHTAGS = ["reels", "viral", "trending"]
    DELAY_BETWEEN = (120, 300)  # 2-5 minutes between posts
    
    # Find all videos
    videos = []
    if os.path.exists(VIDEO_FOLDER):
        for f in os.listdir(VIDEO_FOLDER):
            if f.endswith(('.mp4', '.mov', '.webm')):
                videos.append(os.path.join(VIDEO_FOLDER, f))
    
    if not videos:
        print(f"No videos found in {VIDEO_FOLDER}")
        return
    
    print(f"Found {len(videos)} videos to post")
    
    # Create configs
    configs = [
        ReelConfig(
            video_path=v,
            caption=CAPTION_TEMPLATE,
            hashtags=HASHTAGS
        )
        for v in videos
    ]
    
    # Create automation
    automation = InstagramAutomation()
    
    try:
        # Start browser
        profile_id = os.path.basename(PROFILE_PATH)
        if not await automation.start(profile_id, PROFILE_PATH):
            print("Failed to start browser")
            return
        
        # Check login
        if not await automation.is_logged_in():
            print("Not logged in!")
            return
        
        # Post all reels
        results = await automation.post_multiple_reels(configs, DELAY_BETWEEN)
        
        print("\n" + "=" * 50)
        print("RESULTS:")
        print(f"  Total: {results['total']}")
        print(f"  Success: {results['success']}")
        print(f"  Failed: {results['failed']}")
        print("=" * 50)
        
    finally:
        await automation.stop()


if __name__ == "__main__":
    print("Instagram Reel Automation Demo")
    print("-" * 30)
    print("1. Post single reel")
    print("2. Post multiple reels")
    print("-" * 30)
    
    choice = input("Choose option (1/2): ").strip()
    
    if choice == "1":
        asyncio.run(demo_post_reel())
    elif choice == "2":
        asyncio.run(demo_post_multiple_reels())
    else:
        print("Invalid choice")
