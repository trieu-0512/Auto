# Demo Database Sync Functionality
# Shows how the app automatically imports profiles from main database
# 
# Architecture:
# - data/data.db: Original database (READ-ONLY) - profiles from external app
# - data/app_data.db: App database (READ-WRITE) - stores all app data
# - Auto-sync: When app starts, new profiles from data.db are imported to app_data.db

import os
import sqlite3
from app.data.profile_repository import ProfileRepository
from app.data.profile_models import ProfileData


def show_database_info():
    """Show information about both databases."""
    print("\n" + "=" * 60)
    print("DATABASE INFORMATION")
    print("=" * 60)
    
    # Main database
    main_db = "data/data.db"
    if os.path.exists(main_db):
        conn = sqlite3.connect(main_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM danhsachacc")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"Main DB (data/data.db): {count} profiles [READ-ONLY]")
    else:
        print("Main DB (data/data.db): NOT FOUND")
    
    # App database
    app_db = "data/app_data.db"
    if os.path.exists(app_db):
        conn = sqlite3.connect(app_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM app_profiles")
        app_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM profile_status")
        status_count = cursor.fetchone()[0]
        conn.close()
        print(f"App DB (data/app_data.db): {app_count} profiles, {status_count} status records [READ-WRITE]")
    else:
        print("App DB (data/app_data.db): NOT FOUND (will be created)")


def demo_sync():
    """Demonstrate the sync functionality."""
    print("\n" + "=" * 60)
    print("DATABASE SYNC DEMO")
    print("=" * 60)
    
    # Show initial state
    show_database_info()
    
    # Initialize repository (this will auto-sync from main db)
    print("\n1. Initializing ProfileRepository...")
    print("   - Reading from data/data.db (READ-ONLY)")
    print("   - Writing to data/app_data.db (READ-WRITE)")
    
    repo = ProfileRepository(
        db_path="data/data.db",
        app_db_path="data/app_data.db",
        profile_dir="profile"
    )
    
    # List all profiles
    print("\n2. All Profiles (synced from main db + app created):")
    profiles = repo.get_all_profiles()
    for i, profile in enumerate(profiles[:10]):  # Show first 10
        print(f"   [{i+1}] {profile.idprofile[:20]}... - {profile.name} - {profile.status}")
    if len(profiles) > 10:
        print(f"   ... and {len(profiles) - 10} more profiles")
    
    print(f"\n   Total: {len(profiles)} profiles")
    
    # Test status update (writes to app_data.db only)
    if profiles:
        test_profile = profiles[0]
        print(f"\n3. Testing status update (writes to app_data.db only):")
        print(f"   Profile: {test_profile.idprofile[:20]}...")
        print(f"   Current status: {test_profile.status}")
        
        # Update status
        repo.update_profile_status(test_profile.idprofile, "running")
        
        # Verify
        updated = repo.get_profile_by_id(test_profile.idprofile)
        print(f"   Updated status: {updated.status}")
        
        # Reset status
        repo.update_profile_status(test_profile.idprofile, test_profile.status)
    
    # Test resync
    print("\n4. Testing resync (import new profiles from main db):")
    new_count = repo.resync_from_main_db()
    print(f"   New profiles imported: {new_count}")
    
    # Show final state
    show_database_info()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("✓ Main database (data/data.db) is READ-ONLY")
    print("✓ App database (data/app_data.db) stores all app data")
    print("✓ New profiles from main db are auto-imported on startup")
    print("✓ Status updates only affect app database")
    print("✓ Use resync_from_main_db() to manually import new profiles")


if __name__ == "__main__":
    demo_sync()
