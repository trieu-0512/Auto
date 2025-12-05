# Multi-Profile Fingerprint Automation
# Session Manager for concurrent profile execution

import time
import threading
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from app.core.browser_manager import BrowserManager


class SessionStatus(Enum):
    """Session status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class SessionResult:
    """Result of a session execution."""
    profile_id: str
    status: SessionStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get session duration in seconds."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class SessionManager:
    """
    Manager for concurrent profile session execution.
    """
    
    def __init__(
        self,
        browser_manager: BrowserManager,
        max_concurrent: int = 5,
        default_delay: float = 1.0
    ):
        """
        Initialize SessionManager.
        
        Args:
            browser_manager: BrowserManager instance
            max_concurrent: Maximum concurrent sessions
            default_delay: Default delay between launches (seconds)
        """
        self.browser_manager = browser_manager
        self.max_concurrent = max_concurrent
        self.default_delay = default_delay
        
        self._results: Dict[str, SessionResult] = {}
        self._stop_requested = False
        self._batch_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    @property
    def active_count(self) -> int:
        """Get number of active sessions."""
        return self.browser_manager.get_session_count()
    
    @property
    def is_batch_running(self) -> bool:
        """Check if batch execution is running."""
        return self._batch_thread is not None and self._batch_thread.is_alive()
    
    def can_start_session(self) -> bool:
        """Check if a new session can be started."""
        return self.active_count < self.max_concurrent
    
    def start_batch(
        self,
        profile_ids: List[str],
        delay: float = None,
        on_session_complete: Callable[[SessionResult], None] = None
    ) -> bool:
        """
        Start batch execution of profiles.
        
        Args:
            profile_ids: List of profile IDs to execute
            delay: Delay between launches (uses default if None)
            on_session_complete: Callback when a session completes
            
        Returns:
            True if batch started successfully
        """
        if self.is_batch_running:
            print("Batch execution already running")
            return False
        
        self._stop_requested = False
        self._results.clear()
        
        delay = delay if delay is not None else self.default_delay
        
        # Start batch in background thread
        self._batch_thread = threading.Thread(
            target=self._run_batch,
            args=(profile_ids, delay, on_session_complete),
            daemon=True
        )
        self._batch_thread.start()
        
        return True
    
    def _run_batch(
        self,
        profile_ids: List[str],
        delay: float,
        on_complete: Callable[[SessionResult], None] = None
    ):
        """Run batch execution (internal)."""
        for profile_id in profile_ids:
            if self._stop_requested:
                break
            
            # Wait for available slot
            while not self.can_start_session() and not self._stop_requested:
                time.sleep(0.5)
            
            if self._stop_requested:
                break
            
            # Start session
            result = self._start_session(profile_id)
            
            with self._lock:
                self._results[profile_id] = result
            
            if on_complete:
                on_complete(result)
            
            # Delay before next launch
            if delay > 0:
                time.sleep(delay)
    
    def _start_session(self, profile_id: str) -> SessionResult:
        """Start a single session."""
        result = SessionResult(
            profile_id=profile_id,
            status=SessionStatus.PENDING,
            start_time=datetime.now()
        )
        
        try:
            # Calculate window position
            position = self.browser_manager.calculate_window_position(self.active_count)
            
            # Launch browser
            driver = self.browser_manager.launch_profile(profile_id, window_position=position)
            
            if driver:
                result.status = SessionStatus.RUNNING
            else:
                result.status = SessionStatus.FAILED
                result.error = "Failed to launch browser"
                result.end_time = datetime.now()
                
        except Exception as e:
            result.status = SessionStatus.FAILED
            result.error = str(e)
            result.end_time = datetime.now()
        
        return result
    
    def stop_batch(self) -> int:
        """
        Stop batch execution and close all sessions.
        
        Returns:
            Number of sessions stopped
        """
        self._stop_requested = True
        
        # Wait for batch thread to finish
        if self._batch_thread and self._batch_thread.is_alive():
            self._batch_thread.join(timeout=5.0)
        
        # Close all active sessions
        count = self.browser_manager.close_all_sessions()
        
        # Update results
        with self._lock:
            for profile_id, result in self._results.items():
                if result.status == SessionStatus.RUNNING:
                    result.status = SessionStatus.STOPPED
                    result.end_time = datetime.now()
        
        return count
    
    def stop_session(self, profile_id: str) -> bool:
        """
        Stop a specific session.
        
        Args:
            profile_id: Profile ID to stop
            
        Returns:
            True if session was stopped
        """
        success = self.browser_manager.close_session(profile_id)
        
        if success:
            with self._lock:
                if profile_id in self._results:
                    self._results[profile_id].status = SessionStatus.STOPPED
                    self._results[profile_id].end_time = datetime.now()
        
        return success
    
    def mark_session_complete(self, profile_id: str, success: bool = True, error: str = None):
        """
        Mark a session as complete.
        
        Args:
            profile_id: Profile ID
            success: Whether session completed successfully
            error: Error message if failed
        """
        with self._lock:
            if profile_id in self._results:
                result = self._results[profile_id]
                result.status = SessionStatus.COMPLETED if success else SessionStatus.FAILED
                result.end_time = datetime.now()
                result.error = error
    
    def get_session_status(self, profile_id: str) -> Optional[SessionStatus]:
        """
        Get status of a specific session.
        
        Args:
            profile_id: Profile ID
            
        Returns:
            SessionStatus or None
        """
        with self._lock:
            if profile_id in self._results:
                return self._results[profile_id].status
        
        if self.browser_manager.is_session_active(profile_id):
            return SessionStatus.RUNNING
        
        return None
    
    def get_all_results(self) -> Dict[str, SessionResult]:
        """Get all session results."""
        with self._lock:
            return self._results.copy()
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get execution statistics.
        
        Returns:
            Dictionary with counts by status
        """
        stats = {
            "total": 0,
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "stopped": 0
        }
        
        with self._lock:
            for result in self._results.values():
                stats["total"] += 1
                stats[result.status.value] += 1
        
        return stats
