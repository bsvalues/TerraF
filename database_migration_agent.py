"""
Database Migration Agent Module

This module implements a specialized agent for database schema migrations.
The agent provides capabilities for planning, generating, and managing
database migrations in the TerraFusion platform.
"""

import os
import json
import re
import logging
from typing import Dict, List, Any, Optional, Union, Set, Tuple

# Import base agent classes
from agent_base import (
    DatabaseAgent, ModelInterface, Task, MessageType, 
    MessagePriority, AgentCategory
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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseMigrationAgent(DatabaseAgent):
    """
    Agent that specializes in database schema migrations.
    
    Capabilities:
    - Plan database schema changes
    - Generate migration scripts
    - Track migration history
    - Analyze migration impact
    - Resolve migration conflicts
    """
    
    def __init__(self, agent_id: str = "db_migration_agent", preferred_model: Optional[str] = None):
        capabilities = [
            "schema_migration_planning", 
            "migration_script_generation",
            "migration_history_tracking",
            "migration_impact_analysis",
            "conflict_resolution"
        ]
        
        super().__init__(
            agent_id=agent_id,
            capabilities=capabilities,
            preferred_model=preferred_model
        )
        
        # Initialize the migration manager
        try:
            self.migration_manager = MigrationManager()
        except Exception as e:
            logger.error(f"Error initializing migration manager: {str(e)}")
            self.migration_manager = None
    
    def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a database migration task"""
        task_type = task.task_type
        
        if task_type == "get_migration_status":
            return self._get_migration_status(task)
        
        elif task_type == "plan_migration":
            return self._plan_migration(task)
        
        elif task_type == "generate_migration":
            return self._generate_migration(task)
        
        elif task_type == "apply_migration":
            return self._apply_migration(task)
        
        elif task_type == "rollback_migration":
            return self._rollback_migration(task)
        
        elif task_type == "analyze_migration_impact":
            return self._analyze_migration_impact(task)
        
        elif task_type == "resolve_conflict":
            return self._resolve_migration_conflict(task)
        
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    def _get_migration_status(self, task: Task) -> Dict[str, Any]:
        """Get the current migration status"""
        if not self.migration_manager:
            return {"error": "Migration manager not initialized"}
        
        try:
            status = self.migration_manager.get_migration_status()
            return status
        except Exception as e:
            return {"error": f"Error getting migration status: {str(e)}"}
    
    def _plan_migration(self, task: Task) -> Dict[str, Any]:
        """Plan a database schema migration"""
        current_models = task.input_data.get("current_models", {})
        target_models = task.input_data.get("target_models", {})
        
        if not current_models or not target_models:
            return {"error": "Missing current or target models"}
        
        # Use the model to analyze the changes
        model = ModelInterface(capability="database_analysis")
        
        prompt = f"""
        Plan a database schema migration from the current models to the target models.
        
        Current models:
        {json.dumps(current_models, indent=2)}
        
        Target models:
        {json.dumps(target_models, indent=2)}
        
        Identify required changes, potential issues, and recommended approach.
        Focus on data preservation, performance impact, and rollback strategy.
        """
        
        system_message = "You are a database schema migration expert. Plan migrations that minimize risk and downtime."
        
        migration_plan = model.generate_text(prompt, system_message)
        
        # Extract structured information if possible
        try:
            # Try to extract JSON if the model returned it
            plan_match = re.search(r'```json\s*(.*?)\s*```', migration_plan, re.DOTALL)
            if plan_match:
                structured_plan = json.loads(plan_match.group(1))
            else:
                # Otherwise provide a simple structure based on the text
                structured_plan = {
                    "changes": [],
                    "issues": [],
                    "approach": "",
                    "rollback_strategy": ""
                }
                
                # Basic parsing of the plan text
                sections = migration_plan.split("\n\n")
                for section in sections:
                    if section.lower().startswith("changes:"):
                        changes = section.split("\n")[1:]
                        structured_plan["changes"] = [c.strip('- ') for c in changes if c.strip()]
                    elif section.lower().startswith("issues:"):
                        issues = section.split("\n")[1:]
                        structured_plan["issues"] = [i.strip('- ') for i in issues if i.strip()]
                    elif section.lower().startswith("approach:"):
                        structured_plan["approach"] = section.split(":", 1)[1].strip()
                    elif section.lower().startswith("rollback:"):
                        structured_plan["rollback_strategy"] = section.split(":", 1)[1].strip()
            
            return {
                "plan": structured_plan,
                "raw_plan": migration_plan
            }
        except Exception as e:
            # If parsing fails, return the raw text
            return {
                "plan_text": migration_plan,
                "parse_error": str(e)
            }
    
    def _generate_migration(self, task: Task) -> Dict[str, Any]:
        """Generate a migration script"""
        if not self.migration_manager:
            return {"error": "Migration manager not initialized"}
        
        message = task.input_data.get("message", "")
        autogenerate = task.input_data.get("autogenerate", True)
        
        if not message:
            return {"error": "Missing migration message"}
        
        try:
            migration_script = self.migration_manager.create_migration(message, autogenerate)
            
            return {
                "script_path": migration_script,
                "message": message,
                "autogenerated": autogenerate
            }
        except Exception as e:
            return {"error": f"Error generating migration: {str(e)}"}
    
    def _apply_migration(self, task: Task) -> Dict[str, Any]:
        """Apply a migration to the database"""
        if not self.migration_manager:
            return {"error": "Migration manager not initialized"}
        
        target = task.input_data.get("target", "head")
        
        try:
            success, message = self.migration_manager.upgrade(target)
            
            if success:
                # Get the new status after upgrading
                status = self.migration_manager.get_migration_status()
                
                return {
                    "success": True,
                    "message": message,
                    "current_revision": status.get("current_revision")
                }
            else:
                return {
                    "success": False,
                    "message": message
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error applying migration: {str(e)}"
            }
    
    def _rollback_migration(self, task: Task) -> Dict[str, Any]:
        """Rollback a migration"""
        if not self.migration_manager:
            return {"error": "Migration manager not initialized"}
        
        target = task.input_data.get("target", "")
        
        if not target:
            return {"error": "Missing target revision for rollback"}
        
        try:
            success, message = self.migration_manager.downgrade(target)
            
            if success:
                # Get the new status after downgrading
                status = self.migration_manager.get_migration_status()
                
                return {
                    "success": True,
                    "message": message,
                    "current_revision": status.get("current_revision")
                }
            else:
                return {
                    "success": False,
                    "message": message
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error rolling back migration: {str(e)}"
            }
    
    def _analyze_migration_impact(self, task: Task) -> Dict[str, Any]:
        """Analyze the impact of a proposed migration"""
        migration_script = task.input_data.get("migration_script", "")
        database_size = task.input_data.get("database_size", 0)
        table_counts = task.input_data.get("table_counts", {})
        
        if not migration_script:
            return {"error": "Missing migration script"}
        
        # Use the model to analyze the impact
        model = ModelInterface(capability="database_analysis")
        
        prompt = f"""
        Analyze the impact of applying this migration script:
        
        ```
        {migration_script}
        ```
        
        Database size: {database_size} MB
        Table row counts: {json.dumps(table_counts, indent=2)}
        
        Consider:
        1. Performance impact (execution time)
        2. Storage impact (space changes)
        3. Potential locking or blocking issues
        4. Data loss risks
        5. Application downtime requirements
        """
        
        system_message = "You are a database migration expert. Analyze migration impacts and risks."
        
        impact_analysis = model.generate_text(prompt, system_message)
        
        # Extract key impact metrics if available
        try:
            analysis_match = re.search(r'```json\s*(.*?)\s*```', impact_analysis, re.DOTALL)
            if analysis_match:
                structured_analysis = json.loads(analysis_match.group(1))
            else:
                # Basic metrics extraction
                structured_analysis = {
                    "performance_impact": self._extract_impact_level(impact_analysis, "performance"),
                    "storage_impact": self._extract_impact_level(impact_analysis, "storage"),
                    "locking_impact": self._extract_impact_level(impact_analysis, "lock"),
                    "data_loss_risk": self._extract_impact_level(impact_analysis, "data loss"),
                    "downtime_required": self._extract_boolean(impact_analysis, "downtime")
                }
            
            return {
                "impact": structured_analysis,
                "raw_analysis": impact_analysis
            }
        except Exception as e:
            # If parsing fails, return the raw text
            return {
                "analysis_text": impact_analysis,
                "parse_error": str(e)
            }
    
    def _resolve_migration_conflict(self, task: Task) -> Dict[str, Any]:
        """Resolve a migration conflict"""
        migration_a = task.input_data.get("migration_a", "")
        migration_b = task.input_data.get("migration_b", "")
        conflict_description = task.input_data.get("conflict_description", "")
        
        if not migration_a or not migration_b or not conflict_description:
            return {"error": "Missing migration scripts or conflict description"}
        
        # Use the model to resolve the conflict
        model = ModelInterface(capability="code_analysis")
        
        prompt = f"""
        Resolve the conflict between these two migration scripts:
        
        Migration A:
        ```
        {migration_a}
        ```
        
        Migration B:
        ```
        {migration_b}
        ```
        
        Conflict description:
        {conflict_description}
        
        Generate a merged migration script that correctly resolves the conflict.
        """
        
        system_message = "You are a database migration expert. Resolve conflicts between migrations while preserving both intent and data integrity."
        
        resolved_script = model.generate_text(prompt, system_message)
        
        # Extract the script from the response
        script_match = re.search(r'```(?:\w+)?\s*\n(.*?)\n```', resolved_script, re.DOTALL)
        if script_match:
            resolved_script = script_match.group(1)
        
        return {
            "resolved_script": resolved_script,
            "resolution_notes": self._extract_resolution_notes(model.generate_text(
                f"Explain the key steps taken to resolve the conflict between the migrations:\n\nA: {migration_a}\n\nB: {migration_b}",
                "You are a database migration expert. Explain conflict resolutions clearly and concisely."
            ))
        }
    
    def _extract_impact_level(self, text: str, impact_type: str) -> str:
        """Extract impact level from text"""
        # Look for patterns like "Performance impact: High" or "high performance impact"
        high_pattern = re.compile(rf"(?i){impact_type}.*?(?:high|significant|major|severe)")
        medium_pattern = re.compile(rf"(?i){impact_type}.*?(?:medium|moderate)")
        low_pattern = re.compile(rf"(?i){impact_type}.*?(?:low|minimal|minor)")
        
        if high_pattern.search(text):
            return "high"
        elif medium_pattern.search(text):
            return "medium"
        elif low_pattern.search(text):
            return "low"
        else:
            return "unknown"
    
    def _extract_boolean(self, text: str, keyword: str) -> bool:
        """Extract boolean inference from text"""
        positive_pattern = re.compile(rf"(?i){keyword}.*?(?:required|needed|necessary|yes|true|will be)")
        negative_pattern = re.compile(rf"(?i){keyword}.*?(?:not|no|zero|false|won't be)")
        
        if positive_pattern.search(text) and not negative_pattern.search(text):
            return True
        elif negative_pattern.search(text):
            return False
        else:
            # Default to more cautious interpretation
            return True
    
    def _extract_resolution_notes(self, text: str) -> List[str]:
        """Extract resolution notes from text"""
        # Look for numbered or bulleted lists
        list_items = re.findall(r'(?:^|\n)(?:\d+\.\s+|\*\s+|-\s+)(.+?)(?=\n|$)', text)
        
        if list_items:
            return [item.strip() for item in list_items]
        else:
            # Split by paragraphs if no list found
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            return paragraphs