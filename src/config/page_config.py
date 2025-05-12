"""
Configuration of Confluence pages to be processed.
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional


class PageConfig:
    """Manages configuration of Confluence pages to be processed."""
    
    def __init__(self, config_path: str = "config/pages.json"):
        """
        Initialize the page configuration.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self.pages = {}
        self.spaces = {}
        self.load_config()
        
    def load_config(self) -> bool:
        """
        Load page configuration from the config file.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        # Check if config file exists
        if not os.path.exists(self.config_path):
            self.logger.warning(f"Page configuration file not found: {self.config_path}")
            return False
            
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                
            # Process pages configuration
            self.pages = config.get("pages", {})
            self.spaces = config.get("spaces", {})
            
            self.logger.info(f"Loaded configuration for {len(self.pages)} pages and {len(self.spaces)} spaces")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading page configuration: {str(e)}")
            return False
    
    def get_all_page_ids(self) -> List[str]:
        """
        Get all configured page IDs.
        
        Returns:
            List of page IDs
        """
        return list(self.pages.keys())
    
    def get_all_space_keys(self) -> List[str]:
        """
        Get all configured space keys.
        
        Returns:
            List of space keys
        """
        return list(self.spaces.keys())
    
    def get_page_info(self, page_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific page.
        
        Args:
            page_id: Page ID to get info for
            
        Returns:
            Page information or None if not found
        """
        return self.pages.get(page_id)
    
    def get_space_info(self, space_key: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific space.
        
        Args:
            space_key: Space key to get info for
            
        Returns:
            Space information or None if not found
        """
        return self.spaces.get(space_key)
    
    def is_page_enabled(self, page_id: str) -> bool:
        """
        Check if a page is enabled for processing.
        
        Args:
            page_id: Page ID to check
            
        Returns:
            True if enabled, False otherwise
        """
        page_info = self.get_page_info(page_id)
        if not page_info:
            return False
            
        return page_info.get("enabled", True)
    
    def is_space_enabled(self, space_key: str) -> bool:
        """
        Check if a space is enabled for processing.
        
        Args:
            space_key: Space key to check
            
        Returns:
            True if enabled, False otherwise
        """
        space_info = self.get_space_info(space_key)
        if not space_info:
            return False
            
        return space_info.get("enabled", True)
        
    def add_page(self, page_id: str, name: str = "", enabled: bool = True) -> bool:
        """
        Add a page to the configuration.
        
        Args:
            page_id: Page ID to add
            name: Optional name/description for the page
            enabled: Whether the page is enabled for processing
            
        Returns:
            True if added successfully, False otherwise
        """
        self.pages[page_id] = {
            "name": name,
            "enabled": enabled
        }
        
        return self.save_config()
    
    def remove_page(self, page_id: str) -> bool:
        """
        Remove a page from the configuration.
        
        Args:
            page_id: Page ID to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        if page_id in self.pages:
            del self.pages[page_id]
            return self.save_config()
            
        return False
    
    def save_config(self) -> bool:
        """
        Save the current configuration to the config file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            config = {
                "pages": self.pages,
                "spaces": self.spaces
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
            self.logger.info(f"Saved configuration to {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving page configuration: {str(e)}")
            return False 