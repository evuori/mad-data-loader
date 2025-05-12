#!/usr/bin/env python3
"""
Confluence to Azure Search Data Ingestion App

This application fetches content from Confluence, processes it,
and indexes it in Azure Search.
"""

import argparse
import json
import logging
import sys
from datetime import datetime

from config.settings import load_config
from config.page_config import PageConfig
from core.processor import DocumentProcessor
from connectors.confluence.client import ConfluenceClient
from connectors.azure_search.client import AzureSearchClient
from utils.cache import Cache
from utils.logging_config import setup_logging


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch Confluence content and index it in Azure Search"
    )
    parser.add_argument(
        "--page-id", 
        help="Specific Confluence page ID to process"
    )
    parser.add_argument(
        "--space-key", 
        help="Confluence space key to process all pages from"
    )
    parser.add_argument(
        "--config-file",
        default="config/pages.json",
        help="Path to the page configuration file"
    )
    parser.add_argument(
        "--process-all",
        action="store_true",
        help="Process all pages defined in the configuration file"
    )
    parser.add_argument(
        "--add-page",
        help="Add a page ID to the configuration file"
    )
    parser.add_argument(
        "--page-name",
        help="Name for the page being added to configuration"
    )
    parser.add_argument(
        "--remove-page",
        help="Remove a page ID from the configuration file"
    )
    parser.add_argument(
        "--list-pages",
        action="store_true",
        help="List all pages in the configuration file"
    )
    parser.add_argument(
        "--log-level", 
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Process content but don't send to Azure Search"
    )
    parser.add_argument(
        "--cache-status", 
        action="store_true",
        help="Display cache statistics and exit"
    )
    parser.add_argument(
        "--clear-cache", 
        action="store_true",
        help="Clear the document cache before processing"
    )
    parser.add_argument(
        "--force-reindex",
        action="store_true",
        help="Force reprocessing of pages regardless of cache status"
    )
    
    return parser.parse_args()


def main():
    """Main application entry point."""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(log_level=args.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting Confluence to Azure Search data ingestion - {datetime.now().isoformat()}")
    
    try:
        # Load page configuration
        page_config = PageConfig(config_path=args.config_file)
        
        # Handle page configuration operations
        if args.list_pages:
            print("\nConfigured Pages:")
            for page_id in page_config.get_all_page_ids():
                page_info = page_config.get_page_info(page_id)
                status = "Enabled" if page_config.is_page_enabled(page_id) else "Disabled"
                print(f"  - {page_id}: {page_info.get('name', 'Unnamed')} [{status}]")
                
            print("\nConfigured Spaces:")
            for space_key in page_config.get_all_space_keys():
                space_info = page_config.get_space_info(space_key)
                status = "Enabled" if page_config.is_space_enabled(space_key) else "Disabled"
                print(f"  - {space_key}: {space_info.get('name', 'Unnamed')} [{status}]")
            return 0
            
        if args.add_page:
            page_name = args.page_name or f"Page {args.add_page}"
            if page_config.add_page(args.add_page, name=page_name):
                logger.info(f"Added page {args.add_page} to configuration")
            else:
                logger.error(f"Failed to add page {args.add_page} to configuration")
            return 0
            
        if args.remove_page:
            if page_config.remove_page(args.remove_page):
                logger.info(f"Removed page {args.remove_page} from configuration")
            else:
                logger.error(f"Failed to remove page {args.remove_page} from configuration")
            return 0
            
        # Load application configuration
        config = load_config()
        
        # Initialize cache
        cache = Cache(cache_dir=config.processing.cache_dir)
        
        # Handle cache operations if requested
        if args.cache_status:
            stats = cache.get_stats()
            print("\nCache Statistics:")
            print(f"Total Entries: {stats['total_entries']}")
            print(f"Most Recent Entry: {stats['most_recent_entry']}")
            print(f"Oldest Entry: {stats['oldest_entry']}")
            print(f"Database Path: {stats['database_path']}")
            print("\nCache Keys:")
            for key in cache.get_keys():
                print(f"  - {key}")
            return 0
            
        if args.clear_cache:
            count = cache.clear()
            logger.info(f"Cleared {count} entries from cache")
        
        # Initialize clients
        confluence_client = ConfluenceClient(
            base_url=config.confluence.base_url,
            username=config.confluence.username,
            api_token=config.confluence.api_token,
        )
        
        azure_search_client = AzureSearchClient(
            endpoint=config.azure_search.endpoint,
            index_name=config.azure_search.index_name,
            api_key=config.azure_search.api_key,
            semantic_config_name=config.azure_search.semantic_config_name,
            dry_run=args.dry_run
        )
        
        # Initialize document processor
        processor = DocumentProcessor(
            confluence_client=confluence_client,
            azure_search_client=azure_search_client,
            cache_dir=config.processing.cache_dir,
            summarize=config.processing.enable_summarization,
            vectorize=config.processing.enable_vectorization,
            force_reindex=args.force_reindex
        )
        
        # Process pages based on arguments
        if args.page_id:
            # Process a specific page
            logger.info(f"Processing single page with ID: {args.page_id}")
            processor.process_page(args.page_id)
        elif args.space_key:
            # Process all pages in a space
            logger.info(f"Processing all pages in space: {args.space_key}")
            processor.process_space(args.space_key)
        elif args.process_all:
            # Process all enabled pages from configuration
            enabled_pages = [
                page_id for page_id in page_config.get_all_page_ids()
                if page_config.is_page_enabled(page_id)
            ]
            
            if not enabled_pages:
                logger.warning("No enabled pages found in configuration")
                return 0
                
            logger.info(f"Processing {len(enabled_pages)} pages from configuration")
            
            success_count = 0
            failure_count = 0
            
            for page_id in enabled_pages:
                page_info = page_config.get_page_info(page_id)
                logger.info(f"Processing page {page_id}: {page_info.get('name', 'Unnamed')}")
                
                if processor.process_page(page_id):
                    success_count += 1
                else:
                    failure_count += 1
                    
            logger.info(f"Processing complete. Success: {success_count}, Failures: {failure_count}")
        else:
            if not (args.cache_status or args.clear_cache or args.list_pages):
                logger.error("No operation specified. Please specify a page ID, space key, or --process-all.")
                return 1
            
        logger.info("Processing completed successfully")
        return 0
        
    except Exception as e:
        logger.exception(f"Error during processing: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 