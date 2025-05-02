"""
RAG (Retrieval Augmented Generation) module for the chatbot application.
Implements the main RAG engine combining database queries, vector retrieval, and LLM generation.
"""

import logging
import re
from typing import List, Dict, Any, Tuple, Optional

from chatbot.database import DatabaseManager
from chatbot.embedding import EmbeddingManager
from chatbot.llm import LLMManager
from chatbot.prompts import (
    SYSTEM_PROMPT, 
    SQL_GENERATION_PROMPT,
    RAG_PROMPT,
    CONVERSATIONAL_PROMPT
)

logger = logging.getLogger(__name__)

class RAGEngine:
    """
    Retrieval Augmented Generation engine for the chatbot.
    Combines database queries, vector retrieval, and LLM generation.
    """
    
    def __init__(self, 
                 db_manager: DatabaseManager, 
                 embedding_manager: EmbeddingManager, 
                 llm_manager: LLMManager,
                 top_k: int = 3):
        """
        Initialize the RAG engine.
        
        Args:
            db_manager (DatabaseManager): Database manager instance
            embedding_manager (EmbeddingManager): Embedding manager instance
            llm_manager (LLMManager): LLM manager instance
            top_k (int): Number of similar documents to retrieve
        """
        self.db_manager = db_manager
        self.embedding_manager = embedding_manager
        self.llm_manager = llm_manager
        self.top_k = top_k
        
        # Store the schema info to use in prompts
        self.schema_info = db_manager.get_schema_info()
        
        # Add schema info to vector store if it doesn't exist already
        try:
            self.embedding_manager.add_schema_info_to_vector_store(self.schema_info)
            logger.info("Added database schema info to vector store")
        except Exception as e:
            logger.error(f"Error adding schema info to vector store: {e}")
        
        logger.info("RAG engine initialized")
    
    def is_sql_query(self, text: str) -> bool:
        """
        Check if the text is likely an SQL query.
        
        Args:
            text (str): Text to check
            
        Returns:
            bool: True if the text is likely an SQL query
        """
        # Simple heuristic: check if the text contains SQL keywords
        sql_keywords = ["select", "from", "where", "join", "group by", "order by", "limit"]
        text_lower = text.lower()
        
        # Check if the text starts with SELECT and contains FROM
        if re.search(r'^\s*select', text_lower) and "from" in text_lower:
            return True
        
        # Count SQL keywords in the text
        keyword_count = sum(1 for keyword in sql_keywords if keyword in text_lower)
        
        # If multiple SQL keywords are present, it's likely an SQL query
        return keyword_count >= 2
    
    def generate_sql_query(self, question: str) -> str:
        """
        Generate an SQL query from a natural language question.
        
        Args:
            question (str): Natural language question
            
        Returns:
            str: Generated SQL query
        """
        # First, try the simple rule-based conversion
        query = self.db_manager.natural_language_to_sql_query(question)
        if query:
            logger.info(f"Generated SQL query using rule-based conversion: {query}")
            return query
        
        # If that fails, use the LLM to generate the query
        prompt = SQL_GENERATION_PROMPT.format(
            schema=self.schema_info,
            question=question
        )
        
        response = self.llm_manager.generate(prompt)
        
        # Extract the SQL query from the response
        # Look for SQL blocks in markdown or just the first SQL-like statement
        if "```sql" in response:
            sql_blocks = response.split("```sql")
            if len(sql_blocks) > 1:
                query = sql_blocks[1].split("```")[0].strip()
                return query
        elif "```" in response:
            code_blocks = response.split("```")
            if len(code_blocks) > 1:
                query = code_blocks[1].strip()
                return query
        
        # Fall back to using the entire response if no code blocks were found
        # Remove any non-SQL explanatory text at the beginning
        if "SELECT" in response or "select" in response:
            select_pos = response.find("SELECT") if "SELECT" in response else response.find("select")
            query = response[select_pos:].strip()
            return query
        
        # If all else fails, return the entire response
        return response
    
    def execute_rag_query(self, question: str) -> Dict[str, Any]:
        """
        Execute a RAG query for the given question.
        
        Args:
            question (str): Question to answer
            
        Returns:
            Dict[str, Any]: RAG result containing retrieved context and generated answer
        """
        # Step 1: Check if the question is a direct SQL query
        if self.is_sql_query(question):
            logger.info(f"Detected direct SQL query: {question}")
            try:
                # Execute the query directly
                results = self.db_manager.execute_query(question)
                # Add the results to the vector store for future retrieval
                self.embedding_manager.add_sql_results_to_vector_store(question, results)
                
                return {
                    "query_type": "direct_sql",
                    "sql_query": question,
                    "sql_results": results,
                    "context": [{"content": str(results), "source": "direct_sql_results"}],
                    "answer": f"SQL Query Results: {results}"
                }
            except Exception as e:
                logger.error(f"Error executing direct SQL query: {e}")
                return {
                    "query_type": "direct_sql_error",
                    "sql_query": question,
                    "error": str(e),
                    "context": [],
                    "answer": f"Error executing SQL query: {str(e)}"
                }
        
        # Step 2: Retrieve relevant context from the vector store
        try:
            vector_results = self.embedding_manager.similarity_search(question, k=self.top_k)
            context = [{"content": item["content"], "source": item["metadata"].get("source", "unknown")} 
                      for item in vector_results]
            logger.info(f"Retrieved {len(context)} context items from vector store")
        except Exception as e:
            logger.error(f"Error retrieving context from vector store: {e}")
            context = []
        
        # Step 3: Generate SQL query if the question seems database-related
        # Check if the question contains database-related terms
        db_related_terms = ["database", "data", "query", "show", "list", "find", "how many", 
                            "average", "datacenter", "server", "power", "network"]
        
        is_db_question = any(term in question.lower() for term in db_related_terms)
        
        sql_results = []
        sql_query = None
        
        if is_db_question:
            try:
                # Generate SQL query
                sql_query = self.generate_sql_query(question)
                logger.info(f"Generated SQL query: {sql_query}")
                
                # Execute the query
                sql_results = self.db_manager.execute_query(sql_query)
                logger.info(f"SQL query returned {len(sql_results)} results")
                
                # Add the results to the vector store for future retrieval
                self.embedding_manager.add_sql_results_to_vector_store(sql_query, sql_results)
                
                # Add SQL results to context
                context.append({
                    "content": f"SQL Query: {sql_query}\nResults: {str(sql_results)}",
                    "source": "generated_sql_results"
                })
            except Exception as e:
                logger.error(f"Error generating or executing SQL query: {e}")
                context.append({
                    "content": f"Failed to execute SQL query due to error: {str(e)}",
                    "source": "sql_error"
                })
        
        # Step 4: Generate the final answer using RAG
        context_text = "\n\n".join([f"Context {i+1} ({item['source']}):\n{item['content']}" 
                                   for i, item in enumerate(context)])
        
        rag_prompt = RAG_PROMPT.format(
            schema=self.schema_info,
            context=context_text,
            question=question
        )
        
        answer = self.llm_manager.generate(rag_prompt)
        
        return {
            "query_type": "rag",
            "sql_query": sql_query,
            "sql_results": sql_results,
            "context": context,
            "answer": answer
        }
    
    def answer_conversational_query(self, question: str, conversation_history: List[Dict[str, str]]) -> str:
        """
        Answer a conversational query using RAG and conversation history.
        
        Args:
            question (str): Current question
            conversation_history (List[Dict[str, str]]): Previous conversation exchanges
            
        Returns:
            str: Generated answer
        """
        # Execute RAG query
        rag_result = self.execute_rag_query(question)
        
        # Format conversation history
        history_text = ""
        for i, exchange in enumerate(conversation_history[-5:]):  # Use last 5 exchanges
            history_text += f"User: {exchange['user']}\nAssistant: {exchange['assistant']}\n\n"
        
        # Prepare context for conversational prompt
        rag_context = rag_result.get("context", [])
        context_text = "\n\n".join([f"Context {i+1} ({item['source']}):\n{item['content']}" 
                                  for i, item in enumerate(rag_context)])
        
        # Include SQL results if present
        sql_info = ""
        if rag_result.get("sql_query"):
            sql_info = f"SQL Query: {rag_result['sql_query']}\nSQL Results: {rag_result['sql_results']}"
        
        # Generate conversational response
        prompt = CONVERSATIONAL_PROMPT.format(
            system_prompt=SYSTEM_PROMPT,
            conversation_history=history_text,
            context=context_text,
            sql_info=sql_info,
            rag_answer=rag_result["answer"],
            question=question
        )
        
        return self.llm_manager.generate(prompt)
