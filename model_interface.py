import os
import json
import logging
import time
from typing import Optional, Dict, Any, List, Union
import openai
from openai import OpenAI
import anthropic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('model_interface')

class ModelInterface:
    """
    Interface for interacting with multiple AI models (OpenAI and Anthropic).
    
    This class provides a unified interface for text generation, embedding creation,
    and other AI functionalities, regardless of the underlying model provider.
    """
    
    def __init__(self):
        """Initialize the model interface with API clients."""
        self.openai_client = None
        self.anthropic_client = None
        
        # Initialize OpenAI client if API key is available
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=openai_api_key)
                logger.info("OpenAI client initialized successfully.")
            except Exception as e:
                logger.error(f"Error initializing OpenAI client: {str(e)}")
        
        # Initialize Anthropic client if API key is available
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        if anthropic_api_key:
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
                logger.info("Anthropic client initialized successfully.")
            except Exception as e:
                logger.error(f"Error initializing Anthropic client: {str(e)}")
    
    def check_openai_status(self) -> bool:
        """Check if OpenAI API is available and operational."""
        if not self.openai_client:
            return False
        
        try:
            # Make a simple API call to test connectivity
            models = self.openai_client.models.list()
            return True
        except Exception as e:
            logger.error(f"OpenAI API check failed: {str(e)}")
            return False
    
    def check_anthropic_status(self) -> bool:
        """Check if Anthropic API is available and operational."""
        if not self.anthropic_client:
            return False
        
        try:
            # Make a simple API call to test connectivity
            # Anthropic doesn't have a simple status check API, so we use a minimal query
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except Exception as e:
            logger.error(f"Anthropic API check failed: {str(e)}")
            return False
    
    def generate_text(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        provider: str = "openai",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate text using the specified provider.
        
        Args:
            prompt: The user prompt or question
            system_message: Optional system message for context
            provider: AI provider to use ('openai' or 'anthropic')
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation (randomness)
            options: Additional provider-specific options
            
        Returns:
            Generated text response
        
        Raises:
            Exception: If generation fails or provider is not available
        """
        if not options:
            options = {}
        
        # Use fallback provider if requested one is not available
        if provider == "openai" and not self.openai_client:
            if self.anthropic_client:
                logger.warning("OpenAI not available, falling back to Anthropic")
                provider = "anthropic"
            else:
                raise Exception("No AI providers are available")
        elif provider == "anthropic" and not self.anthropic_client:
            if self.openai_client:
                logger.warning("Anthropic not available, falling back to OpenAI")
                provider = "openai"
            else:
                raise Exception("No AI providers are available")
        
        # Generate with requested provider
        if provider == "openai":
            return self._generate_openai(prompt, system_message, max_tokens, temperature, options)
        elif provider == "anthropic":
            return self._generate_anthropic(prompt, system_message, max_tokens, temperature, options)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def _generate_openai(
        self,
        prompt: str,
        system_message: Optional[str],
        max_tokens: int,
        temperature: float,
        options: Dict[str, Any]
    ) -> str:
        """
        Generate text using OpenAI.
        
        Args:
            prompt: The user prompt or question
            system_message: Optional system message for context
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            options: Additional OpenAI-specific options
            
        Returns:
            Generated text response
        """
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")
        
        # Prepare messages
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        # Set up parameters
        params = {
            "model": options.get("model", "gpt-4o"),  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        # Add any additional parameters
        for key, value in options.items():
            if key != "model":  # Model already handled
                params[key] = value
        
        # Generate response
        response = self.openai_client.chat.completions.create(**params)
        return response.choices[0].message.content
    
    def _generate_anthropic(
        self,
        prompt: str,
        system_message: Optional[str],
        max_tokens: int,
        temperature: float,
        options: Dict[str, Any]
    ) -> str:
        """
        Generate text using Anthropic.
        
        Args:
            prompt: The user prompt or question
            system_message: Optional system message for context
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            options: Additional Anthropic-specific options
            
        Returns:
            Generated text response
        """
        if not self.anthropic_client:
            raise Exception("Anthropic client not initialized")
        
        # Prepare messages
        messages = [{"role": "user", "content": prompt}]
        
        # Set up parameters
        params = {
            "model": options.get("model", "claude-3-5-sonnet-20241022"),  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        # Add system prompt if provided
        if system_message:
            params["system"] = system_message
        
        # Add any additional parameters
        for key, value in options.items():
            if key != "model":  # Model already handled
                params[key] = value
        
        # Generate response
        response = self.anthropic_client.messages.create(**params)
        return response.content[0].text
    
    def create_embeddings(
        self,
        texts: List[str],
        provider: str = "openai",
        options: Optional[Dict[str, Any]] = None
    ) -> List[List[float]]:
        """
        Create embeddings for the given texts.
        
        Args:
            texts: List of texts to create embeddings for
            provider: AI provider to use ('openai' or 'anthropic')
            options: Additional provider-specific options
            
        Returns:
            List of embedding vectors
        
        Raises:
            Exception: If embedding creation fails or provider is not available
        """
        if not options:
            options = {}
        
        # Use fallback provider if requested one is not available
        if provider == "openai" and not self.openai_client:
            if self.anthropic_client:
                logger.warning("OpenAI not available, falling back to Anthropic")
                provider = "anthropic"
            else:
                raise Exception("No AI providers are available")
        elif provider == "anthropic" and not self.anthropic_client:
            if self.openai_client:
                logger.warning("Anthropic not available, falling back to OpenAI")
                provider = "openai"
            else:
                raise Exception("No AI providers are available")
        
        # Create embeddings with requested provider
        if provider == "openai":
            return self._create_embeddings_openai(texts, options)
        else:
            raise ValueError(f"Embeddings not supported for provider: {provider}")
    
    def _create_embeddings_openai(
        self,
        texts: List[str],
        options: Dict[str, Any]
    ) -> List[List[float]]:
        """
        Create embeddings using OpenAI.
        
        Args:
            texts: List of texts to create embeddings for
            options: Additional OpenAI-specific options
            
        Returns:
            List of embedding vectors
        """
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")
        
        # Set up parameters
        params = {
            "model": options.get("model", "text-embedding-3-large"),
            "input": texts,
        }
        
        # Add any additional parameters
        for key, value in options.items():
            if key != "model":  # Model already handled
                params[key] = value
        
        # Create embeddings
        response = self.openai_client.embeddings.create(**params)
        return [data.embedding for data in response.data]
    
    def analyze_image(
        self,
        image_data: Union[str, bytes],
        prompt: str = "Analyze this image in detail",
        provider: str = "openai"
    ) -> str:
        """
        Analyze the given image using vision capabilities.
        
        Args:
            image_data: Image data as base64 string or bytes
            prompt: The prompt for image analysis
            provider: AI provider to use (currently only 'openai' is supported)
            
        Returns:
            Analysis text
        
        Raises:
            Exception: If image analysis fails or provider is not available
        """
        if provider != "openai":
            raise ValueError(f"Image analysis not supported for provider: {provider}")
        
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")
        
        # Prepare image data
        if isinstance(image_data, bytes):
            # Convert bytes to base64
            import base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
        else:
            # Assume it's already a base64 string
            base64_image = image_data
        
        # Create the message content with text and image
        content = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            }
        ]
        
        # Create the response
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "user", "content": content}
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content