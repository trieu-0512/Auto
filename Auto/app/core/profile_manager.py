# Multi-Profile Fingerprint Automation
# Profile Manager for profile lifecycle management

import os
import shutil
import time
from typing import List, Optional
from datetime import datetime

from app.data.profile_models import ProfileData, Profile, GologinConfig
from app.data.profile_repository import ProfileRepository
from app.core.fingerprint_generator import FingerprintGenerator


class ProfileManager:
    """
    Manager for profile lifecycle operations.
    """
    
    def __init__(
        self,
        repository: ProfileRepository = None,
        generator: FingerprintGenerator = None,
        template_dir: str = "temp"
    ):
        """
        Initialize ProfileManager.
        
        Args:
            repository: ProfileRepository instance
            generator: FingerprintGenerator instance
            template_dir: Path to template profile directory
        """
        self.repository = repository or ProfileRepository()
        self.generator = generator or FingerprintGenerator()
        self.template_dir = template_dir
    
    def load_all_profiles(self) -> List[Profile]:
        """
        Load all profiles from database with status check.
        
        Returns:
            List of Profile objects with existence status
        """
        profiles = []
        profile_data_list = self.repository.get_all_profiles()
        
        for data in profile_data_list:
            profile_path = self.repository.get_profile_path(data.idprofile)
            exists = self.repository.profile_exists(data.idprofile)
            
            # Update status if profile is missing
            if not exists and data.status != "missing":
                self.repository.update_profile_status(data.idprofile, "missing")
                data.status = "missing"
            
            profile = Profile(
                data=data,
                fingerprint=None,  # Lazy load fingerprint
                path=profile_path,
                exists=exists
            )
            profiles.append(profile)
        
        return profiles
    
    def get_profile(self, profile_id: str) -> Optional[Profile]:
        """
        Get a single profile by ID.
        
        Args:
            profile_id: The profile ID
            
        Returns:
            Profile object or None
        """
        data = self.repository.get_profile_by_id(profile_id)
        if not data:
            return None
        
        profile_path = self.repository.get_profile_path(profile_id)
        exists = self.repository.profile_exists(profile_id)
        
        return Profile(
            data=data,
            fingerprint=None,
            path=profile_path,
            exists=exists
        )
    
    def get_profile_fingerprint(self, profile_id: str) -> Optional[GologinConfig]:
        """
        Load fingerprint config from Preferences file.
        
        Args:
            profile_id: The profile ID
            
        Returns:
            GologinConfig or None
        """
        profile_path = self.repository.get_profile_path(profile_id)
        prefs = self.generator.read_preferences(profile_path)
        
        if not prefs:
            return None
        
        return self.generator.extract_gologin_config(prefs)
    
    def create_profile(self, name: str = None) -> Optional[Profile]:
        """
        Create new profile from template with random fingerprint.
        
        Args:
            name: Optional profile name
            
        Returns:
            Created Profile or None if failed
        """
        # Generate unique profile ID
        profile_id = str(int(time.time() * 1000000) + hash(os.urandom(8)) % 10000000000)
        profile_id = profile_id[:20]  # Limit to 20 digits
        
        # Ensure unique
        while self.repository.get_profile_by_id(profile_id):
            profile_id = str(int(time.time() * 1000000) + hash(os.urandom(8)) % 10000000000)
            profile_id = profile_id[:20]
        
        profile_path = self.repository.get_profile_path(profile_id)
        
        # Copy template directory
        if os.path.isdir(self.template_dir):
            try:
                shutil.copytree(self.template_dir, profile_path)
            except Exception as e:
                print(f"Error copying template: {e}")
                return None
        else:
            # Create minimal structure if template doesn't exist
            os.makedirs(os.path.join(profile_path, "Default"), exist_ok=True)
        
        # Generate and apply random fingerprint
        fingerprint = self.generator.generate_fingerprint()
        fingerprint.profile_id = profile_id
        fingerprint.name = name or f"Profile_{profile_id[:8]}"
        
        # Read existing preferences or create new
        prefs = self.generator.read_preferences(profile_path) or {}
        prefs = self.generator.update_gologin_config(prefs, fingerprint)
        
        if not self.generator.write_preferences(profile_path, prefs):
            # Cleanup on failure
            shutil.rmtree(profile_path, ignore_errors=True)
            return None
        
        # Create database record
        profile_data = ProfileData(
            name=name or f"Profile_{profile_id[:8]}",
            idprofile=profile_id,
            status="inactive",
            proxymode="none"
        )
        
        if not self.repository.create_profile(profile_data):
            # Cleanup on failure
            shutil.rmtree(profile_path, ignore_errors=True)
            return None
        
        return Profile(
            data=profile_data,
            fingerprint=fingerprint,
            path=profile_path,
            exists=True
        )
    
    def update_profile_status(self, profile_id: str, status: str) -> bool:
        """
        Update profile status in database.
        
        Args:
            profile_id: The profile ID
            status: New status value
            
        Returns:
            True if successful
        """
        return self.repository.update_profile_status(profile_id, status)
    
    def update_last_run(self, profile_id: str) -> bool:
        """
        Update last run timestamp.
        
        Args:
            profile_id: The profile ID
            
        Returns:
            True if successful
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.repository.update_last_run(profile_id, timestamp)
    
    def delete_profile(self, profile_id: str, delete_files: bool = True) -> bool:
        """
        Delete profile from database and optionally filesystem.
        
        Args:
            profile_id: The profile ID
            delete_files: Whether to delete profile directory
            
        Returns:
            True if successful
        """
        # Delete from database
        if not self.repository.delete_profile(profile_id):
            return False
        
        # Delete files if requested
        if delete_files:
            profile_path = self.repository.get_profile_path(profile_id)
            if os.path.isdir(profile_path):
                shutil.rmtree(profile_path, ignore_errors=True)
        
        return True
    
    def filter_profiles(
        self,
        status: str = None,
        group: str = None
    ) -> List[Profile]:
        """
        Filter profiles by criteria.
        
        Args:
            status: Filter by status
            group: Filter by group
            
        Returns:
            List of matching Profile objects
        """
        if status:
            data_list = self.repository.get_profiles_by_status(status)
        elif group:
            data_list = self.repository.get_profiles_by_group(group)
        else:
            data_list = self.repository.get_all_profiles()
        
        profiles = []
        for data in data_list:
            profile_path = self.repository.get_profile_path(data.idprofile)
            exists = self.repository.profile_exists(data.idprofile)
            
            profile = Profile(
                data=data,
                fingerprint=None,
                path=profile_path,
                exists=exists
            )
            profiles.append(profile)
        
        return profiles
    
    def randomize_profile_fingerprint(self, profile_id: str) -> bool:
        """
        Randomize fingerprint for existing profile.
        
        Args:
            profile_id: The profile ID
            
        Returns:
            True if successful
        """
        profile_path = self.repository.get_profile_path(profile_id)
        
        if not self.repository.profile_exists(profile_id):
            return False
        
        # Read current preferences
        prefs = self.generator.read_preferences(profile_path)
        if not prefs:
            return False
        
        # Get current config and randomize
        config = self.generator.extract_gologin_config(prefs)
        if config:
            config = self.generator.randomize_noise_values(config)
        else:
            config = self.generator.generate_fingerprint()
        
        config.profile_id = profile_id
        
        # Update preferences
        prefs = self.generator.update_gologin_config(prefs, config)
        return self.generator.write_preferences(profile_path, prefs)
    
    def count_profiles(self) -> int:
        """Get total number of profiles."""
        return self.repository.count_profiles()
    
    def get_profile_display_list(self) -> List[dict]:
        """
        Get profiles formatted for display.
        
        Returns:
            List of profile display dictionaries
        """
        profiles = self.load_all_profiles()
        return [p.to_display_dict() for p in profiles]
