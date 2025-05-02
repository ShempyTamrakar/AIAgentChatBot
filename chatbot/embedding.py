"""
Embedding module for the chatbot application.
Manages embeddings generation and vector database operations.
"""

import logging
import os
from typing import List, Dict, Any, Optional
import numpy as np

# Importing langchain components for embeddings and vector store
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.document_loaders import TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class EmbeddingManager:
    """
    Manages embeddings generation and vector database operations.
    """
    
    def __init__(self, model_name: str, vector_db_path: str):
        """
        Initialize the embedding manager.
        
        Args:
            model_name (str): Name of the Hugging Face embedding model to use
            vector_db_path (str): Path to store the vector database
        """
        self.model_name = model_name
        self.vector_db_path = vector_db_path
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        self.vector_store = None
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(vector_db_path), exist_ok=True)
        
        # Try to load existing vector store
        self._load_or_create_vector_store()
        
        logger.info(f"Embedding manager initialized with model {model_name}")
    
    def _load_or_create_vector_store(self):
        """Load existing vector store or create a new one if it doesn't exist"""
        try:
            if os.path.exists(f"{self.vector_db_path}/index.faiss"):
                logger.info(f"Loading existing vector store from {self.vector_db_path}")
                self.vector_store = FAISS.load_local(
                    self.vector_db_path,
                    self.embeddings
                )
            else:
                logger.info(f"Creating new vector store at {self.vector_db_path}")
                # Create an empty vector store
                self.vector_store = FAISS.from_texts(
                    ["This is a placeholder document."], 
                    self.embeddings
                )
                # Save the vector store
                self.vector_store.save_local(self.vector_db_path)
        except Exception as e:
            logger.error(f"Error loading or creating vector store: {e}")
            # Create an empty vector store as fallback
            self.vector_store = FAISS.from_texts(
                ["This is a placeholder document."], 
                self.embeddings
            )
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate an embedding for the given text.
        
        Args:
            text (str): Text to generate embedding for
            
        Returns:
            np.ndarray: Embedding vector
        """
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def add_texts_to_vector_store(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """
        Add texts to the vector store.
        
        Args:
            texts (List[str]): List of texts to add
            metadatas (Optional[List[Dict[str, Any]]]): Optional metadata for each text
            
        Returns:
            List[str]: List of document IDs
        """
        try:
            if not texts:
                logger.warning("No texts provided to add to vector store")
                return []
            
            ids = self.vector_store.add_texts(texts, metadatas)
            
            # Save the updated vector store
            self.vector_store.save_local(self.vector_db_path)
            
            logger.info(f"Added {len(texts)} texts to vector store")
            return ids
        except Exception as e:
            logger.error(f"Error adding texts to vector store: {e}")
            raise
    
    def similarity_search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """
        Perform similarity search on the vector store.
        
        Args:
            query (str): Query text
            k (int): Number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of documents with similarity scores
        """
        try:
            documents = self.vector_store.similarity_search_with_score(query, k=k)
            
            # Convert to a more usable format
            results = []
            for doc, score in documents:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                })
            
            return results
        except Exception as e:
            logger.error(f"Error performing similarity search: {e}")
            raise
    
    def add_schema_info_to_vector_store(self, schema_info: str) -> List[str]:
        """
        Add database schema information to the vector store.
        
        Args:
            schema_info (str): Database schema information
            
        Returns:
            List[str]: List of document IDs
        """
        # Split the schema info into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        chunks = text_splitter.split_text(schema_info)
        
        # Add metadata to each chunk
        metadatas = [{"source": "schema_info", "chunk": i} for i in range(len(chunks))]
        
        # Add to vector store
        return self.add_texts_to_vector_store(chunks, metadatas)
    
    def add_sql_results_to_vector_store(self, query: str, results: List[Dict[str, Any]]) -> List[str]:
        """
        Add SQL query results to the vector store.
        
        Args:
            query (str): SQL query that generated the results
            results (List[Dict[str, Any]]): Query results
            
        Returns:
            List[str]: List of document IDs
        """
        if not results:
            logger.warning(f"No results to add for query: {query}")
            return []
        
        # Convert results to text format
        texts = []
        for i, result in enumerate(results):
            result_text = f"Query: {query}\nResult {i+1}:\n"
            for key, value in result.items():
                result_text += f"{key}: {value}\n"
            texts.append(result_text)
        
        # Add metadata to each text
        metadatas = [{"source": "sql_result", "query": query, "result_index": i} for i in range(len(texts))]
        
        # Add to vector store
        return self.add_texts_to_vector_store(texts, metadatas)
