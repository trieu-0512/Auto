# Demo script for launching a profile with Selenium
# Run this to test browser automation

import sys
import time

from app.data.profile_repository import ProfileRepository
from app.core.profile_manager import ProfileManager
from app.core.browser_manager import BrowserManager
from app.core.fingerprint_generator import FingerprintGenerator


def main():
    print("=" * 60)
    print("Multi-Profile Browser Launch - Demo")
    print("=" * 60)
    
    # Initialize components
    repo = ProfileRepository(db_path="data/data.db", profile_dir="profile")
    generator = FingerprintGenerator()
    profile_manager = ProfileManager(repository=repo, generator=generator)
    browser_manager = BrowserManager(
        profile_manager=profile_manager,
        orbita_path="trinhduyet/orbita-browser/chrome.exe",
        extensions_dir="extensions"
    )
    
    # Load profiles
    profiles = profile_manager.load_all_profiles()
    existing_profiles = [p for p in profiles if p.exists]
    
    if not existing_profiles:
        print("No existing profiles found!")
        return
    
    print(f"\nFound {len(existing_profiles)} existing profiles")
    print("\nAvailable profiles:")
    for i, p in enumerate(existing_profiles[:10]):
        print(f"  {i+1}. {p.profile_id} - {p.name}")
    
    # Ask user which profile to launch
    print("\nEnter profile number to launch (1-10), or 'q' to quit:")
    choice = input("> ").strip()
    
    if choice.lower() == 'q':
        print("Exiting...")
        return
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(existing_profiles[:10]):
            profile = existing_profiles[idx]
        else:
            print("Invalid choice!")
            return
    except ValueError:
        print("Invalid input!")
        return
    
    print(f"\nLaunching profile: {profile.profile_id}")
    print(f"Name: {profile.name}")
    print(f"Path: {profile.path}")
    
    # Calculate window position
    position = browser_manager.calculate_window_position(0)
    print(f"Window position: {position}")
    
    # Launch browser
    print("\nStarting browser...")
    driver = browser_manager.launch_profile(
        profile.profile_id,
        window_position=position,
        extensions=["CapSolver"]  # Load CapSolver extension
    )
    
    if driver:
        print("Browser launched successfully!")
        print(f"Active sessions: {browser_manager.get_session_count()}")
        
        # Navigate to a test page
        print("\nNavigating to https://browserleaks.com/canvas...")
        driver.get("https://browserleaks.com/canvas")
        
        print("\nBrowser is running. Press Enter to close...")
        input()
        
        # Close session
        print("Closing browser...")
        browser_manager.close_session(profile.profile_id)
        print("Browser closed.")
    else:
        print("Failed to launch browser!")
    
    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
