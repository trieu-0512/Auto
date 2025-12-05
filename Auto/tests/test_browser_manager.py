# Property-based tests for Browser Manager
# Feature: multi-profile-fingerprint-automation

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import Mock, patch
import tempfile
import os

from app.core.browser_manager import BrowserManager
from app.core.profile_manager import ProfileManager
from app.data.profile_models import Profile, ProfileData


@pytest.fixture
def mock_profile_manager():
    """Create a mock ProfileManager."""
    manager = Mock(spec=ProfileManager)
    return manager


@pytest.fixture
def temp_profile():
    """Create a temporary profile for testing."""
    temp_dir = tempfile.mkdtemp()
    profile_data = ProfileData(
        name="Test Profile",
        idprofile="12345678901234567890",
        status="inactive"
    )
    profile = Profile(
        data=profile_data,
        fingerprint=None,
        path=temp_dir,
        exists=True
    )
    yield profile
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestChromeOptionsContainsRequiredArguments:
    """
    **Feature: multi-profile-fingerprint-automation, Property 10: ChromeOptions Contains Required Arguments**
    **Validates: Requirements 3.2**
    
    For any profile launch, the ChromeOptions SHALL contain: --user-data-dir with correct profile path,
    --load-extension with extensions path, --window-position, and --force-dark-mode.
    """
    
    @given(
        x_pos=st.integers(min_value=0, max_value=1920),
        y_pos=st.integers(min_value=0, max_value=1080)
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_chrome_options_has_required_arguments(self, x_pos, y_pos, mock_profile_manager, temp_profile):
        """Test that ChromeOptions contains all required arguments."""
        browser_manager = BrowserManager(
            profile_manager=mock_profile_manager,
            orbita_path="test/chrome.exe",
            extensions_dir="test_extensions"
        )
        
        options = browser_manager.build_chrome_options(
            temp_profile,
            window_position=(x_pos, y_pos),
            extensions=[]
        )
        
        # Check binary location (now uses absolute path)
        assert "chrome.exe" in options.binary_location
        
        # Check arguments
        args = options.arguments
        
        # Check user-data-dir (now uses absolute path)
        user_data_arg = next((arg for arg in args if arg.startswith("--user-data-dir=")), None)
        assert user_data_arg is not None
        # The path should be absolute and contain the temp profile path
        assert os.path.basename(temp_profile.path) in user_data_arg or temp_profile.path in user_data_arg
        
        # Check window position
        position_arg = next((arg for arg in args if arg.startswith("--window-position=")), None)
        assert position_arg is not None
        assert f"--window-position={x_pos},{y_pos}" == position_arg
        
        # Check force dark mode
        assert "--force-dark-mode" in args
    
    def test_chrome_options_default_position(self, mock_profile_manager, temp_profile):
        """Test that default window position is 0,0."""
        browser_manager = BrowserManager(
            profile_manager=mock_profile_manager,
            orbita_path="test/chrome.exe"
        )
        
        options = browser_manager.build_chrome_options(temp_profile)
        args = options.arguments
        
        assert "--window-position=0,0" in args


class TestWindowPositionsNonOverlapping:
    """
    **Feature: multi-profile-fingerprint-automation, Property 11: Window Positions Non-Overlapping**
    **Validates: Requirements 3.3**
    
    For any set of N concurrent profile launches, the calculated window positions
    SHALL not overlap (no two windows share the same position).
    """
    
    @given(num_windows=st.integers(min_value=2, max_value=20))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_window_positions_do_not_overlap(self, num_windows, mock_profile_manager):
        """Test that calculated window positions don't overlap."""
        browser_manager = BrowserManager(profile_manager=mock_profile_manager)
        
        positions = []
        for i in range(num_windows):
            pos = browser_manager.calculate_window_position(i)
            positions.append(pos)
        
        # All positions should be unique
        unique_positions = set(positions)
        assert len(unique_positions) == len(positions)
        
        # Check that positions are reasonable (within screen bounds or wrapped)
        for x, y in positions:
            assert x >= 0
            assert y >= 0
    
    @given(index=st.integers(min_value=0, max_value=100))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_window_position_deterministic(self, index, mock_profile_manager):
        """Test that window position calculation is deterministic."""
        browser_manager = BrowserManager(profile_manager=mock_profile_manager)
        
        pos1 = browser_manager.calculate_window_position(index)
        pos2 = browser_manager.calculate_window_position(index)
        pos3 = browser_manager.calculate_window_position(index)
        
        assert pos1 == pos2 == pos3


class TestSessionCloseUpdatesStatus:
    """
    **Feature: multi-profile-fingerprint-automation, Property 12: Session Close Updates Status**
    **Validates: Requirements 3.4, 7.1**
    
    For any profile session that is closed, the database status field
    SHALL be updated to reflect the closed state.
    """
    
    def test_close_session_updates_status(self, mock_profile_manager):
        """Test that closing a session updates the profile status."""
        browser_manager = BrowserManager(profile_manager=mock_profile_manager)
        
        # Mock an active session
        mock_driver = Mock()
        profile_id = "test_profile_123"
        browser_manager.active_sessions[profile_id] = mock_driver
        
        # Close session
        result = browser_manager.close_session(profile_id)
        
        # Verify
        assert result is True
        assert profile_id not in browser_manager.active_sessions
        mock_driver.quit.assert_called_once()
        mock_profile_manager.update_profile_status.assert_called_once_with(profile_id, "inactive")
    
    def test_close_nonexistent_session_returns_false(self, mock_profile_manager):
        """Test that closing a non-existent session returns False."""
        browser_manager = BrowserManager(profile_manager=mock_profile_manager)
        
        result = browser_manager.close_session("nonexistent_profile")
        
        assert result is False
        mock_profile_manager.update_profile_status.assert_not_called()
    
    def test_close_all_sessions(self, mock_profile_manager):
        """Test closing all sessions."""
        browser_manager = BrowserManager(profile_manager=mock_profile_manager)
        
        # Add mock sessions
        for i in range(3):
            mock_driver = Mock()
            browser_manager.active_sessions[f"profile_{i}"] = mock_driver
        
        # Close all
        count = browser_manager.close_all_sessions()
        
        assert count == 3
        assert len(browser_manager.active_sessions) == 0


class TestBrowserManagerGeneral:
    """Test general BrowserManager functionality."""
    
    def test_get_active_sessions_returns_copy(self, mock_profile_manager):
        """Test that get_active_sessions returns a copy."""
        browser_manager = BrowserManager(profile_manager=mock_profile_manager)
        
        # Add mock session
        mock_driver = Mock()
        browser_manager.active_sessions["test"] = mock_driver
        
        sessions = browser_manager.get_active_sessions()
        
        # Should be a copy
        assert sessions is not browser_manager.active_sessions
        assert sessions == browser_manager.active_sessions
    
    def test_session_count_correct(self, mock_profile_manager):
        """Test that session count is correct."""
        browser_manager = BrowserManager(profile_manager=mock_profile_manager)
        
        assert browser_manager.get_session_count() == 0
        
        browser_manager.active_sessions["test1"] = Mock()
        browser_manager.active_sessions["test2"] = Mock()
        
        assert browser_manager.get_session_count() == 2
    
    def test_is_session_active(self, mock_profile_manager):
        """Test session active check."""
        browser_manager = BrowserManager(profile_manager=mock_profile_manager)
        
        assert not browser_manager.is_session_active("test")
        
        browser_manager.active_sessions["test"] = Mock()
        
        assert browser_manager.is_session_active("test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestExtensionLoadingArguments:
    """
    **Feature: multi-profile-fingerprint-automation, Property 18: Extension Loading Arguments**
    **Validates: Requirements 8.1**
    
    For any profile with configured extensions, the browser launch command
    SHALL include --load-extension argument with paths to all configured extensions.
    """
    
    @given(
        num_extensions=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_extension_paths_included_in_options(self, num_extensions, mock_profile_manager, temp_profile):
        """Test that extension paths are included in ChromeOptions."""
        import tempfile
        import shutil
        
        # Create temp extensions directory
        ext_dir = tempfile.mkdtemp()
        
        try:
            # Create mock extension directories
            extension_names = []
            for i in range(num_extensions):
                ext_name = f"TestExtension{i}"
                ext_path = os.path.join(ext_dir, ext_name)
                os.makedirs(ext_path, exist_ok=True)
                # Create minimal manifest
                with open(os.path.join(ext_path, "manifest.json"), 'w') as f:
                    f.write('{"name": "Test", "version": "1.0", "manifest_version": 2}')
                extension_names.append(ext_name)
            
            browser_manager = BrowserManager(
                profile_manager=mock_profile_manager,
                orbita_path="test/chrome.exe",
                extensions_dir=ext_dir
            )
            
            options = browser_manager.build_chrome_options(
                temp_profile,
                extensions=extension_names
            )
            
            args = options.arguments
            
            # Find load-extension argument
            load_ext_arg = next((arg for arg in args if arg.startswith("--load-extension=")), None)
            
            assert load_ext_arg is not None, "Should have --load-extension argument"
            
            # Verify all extensions are included
            for ext_name in extension_names:
                assert ext_name in load_ext_arg, f"Extension {ext_name} should be in load-extension argument"
        
        finally:
            shutil.rmtree(ext_dir, ignore_errors=True)
    
    def test_no_extension_arg_when_no_extensions(self, mock_profile_manager, temp_profile):
        """Test that no --load-extension arg when no extensions configured."""
        import tempfile
        import shutil
        
        # Create empty extensions directory
        ext_dir = tempfile.mkdtemp()
        
        try:
            browser_manager = BrowserManager(
                profile_manager=mock_profile_manager,
                orbita_path="test/chrome.exe",
                extensions_dir=ext_dir
            )
            
            options = browser_manager.build_chrome_options(
                temp_profile,
                extensions=[]
            )
            
            args = options.arguments
            
            # Should not have load-extension argument
            load_ext_arg = next((arg for arg in args if arg.startswith("--load-extension=")), None)
            assert load_ext_arg is None, "Should not have --load-extension argument when no extensions"
        
        finally:
            shutil.rmtree(ext_dir, ignore_errors=True)
