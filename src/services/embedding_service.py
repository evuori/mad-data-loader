"""
Embedding service for generating vector representations of text.
"""

import logging
import os
from typing import List, Optional

import requests


def get_embedding(text: str) -> Optional[List[float]]:
    """
    Generate an embedding vector for the input text using Azure OpenAI.
    
    Args:
        text: Text to generate embedding for
        
    Returns:
        List of float values representing the embedding vector, or None if failed
    """
    logger = logging.getLogger(__name__)
    
    # Check if vectorization is enabled
    if not os.getenv("AZURE_SEARCH_VECTOR_SEARCH_ENABLED", "false").lower() == "true":
        logger.info("Vector search is disabled. Skipping embedding generation.")
        return None
    
    # Get configuration
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment_name = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    
    if not api_key or not endpoint or not deployment_name:
        logger.warning("Azure OpenAI embedding configuration is incomplete. Skipping vectorization.")
        return None
    
    try:
        # Prepare request
        url = f"{endpoint}/openai/deployments/{deployment_name}/embeddings?api-version={api_version}"
        
        headers = {
            "Content-Type": "application/json",
            "api-key": api_key
        }
        
        # Truncate text if necessary (most models have max token limits)
        truncated_text = text[:8000]
        
        payload = {
            "input": truncated_text,
            "dimensions": 3072  # Using 3072 dimensions for higher quality embeddings
        }
        
        # Send request
        logger.debug("Sending embedding request")
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            logger.error(f"Embedding generation failed: {response.status_code} {response.text}")
            return None
            
        # Process response
        result = response.json()
        embedding = result.get("data", [{}])[0].get("embedding", [])
        
        if not embedding:
            logger.error("Empty embedding returned from API")
            return None
            
        logger.info(f"Generated embedding with {len(embedding)} dimensions")
        return embedding
        
    except Exception as e:
        logger.exception(f"Error generating embedding: {str(e)}")
        return None 