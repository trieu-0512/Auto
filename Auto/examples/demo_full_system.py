# Full System Demo for Multi-Profile Fingerprint Automation
# This script demonstrates all core functionality

import sys
import time

from app.data.profile_repository import ProfileRepository
from app.data.profile_models import ProfileData, GologinConfig
from app.core.fingerprint_generator import FingerprintGenerator
from app.core.profile_manager import ProfileManager
from app.core.browser_manager import BrowserManager
from app.core.proxy_manager import ProxyManager, ProxyInfo
from app.core.session_manager import SessionManager


def demo_profile_loading():
    """Demo: Load profiles from database."""
    print("\n" + "=" * 60)
    print("DEMO 1: Profile Loading from Database")
    print("=" * 60)
    
    repo = ProfileRepository(db_path="data/data.db", profile_dir="profile")
    manager = ProfileManager(repository=repo)
    
    profiles = manager.load_all_profiles()
    print(f"Loaded {len(profiles)} profiles from database")
    
    # Show first 5
    print("\nFirst 5 profiles:")
    for p in profiles[:5]:
        print(f"  - {p.profile_id}: {p.name} (exists: {p.exists})")
    
    return manager


def demo_fingerprint_generation():
    """Demo: Generate random fingerprint."""
    print("\n" + "=" * 60)
    print("DEMO 2: Fingerprint Generation")
    print("=" * 60)
    
    generator = FingerprintGenerator()
    
    # Generate 3 fingerprints
    for i in range(3):
        fp = generator.generate_fingerprint()
        print(f"\nFingerprint {i+1}:")
        print(f"  Audio Noise: {fp.audioContext.noiseValue:.2e}")
        print(f"  Canvas Noise: {fp.canvas.noise:.2f}")
        print(f"  WebGL Noise: {fp.webGL.noise:.2f}")
        print(f"  GPU: {fp.webGLMetadata.vendor}")
    
    return generator


def demo_proxy_validation():
    """Demo: Proxy validation and parsing."""
    print("\n" + "=" * 60)
    print("DEMO 3: Proxy Validation")
    print("=" * 60)
    
    proxy_manager = ProxyManager()
    
    test_proxies = [
        "192.168.1.1:8080",
        "proxy.example.com:3128",
        "10.0.0.1:8080:user:pass123",
        "invalid",
        "192.168.1.1:abc",
        "192.168.1.1:70000"
    ]
    
    for proxy_str in test_proxies:
        is_valid, error = proxy_manager.validate_proxy_format(proxy_str)
        status = "✓ Valid" if is_valid else f"✗ Invalid: {error}"
        print(f"  {proxy_str:<35} {status}")
    
    return proxy_manager


def demo_read_profile_fingerprint(manager: ProfileManager):
    """Demo: Read fingerprint from existing profile."""
    print("\n" + "=" * 60)
    print("DEMO 4: Read Profile Fingerprint")
    print("=" * 60)
    
    profiles = manager.load_all_profiles()
    existing = [p for p in profiles if p.exists]
    
    if existing:
        profile = existing[0]
        print(f"Reading fingerprint for: {profile.profile_id}")
        
        fp = manager.get_profile_fingerprint(profile.profile_id)
        if fp:
            print(f"  Name: {fp.name}")
            print(f"  User Agent: {fp.userAgent[:60]}...")
            print(f"  Screen: {fp.screenWidth}x{fp.screenHeight}")
            print(f"  Hardware Concurrency: {fp.hardwareConcurrency}")
            print(f"  Device Memory: {fp.deviceMemory} GB")
            print(f"  Timezone: {fp.timezone.id}")
        else:
            print("  Could not read fingerprint")
    else:
        print("  No existing profiles found")


def demo_browser_options():
    """Demo: Build browser options."""
    print("\n" + "=" * 60)
    print("DEMO 5: Browser Options Configuration")
    print("=" * 60)
    
    repo = ProfileRepository(db_path="data/data.db", profile_dir="profile")
    profile_manager = ProfileManager(repository=repo)
    browser_manager = BrowserManager(profile_manager=profile_manager)
    
    profiles = profile_manager.load_all_profiles()
    existing = [p for p in profiles if p.exists]
    
    if existing:
        profile = existing[0]
        print(f"Building options for: {profile.profile_id}")
        
        options = browser_manager.build_chrome_options(
            profile,
            window_position=(100, 100),
            extensions=["CapSolver"]
        )
        
        print(f"  Binary: {options.binary_location}")
        print(f"  Arguments:")
        for arg in options.arguments[:5]:
            print(f"    - {arg}")
    else:
        print("  No existing profiles found")


def demo_window_positions():
    """Demo: Window position calculation."""
    print("\n" + "=" * 60)
    print("DEMO 6: Window Position Calculation")
    print("=" * 60)
    
    browser_manager = BrowserManager()
    
    print("Window positions for 6 profiles:")
    for i in range(6):
        pos = browser_manager.calculate_window_position(i)
        print(f"  Profile {i+1}: position {pos}")


def main():
    print("=" * 60)
    print("Multi-Profile Fingerprint Automation - Full System Demo")
    print("=" * 60)
    
    # Run demos
    manager = demo_profile_loading()
    demo_fingerprint_generation()
    demo_proxy_validation()
    demo_read_profile_fingerprint(manager)
    demo_browser_options()
    demo_window_positions()
    
    print("\n" + "=" * 60)
    print("All demos completed successfully!")
    print("=" * 60)
    
    print("\nTo launch a browser profile, run:")
    print("  python demo_launch_profile.py")


if __name__ == "__main__":
    main()
