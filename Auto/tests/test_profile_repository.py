# Property-based tests for Profile Repository
# Feature: multi-profile-fingerprint-automation

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
import sqlite3
import tempfile
import os
import shutil

from app.data.profile_repository import ProfileRepository
from app.data.profile_models import ProfileData


@pytest.fixture
def temp_db():
    """Create temporary databases for testing (main + app)."""
    # Create temp directory for databases
    temp_dir = tempfile.mkdtemp()
    main_db_path = os.path.join(temp_dir, "data.db")
    app_db_path = os.path.join(temp_dir, "app_data.db")
    
    # Create main database table
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
    
    yield main_db_path, app_db_path
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_profile_dir():
    """Create a temporary profile directory for testing."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture
def repository(temp_db, temp_profile_dir):
    """Create a repository with temporary database and profile directory."""
    main_db_path, app_db_path = temp_db
    return ProfileRepository(db_path=main_db_path, app_db_path=app_db_path, profile_dir=temp_profile_dir)


class TestDatabaseQueryReturnsAllProfiles:
    """
    **Feature: multi-profile-fingerprint-automation, Property 1: Database Query Returns All Profiles**
    **Validates: Requirements 1.1**
    
    For any database state with N profile records, querying all profiles
    SHALL return exactly N ProfileData objects with matching idprofile values.
    """
    
    @given(
        num_profiles=st.integers(min_value=0, max_value=20),
        profile_ids=st.lists(
            st.text(min_size=10, max_size=20, alphabet=st.characters(whitelist_categories=('N',))),
            min_size=1,
            max_size=20,
            unique=True
        )
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_query_returns_all_profiles(self, temp_profile_dir, num_profiles, profile_ids):
        """Test that get_all_profiles returns exactly N profiles."""
        # Create fresh databases for each test iteration
        temp_dir = tempfile.mkdtemp()
        main_db_path = os.path.join(temp_dir, "data.db")
        app_db_path = os.path.join(temp_dir, "app_data.db")
        
        try:
            # Create main database table
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
            
            # Limit to available unique IDs
            actual_num = min(num_profiles, len(profile_ids))
            ids_to_use = profile_ids[:actual_num]
            
            # Insert profiles directly into main database
            for i, pid in enumerate(ids_to_use):
                conn.execute(
                    "INSERT INTO danhsachacc (name, idprofile, status, sothutu) VALUES (?, ?, ?, ?)",
                    (f"Profile {i}", pid, "inactive", i)
                )
            conn.commit()
            conn.close()
            
            # Query using repository (will sync from main to app db)
            repo = ProfileRepository(db_path=main_db_path, app_db_path=app_db_path, profile_dir=temp_profile_dir)
            profiles = repo.get_all_profiles()
            
            # Verify count matches
            assert len(profiles) == actual_num
            
            # Verify all IDs are present
            returned_ids = {p.idprofile for p in profiles}
            expected_ids = set(ids_to_use)
            assert returned_ids == expected_ids
        finally:
            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestProfilePathMappingConsistency:
    """
    **Feature: multi-profile-fingerprint-automation, Property 2: Profile Path Mapping Consistency**
    **Validates: Requirements 1.2**
    
    For any profile with idprofile value X, the mapped filesystem path
    SHALL always be `profile/{X}` and this mapping SHALL be deterministic.
    """
    
    @given(
        profile_id=st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('N', 'L')))
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_path_mapping_deterministic(self, repository, profile_id):
        """Test that path mapping is deterministic."""
        # Call get_profile_path multiple times
        path1 = repository.get_profile_path(profile_id)
        path2 = repository.get_profile_path(profile_id)
        path3 = repository.get_profile_path(profile_id)
        
        # All calls should return the same path
        assert path1 == path2 == path3
        
        # Path should end with profile_id
        assert path1.endswith(profile_id)
    
    @given(
        profile_id=st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('N',)))
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_path_format_correct(self, temp_profile_dir, profile_id):
        """Test that path format is profile_dir/profile_id."""
        repo = ProfileRepository(db_path="test.db", profile_dir=temp_profile_dir)
        
        path = repo.get_profile_path(profile_id)
        expected = os.path.join(temp_profile_dir, profile_id)
        
        assert path == expected


class TestMissingProfileDetection:
    """
    **Feature: multi-profile-fingerprint-automation, Property 4: Missing Profile Detection**
    **Validates: Requirements 1.4**
    
    For any database record where the corresponding profile directory does not exist,
    the profile_exists() method SHALL return False.
    """
    
    @given(
        profile_id=st.text(min_size=10, max_size=25, alphabet=st.characters(whitelist_categories=('N',)))
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_nonexistent_profile_detected(self, repository, profile_id):
        """Test that non-existent profiles are detected."""
        # Profile directory should not exist
        assert not repository.profile_exists(profile_id)
    
    @given(
        profile_id=st.text(min_size=10, max_size=25, alphabet=st.characters(whitelist_categories=('N',)))
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_existing_profile_detected(self, temp_profile_dir, profile_id):
        """Test that existing profiles are detected."""
        repo = ProfileRepository(db_path="test.db", profile_dir=temp_profile_dir)
        
        # Create the profile directory
        profile_path = os.path.join(temp_profile_dir, profile_id)
        os.makedirs(profile_path, exist_ok=True)
        
        # Should detect as existing
        assert repo.profile_exists(profile_id)
        
        # Cleanup
        os.rmdir(profile_path)


class TestProfileCRUD:
    """Test basic CRUD operations."""
    
    def test_create_and_get_profile(self, repository):
        """Test creating and retrieving a profile."""
        profile = ProfileData(
            name="Test Profile",
            idprofile="12345678901234567890",
            status="inactive",
            proxymode="none"
        )
        
        # Create
        assert repository.create_profile(profile)
        
        # Get
        retrieved = repository.get_profile_by_id("12345678901234567890")
        assert retrieved is not None
        assert retrieved.name == "Test Profile"
        assert retrieved.idprofile == "12345678901234567890"
    
    def test_update_profile_status(self, repository):
        """Test updating profile status."""
        profile = ProfileData(
            name="Test Profile",
            idprofile="98765432109876543210",
            status="inactive"
        )
        repository.create_profile(profile)
        
        # Update status
        assert repository.update_profile_status("98765432109876543210", "running")
        
        # Verify
        updated = repository.get_profile_by_id("98765432109876543210")
        assert updated.status == "running"
    
    def test_delete_profile(self, repository):
        """Test deleting a profile."""
        profile = ProfileData(
            name="To Delete",
            idprofile="11111111111111111111",
            status="inactive"
        )
        repository.create_profile(profile)
        
        # Delete
        assert repository.delete_profile("11111111111111111111")
        
        # Verify deleted
        assert repository.get_profile_by_id("11111111111111111111") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
