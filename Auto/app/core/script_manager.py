# Script Manager for loading and managing automation scripts

import os
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class ScriptConfig:
    """Configuration for an automation script."""
    id: str
    description: str
    file_json: str
    inputs: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.inputs is None:
            self.inputs = []


class ScriptManager:
    """Manager for loading and managing automation scripts."""
    
    def __init__(
        self,
        scripts_index_path: str = "data/json/caulenh.json",
        scripts_dir: str = "data/json/New folder",
        xpath_path: str = "data/xpath.json"
    ):
        self.scripts_index_path = scripts_index_path
        self.scripts_dir = scripts_dir
        self.xpath_path = xpath_path
        self.scripts: List[ScriptConfig] = []
        self.xpaths: Dict[str, Dict[str, str]] = {}
        
        self._load_scripts_index()
        self._load_xpaths()
    
    def _load_scripts_index(self):
        """Load scripts index from caulenh.json."""
        if not os.path.exists(self.scripts_index_path):
            print(f"Scripts index not found: {self.scripts_index_path}")
            return
        
        try:
            with open(self.scripts_index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for item in data:
                script = ScriptConfig(
                    id=item.get('id', ''),
                    description=item.get('description', ''),
                    file_json=item.get('file_json', '')
                )
                self.scripts.append(script)
        except Exception as e:
            print(f"Error loading scripts index: {e}")
    
    def _load_xpaths(self):
        """Load xpath selectors."""
        if not os.path.exists(self.xpath_path):
            print(f"XPath file not found: {self.xpath_path}")
            return
        
        try:
            with open(self.xpath_path, 'r', encoding='utf-8') as f:
                self.xpaths = json.load(f)
        except Exception as e:
            print(f"Error loading xpaths: {e}")

    def get_all_scripts(self) -> List[ScriptConfig]:
        """Get all available scripts."""
        return self.scripts
    
    def get_script_by_id(self, script_id: str) -> Optional[ScriptConfig]:
        """Get script by ID."""
        for script in self.scripts:
            if script.id == script_id:
                return script
        return None
    
    def load_script_inputs(self, script: ScriptConfig) -> List[Dict[str, Any]]:
        """Load input configuration for a script."""
        if not script.file_json or script.file_json == "none.json":
            return []
        
        script_path = os.path.join(self.scripts_dir, script.file_json)
        if not os.path.exists(script_path):
            print(f"Script file not found: {script_path}")
            return []
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('inputs', [])
        except Exception as e:
            print(f"Error loading script inputs: {e}")
            return []
    
    def get_xpath(self, platform: str, key: str) -> Optional[str]:
        """Get xpath/css selector for a platform element."""
        platform_xpaths = self.xpaths.get(platform, {})
        return platform_xpaths.get(key)
    
    def get_platform_xpaths(self, platform: str) -> Dict[str, str]:
        """Get all xpaths for a platform."""
        return self.xpaths.get(platform, {})
    
    def parse_selector(self, selector: str) -> tuple:
        """
        Parse selector string to (type, value).
        
        Args:
            selector: Selector string like "css:.class" or "xpath://div"
            
        Returns:
            Tuple of (selector_type, selector_value)
        """
        if selector.startswith("css:"):
            return ("css", selector[4:])
        elif selector.startswith("xpath:"):
            return ("xpath", selector[6:])
        else:
            # Default to xpath if no prefix
            return ("xpath", selector)
