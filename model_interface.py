"""
Model Interface Module

This module provides a unified interface for interacting with different AI models and services.
"""

import os
import logging
import time
from typing import List, Dict, Any, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelInterface:
    """
    Interface for interacting with AI models.
    
    This class abstracts away the differences between different model providers
    and provides a unified interface for the application to use.
    """
    def __init__(self, model_id: Optional[str] = None, capability: Optional[str] = None):
        """
        Initialize the model interface.
        
        Args:
            model_id: Optional specific model ID to use
            capability: Optional capability to select model for
        """
        self.model_id = model_id
        self.capability = capability
        self.clients = {}
        
        # Initialize provider-specific clients
        self._initialize_clients()
        
    def _initialize_clients(self):
        """Initialize provider-specific clients"""
        # Initialize OpenAI client
        try:
            openai_key = os.environ.get("OPENAI_API_KEY")
            if openai_key:
                import openai
                from openai import OpenAI
                self.clients["openai"] = OpenAI(api_key=openai_key)
                logger.info("OpenAI client initialized successfully.")
            else:
                logger.warning("OpenAI API key not found.")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
        
        # Initialize Anthropic client
        try:
            anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
            if anthropic_key:
                import anthropic
                self.clients["anthropic"] = anthropic.Anthropic(api_key=anthropic_key)
                logger.info("Anthropic client initialized successfully.")
            else:
                logger.warning("Anthropic API key not found.")
        except Exception as e:
            logger.error(f"Error initializing Anthropic client: {str(e)}")
            
    def check_openai_status(self) -> bool:
        """
        Check if OpenAI API is available and properly configured.
        
        Returns:
            True if available, False otherwise
        """
        return "openai" in self.clients
        
    def check_anthropic_status(self) -> bool:
        """
        Check if Anthropic API is available and properly configured.
        
        Returns:
            True if available, False otherwise
        """
        return "anthropic" in self.clients
        
    def generate_text(self, prompt: str, system_message: Optional[str] = None,
                    max_tokens: Optional[int] = None, provider: str = "auto") -> str:
        """
        Generate text using the configured model.
        
        Args:
            prompt: The user prompt to send to the model
            system_message: Optional system message for chat models
            max_tokens: Maximum tokens to generate
            provider: Which provider to use ("openai", "anthropic", or "auto")
        
        Returns:
            The generated text
        """
        if provider == "auto":
            # Try OpenAI first, then fall back to Anthropic
            if "openai" in self.clients:
                provider = "openai"
            elif "anthropic" in self.clients:
                provider = "anthropic"
            else:
                raise ValueError("No AI providers available. Please configure API keys.")
        
        if provider == "openai":
            if "openai" not in self.clients:
                raise ValueError("OpenAI client not initialized. Please configure API key.")
            return self._generate_text_openai(prompt, system_message, max_tokens or 1000)
        elif provider == "anthropic":
            if "anthropic" not in self.clients:
                raise ValueError("Anthropic client not initialized. Please configure API key.")
            return self._generate_text_anthropic(prompt, system_message, max_tokens or 1000)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def _generate_text_openai(self, prompt: str, system_message: Optional[str], max_tokens: int) -> str:
        """Generate text using OpenAI models"""
        try:
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            messages = []
            
            if system_message:
                messages.append({"role": "system", "content": system_message})
                
            messages.append({"role": "user", "content": prompt})
            
            response = self.clients["openai"].chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {str(e)}")
            return f"Error: {str(e)}"
    
    def _generate_text_anthropic(self, prompt: str, system_message: Optional[str], max_tokens: int) -> str:
        """Generate text using Anthropic models"""
        try:
            # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024.
            # do not change this unless explicitly requested by the user
            
            # Prepare messages
            if system_message:
                system = system_message
            else:
                system = "You are a helpful AI assistant."
                
            response = self.clients["anthropic"].messages.create(
                model="claude-3-5-sonnet-20241022",
                system=system,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error generating text with Anthropic: {str(e)}")
            return f"Error: {str(e)}"
            
    def analyze_code(self, code: str, language: str, query: str) -> Dict[str, Any]:
        """
        Analyze code using the configured model.
        
        Args:
            code: The code to analyze
            language: The programming language of the code
            query: What to analyze about the code
        
        Returns:
            Analysis results
        """
        prompt = f"""
        I'd like you to analyze the following {language} code:
        
        ```{language}
        {code}
        ```
        
        {query}
        
        Please provide your analysis with the following structure:
        1. Summary of the code's purpose and functionality
        2. Specific response to the query
        3. Any potential issues or improvement suggestions
        4. Code quality assessment (1-10 scale)
        
        Format your response as JSON with these keys: "summary", "query_response", "issues", "quality_score"
        """
        
        system_message = "You are an expert code analysis AI. Provide detailed, accurate analysis of code with actionable insights."
        
        try:
            if "openai" in self.clients:
                response = self.clients["openai"].chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                import json
                return json.loads(response.choices[0].message.content)
            elif "anthropic" in self.clients:
                response = self.clients["anthropic"].messages.create(
                    model="claude-3-5-sonnet-20241022",
                    system=system_message,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000
                )
                import json
                # Try to extract JSON from the response
                content = response.content[0].text
                try:
                    # Try direct JSON parsing
                    return json.loads(content)
                except:
                    # Try to extract JSON from markdown code blocks
                    import re
                    json_match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group(1))
                    else:
                        raise ValueError("Could not extract JSON from response")
            else:
                raise ValueError("No AI providers available. Please configure API keys.")
        except Exception as e:
            logger.error(f"Error analyzing code: {str(e)}")
            return {
                "summary": f"Error analyzing code: {str(e)}",
                "query_response": "Analysis failed",
                "issues": ["Analysis service unavailable"],
                "quality_score": 0
            }