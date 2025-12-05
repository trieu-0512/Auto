# Property-based tests for Profile Manager
# Feature: multi-profile-fingerprint-automation

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
import tempfile
import os
import shutil
import sqlite3

from app.core.profile_manager import ProfileManager
from app.data.profile_repository import ProfileRepository
from app.core.fingerprint_generator import FingerprintGenerator
from app.data.profile_models import ProfileData


@pytest.fixture
def temp_setup():
    """Create temporary databases, profile directory, and template."""
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
    template_dir = os.path.join(temp_dir, "template")
    os.makedirs(profile_dir, exist_ok=True)
    os.makedirs(template_dir, exist_ok=True)
    
    # Create template structure
    os.makedirs(os.path.join(template_dir, "Default"), exist_ok=True)
    with open(os.path.join(template_dir, "Default", "Preferences"), 'w') as f:
        f.write('{"gologin": {"audioContext": {"enable": true, "noiseValue": 0.0}}}')
    
    yield main_db_path, app_db_path, profile_dir, template_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestProfileCreationGeneratesUniqueID:
    """
    **Feature: multi-profile-fingerprint-automation, Property 6: Profile Creation Generates Unique ID**
    **Validates: Requirements 2.1**
    
    For any two profile creation operations, the generated profile IDs
    SHALL be unique and the created directories SHALL not overlap.
    """
    
    @given(num_profiles=st.integers(min_value=2, max_value=10))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_multiple_profiles_have_unique_ids(self, num_profiles, temp_setup):
        """Test that creating multiple profiles generates unique IDs."""
        main_db_path, app_db_path, profile_dir, template_dir = temp_setup
        
        repo = ProfileRepository(db_path=main_db_path, app_db_path=app_db_path, profile_dir=profile_dir)
        generator = FingerprintGenerator()
        manager = ProfileManager(
            repository=repo,
            generator=generator,
            template_dir=template_dir
        )
        
        created_profiles = []
        profile_ids = set()
        
        for i in range(num_profiles):
            profile = manager.create_profile(f"Test Profile {i}")
            if profile:
                created_profiles.append(profile)
                profile_ids.add(profile.profile_id)
        
        # All IDs should be unique
        assert len(profile_ids) == len(created_profiles)
        
        # All directories should exist and be different
        paths = {p.path for p in created_profiles}
        assert len(paths) == len(created_profiles)
        
        for profile in created_profiles:
            assert os.path.isdir(profile.path)
    
    @given(iteration=st.integers(min_value=1, max_value=5))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_profile_id_format_valid(self, iteration, temp_setup):
        """Test that generated profile IDs have valid format."""
        main_db_path, app_db_path, profile_dir, template_dir = temp_setup
        
        repo = ProfileRepository(db_path=main_db_path, app_db_path=app_db_path, profile_dir=profile_dir)
        generator = FingerprintGenerator()
        manager = ProfileManager(
            repository=repo,
            generator=generator,
            template_dir=template_dir
        )
        
        profile = manager.create_profile("Test Profile")
        assert profile is not None
        
        # ID should be numeric string
        assert profile.profile_id.isdigit()
        
        # ID should be reasonable length
        assert len(profile.profile_id) <= 20


class TestFingerprintRandomizationChangesValues:
    """
    **Feature: multi-profile-fingerprint-automation, Property 7: Fingerprint Randomization Changes Values**
    **Validates: Requirements 2.2**
    
    For any profile created from template, the noise values SHALL differ from the template values.
    """
    
    @given(iteration=st.integers(min_value=1, max_value=20))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_created_profile_has_different_noise_values(self, iteration, temp_setup):
        """Test that created profiles have randomized noise values."""
        main_db_path, app_db_path, profile_dir, template_dir = temp_setup
        
        repo = ProfileRepository(db_path=main_db_path, app_db_path=app_db_path, profile_dir=profile_dir)
        generator = FingerprintGenerator()
        manager = ProfileManager(
            repository=repo,
            generator=generator,
            template_dir=template_dir
        )
        
        # Create profile
        profile = manager.create_profile("Test Profile")
        assert profile is not None
        
        # Get fingerprint
        fingerprint = manager.get_profile_fingerprint(profile.profile_id)
        assert fingerprint is not None
        
        # Template has 0.0 noise values, generated should be different
        assert fingerprint.audioContext.noiseValue != 0.0


class TestProfileFilteringCorrectness:
    """
    **Feature: multi-profile-fingerprint-automation, Property 17: Profile Filtering Correctness**
    **Validates: Requirements 7.4**
    
    For any filter criteria, the returned profiles SHALL all match the criteria
    and no matching profiles SHALL be excluded.
    """
    
    @given(
        status_filter=st.sampled_from(["active", "inactive", "running", "error"]),
        num_matching=st.integers(min_value=1, max_value=5),
        num_non_matching=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_status_filtering_returns_correct_profiles(
        self, status_filter, num_matching, num_non_matching, temp_setup
    ):
        """Test that status filtering returns only matching profiles."""
        main_db_path, app_db_path, profile_dir, template_dir = temp_setup
        
        # Clean both databases before each test iteration
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
                pass  # Tables may not exist yet
            conn.close()
        
        repo = ProfileRepository(db_path=main_db_path, app_db_path=app_db_path, profile_dir=profile_dir)
        manager = ProfileManager(
            repository=repo,
            generator=FingerprintGenerator(),
            template_dir=template_dir
        )
        
        # Create profiles with matching status
        matching_ids = []
        for i in range(num_matching):
            profile_data = ProfileData(
                name=f"Match {i}",
                idprofile=f"match_{i:010d}",
                status=status_filter
            )
            repo.create_profile(profile_data)
            matching_ids.append(profile_data.idprofile)
        
        # Create profiles with non-matching status
        non_matching_statuses = ["active", "inactive", "running", "error"]
        non_matching_statuses.remove(status_filter)
        
        for i in range(num_non_matching):
            other_status = non_matching_statuses[i % len(non_matching_statuses)]
            profile_data = ProfileData(
                name=f"NoMatch {i}",
                idprofile=f"nomatch_{i:010d}",
                status=other_status
            )
            repo.create_profile(profile_data)
        
        # Filter by status
        filtered_profiles = manager.filter_profiles(status=status_filter)
        
        # All returned profiles should have the matching status
        for profile in filtered_profiles:
            assert profile.status == status_filter
        
        # Should return exactly the matching profiles
        filtered_ids = {p.profile_id for p in filtered_profiles}
        expected_ids = set(matching_ids)
        assert filtered_ids == expected_ids


class TestProfileManagerOperations:
    """Test general ProfileManager operations."""
    
    def test_load_all_profiles(self, temp_setup):
        """Test loading all profiles."""
        main_db_path, app_db_path, profile_dir, template_dir = temp_setup
        
        repo = ProfileRepository(db_path=main_db_path, app_db_path=app_db_path, profile_dir=profile_dir)
        manager = ProfileManager(
            repository=repo,
            generator=FingerprintGenerator(),
            template_dir=template_dir
        )
        
        # Create some profiles
        for i in range(3):
            profile_data = ProfileData(
                name=f"Profile {i}",
                idprofile=f"profile_{i:010d}",
                status="inactive"
            )
            repo.create_profile(profile_data)
        
        # Load all
        profiles = manager.load_all_profiles()
        assert len(profiles) == 3
    
    def test_update_profile_status(self, temp_setup):
        """Test updating profile status."""
        main_db_path, app_db_path, profile_dir, template_dir = temp_setup
        
        repo = ProfileRepository(db_path=main_db_path, app_db_path=app_db_path, profile_dir=profile_dir)
        manager = ProfileManager(
            repository=repo,
            generator=FingerprintGenerator(),
            template_dir=template_dir
        )
        
        # Create profile
        profile = manager.create_profile("Test")
        assert profile is not None
        
        # Update status
        assert manager.update_profile_status(profile.profile_id, "running")
        
        # Verify
        updated = manager.get_profile(profile.profile_id)
        assert updated.status == "running"
    
    def test_delete_profile(self, temp_setup):
        """Test deleting a profile."""
        main_db_path, app_db_path, profile_dir, template_dir = temp_setup
        
        repo = ProfileRepository(db_path=main_db_path, app_db_path=app_db_path, profile_dir=profile_dir)
        manager = ProfileManager(
            repository=repo,
            generator=FingerprintGenerator(),
            template_dir=template_dir
        )
        
        # Create profile
        profile = manager.create_profile("To Delete")
        assert profile is not None
        profile_path = profile.path
        
        # Delete
        assert manager.delete_profile(profile.profile_id)
        
        # Verify deleted from database
        assert manager.get_profile(profile.profile_id) is None
        
        # Verify directory deleted
        assert not os.path.exists(profile_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
