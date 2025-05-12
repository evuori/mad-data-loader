"""
AI Service for document summarization.
"""

import logging
import os
from typing import Optional

import requests


def get_summary(content: str, max_tokens: int = 500) -> str:
    """
    Generate a summary of the document content using Azure OpenAI.
    
    Args:
        content: Document content to summarize
        max_tokens: Maximum tokens for the summary
        
    Returns:
        Generated summary text
    """
    logger = logging.getLogger(__name__)
    
    # Check if summarization is enabled
    if not os.getenv("ENABLE_SUMMARIZATION", "false").lower() == "true":
        logger.info("Summarization is disabled. Returning empty summary.")
        return ""
    
    # Get configuration
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    
    if not api_key or not endpoint or not deployment_name:
        logger.warning("Azure OpenAI configuration is incomplete. Returning empty summary.")
        return ""
    
    # Prepare the prompt
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that summarizes documents concisely, focusing on key points, main requirements, and important details."
        },
        {
            "role": "user",
            "content": f"Please summarize the following document content:\n\n{content[:8000]}"  # Limit content to avoid token limitations
        }
    ]
    
    try:
        # Prepare request
        url = f"{endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version={api_version}"
        
        headers = {
            "Content-Type": "application/json",
            "api-key": api_key
        }
        
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.3,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
        
        # Send request
        logger.debug("Sending summarization request")
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            logger.error(f"Summarization failed: {response.status_code} {response.text}")
            return ""
            
        # Process response
        result = response.json()
        summary = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        
        logger.info(f"Generated summary of {len(summary)} characters")
        return summary
        
    except Exception as e:
        logger.exception(f"Error generating summary: {str(e)}")
        return "" 