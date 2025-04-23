"""
Specialized Agents Module for Code Deep Dive Analyzer

This module implements specialized agents for different aspects of code analysis,
including code quality, architecture, database, documentation, and agent readiness.
Each agent type has specific capabilities and expertise in its domain.
"""

import os
import json
import time
import re
import ast
import logging
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from dataclasses import dataclass, field

# Import base agent classes
from agent_base import (
    Agent, CodeQualityAgent, ArchitectureAgent, DatabaseAgent,
    DocumentationAgent, AgentReadinessAgent, LearningCoordinatorAgent,
    ModelInterface, Task, MessageType, MessagePriority, AgentCategory
)

# Import database migration manager
try:
    from services.database.migration_manager import MigrationManager
except ImportError:
    # Mock for testing without the migration manager
    class MigrationManager:
        def __init__(self, migrations_dir=None, db_url=None):
            self.migrations_dir = migrations_dir
            self.db_url = db_url
        
        def get_migration_status(self):
            return {"current_revision": None, "available_revisions": []}

# Import protocol server for task and messaging
from protocol_server import (
    ProtocolMessage, AgentIdentity, Task, FeedbackRecord, LearningUpdate
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Code Quality Agents
# =============================================================================

class StyleEnforcerAgent(CodeQualityAgent):
    """
    Agent that enforces code style standards and identifies style issues.
    
    Capabilities:
    - Analyze code style and formatting
    - Identify style guideline violations
    - Generate style recommendations
    - Create style configuration files
    """
    
    def __init__(self, agent_id: str = "style_enforcer", preferred_model: Optional[str] = None):
        capabilities = [
            "style_analysis", "formatting_detection", 
            "guideline_enforcement", "configuration_generation"
        ]
        
        super().__init__(
            agent_id=agent_id,
            capabilities=capabilities,
            preferred_model=preferred_model
        )
        
        # Style-specific attributes
        self.style_guides = {
            "python": "PEP 8",
            "javascript": "Airbnb",
            "typescript": "Google",
            "java": "Google",
            "csharp": "Microsoft",
            "go": "Go Standard",
            "ruby": "Ruby Style Guide",
            "php": "PSR-2"
        }
        
        self.style_checkers = {
            "python": ["pylint", "flake8", "black"],
            "javascript": ["eslint", "prettier"],
            "typescript": ["tslint", "prettier"],
            "java": ["checkstyle", "spotbugs"],
            "csharp": ["stylecop", "roslynator"],
            "go": ["golint", "gofmt"],
            "ruby": ["rubocop"],
            "php": ["php-cs-fixer", "phpcs"]
        }
    
    def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a style enforcer task"""
        task_type = task.task_type
        
        if task_type == "style_analysis":
            return self._analyze_style(task)
        
        elif task_type == "generate_config":
            return self._generate_style_config(task)
        
        elif task_type == "fix_style_issues":
            return self._fix_style_issues(task)
        
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    def _analyze_style(self, task: Task) -> Dict[str, Any]:
        """Analyze code style and identify issues"""
        code = task.input_data.get("code", "")
        language = task.input_data.get("language", "")
        
        if not code or not language:
            return {"error": "Missing code or language information"}
        
        # Use the model interface to analyze the code
        model = ModelInterface(capability="code_analysis")
        
        analysis_query = f"Analyze this code for style issues according to the {self.style_guides.get(language, 'standard')} style guide. Focus on formatting, naming conventions, and code organization."
        
        analysis = model.analyze_code(code, language, analysis_query)
        
        # Extract style issues
        style_issues = []
        for issue in analysis.get("issues", []):
            if issue.get("severity") != "high":  # Most style issues are not high severity
                style_issues.append(issue)
        
        # Generate recommendations
        style_recommendations = []
        for recommendation in analysis.get("recommendations", []):
            if "style" in recommendation.lower() or "format" in recommendation.lower():
                style_recommendations.append(recommendation)
        
        # Identify appropriate style checkers
        recommended_tools = self.style_checkers.get(language, [])
        
        return {
            "style_guide": self.style_guides.get(language, "standard"),
            "issues_count": len(style_issues),
            "issues": style_issues,
            "recommendations": style_recommendations,
            "recommended_tools": recommended_tools
        }
    
    def _generate_style_config(self, task: Task) -> Dict[str, Any]:
        """Generate style configuration files"""
        language = task.input_data.get("language", "")
        customizations = task.input_data.get("customizations", {})
        
        if not language:
            return {"error": "Missing language information"}
        
        # Use the model to generate a configuration
        model = ModelInterface(capability="code_analysis")
        
        prompt = f"""
        Generate a style configuration file for {language} using the {self.style_guides.get(language, 'standard')} style guide.
        
        Include the following customizations:
        {json.dumps(customizations, indent=2)}
        
        Return a complete configuration file that can be used with standard style checkers for {language}.
        The output should be in the appropriate format for the language (e.g., .pylintrc for Python, .eslintrc for JavaScript).
        """
        
        system_message = "You are an expert in code style and formatting. Generate configuration files that follow industry best practices."
        
        config_content = model.generate_text(prompt, system_message)
        
        # Determine the appropriate filename
        config_filename = self._get_config_filename(language)
        
        return {
            "language": language,
            "style_guide": self.style_guides.get(language, "standard"),
            "config_filename": config_filename,
            "config_content": config_content
        }
    
    def _fix_style_issues(self, task: Task) -> Dict[str, Any]:
        """Generate fixed code that addresses style issues"""
        code = task.input_data.get("code", "")
        language = task.input_data.get("language", "")
        issues = task.input_data.get("issues", [])
        
        if not code or not language:
            return {"error": "Missing code or language information"}
        
        # Use the model to fix the issues
        model = ModelInterface(capability="code_analysis")
        
        prompt = f"""
        Fix the following style issues in this {language} code:
        
        Issues:
        {json.dumps(issues, indent=2)}
        
        Original code:
        ```{language}
        {code}
        ```
        
        Return only the fixed code that addresses these style issues while maintaining the original functionality.
        The response should be the complete file with all issues fixed.
        """
        
        system_message = "You are an expert in code style and formatting. Fix style issues while preserving functionality."
        
        fixed_code = model.generate_text(prompt, system_message)
        
        # Extract the code from the response (in case the model includes explanations)
        code_match = re.search(r'```(?:\w+)?\s*\n(.*?)\n```', fixed_code, re.DOTALL)
        if code_match:
            fixed_code = code_match.group(1)
        
        # Verify that the fixed code is valid
        is_valid = self._verify_code_validity(fixed_code, language)
        
        return {
            "fixed_code": fixed_code,
            "is_valid": is_valid,
            "issues_addressed": len(issues)
        }
    
    def _get_config_filename(self, language: str) -> str:
        """Get the appropriate configuration filename for a language"""
        config_files = {
            "python": ".pylintrc",
            "javascript": ".eslintrc",
            "typescript": "tslint.json",
            "java": "checkstyle.xml",
            "csharp": "stylecop.json",
            "go": "golangci.yml",
            "ruby": ".rubocop.yml",
            "php": "phpcs.xml"
        }
        
        return config_files.get(language, f".{language}style")
    
    def _verify_code_validity(self, code: str, language: str) -> bool:
        """Verify that the fixed code is valid"""
        if language == "python":
            try:
                ast.parse(code)
                return True
            except SyntaxError:
                return False
        
        # For other languages, we'll assume the model generated valid code
        # In a real implementation, we'd use language-specific validators
        return True


class BugHunterAgent(CodeQualityAgent):
    """
    Agent that identifies potential bugs and security vulnerabilities in code.
    
    Capabilities:
    - Detect potential bugs and edge cases
    - Identify security vulnerabilities
    - Recommend fixes for identified issues
    - Generate test cases that would expose bugs
    """
    
    def __init__(self, agent_id: str = "bug_hunter", preferred_model: Optional[str] = None):
        capabilities = [
            "bug_detection", "security_analysis", 
            "fix_recommendation", "test_generation"
        ]
        
        super().__init__(
            agent_id=agent_id,
            capabilities=capabilities,
            preferred_model=preferred_model
        )
        
        # Bug hunter specific attributes
        self.common_vulnerabilities = {
            "sql_injection": r"(?i).*(?:execute|query)\s*\(\s*[\"'].*?\+.*?[\"']\s*\)",
            "xss": r"(?i)(?:innerHTML|outerHTML|document\.write)\s*=",
            "command_injection": r"(?i)(?:exec|spawn|system)\s*\(",
            "path_traversal": r"(?i)(?:fs|path)\.(?:read|write).*?\.\.\/",
            "insecure_deserialization": r"(?i)(?:pickle\.loads|json\.loads|yaml\.load)(?!\s*\(\s*.*?\s*,\s*[Ll]oader\s*=\s*.*?[Ss]afe.*?\))",
            "hard_coded_credentials": r"(?i)(?:password|api_key|secret|token)\s*=\s*[\"'][^\"']+[\"']",
            "insecure_hash": r"(?i)(?:md5|sha1)\("
        }
        
        self.security_checkers = {
            "python": ["bandit", "pyt"],
            "javascript": ["eslint-plugin-security", "snyk"],
            "java": ["spotbugs", "find-sec-bugs"],
            "csharp": ["security-code-scan", "sonarqube"],
            "php": ["phpcs-security-audit", "psalm"]
        }
    
    def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a bug hunter task"""
        task_type = task.task_type
        
        if task_type == "bug_detection":
            return self._detect_bugs(task)
        
        elif task_type == "security_analysis":
            return self._analyze_security(task)
        
        elif task_type == "generate_tests":
            return self._generate_test_cases(task)
        
        elif task_type == "recommend_fixes":
            return self._recommend_fixes(task)
        
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    def _detect_bugs(self, task: Task) -> Dict[str, Any]:
        """Detect potential bugs in code"""
        code = task.input_data.get("code", "")
        language = task.input_data.get("language", "")
        
        if not code or not language:
            return {"error": "Missing code or language information"}
        
        # Use the model interface to analyze the code
        model = ModelInterface(capability="code_analysis")
        
        analysis_query = "Analyze this code for potential bugs, edge cases, or reliability issues. Focus on logic errors, memory leaks, race conditions, exception handling, and input validation problems."
        
        analysis = model.analyze_code(code, language, analysis_query)
        
        # Extract bugs and issues
        bugs = []
        for issue in analysis.get("issues", []):
            # Only include high and medium severity issues
            if issue.get("severity") in ["high", "medium"]:
                bugs.append(issue)
        
        # Generate recommendations
        recommendations = []
        for recommendation in analysis.get("recommendations", []):
            if "fix" in recommendation.lower() or "bug" in recommendation.lower():
                recommendations.append(recommendation)
        
        return {
            "bugs_count": len(bugs),
            "bugs": bugs,
            "risk_level": self._calculate_risk_level(bugs),
            "recommendations": recommendations
        }
    
    def _analyze_security(self, task: Task) -> Dict[str, Any]:
        """Analyze code for security vulnerabilities"""
        code = task.input_data.get("code", "")
        language = task.input_data.get("language", "")
        
        if not code or not language:
            return {"error": "Missing code or language information"}
        
        # First, do a quick check for common vulnerabilities using regex
        quick_findings = self._check_common_vulnerabilities(code)
        
        # Use the model interface for deeper analysis
        model = ModelInterface(capability="code_analysis")
        
        analysis_query = "Analyze this code for security vulnerabilities. Focus on injection attacks, authentication issues, sensitive data exposure, broken access control, security misconfigurations, and other OWASP Top 10 issues."
        
        analysis = model.analyze_code(code, language, analysis_query)
        
        # Extract security vulnerabilities
        vulnerabilities = []
        for issue in analysis.get("issues", []):
            if "security" in issue.get("description", "").lower() or issue.get("severity") == "high":
                vulnerabilities.append(issue)
        
        # Combine with quick findings
        for vuln_type, matches in quick_findings.items():
            if matches:
                for match in matches:
                    vulnerabilities.append({
                        "description": f"Potential {vuln_type.replace('_', ' ')} vulnerability",
                        "severity": "high",
                        "line_numbers": [match.get("line", 0)],
                        "recommendations": [f"Review and secure the {vuln_type.replace('_', ' ')} pattern"]
                    })
        
        # Generate recommendations
        recommendations = []
        for recommendation in analysis.get("recommendations", []):
            if "security" in recommendation.lower() or "vulnerability" in recommendation.lower():
                recommendations.append(recommendation)
        
        # Add recommended security checkers
        recommended_tools = self.security_checkers.get(language, [])
        
        return {
            "vulnerabilities_count": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,
            "risk_level": self._calculate_risk_level(vulnerabilities),
            "recommendations": recommendations,
            "recommended_tools": recommended_tools
        }
    
    def _generate_test_cases(self, task: Task) -> Dict[str, Any]:
        """Generate test cases that would expose identified bugs"""
        code = task.input_data.get("code", "")
        language = task.input_data.get("language", "")
        bugs = task.input_data.get("bugs", [])
        
        if not code or not language:
            return {"error": "Missing code or language information"}
        
        # Use the model to generate test cases
        model = ModelInterface(capability="code_analysis")
        
        prompt = f"""
        Generate test cases that would expose the following bugs in this {language} code:
        
        Bugs:
        {json.dumps(bugs, indent=2)}
        
        Original code:
        ```{language}
        {code}
        ```
        
        Generate complete test cases that can be executed to verify whether these bugs are present.
        For each bug, create at least one test case that would fail if the bug exists.
        Format the test cases according to the standard testing framework for {language}.
        """
        
        system_message = "You are an expert in software testing and quality assurance. Generate comprehensive test cases that effectively expose bugs."
        
        test_cases = model.generate_text(prompt, system_message)
        
        # Extract the code from the response
        test_code_match = re.search(r'```(?:\w+)?\s*\n(.*?)\n```', test_cases, re.DOTALL)
        if test_code_match:
            test_code = test_code_match.group(1)
        else:
            test_code = test_cases
        
        return {
            "test_code": test_code,
            "bugs_covered": len(bugs),
            "test_framework": self._determine_test_framework(language)
        }
    
    def _recommend_fixes(self, task: Task) -> Dict[str, Any]:
        """Recommend fixes for identified bugs"""
        code = task.input_data.get("code", "")
        language = task.input_data.get("language", "")
        bugs = task.input_data.get("bugs", [])
        
        if not code or not language or not bugs:
            return {"error": "Missing code, language, or bugs information"}
        
        # Use the model to recommend fixes
        model = ModelInterface(capability="code_analysis")
        
        prompt = f"""
        Recommend fixes for the following bugs in this {language} code:
        
        Bugs:
        {json.dumps(bugs, indent=2)}
        
        Original code:
        ```{language}
        {code}
        ```
        
        For each bug, provide:
        1. A clear explanation of how to fix it
        2. The fixed code snippet that addresses the issue
        3. An explanation of why the fix works
        
        Format your response as JSON with the following structure:
        {{
            "fixes": [
                {{
                    "bug_description": "Description of the bug",
                    "fix_explanation": "How to fix it",
                    "fixed_code": "The fixed code snippet",
                    "why_it_works": "Why this fix addresses the issue"
                }}
            ]
        }}
        """
        
        system_message = "You are an expert in fixing software bugs and security vulnerabilities. Provide clear, effective solutions that address the root cause of each issue."
        
        fixes_text = model.generate_text(prompt, system_message)
        
        # Extract JSON from the response
        try:
            import json
            import re
            
            json_match = re.search(r'(\{.*\})', fixes_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                fixes = json.loads(json_str)
            else:
                fixes = json.loads(fixes_text)
        
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw text
            fixes = {"fixes_text": fixes_text}
        
        return {
            "fixes": fixes.get("fixes", []),
            "bugs_fixed_count": len(fixes.get("fixes", [])),
            "recommendation_quality": self._assess_recommendation_quality(fixes.get("fixes", []))
        }
    
    def _check_common_vulnerabilities(self, code: str) -> Dict[str, List[Dict[str, Any]]]:
        """Check for common vulnerabilities using regex patterns"""
        results = {}
        
        # Split code into lines for line number tracking
        lines = code.split('\n')
        
        for vuln_type, pattern in self.common_vulnerabilities.items():
            matches = []
            
            for i, line in enumerate(lines):
                if re.search(pattern, line):
                    matches.append({
                        "line": i + 1,
                        "code": line.strip()
                    })
            
            results[vuln_type] = matches
        
        return results
    
    def _calculate_risk_level(self, issues: List[Dict[str, Any]]) -> str:
        """Calculate overall risk level based on issues"""
        if not issues:
            return "low"
        
        # Count issues by severity
        high_count = sum(1 for issue in issues if issue.get("severity") == "high")
        medium_count = sum(1 for issue in issues if issue.get("severity") == "medium")
        
        if high_count > 2 or (high_count > 0 and medium_count > 3):
            return "critical"
        elif high_count > 0 or medium_count > 2:
            return "high"
        elif medium_count > 0:
            return "medium"
        else:
            return "low"
    
    def _determine_test_framework(self, language: str) -> str:
        """Determine the appropriate test framework for a language"""
        frameworks = {
            "python": "pytest",
            "javascript": "jest",
            "typescript": "jest",
            "java": "junit",
            "csharp": "xunit",
            "go": "go test",
            "ruby": "rspec",
            "php": "phpunit"
        }
        
        return frameworks.get(language, "standard test framework")
    
    def _assess_recommendation_quality(self, fixes: List[Dict[str, Any]]) -> float:
        """Assess the quality of fix recommendations on a scale of 0-1"""
        if not fixes:
            return 0.0
        
        # Check if each fix has all required components
        completeness_scores = []
        for fix in fixes:
            score = 0.0
            if fix.get("bug_description"):
                score += 0.2
            if fix.get("fix_explanation"):
                score += 0.3
            if fix.get("fixed_code"):
                score += 0.4
            if fix.get("why_it_works"):
                score += 0.1
            
            completeness_scores.append(score)
        
        # Average completeness
        return sum(completeness_scores) / len(completeness_scores)


class PerformanceOptimizerAgent(CodeQualityAgent):
    """
    Agent that identifies performance bottlenecks and suggests optimizations.
    
    Capabilities:
    - Detect performance bottlenecks
    - Analyze algorithm complexity
    - Suggest performance optimizations
    - Benchmark before/after improvements
    """
    
    def __init__(self, agent_id: str = "performance_optimizer", preferred_model: Optional[str] = None):
        capabilities = [
            "performance_analysis", "complexity_analysis", 
            "optimization_suggestion", "benchmark_simulation"
        ]
        
        super().__init__(
            agent_id=agent_id,
            capabilities=capabilities,
            preferred_model=preferred_model
        )
        
        # Performance optimizer specific attributes
        self.complexity_patterns = {
            "n_squared": r"for\s+.+?\s+in\s+.+?:\s*\n\s+for\s+.+?\s+in\s+.+?:",
            "exponential": r"(?:fibonacci|factorial)\s*\(|def\s+(?:fibonacci|factorial)",
            "recursive_without_memoization": r"def\s+\w+\([^)]*\):\s*.*\breturn\b.*\b\w+\([^)]*\)"
        }
        
        self.performance_tools = {
            "python": ["cProfile", "line_profiler", "memory_profiler", "py-spy"],
            "javascript": ["lighthouse", "chrome-devtools", "v8-profiler"],
            "java": ["jvisualvm", "jprofiler", "yourkit"],
            "csharp": ["dotnet-trace", "perfview"],
            "go": ["pprof", "trace"],
            "ruby": ["ruby-prof", "stackprof"],
            "php": ["xdebug", "blackfire"]
        }
    
    def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a performance optimizer task"""
        task_type = task.task_type
        
        if task_type == "performance_analysis":
            return self._analyze_performance(task)
        
        elif task_type == "complexity_analysis":
            return self._analyze_complexity(task)
        
        elif task_type == "optimize_code":
            return self._optimize_code(task)
        
        elif task_type == "benchmark_simulation":
            return self._simulate_benchmark(task)
        
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    def _analyze_performance(self, task: Task) -> Dict[str, Any]:
        """Analyze code for performance issues"""
        code = task.input_data.get("code", "")
        language = task.input_data.get("language", "")
        
        if not code or not language:
            return {"error": "Missing code or language information"}
        
        # Use the model interface to analyze the code
        model = ModelInterface(capability="code_analysis")
        
        analysis_query = "Analyze this code for performance issues and bottlenecks. Focus on inefficient algorithms, redundant operations, unnecessary memory usage, and any operations that could be optimized."
        
        analysis = model.analyze_code(code, language, analysis_query)
        
        # Quick check for common complexity patterns
        complexity_issues = self._check_complexity_patterns(code)
        
        # Extract performance issues
        performance_issues = []
        for issue in analysis.get("issues", []):
            if "performance" in issue.get("description", "").lower():
                performance_issues.append(issue)
        
        # Add complexity issues identified by pattern matching
        for issue_type, matches in complexity_issues.items():
            if matches:
                for match in matches:
                    performance_issues.append({
                        "description": f"Potential {issue_type.replace('_', ' ')} complexity issue",
                        "severity": "medium",
                        "line_numbers": [match.get("line", 0)],
                        "recommendations": [f"Review the {issue_type.replace('_', ' ')} pattern for optimization"]
                    })
        
        # Generate optimization recommendations
        recommendations = []
        for recommendation in analysis.get("recommendations", []):
            if "performance" in recommendation.lower() or "optimize" in recommendation.lower():
                recommendations.append(recommendation)
        
        # Add recommended performance tools
        recommended_tools = self.performance_tools.get(language, [])
        
        return {
            "issues_count": len(performance_issues),
            "performance_issues": performance_issues,
            "recommendations": recommendations,
            "estimated_impact": self._estimate_performance_impact(performance_issues),
            "recommended_tools": recommended_tools
        }
    
    def _analyze_complexity(self, task: Task) -> Dict[str, Any]:
        """Analyze algorithm complexity"""
        code = task.input_data.get("code", "")
        language = task.input_data.get("language", "")
        
        if not code or not language:
            return {"error": "Missing code or language information"}
        
        # Use the model to analyze complexity
        model = ModelInterface(capability="code_analysis")
        
        prompt = f"""
        Analyze the time and space complexity of algorithms in this {language} code.
        For each function or method:
        1. Identify its time complexity (e.g., O(n), O(n²), O(log n))
        2. Identify its space complexity
        3. Explain the factors affecting its complexity
        4. Suggest optimizations where possible
        
        Original code:
        ```{language}
        {code}
        ```
        
        Format your response as JSON with the following structure:
        {{
            "functions": [
                {{
                    "name": "function_name",
                    "time_complexity": "O(n)",
                    "space_complexity": "O(1)",
                    "explanation": "Explanation of complexity",
                    "optimization_potential": "high/medium/low",
                    "optimization_suggestions": ["Suggestion 1", "Suggestion 2"]
                }}
            ],
            "overall_complexity": "O(n²)",
            "bottlenecks": ["Bottleneck 1", "Bottleneck 2"]
        }}
        """
        
        system_message = "You are an expert in algorithm analysis and computational complexity. Provide accurate assessments of time and space complexity using Big O notation."
        
        complexity_text = model.generate_text(prompt, system_message)
        
        # Extract JSON from the response
        try:
            import json
            import re
            
            json_match = re.search(r'(\{.*\})', complexity_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                complexity_analysis = json.loads(json_str)
            else:
                complexity_analysis = json.loads(complexity_text)
        
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw text
            complexity_analysis = {"complexity_text": complexity_text}
        
        return {
            "functions_analyzed": len(complexity_analysis.get("functions", [])),
            "functions": complexity_analysis.get("functions", []),
            "overall_complexity": complexity_analysis.get("overall_complexity", "Unknown"),
            "bottlenecks": complexity_analysis.get("bottlenecks", [])
        }
    
    def _optimize_code(self, task: Task) -> Dict[str, Any]:
        """Optimize code for better performance"""
        code = task.input_data.get("code", "")
        language = task.input_data.get("language", "")
        issues = task.input_data.get("performance_issues", [])
        
        if not code or not language:
            return {"error": "Missing code or language information"}
        
        # Use the model to optimize the code
        model = ModelInterface(capability="code_analysis")
        
        prompt = f"""
        Optimize the following {language} code to improve performance:
        
        Performance issues:
        {json.dumps(issues, indent=2) if issues else "Perform general performance optimization."}
        
        Original code:
        ```{language}
        {code}
        ```
        
        Return an optimized version of the code that addresses these performance issues while maintaining the original functionality.
        For each optimization, include a comment explaining what was optimized and why.
        """
        
        system_message = "You are an expert in code optimization and performance tuning. Optimize code while preserving its functionality and maintaining readability."
        
        optimized_code = model.generate_text(prompt, system_message)
        
        # Extract the code from the response
        code_match = re.search(r'```(?:\w+)?\s*\n(.*?)\n```', optimized_code, re.DOTALL)
        if code_match:
            optimized_code = code_match.group(1)
        
        # Verify that the optimized code is valid
        is_valid = self._verify_code_validity(optimized_code, language)
        
        # Estimate performance improvement
        estimated_improvement = self._estimate_optimization_improvement(issues)
        
        return {
            "optimized_code": optimized_code,
            "is_valid": is_valid,
            "issues_addressed": len(issues) if issues else "general optimization",
            "estimated_improvement": estimated_improvement
        }
    
    def _simulate_benchmark(self, task: Task) -> Dict[str, Any]:
        """Simulate benchmarking results for original vs. optimized code"""
        original_code = task.input_data.get("original_code", "")
        optimized_code = task.input_data.get("optimized_code", "")
        language = task.input_data.get("language", "")
        
        if not original_code or not optimized_code or not language:
            return {"error": "Missing code or language information"}
        
        # Use the model to simulate benchmark results
        # Note: This is a simulation only - in a real system we would run actual benchmarks
        model = ModelInterface(capability="code_analysis")
        
        prompt = f"""
        Simulate benchmark results comparing the performance of these original and optimized {language} code versions:
        
        Original code:
        ```{language}
        {original_code}
        ```
        
        Optimized code:
        ```{language}
        {optimized_code}
        ```
        
        Based on your expertise in performance analysis, estimate:
        1. The execution time difference between the two versions
        2. Memory usage difference
        3. CPU utilization difference
        4. Scaling characteristics with increased input size
        
        Format your response as JSON with the following structure:
        {{
            "execution_time": {{
                "original": "estimated time",
                "optimized": "estimated time",
                "improvement_percentage": percentage
            }},
            "memory_usage": {{
                "original": "estimated usage",
                "optimized": "estimated usage",
                "improvement_percentage": percentage
            }},
            "cpu_utilization": {{
                "original": "estimated percentage",
                "optimized": "estimated percentage",
                "improvement_percentage": percentage
            }},
            "scaling": {{
                "original": "O(x)",
                "optimized": "O(y)",
                "improvement_description": "description"
            }}
        }}
        """
        
        system_message = "You are an expert in performance benchmarking and analysis. Provide realistic performance estimates based on code structure and optimization patterns."
        
        benchmark_text = model.generate_text(prompt, system_message)
        
        # Extract JSON from the response
        try:
            import json
            import re
            
            json_match = re.search(r'(\{.*\})', benchmark_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                benchmark_results = json.loads(json_str)
            else:
                benchmark_results = json.loads(benchmark_text)
        
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw text
            benchmark_results = {"benchmark_text": benchmark_text}
        
        return benchmark_results
    
    def _check_complexity_patterns(self, code: str) -> Dict[str, List[Dict[str, Any]]]:
        """Check for common complexity patterns using regex"""
        results = {}
        
        # Split code into lines for line number tracking
        lines = code.split('\n')
        
        for pattern_type, pattern in self.complexity_patterns.items():
            matches = []
            
            # Check for multi-line patterns
            pattern_matches = re.finditer(pattern, code, re.MULTILINE)
            for match in pattern_matches:
                # Find the line number by counting newlines before the match
                code_before_match = code[:match.start()]
                line_num = code_before_match.count('\n') + 1
                
                matches.append({
                    "line": line_num,
                    "code": match.group(0)
                })
            
            results[pattern_type] = matches
        
        return results
    
    def _estimate_performance_impact(self, issues: List[Dict[str, Any]]) -> str:
        """Estimate the performance impact of the identified issues"""
        if not issues:
            return "minimal"
        
        # Count issues by severity
        high_count = sum(1 for issue in issues if issue.get("severity") == "high")
        medium_count = sum(1 for issue in issues if issue.get("severity") == "medium")
        
        if high_count > 2:
            return "critical"
        elif high_count > 0 or medium_count > 2:
            return "significant"
        elif medium_count > 0:
            return "moderate"
        else:
            return "minor"
    
    def _verify_code_validity(self, code: str, language: str) -> bool:
        """Verify that the optimized code is valid"""
        if language == "python":
            try:
                ast.parse(code)
                return True
            except SyntaxError:
                return False
        
        # For other languages, we'll assume the model generated valid code
        # In a real implementation, we'd use language-specific validators
        return True
    
    def _estimate_optimization_improvement(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate the improvement from addressing the performance issues"""
        if not issues:
            return {
                "time_improvement": "5-10%",
                "memory_improvement": "minimal",
                "confidence": "low"
            }
        
        # Classify issues
        algorithm_issues = 0
        memory_issues = 0
        redundancy_issues = 0
        
        for issue in issues:
            desc = issue.get("description", "").lower()
            if "algorithm" in desc or "complexity" in desc:
                algorithm_issues += 1
            elif "memory" in desc:
                memory_issues += 1
            elif "redundant" in desc or "unnecessary" in desc:
                redundancy_issues += 1
        
        # Estimate improvements
        time_improvement = "minimal"
        if algorithm_issues > 2:
            time_improvement = "major (50%+)"
        elif algorithm_issues > 0 or redundancy_issues > 2:
            time_improvement = "significant (20-50%)"
        elif redundancy_issues > 0:
            time_improvement = "moderate (10-20%)"
        
        memory_improvement = "minimal"
        if memory_issues > 2:
            memory_improvement = "significant (30%+)"
        elif memory_issues > 0:
            memory_improvement = "moderate (10-30%)"
        
        # Estimate confidence
        confidence = "medium"
        if algorithm_issues + memory_issues + redundancy_issues > 4:
            confidence = "high"
        elif algorithm_issues + memory_issues + redundancy_issues < 2:
            confidence = "low"
        
        return {
            "time_improvement": time_improvement,
            "memory_improvement": memory_improvement,
            "confidence": confidence
        }


class TestCoverageAgent(CodeQualityAgent):
    """
    Agent that evaluates test coverage and suggests additional tests.
    
    Capabilities:
    - Analyze test coverage
    - Identify untested code paths
    - Generate test cases
    - Recommend testing strategies
    """
    
    def __init__(self, agent_id: str = "test_coverage", preferred_model: Optional[str] = None):
        capabilities = [
            "coverage_analysis", "test_generation", 
            "strategy_recommendation", "edge_case_identification"
        ]
        
        super().__init__(
            agent_id=agent_id,
            capabilities=capabilities,
            preferred_model=preferred_model
        )
        
        # Test coverage specific attributes
        self.test_frameworks = {
            "python": ["pytest", "unittest", "nose"],
            "javascript": ["jest", "mocha", "jasmine"],
            "typescript": ["jest", "mocha", "jasmine"],
            "java": ["junit", "testng", "spock"],
            "csharp": ["nunit", "xunit", "mstest"],
            "go": ["testing", "testify", "gocheck"],
            "ruby": ["rspec", "minitest", "cucumber"],
            "php": ["phpunit", "codeception", "behat"]
        }
        
        self.coverage_tools = {
            "python": ["coverage.py", "pytest-cov"],
            "javascript": ["istanbul", "nyc"],
            "typescript": ["istanbul", "nyc"],
            "java": ["jacoco", "cobertura"],
            "csharp": ["coverlet", "opencover"],
            "go": ["go cover", "gocov"],
            "ruby": ["simplecov", "rcov"],
            "php": ["phpunit --coverage", "xdebug"]
        }
    
    def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a test coverage task"""
        task_type = task.task_type
        
        if task_type == "coverage_analysis":
            return self._analyze_coverage(task)
        
        elif task_type == "generate_tests":
            return self._generate_tests(task)
        
        elif task_type == "identify_edge_cases":
            return self._identify_edge_cases(task)
        
        elif task_type == "recommend_strategy":
            return self._recommend_testing_strategy(task)
        
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    def _analyze_coverage(self, task: Task) -> Dict[str, Any]:
        """Analyze test coverage"""
        code = task.input_data.get("code", "")
        tests = task.input_data.get("tests", "")
        language = task.input_data.get("language", "")
        
        if not code or not language:
            return {"error": "Missing code or language information"}
        
        # Use the model interface to analyze the code and tests
        model = ModelInterface(capability="code_analysis")
        
        analysis_query = """
        Analyze the test coverage of this code. Identify:
        1. Functions and methods that are not tested
        2. Code branches that are not covered by tests
        3. Edge cases that are not being tested
        4. Overall test coverage percentage estimate
        """
        
        # Combine code and tests for analysis
        combined_code = f"""
        # Main code:
        ```{language}
        {code}
        ```
        
        # Tests:
        ```{language}
        {tests if tests else "# No tests provided"}
        ```
        """
        
        analysis = model.analyze_code(combined_code, language, analysis_query)
        
        # Identify untested code elements
        untested_elements = []
        for issue in analysis.get("issues", []):
            if "untested" in issue.get("description", "").lower() or "not covered" in issue.get("description", "").lower():
                untested_elements.append(issue)
        
        # Extract recommendations
        recommendations = []
        for recommendation in analysis.get("recommendations", []):
            if "test" in recommendation.lower() or "coverage" in recommendation.lower():
                recommendations.append(recommendation)
        
        # Estimate coverage percentage
        coverage_percentage = self._estimate_coverage_percentage(code, tests, analysis)
        
        # Recommend appropriate testing tools
        recommended_frameworks = self.test_frameworks.get(language, [])
        recommended_coverage_tools = self.coverage_tools.get(language, [])
        
        return {
            "coverage_percentage": coverage_percentage,
            "untested_elements_count": len(untested_elements),
            "untested_elements": untested_elements,
            "recommendations": recommendations,
            "recommended_frameworks": recommended_frameworks,
            "recommended_coverage_tools": recommended_coverage_tools
        }
    
    def _generate_tests(self, task: Task) -> Dict[str, Any]:
        """Generate test cases for untested code"""
        code = task.input_data.get("code", "")
        untested_elements = task.input_data.get("untested_elements", [])
        language = task.input_data.get("language", "")
        framework = task.input_data.get("framework", "")
        
        if not code or not language:
            return {"error": "Missing code or language information"}
        
        # If no framework specified, use the first recommended one
        if not framework:
            framework = self.test_frameworks.get(language, ["standard"])[0]
        
        # Use the model to generate tests
        model = ModelInterface(capability="code_analysis")
        
        prompt = f"""
        Generate test cases for the following {language} code, focusing on untested elements:
        
        ```{language}
        {code}
        ```
        
        Untested elements to focus on:
        {json.dumps(untested_elements, indent=2) if untested_elements else "Generate comprehensive tests covering all functionality."}
        
        Create tests using the {framework} framework, including:
        1. Unit tests for all functions/methods
        2. Tests for edge cases and error conditions
        3. Tests that verify expected behavior
        
        The tests should be comprehensive, well-structured, and follow best practices for {framework}.
        """
        
        system_message = "You are an expert in software testing and test-driven development. Create thorough, effective tests that maximize code coverage."
        
        test_code = model.generate_text(prompt, system_message)
        
        # Extract the code from the response
        test_code_match = re.search(r'```(?:\w+)?\s*\n(.*?)\n```', test_code, re.DOTALL)
        if test_code_match:
            test_code = test_code_match.group(1)
        
        # Verify that the test code is valid
        is_valid = self._verify_code_validity(test_code, language)
        
        # Estimate new coverage with these tests
        estimated_new_coverage = self._estimate_new_coverage(untested_elements, 0.7)  # Assume 70% of untested elements now covered
        
        return {
            "test_code": test_code,
            "is_valid": is_valid,
            "framework": framework,
            "elements_covered": len(untested_elements) if untested_elements else "all functionality",
            "estimated_new_coverage": estimated_new_coverage
        }
    
    def _identify_edge_cases(self, task: Task) -> Dict[str, Any]:
        """Identify edge cases that should be tested"""
        code = task.input_data.get("code", "")
        language = task.input_data.get("language", "")
        
        if not code or not language:
            return {"error": "Missing code or language information"}
        
        # Use the model to identify edge cases
        model = ModelInterface(capability="code_analysis")
        
        prompt = f"""
        Identify edge cases and boundary conditions that should be tested in this {language} code:
        
        ```{language}
        {code}
        ```
        
        For each function or method, identify:
        1. Input boundary conditions (min/max values, empty inputs, etc.)
        2. Error conditions that should be handled
        3. Race conditions or timing issues
        4. Resource constraints (memory, file handles, etc.)
        5. Unusual or unexpected inputs
        
        Format your response as JSON with the following structure:
        {{
            "edge_cases": [
                {{
                    "function": "function_name",
                    "description": "Description of the edge case",
                    "test_recommendation": "How to test this case",
                    "severity": "high/medium/low"
                }}
            ]
        }}
        """
        
        system_message = "You are an expert in identifying edge cases and boundary conditions in code. Your goal is to find all possible scenarios that could lead to bugs or unexpected behavior."
        
        edge_cases_text = model.generate_text(prompt, system_message)
        
        # Extract JSON from the response
        try:
            import json
            import re
            
            json_match = re.search(r'(\{.*\})', edge_cases_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                edge_cases = json.loads(json_str)
            else:
                edge_cases = json.loads(edge_cases_text)
        
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw text
            edge_cases = {"edge_cases_text": edge_cases_text}
        
        return {
            "edge_cases_count": len(edge_cases.get("edge_cases", [])),
            "edge_cases": edge_cases.get("edge_cases", []),
            "critical_cases_count": sum(1 for case in edge_cases.get("edge_cases", []) if case.get("severity") == "high")
        }
    
    def _recommend_testing_strategy(self, task: Task) -> Dict[str, Any]:
        """Recommend an overall testing strategy"""
        code_structure = task.input_data.get("code_structure", {})
        language = task.input_data.get("language", "")
        current_coverage = task.input_data.get("current_coverage", 0)
        
        if not language:
            return {"error": "Missing language information"}
        
        # Use the model to recommend a testing strategy
        model = ModelInterface(capability="code_analysis")
        
        prompt = f"""
        Recommend a comprehensive testing strategy for a {language} codebase with the following characteristics:
        
        Current test coverage: {current_coverage}%
        
        Code structure:
        {json.dumps(code_structure, indent=2) if code_structure else "No specific structure information provided."}
        
        Include recommendations for:
        1. Testing frameworks and tools to use
        2. Types of tests to implement (unit, integration, functional, etc.)
        3. Testing priorities (what to test first)
        4. Coverage goals and metrics
        5. Testing workflow and CI/CD integration
        
        Format your response as JSON with the following structure:
        {{
            "recommended_frameworks": ["framework1", "framework2"],
            "recommended_tools": ["tool1", "tool2"],
            "test_types": [
                {{
                    "type": "unit/integration/etc",
                    "importance": "high/medium/low",
                    "focus_areas": ["area1", "area2"]
                }}
            ],
            "priorities": ["priority1", "priority2"],
            "coverage_goals": {{
                "initial_target": percentage,
                "long_term_target": percentage,
                "critical_components": ["component1", "component2"]
            }},
            "workflow_recommendations": ["recommendation1", "recommendation2"]
        }}
        """
        
        system_message = "You are an expert in software testing strategies and best practices. Provide comprehensive, practical recommendations for implementing effective testing."
        
        strategy_text = model.generate_text(prompt, system_message)
        
        # Extract JSON from the response
        try:
            import json
            import re
            
            json_match = re.search(r'(\{.*\})', strategy_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                strategy = json.loads(json_str)
            else:
                strategy = json.loads(strategy_text)
        
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw text
            strategy = {"strategy_text": strategy_text}
        
        return strategy
    
    def _estimate_coverage_percentage(self, code: str, tests: str, analysis: Dict[str, Any]) -> int:
        """Estimate test coverage percentage based on code and analysis"""
        if not code:
            return 0
        
        # If tests are empty, coverage is 0
        if not tests:
            return 0
        
        # Extract coverage estimate from analysis if present
        analysis_text = analysis.get("analysis", "")
        coverage_match = re.search(r'(\d+)%\s+coverage', analysis_text)
        if coverage_match:
            try:
                return int(coverage_match.group(1))
            except ValueError:
                pass
        
        # Count untested elements
        untested_count = sum(1 for issue in analysis.get("issues", []) 
                           if "untested" in issue.get("description", "").lower() 
                           or "not covered" in issue.get("description", "").lower())
        
        # Count total elements (very rough approximation)
        function_count = len(re.findall(r'def\s+\w+\s*\(', code)) + len(re.findall(r'function\s+\w+\s*\(', code))
        class_count = len(re.findall(r'class\s+\w+', code))
        
        total_elements = max(function_count + class_count, 1)  # Avoid division by zero
        
        if untested_count >= total_elements:
            return 10  # Default low value if estimation fails
        
        # Calculate coverage
        coverage = 100 - (untested_count * 100 // total_elements)
        
        # Sanity check - if we have tests but calculated 0, return a minimum value
        if coverage <= 0 and tests:
            return 10
        
        return coverage
    
    def _verify_code_validity(self, code: str, language: str) -> bool:
        """Verify that the generated test code is valid"""
        if language == "python":
            try:
                ast.parse(code)
                return True
            except SyntaxError:
                return False
        
        # For other languages, we'll assume the model generated valid code
        # In a real implementation, we'd use language-specific validators
        return True
    
    def _estimate_new_coverage(self, untested_elements: List[Dict[str, Any]], coverage_factor: float) -> int:
        """Estimate new coverage after testing previously untested elements"""
        # If we don't have untested elements data, make a rough guess
        if not untested_elements:
            return 80  # Assume good coverage with new tests
        
        # Calculate how many elements would now be covered
        newly_covered = len(untested_elements) * coverage_factor
        
        # Assume these represent 30% of the codebase (rough estimate)
        coverage_increase = newly_covered * 30 / len(untested_elements)
        
        # Cap at 95% (it's rare to achieve 100% coverage)
        return min(60 + int(coverage_increase), 95)


# =============================================================================
# Architecture Agents
# =============================================================================

class PatternDetectorAgent(ArchitectureAgent):
    """
    Agent that identifies design patterns and architectural patterns in code.
    
    Capabilities:
    - Detect common design patterns
    - Identify architectural patterns
    - Recognize anti-patterns
    - Suggest pattern improvements
    """
    
    def __init__(self, agent_id: str = "pattern_detector", preferred_model: Optional[str] = None):
        capabilities = [
            "pattern_detection", "antipattern_detection", 
            "architecture_identification", "pattern_recommendation"
        ]
        
        super().__init__(
            agent_id=agent_id,
            capabilities=capabilities,
            preferred_model=preferred_model
        )
        
        # Pattern detector specific attributes
        self.design_patterns = {
            # Creational patterns
            "singleton": r"(?:private|protected)\s+static\s+\w+\s+instance|static\s+getInstance\(\)|private\s+constructor|\s+\w+\s*=\s*null",
            "factory_method": r"interface\s+\w+.*?(?:class|interface)\s+\w+.*?(?:create|make|build)\w*\s*\(|abstract\s+\w+\s+create\w*\s*\(",
            "abstract_factory": r"interface\s+\w+Factory|abstract\s+class\s+\w+Factory",
            "builder": r"(?:class|interface)\s+\w+Builder|\.set\w+\(\).*?\.set\w+\(\).*?\.build\(\)",
            "prototype": r"(?:clone|copy)\(\)|implements\s+Cloneable|prototype",
            
            # Structural patterns
            "adapter": r"class\s+\w+Adapter|implements\s+\w+Target",
            "bridge": r"(?:interface|abstract\s+class)\s+\w+.*?(?:interface|abstract\s+class)\s+\w+Implementation",
            "composite": r"(?:add|remove|get)Child|children.*?(?:List|Array|Collection)",
            "decorator": r"class\s+\w+Decorator|extends\s+\w+(?:Decorator|Wrapper)|super\.\w+\(\)",
            "facade": r"class\s+\w+Facade",
            "flyweight": r"static\s+\w+\s+(?:get|create)\w+\(\).*?return\s+\w+\.get\(\w+\)|HashMap<.*?,\s*.*?>",
            "proxy": r"class\s+\w+Proxy|implements\s+\w+",
            
            # Behavioral patterns
            "chain_of_responsibility": r"if\s*\(.*?\)\s*\{\s*.*?\}\s*else\s*\{\s*successor\.\w+\(|setNext\(\)|getNext\(\)",
            "command": r"(?:interface|abstract\s+class)\s+\w*Command|execute\(\)|(?:do|run|perform)\(\)",
            "interpreter": r"interpret\(\)|context",
            "iterator": r"(?:has|get)(?:Next|Previous)|next\(\)|previous\(\)|iterator\(\)",
            "mediator": r"class\s+\w+Mediator",
            "memento": r"class\s+\w+Memento|saveToMemento\(\)|restore(?:From)?Memento\(\)",
            "observer": r"(?:add|remove)(?:Observer|Listener)|notify\w*\(\)|update\(\)",
            "state": r"(?:interface|abstract\s+class)\s+\w+State|setState\(\)|getState\(\)",
            "strategy": r"(?:interface|abstract\s+class)\s+\w+Strategy|setStrategy\(\)",
            "template_method": r"abstract\s+\w+\s+\w+\(\).*?final\s+\w+\s+\w+\(\)",
            "visitor": r"(?:interface|abstract\s+class)\s+\w+Visitor|visit\(\)",
        }
        
        self.architectural_patterns = {
            "mvc": r"(?:class|interface)\s+\w+(?:Model|View|Controller)",
            "mvvm": r"(?:class|interface)\s+\w+(?:Model|View|ViewModel)",
            "layered": r"(?:class|interface)\s+\w+(?:DAO|Repository|Service|Controller)",
            "microservices": r"@SpringBootApplication|@Service|@RestController|@Microservice",
            "event_driven": r"event.*?listener|pub(?:lish)?/sub(?:scribe)?|on\w+Event",
            "pipelines": r"pipe(?:line)?.*?filter|\.pipe\(\)|\|>",
        }
        
        self.antipatterns = {
            "god_class": r"class\s+\w+\s*\{[^\}]{5000,}\}",  # Very large class
            "spaghetti_code": r"goto|if\s*\(.*?\)\s*goto|if\s*\(.*?\)\s*\{\s*if\s*\(.*?\)\s*\{\s*if\s*\(.*?\)\s*\{",  # Excessive nesting
            "copy_paste": r"",  # Not easily detectable with regex
            "magic_numbers": r"\W\d{4,}\W|\W[3-9]\d{2,}\W",  # Large numeric literals
            "blob": r"",  # Similar to god class
        }
    
    def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a pattern detector task"""
        task_type = task.task_type
        
        if task_type == "detect_patterns":
            return self._detect_patterns(task)
        
        elif task_type == "detect_antipatterns":
            return self._detect_antipatterns(task)
        
        elif task_type == "analyze_architecture":
            return self._analyze_architecture(task)
        
        elif task_type == "recommend_patterns":
            return self._recommend_patterns(task)
        
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    def _detect_patterns(self, task: Task) -> Dict[str, Any]:
        """Detect design patterns in code"""
        code = task.input_data.get("code", "")
        language = task.input_data.get("language", "")
        
        if not code or not language:
            return {"error": "Missing code or language information"}
        
        # Quick check for common pattern signatures
        pattern_matches = self._check_pattern_signatures(code)
        
        # Use the model for deeper analysis
        model = ModelInterface(capability="code_analysis")
        
        analysis_query = """
        Identify design patterns in this code. For each pattern found:
        1. Specify the pattern name and category (creational, structural, behavioral)
        2. Explain how the pattern is implemented
        3. Identify the key classes/components involved
        4. Assess whether the implementation follows pattern best practices
        """
        
        analysis = model.analyze_code(code, language, analysis_query)
        
        # Extract patterns from analysis
        patterns = []
        for issue in analysis.get("issues", []):
            # Issues in this case are not problems but observations
            if "pattern" in issue.get("description", "").lower():
                patterns.append({
                    "pattern": issue.get("description", ""),
                    "location": issue.get("line_numbers", []),
                    "recommendations": issue.get("recommendations", [])
                })
        
        # Combine with pattern matches from signature detection
        for pattern_type, matches in pattern_matches.items():
            if matches and not any(pattern_type.lower() in p.get("pattern", "").lower() for p in patterns):
                # Add pattern if not already detected
                patterns.append({
                    "pattern": f"{pattern_type.replace('_', ' ').title()} pattern",
                    "location": [m.get("line", 0) for m in matches],
                    "confidence": "medium",
                    "detection_method": "signature matching"
                })
        
        # Extract recommendations
        recommendations = []
        for recommendation in analysis.get("recommendations", []):
            if "pattern" in recommendation.lower():
                recommendations.append(recommendation)
        
        return {
            "patterns_count": len(patterns),
            "patterns": patterns,
            "recommendations": recommendations,
            "pattern_quality": self._assess_pattern_quality(patterns)
        }
    
    def _detect_antipatterns(self, task: Task) -> Dict[str, Any]:
        """Detect anti-patterns in code"""
        code = task.input_data.get("code", "")
        language = task.input_data.get("language", "")
        
        if not code or not language:
            return {"error": "Missing code or language information"}
        
        # Quick check for common anti-pattern signatures
        antipattern_matches = self._check_antipattern_signatures(code)
        
        # Use the model for deeper analysis
        model = ModelInterface(capability="code_analysis")
        
        analysis_query = """
        Identify anti-patterns and code smells in this code. For each anti-pattern found:
        1. Specify the anti-pattern name
        2. Explain why it's problematic
        3. Identify the key classes/components involved
        4. Suggest how to refactor the code to eliminate the anti-pattern
        """
        
        analysis = model.analyze_code(code, language, analysis_query)
        
        # Extract anti-patterns from analysis
        antipatterns = []
        for issue in analysis.get("issues", []):
            if any(ap in issue.get("description", "").lower() for ap in ["anti-pattern", "antipattern", "code smell", "bad practice"]):
                antipatterns.append({
                    "antipattern": issue.get("description", ""),
                    "severity": issue.get("severity", "medium"),
                    "location": issue.get("line_numbers", []),
                    "recommendations": issue.get("recommendations", [])
                })
        
        # Combine with anti-pattern matches from signature detection
        for antipattern_type, matches in antipattern_matches.items():
            if matches and not any(antipattern_type.lower() in ap.get("antipattern", "").lower() for ap in antipatterns):
                # Add anti-pattern if not already detected
                antipatterns.append({
                    "antipattern": f"{antipattern_type.replace('_', ' ').title()} anti-pattern",
                    "severity": "medium",
                    "location": [m.get("line", 0) for m in matches],
                    "confidence": "medium",
                    "detection_method": "signature matching"
                })
        
        # Extract recommendations
        recommendations = []
        for recommendation in analysis.get("recommendations", []):
            if any(term in recommendation.lower() for term in ["refactor", "improve", "eliminate", "anti-pattern"]):
                recommendations.append(recommendation)
        
        return {
            "antipatterns_count": len(antipatterns),
            "antipatterns": antipatterns,
            "recommendations": recommendations,
            "code_quality_impact": self._assess_antipattern_impact(antipatterns)
        }
    
    def _analyze_architecture(self, task: Task) -> Dict[str, Any]:
        """Analyze the overall architecture of the codebase"""
        code_files = task.input_data.get("code_files", {})
        language = task.input_data.get("language", "")
        
        if not code_files or not language:
            return {"error": "Missing code files or language information"}
        
        # Quick check for architectural patterns in all files
        architecture_patterns = {}
        for filename, code in code_files.items():
            matches = self._check_architecture_signatures(code)
            for pattern_type, pattern_matches in matches.items():
                if pattern_matches:
                    if pattern_type not in architecture_patterns:
                        architecture_patterns[pattern_type] = []
                    architecture_patterns[pattern_type].append({
                        "file": filename,
                        "matches": len(pattern_matches)
                    })
        
        # Use the model for architecture analysis
        model = ModelInterface(capability="code_analysis")
        
        # Prepare a summary of the codebase structure
        codebase_structure = "\n".join([f"File: {filename}\n```{language}\n{code[:500]}...\n```\n" 
                                       for filename, code in list(code_files.items())[:5]])
        
        prompt = f"""
        Analyze the architectural patterns in this codebase. The codebase contains multiple files. Here's a sample:
        
        {codebase_structure}
        
        Based on these files and file patterns, identify:
        1. The overall architectural style (e.g., MVC, microservices, layered)
        2. Component organization and relationships
        3. Architectural strengths and weaknesses
        4. Recommendations for architectural improvements
        
        Format your response as JSON with the following structure:
        {{
            "detected_architecture": "name",
            "confidence": "high/medium/low",
            "key_components": ["component1", "component2"],
            "strengths": ["strength1", "strength2"],
            "weaknesses": ["weakness1", "weakness2"],
            "recommendations": ["recommendation1", "recommendation2"]
        }}
        """
        
        system_message = "You are an expert in software architecture and design patterns. Analyze codebases to identify their architectural patterns, strengths, and areas for improvement."
        
        architecture_text = model.generate_text(prompt, system_message)
        
        # Extract JSON from the response
        try:
            import json
            import re
            
            json_match = re.search(r'(\{.*\})', architecture_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                architecture_analysis = json.loads(json_str)
            else:
                architecture_analysis = json.loads(architecture_text)
        
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw text
            architecture_analysis = {"architecture_text": architecture_text}
        
        # Add pattern matches from signature detection
        architecture_analysis["pattern_matches"] = architecture_patterns
        
        return architecture_analysis
    
    def _recommend_patterns(self, task: Task) -> Dict[str, Any]:
        """Recommend design patterns for specific code improvements"""
        code = task.input_data.get("code", "")
        language = task.input_data.get("language", "")
        issues = task.input_data.get("issues", [])
        
        if not code or not language:
            return {"error": "Missing code or language information"}
        
        # Use the model to recommend patterns
        model = ModelInterface(capability="code_analysis")
        
        prompt = f"""
        Recommend appropriate design patterns to improve this {language} code:
        
        ```{language}
        {code}
        ```
        
        Issues to address:
        {json.dumps(issues, indent=2) if issues else "General improvement of design and maintainability"}
        
        For each recommended pattern:
        1. Explain why this pattern is appropriate
        2. Describe how to implement it in this code
        3. Outline the benefits it would bring
        4. Note any potential drawbacks
        
        Format your response as JSON with the following structure:
        {{
            "recommended_patterns": [
                {{
                    "pattern": "name",
                    "category": "creational/structural/behavioral",
                    "rationale": "Why this pattern is appropriate",
                    "implementation_approach": "How to implement it",
                    "benefits": ["benefit1", "benefit2"],
                    "drawbacks": ["drawback1", "drawback2"]
                }}
            ]
        }}
        """
        
        system_message = "You are an expert in software design patterns and refactoring. Recommend appropriate patterns that will improve code quality, maintainability, and extensibility."
        
        recommendations_text = model.generate_text(prompt, system_message)
        
        # Extract JSON from the response
        try:
            import json
            import re
            
            json_match = re.search(r'(\{.*\})', recommendations_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                recommendations = json.loads(json_str)
            else:
                recommendations = json.loads(recommendations_text)
        
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw text
            recommendations = {"recommendations_text": recommendations_text}
        
        return recommendations
    
    def _check_pattern_signatures(self, code: str) -> Dict[str, List[Dict[str, Any]]]:
        """Check for common design pattern signatures using regex"""
        results = {}
        
        # Split code into lines for line number tracking
        lines = code.split('\n')
        
        for pattern_type, pattern in self.design_patterns.items():
            matches = []
            
            # Check for patterns
            pattern_matches = re.finditer(pattern, code, re.MULTILINE)
            for match in pattern_matches:
                # Find the line number by counting newlines before the match
                code_before_match = code[:match.start()]
                line_num = code_before_match.count('\n') + 1
                
                matches.append({
                    "line": line_num,
                    "code": match.group(0)
                })
            
            if matches:
                results[pattern_type] = matches
        
        return results
    
    def _check_architecture_signatures(self, code: str) -> Dict[str, List[Dict[str, Any]]]:
        """Check for architectural pattern signatures using regex"""
        results = {}
        
        # Split code into lines for line number tracking
        lines = code.split('\n')
        
        for pattern_type, pattern in self.architectural_patterns.items():
            matches = []
            
            # Check for patterns
            pattern_matches = re.finditer(pattern, code, re.MULTILINE)
            for match in pattern_matches:
                # Find the line number by counting newlines before the match
                code_before_match = code[:match.start()]
                line_num = code_before_match.count('\n') + 1
                
                matches.append({
                    "line": line_num,
                    "code": match.group(0)
                })
            
            if matches:
                results[pattern_type] = matches
        
        return results
    
    def _check_antipattern_signatures(self, code: str) -> Dict[str, List[Dict[str, Any]]]:
        """Check for anti-pattern signatures using regex"""
        results = {}
        
        # Split code into lines for line number tracking
        lines = code.split('\n')
        
        for antipattern_type, pattern in self.antipatterns.items():
            if not pattern:  # Skip empty patterns
                continue
                
            matches = []
            
            # Check for patterns
            pattern_matches = re.finditer(pattern, code, re.MULTILINE | re.DOTALL)
            for match in pattern_matches:
                # Find the line number by counting newlines before the match
                code_before_match = code[:match.start()]
                line_num = code_before_match.count('\n') + 1
                
                matches.append({
                    "line": line_num,
                    "code": match.group(0)[:100] + "..."  # Truncate long matches
                })
            
            if matches:
                results[antipattern_type] = matches
        
        return results
    
    def _assess_pattern_quality(self, patterns: List[Dict[str, Any]]) -> str:
        """Assess the quality of pattern implementations"""
        if not patterns:
            return "no patterns detected"
        
        # Count patterns by confidence/quality
        good_impl = 0
        ok_impl = 0
        poor_impl = 0
        
        for pattern in patterns:
            recs = pattern.get("recommendations", [])
            # If there are many recommendations, the implementation might be poor
            if len(recs) > 2:
                poor_impl += 1
            elif len(recs) > 0:
                ok_impl += 1
            else:
                good_impl += 1
        
        if poor_impl > good_impl + ok_impl:
            return "poor"
        elif poor_impl + ok_impl > good_impl:
            return "mixed"
        else:
            return "good"
    
    def _assess_antipattern_impact(self, antipatterns: List[Dict[str, Any]]) -> str:
        """Assess the impact of detected anti-patterns on code quality"""
        if not antipatterns:
            return "minimal"
        
        # Count antipatterns by severity
        high_severity = sum(1 for ap in antipatterns if ap.get("severity") == "high")
        medium_severity = sum(1 for ap in antipatterns if ap.get("severity") == "medium")
        
        if high_severity > 2:
            return "critical"
        elif high_severity > 0 or medium_severity > 2:
            return "significant"
        elif medium_severity > 0:
            return "moderate"
        else:
            return "minor"


class DependencyManagerAgent(ArchitectureAgent):
    """
    Agent that analyzes and manages dependencies between components.
    
    Capabilities:
    - Map dependencies between modules
    - Identify problematic dependencies
    - Suggest dependency simplifications
    - Detect and resolve circular dependencies
    """
    
    def __init__(self, agent_id: str = "dependency_manager", preferred_model: Optional[str] = None):
        capabilities = [
            "dependency_mapping", "dependency_analysis", 
            "circular_dependency_detection", "dependency_optimization"
        ]
        
        super().__init__(
            agent_id=agent_id,
            capabilities=capabilities,
            preferred_model=preferred_model
        )
        
        # Dependency manager specific attributes
        self.import_patterns = {
            "python": r"(?:import|from)\s+([.\w]+)(?:\s+import\s+)?",
            "javascript": r"(?:import|require)\s*\(\s*['\"]([^'\"]+)['\"]",
            "typescript": r"import\s+.*?from\s+['\"]([^'\"]+)['\"]",
            "java": r"import\s+([.\w]+);",
            "csharp": r"using\s+([.\w]+);",
            "go": r"import\s+[('\"]([^)\"']+)[)\"']",
            "ruby": r"require\s+['\"]([^'\"]+)['\"]",
            "php": r"(?:require|include|use)\s+['\"]?([^;'\"]*)(?:['\"])?;?"
        }
    
    def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a dependency manager task"""
        task_type = task.task_type
        
        if task_type == "map_dependencies":
            return self._map_dependencies(task)
        
        elif task_type == "analyze_dependencies":
            return self._analyze_dependencies(task)
        
        elif task_type == "detect_circular_dependencies":
            return self._detect_circular_dependencies(task)
        
        elif task_type == "optimize_dependencies":
            return self._optimize_dependencies(task)
        
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    def _map_dependencies(self, task: Task) -> Dict[str, Any]:
        """Map dependencies between files and modules"""
        code_files = task.input_data.get("code_files", {})
        language = task.input_data.get("language", "")
        
        if not code_files or not language:
            return {"error": "Missing code files or language information"}
        
        # Extract dependencies from each file
        dependencies = {}
        file_dependencies = {}
        
        for filename, code in code_files.items():
            file_imports = self._extract_imports(code, language)
            file_dependencies[filename] = file_imports
            
            # Aggregate module dependencies
            for imported_module in file_imports:
                module_name = self._extract_module_name(imported_module)
                
                if module_name not in dependencies:
                    dependencies[module_name] = {"imports": set(), "imported_by": set()}
                
                dependencies[module_name]["imported_by"].add(filename)
                
                # Record which module imports this one
                source_module = self._extract_module_name(filename)
                if source_module != module_name:  # Avoid self-references
                    if source_module not in dependencies:
                        dependencies[source_module] = {"imports": set(), "imported_by": set()}
                    
                    dependencies[source_module]["imports"].add(module_name)
        
        # Convert sets to lists for JSON serialization
        for module in dependencies:
            dependencies[module]["imports"] = list(dependencies[module]["imports"])
            dependencies[module]["imported_by"] = list(dependencies[module]["imported_by"])
        
        # Calculate dependency metrics
        dependency_counts = {module: len(info["imports"]) for module, info in dependencies.items()}
        
        most_dependent = max(dependency_counts.items(), key=lambda x: x[1]) if dependency_counts else ("none", 0)
        
        # Count how many modules import each module
        import_counts = {module: len(info["imported_by"]) for module, info in dependencies.items()}
        
        most_imported = max(import_counts.items(), key=lambda x: x[1]) if import_counts else ("none", 0)
        
        return {
            "module_dependencies": dependencies,
            "file_dependencies": file_dependencies,
            "most_dependent_module": {
                "name": most_dependent[0],
                "dependency_count": most_dependent[1]
            },
            "most_imported_module": {
                "name": most_imported[0],
                "imported_by_count": most_imported[1]
            }
        }
    
    def _analyze_dependencies(self, task: Task) -> Dict[str, Any]:
        """Analyze dependencies for issues and improvement opportunities"""
        dependencies = task.input_data.get("module_dependencies", {})
        
        if not dependencies:
            return {"error": "Missing dependency information"}
        
        # Calculate dependency metrics
        coupling_scores = {}
        core_modules = []
        isolated_modules = []
        brittle_modules = []
        stable_modules = []
        
        for module, info in dependencies.items():
            imports = info.get("imports", [])
            imported_by = info.get("imported_by", [])
            
            # Calculate afferent and efferent coupling
            efferent = len(imports)  # Dependencies on other modules
            afferent = len(imported_by)  # Modules depending on this one
            
            # Instability = efferent / (efferent + afferent)
            # 0 = stable, 1 = unstable
            instability = efferent / (efferent + afferent) if (efferent + afferent) > 0 else 0
            
            # Store coupling score
            coupling_scores[module] = {
                "efferent": efferent,
                "afferent": afferent,
                "instability": instability
            }
            
            # Categorize modules
            if afferent > 3 and efferent > 3:
                core_modules.append(module)
            elif afferent == 0 and efferent == 0:
                isolated_modules.append(module)
            elif instability > 0.7:  # Brittle modules are highly unstable
                brittle_modules.append(module)
            elif instability < 0.3:  # Stable modules are hard to change
                stable_modules.append(module)
        
        # Identify problematic dependencies
        problematic_dependencies = []
        
        for module, info in dependencies.items():
            imports = info.get("imports", [])
            
            # Check if this module depends on brittle modules
            brittle_dependencies = [dep for dep in imports if dep in brittle_modules]
            
            if brittle_dependencies:
                problematic_dependencies.append({
                    "module": module,
                    "depends_on_brittle": brittle_dependencies,
                    "risk": "high" if len(brittle_dependencies) > 2 else "medium"
                })
            
            # Check for dependency on stable modules from stable modules (could be an abstraction issue)
            if module in stable_modules:
                stable_dependencies = [dep for dep in imports if dep in stable_modules]
                
                if stable_dependencies:
                    problematic_dependencies.append({
                        "module": module,
                        "stable_depends_on_stable": stable_dependencies,
                        "risk": "medium"
                    })
        
        # Generate recommendations
        recommendations = []
        
        if brittle_modules:
            recommendations.append(f"Improve stability of brittle modules: {', '.join(brittle_modules[:3])}")
        
        if problematic_dependencies:
            recommendations.append("Review and refactor problematic dependencies between modules")
        
        if isolated_modules:
            recommendations.append(f"Investigate isolated modules: {', '.join(isolated_modules[:3])}")
        
        return {
            "coupling_scores": coupling_scores,
            "core_modules": core_modules,
            "isolated_modules": isolated_modules,
            "brittle_modules": brittle_modules,
            "stable_modules": stable_modules,
            "problematic_dependencies": problematic_dependencies,
            "recommendations": recommendations
        }
    
    def _detect_circular_dependencies(self, task: Task) -> Dict[str, Any]:
        """Detect circular dependencies between modules"""
        dependencies = task.input_data.get("module_dependencies", {})
        
        if not dependencies:
            return {"error": "Missing dependency information"}
        
        # Create a directed graph from the dependencies
        graph = {}
        for module, info in dependencies.items():
            imports = info.get("imports", [])
            graph[module] = imports
        
        # Find all cycles in the graph
        cycles = self._find_cycles(graph)
        
        # Categorize cycles by size
        cycles_by_size = {}
        for cycle in cycles:
            size = len(cycle)
            if size not in cycles_by_size:
                cycles_by_size[size] = []
            cycles_by_size[size].append(cycle)
        
        # Generate recommendations for each cycle
        cycle_recommendations = []
        
        for cycle in cycles:
            # For each cycle, suggest breaking at the least stable module
            instability_scores = {}
            
            for module in cycle:
                imports = dependencies.get(module, {}).get("imports", [])
                imported_by = dependencies.get(module, {}).get("imported_by", [])
                
                efferent = len(imports)
                afferent = len(imported_by)
                
                instability = efferent / (efferent + afferent) if (efferent + afferent) > 0 else 0
                instability_scores[module] = instability
            
            # Find most unstable module in the cycle
            most_unstable = max(instability_scores.items(), key=lambda x: x[1])
            
            # Generate recommendation
            cycle_recommendations.append({
                "cycle": cycle,
                "break_at": most_unstable[0],
                "instability": most_unstable[1],
                "approach": "Introduce abstraction or move common functionality"
            })
        
        return {
            "cycles_count": len(cycles),
            "cycles": cycles,
            "cycles_by_size": cycles_by_size,
            "cycle_recommendations": cycle_recommendations,
            "has_circular_dependencies": len(cycles) > 0
        }
    
    def _optimize_dependencies(self, task: Task) -> Dict[str, Any]:
        """Suggest dependency optimizations"""
        dependencies = task.input_data.get("module_dependencies", {})
        circular_dependencies = task.input_data.get("cycles", [])
        problematic_dependencies = task.input_data.get("problematic_dependencies", [])
        
        if not dependencies:
            return {"error": "Missing dependency information"}
        
        # Use the model to generate optimization suggestions
        model = ModelInterface(capability="code_analysis")
        
        # Prepare dependency information for the model
        dependency_info = json.dumps({
            "dependencies": dependencies,
            "circular_dependencies": circular_dependencies,
            "problematic_dependencies": problematic_dependencies
        }, indent=2)
        
        prompt = f"""
        Suggest optimizations for the following dependency structure:
        
        {dependency_info}
        
        Provide specific recommendations for:
        1. Breaking circular dependencies
        2. Addressing problematic dependencies
        3. Improving the overall dependency structure
        
        For each recommendation, explain:
        - What should be changed
        - How it should be implemented
        - The benefits of the change
        
        Format your response as JSON with the following structure:
        {{
            "recommendations": [
                {{
                    "target": "module name or dependency relationship",
                    "issue": "description of the issue",
                    "recommendation": "specific recommendation",
                    "implementation": "how to implement the change",
                    "benefits": ["benefit1", "benefit2"]
                }}
            ],
            "architectural_improvements": ["improvement1", "improvement2"]
        }}
        """
        
        system_message = "You are an expert in software architecture and dependency management. Provide specific, actionable recommendations for improving dependency structures."
        
        optimization_text = model.generate_text(prompt, system_message)
        
        # Extract JSON from the response
        try:
            import json
            import re
            
            json_match = re.search(r'(\{.*\})', optimization_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                optimizations = json.loads(json_str)
            else:
                optimizations = json.loads(optimization_text)
        
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw text
            optimizations = {"optimization_text": optimization_text}
        
        return optimizations
    
    def _extract_imports(self, code: str, language: str) -> List[str]:
        """Extract imports from code using regex"""
        pattern = self.import_patterns.get(language)
        if not pattern:
            return []
        
        imports = []
        matches = re.finditer(pattern, code, re.MULTILINE)
        for match in matches:
            # Extract the imported module
            imported_module = match.group(1).strip()
            
            # Skip empty matches or common standard libraries
            if imported_module and not self._is_standard_library(imported_module, language):
                imports.append(imported_module)
        
        return imports
    
    def _is_standard_library(self, module_name: str, language: str) -> bool:
        """Check if a module is part of the standard library"""
        standard_libs = {
            "python": ["os", "sys", "time", "datetime", "math", "random", "re", "json", "collections"],
            "javascript": ["fs", "path", "http", "https", "url", "util", "querystring"],
            "java": ["java.lang", "java.util", "java.io"],
            "csharp": ["System", "System.Collections", "System.IO"],
            # Add other languages as needed
        }
        
        libs = standard_libs.get(language, [])
        
        return any(module_name.startswith(lib) for lib in libs)
    
    def _extract_module_name(self, path: str) -> str:
        """Extract module name from a file path or import statement"""
        # Remove extension if present
        if "." in path and not path.startswith("."):
            path = path.split(".")[-2]
        
        # Extract last component of path
        if "/" in path:
            path = path.split("/")[-1]
        elif "\\" in path:
            path = path.split("\\")[-1]
        
        return path
    
    def _find_cycles(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """Find all cycles in a directed graph using DFS"""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node, path):
            nonlocal cycles, visited, rec_stack
            
            # Mark current node as visited and add to recursion stack
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            # Check all neighbors
            for neighbor in graph.get(node, []):
                # If not visited, recursively process
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                
                # If in recursion stack, we found a cycle
                elif neighbor in rec_stack:
                    # Get the cycle from the path
                    start_idx = path.index(neighbor)
                    cycle = path[start_idx:]
                    
                    # Add if not already found
                    if cycle not in cycles:
                        cycles.append(cycle)
            
            # Remove from recursion stack
            rec_stack.remove(node)
        
        # Check all nodes
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles


# For brevity, I'll omit the implementation of the remaining specialized agents
# including ServiceBoundaryAnalyzer, InfrastructureAuditor, SchemaOptimizer, 
# and others. These would follow a similar pattern to the ones implemented above.


# =============================================================================
# Agent Registration Function
# =============================================================================

def register_all_agents():
    """Register all specialized agents with the protocol server"""
    from protocol_server import start_server
    
    # Start the protocol server if not already running
    server = start_server()
    
    # Register Code Quality agents
    style_enforcer = StyleEnforcerAgent()
    style_enforcer.start()
    
    bug_hunter = BugHunterAgent()
    bug_hunter.start()
    
    performance_optimizer = PerformanceOptimizerAgent()
    performance_optimizer.start()
    
    test_coverage = TestCoverageAgent()
    test_coverage.start()
    
    # Register Architecture agents
    pattern_detector = PatternDetectorAgent()
    pattern_detector.start()
    
    dependency_manager = DependencyManagerAgent()
    dependency_manager.start()
    
    # Database Agents
    try:
        # Import the database migration agent
        from database_migration_agent import DatabaseMigrationAgent
        db_migration_agent = DatabaseMigrationAgent()
        db_migration_agent.start()
        has_db_migration_agent = True
    except ImportError:
        logger.warning("Database Migration Agent not available")
        has_db_migration_agent = False
    
    # In a full implementation, we would register all specialized agents here
    
    # Build the agents dictionary
    agents = {
        "style_enforcer": style_enforcer,
        "bug_hunter": bug_hunter,
        "performance_optimizer": performance_optimizer,
        "test_coverage": test_coverage,
        "pattern_detector": pattern_detector,
        "dependency_manager": dependency_manager
    }
    
    # Add database agents if available
    if has_db_migration_agent:
        agents["db_migration_agent"] = db_migration_agent
    
    return agents


if __name__ == "__main__":
    # When run directly, register all agents and keep running
    agents = register_all_agents()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down agents...")
        for agent in agents.values():
            agent.stop()