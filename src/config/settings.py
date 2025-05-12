"""
Configuration settings for the data ingestion app.
Loads settings from environment variables and config files.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv


@dataclass
class ConfluenceConfig:
    """Confluence API configuration."""
    base_url: str
    username: str
    api_token: str


@dataclass
class AzureSearchConfig:
    """Azure Search configuration."""
    endpoint: str
    index_name: str
    api_key: str
    semantic_config_name: Optional[str] = None
    vector_search_enabled: bool = False


@dataclass
class AIConfig:
    """AI service configuration for summarization and embeddings."""
    api_key: str
    endpoint: str
    deployment_name: str
    embedding_deployment_name: str
    api_version: str = "2023-05-15"
    max_tokens: int = 500


@dataclass
class ProcessingConfig:
    """Processing configuration options."""
    enable_summarization: bool = False
    enable_vectorization: bool = False
    cache_dir: str = ".cache"


@dataclass
class AppConfig:
    """Main application configuration."""
    confluence: ConfluenceConfig
    azure_search: AzureSearchConfig
    ai: Optional[AIConfig] = None
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)


def load_config() -> AppConfig:
    """
    Load configuration from environment variables.
    Environment variables are loaded from .env file if present.
    """
    # Load .env file if it exists
    load_dotenv()
    
    # Confluence settings
    confluence_config = ConfluenceConfig(
        base_url=os.getenv("CONFLUENCE_BASE_URL"),
        username=os.getenv("CONFLUENCE_USERNAME"),
        api_token=os.getenv("CONFLUENCE_API_TOKEN"),
    )
    
    # Azure Search settings
    azure_search_config = AzureSearchConfig(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        api_key=os.getenv("AZURE_SEARCH_API_KEY"),
        semantic_config_name=os.getenv("AZURE_SEARCH_SEMANTIC_CONFIG_NAME"),
        vector_search_enabled=os.getenv("AZURE_SEARCH_VECTOR_SEARCH_ENABLED", "false").lower() == "true",
    )
    
    # Process configuration
    enable_summarization = os.getenv("ENABLE_SUMMARIZATION", "false").lower() == "true"
    enable_vectorization = azure_search_config.vector_search_enabled
    
    # AI Service settings (Optional)
    ai_config = None
    if enable_summarization or enable_vectorization:
        ai_config = AIConfig(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            embedding_deployment_name=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15"),
            max_tokens=int(os.getenv("AZURE_OPENAI_MAX_TOKENS", "500")),
        )
    
    # Processing configuration
    processing_config = ProcessingConfig(
        enable_summarization=enable_summarization,
        enable_vectorization=enable_vectorization,
        cache_dir=os.getenv("CACHE_DIRECTORY", ".cache"),
    )
    
    return AppConfig(
        confluence=confluence_config,
        azure_search=azure_search_config,
        ai=ai_config,
        processing=processing_config,
    ) 