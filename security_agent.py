"""
Security Agent Module

This module implements a specialized AI agent for security analysis of code repositories.
It can identify security vulnerabilities, suggest security improvements, and provide
in-depth security reports.
"""

import os
import time
import logging
import json
from typing import Dict, List, Any, Optional
import re

from agent_base import Agent, AgentCategory, Task

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SecurityVulnerability:
    """
    Represents a security vulnerability found in code.
    """
    
    def __init__(
        self,
        vulnerability_id: str,
        severity: str,  # "critical", "high", "medium", "low", "info"
        name: str,
        description: str,
        file_path: str,
        line_number: Optional[int] = None,
        code_snippet: Optional[str] = None,
        recommendation: Optional[str] = None,
        cwe_id: Optional[str] = None,  # Common Weakness Enumeration ID
        references: Optional[List[str]] = None
    ):
        """
        Initialize a new security vulnerability.
        
        Args:
            vulnerability_id: Unique identifier for this vulnerability
            severity: Severity level (critical, high, medium, low, info)
            name: Short name or title of the vulnerability
            description: Detailed description of the vulnerability
            file_path: Path to the file containing the vulnerability
            line_number: Optional line number where the vulnerability occurs
            code_snippet: Optional code snippet showing the vulnerability
            recommendation: Optional recommended fix or mitigation
            cwe_id: Optional CWE ID for this type of vulnerability
            references: Optional list of reference URLs
        """
        self.vulnerability_id = vulnerability_id
        self.severity = severity
        self.name = name
        self.description = description
        self.file_path = file_path
        self.line_number = line_number
        self.code_snippet = code_snippet
        self.recommendation = recommendation
        self.cwe_id = cwe_id
        self.references = references or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the vulnerability to a dictionary for serialization"""
        return {
            "vulnerability_id": self.vulnerability_id,
            "severity": self.severity,
            "name": self.name,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "recommendation": self.recommendation,
            "cwe_id": self.cwe_id,
            "references": self.references
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecurityVulnerability':
        """Create a vulnerability from a dictionary"""
        return cls(
            vulnerability_id=data["vulnerability_id"],
            severity=data["severity"],
            name=data["name"],
            description=data["description"],
            file_path=data["file_path"],
            line_number=data.get("line_number"),
            code_snippet=data.get("code_snippet"),
            recommendation=data.get("recommendation"),
            cwe_id=data.get("cwe_id"),
            references=data.get("references", [])
        )


class SecurityAgent(Agent):
    """
    Agent specialized in security analysis of code repositories.
    
    This agent can identify security vulnerabilities, provide recommendations,
    and generate comprehensive security reports.
    """
    
    def __init__(
        self,
        agent_id: str = "security_agent",
        capabilities: List[str] = None,
        preferred_model: Optional[str] = None
    ):
        """
        Initialize a new security agent.
        
        Args:
            agent_id: Unique identifier for this agent
            capabilities: List of capabilities this agent provides
            preferred_model: Optional preferred AI model to use
        """
        # Set default capabilities if none provided
        if capabilities is None:
            capabilities = [
                "security_scan",
                "vulnerability_detection",
                "dependency_check",
                "secret_detection",
                "security_report_generation",
                "secure_coding_recommendations"
            ]
        
        # Initialize the base Agent class
        super().__init__(agent_id, AgentCategory.ARCHITECTURE, capabilities, preferred_model)
        
        # Agent-specific state
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        self.current_scan_results = {}
    
    def _load_vulnerability_patterns(self) -> Dict[str, Any]:
        """
        Load vulnerability patterns from configuration.
        
        Returns:
            Dictionary of patterns mapped by language and vulnerability type
        """
        # In a real implementation, this would load from a database or file
        # Here we're using a simplified in-memory configuration
        patterns = {
            "python": {
                "sql_injection": [
                    r"execute\(\s*[\"'].*?\%.*?[\"']\s*%.*?\)",
                    r"cursor\.execute\(\s*[\"'].*?\+.*?",
                ],
                "command_injection": [
                    r"os\.system\(\s*.*?\+.*?\)",
                    r"subprocess\.(?:call|Popen|run)\(\s*(?:.*?\+.*?|.*?format\(.*?\)|f[\"'].*?{.*?}.*?[\"'])",
                ],
                "insecure_deserialization": [
                    r"pickle\.loads?\(",
                    r"yaml\.(?:load|unsafe_load)\(",
                ],
                "hardcoded_secrets": [
                    r"(?:password|secret|token|key)\s*=\s*[\"'](?!.*?\{\{.*?\}\})([^\"\s]{5,})[\"']",
                    r"api_key\s*=\s*[\"']([^\"\s]{5,})[\"']",
                ],
            },
            "javascript": {
                "xss": [
                    r"\.innerHTML\s*=\s*.*?\+.*?",
                    r"document\.write\(\s*.*?\+.*?\)",
                ],
                "sql_injection": [
                    r"(?:execute|query)\(\s*[\"'].*?\+.*?",
                    r"(?:db|database|connection)\.query\(\s*[\"'].*?\+.*?",
                ],
                "insecure_randomness": [
                    r"Math\.random\(\)",
                ],
                "hardcoded_secrets": [
                    r"(?:password|secret|token|key|apiKey)\s*=\s*[\"']([^\"\s]{5,})[\"']",
                    r"(?:password|secret|token|key|apiKey):\s*[\"']([^\"\s]{5,})[\"']",
                ],
            },
            "java": {
                "sql_injection": [
                    r"(?:execute|prepareStatement|createStatement)\(\s*[\"'].*?\+.*?",
                ],
                "xxe": [
                    r"DocumentBuilderFactory\s*\.\s*newInstance\(\)",
                    r"SAXParserFactory\s*\.\s*newInstance\(\)",
                ],
                "weak_encryption": [
                    r"DES",
                    r"MD5",
                ],
            },
        }
        
        return patterns
    
    def _get_max_concurrent_tasks(self) -> int:
        """Get the maximum number of concurrent tasks this agent can handle"""
        return 3
    
    def _execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a security analysis task.
        
        Args:
            task: Task to execute
        
        Returns:
            Task result as a dictionary
            
        The task parameters should include:
            - 'action': The security action to perform
                (scan, dependency_check, secret_detection, report)
            - 'repository_path': Path to the repository to analyze
            - 'languages': List of programming languages to focus on
            - 'scan_depth': Depth of the scan (quick, standard, deep)
            - Additional action-specific parameters
        """
        parameters = task.parameters
        action = parameters.get("action", "scan")
        repository_path = parameters.get("repository_path", "./")
        languages = parameters.get("languages", ["python", "javascript", "java"])
        scan_depth = parameters.get("scan_depth", "standard")
        
        result = {"success": False, "error": None, "data": None}
        
        try:
            if action == "scan":
                scan_result = self._perform_security_scan(repository_path, languages, scan_depth)
                result = {
                    "success": True,
                    "data": {
                        "scan_id": scan_result["scan_id"],
                        "vulnerabilities": scan_result["vulnerabilities"],
                        "summary": scan_result["summary"],
                        "timestamp": scan_result["timestamp"]
                    }
                }
                
                # Store for later reference
                self.current_scan_results[scan_result["scan_id"]] = scan_result
                
            elif action == "dependency_check":
                dependency_result = self._check_dependencies(repository_path, languages)
                result = {
                    "success": True,
                    "data": dependency_result
                }
                
            elif action == "secret_detection":
                secrets_result = self._detect_secrets(repository_path)
                result = {
                    "success": True,
                    "data": secrets_result
                }
                
            elif action == "report":
                scan_id = parameters.get("scan_id")
                if not scan_id or scan_id not in self.current_scan_results:
                    raise ValueError(f"Invalid or missing scan_id: {scan_id}")
                
                report_result = self._generate_security_report(scan_id)
                result = {
                    "success": True,
                    "data": report_result
                }
            
            else:
                raise ValueError(f"Unknown security action: {action}")
                
        except Exception as e:
            logger.error(f"Error in security task execution: {str(e)}")
            result["error"] = str(e)
            
        return result
    
    def _perform_security_scan(
        self,
        repository_path: str,
        languages: List[str],
        scan_depth: str
    ) -> Dict[str, Any]:
        """
        Perform a security scan on a repository.
        
        Args:
            repository_path: Path to the repository to scan
            languages: List of programming languages to scan
            scan_depth: Depth of the scan (quick, standard, deep)
            
        Returns:
            Dictionary containing scan results
        """
        # Generate a unique scan ID
        scan_id = f"scan_{int(time.time())}"
        
        # In a real implementation, this would use a security analysis library 
        # or integrate with tools like Bandit, ESLint, etc.
        # Here we'll use a simplified pattern-matching approach
        
        # Track vulnerabilities found
        vulnerabilities = []
        
        # Collect files to scan
        files_to_scan = self._collect_files(repository_path, languages)
        
        # Determine pattern set based on scan depth
        pattern_multiplier = {
            "quick": 0.5,    # Use less patterns for quick scan
            "standard": 1.0, # Use all patterns for standard scan
            "deep": 1.5      # Deeper scan would use more complex patterns
        }.get(scan_depth, 1.0)
        
        # Scan each file
        for file_path, language in files_to_scan:
            file_vulnerabilities = self._scan_file(file_path, language, pattern_multiplier)
            vulnerabilities.extend(file_vulnerabilities)
        
        # Generate summary
        vulnerability_count = len(vulnerabilities)
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        
        for vuln in vulnerabilities:
            severity_counts[vuln.severity] = severity_counts.get(vuln.severity, 0) + 1
        
        summary = {
            "total_files_scanned": len(files_to_scan),
            "vulnerability_count": vulnerability_count,
            "severity_counts": severity_counts,
            "risk_score": self._calculate_risk_score(severity_counts)
        }
        
        return {
            "scan_id": scan_id,
            "repository_path": repository_path,
            "languages": languages,
            "scan_depth": scan_depth,
            "vulnerabilities": [v.to_dict() for v in vulnerabilities],
            "summary": summary,
            "timestamp": time.time()
        }
    
    def _collect_files(self, repository_path: str, languages: List[str]) -> List[tuple]:
        """
        Collect files to scan from a repository.
        
        Args:
            repository_path: Path to the repository
            languages: List of programming languages to include
            
        Returns:
            List of (file_path, language) tuples
        """
        # Map language to file extensions
        language_extensions = {
            "python": [".py"],
            "javascript": [".js", ".jsx", ".ts", ".tsx"],
            "java": [".java"],
            "csharp": [".cs"],
            "go": [".go"],
            "ruby": [".rb"],
            "php": [".php"],
        }
        
        # Get extensions for selected languages
        extensions = []
        for lang in languages:
            if lang in language_extensions:
                extensions.extend(language_extensions[lang])
        
        # Collect files
        files = []
        for root, _, filenames in os.walk(repository_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                _, ext = os.path.splitext(filename)
                
                if ext in extensions:
                    # Determine language based on extension
                    file_language = None
                    for lang, exts in language_extensions.items():
                        if ext in exts:
                            file_language = lang
                            break
                    
                    if file_language:
                        files.append((file_path, file_language))
        
        return files
    
    def _scan_file(
        self,
        file_path: str,
        language: str,
        pattern_multiplier: float
    ) -> List[SecurityVulnerability]:
        """
        Scan a single file for security vulnerabilities.
        
        Args:
            file_path: Path to the file to scan
            language: Programming language of the file
            pattern_multiplier: Multiplier for pattern set (scan depth)
            
        Returns:
            List of SecurityVulnerability objects found
        """
        vulnerabilities = []
        
        try:
            # Get patterns for this language
            if language not in self.vulnerability_patterns:
                return []
            
            language_patterns = self.vulnerability_patterns[language]
            
            # Read file content
            with open(file_path, 'r', errors='ignore') as f:
                content = f.read()
                
            # Generate line-indexed content for snippets
            lines = content.split('\n')
            
            # Check each vulnerability type
            for vuln_type, patterns in language_patterns.items():
                # Apply pattern multiplier
                num_patterns = max(1, int(len(patterns) * pattern_multiplier))
                patterns_to_use = patterns[:num_patterns]
                
                # Check each pattern
                for pattern in patterns_to_use:
                    matches = re.finditer(pattern, content)
                    
                    for match in matches:
                        # Get line number
                        line_count = content[:match.start()].count('\n') + 1
                        
                        # Get code snippet
                        start_line = max(0, line_count - 2)
                        end_line = min(len(lines), line_count + 2)
                        snippet = '\n'.join(lines[start_line:end_line])
                        
                        # Determine severity based on vulnerability type
                        severity = self._get_severity_for_vulnerability(vuln_type)
                        
                        # Create vulnerability object
                        vuln = SecurityVulnerability(
                            vulnerability_id=f"VULN-{int(time.time())}-{len(vulnerabilities)}",
                            severity=severity,
                            name=self._get_name_for_vulnerability(vuln_type),
                            description=self._get_description_for_vulnerability(vuln_type),
                            file_path=file_path,
                            line_number=line_count,
                            code_snippet=snippet,
                            recommendation=self._get_recommendation_for_vulnerability(vuln_type),
                            cwe_id=self._get_cwe_for_vulnerability(vuln_type),
                            references=self._get_references_for_vulnerability(vuln_type)
                        )
                        
                        vulnerabilities.append(vuln)
        
        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {str(e)}")
        
        return vulnerabilities
    
    def _get_severity_for_vulnerability(self, vuln_type: str) -> str:
        """Map vulnerability type to severity level"""
        severity_map = {
            "sql_injection": "critical",
            "command_injection": "critical",
            "xss": "high",
            "xxe": "high",
            "insecure_deserialization": "high",
            "weak_encryption": "medium",
            "insecure_randomness": "medium",
            "hardcoded_secrets": "high"
        }
        return severity_map.get(vuln_type, "medium")
    
    def _get_name_for_vulnerability(self, vuln_type: str) -> str:
        """Get human-readable name for vulnerability type"""
        name_map = {
            "sql_injection": "SQL Injection Vulnerability",
            "command_injection": "Command Injection Vulnerability",
            "xss": "Cross-site Scripting (XSS) Vulnerability",
            "xxe": "XML External Entity (XXE) Vulnerability",
            "insecure_deserialization": "Insecure Deserialization",
            "weak_encryption": "Weak Encryption Algorithm",
            "insecure_randomness": "Insecure Random Number Generation",
            "hardcoded_secrets": "Hardcoded Secret or Credential"
        }
        return name_map.get(vuln_type, f"Unknown Vulnerability ({vuln_type})")
    
    def _get_description_for_vulnerability(self, vuln_type: str) -> str:
        """Get description for vulnerability type"""
        description_map = {
            "sql_injection": "SQL injection vulnerabilities occur when user-supplied data is not properly validated and directly included in SQL queries, allowing attackers to manipulate the query structure.",
            "command_injection": "Command injection vulnerabilities allow attackers to execute arbitrary commands on the host operating system via a vulnerable application.",
            "xss": "Cross-site scripting vulnerabilities enable attackers to inject client-side scripts into web pages viewed by others, bypassing same-origin policies.",
            "xxe": "XML External Entity vulnerabilities allow attackers to access server file system files and interact with backend systems through manipulated XML inputs.",
            "insecure_deserialization": "Insecure deserialization can allow an attacker to execute arbitrary code when untrusted data is used to reconstruct objects.",
            "weak_encryption": "Using cryptographically weak algorithms can lead to data exposure since these algorithms may be easily broken by attackers.",
            "insecure_randomness": "Insecure random number generation may lead to predictable values being used in security-sensitive contexts.",
            "hardcoded_secrets": "Hardcoded credentials or secrets in source code present a security risk as they can be discovered through code access or reverse engineering."
        }
        return description_map.get(vuln_type, "A potential security vulnerability was detected in the code.")
    
    def _get_recommendation_for_vulnerability(self, vuln_type: str) -> str:
        """Get recommendation for vulnerability type"""
        recommendation_map = {
            "sql_injection": "Use parameterized queries or prepared statements instead of building SQL statements with string concatenation. Implement proper input validation and sanitization.",
            "command_injection": "Avoid using shell commands with user-supplied input. If necessary, use safe APIs that don't invoke command shells and implement strict input validation.",
            "xss": "Sanitize and validate all user input. Use context-specific output encoding and consider Content Security Policy (CSP) implementation.",
            "xxe": "Disable external entity processing in XML parsers. Use less complex data formats like JSON if possible.",
            "insecure_deserialization": "Avoid deserializing untrusted data. Implement integrity checks and type checks before deserialization.",
            "weak_encryption": "Update to modern, strong encryption algorithms. Use industry-standard libraries and keep cryptographic implementations up to date.",
            "insecure_randomness": "Use cryptographically secure random number generators provided by the language or framework (e.g., secrets module in Python).",
            "hardcoded_secrets": "Remove hardcoded credentials from source code. Use environment variables, secure vaults, or configuration services for secrets management."
        }
        return recommendation_map.get(vuln_type, "Review the code for security issues and follow secure coding practices.")
    
    def _get_cwe_for_vulnerability(self, vuln_type: str) -> Optional[str]:
        """Get CWE ID for vulnerability type"""
        cwe_map = {
            "sql_injection": "CWE-89",
            "command_injection": "CWE-77",
            "xss": "CWE-79",
            "xxe": "CWE-611",
            "insecure_deserialization": "CWE-502",
            "weak_encryption": "CWE-327",
            "insecure_randomness": "CWE-338",
            "hardcoded_secrets": "CWE-798"
        }
        return cwe_map.get(vuln_type)
    
    def _get_references_for_vulnerability(self, vuln_type: str) -> List[str]:
        """Get reference URLs for vulnerability type"""
        reference_map = {
            "sql_injection": [
                "https://owasp.org/www-community/attacks/SQL_Injection",
                "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html"
            ],
            "command_injection": [
                "https://owasp.org/www-community/attacks/Command_Injection",
                "https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html"
            ],
            "xss": [
                "https://owasp.org/www-community/attacks/xss/",
                "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html"
            ],
            "xxe": [
                "https://owasp.org/www-community/vulnerabilities/XML_External_Entity_(XXE)_Processing",
                "https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html"
            ],
            "insecure_deserialization": [
                "https://owasp.org/www-project-top-ten/2017/A8_2017-Insecure_Deserialization",
                "https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html"
            ],
            "weak_encryption": [
                "https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure",
                "https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html"
            ],
            "insecure_randomness": [
                "https://owasp.org/www-community/vulnerabilities/Insecure_Randomness",
                "https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html"
            ],
            "hardcoded_secrets": [
                "https://owasp.org/www-project-top-ten/2017/A2_2017-Broken_Authentication",
                "https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html"
            ]
        }
        return reference_map.get(vuln_type, [])
    
    def _calculate_risk_score(self, severity_counts: Dict[str, int]) -> float:
        """
        Calculate an overall risk score based on vulnerability severity counts.
        
        Args:
            severity_counts: Dictionary mapping severity levels to counts
            
        Returns:
            Risk score between 0.0 and 10.0
        """
        # Weights for each severity level
        weights = {
            "critical": 10.0,
            "high": 7.0,
            "medium": 4.0,
            "low": 1.0,
            "info": 0.1
        }
        
        # Calculate weighted sum
        weighted_sum = sum(weights[severity] * count for severity, count in severity_counts.items())
        
        # Calculate total count
        total_count = sum(severity_counts.values())
        
        if total_count == 0:
            return 0.0
        
        # Base score
        base_score = weighted_sum / total_count
        
        # Apply diminishing returns for many vulnerabilities
        # Cap at 10.0
        return min(10.0, base_score * (1 + 0.5 * (1 - 2.71 ** (-0.1 * total_count))))
    
    def _check_dependencies(
        self,
        repository_path: str,
        languages: List[str]
    ) -> Dict[str, Any]:
        """
        Check dependencies for known vulnerabilities.
        
        Args:
            repository_path: Path to the repository
            languages: List of programming languages to check
            
        Returns:
            Dictionary containing dependency check results
        """
        # In a real implementation, this would integrate with tools like
        # OWASP Dependency Check, NPM Audit, or similar
        
        # Example implementation
        dependency_files = {
            "python": ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile", "poetry.lock"],
            "javascript": ["package.json", "package-lock.json", "yarn.lock", "npm-shrinkwrap.json"],
            "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
        }
        
        results = {
            "vulnerable_dependencies": [],
            "dependency_files_found": [],
            "languages_checked": languages,
            "timestamp": time.time()
        }
        
        # Find dependency files
        for lang in languages:
            if lang in dependency_files:
                for file_pattern in dependency_files[lang]:
                    for root, _, files in os.walk(repository_path):
                        if file_pattern in files:
                            file_path = os.path.join(root, file_pattern)
                            results["dependency_files_found"].append({
                                "language": lang,
                                "file_path": file_path,
                                "file_type": file_pattern
                            })
                            
                            # Mock vulnerable dependency detection
                            if lang == "python" and file_pattern == "requirements.txt":
                                with open(file_path, 'r', errors='ignore') as f:
                                    content = f.read()
                                    # Example check - would be more sophisticated in real implementation
                                    if "flask==0.12.2" in content:
                                        results["vulnerable_dependencies"].append({
                                            "name": "flask",
                                            "version": "0.12.2",
                                            "language": "python",
                                            "vulnerability": "Multiple vulnerabilities including session fixation",
                                            "recommendation": "Upgrade to Flask 2.0.0 or later",
                                            "severity": "high",
                                            "file_path": file_path
                                        })
                                    if "django==1.11" in content:
                                        results["vulnerable_dependencies"].append({
                                            "name": "django",
                                            "version": "1.11",
                                            "language": "python",
                                            "vulnerability": "Multiple CVEs including XSS vulnerabilities",
                                            "recommendation": "Upgrade to Django 3.2 or later",
                                            "severity": "high",
                                            "file_path": file_path
                                        })
                            
                            elif lang == "javascript" and file_pattern == "package.json":
                                with open(file_path, 'r', errors='ignore') as f:
                                    try:
                                        data = json.load(f)
                                        dependencies = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                                        
                                        if "lodash" in dependencies and dependencies["lodash"].startswith("4.17.1"):
                                            results["vulnerable_dependencies"].append({
                                                "name": "lodash",
                                                "version": dependencies["lodash"],
                                                "language": "javascript",
                                                "vulnerability": "Prototype pollution vulnerability",
                                                "recommendation": "Upgrade to lodash 4.17.21 or later",
                                                "severity": "high",
                                                "file_path": file_path
                                            })
                                        
                                        if "axios" in dependencies and dependencies["axios"].startswith("0.19"):
                                            results["vulnerable_dependencies"].append({
                                                "name": "axios",
                                                "version": dependencies["axios"],
                                                "language": "javascript",
                                                "vulnerability": "Server-side request forgery",
                                                "recommendation": "Upgrade to axios 0.21.1 or later",
                                                "severity": "medium",
                                                "file_path": file_path
                                            })
                                    except json.JSONDecodeError:
                                        pass
        
        # Summary
        results["summary"] = {
            "total_dependency_files": len(results["dependency_files_found"]),
            "total_vulnerable_dependencies": len(results["vulnerable_dependencies"]),
            "severity_distribution": {
                "critical": len([d for d in results["vulnerable_dependencies"] if d["severity"] == "critical"]),
                "high": len([d for d in results["vulnerable_dependencies"] if d["severity"] == "high"]),
                "medium": len([d for d in results["vulnerable_dependencies"] if d["severity"] == "medium"]),
                "low": len([d for d in results["vulnerable_dependencies"] if d["severity"] == "low"])
            }
        }
        
        return results
    
    def _detect_secrets(self, repository_path: str) -> Dict[str, Any]:
        """
        Detect hardcoded secrets and credentials in code.
        
        Args:
            repository_path: Path to the repository
            
        Returns:
            Dictionary containing secret detection results
        """
        # In a real implementation, this would integrate with tools like
        # GitLeaks, TruffleHog, or similar
        
        # Example patterns (simplified)
        secret_patterns = {
            "api_key": r"(?i)(?:api|access)_?key(?:[ '\"\=:]+)([a-z0-9]{16,64})",
            "aws_key": r"(?i)(?:aws|amazon)_?(?:access_?)?key(?:_?id)?(?:[ '\"\=:]+)([a-z0-9]{16,})",
            "password": r"(?i)password(?:[ '\"\=:]+)([a-z0-9]{8,})",
            "private_key": r"-----BEGIN (?:RSA|DSA|EC|OPENSSH) PRIVATE KEY-----",
            "auth_token": r"(?i)(?:auth|authentication|bearer)_?token(?:[ '\"\=:]+)([a-z0-9]{16,})"
        }
        
        results = {
            "secrets_found": [],
            "timestamp": time.time()
        }
        
        excluded_dirs = ['.git', 'node_modules', 'venv', '.env', '.venv', '__pycache__']
        excluded_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.mp3', '.mp4', '.mov', '.avi', '.pdf']
        
        # Scan files
        for root, dirs, files in os.walk(repository_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            for filename in files:
                # Skip excluded file types
                if any(filename.endswith(ext) for ext in excluded_extensions):
                    continue
                
                file_path = os.path.join(root, filename)
                
                try:
                    with open(file_path, 'r', errors='ignore') as f:
                        content = f.read()
                        lines = content.split('\n')
                        
                        # Check each pattern
                        for secret_type, pattern in secret_patterns.items():
                            matches = re.finditer(pattern, content)
                            
                            for match in matches:
                                # Get line number
                                line_count = content[:match.start()].count('\n') + 1
                                
                                # Get line content
                                line_content = lines[line_count - 1] if line_count <= len(lines) else ""
                                
                                # Masked value (keep first and last chars, mask the rest)
                                value = match.group(1) if match.lastindex else match.group(0)
                                value_length = len(value)
                                masked_value = value[:2] + '*' * (value_length - 4) + value[-2:] if value_length > 4 else '****'
                                
                                # Add to results
                                results["secrets_found"].append({
                                    "type": secret_type,
                                    "file_path": file_path,
                                    "line_number": line_count,
                                    "line_content": line_content,
                                    "masked_value": masked_value,
                                    "severity": "high"
                                })
                except Exception as e:
                    logger.error(f"Error checking file {file_path} for secrets: {str(e)}")
        
        # Summary
        results["summary"] = {
            "total_secrets_found": len(results["secrets_found"]),
            "type_distribution": {},
            "files_with_secrets": len(set(s["file_path"] for s in results["secrets_found"]))
        }
        
        # Count occurrences of each secret type
        for secret in results["secrets_found"]:
            secret_type = secret["type"]
            if secret_type not in results["summary"]["type_distribution"]:
                results["summary"]["type_distribution"][secret_type] = 0
            results["summary"]["type_distribution"][secret_type] += 1
        
        return results
    
    def _generate_security_report(self, scan_id: str) -> Dict[str, Any]:
        """
        Generate a comprehensive security report based on a previous scan.
        
        Args:
            scan_id: ID of the scan to generate a report for
            
        Returns:
            Dictionary containing the report
            
        Raises:
            ValueError: If the scan ID is invalid or not found
        """
        if scan_id not in self.current_scan_results:
            raise ValueError(f"Invalid scan ID: {scan_id}")
        
        scan_result = self.current_scan_results[scan_id]
        
        # Extract data
        vulnerabilities = [SecurityVulnerability.from_dict(v) for v in scan_result["vulnerabilities"]]
        summary = scan_result["summary"]
        
        # Group vulnerabilities by severity
        vulnerabilities_by_severity = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": []
        }
        
        for vuln in vulnerabilities:
            if vuln.severity in vulnerabilities_by_severity:
                vulnerabilities_by_severity[vuln.severity].append(vuln.to_dict())
        
        # Group vulnerabilities by type
        vulnerabilities_by_type = {}
        for vuln in vulnerabilities:
            vuln_type = vuln.name.split(" ")[0]  # Simplified grouping
            if vuln_type not in vulnerabilities_by_type:
                vulnerabilities_by_type[vuln_type] = []
            vulnerabilities_by_type[vuln_type].append(vuln.to_dict())
        
        # Group vulnerabilities by file
        vulnerabilities_by_file = {}
        for vuln in vulnerabilities:
            if vuln.file_path not in vulnerabilities_by_file:
                vulnerabilities_by_file[vuln.file_path] = []
            vulnerabilities_by_file[vuln.file_path].append(vuln.to_dict())
        
        # Generate recommendations
        recommendations = self._generate_recommendations(vulnerabilities, summary)
        
        # Create report
        report = {
            "report_id": f"report_{int(time.time())}",
            "scan_id": scan_id,
            "generated_at": time.time(),
            "summary": summary,
            "risk_assessment": self._generate_risk_assessment(summary),
            "vulnerabilities_by_severity": vulnerabilities_by_severity,
            "vulnerabilities_by_type": vulnerabilities_by_type,
            "vulnerabilities_by_file": vulnerabilities_by_file,
            "recommendations": recommendations,
            "compliance": self._assess_compliance(vulnerabilities, summary),
            "appendices": {
                "methodology": "Static code analysis using pattern matching and security best practices.",
                "limitations": "This report is based on automated static analysis and may contain false positives. A thorough security assessment should also include dynamic testing and manual code review.",
                "references": [
                    "OWASP Top 10 Web Application Security Risks",
                    "SANS Top 25 Software Errors",
                    "Common Weakness Enumeration (CWE)",
                    "Common Vulnerabilities and Exposures (CVE)"
                ],
                "glossary": {
                    "SQL Injection": "A code injection technique that exploits a security vulnerability in an application's software by inserting malicious SQL statements into entry fields for execution.",
                    "XSS": "Cross-site scripting is a type of security vulnerability that can occur in web applications by injecting client-side scripts into pages viewed by other users.",
                    "SAST": "Static Application Security Testing, a set of technologies designed to analyze application source code for security vulnerabilities.",
                    "CWE": "Common Weakness Enumeration, a community-developed list of software and hardware weakness types."
                }
            }
        }
        
        return report
    
    def _generate_recommendations(
        self,
        vulnerabilities: List[SecurityVulnerability],
        summary: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate prioritized security recommendations based on vulnerabilities.
        
        Args:
            vulnerabilities: List of vulnerabilities
            summary: Scan summary data
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # Count vulnerability types
        vuln_type_counts = {}
        for vuln in vulnerabilities:
            vuln_type = vuln.name
            if vuln_type not in vuln_type_counts:
                vuln_type_counts[vuln_type] = {
                    "count": 0,
                    "severity": vuln.severity,
                    "recommendation": vuln.recommendation
                }
            vuln_type_counts[vuln_type]["count"] += 1
        
        # Sort by severity and count
        severity_ranks = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1,
            "info": 0
        }
        
        sorted_types = sorted(
            vuln_type_counts.items(),
            key=lambda x: (severity_ranks.get(x[1]["severity"], 0), x[1]["count"]),
            reverse=True
        )
        
        # Generate recommendations for top issues
        for vuln_type, data in sorted_types:
            recommendations.append({
                "title": f"Address {data['count']} instances of {vuln_type}",
                "severity": data["severity"],
                "recommendation": data["recommendation"],
                "count": data["count"],
                "priority": self._get_priority_label(data["severity"])
            })
        
        # Add general recommendations based on scan results
        if summary["risk_score"] > 7.0:
            recommendations.append({
                "title": "Implement a Secure Development Lifecycle (SDLC)",
                "severity": "high",
                "recommendation": "Establish a formal secure development lifecycle process that includes security training, threat modeling, and security testing at each phase.",
                "priority": "High"
            })
        
        if len(vulnerabilities) > 10:
            recommendations.append({
                "title": "Conduct Developer Security Training",
                "severity": "medium",
                "recommendation": "Provide security training for developers focused on common vulnerability types found in this scan.",
                "priority": "Medium"
            })
        
        return recommendations
    
    def _get_priority_label(self, severity: str) -> str:
        """Convert severity to priority label"""
        priority_map = {
            "critical": "Critical",
            "high": "High",
            "medium": "Medium",
            "low": "Low",
            "info": "Informational"
        }
        return priority_map.get(severity, "Medium")
    
    def _generate_risk_assessment(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a risk assessment based on scan summary.
        
        Args:
            summary: Scan summary data
            
        Returns:
            Risk assessment dictionary
        """
        risk_score = summary["risk_score"]
        
        # Determine risk level
        risk_level = "Low"
        if risk_score >= 7.0:
            risk_level = "Critical"
        elif risk_score >= 5.0:
            risk_level = "High"
        elif risk_score >= 3.0:
            risk_level = "Medium"
        
        # Generate assessment explanation
        explanation = f"The codebase has a risk score of {risk_score:.1f}/10.0, indicating a {risk_level.lower()} level of security risk. "
        
        if summary["vulnerability_count"] > 0:
            explanation += f"The scan identified {summary['vulnerability_count']} vulnerabilities across {summary.get('total_files_scanned', 'multiple')} files. "
        
            severity_counts = summary.get("severity_counts", {})
            if severity_counts.get("critical", 0) > 0:
                explanation += f"Critical attention is required for {severity_counts['critical']} critical vulnerabilities. "
            
            if severity_counts.get("high", 0) > 0:
                explanation += f"High priority should be given to {severity_counts['high']} high-severity issues. "
        else:
            explanation += "No vulnerabilities were detected in the scan, suggesting good security practices are being followed. "
        
        # Generate risk vectors
        risk_vectors = {
            "impact": self._calculate_impact_score(summary),
            "likelihood": self._calculate_likelihood_score(summary),
            "exposure": self._calculate_exposure_score(summary),
            "detection_difficulty": self._calculate_detection_difficulty(summary)
        }
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "explanation": explanation,
            "risk_vectors": risk_vectors,
            "business_impact": self._assess_business_impact(risk_score, summary)
        }
    
    def _calculate_impact_score(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate potential impact score"""
        severity_counts = summary.get("severity_counts", {})
        
        # Weighted score based on severity
        impact_score = (
            10.0 * severity_counts.get("critical", 0) +
            7.0 * severity_counts.get("high", 0) +
            4.0 * severity_counts.get("medium", 0) +
            1.0 * severity_counts.get("low", 0)
        ) / max(1, summary.get("vulnerability_count", 1))
        
        impact_score = min(10.0, impact_score)
        
        # Determine impact level
        impact_level = "Low"
        if impact_score >= 7.0:
            impact_level = "Critical"
        elif impact_score >= 5.0:
            impact_level = "High"
        elif impact_score >= 3.0:
            impact_level = "Medium"
        
        return {
            "score": impact_score,
            "level": impact_level,
            "description": f"The potential impact of exploitation is {impact_level.lower()}, based on the severity of identified vulnerabilities."
        }
    
    def _calculate_likelihood_score(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate likelihood score"""
        # Simple likelihood calculation
        likelihood_score = min(10.0, summary.get("vulnerability_count", 0) / 5.0)
        
        # Determine likelihood level
        likelihood_level = "Low"
        if likelihood_score >= 7.0:
            likelihood_level = "Critical"
        elif likelihood_score >= 5.0:
            likelihood_level = "High"
        elif likelihood_score >= 3.0:
            likelihood_level = "Medium"
        
        return {
            "score": likelihood_score,
            "level": likelihood_level,
            "description": f"The likelihood of exploitation is {likelihood_level.lower()}, based on the number and nature of vulnerabilities."
        }
    
    def _calculate_exposure_score(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate exposure score"""
        # Simplified exposure calculation
        exposure_score = summary.get("risk_score", 5.0) * 0.7
        
        # Determine exposure level
        exposure_level = "Low"
        if exposure_score >= 7.0:
            exposure_level = "Critical"
        elif exposure_score >= 5.0:
            exposure_level = "High"
        elif exposure_score >= 3.0:
            exposure_level = "Medium"
        
        return {
            "score": exposure_score,
            "level": exposure_level,
            "description": f"The attack surface exposure is {exposure_level.lower()}, indicating the degree to which vulnerabilities are accessible."
        }
    
    def _calculate_detection_difficulty(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detection difficulty score"""
        # Simplified detection difficulty calculation
        detection_score = 5.0  # Medium by default
        
        # Determine detection level
        detection_level = "Medium"
        if detection_score >= 7.0:
            detection_level = "Critical"
        elif detection_score >= 5.0:
            detection_level = "High"
        elif detection_score >= 3.0:
            detection_level = "Medium"
        else:
            detection_level = "Low"
        
        return {
            "score": detection_score,
            "level": detection_level,
            "description": f"The difficulty of detecting exploits is {detection_level.lower()}, indicating how challenging it might be to identify attacks targeting these vulnerabilities."
        }
    
    def _assess_business_impact(self, risk_score: float, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Assess potential business impact"""
        impact_areas = []
        
        if risk_score >= 7.0:
            impact_areas.append({
                "area": "Data Breach Risk",
                "description": "High risk of unauthorized data access or exfiltration that could lead to regulatory penalties and reputational damage.",
                "severity": "Critical"
            })
        
        if risk_score >= 5.0:
            impact_areas.append({
                "area": "Service Availability",
                "description": "Vulnerabilities could be exploited to disrupt service availability, affecting user experience and business operations.",
                "severity": "High"
            })
        
        if summary.get("vulnerability_count", 0) > 0:
            impact_areas.append({
                "area": "Compliance Risk",
                "description": "Security vulnerabilities may lead to non-compliance with industry standards and regulations such as GDPR, PCI-DSS, or HIPAA.",
                "severity": "Medium"
            })
        
        if risk_score >= 3.0:
            impact_areas.append({
                "area": "Remediation Cost",
                "description": "Addressing the identified security issues will require developer time and resources. Early remediation is more cost-effective than addressing breaches.",
                "severity": "Medium"
            })
        
        return {
            "summary": f"Overall business risk is assessed as {self._risk_score_to_text(risk_score)}.",
            "impact_areas": impact_areas
        }
    
    def _risk_score_to_text(self, score: float) -> str:
        """Convert risk score to text description"""
        if score >= 8.5:
            return "Critical"
        elif score >= 7.0:
            return "High"
        elif score >= 4.0:
            return "Medium"
        elif score >= 2.0:
            return "Low"
        else:
            return "Minimal"
    
    def _assess_compliance(
        self,
        vulnerabilities: List[SecurityVulnerability],
        summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess compliance implications of vulnerabilities.
        
        Args:
            vulnerabilities: List of vulnerabilities
            summary: Scan summary data
            
        Returns:
            Compliance assessment dictionary
        """
        # Simplified compliance checking
        compliances = {
            "owasp_top10": {
                "name": "OWASP Top 10",
                "status": "Pass" if summary["risk_score"] < 3.0 else "Fail",
                "details": []
            },
            "pci_dss": {
                "name": "PCI DSS",
                "status": "Undetermined",  # Would need more context
                "details": ["PCI DSS compliance requires a more comprehensive assessment."]
            },
            "gdpr": {
                "name": "GDPR",
                "status": "Undetermined",  # Would need more context
                "details": ["GDPR compliance requires additional context about data processing activities."]
            }
        }
        
        # Check for specific OWASP Top 10 issues
        owasp_mapping = {
            "sql_injection": "A1:2017-Injection",
            "xss": "A7:2017-Cross-Site Scripting",
            "insecure_deserialization": "A8:2017-Insecure Deserialization",
            "hardcoded_secrets": "A2:2017-Broken Authentication",
            "command_injection": "A1:2017-Injection"
        }
        
        owasp_issues = set()
        for vuln in vulnerabilities:
            for pattern, category in owasp_mapping.items():
                if pattern in vuln.name.lower():
                    owasp_issues.add(category)
        
        if owasp_issues:
            compliances["owasp_top10"]["details"] = [
                f"Fails compliance with: {', '.join(sorted(owasp_issues))}"
            ]
        else:
            compliances["owasp_top10"]["details"] = [
                "No specific OWASP Top 10 categories were identified in the scan."
            ]
        
        # Overall compliance assessment
        passing = sum(1 for c in compliances.values() if c["status"] == "Pass")
        failing = sum(1 for c in compliances.values() if c["status"] == "Fail")
        undetermined = sum(1 for c in compliances.values() if c["status"] == "Undetermined")
        
        return {
            "overall_status": (
                "Pass" if passing == len(compliances) else
                "Fail" if failing > 0 else
                "Undetermined"
            ),
            "standards": compliances,
            "summary": f"Passing {passing}, Failing {failing}, Undetermined {undetermined} standards."
        }