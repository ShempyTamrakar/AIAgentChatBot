"""
Conversation module for the chatbot application.
Manages conversation history and high-level interaction flow.
"""

import logging
import re
from typing import List, Dict, Any, Optional

from chatbot.rag import RAGEngine
from chatbot.prompts import GREETING_PROMPT

logger = logging.getLogger(__name__)

class Conversation:
    """
    Manages conversation history and high-level interaction flow.
    """
    
    def __init__(self, rag_engine: RAGEngine):
        """
        Initialize the conversation manager.
        
        Args:
            rag_engine (RAGEngine): RAG engine instance
        """
        self.rag_engine = rag_engine
        self.conversation_history = []
        
        logger.info("Conversation manager initialized")
    
    def is_greeting(self, text: str) -> bool:
        """
        Check if the text is a greeting or small talk.
        
        Args:
            text (str): Text to check
            
        Returns:
            bool: True if the text is a greeting
        """
        greetings = [
            r"^(hi|hello|hey|greetings|howdy)(\s|$|!)",
            r"^good\s(morning|afternoon|evening|day)(\s|$|!)",
            r"^how\s(are\syou|is\sit\sgoing|are\sthings)(\?|\s|$)",
            r"^what'?s\sup(\?|\s|$)",
            r"^nice\sto\s(meet|see)\syou(\s|$|!)",
        ]
        
        for pattern in greetings:
            if re.search(pattern, text.lower()):
                return True
        
        # Check if the input is very short (likely a greeting or short question)
        if len(text.split()) <= 3:
            return True
            
        return False
    
    def handle_greeting(self, text: str) -> str:
        """
        Handle greetings and small talk.
        
        Args:
            text (str): User input text
            
        Returns:
            str: Response to the greeting
        """
        prompt = GREETING_PROMPT.format(user_input=text)
        
        return self.rag_engine.llm_manager.generate(prompt)
    
    def process_input(self, user_input: str) -> str:
        """
        Process user input and generate a response.
        
        Args:
            user_input (str): User input text
            
        Returns:
            str: Generated response
        """
        # Check if the input is a greeting or small talk
        if self.is_greeting(user_input):
            logger.info(f"Detected greeting or small talk: {user_input}")
            response = self.handle_greeting(user_input)
        else:
            # Use RAG to answer the question
            logger.info(f"Processing question: {user_input}")
            response = self.rag_engine.answer_conversational_query(user_input, self.conversation_history)
        
        # Add the exchange to conversation history
        self.conversation_history.append({
            "user": user_input,
            "assistant": response
        })
        
        return response
    
    def get_conversation_summary(self) -> str:
        """
        Get a summary of the conversation.
        
        Returns:
            str: Conversation summary
        """
        if not self.conversation_history:
            return "No conversation history."
        
        # Get the last 5 exchanges
        recent_history = self.conversation_history[-5:]
        
        summary = "Recent conversation exchanges:\n\n"
        for i, exchange in enumerate(recent_history):
            summary += f"Exchange {i+1}:\n"
            summary += f"User: {exchange['user']}\n"
            summary += f"Assistant: {exchange['assistant']}\n\n"
        
        return summary
    
    def clear_history(self) -> None:
        """
        Clear the conversation history.
        """
        self.conversation_history = []
        logger.info("Conversation history cleared")
