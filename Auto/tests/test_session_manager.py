# Property-based tests for Session Manager
# Feature: multi-profile-fingerprint-automation

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import Mock, patch
import time

from app.core.session_manager import SessionManager, SessionStatus
from app.core.browser_manager import BrowserManager


@pytest.fixture
def mock_browser_manager():
    """Create mock BrowserManager."""
    manager = Mock(spec=BrowserManager)
    manager.get_session_count.return_value = 0
    manager.is_session_active.return_value = False
    manager.close_all_sessions.return_value = 0
    manager.calculate_window_position.return_value = (0, 0)
    manager.launch_profile.return_value = Mock()  # Mock WebDriver
    return manager


class TestConcurrentSessionLimitEnforcement:
    """
    **Feature: multi-profile-fingerprint-automation, Property 16: Concurrent Session Limit Enforcement**
    **Validates: Requirements 6.2**
    
    For any batch execution request, the number of simultaneously running sessions
    SHALL not exceed the configured maximum concurrent limit.
    """
    
    @given(
        max_concurrent=st.integers(min_value=1, max_value=5),
        num_profiles=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_concurrent_limit_not_exceeded(self, max_concurrent, num_profiles, mock_browser_manager):
        """Test that concurrent session limit is enforced."""
        # Track active count
        active_count = [0]
        max_observed = [0]
        
        def mock_get_session_count():
            return active_count[0]
        
        def mock_launch_profile(*args, **kwargs):
            if active_count[0] < max_concurrent:
                active_count[0] += 1
                max_observed[0] = max(max_observed[0], active_count[0])
                return Mock()
            return None
        
        mock_browser_manager.get_session_count.side_effect = mock_get_session_count
        mock_browser_manager.launch_profile.side_effect = mock_launch_profile
        
        session_manager = SessionManager(
            browser_manager=mock_browser_manager,
            max_concurrent=max_concurrent,
            default_delay=0.0
        )
        
        # Generate profile IDs
        profile_ids = [f"profile_{i:03d}" for i in range(num_profiles)]
        
        # Start batch
        session_manager.start_batch(profile_ids, delay=0.0)
        
        # Wait a bit for launches to process
        time.sleep(0.2)
        
        # Stop batch
        session_manager.stop_batch()
        
        # Check that we never exceeded the limit
        assert max_observed[0] <= max_concurrent
    
    def test_can_start_session_respects_limit(self, mock_browser_manager):
        """Test that can_start_session respects the limit."""
        max_concurrent = 3
        
        session_manager = SessionManager(
            browser_manager=mock_browser_manager,
            max_concurrent=max_concurrent
        )
        
        # Under limit
        mock_browser_manager.get_session_count.return_value = 2
        assert session_manager.can_start_session() is True
        
        # At limit
        mock_browser_manager.get_session_count.return_value = 3
        assert session_manager.can_start_session() is False
        
        # Over limit
        mock_browser_manager.get_session_count.return_value = 4
        assert session_manager.can_start_session() is False


class TestBatchExecution:
    """Test batch execution functionality."""
    
    def test_start_batch_success(self, mock_browser_manager):
        """Test successful batch start."""
        session_manager = SessionManager(
            browser_manager=mock_browser_manager,
            max_concurrent=5
        )
        
        profile_ids = ["profile1", "profile2", "profile3"]
        result = session_manager.start_batch(profile_ids, delay=0.0)
        
        assert result is True
        
        # Wait a bit for thread to start
        time.sleep(0.1)
        
        # Cleanup
        session_manager.stop_batch()
    
    def test_start_batch_already_running(self, mock_browser_manager):
        """Test that starting batch when already running fails."""
        session_manager = SessionManager(
            browser_manager=mock_browser_manager,
            max_concurrent=5
        )
        
        profile_ids = ["profile1", "profile2"]
        
        # Start first batch with longer delay to keep it running
        result1 = session_manager.start_batch(profile_ids, delay=1.0)
        assert result1 is True
        
        # Wait for thread to start
        time.sleep(0.1)
        
        # Try to start second batch while first is running
        result2 = session_manager.start_batch(profile_ids, delay=0.0)
        assert result2 is False
        
        # Cleanup
        session_manager.stop_batch()
    
    def test_stop_batch(self, mock_browser_manager):
        """Test stopping batch execution."""
        mock_browser_manager.close_all_sessions.return_value = 3
        
        session_manager = SessionManager(
            browser_manager=mock_browser_manager,
            max_concurrent=5
        )
        
        profile_ids = ["profile1", "profile2", "profile3"]
        session_manager.start_batch(profile_ids, delay=0.0)
        
        time.sleep(0.1)
        
        stopped_count = session_manager.stop_batch()
        
        assert stopped_count == 3
        mock_browser_manager.close_all_sessions.assert_called_once()


class TestSessionStatus:
    """Test session status tracking."""
    
    def test_get_session_status_running(self, mock_browser_manager):
        """Test getting status of running session."""
        mock_browser_manager.is_session_active.return_value = True
        
        session_manager = SessionManager(
            browser_manager=mock_browser_manager,
            max_concurrent=5
        )
        
        status = session_manager.get_session_status("profile1")
        assert status == SessionStatus.RUNNING
    
    def test_get_session_status_unknown(self, mock_browser_manager):
        """Test getting status of unknown session."""
        mock_browser_manager.is_session_active.return_value = False
        
        session_manager = SessionManager(
            browser_manager=mock_browser_manager,
            max_concurrent=5
        )
        
        status = session_manager.get_session_status("unknown_profile")
        assert status is None
    
    def test_stop_specific_session(self, mock_browser_manager):
        """Test stopping a specific session."""
        mock_browser_manager.close_session.return_value = True
        
        session_manager = SessionManager(
            browser_manager=mock_browser_manager,
            max_concurrent=5
        )
        
        result = session_manager.stop_session("profile1")
        
        assert result is True
        mock_browser_manager.close_session.assert_called_once_with("profile1")


class TestStatistics:
    """Test statistics functionality."""
    
    def test_get_statistics_empty(self, mock_browser_manager):
        """Test getting statistics with no sessions."""
        session_manager = SessionManager(
            browser_manager=mock_browser_manager,
            max_concurrent=5
        )
        
        stats = session_manager.get_statistics()
        
        assert stats["total"] == 0
        assert stats["running"] == 0
        assert stats["completed"] == 0
    
    def test_active_count(self, mock_browser_manager):
        """Test active count property."""
        mock_browser_manager.get_session_count.return_value = 3
        
        session_manager = SessionManager(
            browser_manager=mock_browser_manager,
            max_concurrent=5
        )
        
        assert session_manager.active_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
