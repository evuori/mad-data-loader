"""
Document processor for Confluence content.
"""

import hashlib
import json
import logging
import os
import re
from typing import Dict, List, Any, Optional, Tuple

from bs4 import BeautifulSoup
import markdown2

from connectors.confluence.client import ConfluenceClient
from connectors.azure_search.client import AzureSearchClient
from models.document import (
    DocumentMetadata, 
    DocumentSection, 
    DocumentType, 
    SearchableDocument
)
from services.ai_service import get_summary
from services.embedding_service import get_embedding
from utils.cache import Cache


class DocumentProcessor:
    """Process Confluence documents and index them in Azure Search."""
    
    def __init__(
        self, 
        confluence_client: ConfluenceClient,
        azure_search_client: AzureSearchClient,
        cache_dir: str = ".cache",
        summarize: bool = False,
        vectorize: bool = False,
        force_reindex: bool = False
    ):
        """
        Initialize the document processor.
        
        Args:
            confluence_client: Client for Confluence API
            azure_search_client: Client for Azure Search
            cache_dir: Directory to store cache files
            summarize: Whether to generate summaries for documents
            vectorize: Whether to generate vector embeddings for documents
            force_reindex: Whether to force reprocessing regardless of cache
        """
        self.confluence_client = confluence_client
        self.azure_search_client = azure_search_client
        self.cache = Cache(cache_dir)
        self.summarize = summarize
        self.vectorize = vectorize
        self.force_reindex = force_reindex
        self.logger = logging.getLogger(__name__)
        
    def process_page(self, page_id: str) -> bool:
        """
        Process a single Confluence page.
        
        Args:
            page_id: ID of the page to process
            
        Returns:
            True if processing was successful, False otherwise
        """
        try:
            # Fetch the page content
            page = self.confluence_client.get_page_by_id(page_id)
            
            # Get current version
            current_version = page.get("version", {}).get("number", 0)
            
            # Check for existing versions in cache
            # Use the page ID as the base key
            base_page_key = f"{page_id}"
            
            cached_data = self.cache.get(base_page_key)
            if cached_data and not self.force_reindex:
                cached_version = float(cached_data.get("version", "0"))
                # Only process if current version is greater than cached version
                if float(current_version) <= cached_version:
                    self.logger.info(
                        f"Page {page_id} version {current_version} is not newer than cached version {cached_version}. Skipping."
                    )
                    return True
                else:
                    self.logger.info(
                        f"Page {page_id} version {current_version} is newer than cached version {cached_version}. Processing."
                    )
            else:
                if self.force_reindex:
                    self.logger.info(f"Force reindexing page {page_id} version {current_version}.")
                else:
                    self.logger.info(f"Page {page_id} not found in cache. Processing version {current_version}.")
                
            # Extract metadata and content
            metadata = self._extract_metadata(page)
            
            # Skip processing if status is not approved (unless it's a draft)
            if metadata.status.upper() not in ("DRAFT", "APPROVED"):
                self.logger.info(
                    f"Skipping page {page_id} with status {metadata.status}"
                )
                return True
            
            # Process content
            html_content = page.get("body", {}).get("storage", {}).get("value", "")
            sections = self._split_content_into_sections(html_content, metadata)
            
            # Convert to markdown
            markdown_content = self._html_to_markdown(html_content)
            
            # Generate summary if enabled
            summary = ""
            if self.summarize:
                summary = get_summary(markdown_content)
            
            # Generate embedding for the full document if enabled
            vector = None
            if self.vectorize:
                vector = get_embedding(markdown_content)
                
            # Create searchable documents - use version in ID to ensure unique entries
            documents = []
            
            # Add full document with version in the ID to maintain history
            full_doc = SearchableDocument(
                id=f"{page_id}_v{current_version}_full",  # Include version in ID
                content=markdown_content,
                source_page_id=page_id,
                source_page_title=page.get("title", ""),
                source_url=self._get_page_url(page),
                is_section=False,
                section_id="",
                section_title="",
                section_level=0,
                section_number="",
                document_type=metadata.document_type,
                project_code=metadata.project_code,
                document_id=metadata.document_id,
                document_version=metadata.document_version,
                document_status=metadata.status,
                created_date=metadata.created_date,
                last_updated_date=metadata.last_updated_date,
                document_owner=metadata.document_owner,
                summary=summary,
                vectorized=bool(vector),
                vector=vector
            )
            documents.append(full_doc.to_dict())
            
            # Add individual sections with version in the ID to maintain history
            for section in sections:
                # Generate embedding for the section if enabled
                section_vector = None
                if self.vectorize:
                    section_vector = get_embedding(section.content)
                    
                section_doc = SearchableDocument(
                    id=f"{page_id}_v{current_version}_{section.section_id}",  # Include version in ID
                    content=section.content,
                    source_page_id=page_id,
                    source_page_title=page.get("title", ""),
                    source_url=self._get_page_url(page),
                    is_section=True,
                    section_id=section.section_id,
                    section_title=section.title,
                    section_level=section.level,
                    section_number=section.section_number,
                    document_type=metadata.document_type,
                    project_code=metadata.project_code,
                    document_id=metadata.document_id,
                    document_version=metadata.document_version,
                    document_status=metadata.status,
                    created_date=metadata.created_date,
                    last_updated_date=metadata.last_updated_date,
                    document_owner=metadata.document_owner,
                    summary="",  # No summary for sections
                    requirement_ids=section.requirement_ids,
                    vectorized=bool(section_vector),
                    vector=section_vector
                )
                documents.append(section_doc.to_dict())
            
            # Index documents in Azure Search - using upload since these are new documents with unique IDs
            result = self.azure_search_client.index_documents(documents, action="upload")
            
            # Update cache with the new version information
            self.cache.set(base_page_key, {
                "version": current_version,
                "metadata": metadata.to_dict(),
                "processed_at": self.cache.current_timestamp(),
                "document_count": len(documents),
                "vectorized": self.vectorize
            })
            
            self.logger.info(
                f"Successfully processed page {page_id} (version {current_version}). "
                f"Indexed {len(documents)} documents."
            )
            
            return True
            
        except Exception as e:
            self.logger.exception(f"Error processing page {page_id}: {str(e)}")
            return False
    
    def process_space(self, space_key: str) -> Tuple[int, int]:
        """
        Process all pages in a Confluence space.
        
        Args:
            space_key: Key of the space to process
            
        Returns:
            Tuple of (success_count, failure_count)
        """
        self.logger.info(f"Processing all pages in space {space_key}")
        
        # Get all pages in the space
        pages = self.confluence_client.get_pages_in_space(space_key)
        
        self.logger.info(f"Found {len(pages)} pages in space {space_key}")
        
        success_count = 0
        failure_count = 0
        
        for page in pages:
            page_id = page.get("id")
            if self.process_page(page_id):
                success_count += 1
            else:
                failure_count += 1
                
        self.logger.info(
            f"Finished processing space {space_key}. "
            f"Success: {success_count}, Failures: {failure_count}"
        )
        
        return success_count, failure_count
    
    def _extract_metadata(self, page: Dict[str, Any]) -> DocumentMetadata:
        """
        Extract metadata from the page.
        
        Args:
            page: Page content and metadata from Confluence
            
        Returns:
            DocumentMetadata object
        """
        html_content = page.get("body", {}).get("storage", {}).get("value", "")
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Find Document Control table
        metadata_table = None
        tables = soup.find_all("table")
        
        for table in tables:
            first_cell = table.find("th") or table.find("td")
            if first_cell and "document" in first_cell.text.lower() and "control" in first_cell.text.lower():
                metadata_table = table
                break
                
        # Alternative approach: look for Document ID in any table
        if not metadata_table:
            for table in tables:
                if table.find(string=re.compile(r"Document ID", re.IGNORECASE)):
                    metadata_table = table
                    break
        
        # Extract metadata from table
        metadata = DocumentMetadata()
        
        if metadata_table:
            rows = metadata_table.find_all("tr")
            for row in rows:
                cells = row.find_all(["th", "td"])
                if len(cells) >= 2:
                    key = cells[0].text.strip()
                    value = cells[1].text.strip()
                    
                    if re.search(r"document\s*id", key, re.IGNORECASE):
                        metadata.document_id = value
                        # Extract document type, project code, and version from ID
                        self._parse_document_id(metadata, value)
                    elif re.search(r"version", key, re.IGNORECASE):
                        metadata.document_version = value
                    elif re.search(r"status", key, re.IGNORECASE):
                        metadata.status = value
                    elif re.search(r"created|date created", key, re.IGNORECASE):
                        metadata.created_date = value
                    elif re.search(r"updated|last updated", key, re.IGNORECASE):
                        metadata.last_updated_date = value
                    elif re.search(r"owner|author", key, re.IGNORECASE):
                        metadata.document_owner = value
        
        # Set defaults if not found
        if not metadata.document_id:
            metadata.document_id = f"DOC-{page.get('id')}"
            
        if not metadata.document_type:
            metadata.document_type = DocumentType.UNKNOWN
            
        if not metadata.document_version:
            metadata.document_version = str(page.get("version", {}).get("number", "1.0"))
            
        if not metadata.status:
            metadata.status = "UNKNOWN"
            
        if not metadata.created_date:
            created = page.get("history", {}).get("createdDate", "")
            if created:
                metadata.created_date = created
                
        if not metadata.last_updated_date:
            last_updated = page.get("version", {}).get("when", "")
            if last_updated:
                metadata.last_updated_date = last_updated
                
        if not metadata.document_owner:
            creator = page.get("history", {}).get("createdBy", {}).get("displayName", "")
            if creator:
                metadata.document_owner = creator
                
        return metadata
    
    def _parse_document_id(self, metadata: DocumentMetadata, document_id: str):
        """
        Parse document ID to extract type, project code, and version.
        
        Args:
            metadata: DocumentMetadata to update
            document_id: Document ID string (e.g., ABRD-HRMS-2025-1.0)
        """
        # Extract document type
        if document_id.startswith("ABRD-"):
            metadata.document_type = DocumentType.ABRD
        elif document_id.startswith("FBRD-"):
            metadata.document_type = DocumentType.FBRD
        else:
            metadata.document_type = DocumentType.UNKNOWN
            
        # Extract project code
        match = re.match(r"(?:ABRD|FBRD)-([A-Z0-9]+)-\d{4}-[\d\.]+", document_id)
        if match:
            metadata.project_code = match.group(1)
    
    def _split_content_into_sections(
        self, 
        html_content: str, 
        metadata: DocumentMetadata
    ) -> List[DocumentSection]:
        """
        Split HTML content into sections based on headings.
        
        Args:
            html_content: HTML content from Confluence
            metadata: Document metadata
            
        Returns:
            List of document sections
        """
        soup = BeautifulSoup(html_content, "html.parser")
        sections = []
        
        # Find all headings (h1 to h6)
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        
        if not headings:
            # No headings found, treat the whole document as one section
            content = self._html_to_markdown(str(soup))
            section = DocumentSection(
                section_id="section_1",
                title="Main Content",
                level=1,
                section_number="",
                content=content
            )
            sections.append(section)
            return sections
            
        # Process each heading and its content
        for i, heading in enumerate(headings):
            # Extract heading properties
            heading_text = heading.text.strip()
            heading_tag = heading.name
            heading_level = int(heading_tag[1])  # h1 -> 1, h2 -> 2, etc.
            
            # Extract section number (if present)
            section_number = ""
            number_match = re.match(r"^(\d+(?:\.\d+)*)\s+(.+)$", heading_text)
            if number_match:
                section_number = number_match.group(1)
                heading_text = number_match.group(2)
                
            # Generate a section ID
            section_id = f"section_{i+1}"
            if section_number:
                section_id = f"section_{section_number.replace('.', '_')}"
            
            # Get content until the next heading or end of document
            content_elements = []
            current = heading.next_sibling
            
            while current and (
                i == len(headings) - 1 or 
                current not in headings[i+1:]
            ):
                if current.name and current.name not in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    content_elements.append(str(current))
                current = current.next_sibling
            
            # Convert content to markdown
            content = self._html_to_markdown("".join(content_elements))
            
            # Check for requirement IDs
            requirement_ids = re.findall(
                r"((?:FR|PR|SR|UR|RR|CR|BR|INT)-[A-Z0-9]+-\d{3})", 
                content
            )
            
            # Create section object
            section = DocumentSection(
                section_id=section_id,
                title=heading_text,
                level=heading_level,
                section_number=section_number,
                content=content,
                requirement_ids=requirement_ids
            )
            
            sections.append(section)
            
        return sections
    
    def _html_to_markdown(self, html_content: str) -> str:
        """
        Convert HTML content to Markdown.
        
        Args:
            html_content: HTML content to convert
            
        Returns:
            Markdown formatted content
        """
        # Use BeautifulSoup to clean up HTML
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Remove unwanted elements
        for element in soup.find_all(["script", "style"]):
            element.decompose()
            
        # Process tables to ensure proper formatting
        for table in soup.find_all("table"):
            # Ensure all tables have thead and tbody
            if not table.find("thead") and table.find("tr"):
                # Move first row to thead
                thead = soup.new_tag("thead")
                thead.append(table.find("tr").extract())
                table.insert(0, thead)
                
                # Wrap remaining rows in tbody if not already
                if not table.find("tbody"):
                    tbody = soup.new_tag("tbody")
                    for tr in table.find_all("tr"):
                        tbody.append(tr.extract())
                    table.append(tbody)
        
        # Convert to markdown
        markdown_content = markdown2.markdown(
            str(soup),
            extras=[
                "tables", "fenced-code-blocks", "header-ids", 
                "strike", "task_list", "target-blank-links"
            ]
        )
        
        return markdown_content
    
    def _get_page_url(self, page: Dict[str, Any]) -> str:
        """
        Get the URL for a Confluence page.
        
        Args:
            page: Page data from Confluence API
            
        Returns:
            URL string
        """
        base_url = self.confluence_client.base_url
        space_key = page.get("space", {}).get("key", "")
        page_id = page.get("id", "")
        
        return f"{base_url}/display/{space_key}/{page_id}" 