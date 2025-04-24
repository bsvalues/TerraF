"""
Multi-Model Interface

This module provides a unified interface for interacting with various AI models,
including OpenAI, Anthropic, Perplexity, DeepSeek, and Google's Gemini.
"""

import os
import json
import logging
import time
import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelDetails:
    """Model details and capabilities"""
    def __init__(self, name: str, provider: str, capabilities: List[str], max_tokens: int = 4096):
        self.name = name
        self.provider = provider
        self.capabilities = capabilities
        self.max_tokens = max_tokens

class MultiModelInterface:
    """
    Unified interface for interacting with multiple AI models.
    
    This class provides a consistent way to access different AI models,
    including OpenAI, Anthropic, Perplexity, DeepSeek, and Google's Gemini.
    """
    
    def __init__(self, preferred_model: Optional[str] = None):
        """
        Initialize the multi-model interface.
        
        Args:
            preferred_model: Optional preferred model to use
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Define available models and their capabilities
        self.models = {
            # OpenAI models
            "gpt-4o": ModelDetails(
                name="gpt-4o",
                provider="openai",
                capabilities=["text", "vision", "reasoning", "code"],
                max_tokens=8192
            ),
            "gpt-4-turbo": ModelDetails(
                name="gpt-4-turbo",
                provider="openai",
                capabilities=["text", "vision", "reasoning", "code"],
                max_tokens=4096
            ),
            "gpt-3.5-turbo": ModelDetails(
                name="gpt-3.5-turbo",
                provider="openai",
                capabilities=["text", "code"],
                max_tokens=4096
            ),
            
            # Anthropic models
            "claude-3-5-sonnet-20241022": ModelDetails(
                name="claude-3-5-sonnet-20241022",
                provider="anthropic",
                capabilities=["text", "vision", "reasoning"],
                max_tokens=200000
            ),
            "claude-3-opus-20240229": ModelDetails(
                name="claude-3-opus-20240229",
                provider="anthropic",
                capabilities=["text", "vision", "reasoning", "code"],
                max_tokens=100000
            ),
            "claude-3-sonnet-20240229": ModelDetails(
                name="claude-3-sonnet-20240229",
                provider="anthropic",
                capabilities=["text", "vision", "reasoning"],
                max_tokens=100000
            ),
            
            # Perplexity models
            "perplexity-online-mistral": ModelDetails(
                name="perplexity-online-mistral",
                provider="perplexity",
                capabilities=["text", "search", "current_events"],
                max_tokens=4096
            ),
            "perplexity-online-llama-3": ModelDetails(
                name="perplexity-online-llama-3",
                provider="perplexity",
                capabilities=["text", "search", "current_events"],
                max_tokens=4096
            ),
            
            # DeepSeek models
            "deepseek-coder": ModelDetails(
                name="deepseek-coder",
                provider="deepseek",
                capabilities=["code", "reasoning"],
                max_tokens=16384
            ),
            "deepseek-chat": ModelDetails(
                name="deepseek-chat",
                provider="deepseek",
                capabilities=["text", "reasoning"],
                max_tokens=8192
            ),
            
            # Google's Gemini models
            "gemini-pro": ModelDetails(
                name="gemini-pro",
                provider="google",
                capabilities=["text", "reasoning"],
                max_tokens=8192
            ),
            "gemini-pro-vision": ModelDetails(
                name="gemini-pro-vision",
                provider="google",
                capabilities=["text", "vision", "reasoning"],
                max_tokens=4096
            ),
        }
        
        # Select model
        self.preferred_model = preferred_model or "gpt-4o"
        if self.preferred_model not in self.models:
            self.logger.warning(f"Model {self.preferred_model} not found. Using gpt-4o as default.")
            self.preferred_model = "gpt-4o"
        
        # Initialize model clients
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize API clients for each provider"""
        # Dictionary to store initialized clients
        self.clients = {}
        
        # Initialize OpenAI client
        try:
            openai_key = os.environ.get("OPENAI_API_KEY")
            if openai_key:
                import openai
                self.clients["openai"] = openai.OpenAI(api_key=openai_key)
                self.logger.info("OpenAI client initialized successfully.")
            else:
                self.logger.warning("OpenAI API key not found.")
        except Exception as e:
            self.logger.error(f"Error initializing OpenAI client: {str(e)}")
        
        # Initialize Anthropic client
        try:
            anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
            if anthropic_key:
                import anthropic
                self.clients["anthropic"] = anthropic.Anthropic(api_key=anthropic_key)
                self.logger.info("Anthropic client initialized successfully.")
            else:
                self.logger.warning("Anthropic API key not found.")
        except Exception as e:
            self.logger.error(f"Error initializing Anthropic client: {str(e)}")
        
        # Initialize Perplexity client
        try:
            perplexity_key = os.environ.get("PERPLEXITY_API_KEY")
            if perplexity_key:
                # Perplexity uses the OpenAI client with a different base URL
                import openai
                self.clients["perplexity"] = openai.OpenAI(
                    api_key=perplexity_key,
                    base_url="https://api.perplexity.ai"
                )
                self.logger.info("Perplexity client initialized successfully.")
            else:
                self.logger.warning("Perplexity API key not found.")
        except Exception as e:
            self.logger.error(f"Error initializing Perplexity client: {str(e)}")
        
        # Initialize DeepSeek client
        try:
            deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
            if deepseek_key:
                # DeepSeek uses the OpenAI client with a different base URL
                import openai
                self.clients["deepseek"] = openai.OpenAI(
                    api_key=deepseek_key,
                    base_url="https://api.deepseek.com/v1"
                )
                self.logger.info("DeepSeek client initialized successfully.")
            else:
                self.logger.warning("DeepSeek API key not found.")
        except Exception as e:
            self.logger.error(f"Error initializing DeepSeek client: {str(e)}")
        
        # Initialize Google (Gemini) client
        try:
            google_key = os.environ.get("GOOGLE_API_KEY")
            if google_key:
                import google.generativeai as genai
                genai.configure(api_key=google_key)
                self.clients["google"] = genai
                self.logger.info("Google Gemini client initialized successfully.")
            else:
                self.logger.warning("Google API key not found.")
        except Exception as e:
            self.logger.error(f"Error initializing Google Gemini client: {str(e)}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        available = []
        for model_name, model_details in self.models.items():
            provider = model_details.provider
            if provider in self.clients:
                available.append(model_name)
        return available
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return list(self.clients.keys())
    
    def generate_text(self, 
                     prompt: str, 
                     system_message: Optional[str] = None,
                     model: Optional[str] = None,
                     max_tokens: Optional[int] = None,
                     temperature: float = 0.7,
                     fallback: bool = True) -> Tuple[str, Dict[str, Any]]:
        """
        Generate text using the selected model.
        
        Args:
            prompt: The user prompt
            system_message: Optional system message for models that support it
            model: Optional model override
            max_tokens: Maximum tokens to generate
            temperature: Creativity temperature (0.0 to 1.0)
            fallback: Whether to try fallback models if the selected model fails
            
        Returns:
            Tuple containing (generated_text, metadata)
        """
        model_name = model or self.preferred_model
        
        # Check if model is available
        if model_name not in self.models:
            self.logger.warning(f"Model {model_name} not found. Using {self.preferred_model}.")
            model_name = self.preferred_model
        
        model_details = self.models[model_name]
        provider = model_details.provider
        
        # Check if provider client is initialized
        if provider not in self.clients:
            error_msg = f"Provider {provider} client not initialized."
            self.logger.error(error_msg)
            
            if fallback:
                self.logger.info("Attempting to use fallback model.")
                return self._fallback_generate_text(prompt, system_message, max_tokens, temperature)
            else:
                return f"Error: {error_msg}", {"error": error_msg, "model": model_name}
        
        # Set max tokens if not specified
        if max_tokens is None:
            max_tokens = model_details.max_tokens // 2  # Use half the model's capacity by default
        
        # Generate text based on provider
        try:
            if provider == "openai":
                return self._generate_text_openai(model_name, prompt, system_message, max_tokens, temperature)
            elif provider == "anthropic":
                return self._generate_text_anthropic(model_name, prompt, system_message, max_tokens, temperature)
            elif provider == "perplexity":
                return self._generate_text_perplexity(model_name, prompt, system_message, max_tokens, temperature)
            elif provider == "deepseek":
                return self._generate_text_deepseek(model_name, prompt, system_message, max_tokens, temperature)
            elif provider == "google":
                return self._generate_text_google(model_name, prompt, system_message, max_tokens, temperature)
            else:
                error_msg = f"Provider {provider} not supported."
                self.logger.error(error_msg)
                
                if fallback:
                    self.logger.info("Attempting to use fallback model.")
                    return self._fallback_generate_text(prompt, system_message, max_tokens, temperature)
                else:
                    return f"Error: {error_msg}", {"error": error_msg, "model": model_name}
        
        except Exception as e:
            error_msg = f"Error generating text with {model_name}: {str(e)}"
            self.logger.error(error_msg)
            
            if fallback:
                self.logger.info("Attempting to use fallback model.")
                return self._fallback_generate_text(prompt, system_message, max_tokens, temperature)
            else:
                return f"Error: {error_msg}", {"error": error_msg, "model": model_name}
    
    def _fallback_generate_text(self, 
                              prompt: str, 
                              system_message: Optional[str] = None,
                              max_tokens: Optional[int] = None,
                              temperature: float = 0.7) -> Tuple[str, Dict[str, Any]]:
        """Try fallback models when primary model fails"""
        # Priority order for fallback
        fallback_models = [
            "gpt-3.5-turbo",     # OpenAI fallback
            "claude-3-sonnet-20240229",  # Anthropic fallback
            "perplexity-online-mistral",  # Perplexity fallback
            "deepseek-chat",     # DeepSeek fallback
            "gemini-pro"         # Google fallback
        ]
        
        # Try each fallback model
        for model_name in fallback_models:
            # Skip if this was the model that already failed
            if model_name == self.preferred_model:
                continue
                
            # Skip if model not available
            if model_name not in self.models:
                continue
                
            # Skip if provider not initialized
            provider = self.models[model_name].provider
            if provider not in self.clients:
                continue
            
            try:
                self.logger.info(f"Trying fallback model: {model_name}")
                if provider == "openai":
                    return self._generate_text_openai(model_name, prompt, system_message, max_tokens, temperature)
                elif provider == "anthropic":
                    return self._generate_text_anthropic(model_name, prompt, system_message, max_tokens, temperature)
                elif provider == "perplexity":
                    return self._generate_text_perplexity(model_name, prompt, system_message, max_tokens, temperature)
                elif provider == "deepseek":
                    return self._generate_text_deepseek(model_name, prompt, system_message, max_tokens, temperature)
                elif provider == "google":
                    return self._generate_text_google(model_name, prompt, system_message, max_tokens, temperature)
            except Exception as e:
                self.logger.warning(f"Fallback model {model_name} failed: {str(e)}")
                continue
        
        # If all fallbacks fail, return error
        error_msg = "All fallback models failed."
        self.logger.error(error_msg)
        return f"Error: {error_msg}", {"error": error_msg, "model": "fallback_failure"}
    
    def _generate_text_openai(self,
                             model_name: str,
                             prompt: str, 
                             system_message: Optional[str], 
                             max_tokens: Optional[int],
                             temperature: float) -> Tuple[str, Dict[str, Any]]:
        """Generate text using OpenAI models"""
        client = self.clients["openai"]
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        # Set default max_tokens if None
        if max_tokens is None:
            max_tokens = 1000
        
        start_time = time.time()
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        end_time = time.time()
        
        generated_text = response.choices[0].message.content
        
        # Extract metadata
        metadata = {
            "model": model_name,
            "provider": "openai",
            "latency": round(end_time - start_time, 2),
            "finish_reason": response.choices[0].finish_reason,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        return generated_text, metadata
    
    def _generate_text_anthropic(self,
                               model_name: str,
                               prompt: str, 
                               system_message: Optional[str], 
                               max_tokens: Optional[int],
                               temperature: float) -> Tuple[str, Dict[str, Any]]:
        """Generate text using Anthropic models"""
        client = self.clients["anthropic"]
        
        # Set default max_tokens if None
        if max_tokens is None:
            max_tokens = 1000
            
        start_time = time.time()
        
        # Anthropic's API expects system prompt and user message differently
        response = client.messages.create(
            model=model_name,
            system=system_message if system_message else None,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        end_time = time.time()
        
        # Extract content based on the structure
        generated_text = response.content[0].text
        
        # Extract metadata
        metadata = {
            "model": model_name,
            "provider": "anthropic",
            "latency": round(end_time - start_time, 2),
            "stop_reason": response.stop_reason,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        return generated_text, metadata
    
    def _generate_text_perplexity(self,
                                model_name: str,
                                prompt: str, 
                                system_message: Optional[str], 
                                max_tokens: Optional[int],
                                temperature: float) -> Tuple[str, Dict[str, Any]]:
        """Generate text using Perplexity models"""
        client = self.clients["perplexity"]
        
        # Convert model name to Perplexity format
        perplexity_model = model_name.replace("perplexity-", "")
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        # Set default max_tokens if None
        if max_tokens is None:
            max_tokens = 1000
            
        start_time = time.time()
        response = client.chat.completions.create(
            model=perplexity_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        end_time = time.time()
        
        generated_text = response.choices[0].message.content
        
        # Extract metadata
        metadata = {
            "model": model_name,
            "provider": "perplexity",
            "latency": round(end_time - start_time, 2),
            "finish_reason": response.choices[0].finish_reason,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        return generated_text, metadata
    
    def _generate_text_deepseek(self,
                              model_name: str,
                              prompt: str, 
                              system_message: Optional[str], 
                              max_tokens: Optional[int],
                              temperature: float) -> Tuple[str, Dict[str, Any]]:
        """Generate text using DeepSeek models"""
        client = self.clients["deepseek"]
        
        # Convert model name to DeepSeek format
        if model_name == "deepseek-coder":
            deepseek_model = "deepseek-coder:33b"
        elif model_name == "deepseek-chat":
            deepseek_model = "deepseek-chat"
        else:
            deepseek_model = model_name
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        # Set default max_tokens if None
        if max_tokens is None:
            max_tokens = 1000
            
        start_time = time.time()
        response = client.chat.completions.create(
            model=deepseek_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        end_time = time.time()
        
        generated_text = response.choices[0].message.content
        
        # Extract metadata
        metadata = {
            "model": model_name,
            "provider": "deepseek",
            "latency": round(end_time - start_time, 2),
            "finish_reason": response.choices[0].finish_reason,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        return generated_text, metadata
    
    def _generate_text_google(self,
                            model_name: str,
                            prompt: str, 
                            system_message: Optional[str], 
                            max_tokens: Optional[int],
                            temperature: float) -> Tuple[str, Dict[str, Any]]:
        """Generate text using Google Gemini models"""
        genai = self.clients["google"]
        
        # Convert model name to Gemini format
        if model_name == "gemini-pro":
            gemini_model = "gemini-pro"
        elif model_name == "gemini-pro-vision":
            gemini_model = "gemini-pro-vision"
        else:
            gemini_model = model_name
        
        # Initialize model
        model = genai.GenerativeModel(gemini_model)
        
        # Prepare content
        content = []
        if system_message:
            content.append({"role": "system", "parts": [system_message]})
        content.append({"role": "user", "parts": [prompt]})
        
        # Set generation config for max_tokens if provided
        generation_config = None
        if max_tokens is not None:
            generation_config = genai.GenerationConfig(max_output_tokens=max_tokens)
        
        # Generate response
        start_time = time.time()
        if generation_config:
            response = model.generate_content(content, generation_config=generation_config)
        else:
            response = model.generate_content(content)
        end_time = time.time()
        
        # Extract text
        generated_text = response.text
        
        # Extract metadata
        metadata = {
            "model": model_name,
            "provider": "google",
            "latency": round(end_time - start_time, 2),
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        return generated_text, metadata
    
    def analyze_with_multiple_models(self, 
                                    prompt: str, 
                                    system_message: Optional[str] = None,
                                    models: Optional[List[str]] = None,
                                    max_tokens: Optional[int] = None,
                                    temperature: float = 0.7) -> Dict[str, Any]:
        """
        Generate responses from multiple models and compare them.
        
        Args:
            prompt: The user prompt
            system_message: Optional system message
            models: List of models to use (uses all available if None)
            max_tokens: Maximum tokens per response
            temperature: Creativity temperature
            
        Returns:
            Dict with responses from each model and aggregated insights
        """
        # Use all available models if none specified
        if models is None:
            models = self.get_available_models()
        
        # Generate responses from each model
        responses = {}
        errors = {}
        
        for model_name in models:
            try:
                text, metadata = self.generate_text(
                    prompt=prompt,
                    system_message=system_message,
                    model=model_name,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    fallback=False  # Don't fallback when comparing models
                )
                
                responses[model_name] = {
                    "text": text,
                    "metadata": metadata
                }
            except Exception as e:
                errors[model_name] = str(e)
        
        # Return results
        return {
            "responses": responses,
            "errors": errors,
            "prompt": prompt,
            "system_message": system_message,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
    def get_domain_expert_response(self,
                                 query: str,
                                 domain: str,
                                 context: Optional[Dict[str, Any]] = None,
                                 model: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Get expert response for a domain-specific query.
        
        Args:
            query: The domain-specific query
            domain: The knowledge domain (tax_assessment, real_estate, etc.)
            context: Optional additional context
            model: Optional model to use
            
        Returns:
            Tuple containing (response_text, metadata)
        """
        # Prepare domain-specific prompt
        if domain == "tax_assessment":
            system_message = """You are a professional property tax assessor with extensive knowledge of assessment methodologies, 
            tax regulations, exemptions, and appeal processes. Your expertise includes market value, income, and cost approaches 
            to value. Provide detailed, accurate responses that would help property owners understand their assessments."""
        elif domain == "real_estate":
            system_message = """You are a real estate market expert with deep knowledge of property valuation, market trends, 
            investment analysis, and market indicators. You understand both residential and commercial real estate dynamics, 
            financing, and return metrics. Provide practical insights that would help investors and property owners make 
            informed decisions."""
        elif domain == "gis":
            system_message = """You are a Geographic Information Systems (GIS) specialist with expertise in spatial analysis, 
            map layers, coordinate systems, and property-related GIS applications. You understand how location factors 
            impact property values and how to analyze geographic data for real estate purposes. Provide technically 
            accurate but accessible explanations."""
        elif domain == "appraisal":
            system_message = """You are a licensed property appraiser with extensive experience in the sales comparison, 
            income, and cost approaches to value. You understand adjustment factors, capitalization rates, depreciation, 
            and valuation models. Provide professional insights that explain appraisal methodologies and considerations."""
        elif domain == "local_market":
            system_message = """You are a local market analyst specializing in neighborhood-level factors that influence 
            property values, including schools, crime, walkability, demographics, and economic indicators. You understand 
            how these factors interact and their relative impact on different property types. Provide nuanced analysis 
            of local market dynamics."""
        elif domain == "database":
            system_message = """You are a database architect specializing in real estate and property assessment databases. 
            You understand data modeling for property records, GIS integration, optimization techniques, and query patterns 
            for property data. Provide expert guidance on database design, performance, and best practices."""
        else:
            system_message = f"""You are a domain expert in {domain}. Provide accurate, helpful information 
            based on your specialized knowledge. Be specific, practical, and focus on actionable insights."""
        
        # Add context if provided
        prompt = query
        if context:
            context_str = "\n\nAdditional context:\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"
            prompt += context_str
        
        # Generate response
        return self.generate_text(
            prompt=prompt,
            system_message=system_message,
            model=model,
            temperature=0.3  # Use lower temperature for expert responses
        )