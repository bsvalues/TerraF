"""
Integration Test Agent Module

This module implements a specialized agent for managing and executing integration tests.
The agent can generate, execute, and analyze the results of integration tests for
microservices and other components in the TerraFusion platform.
"""

import os
import json
import re
import logging
import subprocess
from typing import Dict, List, Any, Optional, Union, Set, Tuple

# Import base agent classes
from agent_base import (
    Agent, CodeQualityAgent, ModelInterface, Task, MessageType, 
    MessagePriority, AgentCategory
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegrationTestAgent(CodeQualityAgent):
    """
    Agent that specializes in managing and executing integration tests.
    
    Capabilities:
    - Generate integration test scenarios
    - Create test fixtures and mocks
    - Execute integration tests
    - Analyze test results
    - Recommend test coverage improvements
    """
    
    def __init__(self, agent_id: str = "integration_test_agent", preferred_model: Optional[str] = None):
        capabilities = [
            "test_scenario_generation",
            "test_fixture_creation",
            "test_execution",
            "result_analysis",
            "coverage_recommendation"
        ]
        
        super().__init__(
            agent_id=agent_id,
            capabilities=capabilities,
            preferred_model=preferred_model
        )
        
        # Test frameworks by language
        self.test_frameworks = {
            "python": ["pytest", "unittest"],
            "javascript": ["jest", "mocha"],
            "typescript": ["jest", "mocha"],
            "java": ["junit", "testng"],
            "csharp": ["nunit", "xunit"],
            "go": ["go test", "testify"],
            "ruby": ["rspec", "minitest"],
            "php": ["phpunit", "codeception"]
        }
        
        # Test types
        self.test_types = [
            "api_integration",
            "service_communication",
            "database_integration",
            "third_party_integration",
            "end_to_end",
            "performance",
            "security"
        ]
    
    def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute an integration test task"""
        task_type = task.task_type
        
        if task_type == "generate_test_scenarios":
            return self._generate_test_scenarios(task)
        
        elif task_type == "create_test_fixtures":
            return self._create_test_fixtures(task)
        
        elif task_type == "execute_tests":
            return self._execute_tests(task)
        
        elif task_type == "analyze_results":
            return self._analyze_results(task)
        
        elif task_type == "recommend_improvements":
            return self._recommend_improvements(task)
        
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    def _generate_test_scenarios(self, task: Task) -> Dict[str, Any]:
        """Generate integration test scenarios"""
        components = task.input_data.get("components", [])
        test_types = task.input_data.get("test_types", self.test_types)
        system_description = task.input_data.get("system_description", "")
        
        if not components:
            return {"error": "Missing components information"}
        
        # Use the model to generate test scenarios
        model = ModelInterface(capability="code_analysis")
        
        prompt = f"""
        Generate integration test scenarios for the following components:
        
        Components:
        {json.dumps(components, indent=2)}
        
        Test types to focus on:
        {json.dumps(test_types, indent=2)}
        
        System description:
        {system_description}
        
        For each component, generate at least 3 integration test scenarios.
        For each scenario, provide:
        1. A descriptive name
        2. Prerequisite conditions
        3. Test steps
        4. Expected results
        5. Potential edge cases to consider
        
        Format your response as JSON with component names as keys, and arrays of scenario objects as values.
        """
        
        system_message = "You are an expert in integration testing. Design comprehensive test scenarios that verify how components interact with each other."
        
        test_scenarios_text = model.generate_text(prompt, system_message)
        
        # Extract JSON from the response
        try:
            # Try to extract JSON if the model wrapped it in markdown
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', test_scenarios_text, re.DOTALL)
            if json_match:
                test_scenarios = json.loads(json_match.group(1))
            else:
                # Otherwise try to parse the whole text as JSON
                test_scenarios = json.loads(test_scenarios_text)
            
            return {
                "test_scenarios": test_scenarios,
                "component_count": len(components),
                "scenario_count": sum(len(scenarios) for scenarios in test_scenarios.values())
            }
        except Exception as e:
            # If parsing fails, return the raw text
            return {
                "raw_output": test_scenarios_text,
                "parse_error": str(e)
            }
    
    def _create_test_fixtures(self, task: Task) -> Dict[str, Any]:
        """Create test fixtures for integration tests"""
        scenarios = task.input_data.get("scenarios", [])
        language = task.input_data.get("language", "python")
        framework = task.input_data.get("framework", self.test_frameworks.get(language, [])[0] if self.test_frameworks.get(language) else None)
        
        if not scenarios:
            return {"error": "Missing test scenarios"}
        
        if not framework:
            return {"error": f"No testing framework available for {language}"}
        
        # Use the model to generate fixtures
        model = ModelInterface(capability="code_analysis")
        
        prompt = f"""
        Create test fixtures for the following integration test scenarios using {framework} in {language}:
        
        Scenarios:
        {json.dumps(scenarios, indent=2)}
        
        Generate:
        1. Mock data
        2. Service mocks/stubs
        3. Database fixtures
        4. Environment setup code
        
        Format the code appropriately for {framework}.
        """
        
        system_message = f"You are an expert in {framework} and {language}. Create efficient test fixtures that simplify integration testing."
        
        fixtures_text = model.generate_text(prompt, system_message)
        
        # Extract code blocks from the response
        fixtures = {}
        code_blocks = re.findall(r'```(?:\w+)?\s*\n(.*?)\n```', fixtures_text, re.DOTALL)
        
        for i, block in enumerate(code_blocks):
            fixtures[f"fixture_{i+1}"] = block
        
        if not fixtures:
            # No code blocks found, return the raw text
            fixtures = {"raw_output": fixtures_text}
        
        return {
            "fixtures": fixtures,
            "language": language,
            "framework": framework,
            "fixture_count": len(fixtures)
        }
    
    def _execute_tests(self, task: Task) -> Dict[str, Any]:
        """Execute integration tests"""
        test_command = task.input_data.get("test_command", "")
        test_directory = task.input_data.get("test_directory", "")
        
        if not test_command and not test_directory:
            return {"error": "Missing test command or directory"}
        
        # If only directory is provided, construct a command based on common test runners
        if not test_command:
            if os.path.exists(os.path.join(test_directory, "pytest.ini")):
                test_command = f"python -m pytest {test_directory} -v"
            elif os.path.exists(os.path.join(test_directory, "package.json")):
                test_command = "npm test"
            elif os.path.exists(os.path.join(test_directory, "pom.xml")):
                test_command = "mvn test"
            elif os.path.exists(os.path.join(test_directory, "build.gradle")):
                test_command = "./gradlew test"
            else:
                # Default to pytest for Python
                test_command = f"python -m pytest {test_directory} -v"
        
        try:
            # Run the test command
            process = subprocess.Popen(
                test_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=300)  # 5-minute timeout
            
            # Parse the results
            success = process.returncode == 0
            
            # Extract test results
            test_results = self._parse_test_output(stdout, stderr)
            
            return {
                "success": success,
                "command": test_command,
                "results": test_results,
                "exit_code": process.returncode,
                "stdout": stdout,
                "stderr": stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "command": test_command,
                "error": "Test execution timed out after 5 minutes",
                "exit_code": -1
            }
        except Exception as e:
            return {
                "success": False,
                "command": test_command,
                "error": str(e),
                "exit_code": -1
            }
    
    def _analyze_results(self, task: Task) -> Dict[str, Any]:
        """Analyze integration test results"""
        test_results = task.input_data.get("results", {})
        test_output = task.input_data.get("output", "")
        
        if not test_results and not test_output:
            return {"error": "Missing test results"}
        
        # Use the model to analyze the results
        model = ModelInterface(capability="code_analysis")
        
        prompt = f"""
        Analyze the following integration test results:
        
        Results:
        {json.dumps(test_results, indent=2) if test_results else ""}
        
        Raw test output:
        {test_output}
        
        Provide:
        1. Summary of test success/failure
        2. Analysis of failed tests, including potential root causes
        3. Patterns in failures (e.g., specific component interactions)
        4. Recommendations for fixing issues
        
        Format your response as JSON with these sections.
        """
        
        system_message = "You are an expert in integration testing. Analyze test results to identify patterns and root causes of failures."
        
        analysis_text = model.generate_text(prompt, system_message)
        
        # Extract JSON from the response
        try:
            # Try to extract JSON if the model wrapped it in markdown
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', analysis_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(1))
            else:
                # Otherwise try to parse the whole text as JSON
                analysis = json.loads(analysis_text)
            
            return analysis
        except Exception as e:
            # If parsing fails, return structured analysis based on text
            return {
                "summary": self._extract_summary(analysis_text),
                "failed_tests": self._extract_failures(analysis_text),
                "patterns": self._extract_patterns(analysis_text),
                "recommendations": self._extract_recommendations(analysis_text),
                "raw_analysis": analysis_text
            }
    
    def _recommend_improvements(self, task: Task) -> Dict[str, Any]:
        """Recommend integration test improvements"""
        coverage_data = task.input_data.get("coverage_data", {})
        components = task.input_data.get("components", [])
        system_description = task.input_data.get("system_description", "")
        
        # Use the model to generate recommendations
        model = ModelInterface(capability="code_analysis")
        
        prompt = f"""
        Recommend improvements for integration testing coverage:
        
        Current coverage data:
        {json.dumps(coverage_data, indent=2) if coverage_data else "Not provided"}
        
        Components:
        {json.dumps(components, indent=2) if components else "Not provided"}
        
        System description:
        {system_description}
        
        Provide:
        1. Analysis of current test coverage gaps
        2. High-priority test scenarios to add
        3. Recommendations for improving test quality
        4. Suggestions for testing infrastructure improvements
        
        Format your response as JSON with these sections.
        """
        
        system_message = "You are an expert in test coverage analysis. Recommend improvements to ensure comprehensive integration testing."
        
        recommendations_text = model.generate_text(prompt, system_message)
        
        # Extract JSON from the response
        try:
            # Try to extract JSON if the model wrapped it in markdown
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', recommendations_text, re.DOTALL)
            if json_match:
                recommendations = json.loads(json_match.group(1))
            else:
                # Otherwise try to parse the whole text as JSON
                recommendations = json.loads(recommendations_text)
            
            return recommendations
        except Exception as e:
            # If parsing fails, return structured recommendations based on text
            return {
                "coverage_gaps": self._extract_coverage_gaps(recommendations_text),
                "priority_scenarios": self._extract_priority_scenarios(recommendations_text),
                "quality_improvements": self._extract_quality_improvements(recommendations_text),
                "infrastructure_suggestions": self._extract_infrastructure_suggestions(recommendations_text),
                "raw_recommendations": recommendations_text
            }
    
    def _parse_test_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Parse test output into structured results"""
        # This is a simplified parser that will be enhanced based on actual output formats
        combined_output = f"{stdout}\n{stderr}"
        
        # Basic parsing for pytest-style output
        if "collected" in combined_output and "passed" in combined_output:
            # Extract tests counts
            collected_match = re.search(r'collected\s+(\d+)\s+items', combined_output)
            passed_match = re.search(r'(\d+)\s+passed', combined_output)
            failed_match = re.search(r'(\d+)\s+failed', combined_output)
            skipped_match = re.search(r'(\d+)\s+skipped', combined_output)
            
            collected = int(collected_match.group(1)) if collected_match else 0
            passed = int(passed_match.group(1)) if passed_match else 0
            failed = int(failed_match.group(1)) if failed_match else 0
            skipped = int(skipped_match.group(1)) if skipped_match else 0
            
            # Extract failed test names
            failed_tests = []
            for line in combined_output.split('\n'):
                if 'FAILED' in line and 'test_' in line:
                    test_name_match = re.search(r'(test_\w+)', line)
                    if test_name_match:
                        failed_tests.append(test_name_match.group(1))
            
            return {
                "total": collected,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "failed_tests": failed_tests,
                "success_rate": round(passed / collected * 100, 2) if collected > 0 else 0
            }
        
        # Basic parsing for Jest/Mocha style output
        elif "passing" in combined_output and "failing" in combined_output:
            # Extract tests counts
            passing_match = re.search(r'(\d+)\s+passing', combined_output)
            failing_match = re.search(r'(\d+)\s+failing', combined_output)
            
            passing = int(passing_match.group(1)) if passing_match else 0
            failing = int(failing_match.group(1)) if failing_match else 0
            total = passing + failing
            
            # Extract failed test names (simplified approach)
            failed_tests = []
            in_failure_section = False
            for line in combined_output.split('\n'):
                if 'failing' in line and not in_failure_section:
                    in_failure_section = True
                    continue
                
                if in_failure_section and line.strip() and not line.startswith(' '):
                    failed_tests.append(line.strip())
                    if len(failed_tests) >= failing:
                        break
            
            return {
                "total": total,
                "passed": passing,
                "failed": failing,
                "skipped": 0,  # Would need to extract from output
                "failed_tests": failed_tests,
                "success_rate": round(passing / total * 100, 2) if total > 0 else 0
            }
        
        # Default to generic parsing
        else:
            # Count basic indicators in output
            passed = combined_output.count("PASS") + combined_output.count("OK")
            failed = combined_output.count("FAIL") + combined_output.count("ERROR")
            
            return {
                "parsed": False,  # Indicate that we used a fallback parsing method
                "passed_indicators": passed,
                "failed_indicators": failed,
                "success": failed == 0 and passed > 0,
                "raw_output": combined_output[:1000]  # Truncated output
            }
    
    def _extract_summary(self, text: str) -> Dict[str, Any]:
        """Extract test summary from analysis text"""
        summary = {}
        
        # Look for test counts
        total_match = re.search(r'(?:total|ran|executed)\D*(\d+)\D*tests', text, re.IGNORECASE)
        if total_match:
            summary["total"] = int(total_match.group(1))
        
        passed_match = re.search(r'(\d+)\D*(?:tests)?\D*pass', text, re.IGNORECASE)
        if passed_match:
            summary["passed"] = int(passed_match.group(1))
        
        failed_match = re.search(r'(\d+)\D*(?:tests)?\D*fail', text, re.IGNORECASE)
        if failed_match:
            summary["failed"] = int(failed_match.group(1))
        
        # Look for success rate
        success_rate_match = re.search(r'(?:success|pass)(?:.*?)(\d+)%', text, re.IGNORECASE)
        if success_rate_match:
            summary["success_rate"] = int(success_rate_match.group(1))
        
        return summary
    
    def _extract_failures(self, text: str) -> List[Dict[str, str]]:
        """Extract failed tests from analysis text"""
        failures = []
        
        # Look for sections about failed tests
        fail_section_match = re.search(r'(?:failed tests|failures|failing tests):(.*?)(?:^#|\n\n|$)', text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        
        if fail_section_match:
            fail_section = fail_section_match.group(1).strip()
            
            # Extract each failure
            for line in fail_section.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('--'):
                    # Try to separate test name from cause
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        failures.append({
                            "test": parts[0].strip(),
                            "cause": parts[1].strip()
                        })
                    else:
                        failures.append({"test": line, "cause": "Unknown"})
        
        return failures
    
    def _extract_patterns(self, text: str) -> List[str]:
        """Extract failure patterns from analysis text"""
        patterns = []
        
        # Look for sections about patterns
        pattern_section_match = re.search(r'(?:patterns|common issues|recurring problems):(.*?)(?:^#|\n\n|$)', text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        
        if pattern_section_match:
            pattern_section = pattern_section_match.group(1).strip()
            
            # Extract each pattern
            for line in pattern_section.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('--'):
                    # Remove bullet points
                    line = re.sub(r'^[*\-•]\s*', '', line)
                    if line:
                        patterns.append(line)
        
        return patterns
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from analysis text"""
        recommendations = []
        
        # Look for sections about recommendations
        rec_section_match = re.search(r'(?:recommendations|suggested fixes|how to fix):(.*?)(?:^#|\n\n|$)', text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        
        if rec_section_match:
            rec_section = rec_section_match.group(1).strip()
            
            # Extract each recommendation
            for line in rec_section.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('--'):
                    # Remove bullet points
                    line = re.sub(r'^[*\-•]\s*', '', line)
                    if line:
                        recommendations.append(line)
        
        return recommendations
    
    def _extract_coverage_gaps(self, text: str) -> List[str]:
        """Extract coverage gaps from recommendations text"""
        gaps = []
        
        # Look for sections about coverage gaps
        gaps_section_match = re.search(r'(?:coverage gaps|missing tests|untested areas):(.*?)(?:^#|\n\n|$)', text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        
        if gaps_section_match:
            gaps_section = gaps_section_match.group(1).strip()
            
            # Extract each gap
            for line in gaps_section.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('--'):
                    # Remove bullet points
                    line = re.sub(r'^[*\-•]\s*', '', line)
                    if line:
                        gaps.append(line)
        
        return gaps
    
    def _extract_priority_scenarios(self, text: str) -> List[Dict[str, str]]:
        """Extract priority test scenarios from recommendations text"""
        scenarios = []
        
        # Look for sections about priority scenarios
        priority_section_match = re.search(r'(?:priority scenarios|high-priority tests|key scenarios):(.*?)(?:^#|\n\n|$)', text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        
        if priority_section_match:
            priority_section = priority_section_match.group(1).strip()
            
            # Extract each scenario
            current_scenario = {"name": "", "description": ""}
            for line in priority_section.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('--'):
                    # Check if this is a new scenario name
                    if re.match(r'^[*\-•]', line) or re.match(r'^\d+\.', line):
                        # Save previous scenario if it exists
                        if current_scenario["name"]:
                            scenarios.append(current_scenario.copy())
                        
                        # Start new scenario
                        line = re.sub(r'^[*\-•]\s*', '', line)
                        line = re.sub(r'^\d+\.\s*', '', line)
                        
                        # Split into name and description if possible
                        parts = line.split(':', 1)
                        if len(parts) > 1:
                            current_scenario = {
                                "name": parts[0].strip(),
                                "description": parts[1].strip()
                            }
                        else:
                            current_scenario = {"name": line, "description": ""}
                    else:
                        # Add to current scenario description
                        if current_scenario["description"]:
                            current_scenario["description"] += " " + line
                        else:
                            current_scenario["description"] = line
            
            # Add the last scenario
            if current_scenario["name"]:
                scenarios.append(current_scenario)
        
        return scenarios
    
    def _extract_quality_improvements(self, text: str) -> List[str]:
        """Extract test quality improvements from recommendations text"""
        improvements = []
        
        # Look for sections about quality improvements
        quality_section_match = re.search(r'(?:quality improvements|improve quality|test quality):(.*?)(?:^#|\n\n|$)', text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        
        if quality_section_match:
            quality_section = quality_section_match.group(1).strip()
            
            # Extract each improvement
            for line in quality_section.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('--'):
                    # Remove bullet points
                    line = re.sub(r'^[*\-•]\s*', '', line)
                    if line:
                        improvements.append(line)
        
        return improvements
    
    def _extract_infrastructure_suggestions(self, text: str) -> List[str]:
        """Extract infrastructure suggestions from recommendations text"""
        suggestions = []
        
        # Look for sections about infrastructure
        infra_section_match = re.search(r'(?:infrastructure|test infrastructure|testing infrastructure):(.*?)(?:^#|\n\n|$)', text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        
        if infra_section_match:
            infra_section = infra_section_match.group(1).strip()
            
            # Extract each suggestion
            for line in infra_section.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('--'):
                    # Remove bullet points
                    line = re.sub(r'^[*\-•]\s*', '', line)
                    if line:
                        suggestions.append(line)
        
        return suggestions