# Multi-Profile Fingerprint Automation
# Backup Manager for profile backup and restore

import os
import json
import shutil
import zipfile
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from app.data.profile_models import ProfileData, Profile
from app.data.profile_repository import ProfileRepository


@dataclass
class BackupInfo:
    """Information about a backup."""
    backup_path: str
    profile_id: str
    profile_name: str
    created_at: datetime
    size_bytes: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'backup_path': self.backup_path,
            'profile_id': self.profile_id,
            'profile_name': self.profile_name,
            'created_at': self.created_at.isoformat(),
            'size_bytes': self.size_bytes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupInfo':
        """Create from dictionary."""
        return cls(
            backup_path=data['backup_path'],
            profile_id=data['profile_id'],
            profile_name=data['profile_name'],
            created_at=datetime.fromisoformat(data['created_at']),
            size_bytes=data['size_bytes']
        )


class BackupManager:
    """
    Manager for profile backup and restore operations.
    """
    
    BACKUP_METADATA_FILE = "backup_metadata.json"
    PROFILE_DATA_FILE = "profile_data.json"
    
    def __init__(
        self,
        repository: ProfileRepository,
        backup_dir: str = "data/backup"
    ):
        """
        Initialize BackupManager.
        
        Args:
            repository: ProfileRepository instance
            backup_dir: Directory to store backups
        """
        self.repository = repository
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
    
    def backup_profile(self, profile_id: str) -> Optional[BackupInfo]:
        """
        Create backup of a single profile.
        
        Args:
            profile_id: Profile ID to backup
            
        Returns:
            BackupInfo or None if failed
        """
        # Get profile data
        profile_data = self.repository.get_profile_by_id(profile_id)
        if not profile_data:
            print(f"Profile {profile_id} not found in database")
            return None
        
        # Get profile path
        profile_path = self.repository.get_profile_path(profile_id)
        if not os.path.isdir(profile_path):
            print(f"Profile directory not found: {profile_path}")
            return None
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{profile_id}_{timestamp}.zip"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            # Create zip archive
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add profile directory contents
                for root, dirs, files in os.walk(profile_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, profile_path)
                        zipf.write(file_path, arcname)
                
                # Add profile data as JSON
                profile_json = json.dumps(profile_data.to_dict(), ensure_ascii=False, indent=2)
                zipf.writestr(self.PROFILE_DATA_FILE, profile_json)
                
                # Add metadata
                metadata = {
                    'profile_id': profile_id,
                    'profile_name': profile_data.name,
                    'created_at': datetime.now().isoformat(),
                    'version': '1.0'
                }
                zipf.writestr(self.BACKUP_METADATA_FILE, json.dumps(metadata, indent=2))
            
            # Get backup size
            size_bytes = os.path.getsize(backup_path)
            
            return BackupInfo(
                backup_path=backup_path,
                profile_id=profile_id,
                profile_name=profile_data.name,
                created_at=datetime.now(),
                size_bytes=size_bytes
            )
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            # Cleanup failed backup
            if os.path.exists(backup_path):
                os.remove(backup_path)
            return None

    def restore_profile(
        self,
        backup_path: str,
        overwrite: bool = False
    ) -> Optional[Profile]:
        """
        Restore profile from backup.
        
        Args:
            backup_path: Path to backup zip file
            overwrite: Whether to overwrite existing profile
            
        Returns:
            Restored Profile or None if failed
        """
        if not os.path.exists(backup_path):
            print(f"Backup file not found: {backup_path}")
            return None
        
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Read metadata
                if self.BACKUP_METADATA_FILE not in zipf.namelist():
                    print("Invalid backup: missing metadata")
                    return None
                
                metadata = json.loads(zipf.read(self.BACKUP_METADATA_FILE))
                profile_id = metadata['profile_id']
                
                # Read profile data
                if self.PROFILE_DATA_FILE not in zipf.namelist():
                    print("Invalid backup: missing profile data")
                    return None
                
                profile_dict = json.loads(zipf.read(self.PROFILE_DATA_FILE))
                profile_data = ProfileData.from_dict(profile_dict)
                
                # Check if profile already exists
                existing = self.repository.get_profile_by_id(profile_id)
                if existing and not overwrite:
                    print(f"Profile {profile_id} already exists. Use overwrite=True to replace.")
                    return None
                
                # Get target path
                profile_path = self.repository.get_profile_path(profile_id)
                
                # Remove existing directory if overwriting
                if os.path.exists(profile_path):
                    shutil.rmtree(profile_path)
                
                # Extract profile directory
                os.makedirs(profile_path, exist_ok=True)
                
                for name in zipf.namelist():
                    # Skip metadata files
                    if name in [self.BACKUP_METADATA_FILE, self.PROFILE_DATA_FILE]:
                        continue
                    
                    # Extract to profile directory
                    target_path = os.path.join(profile_path, name)
                    
                    if name.endswith('/'):
                        os.makedirs(target_path, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with zipf.open(name) as src, open(target_path, 'wb') as dst:
                            dst.write(src.read())
                
                # Update or create database record
                if existing:
                    self.repository.update_profile(profile_data)
                    # Clear status override to use restored status
                    self.repository.update_profile_status(profile_id, profile_data.status)
                else:
                    self.repository.create_profile(profile_data)
                
                return Profile(
                    data=profile_data,
                    fingerprint=None,
                    path=profile_path,
                    exists=True
                )
                
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return None
    
    def backup_multiple(self, profile_ids: List[str]) -> List[BackupInfo]:
        """
        Backup multiple profiles.
        
        Args:
            profile_ids: List of profile IDs to backup
            
        Returns:
            List of successful BackupInfo objects
        """
        results = []
        for profile_id in profile_ids:
            backup_info = self.backup_profile(profile_id)
            if backup_info:
                results.append(backup_info)
        return results
    
    def list_backups(self, profile_id: str = None) -> List[BackupInfo]:
        """
        List available backups.
        
        Args:
            profile_id: Optional filter by profile ID
            
        Returns:
            List of BackupInfo objects
        """
        backups = []
        
        if not os.path.isdir(self.backup_dir):
            return backups
        
        for filename in os.listdir(self.backup_dir):
            if not filename.endswith('.zip'):
                continue
            
            backup_path = os.path.join(self.backup_dir, filename)
            
            try:
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    if self.BACKUP_METADATA_FILE not in zipf.namelist():
                        continue
                    
                    metadata = json.loads(zipf.read(self.BACKUP_METADATA_FILE))
                    
                    # Filter by profile_id if specified
                    if profile_id and metadata['profile_id'] != profile_id:
                        continue
                    
                    backups.append(BackupInfo(
                        backup_path=backup_path,
                        profile_id=metadata['profile_id'],
                        profile_name=metadata['profile_name'],
                        created_at=datetime.fromisoformat(metadata['created_at']),
                        size_bytes=os.path.getsize(backup_path)
                    ))
            except Exception:
                continue
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x.created_at, reverse=True)
        return backups
    
    def delete_backup(self, backup_path: str) -> bool:
        """
        Delete a backup file.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if deleted successfully
        """
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting backup: {e}")
            return False
    
    def validate_backup(self, backup_path: str) -> bool:
        """
        Validate a backup file.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if backup is valid
        """
        if not os.path.exists(backup_path):
            return False
        
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Check required files
                if self.BACKUP_METADATA_FILE not in zipf.namelist():
                    return False
                if self.PROFILE_DATA_FILE not in zipf.namelist():
                    return False
                
                # Validate metadata
                metadata = json.loads(zipf.read(self.BACKUP_METADATA_FILE))
                if 'profile_id' not in metadata:
                    return False
                
                # Validate profile data
                profile_dict = json.loads(zipf.read(self.PROFILE_DATA_FILE))
                if 'idprofile' not in profile_dict:
                    return False
                
                return True
                
        except Exception:
            return False
