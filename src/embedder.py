"""
Embedding Module

This module handles the generation of vector embeddings for text using the Ollama API.
It supports batch embedding and single text embedding, with integrated logging and progress tracking.
"""

from typing import List
from ollama import Client
from src.config import EMBEDDING_MODEL, OLLAMA_HOST
from src.logger import get_logger, progress_tracker

logger = get_logger("embedder")

# Create a single client for reuse
try:
    ollama_client = Client(host=OLLAMA_HOST)
    logger.info(f"✓ Ollama client initialized with host: {OLLAMA_HOST}")
except Exception as e:
    logger.error(f"✗ Failed to initialize Ollama client: {e}")
    raise

def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using the configured Ollama model.
    
    Args:
        texts (List[str]): A list of text strings to embed.
        
    Returns:
        List[List[float]]: A list of vector embeddings (lists of floats).
        
    Raises:
        Exception: If the embedding process fails.
    """
    try:
        logger.debug(f"Embedding {len(texts)} text(s) using model: {EMBEDDING_MODEL}")
        progress_tracker.start_stage("embed_texts", f"Embedding {len(texts)} texts")
        
        resp = ollama_client.embed(
            model=EMBEDDING_MODEL,
            input=texts,                 # must be a list
            truncate=True,
            keep_alive="30m"
        )
        
        embeddings = resp["embeddings"]
        progress_tracker.complete_stage("embed_texts", f"Generated {len(embeddings)} embeddings")
        logger.info(f"✓ Successfully embedded {len(texts)} texts")
        
        return embeddings
    except Exception as e:
        progress_tracker.fail_stage("embed_texts", str(e))
        logger.error(f"✗ Embedding failed: {e}")
        raise

def embed_text(text: str) -> List[float]:
    """
    Generate an embedding for a single text string.
    
    Args:
        text (str): The text to embed.
        
    Returns:
        List[float]: The vector embedding.
    """
    try:
        embeddings = embed_texts([text])
        return embeddings[0]
    except Exception as e:
        logger.error(f"✗ Single text embedding failed: {e}")
        raise
