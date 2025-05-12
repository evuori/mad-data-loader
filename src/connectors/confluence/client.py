"""
Confluence API client for fetching content from Confluence.
"""

import logging
from typing import Dict, List, Optional, Any

from atlassian import Confluence


class ConfluenceClient:
    """Client for interacting with the Confluence API using the official Atlassian Python API."""
    
    def __init__(self, base_url: str, username: str, api_token: str):
        """
        Initialize the Confluence client.
        
        Args:
            base_url: Base URL of the Confluence instance
            username: Confluence username
            api_token: Confluence API token
        """
        self.base_url = base_url.rstrip('/')
        self.logger = logging.getLogger(__name__)
        self.client = Confluence(
            url=self.base_url,
            username=username,
            password=api_token,
            cloud=True  # Set to True for Atlassian Cloud (atlassian.net)
        )
        
    def get_page_by_id(self, page_id: str) -> Dict[str, Any]:
        """
        Fetch a page by its ID.
        
        Args:
            page_id: The ID of the page to fetch
            
        Returns:
            The page content and metadata
            
        Raises:
            Exception: If the page cannot be fetched
        """
        self.logger.debug(f"Fetching page with ID: {page_id}")
        
        try:
            page = self.client.get_page_by_id(
                page_id=page_id,
                expand="body.storage,version,metadata,history,ancestors"
            )
            return page
        except Exception as e:
            self.logger.error(f"Failed to fetch page {page_id}: {str(e)}")
            raise
    
    def get_pages_in_space(self, space_key: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch all pages in a space.
        
        Args:
            space_key: The key of the space to fetch pages from
            limit: Maximum number of pages to fetch per request
            
        Returns:
            A list of pages in the space
        """
        self.logger.debug(f"Fetching pages in space {space_key}")
        
        try:
            # Get all pages in the space
            return self.client.get_all_pages_from_space(
                space=space_key,
                start=0,
                limit=limit,
                expand="version"
            )
        except Exception as e:
            self.logger.error(f"Failed to fetch pages in space {space_key}: {str(e)}")
            raise
    
    def get_page_history(self, page_id: str) -> Dict[str, Any]:
        """
        Get the history of a page.
        
        Args:
            page_id: The ID of the page
            
        Returns:
            The page history information
        """
        try:
            return self.client.history(page_id, expand="contributors")
        except Exception as e:
            self.logger.error(f"Failed to fetch page history for {page_id}: {str(e)}")
            raise
    
    def get_content_properties(self, page_id: str) -> List[Dict[str, Any]]:
        """
        Get the content properties of a page.
        
        Args:
            page_id: The ID of the page
            
        Returns:
            The content properties of the page
        """
        try:
            return self.client.get_content_properties(page_id)
        except Exception as e:
            self.logger.error(f"Failed to fetch content properties for {page_id}: {str(e)}")
            raise 