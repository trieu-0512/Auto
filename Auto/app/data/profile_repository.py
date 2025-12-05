# Multi-Profile Fingerprint Automation
# Profile Repository for Database Access
# 
# Architecture:
# - data/data.db: Original database, READ-ONLY (profiles from danhsachacc table)
# - data/app_data.db: App database for writing (sessions, logs, new profiles, etc.)

import sqlite3
import os
from typing import List, Optional, Tuple
from contextlib import contextmanager

from app.data.profile_models import ProfileData, Profile, GologinConfig


class ProfileRepository:
    """
    Repository for managing profile data.
    
    Uses two databases:
    - main_db_path: Original database (READ-ONLY) - data/data.db
    - app_db_path: App database (READ-WRITE) - data/app_data.db
    """
    
    # Database table columns
    COLUMNS = [
        'id', 'name', 'idprofile', 'proxymode', 'proxy', 'status',
        'username_fb', 'password_fb', 'ma2fa', 'list_uid', 'list_group',
        'control_fb', 'username_gmail', 'password_gmail', 'gmail_khoiphuc',
        'sothutu', 'notes', 'cookies', 'group_profile', 'last_run'
    ]
    
    def __init__(
        self,
        db_path: str = "data/data.db",
        app_db_path: str = "data/app_data.db",
        profile_dir: str = "profile"
    ):
        """
        Initialize repository with database paths and profile directory.
        
        Args:
            db_path: Path to main SQLite database (READ-ONLY)
            app_db_path: Path to app SQLite database (READ-WRITE)
            profile_dir: Path to profile directories
        """
        self.db_path = db_path  # READ-ONLY
        self.app_db_path = app_db_path  # READ-WRITE
        self.profile_dir = profile_dir
        
        # Initialize app database
        self._init_app_database()
        
        # Sync profiles from main database to app database
        self._sync_from_main_db()
    
    def _init_app_database(self):
        """Initialize app database with required tables."""
        os.makedirs(os.path.dirname(self.app_db_path), exist_ok=True)
        
        with self._get_app_connection() as conn:
            cursor = conn.cursor()
            
            # Table for new profiles created by app
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_profiles (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    idprofile TEXT UNIQUE,
                    proxymode TEXT DEFAULT 'none',
                    proxy TEXT DEFAULT '',
                    status TEXT DEFAULT 'inactive',
                    username_fb TEXT DEFAULT '',
                    password_fb TEXT DEFAULT '',
                    ma2fa TEXT DEFAULT '',
                    list_uid TEXT DEFAULT '',
                    list_group TEXT DEFAULT '',
                    control_fb TEXT DEFAULT '',
                    username_gmail TEXT DEFAULT '',
                    password_gmail TEXT DEFAULT '',
                    gmail_khoiphuc TEXT DEFAULT '',
                    sothutu INTEGER DEFAULT 0,
                    notes TEXT DEFAULT '',
                    cookies TEXT DEFAULT '',
                    group_profile TEXT DEFAULT '',
                    last_run TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table for profile status tracking (overrides main db status)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profile_status (
                    idprofile TEXT PRIMARY KEY,
                    status TEXT,
                    last_run TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table for session logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_logs (
                    id INTEGER PRIMARY KEY,
                    idprofile TEXT,
                    action TEXT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def _sync_from_main_db(self):
        """
        Sync profiles from main database to app database.
        Only imports profiles that don't exist in app database yet.
        This ensures new profiles added by other apps are imported.
        """
        if not os.path.exists(self.db_path):
            return
        
        try:
            # Get existing profile IDs in app database
            existing_ids = set()
            with self._get_app_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT idprofile FROM app_profiles")
                existing_ids = {row['idprofile'] for row in cursor.fetchall()}
            
            # Get profiles from main database
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM danhsachacc")
                rows = cursor.fetchall()
                
                # Import new profiles to app database
                new_profiles = []
                for row in rows:
                    profile = ProfileData.from_db_row(tuple(row), list(row.keys()))
                    if profile.idprofile and profile.idprofile not in existing_ids:
                        new_profiles.append(profile)
            
            # Insert new profiles into app database
            if new_profiles:
                with self._get_app_connection() as conn:
                    cursor = conn.cursor()
                    for profile in new_profiles:
                        cursor.execute("""
                            INSERT OR IGNORE INTO app_profiles (
                                name, idprofile, proxymode, proxy, status,
                                username_fb, password_fb, ma2fa, list_uid, list_group,
                                control_fb, username_gmail, password_gmail, gmail_khoiphuc,
                                sothutu, notes, cookies, group_profile, last_run
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            profile.name, profile.idprofile, profile.proxymode, profile.proxy,
                            profile.status, profile.username_fb, profile.password_fb,
                            profile.ma2fa, profile.list_uid, profile.list_group,
                            profile.control_fb, profile.username_gmail, profile.password_gmail,
                            profile.gmail_khoiphuc, profile.sothutu, profile.notes,
                            profile.cookies, profile.group_profile, profile.last_run
                        ))
                    conn.commit()
                    print(f"Synced {len(new_profiles)} new profiles from main database")
        except sqlite3.Error as e:
            print(f"Error syncing from main database: {e}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for READ-ONLY main database connections."""
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    @contextmanager
    def _get_app_connection(self):
        """Context manager for READ-WRITE app database connections."""
        conn = sqlite3.connect(self.app_db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def get_all_profiles(self) -> List[ProfileData]:
        """
        Query all profiles from app database.
        Profiles are synced from main db on startup, so app_profiles contains all data.
        Merges status from profile_status table.
        
        Returns:
            List of ProfileData objects
        """
        profiles = []
        
        # Get profiles from app database (contains synced + new profiles)
        with self._get_app_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM app_profiles ORDER BY sothutu, id")
            rows = cursor.fetchall()
            
            for row in rows:
                profile = ProfileData.from_db_row(tuple(row), list(row.keys()))
                profile = self._merge_app_status(profile)
                profiles.append(profile)
        
        return profiles
    
    def get_profile_by_id(self, profile_id: str) -> Optional[ProfileData]:
        """
        Get single profile by idprofile from app database.
        Profiles are synced from main db on startup.
        
        Args:
            profile_id: The profile ID (idprofile field)
            
        Returns:
            ProfileData if found, None otherwise
        """
        with self._get_app_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM app_profiles WHERE idprofile = ?",
                (profile_id,)
            )
            row = cursor.fetchone()
            
            if row:
                profile = ProfileData.from_db_row(tuple(row), list(row.keys()))
                return self._merge_app_status(profile)
        
        return None
    
    def _merge_app_status(self, profile: ProfileData) -> ProfileData:
        """Merge status and last_run from app database."""
        with self._get_app_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT status, last_run FROM profile_status WHERE idprofile = ?",
                (profile.idprofile,)
            )
            row = cursor.fetchone()
            
            if row:
                if row['status']:
                    profile.status = row['status']
                if row['last_run']:
                    profile.last_run = row['last_run']
        
        return profile
    
    def get_profile_by_db_id(self, db_id: int) -> Optional[ProfileData]:
        """
        Get single profile by database ID from app database.
        
        Args:
            db_id: The database ID (id field)
            
        Returns:
            ProfileData if found, None otherwise
        """
        with self._get_app_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM app_profiles WHERE id = ?",
                (db_id,)
            )
            row = cursor.fetchone()
            
            if row:
                profile = ProfileData.from_db_row(tuple(row), list(row.keys()))
                return self._merge_app_status(profile)
            return None
    
    def create_profile(self, profile: ProfileData) -> bool:
        """
        Insert new profile record into APP database (not main db).
        
        Args:
            profile: ProfileData to insert
            
        Returns:
            True if successful, False otherwise
        """
        with self._get_app_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO app_profiles (
                        name, idprofile, proxymode, proxy, status,
                        username_fb, password_fb, ma2fa, list_uid, list_group,
                        control_fb, username_gmail, password_gmail, gmail_khoiphuc,
                        sothutu, notes, cookies, group_profile, last_run
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    profile.name, profile.idprofile, profile.proxymode, profile.proxy,
                    profile.status, profile.username_fb, profile.password_fb,
                    profile.ma2fa, profile.list_uid, profile.list_group,
                    profile.control_fb, profile.username_gmail, profile.password_gmail,
                    profile.gmail_khoiphuc, profile.sothutu, profile.notes,
                    profile.cookies, profile.group_profile, profile.last_run
                ))
                conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Database error: {e}")
                return False
    
    def update_profile(self, profile: ProfileData) -> bool:
        """
        Update existing profile record in APP database.
        Uses INSERT OR REPLACE to handle both new and existing profiles.
        
        Args:
            profile: ProfileData with updated values
            
        Returns:
            True if successful, False otherwise
        """
        with self._get_app_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO app_profiles (
                        name, idprofile, proxymode, proxy, status,
                        username_fb, password_fb, ma2fa, list_uid, list_group,
                        control_fb, username_gmail, password_gmail, gmail_khoiphuc,
                        sothutu, notes, cookies, group_profile, last_run
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    profile.name, profile.idprofile, profile.proxymode, profile.proxy,
                    profile.status, profile.username_fb, profile.password_fb,
                    profile.ma2fa, profile.list_uid, profile.list_group,
                    profile.control_fb, profile.username_gmail, profile.password_gmail,
                    profile.gmail_khoiphuc, profile.sothutu, profile.notes,
                    profile.cookies, profile.group_profile, profile.last_run
                ))
                conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Database error: {e}")
                return False
    
    def update_profile_status(self, profile_id: str, status: str) -> bool:
        """
        Update only the status field of a profile in APP database.
        Stores status override in profile_status table.
        
        Args:
            profile_id: The profile ID
            status: New status value
            
        Returns:
            True if successful, False otherwise
        """
        with self._get_app_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO profile_status (idprofile, status, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (profile_id, status))
                conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Database error: {e}")
                return False
    
    def update_last_run(self, profile_id: str, last_run: str) -> bool:
        """
        Update the last_run field of a profile in APP database.
        
        Args:
            profile_id: The profile ID
            last_run: Last run timestamp string
            
        Returns:
            True if successful, False otherwise
        """
        with self._get_app_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO profile_status (idprofile, status, last_run, updated_at)
                    VALUES (?, COALESCE((SELECT status FROM profile_status WHERE idprofile = ?), 'inactive'), ?, CURRENT_TIMESTAMP)
                """, (profile_id, profile_id, last_run))
                conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Database error: {e}")
                return False
    
    def delete_profile(self, profile_id: str) -> bool:
        """
        Delete profile from APP database only.
        Does NOT delete from main database (read-only).
        
        Args:
            profile_id: The profile ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        with self._get_app_connection() as conn:
            cursor = conn.cursor()
            try:
                # Delete from app_profiles
                cursor.execute(
                    "DELETE FROM app_profiles WHERE idprofile = ?",
                    (profile_id,)
                )
                # Delete status tracking
                cursor.execute(
                    "DELETE FROM profile_status WHERE idprofile = ?",
                    (profile_id,)
                )
                conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Database error: {e}")
                return False
    
    def get_profile_path(self, profile_id: str) -> str:
        """
        Map profile ID to filesystem path.
        
        Args:
            profile_id: The profile ID
            
        Returns:
            Full path to profile directory
        """
        return os.path.join(self.profile_dir, profile_id)
    
    def profile_exists(self, profile_id: str) -> bool:
        """
        Check if profile directory exists.
        
        Args:
            profile_id: The profile ID
            
        Returns:
            True if directory exists, False otherwise
        """
        path = self.get_profile_path(profile_id)
        return os.path.isdir(path)
    
    def get_profiles_by_status(self, status: str) -> List[ProfileData]:
        """
        Get profiles filtered by status.
        Checks app database status overrides.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of matching ProfileData objects
        """
        # Get all profiles and filter by effective status
        all_profiles = self.get_all_profiles()
        return [p for p in all_profiles if p.status == status]
    
    def get_profiles_by_group(self, group: str) -> List[ProfileData]:
        """
        Get profiles filtered by group from app database.
        
        Args:
            group: Group to filter by
            
        Returns:
            List of matching ProfileData objects
        """
        all_profiles = self.get_all_profiles()
        return [p for p in all_profiles if p.group_profile == group]
    
    def count_profiles(self) -> int:
        """
        Count total number of profiles in app database.
        
        Returns:
            Number of profiles in database
        """
        with self._get_app_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM app_profiles")
            return cursor.fetchone()[0]
    
    def resync_from_main_db(self) -> int:
        """
        Force resync profiles from main database.
        Call this to import new profiles added by other apps.
        
        Returns:
            Number of new profiles imported
        """
        if not os.path.exists(self.db_path):
            return 0
        
        try:
            # Get existing profile IDs in app database
            existing_ids = set()
            with self._get_app_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT idprofile FROM app_profiles")
                existing_ids = {row['idprofile'] for row in cursor.fetchall()}
            
            # Get profiles from main database
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM danhsachacc")
                rows = cursor.fetchall()
                
                new_profiles = []
                for row in rows:
                    profile = ProfileData.from_db_row(tuple(row), list(row.keys()))
                    if profile.idprofile and profile.idprofile not in existing_ids:
                        new_profiles.append(profile)
            
            # Insert new profiles
            if new_profiles:
                with self._get_app_connection() as conn:
                    cursor = conn.cursor()
                    for profile in new_profiles:
                        cursor.execute("""
                            INSERT OR IGNORE INTO app_profiles (
                                name, idprofile, proxymode, proxy, status,
                                username_fb, password_fb, ma2fa, list_uid, list_group,
                                control_fb, username_gmail, password_gmail, gmail_khoiphuc,
                                sothutu, notes, cookies, group_profile, last_run
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            profile.name, profile.idprofile, profile.proxymode, profile.proxy,
                            profile.status, profile.username_fb, profile.password_fb,
                            profile.ma2fa, profile.list_uid, profile.list_group,
                            profile.control_fb, profile.username_gmail, profile.password_gmail,
                            profile.gmail_khoiphuc, profile.sothutu, profile.notes,
                            profile.cookies, profile.group_profile, profile.last_run
                        ))
                    conn.commit()
            
            return len(new_profiles)
        except sqlite3.Error as e:
            print(f"Error resyncing from main database: {e}")
            return 0
