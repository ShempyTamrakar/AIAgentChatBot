"""
Unit tests for the RAG module.
"""

import unittest
from unittest.mock import MagicMock, patch

from chatbot.rag import RAGEngine

class TestRAGEngine(unittest.TestCase):
    """Test cases for the RAGEngine class."""
    
    def setUp(self):
        """Set up mocks for testing."""
        # Mock database manager
        self.db_manager = MagicMock()
        self.db_manager.get_schema_info.return_value = "Mock Schema Info"
        self.db_manager.execute_query.return_value = [{"result": "Mock DB Result"}]
        
        # Mock embedding manager
        self.embedding_manager = MagicMock()
        self.embedding_manager.similarity_search.return_value = [
            {"content": "Mock Content 1", "metadata": {"source": "mock_source_1"}, "score": 0.9},
            {"content": "Mock Content 2", "metadata": {"source": "mock_source_2"}, "score": 0.8}
        ]
        
        # Mock LLM manager
        self.llm_manager = MagicMock()
        self.llm_manager.generate.return_value = "Mock LLM Response"
        
        # Initialize RAG engine with mocks
        self.rag_engine = RAGEngine(
            self.db_manager,
            self.embedding_manager,
            self.llm_manager,
            top_k=2
        )
    
    def test_is_sql_query(self):
        """Test SQL query detection."""
        sql_queries = [
            "SELECT * FROM data_centers",
            "select name, location from data_centers where capacity_kw > 4000",
            "SELECT servers.hostname FROM servers JOIN data_centers ON servers.datacenter_id = data_centers.id"
        ]
        
        non_sql_queries = [
            "How many data centers do we have?",
            "List all servers in the Austin data center",
            "What is the average power usage in DC-North-1?"
        ]
        
        for query in sql_queries:
            self.assertTrue(self.rag_engine.is_sql_query(query))
        
        for query in non_sql_queries:
            self.assertFalse(self.rag_engine.is_sql_query(query))
    
    def test_generate_sql_query(self):
        """Test SQL query generation."""
        # Mock the LLM response to contain SQL
        self.llm_manager.generate.return_value = "```sql\nSELECT * FROM data_centers\n```"
        
        question = "List all data centers"
        sql_query = self.rag_engine.generate_sql_query(question)
        
        self.assertEqual(sql_query, "SELECT * FROM data_centers")
        self.llm_manager.generate.assert_called_once()
    
    def test_execute_rag_query_direct_sql(self):
        """Test RAG query execution with direct SQL."""
        query = "SELECT * FROM data_centers"
        result = self.rag_engine.execute_rag_query(query)
        
        self.assertEqual(result["query_type"], "direct_sql")
        self.assertEqual(result["sql_query"], query)
        self.db_manager.execute_query.assert_called_once_with(query)
    
    def test_execute_rag_query_natural_language(self):
        """Test RAG query execution with natural language."""
        # Mock generate_sql_query
        self.rag_engine.generate_sql_query = MagicMock(return_value="SELECT * FROM data_centers")
        
        query = "How many data centers do we have?"
        result = self.rag_engine.execute_rag_query(query)
        
        self.assertEqual(result["query_type"], "rag")
        self.assertEqual(result["sql_query"], "SELECT * FROM data_centers")
        self.embedding_manager.similarity_search.assert_called_once()
        self.llm_manager.generate.assert_called_once()
    
    def test_answer_conversational_query(self):
        """Test conversational query answering."""
        # Mock execute_rag_query
        self.rag_engine.execute_rag_query = MagicMock(return_value={
            "query_type": "rag",
            "sql_query": "SELECT * FROM data_centers",
            "sql_results": [{"name": "DC-North-1"}],
            "context": [{"content": "Mock Content", "source": "mock_source"}],
            "answer": "Mock RAG Answer"
        })
        
        conversation_history = [
            {"user": "Hello", "assistant": "Hi there! How can I help you?"},
            {"user": "Tell me about data centers", "assistant": "I'd be happy to help with data center information."}
        ]
        
        query = "How many data centers are in Seattle?"
        result = self.rag_engine.answer_conversational_query(query, conversation_history)
        
        self.assertEqual(result, "Mock LLM Response")
        self.rag_engine.execute_rag_query.assert_called_once_with(query)
        self.llm_manager.generate.assert_called_once()

if __name__ == "__main__":
    unittest.main()
