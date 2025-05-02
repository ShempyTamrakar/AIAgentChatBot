"""
Configuration module for the chatbot application.
Handles loading settings from environment variables or defaults.
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def get_config():
    """
    Load and return the configuration for the chatbot.
    
    Returns:
        dict: Configuration dictionary
    """
    # Define base directory for relative paths
    base_dir = Path(__file__).parent.parent.absolute()
    
    # Database configuration
    db_path = os.getenv("DB_PATH", str(base_dir / "data" / "datacenter.db"))
    
    # Embedding configuration
    embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    vector_db_path = os.getenv("VECTOR_DB_PATH", str(base_dir / "data" / "vector_db"))
    
    # LLM Configuration
    llm_model = os.getenv("LLM_MODEL", "gemma")
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # RAG Configuration
    top_k_results = int(os.getenv("TOP_K_RESULTS", "3"))
    
    config = {
        "database": {
            "path": db_path,
        },
        "embeddings": {
            "model_name": embedding_model,
            "vector_db_path": vector_db_path,
        },
        "llm": {
            "model_name": llm_model,
            "base_url": ollama_base_url,
            "temperature": 0.7,
            "top_p": 0.9,
        },
        "rag": {
            "top_k": top_k_results,
        }
    }
    
    logger.info(f"Loaded configuration with database path: {db_path}")
    logger.info(f"Using LLM model: {llm_model}")
    
    return config
