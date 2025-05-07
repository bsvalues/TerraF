"""
Interactive Tutorial Framework for TerraFlow Platform

This module provides a framework for creating and displaying
interactive guided tutorials for the TerraFlow platform.
"""

import os
import json
import time
import uuid
import logging
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Set, Tuple, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TutorialDifficulty(Enum):
    """Difficulty levels for tutorials"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class TutorialCategory(Enum):
    """Categories for tutorials"""
    GETTING_STARTED = "getting_started"
    FEATURES = "features"
    AGENT_DEVELOPMENT = "agent_development"
    WORKFLOW_AUTOMATION = "workflow_automation"
    INTEGRATION = "integration"
    BEST_PRACTICES = "best_practices"
    TROUBLESHOOTING = "troubleshooting"
    SECURITY = "security"
    PERFORMANCE = "performance"

class StepType(Enum):
    """Types of tutorial steps"""
    INFORMATION = "information"  # Informational step
    ACTION = "action"  # Step requiring user action
    CODE = "code"  # Code example step
    QUIZ = "quiz"  # Quiz step
    VIDEO = "video"  # Video tutorial step
    INTERACTIVE = "interactive"  # Interactive step (e.g., interactive code)

class TutorialStep:
    """
    A step in a tutorial
    
    This class represents a single step in an interactive tutorial.
    """
    
    def __init__(self,
                step_id: str,
                title: str,
                description: str,
                step_type: StepType,
                content: Dict[str, Any],
                order: int,
                estimated_time: int = 0):
        """
        Initialize a new tutorial step
        
        Args:
            step_id: Unique identifier for this step
            title: Step title
            description: Step description
            step_type: Type of step
            content: Step content
            order: Order of this step in the tutorial
            estimated_time: Estimated time to complete (in seconds)
        """
        self.step_id = step_id
        self.title = title
        self.description = description
        self.step_type = step_type
        self.content = content
        self.order = order
        self.estimated_time = estimated_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary for serialization"""
        return {
            "step_id": self.step_id,
            "title": self.title,
            "description": self.description,
            "step_type": self.step_type.value,
            "content": self.content,
            "order": self.order,
            "estimated_time": self.estimated_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TutorialStep':
        """Create step from dictionary"""
        return cls(
            step_id=data["step_id"],
            title=data["title"],
            description=data["description"],
            step_type=StepType(data["step_type"]),
            content=data["content"],
            order=data["order"],
            estimated_time=data.get("estimated_time", 0)
        )

class Tutorial:
    """
    An interactive tutorial for the TerraFlow platform
    
    This class represents an interactive tutorial that guides
    users through a specific feature or workflow.
    """
    
    def __init__(self,
                tutorial_id: str,
                title: str,
                description: str,
                category: TutorialCategory,
                difficulty: TutorialDifficulty,
                tags: List[str],
                version: str = "1.0.0",
                prerequisites: List[str] = None,
                estimated_time: int = 0):
        """
        Initialize a new tutorial
        
        Args:
            tutorial_id: Unique identifier for this tutorial
            title: Tutorial title
            description: Tutorial description
            category: Tutorial category
            difficulty: Tutorial difficulty
            tags: Tutorial tags for searchability
            version: Tutorial version
            prerequisites: List of prerequisite tutorial IDs
            estimated_time: Estimated time to complete (in seconds)
        """
        self.tutorial_id = tutorial_id
        self.title = title
        self.description = description
        self.category = category
        self.difficulty = difficulty
        self.tags = tags
        self.version = version
        self.prerequisites = prerequisites or []
        self.estimated_time = estimated_time
        self.steps = []  # List of TutorialStep
        self.created_at = time.time()
        self.updated_at = time.time()
    
    def add_step(self, step: TutorialStep) -> bool:
        """
        Add a step to the tutorial
        
        Args:
            step: The step to add
            
        Returns:
            bool: True if the step was added, False if a step with the same ID already exists
        """
        # Check if step with same ID already exists
        if any(s.step_id == step.step_id for s in self.steps):
            logger.warning(f"Step with ID {step.step_id} already exists in tutorial {self.tutorial_id}")
            return False
        
        # Add step
        self.steps.append(step)
        
        # Update estimated time
        self.estimated_time = sum(s.estimated_time for s in self.steps)
        
        # Sort steps by order
        self.steps.sort(key=lambda s: s.order)
        
        # Update updated_at
        self.updated_at = time.time()
        
        return True
    
    def get_step(self, step_id: str) -> Optional[TutorialStep]:
        """
        Get a step by ID
        
        Args:
            step_id: ID of the step to get
            
        Returns:
            Optional[TutorialStep]: The step, or None if not found
        """
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def get_step_by_order(self, order: int) -> Optional[TutorialStep]:
        """
        Get a step by order
        
        Args:
            order: Order of the step to get
            
        Returns:
            Optional[TutorialStep]: The step, or None if not found
        """
        for step in self.steps:
            if step.order == order:
                return step
        return None
    
    def get_next_step(self, current_step_id: str) -> Optional[TutorialStep]:
        """
        Get the next step after a given step
        
        Args:
            current_step_id: ID of the current step
            
        Returns:
            Optional[TutorialStep]: The next step, or None if this is the last step
        """
        # Find current step
        current_step = self.get_step(current_step_id)
        if not current_step:
            return None
        
        # Find next step
        for step in self.steps:
            if step.order > current_step.order:
                return step
        
        # No next step found
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tutorial to dictionary for serialization"""
        return {
            "tutorial_id": self.tutorial_id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "difficulty": self.difficulty.value,
            "tags": self.tags,
            "version": self.version,
            "prerequisites": self.prerequisites,
            "estimated_time": self.estimated_time,
            "steps": [step.to_dict() for step in self.steps],
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tutorial':
        """Create tutorial from dictionary"""
        tutorial = cls(
            tutorial_id=data["tutorial_id"],
            title=data["title"],
            description=data["description"],
            category=TutorialCategory(data["category"]),
            difficulty=TutorialDifficulty(data["difficulty"]),
            tags=data["tags"],
            version=data.get("version", "1.0.0"),
            prerequisites=data.get("prerequisites", []),
            estimated_time=data.get("estimated_time", 0)
        )
        
        # Add steps
        for step_data in data.get("steps", []):
            step = TutorialStep.from_dict(step_data)
            tutorial.steps.append(step)
        
        # Sort steps by order
        tutorial.steps.sort(key=lambda s: s.order)
        
        # Set timestamps
        tutorial.created_at = data.get("created_at", time.time())
        tutorial.updated_at = data.get("updated_at", time.time())
        
        return tutorial

class UserProgress:
    """
    User progress through tutorials
    
    This class tracks a user's progress through tutorials,
    including completed steps and achievements.
    """
    
    def __init__(self, user_id: str):
        """
        Initialize new user progress
        
        Args:
            user_id: ID of the user
        """
        self.user_id = user_id
        self.completed_tutorials = {}  # tutorial_id -> completion timestamp
        self.completed_steps = {}  # tutorial_id -> Set[step_id]
        self.achievements = {}  # achievement_id -> achievement data
        self.last_activity = time.time()
    
    def mark_step_completed(self, tutorial_id: str, step_id: str):
        """
        Mark a step as completed
        
        Args:
            tutorial_id: ID of the tutorial
            step_id: ID of the step
        """
        if tutorial_id not in self.completed_steps:
            self.completed_steps[tutorial_id] = set()
        
        self.completed_steps[tutorial_id].add(step_id)
        self.last_activity = time.time()
    
    def mark_tutorial_completed(self, tutorial_id: str):
        """
        Mark a tutorial as completed
        
        Args:
            tutorial_id: ID of the tutorial
        """
        self.completed_tutorials[tutorial_id] = time.time()
        self.last_activity = time.time()
    
    def is_step_completed(self, tutorial_id: str, step_id: str) -> bool:
        """
        Check if a step is completed
        
        Args:
            tutorial_id: ID of the tutorial
            step_id: ID of the step
            
        Returns:
            bool: True if the step is completed, False otherwise
        """
        return tutorial_id in self.completed_steps and step_id in self.completed_steps[tutorial_id]
    
    def is_tutorial_completed(self, tutorial_id: str) -> bool:
        """
        Check if a tutorial is completed
        
        Args:
            tutorial_id: ID of the tutorial
            
        Returns:
            bool: True if the tutorial is completed, False otherwise
        """
        return tutorial_id in self.completed_tutorials
    
    def get_completed_step_count(self, tutorial_id: str) -> int:
        """
        Get the number of completed steps in a tutorial
        
        Args:
            tutorial_id: ID of the tutorial
            
        Returns:
            int: Number of completed steps
        """
        if tutorial_id not in self.completed_steps:
            return 0
        
        return len(self.completed_steps[tutorial_id])
    
    def add_achievement(self, achievement_id: str, achievement_data: Dict[str, Any]):
        """
        Add an achievement
        
        Args:
            achievement_id: ID of the achievement
            achievement_data: Achievement data
        """
        self.achievements[achievement_id] = {
            **achievement_data,
            "earned_at": time.time()
        }
        self.last_activity = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user progress to dictionary for serialization"""
        return {
            "user_id": self.user_id,
            "completed_tutorials": self.completed_tutorials,
            "completed_steps": {tutorial_id: list(steps) for tutorial_id, steps in self.completed_steps.items()},
            "achievements": self.achievements,
            "last_activity": self.last_activity
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProgress':
        """Create user progress from dictionary"""
        progress = cls(user_id=data["user_id"])
        
        # Set completed tutorials
        progress.completed_tutorials = data.get("completed_tutorials", {})
        
        # Set completed steps
        completed_steps = {}
        for tutorial_id, steps in data.get("completed_steps", {}).items():
            completed_steps[tutorial_id] = set(steps)
        progress.completed_steps = completed_steps
        
        # Set achievements
        progress.achievements = data.get("achievements", {})
        
        # Set last activity
        progress.last_activity = data.get("last_activity", time.time())
        
        return progress

class TutorialRegistry:
    """
    Registry for tutorials
    
    This class manages tutorials and user progress.
    """
    
    def __init__(self, data_dir: str = "data/tutorials"):
        """
        Initialize a new tutorial registry
        
        Args:
            data_dir: Directory for storing tutorial data
        """
        self.data_dir = data_dir
        self.tutorials_dir = os.path.join(data_dir, "tutorials")
        self.progress_dir = os.path.join(data_dir, "progress")
        self.tutorials = {}  # tutorial_id -> Tutorial
        self.user_progress = {}  # user_id -> UserProgress
        
        # Create directories
        os.makedirs(self.tutorials_dir, exist_ok=True)
        os.makedirs(self.progress_dir, exist_ok=True)
        
        # Load tutorials
        self._load_tutorials()
    
    def _load_tutorials(self):
        """Load tutorials from disk"""
        for filename in os.listdir(self.tutorials_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.tutorials_dir, filename), "r") as f:
                        tutorial_data = json.load(f)
                        tutorial = Tutorial.from_dict(tutorial_data)
                        self.tutorials[tutorial.tutorial_id] = tutorial
                        
                except Exception as e:
                    logger.error(f"Error loading tutorial {filename}: {str(e)}")
        
        logger.info(f"Loaded {len(self.tutorials)} tutorials")
    
    def _save_tutorial(self, tutorial: Tutorial):
        """Save tutorial to disk"""
        tutorial_path = os.path.join(self.tutorials_dir, f"{tutorial.tutorial_id}.json")
        
        try:
            with open(tutorial_path, "w") as f:
                json.dump(tutorial.to_dict(), f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving tutorial {tutorial.tutorial_id}: {str(e)}")
    
    def _load_user_progress(self, user_id: str) -> UserProgress:
        """Load user progress from disk"""
        progress_path = os.path.join(self.progress_dir, f"{user_id}.json")
        
        if not os.path.exists(progress_path):
            return UserProgress(user_id)
        
        try:
            with open(progress_path, "r") as f:
                progress_data = json.load(f)
                return UserProgress.from_dict(progress_data)
                
        except Exception as e:
            logger.error(f"Error loading user progress for {user_id}: {str(e)}")
            return UserProgress(user_id)
    
    def _save_user_progress(self, progress: UserProgress):
        """Save user progress to disk"""
        progress_path = os.path.join(self.progress_dir, f"{progress.user_id}.json")
        
        try:
            with open(progress_path, "w") as f:
                json.dump(progress.to_dict(), f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving user progress for {progress.user_id}: {str(e)}")
    
    def register_tutorial(self, tutorial: Tutorial) -> bool:
        """
        Register a new tutorial
        
        Args:
            tutorial: The tutorial to register
            
        Returns:
            bool: True if the tutorial was registered, False if a tutorial with the same ID already exists
        """
        if tutorial.tutorial_id in self.tutorials:
            logger.warning(f"Tutorial with ID {tutorial.tutorial_id} already exists")
            return False
        
        self.tutorials[tutorial.tutorial_id] = tutorial
        self._save_tutorial(tutorial)
        
        logger.info(f"Registered tutorial {tutorial.tutorial_id}")
        return True
    
    def update_tutorial(self, tutorial: Tutorial) -> bool:
        """
        Update an existing tutorial
        
        Args:
            tutorial: The tutorial to update
            
        Returns:
            bool: True if the tutorial was updated, False if the tutorial doesn't exist
        """
        if tutorial.tutorial_id not in self.tutorials:
            logger.warning(f"Tutorial with ID {tutorial.tutorial_id} doesn't exist")
            return False
        
        self.tutorials[tutorial.tutorial_id] = tutorial
        self._save_tutorial(tutorial)
        
        logger.info(f"Updated tutorial {tutorial.tutorial_id}")
        return True
    
    def get_tutorial(self, tutorial_id: str) -> Optional[Tutorial]:
        """
        Get a tutorial by ID
        
        Args:
            tutorial_id: ID of the tutorial to get
            
        Returns:
            Optional[Tutorial]: The tutorial, or None if not found
        """
        return self.tutorials.get(tutorial_id)
    
    def get_tutorials_by_category(self, category: TutorialCategory) -> List[Tutorial]:
        """
        Get tutorials by category
        
        Args:
            category: Category to filter by
            
        Returns:
            List[Tutorial]: List of tutorials in the category
        """
        return [t for t in self.tutorials.values() if t.category == category]
    
    def get_tutorials_by_difficulty(self, difficulty: TutorialDifficulty) -> List[Tutorial]:
        """
        Get tutorials by difficulty
        
        Args:
            difficulty: Difficulty to filter by
            
        Returns:
            List[Tutorial]: List of tutorials with the difficulty
        """
        return [t for t in self.tutorials.values() if t.difficulty == difficulty]
    
    def get_tutorials_by_tag(self, tag: str) -> List[Tutorial]:
        """
        Get tutorials by tag
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List[Tutorial]: List of tutorials with the tag
        """
        return [t for t in self.tutorials.values() if tag in t.tags]
    
    def search_tutorials(self, query: str) -> List[Tutorial]:
        """
        Search for tutorials
        
        Args:
            query: Search query
            
        Returns:
            List[Tutorial]: List of tutorials matching the query
        """
        query = query.lower()
        return [t for t in self.tutorials.values() if
                query in t.title.lower() or
                query in t.description.lower() or
                any(query in tag.lower() for tag in t.tags)]
    
    def mark_step_completed(self, user_id: str, tutorial_id: str, step_id: str):
        """
        Mark a step as completed for a user
        
        Args:
            user_id: ID of the user
            tutorial_id: ID of the tutorial
            step_id: ID of the step
        """
        # Get the progress for this user
        progress = self.get_user_progress(user_id)
        
        # Mark step as completed
        progress.mark_step_completed(tutorial_id, step_id)
        
        # Check if all steps are completed
        tutorial = self.get_tutorial(tutorial_id)
        if tutorial and progress.get_completed_step_count(tutorial_id) == len(tutorial.steps):
            progress.mark_tutorial_completed(tutorial_id)
        
        # Save progress
        self._save_user_progress(progress)
    
    def mark_tutorial_completed(self, user_id: str, tutorial_id: str):
        """
        Mark a tutorial as completed for a user
        
        Args:
            user_id: ID of the user
            tutorial_id: ID of the tutorial
        """
        # Get the progress for this user
        progress = self.get_user_progress(user_id)
        
        # Mark tutorial as completed
        progress.mark_tutorial_completed(tutorial_id)
        
        # Save progress
        self._save_user_progress(progress)
    
    def get_user_progress(self, user_id: str) -> UserProgress:
        """
        Get progress for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            UserProgress: The user's progress
        """
        if user_id not in self.user_progress:
            self.user_progress[user_id] = self._load_user_progress(user_id)
        
        return self.user_progress[user_id]
    
    def get_recommended_tutorials(self, user_id: str, limit: int = 5) -> List[Tutorial]:
        """
        Get recommended tutorials for a user
        
        Args:
            user_id: ID of the user
            limit: Maximum number of tutorials to recommend
            
        Returns:
            List[Tutorial]: List of recommended tutorials
        """
        # Get the progress for this user
        progress = self.get_user_progress(user_id)
        
        # Get completed tutorials
        completed_tutorials = set(progress.completed_tutorials.keys())
        
        # Get tutorials by difficulty
        if not completed_tutorials:
            # No completed tutorials, recommend beginner tutorials
            recommendations = self.get_tutorials_by_difficulty(TutorialDifficulty.BEGINNER)
        else:
            # Recommend tutorials based on completed ones
            recommendations = []
            
            # First, get tutorials that are prerequisites for completed ones
            for tutorial_id in completed_tutorials:
                tutorial = self.get_tutorial(tutorial_id)
                if tutorial:
                    for prereq_id in tutorial.prerequisites:
                        if prereq_id not in completed_tutorials:
                            prereq = self.get_tutorial(prereq_id)
                            if prereq and prereq not in recommendations:
                                recommendations.append(prereq)
            
            # If we don't have enough recommendations, add tutorials with same tags as completed ones
            if len(recommendations) < limit:
                # Get tags from completed tutorials
                tags = set()
                for tutorial_id in completed_tutorials:
                    tutorial = self.get_tutorial(tutorial_id)
                    if tutorial:
                        tags.update(tutorial.tags)
                
                # Get tutorials with matching tags
                for tag in tags:
                    for tutorial in self.get_tutorials_by_tag(tag):
                        if tutorial.tutorial_id not in completed_tutorials and tutorial not in recommendations:
                            recommendations.append(tutorial)
                            if len(recommendations) >= limit:
                                break
                    
                    if len(recommendations) >= limit:
                        break
            
            # If we still don't have enough recommendations, add intermediate tutorials
            if len(recommendations) < limit:
                for tutorial in self.get_tutorials_by_difficulty(TutorialDifficulty.INTERMEDIATE):
                    if tutorial.tutorial_id not in completed_tutorials and tutorial not in recommendations:
                        recommendations.append(tutorial)
                        if len(recommendations) >= limit:
                            break
        
        # Limit the number of recommendations
        return recommendations[:limit]
    
    def add_achievement(self, user_id: str, achievement_id: str, achievement_data: Dict[str, Any]):
        """
        Add an achievement for a user
        
        Args:
            user_id: ID of the user
            achievement_id: ID of the achievement
            achievement_data: Achievement data
        """
        # Get the progress for this user
        progress = self.get_user_progress(user_id)
        
        # Add achievement
        progress.add_achievement(achievement_id, achievement_data)
        
        # Save progress
        self._save_user_progress(progress)

# Example tutorials

def create_getting_started_tutorial() -> Tutorial:
    """Create a getting started tutorial"""
    tutorial = Tutorial(
        tutorial_id="getting-started",
        title="Getting Started with TerraFlow",
        description="Learn the basics of the TerraFlow platform and how to use its core features.",
        category=TutorialCategory.GETTING_STARTED,
        difficulty=TutorialDifficulty.BEGINNER,
        tags=["beginner", "overview", "basics"],
        version="1.0.0",
        prerequisites=[]
    )
    
    # Introduction step
    intro_step = TutorialStep(
        step_id="introduction",
        title="Introduction to TerraFlow",
        description="Learn what TerraFlow is and how it can help you.",
        step_type=StepType.INFORMATION,
        content={
            "text": """
# Introduction to TerraFlow

TerraFlow is a comprehensive AI-powered development platform designed to optimize your software development workflow. It combines advanced AI capabilities with intuitive interfaces to enhance productivity, code quality, and collaboration.

## Key Features

- **AI-Assisted Development**: Get intelligent suggestions and automated tasks.
- **Workflow Optimization**: Streamline your development process.
- **Code Analysis**: Identify issues and opportunities for improvement.
- **Multi-Agent Architecture**: Specialized agents for different aspects of development.
            """
        },
        order=1,
        estimated_time=120  # 2 minutes
    )
    tutorial.add_step(intro_step)
    
    # Interface overview step
    interface_step = TutorialStep(
        step_id="interface-overview",
        title="Interface Overview",
        description="Get familiar with the TerraFlow interface.",
        step_type=StepType.INFORMATION,
        content={
            "text": """
# Interface Overview

The TerraFlow interface is designed to be intuitive and efficient. Here are the main components:

## Navigation Sidebar

The sidebar on the left provides access to different sections of the platform:

- **Dashboard**: Overview of your project and activity.
- **Sync Service**: Manage synchronization between services.
- **Workflow Mapper**: Visualize and optimize workflows.
- **Code Analysis**: Analyze code quality and structure.
- **Repository Analysis**: Detailed analysis of your codebase.
- **Security Dashboard**: Monitor and address security issues.

## Main Content Area

The main area displays the content of the selected section.

## Action Bar

The action bar at the top provides access to common actions and settings.
            """,
            "image_url": "https://example.com/terraflow-interface.png"
        },
        order=2,
        estimated_time=180  # 3 minutes
    )
    tutorial.add_step(interface_step)
    
    # First task step
    first_task_step = TutorialStep(
        step_id="first-task",
        title="Your First Task",
        description="Complete your first task with TerraFlow.",
        step_type=StepType.ACTION,
        content={
            "text": """
# Your First Task

Let's complete a simple task to get familiar with TerraFlow. We'll run a basic code analysis on a sample repository.

## Steps

1. Click on the **Code Analysis** section in the sidebar.
2. In the repository field, enter the URL of a GitHub repository, or use the sample repository: `https://github.com/example/sample-repo`.
3. Click the **Analyze** button.
4. Wait for the analysis to complete.
5. Explore the results.

Once you've completed these steps, click the **Mark as Completed** button below.
            """,
            "action": {
                "type": "navigate",
                "target": "code-analysis"
            },
            "validation": {
                "type": "user_confirmation"
            }
        },
        order=3,
        estimated_time=300  # 5 minutes
    )
    tutorial.add_step(first_task_step)
    
    # Using AI agents step
    agents_step = TutorialStep(
        step_id="using-ai-agents",
        title="Using AI Agents",
        description="Learn how to use AI agents to assist with development tasks.",
        step_type=StepType.INFORMATION,
        content={
            "text": """
# Using AI Agents

TerraFlow includes a variety of specialized AI agents that can assist with different aspects of development. Here's how to use them:

## Agent Types

- **Code Quality Agent**: Analyzes code quality and suggests improvements.
- **Architecture Agent**: Analyzes system architecture and suggests optimizations.
- **Security Agent**: Identifies security vulnerabilities and suggests fixes.
- **Documentation Agent**: Generates and updates documentation.
- **Workflow Agent**: Optimizes development workflows.

## Using Agents

1. Navigate to the relevant section (e.g., Code Analysis for the Code Quality Agent).
2. Configure the agent settings.
3. Run the agent.
4. Review the results and suggestions.
5. Apply the suggestions as needed.

Agents can also be used programmatically through the TerraFlow API.
            """
        },
        order=4,
        estimated_time=240  # 4 minutes
    )
    tutorial.add_step(agents_step)
    
    # Quiz step
    quiz_step = TutorialStep(
        step_id="knowledge-check",
        title="Knowledge Check",
        description="Test your understanding of TerraFlow basics.",
        step_type=StepType.QUIZ,
        content={
            "questions": [
                {
                    "id": "q1",
                    "text": "What is the primary purpose of TerraFlow?",
                    "options": [
                        {"id": "a", "text": "To replace human developers"},
                        {"id": "b", "text": "To optimize development workflows and enhance productivity"},
                        {"id": "c", "text": "To generate code from scratch"},
                        {"id": "d", "text": "To manage server infrastructure"}
                    ],
                    "correct_option": "b",
                    "explanation": "TerraFlow is designed to optimize development workflows and enhance productivity through AI-assisted development."
                },
                {
                    "id": "q2",
                    "text": "Which of the following is NOT a type of agent in TerraFlow?",
                    "options": [
                        {"id": "a", "text": "Code Quality Agent"},
                        {"id": "b", "text": "Security Agent"},
                        {"id": "c", "text": "Database Administrator Agent"},
                        {"id": "d", "text": "Documentation Agent"}
                    ],
                    "correct_option": "c",
                    "explanation": "TerraFlow does not have a Database Administrator Agent. The main agent types are Code Quality, Architecture, Security, Documentation, and Workflow agents."
                }
            ]
        },
        order=5,
        estimated_time=180  # 3 minutes
    )
    tutorial.add_step(quiz_step)
    
    # Next steps
    next_steps_step = TutorialStep(
        step_id="next-steps",
        title="Next Steps",
        description="Learn what to do next with TerraFlow.",
        step_type=StepType.INFORMATION,
        content={
            "text": """
# Next Steps

Congratulations! You've completed the Getting Started tutorial. Here are some suggestions for what to do next:

## Explore More Features

- **Run a security scan** on your repository to identify vulnerabilities.
- **Generate documentation** for your codebase using the Documentation Agent.
- **Optimize your workflow** using the Workflow Mapper.

## Complete More Tutorials

Check out these tutorials:

- **Code Analysis Deep Dive**: Learn how to use the Code Analysis features effectively.
- **Workflow Optimization**: Learn how to optimize your development workflow.
- **Security Best Practices**: Learn how to keep your code secure.

## Get Support

If you need help, you can:

- **Check the documentation** by clicking on the question mark icon.
- **Join our community** at [community.terraflow.dev](https://community.terraflow.dev).
- **Contact support** at [support@terraflow.dev](mailto:support@terraflow.dev).
            """
        },
        order=6,
        estimated_time=120  # 2 minutes
    )
    tutorial.add_step(next_steps_step)
    
    return tutorial

def create_code_analysis_tutorial() -> Tutorial:
    """Create a code analysis tutorial"""
    tutorial = Tutorial(
        tutorial_id="code-analysis",
        title="Code Analysis Deep Dive",
        description="Learn how to use the code analysis features to improve your code quality.",
        category=TutorialCategory.FEATURES,
        difficulty=TutorialDifficulty.INTERMEDIATE,
        tags=["code-quality", "analysis"],
        version="1.0.0",
        prerequisites=["getting-started"]
    )
    
    # Introduction step
    intro_step = TutorialStep(
        step_id="introduction",
        title="Introduction to Code Analysis",
        description="Learn about the code analysis features in TerraFlow.",
        step_type=StepType.INFORMATION,
        content={
            "text": """
# Introduction to Code Analysis

TerraFlow's code analysis features help you identify issues and opportunities for improvement in your codebase. The Code Quality Agent analyzes your code and provides suggestions for improving quality, performance, and maintainability.

## Key Features

- **Quality Analysis**: Identify code quality issues such as complexity, duplication, and style violations.
- **Performance Analysis**: Identify performance bottlenecks and inefficient code.
- **Security Analysis**: Identify security vulnerabilities and risky code patterns.
- **Architecture Analysis**: Analyze the structure and organization of your codebase.
- **Trend Analysis**: Track code quality over time.
            """
        },
        order=1,
        estimated_time=180  # 3 minutes
    )
    tutorial.add_step(intro_step)
    
    # More steps would be added here...
    
    return tutorial

def create_security_tutorial() -> Tutorial:
    """Create a security tutorial"""
    tutorial = Tutorial(
        tutorial_id="security-best-practices",
        title="Security Best Practices",
        description="Learn how to keep your code secure with TerraFlow's security features.",
        category=TutorialCategory.SECURITY,
        difficulty=TutorialDifficulty.ADVANCED,
        tags=["security", "best-practices"],
        version="1.0.0",
        prerequisites=["getting-started", "code-analysis"]
    )
    
    # Introduction step
    intro_step = TutorialStep(
        step_id="introduction",
        title="Introduction to Security Features",
        description="Learn about the security features in TerraFlow.",
        step_type=StepType.INFORMATION,
        content={
            "text": """
# Introduction to Security Features

TerraFlow includes a comprehensive set of security features to help you identify and address security vulnerabilities in your codebase. The Security Agent analyzes your code for common security issues and provides recommendations for fixing them.

## Key Features

- **Vulnerability Scanning**: Identify common security vulnerabilities such as injection attacks, cross-site scripting, and authentication issues.
- **Dependency Analysis**: Identify vulnerabilities in your dependencies.
- **Secure Coding Practices**: Get recommendations for following secure coding practices.
- **Security Monitoring**: Monitor your code for security issues over time.
- **Compliance Checking**: Check your code against security standards and compliance requirements.
            """
        },
        order=1,
        estimated_time=180  # 3 minutes
    )
    tutorial.add_step(intro_step)
    
    # More steps would be added here...
    
    return tutorial

# Create tutorial renderer interfaces

class TutorialRenderer:
    """
    Interface for rendering tutorials
    
    This class provides an interface for rendering tutorials
    in different formats (e.g., web, CLI, IDE).
    """
    
    def render_tutorial(self, tutorial: Tutorial):
        """
        Render a tutorial
        
        Args:
            tutorial: The tutorial to render
        """
        raise NotImplementedError("Subclasses must implement render_tutorial")
    
    def render_step(self, tutorial: Tutorial, step: TutorialStep):
        """
        Render a tutorial step
        
        Args:
            tutorial: The tutorial
            step: The step to render
        """
        raise NotImplementedError("Subclasses must implement render_step")

class WebTutorialRenderer(TutorialRenderer):
    """
    Web-based tutorial renderer
    
    This class renders tutorials for web-based interfaces.
    """
    
    def render_tutorial(self, tutorial: Tutorial) -> Dict[str, Any]:
        """
        Render a tutorial for web
        
        Args:
            tutorial: The tutorial to render
            
        Returns:
            Dict[str, Any]: Rendered tutorial data
        """
        return {
            "id": tutorial.tutorial_id,
            "title": tutorial.title,
            "description": tutorial.description,
            "category": tutorial.category.value,
            "difficulty": tutorial.difficulty.value,
            "tags": tutorial.tags,
            "steps": [self._render_step_data(step) for step in tutorial.steps],
            "estimated_time": tutorial.estimated_time
        }
    
    def render_step(self, tutorial: Tutorial, step: TutorialStep) -> Dict[str, Any]:
        """
        Render a tutorial step for web
        
        Args:
            tutorial: The tutorial
            step: The step to render
            
        Returns:
            Dict[str, Any]: Rendered step data
        """
        return {
            "tutorial_id": tutorial.tutorial_id,
            "tutorial_title": tutorial.title,
            **self._render_step_data(step)
        }
    
    def _render_step_data(self, step: TutorialStep) -> Dict[str, Any]:
        """
        Render step data for web
        
        Args:
            step: The step to render
            
        Returns:
            Dict[str, Any]: Rendered step data
        """
        return {
            "id": step.step_id,
            "title": step.title,
            "description": step.description,
            "type": step.step_type.value,
            "content": step.content,
            "order": step.order,
            "estimated_time": step.estimated_time
        }

class CLITutorialRenderer(TutorialRenderer):
    """
    CLI-based tutorial renderer
    
    This class renders tutorials for command-line interfaces.
    """
    
    def render_tutorial(self, tutorial: Tutorial) -> str:
        """
        Render a tutorial for CLI
        
        Args:
            tutorial: The tutorial to render
            
        Returns:
            str: Rendered tutorial text
        """
        lines = [
            f"=== {tutorial.title} ===",
            "",
            tutorial.description,
            "",
            f"Category: {tutorial.category.value}",
            f"Difficulty: {tutorial.difficulty.value}",
            f"Tags: {', '.join(tutorial.tags)}",
            f"Estimated time: {tutorial.estimated_time // 60} minutes",
            "",
            "Steps:",
            ""
        ]
        
        for step in tutorial.steps:
            lines.append(f"{step.order}. {step.title}")
        
        return "\n".join(lines)
    
    def render_step(self, tutorial: Tutorial, step: TutorialStep) -> str:
        """
        Render a tutorial step for CLI
        
        Args:
            tutorial: The tutorial
            step: The step to render
            
        Returns:
            str: Rendered step text
        """
        lines = [
            f"=== {tutorial.title} - Step {step.order} ===",
            "",
            f"=== {step.title} ===",
            "",
            step.description,
            ""
        ]
        
        # Render content based on step type
        if step.step_type == StepType.INFORMATION:
            lines.append(step.content.get("text", ""))
        elif step.step_type == StepType.ACTION:
            lines.append(step.content.get("text", ""))
            lines.append("")
            lines.append("Action required: Complete the steps above, then press Enter to continue.")
        elif step.step_type == StepType.CODE:
            lines.append(step.content.get("text", ""))
            lines.append("")
            lines.append("Code example:")
            lines.append("")
            lines.append("```")
            lines.append(step.content.get("code", ""))
            lines.append("```")
        elif step.step_type == StepType.QUIZ:
            lines.append("Quiz:")
            lines.append("")
            for i, question in enumerate(step.content.get("questions", [])):
                lines.append(f"Question {i+1}: {question['text']}")
                lines.append("")
                for option in question["options"]:
                    lines.append(f"{option['id']}) {option['text']}")
                lines.append("")
        elif step.step_type == StepType.VIDEO:
            lines.append(f"Video: {step.content.get('video_url', '')}")
            lines.append("")
            lines.append("(You may need to open this URL in a web browser)")
        elif step.step_type == StepType.INTERACTIVE:
            lines.append(step.content.get("text", ""))
            lines.append("")
            lines.append("(Interactive steps may require a web or IDE interface)")
        
        return "\n".join(lines)

# Initialize the tutorial registry with example tutorials
def initialize_tutorial_registry() -> TutorialRegistry:
    """Initialize the tutorial registry with example tutorials"""
    registry = TutorialRegistry()
    
    # Create and register example tutorials
    registry.register_tutorial(create_getting_started_tutorial())
    registry.register_tutorial(create_code_analysis_tutorial())
    registry.register_tutorial(create_security_tutorial())
    
    return registry