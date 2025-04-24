"""
Documentation Agent Module

This module implements a specialized agent for generating and managing technical documentation.
The agent can create different types of documentation artifacts including API documentation,
user guides, system architecture, and developer onboarding materials.
"""

import os
import json
import re
import logging
from typing import Dict, List, Any, Optional, Union, Set, Tuple
import ast
import inspect

# Import base agent classes
from agent_base import (
    DocumentationAgent as BaseDocumentationAgent, ModelInterface, Task, MessageType, 
    MessagePriority, AgentCategory
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TechnicalDocumentationAgent(BaseDocumentationAgent):
    """
    Agent that specializes in generating and managing technical documentation.
    
    Capabilities:
    - Generate API documentation
    - Create user guides
    - Document system architecture
    - Produce developer onboarding materials
    - Maintain documentation consistency
    """
    
    def __init__(self, agent_id: str = "tech_doc_agent", preferred_model: Optional[str] = None):
        capabilities = [
            "api_documentation",
            "user_guide_creation",
            "architecture_documentation",
            "onboarding_materials",
            "documentation_maintenance"
        ]
        
        super().__init__(
            agent_id=agent_id,
            capabilities=capabilities,
            preferred_model=preferred_model
        )
        
        # Documentation formats
        self.doc_formats = {
            "markdown": {
                "extension": ".md",
                "header_prefix": "#",
                "code_block": "```"
            },
            "restructuredtext": {
                "extension": ".rst",
                "header_prefix": "=",
                "code_block": "::"
            },
            "html": {
                "extension": ".html",
                "header_prefix": "<h",
                "code_block": "<pre><code>"
            },
            "asciidoc": {
                "extension": ".adoc",
                "header_prefix": "=",
                "code_block": "----"
            }
        }
        
        # Documentation generators by language
        self.doc_generators = {
            "python": ["sphinx", "pdoc", "mkdocs"],
            "javascript": ["jsdoc", "typedoc", "docsify"],
            "typescript": ["typedoc", "tsdoc", "docsify"],
            "java": ["javadoc", "dokka"],
            "csharp": ["docfx", "sandcastle"],
            "go": ["godoc", "pkgsite"],
            "ruby": ["yard", "rdoc"],
            "php": ["phpDocumentor", "apigen"]
        }
    
    def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a documentation task"""
        task_type = task.task_type
        
        if task_type == "generate_api_docs":
            return self._generate_api_docs(task)
        
        elif task_type == "create_user_guide":
            return self._create_user_guide(task)
        
        elif task_type == "document_architecture":
            return self._document_architecture(task)
        
        elif task_type == "create_onboarding_docs":
            return self._create_onboarding_docs(task)
        
        elif task_type == "assess_documentation":
            return self._assess_documentation(task)
        
        elif task_type == "generate_readme":
            return self._generate_readme(task)
        
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    def _generate_api_docs(self, task: Task) -> Dict[str, Any]:
        """Generate API documentation from code and specifications"""
        code_files = task.input_data.get("code_files", {})
        api_specs = task.input_data.get("api_specs", {})
        language = task.input_data.get("language", "python")
        doc_format = task.input_data.get("format", "markdown")
        
        if not code_files and not api_specs:
            return {"error": "Missing code files or API specifications"}
        
        # Initialize documentation
        api_docs = {}
        
        # Process API specifications if available
        if api_specs:
            api_docs = self._process_api_specs(api_specs, doc_format)
        
        # Process code files if available
        if code_files:
            code_docs = self._extract_docs_from_code(code_files, language, doc_format)
            
            # Merge with API specs docs
            for endpoint, doc in code_docs.items():
                if endpoint in api_docs:
                    # Enhance existing docs with code details
                    api_docs[endpoint].update(doc)
                else:
                    # Add new endpoint documentation
                    api_docs[endpoint] = doc
        
        # Use model to enhance documentation
        if api_docs:
            enhanced_docs = self._enhance_api_docs(api_docs, language, doc_format)
            return {
                "documentation": enhanced_docs,
                "format": doc_format,
                "language": language,
                "endpoint_count": len(enhanced_docs)
            }
        else:
            return {"error": "Failed to generate API documentation"}
    
    def _create_user_guide(self, task: Task) -> Dict[str, Any]:
        """Create user guide documentation"""
        features = task.input_data.get("features", [])
        app_name = task.input_data.get("app_name", "")
        screenshots = task.input_data.get("screenshots", {})
        audience = task.input_data.get("audience", "end-user")
        doc_format = task.input_data.get("format", "markdown")
        
        if not features or not app_name:
            return {"error": "Missing features or application name"}
        
        # Use the model to generate user guide
        model = ModelInterface(capability="content_generation")
        
        prompt = f"""
        Create a comprehensive user guide for '{app_name}' with these features:
        
        Features:
        {json.dumps(features, indent=2)}
        
        Target audience: {audience}
        
        The guide should include:
        1. Introduction
        2. Getting Started
        3. Feature overviews with step-by-step instructions
        4. Troubleshooting section
        5. FAQ
        
        Format the guide in {doc_format}.
        """
        
        system_message = f"You are an expert technical writer who creates clear, concise, and helpful user documentation for {audience} audiences."
        
        user_guide = model.generate_text(prompt, system_message)
        
        # If screenshots are available, insert references
        if screenshots:
            user_guide = self._insert_screenshot_references(user_guide, screenshots, doc_format)
        
        # Process the guide into sections for easier consumption
        guide_sections = self._split_into_sections(user_guide, doc_format)
        
        return {
            "user_guide": user_guide,
            "sections": guide_sections,
            "format": doc_format,
            "app_name": app_name,
            "audience": audience
        }
    
    def _document_architecture(self, task: Task) -> Dict[str, Any]:
        """Document system architecture"""
        components = task.input_data.get("components", [])
        relationships = task.input_data.get("relationships", [])
        system_name = task.input_data.get("system_name", "")
        tech_stack = task.input_data.get("tech_stack", {})
        doc_format = task.input_data.get("format", "markdown")
        include_diagrams = task.input_data.get("include_diagrams", True)
        
        if not components or not system_name:
            return {"error": "Missing components or system name"}
        
        # Use the model to generate architecture documentation
        model = ModelInterface(capability="content_generation")
        
        prompt = f"""
        Create comprehensive architecture documentation for '{system_name}' with these components:
        
        Components:
        {json.dumps(components, indent=2)}
        
        Component Relationships:
        {json.dumps(relationships, indent=2)}
        
        Technology Stack:
        {json.dumps(tech_stack, indent=2)}
        
        Include:
        1. System Overview
        2. Architecture Principles
        3. Component Descriptions
        4. Component Relationships
        5. Data Flow
        6. Deployment Architecture
        7. Security Considerations
        
        Format the documentation in {doc_format}.
        """
        
        if include_diagrams:
            prompt += "\n\nInclude PlantUML or Mermaid diagram code for visualizing the architecture."
        
        system_message = "You are an expert software architect who creates clear, thorough, and technically accurate architecture documentation."
        
        architecture_doc = model.generate_text(prompt, system_message)
        
        # Extract diagrams if requested
        diagrams = {}
        if include_diagrams:
            diagrams = self._extract_diagrams(architecture_doc)
        
        # Process the document into sections
        doc_sections = self._split_into_sections(architecture_doc, doc_format)
        
        return {
            "architecture_doc": architecture_doc,
            "sections": doc_sections,
            "diagrams": diagrams,
            "format": doc_format,
            "system_name": system_name
        }
    
    def _create_onboarding_docs(self, task: Task) -> Dict[str, Any]:
        """Create developer onboarding documentation"""
        setup_steps = task.input_data.get("setup_steps", [])
        codebase_overview = task.input_data.get("codebase_overview", {})
        project_name = task.input_data.get("project_name", "")
        workflows = task.input_data.get("workflows", [])
        doc_format = task.input_data.get("format", "markdown")
        
        if not project_name:
            return {"error": "Missing project name"}
        
        # Use the model to generate onboarding documentation
        model = ModelInterface(capability="content_generation")
        
        prompt = f"""
        Create comprehensive developer onboarding documentation for '{project_name}' that includes:
        
        Setup Steps:
        {json.dumps(setup_steps, indent=2) if setup_steps else "Not provided"}
        
        Codebase Overview:
        {json.dumps(codebase_overview, indent=2) if codebase_overview else "Not provided"}
        
        Development Workflows:
        {json.dumps(workflows, indent=2) if workflows else "Not provided"}
        
        Include:
        1. Welcome and Introduction
        2. Development Environment Setup
        3. Codebase Structure and Navigation
        4. Key Concepts and Patterns
        5. Development Workflow
        6. Testing Guidelines
        7. Contribution Guidelines
        8. Resources and Further Reading
        
        Format the documentation in {doc_format}.
        """
        
        system_message = "You are an expert developer who creates clear, thorough, and helpful onboarding documentation for new team members."
        
        onboarding_doc = model.generate_text(prompt, system_message)
        
        # Process the document into sections
        doc_sections = self._split_into_sections(onboarding_doc, doc_format)
        
        # Generate quick reference guide
        quick_reference = self._generate_quick_reference(doc_sections, project_name, doc_format)
        
        return {
            "onboarding_doc": onboarding_doc,
            "sections": doc_sections,
            "quick_reference": quick_reference,
            "format": doc_format,
            "project_name": project_name
        }
    
    def _assess_documentation(self, task: Task) -> Dict[str, Any]:
        """Assess documentation quality and coverage"""
        docs = task.input_data.get("docs", {})
        codebase = task.input_data.get("codebase", {})
        project_name = task.input_data.get("project_name", "")
        
        if not docs:
            return {"error": "Missing documentation to assess"}
        
        # Initialize assessment metrics
        assessment = {
            "overall_score": 0,
            "coverage": 0,
            "clarity": 0,
            "completeness": 0,
            "accuracy": 0,
            "gaps": [],
            "recommendations": []
        }
        
        # Use the model to assess documentation
        model = ModelInterface(capability="content_analysis")
        
        prompt = f"""
        Assess the documentation quality for '{project_name}':
        
        Documentation:
        {json.dumps(docs, indent=2)}
        
        Codebase Info:
        {json.dumps(codebase, indent=2) if codebase else "Not provided"}
        
        Provide:
        1. Overall assessment score (0-100)
        2. Coverage score (0-100)
        3. Clarity score (0-100)
        4. Completeness score (0-100)
        5. Accuracy score (0-100)
        6. Documentation gaps
        7. Improvement recommendations
        
        Format your response as JSON with these metrics.
        """
        
        system_message = "You are an expert in technical documentation standards and best practices. Provide objective assessments with actionable recommendations."
        
        assessment_text = model.generate_text(prompt, system_message)
        
        # Extract JSON from the response
        try:
            # Try to extract JSON if the model wrapped it in markdown
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', assessment_text, re.DOTALL)
            if json_match:
                assessment = json.loads(json_match.group(1))
            else:
                # Otherwise try to parse the whole text as JSON
                assessment = json.loads(assessment_text)
        except Exception as e:
            # If parsing fails, extract metrics manually
            assessment = {
                "overall_score": self._extract_score(assessment_text, "overall"),
                "coverage": self._extract_score(assessment_text, "coverage"),
                "clarity": self._extract_score(assessment_text, "clarity"),
                "completeness": self._extract_score(assessment_text, "completeness"),
                "accuracy": self._extract_score(assessment_text, "accuracy"),
                "gaps": self._extract_list_items(assessment_text, "gaps"),
                "recommendations": self._extract_list_items(assessment_text, "recommendations")
            }
        
        return assessment
    
    def _generate_readme(self, task: Task) -> Dict[str, Any]:
        """Generate a README file for a project"""
        project_name = task.input_data.get("project_name", "")
        project_description = task.input_data.get("description", "")
        features = task.input_data.get("features", [])
        installation = task.input_data.get("installation", [])
        usage = task.input_data.get("usage", [])
        tech_stack = task.input_data.get("tech_stack", [])
        contributing = task.input_data.get("contributing", "")
        license_info = task.input_data.get("license", "")
        doc_format = task.input_data.get("format", "markdown")
        
        if not project_name:
            return {"error": "Missing project name"}
        
        # Use the model to generate README
        model = ModelInterface(capability="content_generation")
        
        prompt = f"""
        Create a comprehensive README for '{project_name}':
        
        Project Description:
        {project_description}
        
        Features:
        {json.dumps(features, indent=2) if features else "Not provided"}
        
        Installation:
        {json.dumps(installation, indent=2) if installation else "Not provided"}
        
        Usage:
        {json.dumps(usage, indent=2) if usage else "Not provided"}
        
        Technology Stack:
        {json.dumps(tech_stack, indent=2) if tech_stack else "Not provided"}
        
        Contributing:
        {contributing}
        
        License:
        {license_info}
        
        Include:
        1. Project title and badges
        2. Brief description
        3. Features
        4. Installation steps
        5. Usage examples
        6. API Reference (if applicable)
        7. Contributing guidelines
        8. License information
        9. Acknowledgments (if applicable)
        
        Format the README in {doc_format}.
        """
        
        system_message = "You are an expert developer who creates clear, informative, and engaging README files for software projects."
        
        readme = model.generate_text(prompt, system_message)
        
        return {
            "readme": readme,
            "format": doc_format,
            "project_name": project_name,
            "sections": self._split_into_sections(readme, doc_format)
        }
    
    def _process_api_specs(self, api_specs: Dict[str, Any], doc_format: str) -> Dict[str, Any]:
        """Process API specifications into documentation"""
        api_docs = {}
        
        for endpoint, spec in api_specs.items():
            # Extract relevant information
            method = spec.get("method", "GET")
            description = spec.get("description", "")
            params = spec.get("parameters", [])
            responses = spec.get("responses", {})
            
            # Create documentation for this endpoint
            api_docs[endpoint] = {
                "method": method,
                "description": description,
                "parameters": params,
                "responses": responses,
                "examples": spec.get("examples", [])
            }
        
        return api_docs
    
    def _extract_docs_from_code(self, code_files: Dict[str, str], language: str, doc_format: str) -> Dict[str, Any]:
        """Extract API documentation from code files"""
        docs = {}
        
        # Process each code file
        for file_path, code in code_files.items():
            if language == "python":
                file_docs = self._extract_python_docs(file_path, code)
            elif language in ["javascript", "typescript"]:
                file_docs = self._extract_js_docs(file_path, code)
            else:
                # Default extractor
                file_docs = self._extract_generic_docs(file_path, code, language)
            
            # Add to overall documentation
            docs.update(file_docs)
        
        return docs
    
    def _extract_python_docs(self, file_path: str, code: str) -> Dict[str, Any]:
        """Extract API documentation from Python code"""
        docs = {}
        
        try:
            # Parse Python code
            tree = ast.parse(code)
            
            # Extract classes and functions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_name = node.name
                    # Extract class docstring
                    class_doc = ast.get_docstring(node) or ""
                    
                    # Process methods
                    for method in [n for n in node.body if isinstance(n, ast.FunctionDef)]:
                        method_name = method.name
                        method_doc = ast.get_docstring(method) or ""
                        
                        # Create endpoint key (for API-like classes)
                        endpoint_key = f"{class_name}.{method_name}"
                        
                        # Extract parameters
                        params = []
                        for arg in method.args.args:
                            if arg.arg != "self":
                                param_info = {"name": arg.arg}
                                # Extract type annotation if available
                                if arg.annotation:
                                    param_info["type"] = self._get_annotation_name(arg.annotation)
                                params.append(param_info)
                        
                        # Extract return type
                        returns = {}
                        if method.returns:
                            returns["type"] = self._get_annotation_name(method.returns)
                        
                        # Add to documentation
                        docs[endpoint_key] = {
                            "description": method_doc,
                            "parameters": params,
                            "returns": returns,
                            "source_file": file_path
                        }
                
                elif isinstance(node, ast.FunctionDef) and node.parent_field != 'body':
                    func_name = node.name
                    func_doc = ast.get_docstring(node) or ""
                    
                    # Create endpoint key
                    endpoint_key = func_name
                    
                    # Extract parameters
                    params = []
                    for arg in node.args.args:
                        param_info = {"name": arg.arg}
                        # Extract type annotation if available
                        if arg.annotation:
                            param_info["type"] = self._get_annotation_name(arg.annotation)
                        params.append(param_info)
                    
                    # Extract return type
                    returns = {}
                    if node.returns:
                        returns["type"] = self._get_annotation_name(node.returns)
                    
                    # Add to documentation
                    docs[endpoint_key] = {
                        "description": func_doc,
                        "parameters": params,
                        "returns": returns,
                        "source_file": file_path
                    }
        
        except SyntaxError:
            logger.error(f"Syntax error in Python file: {file_path}")
        except Exception as e:
            logger.error(f"Error extracting docs from {file_path}: {str(e)}")
        
        return docs
    
    def _get_annotation_name(self, annotation):
        """Get the name of a type annotation"""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Subscript):
            if isinstance(annotation.value, ast.Name):
                return f"{annotation.value.id}[...]"
            return "complex_type"
        elif isinstance(annotation, ast.Attribute):
            return f"{self._get_annotation_name(annotation.value)}.{annotation.attr}"
        return "unknown_type"
    
    def _extract_js_docs(self, file_path: str, code: str) -> Dict[str, Any]:
        """Extract API documentation from JavaScript/TypeScript code"""
        docs = {}
        
        # Simple regex-based parsing for JS/TS functions and methods
        # Class or function pattern
        class_pattern = r'(?:export\s+)?class\s+(\w+)'
        function_pattern = r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\((.*?)\)'
        method_pattern = r'(?:async\s+)?(\w+)\s*\((.*?)\)(?:\s*:\s*([^{]+))?'
        
        # JSDoc pattern
        jsdoc_pattern = r'/\*\*(.*?)\*/'
        
        # Find classes
        class_matches = re.finditer(class_pattern, code, re.DOTALL)
        for class_match in class_matches:
            class_name = class_match.group(1)
            class_start = class_match.start()
            
            # Look for class JSDoc
            class_doc = ""
            jsdoc_match = re.search(jsdoc_pattern, code[:class_start], re.DOTALL)
            if jsdoc_match and jsdoc_match.end() > class_start - 20:  # Close enough to be the class doc
                class_doc = jsdoc_match.group(1)
            
            # Extract class methods
            class_code = self._find_matching_braces(code[class_start:])
            method_matches = re.finditer(method_pattern, class_code, re.DOTALL)
            
            for method_match in method_matches:
                method_name = method_match.group(1)
                if method_name in ['constructor', 'get', 'set']:
                    continue  # Skip special methods
                
                params_str = method_match.group(2)
                return_type = method_match.group(3) if len(method_match.groups()) > 2 else None
                
                # Parse parameters
                params = self._parse_js_params(params_str)
                
                # Find method JSDoc
                method_start = method_match.start()
                method_doc = ""
                jsdoc_match = re.search(jsdoc_pattern, class_code[:method_start], re.DOTALL)
                if jsdoc_match and jsdoc_match.end() > method_start - 20:  # Close enough to be the method doc
                    method_doc = jsdoc_match.group(1)
                
                # Create endpoint key
                endpoint_key = f"{class_name}.{method_name}"
                
                # Add to documentation
                docs[endpoint_key] = {
                    "description": method_doc.strip(),
                    "parameters": params,
                    "returns": {"type": return_type.strip() if return_type else "void"},
                    "source_file": file_path
                }
        
        # Find standalone functions
        function_matches = re.finditer(function_pattern, code, re.DOTALL)
        for function_match in function_matches:
            func_name = function_match.group(1)
            params_str = function_match.group(2)
            
            # Parse parameters
            params = self._parse_js_params(params_str)
            
            # Find function JSDoc
            func_start = function_match.start()
            func_doc = ""
            jsdoc_match = re.search(jsdoc_pattern, code[:func_start], re.DOTALL)
            if jsdoc_match and jsdoc_match.end() > func_start - 20:  # Close enough to be the function doc
                func_doc = jsdoc_match.group(1)
            
            # Create endpoint key
            endpoint_key = func_name
            
            # Add to documentation
            docs[endpoint_key] = {
                "description": func_doc.strip(),
                "parameters": params,
                "returns": {"type": self._extract_js_return_type(func_doc)},
                "source_file": file_path
            }
        
        return docs
    
    def _parse_js_params(self, params_str: str) -> List[Dict[str, str]]:
        """Parse JavaScript function parameters"""
        if not params_str.strip():
            return []
        
        params = []
        param_parts = []
        
        # Handle nested structures like arrays or objects in parameters
        brace_count = 0
        square_count = 0
        current_part = ""
        
        for char in params_str:
            if char == ',' and brace_count == 0 and square_count == 0:
                param_parts.append(current_part.strip())
                current_part = ""
            else:
                current_part += char
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                elif char == '[':
                    square_count += 1
                elif char == ']':
                    square_count -= 1
        
        if current_part.strip():
            param_parts.append(current_part.strip())
        
        # Process each parameter
        for part in param_parts:
            param_info = {"name": part}
            
            # Extract type if available (TypeScript)
            type_match = re.search(r'(\w+)\s*:\s*([^=]+)', part)
            if type_match:
                param_info["name"] = type_match.group(1)
                param_info["type"] = type_match.group(2).strip()
            
            # Check for default value
            default_match = re.search(r'=\s*(.+)$', part)
            if default_match:
                param_info["default"] = default_match.group(1).strip()
            
            params.append(param_info)
        
        return params
    
    def _extract_js_return_type(self, jsdoc: str) -> str:
        """Extract return type from JSDoc comment"""
        return_match = re.search(r'@returns?\s+{(.+?)}', jsdoc)
        if return_match:
            return return_match.group(1).strip()
        return "any"
    
    def _find_matching_braces(self, text: str) -> str:
        """Find text between matching braces"""
        brace_count = 0
        start_found = False
        result = ""
        
        for i, char in enumerate(text):
            if char == '{':
                brace_count += 1
                start_found = True
            elif char == '}':
                brace_count -= 1
            
            if start_found:
                result += char
                
                if brace_count == 0:
                    break
        
        return result
    
    def _extract_generic_docs(self, file_path: str, code: str, language: str) -> Dict[str, Any]:
        """Generic documentation extractor for unsupported languages"""
        docs = {}
        
        # Look for function-like patterns
        function_pattern = r'(?:public\s+|private\s+|protected\s+|static\s+)*(?:function|def|func)\s+(\w+)\s*\((.*?)\)'
        method_pattern = r'(?:public\s+|private\s+|protected\s+|static\s+)*(?:function|def|func)\s+(\w+)\s*\((.*?)\)'
        
        # Find functions/methods
        function_matches = re.finditer(function_pattern, code, re.DOTALL)
        for func_match in function_matches:
            func_name = func_match.group(1)
            params_str = func_match.group(2)
            
            # Simple parameter parsing
            params = []
            if params_str.strip():
                param_parts = params_str.split(',')
                for part in param_parts:
                    params.append({"name": part.strip()})
            
            # Look for documentation comments
            func_pos = func_match.start()
            func_doc = ""
            
            # Look back for a comment
            comment_search = code[:func_pos].strip()
            if language in ["java", "csharp", "javascript", "typescript", "php"]:
                # Multi-line comment style
                doc_match = re.search(r'/\*\*(.*?)\*/', comment_search[::-1], re.DOTALL)
                if doc_match:
                    func_doc = doc_match.group(1)[::-1].strip()
            elif language in ["python", "ruby"]:
                # Python docstring or Ruby comment
                doc_match = re.search(r'"""(.*?)"""', comment_search[::-1], re.DOTALL)
                if doc_match:
                    func_doc = doc_match.group(1)[::-1].strip()
                else:
                    # Look for hash comments
                    lines = comment_search.split('\n')
                    doc_lines = []
                    for line in reversed(lines):
                        if line.strip().startswith('#'):
                            doc_lines.append(line.strip()[1:].strip())
                        else:
                            break
                    func_doc = '\n'.join(reversed(doc_lines))
            
            # Create endpoint key
            endpoint_key = func_name
            
            # Add to documentation
            docs[endpoint_key] = {
                "description": func_doc,
                "parameters": params,
                "source_file": file_path
            }
        
        return docs
    
    def _enhance_api_docs(self, api_docs: Dict[str, Any], language: str, doc_format: str) -> Dict[str, Any]:
        """Enhance API documentation with model-generated content"""
        enhanced_docs = {}
        
        # Use the model to enhance each endpoint's documentation
        model = ModelInterface(capability="content_generation")
        
        for endpoint, doc in api_docs.items():
            # Build prompt for enhancing this endpoint's docs
            prompt = f"""
            Enhance the documentation for this API endpoint:
            
            Endpoint: {endpoint}
            Language: {language}
            
            Current Documentation:
            {json.dumps(doc, indent=2)}
            
            Improve the description, add examples, and clarify parameter descriptions.
            Format the output as JSON following the same structure as the input.
            """
            
            system_message = "You are an expert API documentation writer who creates clear, thorough, and technically accurate documentation."
            
            enhanced_text = model.generate_text(prompt, system_message)
            
            # Extract enhanced documentation
            try:
                # Try to extract JSON if the model wrapped it in markdown
                json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', enhanced_text, re.DOTALL)
                if json_match:
                    enhanced_doc = json.loads(json_match.group(1))
                else:
                    # Otherwise try to parse the whole text as JSON
                    enhanced_doc = json.loads(enhanced_text)
                
                # Add the enhanced documentation
                enhanced_docs[endpoint] = enhanced_doc
            except Exception as e:
                logger.error(f"Error parsing enhanced documentation for {endpoint}: {str(e)}")
                # Fallback to original documentation
                enhanced_docs[endpoint] = doc
        
        return enhanced_docs
    
    def _insert_screenshot_references(self, user_guide: str, screenshots: Dict[str, str], doc_format: str) -> str:
        """Insert screenshot references into user guide"""
        format_info = self.doc_formats.get(doc_format, self.doc_formats["markdown"])
        
        for screenshot_id, screenshot_path in screenshots.items():
            # Create reference based on format
            if doc_format == "markdown":
                ref = f"![{screenshot_id}]({screenshot_path})"
            elif doc_format == "restructuredtext":
                ref = f".. image:: {screenshot_path}\n   :alt: {screenshot_id}"
            elif doc_format == "html":
                ref = f'<img src="{screenshot_path}" alt="{screenshot_id}" />'
            elif doc_format == "asciidoc":
                ref = f"image::{screenshot_path}[{screenshot_id}]"
            else:
                ref = f"[Screenshot: {screenshot_id}]"
            
            # Insert reference in relevant section
            pattern = fr"(?i){re.escape(screenshot_id)}.*?(?:image|screenshot|figure)"
            match = re.search(pattern, user_guide)
            if match:
                # Insert after the found mention
                pos = match.end()
                user_guide = user_guide[:pos] + "\n\n" + ref + "\n\n" + user_guide[pos:]
        
        return user_guide
    
    def _split_into_sections(self, document: str, doc_format: str) -> Dict[str, str]:
        """Split document into sections based on headers"""
        sections = {}
        format_info = self.doc_formats.get(doc_format, self.doc_formats["markdown"])
        
        if doc_format == "markdown":
            # Split by markdown headers
            pattern = r'^(#+)\s+(.+?)$'
            matches = re.finditer(pattern, document, re.MULTILINE)
            
            last_pos = 0
            current_section = "Introduction"
            sections[current_section] = ""
            
            for match in matches:
                # Add content to current section
                section_content = document[last_pos:match.start()].strip()
                if section_content:
                    sections[current_section] += section_content
                
                # Start a new section
                current_section = match.group(2).strip()
                last_pos = match.end()
                sections[current_section] = ""
            
            # Add the remaining content
            if document[last_pos:].strip():
                sections[current_section] += document[last_pos:].strip()
        
        elif doc_format == "restructuredtext":
            # Split by RST section headers
            lines = document.split('\n')
            current_section = "Introduction"
            sections[current_section] = ""
            
            i = 0
            while i < len(lines):
                line = lines[i]
                # Check for underlined headers
                if i < len(lines) - 1 and re.match(r'^[=\-`~:\'">^*]', lines[i+1]) and len(lines[i+1].strip()) >= len(line.strip()):
                    if sections[current_section].strip():
                        # Start a new section
                        current_section = line.strip()
                        sections[current_section] = ""
                    else:
                        # This might be the document title
                        sections[current_section] = line.strip()
                    i += 1  # Skip the underline
                else:
                    sections[current_section] += line + "\n"
                i += 1
        
        else:
            # Default to just having a single section
            sections["Document"] = document
        
        return sections
    
    def _extract_diagrams(self, document: str) -> Dict[str, str]:
        """Extract diagram code from document"""
        diagrams = {}
        
        # Look for PlantUML code
        plantuml_matches = re.finditer(r'```plantuml\s*(.*?)\s*```', document, re.DOTALL)
        for i, match in enumerate(plantuml_matches):
            diagrams[f"plantuml_{i+1}"] = match.group(1).strip()
        
        # Look for Mermaid code
        mermaid_matches = re.finditer(r'```mermaid\s*(.*?)\s*```', document, re.DOTALL)
        for i, match in enumerate(mermaid_matches):
            diagrams[f"mermaid_{i+1}"] = match.group(1).strip()
        
        return diagrams
    
    def _generate_quick_reference(self, sections: Dict[str, str], project_name: str, doc_format: str) -> str:
        """Generate a quick reference guide from documentation sections"""
        format_info = self.doc_formats.get(doc_format, self.doc_formats["markdown"])
        
        if doc_format == "markdown":
            quick_ref = f"# {project_name} Quick Reference\n\n"
            
            # Add table of contents
            quick_ref += "## Table of Contents\n\n"
            for section in sections.keys():
                # Create anchor link
                anchor = section.lower().replace(' ', '-')
                quick_ref += f"- [{section}](#{anchor})\n"
            
            quick_ref += "\n"
            
            # Add key information from each section
            for section, content in sections.items():
                quick_ref += f"## {section}\n\n"
                
                # Extract key points
                lines = content.split('\n')
                bullet_points = [line for line in lines if line.strip().startswith('- ') or line.strip().startswith('* ')]
                
                if bullet_points:
                    # Add bullet points if available
                    for point in bullet_points[:3]:  # Limit to first 3 points
                        quick_ref += f"{point}\n"
                else:
                    # Add first paragraph
                    paragraphs = [p for p in content.split('\n\n') if p.strip()]
                    if paragraphs:
                        quick_ref += f"{paragraphs[0]}\n"
                
                quick_ref += "\n"
        
        elif doc_format == "restructuredtext":
            quick_ref = f"{project_name} Quick Reference\n"
            quick_ref += "=" * len(f"{project_name} Quick Reference") + "\n\n"
            
            # Add table of contents
            quick_ref += ".. contents:: Table of Contents\n"
            quick_ref += "   :local:\n\n"
            
            # Add key information from each section
            for section, content in sections.items():
                quick_ref += f"{section}\n"
                quick_ref += "-" * len(section) + "\n\n"
                
                # Extract key points
                lines = content.split('\n')
                bullet_points = [line for line in lines if line.strip().startswith('- ') or line.strip().startswith('* ')]
                
                if bullet_points:
                    # Add bullet points if available
                    for point in bullet_points[:3]:  # Limit to first 3 points
                        quick_ref += f"{point}\n"
                else:
                    # Add first paragraph
                    paragraphs = [p for p in content.split('\n\n') if p.strip()]
                    if paragraphs:
                        quick_ref += f"{paragraphs[0]}\n"
                
                quick_ref += "\n"
        
        else:
            # Default to markdown for other formats
            quick_ref = f"# {project_name} Quick Reference\n\n"
            
            for section, content in sections.items():
                quick_ref += f"## {section}\n\n"
                paragraphs = [p for p in content.split('\n\n') if p.strip()]
                if paragraphs:
                    quick_ref += f"{paragraphs[0]}\n\n"
        
        return quick_ref
    
    def _extract_score(self, text: str, metric: str) -> int:
        """Extract a numerical score from assessment text"""
        pattern = rf"(?:{metric}|{metric.capitalize()})[^\d]*?(\d+)"
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            score = int(match.group(1))
            return min(100, max(0, score))  # Ensure score is between 0-100
        
        return 0  # Default score
    
    def _extract_list_items(self, text: str, section: str) -> List[str]:
        """Extract list items from a section in assessment text"""
        items = []
        
        # Find the section
        section_pattern = rf"(?:{section}|{section.capitalize()})(?:[^\n]*)?:(.*?)(?:$|(?:\n\s*\n)|(?:\n\s*#))"
        section_match = re.search(section_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if section_match:
            section_text = section_match.group(1).strip()
            
            # Extract bullet points
            for line in section_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('*') or re.match(r'^\d+\.', line)):
                    # Remove the bullet or number prefix
                    item = re.sub(r'^[*\-•\d.]+\s*', '', line)
                    items.append(item)
        
        return items