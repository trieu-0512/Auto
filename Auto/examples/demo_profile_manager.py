# Demo script for Profile Manager
# Run this to test loading profiles from the real database

from app.data.profile_repository import ProfileRepository
from app.core.profile_manager import ProfileManager
from app.core.fingerprint_generator import FingerprintGenerator


def main():
    print("=" * 60)
    print("Multi-Profile Fingerprint Automation - Demo")
    print("=" * 60)
    
    # Initialize components
    repo = ProfileRepository(db_path="data/data.db", profile_dir="profile")
    generator = FingerprintGenerator()
    manager = ProfileManager(repository=repo, generator=generator)
    
    # Load all profiles
    print("\n1. Loading profiles from database...")
    profiles = manager.load_all_profiles()
    print(f"   Found {len(profiles)} profiles")
    
    # Display first 10 profiles
    print("\n2. First 10 profiles:")
    print("-" * 80)
    print(f"{'ID':<25} {'Name':<20} {'Status':<10} {'Exists':<8}")
    print("-" * 80)
    
    for profile in profiles[:10]:
        print(f"{profile.profile_id:<25} {profile.name[:18]:<20} {profile.status:<10} {str(profile.exists):<8}")
    
    # Get fingerprint for first existing profile
    print("\n3. Loading fingerprint for first existing profile...")
    for profile in profiles:
        if profile.exists:
            fingerprint = manager.get_profile_fingerprint(profile.profile_id)
            if fingerprint:
                print(f"   Profile: {profile.profile_id}")
                print(f"   Audio Noise: {fingerprint.audioContext.noiseValue}")
                print(f"   Canvas Noise: {fingerprint.canvas.noise}")
                print(f"   WebGL Noise: {fingerprint.webGL.noise}")
                print(f"   GPU Vendor: {fingerprint.webGLMetadata.vendor}")
                print(f"   GPU Renderer: {fingerprint.webGLMetadata.renderer[:50]}...")
                break
    
    # Count profiles by status
    print("\n4. Profile statistics:")
    total = manager.count_profiles()
    existing = sum(1 for p in profiles if p.exists)
    missing = sum(1 for p in profiles if not p.exists)
    print(f"   Total: {total}")
    print(f"   Existing: {existing}")
    print(f"   Missing: {missing}")
    
    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
