"""
AI Integration Agent Module

This module implements a specialized agent for integrating with external AI services
such as OpenAI, Anthropic, and other LLM providers. The agent facilitates the configuration,
testing, and optimization of AI service connections in the TerraFusion platform.
"""

import os
import json
import re
import logging
import base64
from typing import Dict, List, Any, Optional, Union, Set, Tuple
import requests
from urllib.parse import urlparse

# Import base agent classes
from agent_base import (
    Agent, ModelInterface, Task, MessageType, 
    MessagePriority, AgentCategory
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIIntegrationAgent(Agent):
    """
    Agent that specializes in integrating with external AI services.
    
    Capabilities:
    - Configure AI service connections
    - Test API integrations
    - Optimize model parameters and prompts
    - Monitor usage and costs
    - Implement AI service failover
    """
    
    def __init__(self, agent_id: str = "ai_integration_agent", preferred_model: Optional[str] = None):
        capabilities = [
            "service_configuration",
            "api_testing",
            "prompt_optimization",
            "usage_monitoring",
            "failover_implementation"
        ]
        
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentCategory.INTEGRATION,
            capabilities=capabilities,
            preferred_model=preferred_model
        )
        
        # Supported AI services
        self.supported_services = {
            "openai": {
                "api_base": "https://api.openai.com/v1",
                "models": ["gpt-4o", "gpt-4", "gpt-3.5-turbo", "whisper-1", "dall-e-3"],
                "env_vars": ["OPENAI_API_KEY"],
                "config_keys": ["api_key", "organization", "api_base", "timeout"]
            },
            "anthropic": {
                "api_base": "https://api.anthropic.com",
                "models": ["claude-3-5-sonnet-20241022", "claude-3-sonnet-20240229", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
                "env_vars": ["ANTHROPIC_API_KEY"],
                "config_keys": ["api_key", "timeout"]
            },
            "huggingface": {
                "api_base": "https://api-inference.huggingface.co/models",
                "models": ["all-huggingface-models"],
                "env_vars": ["HUGGINGFACE_API_KEY"],
                "config_keys": ["api_key", "timeout"]
            },
            "cohere": {
                "api_base": "https://api.cohere.ai/v1",
                "models": ["command", "command-light", "command-r", "command-r-plus"],
                "env_vars": ["COHERE_API_KEY"],
                "config_keys": ["api_key", "timeout"]
            }
        }
        
        # Cache for tested configs
        self.tested_configs = {}
    
    def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute an AI integration task"""
        task_type = task.task_type
        
        if task_type == "configure_service":
            return self._configure_service(task)
        
        elif task_type == "test_connection":
            return self._test_connection(task)
        
        elif task_type == "optimize_prompt":
            return self._optimize_prompt(task)
        
        elif task_type == "monitor_usage":
            return self._monitor_usage(task)
        
        elif task_type == "implement_failover":
            return self._implement_failover(task)
        
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    def _configure_service(self, task: Task) -> Dict[str, Any]:
        """Configure an AI service connection"""
        service_name = task.input_data.get("service", "")
        config = task.input_data.get("config", {})
        check_env_vars = task.input_data.get("check_env_vars", True)
        
        if not service_name:
            return {"error": "Missing service name"}
        
        # Check if service is supported
        if service_name.lower() not in self.supported_services:
            return {
                "success": False,
                "error": f"Unsupported service: {service_name}",
                "supported_services": list(self.supported_services.keys())
            }
        
        service_info = self.supported_services[service_name.lower()]
        
        # Check environment variables if requested
        if check_env_vars:
            missing_env_vars = []
            for env_var in service_info["env_vars"]:
                if not os.environ.get(env_var):
                    missing_env_vars.append(env_var)
            
            if missing_env_vars:
                return {
                    "success": False,
                    "error": f"Missing environment variables: {', '.join(missing_env_vars)}",
                    "required_env_vars": service_info["env_vars"]
                }
        
        # Validate config
        validated_config = self._validate_service_config(service_name.lower(), config)
        
        if "error" in validated_config:
            return {
                "success": False,
                "error": validated_config["error"]
            }
        
        # Store validated config
        self._store_service_config(service_name.lower(), validated_config)
        
        return {
            "success": True,
            "service": service_name,
            "config": validated_config,
            "message": f"{service_name} service configured successfully"
        }
    
    def _test_connection(self, task: Task) -> Dict[str, Any]:
        """Test AI service connection"""
        service_name = task.input_data.get("service", "")
        config = task.input_data.get("config", {})
        model = task.input_data.get("model", "")
        test_prompt = task.input_data.get("prompt", "Hello, can you hear me?")
        
        if not service_name:
            return {"error": "Missing service name"}
        
        # Check if service is supported
        if service_name.lower() not in self.supported_services:
            return {
                "success": False,
                "error": f"Unsupported service: {service_name}",
                "supported_services": list(self.supported_services.keys())
            }
        
        service_info = self.supported_services[service_name.lower()]
        
        # If config is not provided, use stored config or environment variables
        if not config:
            config = self._get_service_config(service_name.lower())
            
            # If still no config, use environment variables
            if not config:
                config = {}
                for env_var in service_info["env_vars"]:
                    env_value = os.environ.get(env_var)
                    if env_value:
                        # Strip prefix and convert to lowercase
                        key = env_var.replace(f"{service_name.upper()}_", "").lower()
                        config[key] = env_value
        
        # Select default model if not specified
        if not model and service_info["models"]:
            model = service_info["models"][0]
        
        # Test connection
        result = self._make_test_request(service_name.lower(), config, model, test_prompt)
        
        # Cache successful config
        if result.get("success", False):
            self.tested_configs[service_name.lower()] = config
        
        return result
    
    def _optimize_prompt(self, task: Task) -> Dict[str, Any]:
        """Optimize prompts for AI services"""
        service_name = task.input_data.get("service", "")
        model = task.input_data.get("model", "")
        original_prompt = task.input_data.get("prompt", "")
        target_outcome = task.input_data.get("target_outcome", "")
        optimization_goal = task.input_data.get("optimization_goal", "quality")
        
        if not service_name or not original_prompt:
            return {"error": "Missing service name or prompt"}
        
        # Use the model to optimize the prompt
        model_interface = ModelInterface(capability="prompt_optimization")
        
        prompt = f"""
        Optimize this prompt for the {service_name} {model if model else 'AI'} service:
        
        Original prompt:
        ```
        {original_prompt}
        ```
        
        Target outcome:
        {target_outcome}
        
        Optimization goal: {optimization_goal}
        
        Provide:
        1. An optimized version of the prompt
        2. Explanation of improvements
        3. Expected impact on results
        4. Suggested system message (if applicable)
        5. Additional parameters to consider
        
        Format your response as JSON with these sections.
        """
        
        system_message = "You are an expert in prompt engineering for large language models. Optimize prompts to achieve the best possible results."
        
        optimization_result = model_interface.generate_text(prompt, system_message)
        
        # Extract structured information
        try:
            # Try to extract JSON if the model wrapped it in markdown
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', optimization_result, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                # Otherwise try to parse the whole text as JSON
                result = json.loads(optimization_result)
            
            return {
                "success": True,
                "service": service_name,
                "model": model,
                "original_prompt": original_prompt,
                "optimized_prompt": result.get("optimized_prompt"),
                "explanation": result.get("explanation"),
                "expected_impact": result.get("expected_impact"),
                "system_message": result.get("system_message", ""),
                "additional_parameters": result.get("additional_parameters", {})
            }
        except Exception as e:
            # If JSON parsing fails, extract information manually
            optimized_prompt = self._extract_optimized_prompt(optimization_result)
            
            return {
                "success": True,
                "service": service_name,
                "model": model,
                "original_prompt": original_prompt,
                "optimized_prompt": optimized_prompt,
                "explanation": self._extract_section(optimization_result, "explanation"),
                "raw_output": optimization_result,
                "parse_error": str(e)
            }
    
    def _monitor_usage(self, task: Task) -> Dict[str, Any]:
        """Monitor AI service usage and costs"""
        service_name = task.input_data.get("service", "")
        config = task.input_data.get("config", {})
        start_date = task.input_data.get("start_date", "")
        end_date = task.input_data.get("end_date", "")
        
        if not service_name:
            return {"error": "Missing service name"}
        
        # Placeholder for actual API calls to service usage endpoints
        # In a real implementation, this would make API calls to get usage data
        
        # For now, generate a simulated report
        model_interface = ModelInterface(capability="data_analysis")
        
        prompt = f"""
        Generate a simulated usage report for {service_name} AI service from {start_date if start_date else 'last month'} to {end_date if end_date else 'today'}.
        
        Include:
        1. Total number of API calls
        2. Tokens used (prompt and completion)
        3. Estimated cost
        4. Usage by model
        5. Usage patterns
        
        Make the data realistic but fictional. Format as JSON.
        """
        
        system_message = "You are a data analyst generating realistic but fictional usage reports for AI services."
        
        report_text = model_interface.generate_text(prompt, system_message)
        
        # Extract JSON from the response
        try:
            # Try to extract JSON if the model wrapped it in markdown
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', report_text, re.DOTALL)
            if json_match:
                report = json.loads(json_match.group(1))
            else:
                # Otherwise try to parse the whole text as JSON
                report = json.loads(report_text)
            
            return {
                "success": True,
                "service": service_name,
                "report": report,
                "note": "This is a simulated report for demonstration purposes. In a real implementation, this would fetch actual usage data from the service API."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse usage report: {str(e)}",
                "raw_output": report_text
            }
    
    def _implement_failover(self, task: Task) -> Dict[str, Any]:
        """Implement AI service failover configuration"""
        primary_service = task.input_data.get("primary_service", "")
        backup_services = task.input_data.get("backup_services", [])
        failover_strategy = task.input_data.get("strategy", "sequential")
        timeout = task.input_data.get("timeout", 10)
        retry_attempts = task.input_data.get("retry_attempts", 3)
        
        if not primary_service or not backup_services:
            return {"error": "Missing primary service or backup services"}
        
        # Check if services are supported
        unsupported_services = []
        services_to_check = [primary_service] + backup_services
        
        for service in services_to_check:
            if service.lower() not in self.supported_services:
                unsupported_services.append(service)
        
        if unsupported_services:
            return {
                "success": False,
                "error": f"Unsupported services: {', '.join(unsupported_services)}",
                "supported_services": list(self.supported_services.keys())
            }
        
        # Validate failover strategy
        valid_strategies = ["sequential", "random", "weighted", "parallel"]
        if failover_strategy not in valid_strategies:
            return {
                "success": False,
                "error": f"Invalid failover strategy: {failover_strategy}",
                "valid_strategies": valid_strategies
            }
        
        # Generate failover configuration
        failover_config = {
            "primary_service": primary_service,
            "backup_services": backup_services,
            "strategy": failover_strategy,
            "timeout": timeout,
            "retry_attempts": retry_attempts
        }
        
        # Generate failover implementation code
        implementation_code = self._generate_failover_code(failover_config)
        
        return {
            "success": True,
            "failover_config": failover_config,
            "implementation_code": implementation_code,
            "message": f"Failover configuration generated successfully for {primary_service} with {len(backup_services)} backup services"
        }
    
    def _validate_service_config(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate AI service configuration"""
        service_info = self.supported_services.get(service_name, {})
        required_keys = ["api_key"]
        
        # Check required keys
        for key in required_keys:
            if key not in config and key in service_info.get("config_keys", []):
                return {"error": f"Missing required configuration key: {key}"}
        
        # Add default values if missing
        validated_config = config.copy()
        
        # Add API base URL if not provided
        if "api_base" not in validated_config and "api_base" in service_info:
            validated_config["api_base"] = service_info["api_base"]
        
        # Add default timeout if not provided
        if "timeout" not in validated_config:
            validated_config["timeout"] = 30
        
        return validated_config
    
    def _store_service_config(self, service_name: str, config: Dict[str, Any]):
        """Store service configuration (in a real implementation, this would use secure storage)"""
        logger.info(f"Storing configuration for {service_name}")
        # In a real implementation, this would securely store the configuration
        # For now, we'll just store it in the agent's memory
        self.tested_configs[service_name] = config
    
    def _get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get stored service configuration"""
        return self.tested_configs.get(service_name, {})
    
    def _make_test_request(self, service_name: str, config: Dict[str, Any], model: str, prompt: str) -> Dict[str, Any]:
        """Make a test request to the AI service"""
        # This is a simulated test - in a real implementation, it would make actual API calls
        
        # Validate configuration
        if not config.get("api_key"):
            return {
                "success": False,
                "error": "API key not provided",
                "service": service_name,
                "model": model
            }
        
        # Simulate API call
        service_info = self.supported_services.get(service_name, {})
        
        # Check if model is supported
        if model not in service_info.get("models", []) and "all-huggingface-models" not in service_info.get("models", []):
            return {
                "success": False,
                "error": f"Model {model} not supported for {service_name}",
                "supported_models": service_info.get("models", [])
            }
        
        # Placeholder for actual API call
        # In a real implementation, this would make an API call to the service
        
        # Simulate successful response
        return {
            "success": True,
            "service": service_name,
            "model": model,
            "response": "This is a simulated test response. In a real implementation, this would be an actual response from the service API.",
            "latency_ms": 520,  # Simulated latency
            "tokens": {
                "prompt": len(prompt.split()),
                "completion": 15
            }
        }
    
    def _extract_optimized_prompt(self, text: str) -> str:
        """Extract optimized prompt from text"""
        # Try to find a section labeled as the optimized prompt
        optimized_section = self._extract_section(text, "optimized prompt", 
                                                 alternatives=["improved prompt", "enhanced prompt", "new prompt"])
        
        if optimized_section:
            return optimized_section
        
        # Look for text between triple backticks
        code_match = re.search(r'```(?:\w+)?\s*(.*?)\s*```', text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # If all else fails, return the text with "Optimized Prompt:" prefix removed
        prompt_match = re.search(r'(?:Optimized|Improved|Enhanced)\s+Prompt:?\s*(.*?)(?:$|\n\n)', text, re.IGNORECASE | re.DOTALL)
        if prompt_match:
            return prompt_match.group(1).strip()
        
        return ""
    
    def _extract_section(self, text: str, section_name: str, alternatives: List[str] = None) -> str:
        """Extract a specific section from text"""
        if alternatives is None:
            alternatives = []
        
        patterns = [section_name] + alternatives
        
        for pattern in patterns:
            section_pattern = rf'(?:{pattern}|{pattern.capitalize()})(?:[^\n]*)?:(.*?)(?:$|(?:\n\s*\n)|(?:\n\s*#)|(?:\n\s*\d+\.))'.replace(' ', r'\s+')
            section_match = re.search(section_pattern, text, re.IGNORECASE | re.DOTALL)
            
            if section_match:
                return section_match.group(1).strip()
        
        return ""
    
    def _generate_failover_code(self, failover_config: Dict[str, Any]) -> str:
        """Generate code for implementing service failover"""
        primary_service = failover_config["primary_service"]
        backup_services = failover_config["backup_services"]
        strategy = failover_config["strategy"]
        timeout = failover_config["timeout"]
        retry_attempts = failover_config["retry_attempts"]
        
        code = f"""
import os
import time
import random
import logging
from typing import Dict, List, Any, Optional, Union
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_service_failover")

class AIServiceFailover:
    """AI Service failover implementation"""
    
    def __init__(self):
        """Initialize the failover manager"""
        # Primary service configuration
        self.primary_service = "{primary_service}"
        
        # Backup services in priority order
        self.backup_services = {backup_services}
        
        # Failover strategy
        self.strategy = "{strategy}"
        
        # Request timeout in seconds
        self.timeout = {timeout}
        
        # Max retry attempts per service
        self.retry_attempts = {retry_attempts}
        
        # Service configurations
        self.service_configs = {{}}
        
        # Initialize services
        self._init_services()
    
    def _init_services(self):
        """Initialize service configurations from environment variables"""
        # Primary service
        self.service_configs[self.primary_service] = self._load_service_config(self.primary_service)
        
        # Backup services
        for service in self.backup_services:
            self.service_configs[service] = self._load_service_config(service)
    
    def _load_service_config(self, service_name: str) -> Dict[str, Any]:
        """Load service configuration from environment variables"""
        config = {{}}
        
        # Map of common environment variable patterns
        env_patterns = [
            f"{{service_name.upper()}}_API_KEY",
            f"{{service_name.upper()}}_KEY",
            f"{{service_name.upper()}}_SECRET"
        ]
        
        # Try each pattern
        for pattern in env_patterns:
            env_value = os.environ.get(pattern)
            if env_value:
                config["api_key"] = env_value
                break
        
        # Add specific config for different services
        if service_name.lower() == "openai":
            config["api_base"] = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
            config["model"] = os.environ.get("OPENAI_MODEL", "gpt-4o")
        
        elif service_name.lower() == "anthropic":
            config["api_base"] = os.environ.get("ANTHROPIC_API_BASE", "https://api.anthropic.com")
            config["model"] = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        
        elif service_name.lower() == "huggingface":
            config["api_base"] = os.environ.get("HUGGINGFACE_API_BASE", "https://api-inference.huggingface.co/models")
            config["model"] = os.environ.get("HUGGINGFACE_MODEL", "")
        
        elif service_name.lower() == "cohere":
            config["api_base"] = os.environ.get("COHERE_API_BASE", "https://api.cohere.ai/v1")
            config["model"] = os.environ.get("COHERE_MODEL", "command-r")
        
        return config
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def _call_service(self, service_name: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Make a call to a specific AI service"""
        config = self.service_configs.get(service_name, {{}})
        
        if not config.get("api_key"):
            raise ValueError(f"API key not found for {{service_name}}")
        
        # Service-specific API calls
        if service_name.lower() == "openai":
            return self._call_openai(config, prompt, **kwargs)
        
        elif service_name.lower() == "anthropic":
            return self._call_anthropic(config, prompt, **kwargs)
        
        elif service_name.lower() == "huggingface":
            return self._call_huggingface(config, prompt, **kwargs)
        
        elif service_name.lower() == "cohere":
            return self._call_cohere(config, prompt, **kwargs)
        
        else:
            raise ValueError(f"Unsupported service: {{service_name}}")
    
    def _call_openai(self, config: Dict[str, Any], prompt: str, **kwargs) -> Dict[str, Any]:
        """Call OpenAI API"""
        import openai
        
        openai.api_key = config["api_key"]
        if "api_base" in config:
            openai.api_base = config["api_base"]
        
        model = kwargs.get("model", config.get("model", "gpt-4o"))
        max_tokens = kwargs.get("max_tokens", 1000)
        temperature = kwargs.get("temperature", 0.7)
        
        try:
            response = openai.chat.completions.create(
                model=model,
                messages=[{{"role": "user", "content": prompt}}],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=self.timeout
            )
            
            return {{
                "success": True,
                "service": "openai",
                "model": model,
                "content": response.choices[0].message.content,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {{
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }}
            }}
        
        except Exception as e:
            logger.error(f"OpenAI API error: {{str(e)}}")
            raise
    
    def _call_anthropic(self, config: Dict[str, Any], prompt: str, **kwargs) -> Dict[str, Any]:
        """Call Anthropic API"""
        try:
            import anthropic
        except ImportError:
            raise ImportError("Anthropic package not installed. Install with: pip install anthropic")
        
        client = anthropic.Anthropic(api_key=config["api_key"])
        
        model = kwargs.get("model", config.get("model", "claude-3-5-sonnet-20241022"))
        max_tokens = kwargs.get("max_tokens", 1000)
        temperature = kwargs.get("temperature", 0.7)
        
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {{"role": "user", "content": prompt}}
                ]
            )
            
            return {{
                "success": True,
                "service": "anthropic",
                "model": model,
                "content": response.content[0].text,
                "finish_reason": response.stop_reason,
                "usage": {{
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }}
            }}
        
        except Exception as e:
            logger.error(f"Anthropic API error: {{str(e)}}")
            raise
    
    def _call_huggingface(self, config: Dict[str, Any], prompt: str, **kwargs) -> Dict[str, Any]:
        """Call Hugging Face API"""
        headers = {{"Authorization": f"Bearer {{config['api_key']}}"}}
        model = kwargs.get("model", config.get("model", ""))
        
        if not model:
            raise ValueError("Model name required for Hugging Face API")
        
        api_url = f"{{config['api_base']}}/{{model}}"
        
        try:
            response = requests.post(
                api_url,
                headers=headers,
                json={{"inputs": prompt}},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            return {{
                "success": True,
                "service": "huggingface",
                "model": model,
                "content": response.json()[0]["generated_text"],
                "raw_response": response.json()
            }}
        
        except Exception as e:
            logger.error(f"Hugging Face API error: {{str(e)}}")
            raise
    
    def _call_cohere(self, config: Dict[str, Any], prompt: str, **kwargs) -> Dict[str, Any]:
        """Call Cohere API"""
        headers = {{
            "Authorization": f"Bearer {{config['api_key']}}",
            "Content-Type": "application/json"
        }}
        
        model = kwargs.get("model", config.get("model", "command-r"))
        max_tokens = kwargs.get("max_tokens", 1000)
        temperature = kwargs.get("temperature", 0.7)
        
        api_url = f"{{config['api_base']}}/generate"
        
        try:
            response = requests.post(
                api_url,
                headers=headers,
                json={{
                    "model": model,
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }},
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            return {{
                "success": True,
                "service": "cohere",
                "model": model,
                "content": result["generations"][0]["text"],
                "finish_reason": result["generations"][0]["finish_reason"],
                "raw_response": result
            }}
        
        except Exception as e:
            logger.error(f"Cohere API error: {{str(e)}}")
            raise
    
    def call_with_failover(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Call AI services with failover support"""
        if self.strategy == "sequential":
            return self._sequential_failover(prompt, **kwargs)
        
        elif self.strategy == "random":
            return self._random_failover(prompt, **kwargs)
        
        elif self.strategy == "weighted":
            return self._weighted_failover(prompt, **kwargs)
        
        elif self.strategy == "parallel":
            return self._parallel_failover(prompt, **kwargs)
        
        else:
            raise ValueError(f"Unsupported failover strategy: {{self.strategy}}")
    
    def _sequential_failover(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Sequential failover strategy - try services in order"""
        # Try primary service first
        try:
            return self._call_service(self.primary_service, prompt, **kwargs)
        except Exception as e:
            logger.warning(f"Primary service {{self.primary_service}} failed: {{str(e)}}")
        
        # Try backup services in order
        for service in self.backup_services:
            try:
                result = self._call_service(service, prompt, **kwargs)
                logger.info(f"Failover to {{service}} successful")
                return result
            except Exception as e:
                logger.warning(f"Backup service {{service}} failed: {{str(e)}}")
                continue
        
        # If all services fail, raise an exception
        raise RuntimeError(f"All AI services failed for prompt: {{prompt[:50]}}...")
    
    def _random_failover(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Random failover strategy - try primary service then random backup services"""
        # Try primary service first
        try:
            return self._call_service(self.primary_service, prompt, **kwargs)
        except Exception as e:
            logger.warning(f"Primary service {{self.primary_service}} failed: {{str(e)}}")
        
        # Try backup services in random order
        backup_services = self.backup_services.copy()
        random.shuffle(backup_services)
        
        for service in backup_services:
            try:
                result = self._call_service(service, prompt, **kwargs)
                logger.info(f"Failover to {{service}} successful")
                return result
            except Exception as e:
                logger.warning(f"Backup service {{service}} failed: {{str(e)}}")
                continue
        
        # If all services fail, raise an exception
        raise RuntimeError(f"All AI services failed for prompt: {{prompt[:50]}}...")
    
    def _weighted_failover(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Weighted failover strategy - assign weights to backup services"""
        # Try primary service first
        try:
            return self._call_service(self.primary_service, prompt, **kwargs)
        except Exception as e:
            logger.warning(f"Primary service {{self.primary_service}} failed: {{str(e)}}")
        
        # Assign weights (earlier services have higher weights)
        weights = []
        for i, _ in enumerate(self.backup_services):
            weights.append(len(self.backup_services) - i)
        
        # Select service based on weights
        services_tried = set()
        
        for _ in range(len(self.backup_services)):
            # Select weighted random service that hasn't been tried yet
            available_services = [s for i, s in enumerate(self.backup_services) 
                                if s not in services_tried]
            available_weights = [w for i, w in enumerate(weights) 
                               if self.backup_services[i] not in services_tried]
            
            if not available_services:
                break
            
            service = random.choices(available_services, weights=available_weights, k=1)[0]
            services_tried.add(service)
            
            try:
                result = self._call_service(service, prompt, **kwargs)
                logger.info(f"Failover to {{service}} successful")
                return result
            except Exception as e:
                logger.warning(f"Backup service {{service}} failed: {{str(e)}}")
                continue
        
        # If all services fail, raise an exception
        raise RuntimeError(f"All AI services failed for prompt: {{prompt[:50]}}...")
    
    def _parallel_failover(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Parallel failover strategy - call all services simultaneously"""
        import concurrent.futures
        
        # Function to call a service and return the result or exception
        def call_service_safe(service):
            try:
                return self._call_service(service, prompt, **kwargs)
            except Exception as e:
                logger.warning(f"Service {{service}} failed: {{str(e)}}")
                return {{"success": False, "service": service, "error": str(e)}}
        
        # Call all services in parallel
        all_services = [self.primary_service] + self.backup_services
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(all_services)) as executor:
            future_to_service = {{executor.submit(call_service_safe, service): service 
                               for service in all_services}}
            
            for future in concurrent.futures.as_completed(future_to_service):
                service = future_to_service[future]
                try:
                    result = future.result()
                    results.append((service, result))
                except Exception as e:
                    logger.error(f"Unexpected error in parallel execution for {{service}}: {{str(e)}}")
        
        # Filter successful results
        successful_results = [(service, result) for service, result in results 
                            if result.get("success", False)]
        
        if not successful_results:
            raise RuntimeError(f"All AI services failed for prompt: {{prompt[:50]}}...")
        
        # Return the primary service result if successful, otherwise the first successful result
        primary_results = [result for service, result in successful_results 
                         if service == self.primary_service]
        
        if primary_results:
            return primary_results[0]
        else:
            return successful_results[0][1]

# Example usage
failover = AIServiceFailover()

# Example prompt
example_prompt = "Explain the concept of quantum computing in simple terms."

try:
    response = failover.call_with_failover(
        example_prompt,
        max_tokens=500,
        temperature=0.7
    )
    print(f"Response from {{response['service']}} ({{response['model']}}): {{response['content'][:100]}}...")
except Exception as e:
    print(f"All services failed: {{str(e)}}")
"""
        
        return code