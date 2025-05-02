"""
LLM module for the chatbot application.
Manages interactions with the Ollama LLM using the gemma model.
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional

import requests

logger = logging.getLogger(__name__)

class LLMManager:
    """
    Manages interactions with the Ollama LLM.
    """
    
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434"):
        """
        Initialize the LLM manager.
        
        Args:
            model_name (str): Name of the Ollama model to use (e.g., 'gemma')
            base_url (str): Base URL of the Ollama API
        """
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        
        # Check if Ollama is available
        self._check_ollama_availability()
        
        logger.info(f"LLM manager initialized with model {model_name}")
    
    def _check_ollama_availability(self):
        """
        Check if Ollama is available and the model is loaded.
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                logger.warning(f"Ollama API returned status code {response.status_code}")
                return
            
            # Check if the model is available
            models = response.json().get("models", [])
            model_names = [model.get("name") for model in models]
            
            if self.model_name not in model_names:
                logger.warning(f"Model {self.model_name} not found in Ollama. Available models: {model_names}")
                logger.info(f"You may need to pull the model using: ollama pull {self.model_name}")
            else:
                logger.info(f"Model {self.model_name} is available in Ollama")
                
        except requests.RequestException as e:
            logger.error(f"Error connecting to Ollama API: {e}")
            logger.info("Make sure Ollama is running and accessible")
    
    def generate(self, prompt: str, temperature: float = 0.7, top_p: float = 0.9, max_tokens: int = 2048) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt (str): Prompt to send to the LLM
            temperature (float): Temperature parameter for generation
            top_p (float): Top-p parameter for generation
            max_tokens (int): Maximum number of tokens to generate
            
        Returns:
            str: Generated response
        """
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "stream": False  # Don't stream the response
            }
            
            logger.debug(f"Sending prompt to LLM: {prompt[:100]}...")
            
            response = requests.post(self.api_url, json=payload)
            
            if response.status_code != 200:
                logger.error(f"LLM API returned status code {response.status_code}: {response.text}")
                return f"Error: Failed to generate response (status code {response.status_code})"
            
            response_data = response.json()
            generated_text = response_data.get("response", "")
            
            return generated_text.strip()
            
        except requests.RequestException as e:
            logger.error(f"Error calling LLM API: {e}")
            return f"Error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error in LLM generation: {e}")
            return f"Error: {str(e)}"
    
    def generate_with_retries(self, prompt: str, max_retries: int = 3, **kwargs) -> str:
        """
        Generate a response with retries in case of failure.
        
        Args:
            prompt (str): Prompt to send to the LLM
            max_retries (int): Maximum number of retries
            **kwargs: Additional arguments to pass to generate()
            
        Returns:
            str: Generated response
        """
        for attempt in range(max_retries):
            try:
                return self.generate(prompt, **kwargs)
            except Exception as e:
                logger.warning(f"Attempt {attempt+1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    # Exponential backoff
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"All {max_retries} attempts failed")
                    return f"I'm sorry, I'm having trouble generating a response after {max_retries} attempts."
    
    def generate_structured_output(self, prompt: str, output_format: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
        """
        Generate a structured output from the LLM using a specific format.
        
        Args:
            prompt (str): Prompt to send to the LLM
            output_format (Dict[str, Any]): Expected format of the output
            **kwargs: Additional arguments to pass to generate()
            
        Returns:
            Optional[Dict[str, Any]]: Generated structured output or None if parsing fails
        """
        format_prompt = f"{prompt}\n\nPlease provide your response in the following JSON format: {json.dumps(output_format, indent=2)}"
        
        response = self.generate(format_prompt, **kwargs)
        
        # Try to extract and parse JSON from the response
        try:
            # Look for JSON block in the response
            json_text = None
            if "```json" in response:
                json_blocks = response.split("```json")
                if len(json_blocks) > 1:
                    json_text = json_blocks[1].split("```")[0].strip()
            elif "```" in response:
                json_blocks = response.split("```")
                if len(json_blocks) > 1:
                    json_text = json_blocks[1].strip()
            else:
                # Try to find JSON-like content using braces
                start_idx = response.find('{')
                end_idx = response.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_text = response[start_idx:end_idx+1]
            
            if json_text:
                return json.loads(json_text)
            else:
                # Fallback: try to parse the entire response as JSON
                return json.loads(response)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            logger.debug(f"Response causing JSON parse error: {response}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing structured output: {e}")
            return None
