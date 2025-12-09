"""
Configuration Module

This module loads environment variables and defines configuration constants
for the application, including settings for Ollama, Weaviate, and Google Gemini.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ==========================================
# LLM & Embedding Configuration
# ==========================================
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "embeddinggemma")
SUMMARIZE_MODEL = os.getenv("SUMMARIZE_MODEL", "gemini-2.5-flash")
GEMMA_API_KEY = os.getenv("GEMMA_API_KEY", "googleapi")

# ==========================================
# Vector Database Configuration (Weaviate)
# ==========================================
WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "localhost")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "supersecret_api_key_123")
WEAVIATE_COLLECTION = os.getenv("WEAVIATE_COLLECTION", "Advisory")
TOP_K_DEFAULT = int(os.getenv("TOP_K_DEFAULT", "25"))
