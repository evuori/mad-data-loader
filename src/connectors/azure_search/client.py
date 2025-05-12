"""
Azure Search client for indexing documents.
"""

import json
import logging
from typing import Dict, List, Any, Optional

import requests
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchAlgorithmKind,
    VectorSearchAlgorithmMetric,
    SemanticSearch,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField
)


class AzureSearchClient:
    """Client for interacting with Azure Cognitive Search."""
    
    def __init__(
        self, 
        endpoint: str, 
        index_name: str, 
        api_key: str, 
        api_version: str = "2023-11-01", 
        dry_run: bool = False,
        semantic_config_name: Optional[str] = None
    ):
        """
        Initialize the Azure Search client.
        
        Args:
            endpoint: Azure Search service endpoint
            index_name: Name of the search index
            api_key: API key for the search service
            api_version: API version to use
            dry_run: If True, don't actually send data to Azure Search
            semantic_config_name: Name of the semantic configuration to use/create
        """
        # Fix the endpoint URL to ensure it ends with .net
        if "windows.ne" in endpoint and not endpoint.endswith(".net"):
            self.endpoint = endpoint.replace("windows.ne", "windows.net").rstrip('/')
        else:
            self.endpoint = endpoint.rstrip('/')
            
        self.index_name = index_name
        self.api_key = api_key
        self.api_version = api_version
        self.dry_run = dry_run
        self.semantic_config_name = semantic_config_name
        self.logger = logging.getLogger(__name__)
        
        # Initialize Azure Search clients
        self.credential = AzureKeyCredential(api_key)
        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=self.credential
        )
        self.index_client = SearchIndexClient(
            endpoint=self.endpoint,
            credential=self.credential
        )
        
        # Headers for REST API requests
        self.headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
    
    def create_index_if_not_exists(self):
        """Create the search index if it doesn't already exist."""
        if self.dry_run:
            self.logger.info(f"DRY RUN: Would create index {self.index_name}")
            return
            
        try:
            # Check if index exists
            existing_index = self.index_client.get_index(self.index_name)
            self.logger.info(f"Index {self.index_name} already exists")
            return
        except Exception as e:
            self.logger.info(f"Index {self.index_name} does not exist, creating...")
        
        # Create the index with our schema
        fields = [
            SimpleField(name="id", type="Edm.String", key=True, filterable=True),
            SearchableField(name="content", type="Edm.String", analyzer="standard.lucene"),
            SimpleField(name="source_page_id", type="Edm.String", filterable=True, facetable=True),
            SearchableField(name="source_page_title", type="Edm.String", filterable=True),
            SimpleField(name="source_url", type="Edm.String", filterable=True),
            SimpleField(name="is_section", type="Edm.Boolean", filterable=True, facetable=True),
            SimpleField(name="section_id", type="Edm.String", filterable=True),
            SearchableField(name="section_title", type="Edm.String", filterable=True),
            SimpleField(name="section_level", type="Edm.Int32", filterable=True, facetable=True),
            SimpleField(name="section_number", type="Edm.String", filterable=True),
            SimpleField(name="document_type", type="Edm.String", filterable=True, facetable=True),
            SimpleField(name="project_code", type="Edm.String", filterable=True, facetable=True),
            SimpleField(name="document_id", type="Edm.String", filterable=True),
            SimpleField(name="document_version", type="Edm.String", filterable=True),
            SimpleField(name="document_status", type="Edm.String", filterable=True, facetable=True),
            SimpleField(name="created_date", type="Edm.String", filterable=True),
            SimpleField(name="last_updated_date", type="Edm.String", filterable=True),
            SimpleField(name="document_owner", type="Edm.String", filterable=True),
            SearchableField(name="summary", type="Edm.String"),
            SimpleField(name="requirement_ids", type="Collection(Edm.String)", filterable=True, facetable=True),
            SearchableField(
                name="vector",
                type="Collection(Edm.Single)",
                vector_search_dimensions=3072,
                vector_search_configuration="default"
            )
        ]

        # Configure vector search
        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="default",
                    kind=VectorSearchAlgorithmKind.HNSW,
                    parameters={
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500,
                        "metric": VectorSearchAlgorithmMetric.COSINE
                    }
                )
            ]
        )

        # Configure semantic search if a name is provided
        semantic_search_settings = None
        if self.semantic_config_name:
            semantic_config = SemanticConfiguration(
                name=self.semantic_config_name,
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="source_page_title"),
                    content_fields=[SemanticField(field_name="content")],
                    keywords_fields=[
                        SemanticField(field_name="project_code"),
                        SemanticField(field_name="document_id")
                    ]
                )
            )
            semantic_search_settings = SemanticSearch(
                configurations=[semantic_config]
            )

        # Create the index
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search,
            semantic_search=semantic_search_settings
        )

        try:
            self.index_client.create_index(index)
            self.logger.info(f"Successfully created index {self.index_name}")
        except Exception as e:
            self.logger.error(f"Error creating index: {str(e)}")
            raise
    
    def index_documents(self, documents: List[Dict[str, Any]], action: str = "mergeOrUpload") -> Dict[str, Any]:
        """
        Index a batch of documents.
        
        Args:
            documents: List of documents to index
            action: The indexing action to use:
                    - "upload": Creates new documents or replaces existing ones
                    - "merge": Updates specified fields in existing documents
                    - "mergeOrUpload": Updates if exists, creates if not (default)
                    - "delete": Removes documents
            
        Returns:
            Response from the indexing operation
        """
        if self.dry_run:
            self.logger.info(f"DRY RUN: Would index {len(documents)} documents with action '{action}'")
            self.logger.debug(f"Documents: {json.dumps(documents, indent=2)}")
            return {"status": "dry_run", "count": len(documents), "action": action}
        
        # Try to create the index if it doesn't exist
        try:
            self.create_index_if_not_exists()
        except Exception as e:
            self.logger.warning(f"Failed to create index: {str(e)}")
            
        url = f"{self.endpoint}/indexes/{self.index_name}/docs/index"
        params = {"api-version": self.api_version}
        
        # Add the search action to each document
        actions = []
        for doc in documents:
            action_doc = doc.copy()
            action_doc["@search.action"] = action
            actions.append(action_doc)
        
        payload = {"value": actions}
        
        self.logger.info(f"Indexing {len(documents)} documents with action '{action}'")
        self.logger.debug(f"Index request: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, headers=self.headers, params=params, json=payload)
        
        if response.status_code not in (200, 201, 207):
            self.logger.error(f"Failed to index documents: {response.status_code} {response.text}")
            response.raise_for_status()
            
        result = response.json()
        self.logger.debug(f"Index response: {json.dumps(result, indent=2)}")
        
        # Check for specific document errors
        if "value" in result:
            errors = [doc for doc in result["value"] if doc.get("status") >= 300]
            if errors:
                self.logger.warning(f"Some documents failed to index: {errors}")
                
        return result
    
    def delete_documents(self, keys: List[str], key_field_name: str = "id") -> Dict[str, Any]:
        """
        Delete documents by their keys.
        
        Args:
            keys: List of document keys to delete
            key_field_name: Name of the key field
            
        Returns:
            Response from the delete operation
        """
        if self.dry_run:
            self.logger.info(f"DRY RUN: Would delete {len(keys)} documents")
            return {"status": "dry_run", "count": len(keys)}
            
        url = f"{self.endpoint}/indexes/{self.index_name}/docs/index"
        params = {"api-version": self.api_version}
        
        # Create delete actions
        actions = [
            {
                "@search.action": "delete",
                key_field_name: key
            }
            for key in keys
        ]
        
        payload = {"value": actions}
        
        self.logger.info(f"Deleting {len(keys)} documents")
        
        response = requests.post(url, headers=self.headers, params=params, json=payload)
        
        if response.status_code not in (200, 201, 207):
            self.logger.error(f"Failed to delete documents: {response.status_code} {response.text}")
            response.raise_for_status()
            
        return response.json()
    
    def search(
        self, 
        query: str, 
        semantic_config_name: Optional[str] = None,
        filter_expr: Optional[str] = None,
        top: int = 10
    ) -> Dict[str, Any]:
        """
        Perform a search query.
        
        Args:
            query: Search query text
            semantic_config_name: Name of the semantic configuration to use
            filter_expr: OData filter expression
            top: Maximum number of results to return
            
        Returns:
            Search results
        """
        url = f"{self.endpoint}/indexes/{self.index_name}/docs/search"
        params = {"api-version": self.api_version}
        
        payload = {
            "search": query,
            "top": top,
            "queryType": "simple"
        }
        
        # Add optional parameters
        if filter_expr:
            payload["filter"] = filter_expr
            
        # Enable semantic search if config name is provided
        if semantic_config_name:
            payload["queryType"] = "semantic"
            payload["semanticConfiguration"] = semantic_config_name
            payload["captions"] = "extractive"
            payload["answers"] = "extractive"
            
        self.logger.info(f"Searching for: {query}")
        self.logger.debug(f"Search request: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, headers=self.headers, params=params, json=payload)
        
        if response.status_code != 200:
            self.logger.error(f"Search failed: {response.status_code} {response.text}")
            response.raise_for_status()
            
        result = response.json()
        self.logger.debug(f"Search response: {json.dumps(result, indent=2)}")
        
        return result
    
    def vector_search(
        self, 
        vector: List[float],
        filter_expr: Optional[str] = None, 
        top: int = 10,
        vector_field: str = "vector",
        hybrid_query: Optional[str] = None,
        semantic_config_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform a vector search query.
        
        Args:
            vector: Vector to search with
            filter_expr: OData filter expression
            top: Maximum number of results to return
            vector_field: Name of the vector field to search
            hybrid_query: Optional text query for hybrid search
            semantic_config_name: Name of the semantic configuration to use for hybrid search
            
        Returns:
            Search results
        """
        url = f"{self.endpoint}/indexes/{self.index_name}/docs/search"
        params = {"api-version": self.api_version}
        
        # Base payload with vector search
        payload = {
            "top": top,
            "vectorQueries": [
                {
                    "vector": vector,
                    "fields": vector_field,
                    "k": top
                }
            ]
        }
        
        # Add text search for hybrid search
        if hybrid_query:
            payload["search"] = hybrid_query
            # Add the semantic configuration for hybrid search
            if semantic_config_name:
                payload["queryType"] = "semantic"
                payload["semanticConfiguration"] = semantic_config_name
                payload["captions"] = "extractive"
                payload["answers"] = "extractive"
        
        # Add optional filter
        if filter_expr:
            payload["filter"] = filter_expr
            
        self.logger.info(f"Performing vector search (hybrid: {bool(hybrid_query)})")
        self.logger.debug(f"Search request: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, headers=self.headers, params=params, json=payload)
        
        if response.status_code != 200:
            self.logger.error(f"Vector search failed: {response.status_code} {response.text}")
            response.raise_for_status()
            
        result = response.json()
        self.logger.debug(f"Search response: {json.dumps(result, indent=2)}")
        
        return result
    
    def hybrid_search(
        self,
        query: str,
        vector: List[float],
        semantic_config_name: Optional[str] = None,
        filter_expr: Optional[str] = None,
        top: int = 10,
        vector_field: str = "vector"
    ) -> Dict[str, Any]:
        """
        Perform a hybrid search (text + vector).
        
        Args:
            query: Text query
            vector: Vector representation of the query
            semantic_config_name: Name of the semantic configuration to use
            filter_expr: OData filter expression
            top: Maximum number of results to return
            vector_field: Name of the vector field to search
            
        Returns:
            Search results
        """
        return self.vector_search(
            vector=vector,
            filter_expr=filter_expr,
            top=top,
            vector_field=vector_field,
            hybrid_query=query,
            semantic_config_name=semantic_config_name
        ) 