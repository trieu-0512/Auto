# Property-based tests for Backup Manager
# Feature: multi-profile-fingerprint-automation

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
import tempfile
import os
import shutil
import sqlite3
import json

from app.core.backup_manager import BackupManager, BackupInfo
from app.data.profile_repository import ProfileRepository
from app.data.profile_models import ProfileData


@pytest.fixture
def temp_setup():
    """Create temporary databases, profile directory, and backup directory."""
    # Create temp directory for all test files
    temp_dir = tempfile.mkdtemp()
    
    # Create main database (read-only source)
    main_db_path = os.path.join(temp_dir, "data.db")
    conn = sqlite3.connect(main_db_path)
    conn.execute("""
        CREATE TABLE danhsachacc (
            id INTEGER PRIMARY KEY,
            name TEXT,
            idprofile TEXT,
            proxymode TEXT,
            proxy TEXT,
            status TEXT,
            username_fb TEXT,
            password_fb TEXT,
            ma2fa TEXT,
            list_uid TEXT,
            list_group TEXT,
            control_fb TEXT,
            username_gmail TEXT,
            password_gmail TEXT,
            gmail_khoiphuc TEXT,
            sothutu INTEGER,
            notes TEXT,
            cookies TEXT,
            group_profile TEXT,
            last_run TEXT
        )
    """)
    conn.commit()
    conn.close()
    
    # App database path (will be created by ProfileRepository)
    app_db_path = os.path.join(temp_dir, "app_data.db")
    
    # Create temp directories
    profile_dir = os.path.join(temp_dir, "profiles")
    backup_dir = os.path.join(temp_dir, "backups")
    os.makedirs(profile_dir, exist_ok=True)
    os.makedirs(backup_dir, exist_ok=True)
    
    yield main_db_path, app_db_path, profile_dir, backup_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestBackupRestoreRoundTrip:
    """
    **Feature: multi-profile-fingerprint-automation, Property 15: Backup/Restore Round-Trip**
    **Validates: Requirements 5.3, 5.4**
    
    For any set of profiles, backing up and then restoring SHALL produce
    profiles with equivalent data and fingerprint configurations.
    """
    
    @given(
        profile_name=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        profile_id=st.text(min_size=10, max_size=20, alphabet=st.characters(whitelist_categories=('N',))),
        status=st.sampled_from(["active", "inactive"]),
        proxy=st.text(min_size=0, max_size=30, alphabet=st.characters(whitelist_categories=('L', 'N', 'P'))),
        username=st.text(min_size=0, max_size=20, alphabet=st.characters(whitelist_categories=('L', 'N')))
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_backup_restore_preserves_profile_data(
        self, profile_name, profile_id, status, proxy, username, temp_setup
    ):
        """Test that backup and restore preserves profile data."""
        main_db_path, app_db_path, profile_dir, backup_dir = temp_setup
        
        # Clean both databases
        conn = sqlite3.connect(main_db_path)
        conn.execute("DELETE FROM danhsachacc")
        conn.commit()
        conn.close()
        
        # Clean app database if exists
        if os.path.exists(app_db_path):
            conn = sqlite3.connect(app_db_path)
            try:
                conn.execute("DELETE FROM app_profiles")
                conn.execute("DELETE FROM profile_status")
                conn.commit()
            except sqlite3.OperationalError:
                pass
            conn.close()
        
        repo = ProfileRepository(db_path=main_db_path, app_db_path=app_db_path, profile_dir=profile_dir)
        backup_manager = BackupManager(repository=repo, backup_dir=backup_dir)
        
        # Create profile data
        original_data = ProfileData(
            name=profile_name,
            idprofile=profile_id,
            status=status,
            proxy=proxy,
            username_fb=username
        )
        
        # Create profile in database
        repo.create_profile(original_data)
        
        # Create profile directory with some content
        profile_path = repo.get_profile_path(profile_id)
        os.makedirs(os.path.join(profile_path, "Default"), exist_ok=True)
        
        # Create Preferences file with fingerprint
        prefs = {
            "gologin": {
                "audioContext": {"enable": True, "noiseValue": 1.5e-8},
                "canvas": {"mode": "noise", "noise": 5.5}
            }
        }
        with open(os.path.join(profile_path, "Default", "Preferences"), 'w') as f:
            json.dump(prefs, f)
        
        # Backup
        backup_info = backup_manager.backup_profile(profile_id)
        assert backup_info is not None
        assert os.path.exists(backup_info.backup_path)
        
        # Delete original
        repo.delete_profile(profile_id)
        shutil.rmtree(profile_path, ignore_errors=True)
        
        # Verify deleted
        assert repo.get_profile_by_id(profile_id) is None
        assert not os.path.exists(profile_path)
        
        # Restore
        restored_profile = backup_manager.restore_profile(backup_info.backup_path)
        assert restored_profile is not None
        
        # Verify restored data matches original
        restored_data = repo.get_profile_by_id(profile_id)
        assert restored_data is not None
        assert restored_data.name == original_data.name
        assert restored_data.idprofile == original_data.idprofile
        assert restored_data.status == original_data.status
        assert restored_data.proxy == original_data.proxy
        assert restored_data.username_fb == original_data.username_fb
        
        # Verify directory restored
        assert os.path.exists(profile_path)
        
        # Verify Preferences file restored
        prefs_path = os.path.join(profile_path, "Default", "Preferences")
        assert os.path.exists(prefs_path)
        
        with open(prefs_path, 'r') as f:
            restored_prefs = json.load(f)
        
        assert restored_prefs == prefs


class TestBackupOperations:
    """Test backup operations."""
    
    def test_backup_creates_valid_zip(self, temp_setup):
        """Test that backup creates a valid zip file."""
        main_db_path, app_db_path, profile_dir, backup_dir = temp_setup
        
        repo = ProfileRepository(db_path=main_db_path, app_db_path=app_db_path, profile_dir=profile_dir)
        backup_manager = BackupManager(repository=repo, backup_dir=backup_dir)
        
        # Create profile
        profile_data = ProfileData(
            name="Test Profile",
            idprofile="12345678901234567890",
            status="inactive"
        )
        repo.create_profile(profile_data)
        
        # Create profile directory
        profile_path = repo.get_profile_path("12345678901234567890")
        os.makedirs(os.path.join(profile_path, "Default"), exist_ok=True)
        with open(os.path.join(profile_path, "Default", "test.txt"), 'w') as f:
            f.write("test content")
        
        # Backup
        backup_info = backup_manager.backup_profile("12345678901234567890")
        
        assert backup_info is not None
        assert backup_info.profile_id == "12345678901234567890"
        assert backup_info.profile_name == "Test Profile"
        assert backup_info.size_bytes > 0
        assert os.path.exists(backup_info.backup_path)
    
    def test_backup_nonexistent_profile_returns_none(self, temp_setup):
        """Test that backing up non-existent profile returns None."""
        main_db_path, app_db_path, profile_dir, backup_dir = temp_setup
        
        repo = ProfileRepository(db_path=main_db_path, app_db_path=app_db_path, profile_dir=profile_dir)
        backup_manager = BackupManager(repository=repo, backup_dir=backup_dir)
        
        result = backup_manager.backup_profile("nonexistent")
        assert result is None
    
    def test_validate_backup(self, temp_setup):
        """Test backup validation."""
        main_db_path, app_db_path, profile_dir, backup_dir = temp_setup
        
        repo = ProfileRepository(db_path=main_db_path, app_db_path=app_db_path, profile_dir=profile_dir)
        backup_manager = BackupManager(repository=repo, backup_dir=backup_dir)
        
        # Create and backup profile
        profile_data = ProfileData(
            name="Test",
            idprofile="99999999999999999999",
            status="inactive"
        )
        repo.create_profile(profile_data)
        
        profile_path = repo.get_profile_path("99999999999999999999")
        os.makedirs(profile_path, exist_ok=True)
        
        backup_info = backup_manager.backup_profile("99999999999999999999")
        
        # Validate
        assert backup_manager.validate_backup(backup_info.backup_path) is True
        assert backup_manager.validate_backup("nonexistent.zip") is False


class TestRestoreOperations:
    """Test restore operations."""
    
    def test_restore_with_overwrite(self, temp_setup):
        """Test restoring with overwrite flag."""
        main_db_path, app_db_path, profile_dir, backup_dir = temp_setup
        
        repo = ProfileRepository(db_path=main_db_path, app_db_path=app_db_path, profile_dir=profile_dir)
        backup_manager = BackupManager(repository=repo, backup_dir=backup_dir)
        
        # Create original profile
        profile_data = ProfileData(
            name="Original",
            idprofile="88888888888888888888",
            status="inactive"
        )
        repo.create_profile(profile_data)
        
        profile_path = repo.get_profile_path("88888888888888888888")
        os.makedirs(profile_path, exist_ok=True)
        
        # Backup
        backup_info = backup_manager.backup_profile("88888888888888888888")
        
        # Modify profile
        repo.update_profile_status("88888888888888888888", "running")
        
        # Restore without overwrite should fail
        result = backup_manager.restore_profile(backup_info.backup_path, overwrite=False)
        assert result is None
        
        # Restore with overwrite should succeed
        result = backup_manager.restore_profile(backup_info.backup_path, overwrite=True)
        assert result is not None
        
        # Verify original status restored
        restored = repo.get_profile_by_id("88888888888888888888")
        assert restored.status == "inactive"


class TestListBackups:
    """Test listing backups."""
    
    def test_list_backups_empty(self, temp_setup):
        """Test listing backups when none exist."""
        main_db_path, app_db_path, profile_dir, backup_dir = temp_setup
        
        repo = ProfileRepository(db_path=main_db_path, app_db_path=app_db_path, profile_dir=profile_dir)
        backup_manager = BackupManager(repository=repo, backup_dir=backup_dir)
        
        backups = backup_manager.list_backups()
        assert backups == []
    
    def test_list_backups_filter_by_profile(self, temp_setup):
        """Test filtering backups by profile ID."""
        main_db_path, app_db_path, profile_dir, backup_dir = temp_setup
        
        repo = ProfileRepository(db_path=main_db_path, app_db_path=app_db_path, profile_dir=profile_dir)
        backup_manager = BackupManager(repository=repo, backup_dir=backup_dir)
        
        # Create two profiles
        for i, pid in enumerate(["11111111111111111111", "22222222222222222222"]):
            profile_data = ProfileData(
                name=f"Profile {i}",
                idprofile=pid,
                status="inactive"
            )
            repo.create_profile(profile_data)
            
            profile_path = repo.get_profile_path(pid)
            os.makedirs(profile_path, exist_ok=True)
            
            backup_manager.backup_profile(pid)
        
        # List all
        all_backups = backup_manager.list_backups()
        assert len(all_backups) == 2
        
        # Filter by profile
        filtered = backup_manager.list_backups(profile_id="11111111111111111111")
        assert len(filtered) == 1
        assert filtered[0].profile_id == "11111111111111111111"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
