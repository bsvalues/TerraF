"""
AI Integration Agent

This module provides an agent for integrating with external AI services.
It handles service configuration, testing, prompt optimization, and failover.
"""

import os
import re
import json
import time
import random
import logging
from typing import Dict, List, Any, Optional, Union

# Import the simplified agent base
from simple_agent_base import Agent, AgentCategory

class AIIntegrationAgent(Agent):
    """
    Agent for integrating with external AI services.
    
    This agent handles:
    - Service configuration
    - Connection testing
    - Prompt optimization
    - Service failover implementation
    """
    
    def __init__(self, agent_id: str = "ai_integration_agent", 
                 capabilities: List[str] = None):
        """Initialize the AI Integration Agent"""
        if capabilities is None:
            capabilities = [
                "configure_service",
                "test_connection",
                "optimize_prompt",
                "implement_failover"
            ]
        
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentCategory.AI_INTEGRATION,
            capabilities=capabilities
        )
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Define available services
        self.available_services = {
            "openai": {
                "models": ["gpt-4o", "gpt-3.5-turbo"],
                "capabilities": ["text", "vision", "embedding"]
            },
            "anthropic": {
                "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
                "capabilities": ["text", "vision"]
            },
            "cohere": {
                "models": ["command", "command-light"],
                "capabilities": ["text", "embedding"]
            }
        }
        
    def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task assigned to this agent.
        
        Args:
            task: The task to execute
        
        Returns:
            Dict containing the result of the task execution
        """
        task_type = task.get("type", "unknown")
        result = {"status": "error", "message": f"Unknown task type: {task_type}"}
        
        # Implement task execution logic here
        if task_type == "configure_service":
            result = self.configure_service(task.get("service_name", ""), task.get("config", {}))
        elif task_type == "test_connection":
            result = self.test_connection(task.get("service_name", ""), task.get("model"))
        elif task_type == "optimize_prompt":
            result = self.optimize_prompt(
                task.get("service_name", ""), 
                task.get("model", ""), 
                task.get("original_prompt", "")
            )
        elif task_type == "implement_failover":
            result = self.implement_failover(
                task.get("primary_service", ""),
                task.get("backup_services", [])
            )
        
        return result
    
    def configure_service(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure an AI service with the provided settings.
        
        Args:
            service_name: Name of the service (e.g., "openai", "anthropic")
            config: Service configuration parameters
        
        Returns:
            Dict with configuration result
        """
        if service_name not in self.available_services:
            return {
                "success": False,
                "error": f"Service '{service_name}' not supported"
            }
        
        # In a real implementation, this would validate and store the config
        required_keys = ["api_key"]
        
        for key in required_keys:
            if key not in config:
                return {
                    "success": False,
                    "error": f"Missing required config key: {key}"
                }
        
        # Simulate successful configuration
        return {
            "success": True,
            "service": service_name,
            "config": {
                key: (value if key != "api_key" else "sk_...redacted") 
                for key, value in config.items()
            },
            "message": f"{service_name} service configured successfully"
        }
    
    def test_connection(self, service_name: str, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Test connection to an AI service.
        
        Args:
            service_name: Name of the service (e.g., "openai", "anthropic")
            model: Optional specific model to test
        
        Returns:
            Dict with test result
        """
        if service_name not in self.available_services:
            return {
                "success": False,
                "error": f"Service '{service_name}' not supported"
            }
        
        # If model not specified, use the first available model
        if model is None:
            model = self.available_services[service_name]["models"][0]
        elif model not in self.available_services[service_name]["models"]:
            return {
                "success": False,
                "error": f"Model '{model}' not available for service '{service_name}'"
            }
        
        # Simulate successful test
        return {
            "success": True,
            "service": service_name,
            "model": model,
            "response": f"This is a simulated test response from {service_name}'s {model} model.",
            "latency_ms": random.randint(100, 1000),
            "tokens": {
                "prompt": random.randint(5, 10),
                "completion": random.randint(10, 20),
                "total": random.randint(15, 30)
            }
        }
    
    def optimize_prompt(self, service_name: str, model: str, 
                       original_prompt: str) -> Dict[str, Any]:
        """
        Optimize a prompt for better results with a specific model.
        
        Args:
            service_name: Name of the service (e.g., "openai", "anthropic")
            model: Model to optimize for
            original_prompt: The original prompt to optimize
        
        Returns:
            Dict with optimized prompt and explanation
        """
        if service_name not in self.available_services:
            return {
                "success": False,
                "error": f"Service '{service_name}' not supported"
            }
        
        if model not in self.available_services[service_name]["models"]:
            return {
                "success": False,
                "error": f"Model '{model}' not available for service '{service_name}'"
            }
        
        # In a real implementation, this would use the model to generate an optimized prompt
        
        # For demo purposes, let's create a more structured prompt
        if "quantum computing" in original_prompt.lower():
            optimized_prompt = (
                "Explain the fundamental principles of quantum computing, including superposition and entanglement, "
                "and describe how these principles enable quantum computers to solve certain problems more efficiently "
                "than classical computers. Provide specific examples of quantum algorithms like Shor's algorithm and "
                "Grover's algorithm, and explain their advantages."
            )
            
            explanation = (
                "The optimized prompt is more specific and structured, guiding the model to provide a "
                "comprehensive yet focused explanation of quantum computing. It explicitly requests information "
                "about key concepts (superposition, entanglement) and specific algorithms, which will result in "
                "a more informative and useful response."
            )
            
            system_message = (
                "You are a quantum physics professor explaining concepts to a student with a strong background "
                "in computer science but limited knowledge of quantum mechanics. Focus on conceptual clarity "
                "while maintaining technical accuracy."
            )
        else:
            # Generic prompt enhancement
            optimized_prompt = (
                f"{original_prompt}\n\nPlease provide a comprehensive and well-structured response with concrete examples. "
                "Include relevant technical details, practical applications, and any important considerations or limitations."
            )
            
            explanation = (
                "The optimized prompt adds instructions for comprehensiveness, structure, and examples, "
                "which helps guide the model to provide a more useful and detailed response."
            )
            
            system_message = (
                "You are an expert providing clear, accurate, and comprehensive information. "
                "Structure your responses with logical organization, and support claims with evidence or examples."
            )
        
        # Simulate successful optimization
        return {
            "success": True,
            "service": service_name,
            "model": model,
            "original_prompt": original_prompt,
            "optimized_prompt": optimized_prompt,
            "explanation": explanation,
            "expected_impact": "The optimized prompt will likely result in a more detailed, organized, and technically accurate response.",
            "system_message": system_message,
            "additional_parameters": {
                "temperature": 0.3,
                "top_p": 0.9,
                "max_tokens": 800
            }
        }
    
    def implement_failover(self, primary_service: str, 
                          backup_services: List[str]) -> Dict[str, Any]:
        """
        Implement an AI service failover strategy.
        
        Args:
            primary_service: Name of the primary service
            backup_services: List of backup services to use on failure
        
        Returns:
            Dict with failover configuration and implementation
        """
        unsupported_services = [
            service for service in [primary_service] + backup_services 
            if service not in self.available_services
        ]
        
        if unsupported_services:
            return {
                "success": False,
                "error": f"Services not supported: {', '.join(unsupported_services)}"
            }
        
        if not backup_services:
            return {
                "success": False,
                "error": "At least one backup service must be specified"
            }
        
        # Create failover configuration
        failover_config = {
            "primary_service": primary_service,
            "backup_services": backup_services,
            "strategy": "sequential",
            "timeout": 10,
            "retry_attempts": 3
        }
        
        # Generate implementation code
        implementation_code = self._generate_failover_code(failover_config)
        
        # Return result
        return {
            "success": True,
            "failover_config": failover_config,
            "implementation_code": implementation_code,
            "message": f"Failover configuration generated successfully for {primary_service} with {len(backup_services)} backup services"
        }
    
    def _extract_prompt_from_text(self, text: str) -> str:
        """Extract optimized prompt from text"""
        prompt_match = re.search(r'(?:Optimized|Improved|Enhanced)\s+Prompt:?\s*(.*?)(?:$|\n\n)', text, re.IGNORECASE | re.DOTALL)
        if prompt_match:
            return prompt_match.group(1).strip()
        
        return ""
    
    def _extract_section(self, text: str, section_name: str, alternatives: List[str] = None) -> str:
        """Extract a specific section from text"""
        if alternatives is None:
            alternatives = []
        
        patterns = [re.escape(section_name)] + [re.escape(alt) for alt in alternatives]
        pattern = '|'.join(patterns)
        
        section_match = re.search(f'({pattern})s?:?\s*(.*?)(?:$|\n\n|\n#|\n##)', text, re.IGNORECASE | re.DOTALL)
        if section_match:
            return section_match.group(2).strip()
        
        return ""
    
    def _generate_failover_code(self, failover_config: Dict[str, Any]) -> str:
        """Generate code for implementing service failover"""
        primary_service = failover_config["primary_service"]
        backup_services = failover_config["backup_services"]
        strategy = failover_config["strategy"]
        timeout = failover_config["timeout"]
        retry_attempts = failover_config["retry_attempts"]
        
        # This is a simpler approach than the triple-quote approach that caused syntax issues
        code_lines = []
        
        # Imports
        code_lines.extend([
            "import os",
            "import random",
            "import logging",
            "from typing import Dict, List, Any",
            "import openai",
            "import anthropic",
            "import cohere",
            "",
            "class AIServiceFailover:",
            "    def __init__(self):",
            "        # Configure services",
            "        self.services = {",
            '            "openai": {',
            '                "api_key": os.environ.get("OPENAI_API_KEY"),',
            '                "model": "gpt-4o"',
            "            },",
            '            "anthropic": {',
            '                "api_key": os.environ.get("ANTHROPIC_API_KEY"),',
            '                "model": "claude-3-5-sonnet-20241022"',
            "            },",
            '            "cohere": {',
            '                "api_key": os.environ.get("COHERE_API_KEY"),',
            '                "model": "command-r"',
            "            }",
            "        }",
            "        ",
            "        # Failover configuration",
            f'        self.primary = "{primary_service}"',
            f'        self.backups = {backup_services}',
            f"        self.timeout = {timeout}",
            f"        self.max_retries = {retry_attempts}",
            "        ",
            "    def generate_text(self, prompt: str, **kwargs):",
            "        # Try primary service",
            "        try:",
            "            return self._call_openai(prompt, **kwargs)",
            "        except Exception as e:",
            '            logging.warning(f"Primary service failed: {str(e)}")',
            "        ",
            "        # Try backup services",
            "        for service in self.backups:",
            "            try:",
            '                if service == "anthropic":',
            "                    return self._call_anthropic(prompt, **kwargs)",
            '                elif service == "cohere":',
            "                    return self._call_cohere(prompt, **kwargs)",
            "            except Exception as e:",
            '                logging.warning(f"Backup service {service} failed: {str(e)}")',
            "                continue",
            "        ",
            "        # If all services fail",
            '        raise RuntimeError("All AI services failed")',
            "    ",
            "    def _call_openai(self, prompt: str, **kwargs):",
            "        # OpenAI implementation",
            '        openai.api_key = self.services["openai"]["api_key"]',
            "        ",
            "        response = openai.chat.completions.create(",
            '            model=kwargs.get("model", self.services["openai"]["model"]),',
            '            messages=[{"role": "user", "content": prompt}],',
            '            max_tokens=kwargs.get("max_tokens", 500),',
            '            temperature=kwargs.get("temperature", 0.7),',
            "            timeout=self.timeout",
            "        )",
            "        ",
            "        return {",
            '            "text": response.choices[0].message.content,',
            '            "service": "openai",',
            '            "model": kwargs.get("model", self.services["openai"]["model"])',
            "        }",
            "    ",
            "    def _call_anthropic(self, prompt: str, **kwargs):",
            "        # Anthropic implementation",
            '        client = anthropic.Anthropic(api_key=self.services["anthropic"]["api_key"])',
            "        ",
            "        response = client.messages.create(",
            '            model=kwargs.get("model", self.services["anthropic"]["model"]),',
            '            max_tokens=kwargs.get("max_tokens", 500),',
            '            temperature=kwargs.get("temperature", 0.7),',
            "            messages=[",
            '                {"role": "user", "content": prompt}',
            "            ]",
            "        )",
            "        ",
            "        return {",
            '            "text": response.content[0].text,',
            '            "service": "anthropic",',
            '            "model": kwargs.get("model", self.services["anthropic"]["model"])',
            "        }",
            "    ",
            "    def _call_cohere(self, prompt: str, **kwargs):",
            "        # Cohere implementation",
            '        client = cohere.Client(self.services["cohere"]["api_key"])',
            "        ",
            "        response = client.generate(",
            "            prompt=prompt,",
            '            model=kwargs.get("model", self.services["cohere"]["model"]),',
            '            max_tokens=kwargs.get("max_tokens", 500),',
            '            temperature=kwargs.get("temperature", 0.7)',
            "        )",
            "        ",
            "        return {",
            '            "text": response.generations[0].text,',
            '            "service": "cohere",',
            '            "model": kwargs.get("model", self.services["cohere"]["model"])',
            "        }"
        ])
        
        return "\n".join(code_lines)