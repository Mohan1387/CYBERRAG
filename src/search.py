"""
Search Backend Module

This module handles the retrieval of documents from the Weaviate vector database.
It includes functionality for:
- Connecting to Weaviate
- Embedding search queries
- Performing vector similarity search
- Filtering and deduplicating results based on chunk frequency
"""

import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Property, DataType, Configure
from src.config import WEAVIATE_HOST, WEAVIATE_API_KEY, WEAVIATE_COLLECTION, TOP_K_DEFAULT
from src.embedder import embed_text
from src.logger import get_logger, progress_tracker
import pandas as pd
import numpy as np

logger = get_logger("search_backend")

def get_client() -> weaviate.WeaviateClient:
    """
    Initialize and return a Weaviate client connection.
    
    Returns:
        weaviate.WeaviateClient: The connected Weaviate client.
        
    Raises:
        Exception: If connection fails.
    """
    try:
        logger.debug(f"Connecting to Weaviate at {WEAVIATE_HOST}:9090")
        client = weaviate.connect_to_custom(
            http_host=WEAVIATE_HOST, http_port=9090, http_secure=False,
            grpc_host=WEAVIATE_HOST, grpc_port=50051, grpc_secure=False,
            auth_credentials=Auth.api_key(WEAVIATE_API_KEY),
        )
        logger.info(f"✓ Weaviate client connected successfully")
        return client
    except Exception as e:
        logger.error(f"✗ Failed to connect to Weaviate: {e}")
        raise

def _filterresults(results):
    """
    Filter and deduplicate search results.
    
    This function aggregates results by document name and filters for the most relevant documents
    based on the number of matching chunks (using the 90th percentile as a threshold).
    
    Args:
        results: The raw search results from Weaviate.
        
    Returns:
        dict: A dictionary mapping document names to their text content.
    """
    try:
        logger.debug("Filtering and deduplicating results")
        resultdict = []
        hitsdict = {}
        
        for obj in results.objects:
            doc_name = obj.properties['doc_name']
            text = obj.properties['text']

            row_data = {
                "doc_name": doc_name,
                "text" : text
            }
            resultdict.append(row_data)

            try:
                hitsdict[obj.properties['doc_name']] += 1
            except KeyError:
                hitsdict[obj.properties['doc_name']]  = 1

        logger.debug(f"Extracted {len(resultdict)} results, {len(hitsdict)} unique documents")

        res_df = pd.DataFrame(resultdict).drop_duplicates()
        # top matching documents based on chunk counts (90th percentile)
        if len(hitsdict) > 0:
            high_values = [key for key, value in hitsdict.items() if value >= int(np.quantile(list(hitsdict.values()), 0.90))]
            res_df = res_df.loc[res_df['doc_name'].isin(high_values)]
            logger.debug(f"Filtered to top {len(high_values)} documents by relevance")
        
        final_res = dict(zip(res_df['doc_name'], res_df['text']))
        logger.info(f"✓ Filter complete: {len(final_res)} results")
        
        return final_res
    except Exception as e:
        logger.error(f"✗ Filter failed: {e}")
        raise

def search(query: str) -> dict:
    """
    Search for documents using vector similarity.
    
    Args:
        query (str): The search query string.
        
    Returns:
        dict: A dictionary of filtered search results.
    """
    progress_tracker.start_stage("search", f"Query: {query[:50]}")
    
    try:
        logger.info(f"🔍 Starting search for query: '{query}'")
        client = get_client()
        
        if client is None:
            raise ValueError("Weaviate client is not initialized.")
        
        logger.debug(f"Fetching collection: {WEAVIATE_COLLECTION}")
        collection = client.collections.get(WEAVIATE_COLLECTION)

        logger.debug("Embedding query text...")
        query_vector = embed_text(query)
        logger.debug(f"✓ Query embedded (dimension: {len(query_vector)})")

        logger.debug(f"Querying nearest vectors (top_k={TOP_K_DEFAULT})")
        res = collection.query.near_vector(
            near_vector=query_vector,
            limit=TOP_K_DEFAULT,
            return_metadata=["distance"],
            include_vector=False
        )
        
        logger.info(f"✓ Query returned {len(res.objects) if res.objects else 0} objects")

        client.close()
        logger.debug("Weaviate client closed")

        filtered = _filterresults(res)
        result_count = len(filtered)
        progress_tracker.complete_stage("search", f"Found {result_count} documents")
        logger.info(f"✓ Search complete: {result_count} filtered results")
        
        return filtered if filtered else {}
        
    except Exception as e:
        progress_tracker.fail_stage("search", str(e))
        logger.error(f"✗ Search failed: {e}", exc_info=True)
        raise