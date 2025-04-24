"""
Agent Demo UI

This module provides a Streamlit UI for demonstrating and interacting with the various
specialized agents in the TerraFusion platform.
"""

import streamlit as st
import json
import os
import time
import datetime
import random
import logging
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import simplified agent registry
from specialized_agents import register_all_agents

# Import workflow mapper UI module
try:
    from workflow_mapper_ui import render_workflow_mapper_tab, add_workflow_mapper_tab
    WORKFLOW_MAPPER_AVAILABLE = True
except ImportError:
    WORKFLOW_MAPPER_AVAILABLE = False

# Import domain knowledge UI module
try:
    from domain_knowledge_ui import render_domain_knowledge_ui
    DOMAIN_KNOWLEDGE_AVAILABLE = True
except ImportError:
    DOMAIN_KNOWLEDGE_AVAILABLE = False

# Import pattern recognition UI module
try:
    from pattern_recognition_ui import render_pattern_recognition_tab, add_pattern_recognition_tab, add_integrated_analysis_tab, render_integrated_analysis_tab
    PATTERN_RECOGNITION_AVAILABLE = True
    INTEGRATED_ANALYSIS_AVAILABLE = True
except ImportError as e:
    logger.error(f"Pattern recognition UI not available: {str(e)}")
    PATTERN_RECOGNITION_AVAILABLE = False
    INTEGRATED_ANALYSIS_AVAILABLE = False

# Set page configuration
st.set_page_config(
    page_title="Specialized Agent Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables"""
    if 'agents' not in st.session_state:
        st.session_state.agents = register_all_agents()
    
    if 'current_agent' not in st.session_state:
        st.session_state.current_agent = None
    
    if 'demo_results' not in st.session_state:
        st.session_state.demo_results = {}
        
    if 'task_history' not in st.session_state:
        st.session_state.task_history = []
        
    if 'active_tabs' not in st.session_state:
        st.session_state.active_tabs = []

def get_agent_info(agent_key: str) -> Dict[str, Any]:
    """Get information about an agent based on its key"""
    
    agent_info = {
        "style_enforcer": {
            "name": "Style Enforcer Agent",
            "description": "Enforces code style standards and identifies style issues.",
            "capabilities": [
                "Analyze code style and formatting",
                "Identify style guideline violations",
                "Generate style recommendations", 
                "Create style configuration files"
            ],
            "demo_tasks": [
                "Analyze code style",
                "Generate style config",
                "Fix style issues"
            ]
        },
        "bug_hunter": {
            "name": "Bug Hunter Agent",
            "description": "Identifies potential bugs and security vulnerabilities in code.",
            "capabilities": [
                "Detect potential bugs and edge cases",
                "Identify security vulnerabilities",
                "Recommend fixes for identified issues",
                "Generate test cases that would expose bugs"
            ],
            "demo_tasks": [
                "Detect bugs",
                "Analyze security",
                "Generate test cases",
                "Recommend fixes"
            ]
        },
        "performance_optimizer": {
            "name": "Performance Optimizer Agent",
            "description": "Analyzes and optimizes code for performance improvements.",
            "capabilities": [
                "Identify performance bottlenecks",
                "Suggest algorithmic improvements",
                "Recommend caching strategies",
                "Optimize resource usage"
            ],
            "demo_tasks": [
                "Analyze performance",
                "Optimize algorithm",
                "Generate optimized code"
            ]
        },
        "test_coverage": {
            "name": "Test Coverage Agent",
            "description": "Analyzes test coverage and generates test cases.",
            "capabilities": [
                "Analyze test coverage metrics",
                "Identify untested code paths",
                "Generate test cases",
                "Suggest testing strategies"
            ],
            "demo_tasks": [
                "Analyze test coverage",
                "Generate test cases",
                "Suggest testing strategy"
            ]
        },
        "pattern_detector": {
            "name": "Pattern Detector Agent",
            "description": "Detects design patterns and anti-patterns in code.",
            "capabilities": [
                "Identify design patterns in code",
                "Detect anti-patterns",
                "Suggest pattern-based refactorings",
                "Analyze architectural patterns"
            ],
            "demo_tasks": [
                "Identify patterns",
                "Detect anti-patterns",
                "Suggest refactorings"
            ]
        },
        "dependency_manager": {
            "name": "Dependency Manager Agent",
            "description": "Analyzes and manages code dependencies.",
            "capabilities": [
                "Analyze dependency relationships",
                "Identify unused or problematic dependencies",
                "Recommend dependency improvements",
                "Generate dependency management files"
            ],
            "demo_tasks": [
                "Analyze dependencies",
                "Identify problematic dependencies",
                "Generate dependency graph"
            ]
        },
        "db_migration_agent": {
            "name": "Database Migration Agent",
            "description": "Manages database schema migrations.",
            "capabilities": [
                "Plan database schema changes",
                "Generate migration scripts",
                "Track migration history",
                "Analyze migration impact",
                "Resolve migration conflicts"
            ],
            "demo_tasks": [
                "Get migration status",
                "Plan migration",
                "Generate migration script",
                "Analyze migration impact"
            ]
        },
        "integration_test_agent": {
            "name": "Integration Test Agent",
            "description": "Manages and executes integration tests.",
            "capabilities": [
                "Generate integration test scenarios",
                "Create test fixtures and mocks",
                "Execute integration tests",
                "Analyze test results",
                "Recommend test coverage improvements"
            ],
            "demo_tasks": [
                "Generate test scenarios",
                "Create test fixtures",
                "Analyze test results",
                "Recommend improvements"
            ]
        },
        "tech_doc_agent": {
            "name": "Technical Documentation Agent",
            "description": "Generates and manages technical documentation.",
            "capabilities": [
                "Generate API documentation",
                "Create user guides",
                "Document system architecture", 
                "Produce developer onboarding materials",
                "Maintain documentation consistency"
            ],
            "demo_tasks": [
                "Generate API docs",
                "Create user guide",
                "Document architecture",
                "Generate README"
            ]
        },
        "ai_integration_agent": {
            "name": "AI Integration Agent",
            "description": "Integrates with external AI services.",
            "capabilities": [
                "Configure AI service connections",
                "Test API integrations",
                "Optimize model parameters and prompts",
                "Monitor usage and costs",
                "Implement AI service failover"
            ],
            "demo_tasks": [
                "Configure service",
                "Test connection",
                "Optimize prompt",
                "Implement failover"
            ]
        },
        "sync_service_agent": {
            "name": "SyncService Agent",
            "description": "Manages data synchronization between legacy PACS and modern CAMA systems.",
            "capabilities": [
                "Detect changes in source systems",
                "Transform data between formats",
                "Validate data consistency",
                "Perform synchronization operations",
                "Monitor sync processes"
            ],
            "demo_tasks": [
                "Detect changes",
                "Transform data",
                "Validate data",
                "Perform sync",
                "Monitor sync status"
            ]
        }
    }
    
    return agent_info.get(agent_key, {
        "name": agent_key.replace("_", " ").title(),
        "description": "A specialized agent.",
        "capabilities": [],
        "demo_tasks": ["Demo task"]
    })

def render_agent_cards():
    """Render cards for all available agents"""
    
    st.title("TerraFusion Specialized Agent Demo")
    
    st.markdown("""
    This demo showcases the various specialized agents in the TerraFusion platform.
    Each agent has specific capabilities and can be used to perform various tasks.
    Select an agent to see its capabilities and demo tasks.
    """)
    
    # Create columns for agent cards
    cols_per_row = 3
    
    if not st.session_state.agents:
        st.warning("No agents available. Please check that the specialized agents are properly registered.")
        return
    
    # Create rows of agent cards
    agent_keys = list(st.session_state.agents.keys())
    rows = [agent_keys[i:i+cols_per_row] for i in range(0, len(agent_keys), cols_per_row)]
    
    for row in rows:
        cols = st.columns(cols_per_row)
        
        for i, agent_key in enumerate(row):
            agent = st.session_state.agents[agent_key]
            agent_info = get_agent_info(agent_key)
            
            with cols[i]:
                st.subheader(agent_info["name"])
                st.markdown(agent_info["description"])
                
                # Display capabilities
                if agent_info["capabilities"]:
                    with st.expander("Capabilities"):
                        for capability in agent_info["capabilities"]:
                            st.markdown(f"- {capability}")
                
                # Button to demo the agent
                if st.button(f"Demo {agent_info['name']}", key=f"demo_{agent_key}"):
                    st.session_state.current_agent = agent_key
                    if agent_key not in st.session_state.active_tabs:
                        st.session_state.active_tabs.append(agent_key)
                    st.rerun()

def render_demo_tabs():
    """Render tabs for active agent demos"""
    
    if not st.session_state.active_tabs:
        return
    
    tab_titles = [get_agent_info(agent_key)["name"] for agent_key in st.session_state.active_tabs]
    tabs = st.tabs(tab_titles)
    
    for i, agent_key in enumerate(st.session_state.active_tabs):
        with tabs[i]:
            render_agent_demo(agent_key)
            
def render_agent_demo(agent_key: str):
    """Render demo for a specific agent"""
    
    agent_info = get_agent_info(agent_key)
    
    st.header(agent_info["name"])
    st.markdown(agent_info["description"])
    
    # Check if agent exists
    agent = st.session_state.agents.get(agent_key)
    if not agent:
        st.error(f"Agent {agent_key} not available.")
        return
    
    # Display demo tasks
    st.subheader("Demo Tasks")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        demo_task = st.selectbox(
            "Select a task to demo",
            agent_info["demo_tasks"],
            key=f"task_select_{agent_key}"
        )
    
    with col2:
        run_task = st.button("Run Task", key=f"run_{agent_key}")
    
    # Run the selected task
    if run_task:
        with st.spinner(f"Running {demo_task}..."):
            result = run_demo_task(agent_key, demo_task)
            
            # Store the result
            if agent_key not in st.session_state.demo_results:
                st.session_state.demo_results[agent_key] = {}
            
            st.session_state.demo_results[agent_key][demo_task] = result
            
            # Add to task history
            st.session_state.task_history.append({
                "agent": agent_key,
                "task": demo_task,
                "timestamp": time.time()
            })
    
    # Display results
    if agent_key in st.session_state.demo_results:
        st.subheader("Results")
        
        for task, result in st.session_state.demo_results[agent_key].items():
            with st.expander(f"Result: {task}", expanded=(task == demo_task)):
                # Format and display the result
                display_task_result(agent_key, task, result)

def run_demo_task(agent_key: str, task: str) -> Dict[str, Any]:
    """Run a demo task for an agent"""
    
    # In a real implementation, this would call the agent's methods directly
    # For this demo, we'll simulate the agent's behavior
    
    # Get sample data for the task
    task_data = get_sample_task_data(agent_key, task)
    
    # Simulate task execution time
    time.sleep(2)
    
    # Return simulated result
    if agent_key == "style_enforcer":
        if task == "Analyze code style":
            return {
                "style_guide": "PEP 8",
                "issues_count": random.randint(3, 15),
                "issues": [
                    {"line": 10, "description": "Line too long (82 > 79 characters)", "severity": "low"},
                    {"line": 25, "description": "Missing whitespace after comma", "severity": "low"},
                    {"line": 42, "description": "Variable 'x' should be snake_case", "severity": "medium"}
                ],
                "recommendations": [
                    "Format code with Black",
                    "Add Pylint to CI pipeline",
                    "Configure line length to 88 characters"
                ],
                "recommended_tools": ["pylint", "flake8", "black"]
            }
        elif task == "Generate style config":
            return {
                "language": "python",
                "style_guide": "PEP 8",
                "config_filename": ".pylintrc",
                "config_content": """
                [MASTER]
                init-hook='import sys; sys.path.append(".")'
                
                [FORMAT]
                max-line-length=88
                
                [MESSAGES CONTROL]
                disable=C0111,R0903,C0103
                
                [SIMILARITIES]
                min-similarity-lines=7
                """
            }
        elif task == "Fix style issues":
            return {
                "fixed_code": """
def calculate_average(numbers):
    \"\"\"Calculate the average of a list of numbers.\"\"\"
    if not numbers:
        return 0
    
    total = sum(numbers)
    average = total / len(numbers)
    
    return average
                """,
                "is_valid": True,
                "issues_addressed": 3
            }
    
    elif agent_key == "db_migration_agent":
        if task == "Get migration status":
            return {
                "current_revision": "9f72b8a41d3c",
                "available_revisions": [
                    {"revision": "9f72b8a41d3c", "description": "Add user preferences table", "created_date": "2025-04-20 15:32:45"},
                    {"revision": "1a2b3c4d5e6f", "description": "Initial schema", "created_date": "2025-04-15 10:15:30"}
                ],
                "pending_migrations": [
                    {"revision": "abcdef123456", "description": "Add analytics table", "created_date": "2025-04-22 09:45:12"}
                ]
            }
        elif task == "Plan migration":
            return {
                "plan": {
                    "changes": [
                        "Add 'email_verified' boolean column to users table",
                        "Create index on 'email' column in users table",
                        "Rename 'user_prefs' table to 'user_preferences'"
                    ],
                    "issues": [
                        "Column rename requires data copy which may be slow on large tables",
                        "New boolean column will have NULL values for existing users"
                    ],
                    "approach": "Use multi-step migration to minimize downtime: add column with default value first, create separate migration for index creation",
                    "rollback_strategy": "Create reverse migrations for each step"
                },
                "raw_plan": "Database migration plan with detailed analysis..."
            }
        elif task == "Generate migration script":
            return {
                "script_path": "migrations/versions/abcdef123456_add_email_verified.py",
                "message": "Add email_verified to users table",
                "autogenerated": True
            }
        elif task == "Analyze migration impact":
            return {
                "impact": {
                    "performance_impact": "medium",
                    "storage_impact": "low",
                    "locking_impact": "medium",
                    "data_loss_risk": "low",
                    "downtime_required": False
                },
                "raw_analysis": "Detailed analysis of migration impact...",
                "recommendations": [
                    "Run migration during low-traffic period",
                    "Monitor query performance after adding index",
                    "Add application-level validation for new boolean field"
                ]
            }
    
    elif agent_key == "integration_test_agent":
        if task == "Generate test scenarios":
            return {
                "test_scenarios": {
                    "UserService": [
                        {
                            "name": "User Registration Flow",
                            "prerequisites": ["Clean database", "Email service running"],
                            "steps": [
                                "Call register endpoint with valid user data",
                                "Verify user is created in database",
                                "Verify verification email is sent"
                            ],
                            "expected_results": ["User created with inactive status", "Email contains verification token"],
                            "edge_cases": ["Duplicate email registration", "Invalid email format"]
                        },
                        {
                            "name": "User Authentication Flow",
                            "prerequisites": ["Existing user in database"],
                            "steps": [
                                "Call login endpoint with valid credentials",
                                "Verify JWT token is returned",
                                "Call authenticated endpoint with token"
                            ],
                            "expected_results": ["Valid JWT with correct claims", "Authenticated endpoint returns 200"],
                            "edge_cases": ["Invalid password", "Expired token", "Inactive user"]
                        }
                    ],
                    "PaymentService": [
                        {
                            "name": "Payment Processing Flow",
                            "prerequisites": ["Valid user account", "Payment provider mock"],
                            "steps": [
                                "Initiate payment for subscription",
                                "Mock successful payment response",
                                "Verify subscription is activated"
                            ],
                            "expected_results": ["Payment recorded", "Subscription status active", "Receipt email sent"],
                            "edge_cases": ["Payment declined", "Network timeout", "Duplicate payment"]
                        }
                    ]
                },
                "component_count": 2,
                "scenario_count": 3
            }
        elif task == "Create test fixtures":
            return {
                "fixtures": {
                    "fixture_1": """
@pytest.fixture
def test_user():
    \"\"\"Create a test user for authentication tests.\"\"\"
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="$2b$12$IKEQb00u5eHhkplO6KWoTO7JPAQ6RXJ/E0PYPrktmhC72qi9BvltG",
        is_active=True
    )
    db.session.add(user)
    db.session.commit()
    yield user
    db.session.delete(user)
    db.session.commit()
                    """,
                    "fixture_2": """
@pytest.fixture
def auth_client(test_user):
    \"\"\"Create an authenticated test client.\"\"\"
    client = TestClient(app)
    access_token = create_access_token(
        data={"sub": test_user.email},
        expires_delta=timedelta(minutes=30)
    )
    client.headers = {
        "Authorization": f"Bearer {access_token}"
    }
    return client
                    """,
                    "fixture_3": """
@pytest.fixture
def payment_mock():
    \"\"\"Mock the payment provider API.\"\"\"
    with requests_mock.Mocker() as m:
        m.post(
            "https://api.payment-provider.com/v1/charges",
            json={
                "id": "ch_123456",
                "object": "charge",
                "amount": 2000,
                "status": "succeeded"
            }
        )
        yield m
                    """
                },
                "language": "python",
                "framework": "pytest",
                "fixture_count": 3
            }
        elif task == "Analyze test results":
            return {
                "summary": {
                    "total": 42,
                    "passed": 37,
                    "failed": 3,
                    "skipped": 2,
                    "success_rate": 88.1
                },
                "failed_tests": [
                    {
                        "test": "test_payment_timeout",
                        "cause": "Test timed out after 5s waiting for payment confirmation"
                    },
                    {
                        "test": "test_concurrent_updates",
                        "cause": "Race condition: expected 1 update, got 2"
                    },
                    {
                        "test": "test_large_data_import",
                        "cause": "AssertionError: expected 10000 rows, got 9998"
                    }
                ],
                "patterns": [
                    "Timeout issues with external service integration",
                    "Race conditions in concurrent operations",
                    "Edge cases in data processing not fully handled"
                ],
                "recommendations": [
                    "Increase timeout for payment service tests",
                    "Implement proper locking for concurrent operations",
                    "Add validation for edge cases in data import"
                ]
            }
        elif task == "Recommend improvements":
            return {
                "coverage_gaps": [
                    "No tests for error handling in file upload service",
                    "Missing integration tests for notification service",
                    "Insufficient coverage of admin APIs",
                    "No performance tests for data processing pipeline"
                ],
                "priority_scenarios": [
                    {
                        "name": "Error handling in file uploads",
                        "description": "Test scenarios for various file upload errors including format validation, size limits, and corrupt files"
                    },
                    {
                        "name": "Notification delivery",
                        "description": "End-to-end tests for notification delivery across different channels (email, SMS, push)"
                    },
                    {
                        "name": "Admin operations",
                        "description": "Tests for critical admin operations including user management and content moderation"
                    }
                ],
                "quality_improvements": [
                    "Implement contract testing for service boundaries",
                    "Add chaos testing for system resilience",
                    "Improve test isolation to prevent test pollution",
                    "Implement parallel test execution to reduce CI time"
                ],
                "infrastructure_suggestions": [
                    "Set up dedicated test database with consistent test data",
                    "Implement test containers for service dependencies",
                    "Add monitoring for test execution metrics",
                    "Improve test logging for debugging failed tests"
                ]
            }
    
    elif agent_key == "tech_doc_agent":
        if task == "Generate API docs":
            return {
                "documentation": {
                    "/api/users": {
                        "method": "GET",
                        "description": "Get a list of all users in the system. Supports pagination, filtering, and sorting.",
                        "parameters": [
                            {"name": "page", "type": "integer", "description": "Page number, starting from 1", "required": False, "default": 1},
                            {"name": "limit", "type": "integer", "description": "Number of users per page", "required": False, "default": 50},
                            {"name": "sort", "type": "string", "description": "Field to sort by (e.g., 'name', 'created_at')", "required": False}
                        ],
                        "responses": {
                            "200": {"description": "List of users", "schema": {"$ref": "#/components/schemas/UserList"}},
                            "400": {"description": "Invalid parameters"},
                            "401": {"description": "Unauthorized"}
                        },
                        "examples": [
                            {
                                "request": "GET /api/users?page=1&limit=2",
                                "response": {
                                    "users": [
                                        {"id": 1, "name": "Alice", "email": "alice@example.com"},
                                        {"id": 2, "name": "Bob", "email": "bob@example.com"}
                                    ],
                                    "meta": {"total": 42, "page": 1, "pages": 21}
                                }
                            }
                        ]
                    },
                    "/api/users/{id}": {
                        "method": "GET",
                        "description": "Get a specific user by ID.",
                        "parameters": [
                            {"name": "id", "type": "integer", "description": "User ID", "required": True, "in": "path"}
                        ],
                        "responses": {
                            "200": {"description": "User details", "schema": {"$ref": "#/components/schemas/User"}},
                            "404": {"description": "User not found"},
                            "401": {"description": "Unauthorized"}
                        },
                        "examples": [
                            {
                                "request": "GET /api/users/1",
                                "response": {
                                    "id": 1,
                                    "name": "Alice",
                                    "email": "alice@example.com",
                                    "created_at": "2023-01-15T12:00:00Z",
                                    "roles": ["user", "admin"]
                                }
                            }
                        ]
                    }
                },
                "format": "markdown",
                "language": "python",
                "endpoint_count": 2
            }
        elif task == "Create user guide":
            return {
                "user_guide": """
# TerraFusion Platform User Guide

## Introduction

Welcome to TerraFusion, a comprehensive platform for code analysis and workflow management. This guide will help you navigate the platform and make the most of its features.

## Getting Started

### Account Setup

1. Create an account using your email address
2. Verify your email and set up your password
3. Complete your profile with your name and organization

### First Steps

1. Navigate to the Dashboard to see your recent activities
2. Connect your first repository by clicking "Add Repository"
3. Select the repository type (GitHub, GitLab, etc.)
4. Authorize TerraFusion to access your repositories

## Feature Overview

### Repository Analysis

The Repository Analysis feature allows you to gain insights into your codebase:

1. Select a repository from your dashboard
2. Click "Analyze Repository"
3. Choose analysis options (code quality, security, etc.)
4. Wait for the analysis to complete
5. Review the detailed report

### Workflow Mapping

The Workflow Mapping feature helps you visualize and optimize your development workflows:

1. Navigate to the Workflow Mapper
2. Select a repository to analyze
3. Choose the mapping parameters
4. Explore the generated workflow map
5. Use insights to optimize your processes

## Troubleshooting

### Common Issues

- **API Rate Limits**: If you encounter rate limit errors, try again after a few minutes
- **Repository Access**: Ensure TerraFusion has the correct permissions to access your repositories
- **Analysis Timeout**: For large repositories, analysis may take longer; try analyzing specific branches

### Getting Help

- Visit our Help Center at help.terrafusion.com
- Contact support at support@terrafusion.com
- Join our community forum at community.terrafusion.com

## FAQ

1. **How often should I analyze my repository?**
   We recommend running an analysis after major changes or at least once a week.

2. **Can I analyze private repositories?**
   Yes, TerraFusion can analyze private repositories if you grant the appropriate permissions.

3. **How are my repository credentials stored?**
   We use industry-standard encryption and never store your raw credentials.
                """,
                "sections": {
                    "Introduction": "Welcome to TerraFusion, a comprehensive platform for code analysis and workflow management. This guide will help you navigate the platform and make the most of its features.",
                    "Getting Started": "### Account Setup\n\n1. Create an account using your email address\n2. Verify your email and set up your password\n3. Complete your profile with your name and organization\n\n### First Steps\n\n1. Navigate to the Dashboard to see your recent activities\n2. Connect your first repository by clicking \"Add Repository\"\n3. Select the repository type (GitHub, GitLab, etc.)\n4. Authorize TerraFusion to access your repositories",
                    "Feature Overview": "### Repository Analysis\n\nThe Repository Analysis feature allows you to gain insights into your codebase:\n\n1. Select a repository from your dashboard\n2. Click \"Analyze Repository\"\n3. Choose analysis options (code quality, security, etc.)\n4. Wait for the analysis to complete\n5. Review the detailed report\n\n### Workflow Mapping\n\nThe Workflow Mapping feature helps you visualize and optimize your development workflows:\n\n1. Navigate to the Workflow Mapper\n2. Select a repository to analyze\n3. Choose the mapping parameters\n4. Explore the generated workflow map\n5. Use insights to optimize your processes",
                    "Troubleshooting": "### Common Issues\n\n- **API Rate Limits**: If you encounter rate limit errors, try again after a few minutes\n- **Repository Access**: Ensure TerraFusion has the correct permissions to access your repositories\n- **Analysis Timeout**: For large repositories, analysis may take longer; try analyzing specific branches\n\n### Getting Help\n\n- Visit our Help Center at help.terrafusion.com\n- Contact support at support@terrafusion.com\n- Join our community forum at community.terrafusion.com",
                    "FAQ": "1. **How often should I analyze my repository?**\n   We recommend running an analysis after major changes or at least once a week.\n\n2. **Can I analyze private repositories?**\n   Yes, TerraFusion can analyze private repositories if you grant the appropriate permissions.\n\n3. **How are my repository credentials stored?**\n   We use industry-standard encryption and never store your raw credentials."
                },
                "format": "markdown",
                "app_name": "TerraFusion",
                "audience": "end-user"
            }
        elif task == "Document architecture":
            return {
                "architecture_doc": """
# TerraFusion System Architecture

## System Overview

TerraFusion is a microservices-based platform designed for code analysis and workflow optimization. The system employs a modular architecture with specialized services that communicate through well-defined APIs.

## Architecture Principles

- **Modularity**: Each component is self-contained with a single responsibility
- **Scalability**: Components can scale independently based on load
- **Resilience**: The system continues to function even if some components fail
- **Observability**: Comprehensive monitoring and logging throughout the system
- **Security**: Defense-in-depth approach with multiple security layers

## Component Descriptions

### API Gateway

The API Gateway serves as the entry point for all client requests. It handles:
- Request routing to appropriate microservices
- Authentication and rate limiting
- Request/response transformation
- API versioning

### Authentication Service

The Authentication Service manages:
- User authentication (username/password, OAuth, SSO)
- Token generation and validation
- Permission management
- User profile storage

### Repository Service

The Repository Service handles:
- Repository metadata storage
- Integration with source control systems (GitHub, GitLab, etc.)
- Code retrieval and caching
- Change detection

### Analysis Service

The Analysis Service performs:
- Code quality analysis
- Security vulnerability scanning
- Performance analysis
- Technical debt assessment

### Model Content Protocol Server

The MCP Server facilitates:
- Communication between AI models and services
- Model output standardization
- Request formatting and validation
- Response processing

### Agent Orchestration Service

The Agent Orchestration Service manages:
- AI agent lifecycle
- Task distribution and scheduling
- Agent communication
- Result aggregation

## Component Relationships

- Clients interact with the system through the API Gateway
- The API Gateway routes requests to appropriate microservices
- The Authentication Service validates all authenticated requests
- The Repository Service provides code to the Analysis Service
- The Analysis Service uses the MCP Server to interact with AI models
- The Agent Orchestration Service manages specialized agents that perform specific tasks

## Data Flow

1. Users authenticate through the Authentication Service
2. Authenticated requests flow through the API Gateway
3. Repository metadata and code are retrieved by the Repository Service
4. Analysis requests are processed by the Analysis Service
5. AI processing is facilitated by the MCP Server
6. AI agents perform specialized tasks coordinated by the Agent Orchestration Service
7. Results are aggregated and returned to the user

## Deployment Architecture

The system is deployed using containerization and orchestration:
- All components are packaged as Docker containers
- Kubernetes manages container deployment and scaling
- Horizontal scaling is configured for each component
- Load balancers distribute traffic across component instances
- Database clusters provide redundancy for persistent storage

## Security Considerations

- All communication uses TLS encryption
- Authentication uses industry-standard protocols (OAuth 2.0, OIDC)
- Authorization follows least-privilege principle
- Secrets are managed using a dedicated secrets management service
- Regular security scanning and penetration testing

```mermaid
graph TD
    Client[Client] --> ApiGateway[API Gateway]
    ApiGateway --> AuthService[Authentication Service]
    ApiGateway --> RepoService[Repository Service]
    ApiGateway --> AnalysisService[Analysis Service]
    
    AnalysisService --> MCPServer[Model Content Protocol Server]
    MCPServer --> AIModels[AI Models]
    
    AnalysisService --> AgentOrchestrator[Agent Orchestration Service]
    AgentOrchestrator --> Agents[Specialized Agents]
    
    RepoService --> GitProviders[Git Providers]
    AuthService --> UserDB[(User Database)]
    RepoService --> RepoDB[(Repository Database)]
    AnalysisService --> ResultsDB[(Results Database)]
    
    subgraph "Data Layer"
        UserDB
        RepoDB
        ResultsDB
    end
    
    subgraph "AI Layer"
        MCPServer
        AIModels
        AgentOrchestrator
        Agents
    end
```
                """,
                "sections": {
                    "System Overview": "TerraFusion is a microservices-based platform designed for code analysis and workflow optimization. The system employs a modular architecture with specialized services that communicate through well-defined APIs.",
                    "Architecture Principles": "- **Modularity**: Each component is self-contained with a single responsibility\n- **Scalability**: Components can scale independently based on load\n- **Resilience**: The system continues to function even if some components fail\n- **Observability**: Comprehensive monitoring and logging throughout the system\n- **Security**: Defense-in-depth approach with multiple security layers",
                    "Component Descriptions": "### API Gateway\n\nThe API Gateway serves as the entry point for all client requests. It handles:\n- Request routing to appropriate microservices\n- Authentication and rate limiting\n- Request/response transformation\n- API versioning\n\n### Authentication Service\n\nThe Authentication Service manages:\n- User authentication (username/password, OAuth, SSO)\n- Token generation and validation\n- Permission management\n- User profile storage\n\n### Repository Service\n\nThe Repository Service handles:\n- Repository metadata storage\n- Integration with source control systems (GitHub, GitLab, etc.)\n- Code retrieval and caching\n- Change detection\n\n### Analysis Service\n\nThe Analysis Service performs:\n- Code quality analysis\n- Security vulnerability scanning\n- Performance analysis\n- Technical debt assessment\n\n### Model Content Protocol Server\n\nThe MCP Server facilitates:\n- Communication between AI models and services\n- Model output standardization\n- Request formatting and validation\n- Response processing\n\n### Agent Orchestration Service\n\nThe Agent Orchestration Service manages:\n- AI agent lifecycle\n- Task distribution and scheduling\n- Agent communication\n- Result aggregation",
                    "Component Relationships": "- Clients interact with the system through the API Gateway\n- The API Gateway routes requests to appropriate microservices\n- The Authentication Service validates all authenticated requests\n- The Repository Service provides code to the Analysis Service\n- The Analysis Service uses the MCP Server to interact with AI models\n- The Agent Orchestration Service manages specialized agents that perform specific tasks",
                    "Data Flow": "1. Users authenticate through the Authentication Service\n2. Authenticated requests flow through the API Gateway\n3. Repository metadata and code are retrieved by the Repository Service\n4. Analysis requests are processed by the Analysis Service\n5. AI processing is facilitated by the MCP Server\n6. AI agents perform specialized tasks coordinated by the Agent Orchestration Service\n7. Results are aggregated and returned to the user",
                    "Deployment Architecture": "The system is deployed using containerization and orchestration:\n- All components are packaged as Docker containers\n- Kubernetes manages container deployment and scaling\n- Horizontal scaling is configured for each component\n- Load balancers distribute traffic across component instances\n- Database clusters provide redundancy for persistent storage",
                    "Security Considerations": "- All communication uses TLS encryption\n- Authentication uses industry-standard protocols (OAuth 2.0, OIDC)\n- Authorization follows least-privilege principle\n- Secrets are managed using a dedicated secrets management service\n- Regular security scanning and penetration testing"
                },
                "diagrams": {
                    "mermaid_1": """
graph TD
    Client[Client] --> ApiGateway[API Gateway]
    ApiGateway --> AuthService[Authentication Service]
    ApiGateway --> RepoService[Repository Service]
    ApiGateway --> AnalysisService[Analysis Service]
    
    AnalysisService --> MCPServer[Model Content Protocol Server]
    MCPServer --> AIModels[AI Models]
    
    AnalysisService --> AgentOrchestrator[Agent Orchestration Service]
    AgentOrchestrator --> Agents[Specialized Agents]
    
    RepoService --> GitProviders[Git Providers]
    AuthService --> UserDB[(User Database)]
    RepoService --> RepoDB[(Repository Database)]
    AnalysisService --> ResultsDB[(Results Database)]
    
    subgraph "Data Layer"
        UserDB
        RepoDB
        ResultsDB
    end
    
    subgraph "AI Layer"
        MCPServer
        AIModels
        AgentOrchestrator
        Agents
    end
                    """
                },
                "format": "markdown",
                "system_name": "TerraFusion"
            }
        elif task == "Generate README":
            return {
                "readme": """
# TerraFusion

![Build Status](https://img.shields.io/github/workflow/status/terrafusion/platform/CI)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)

An advanced AI-powered code analysis and optimization platform that provides intelligent workflow management through multi-agent AI orchestration and interactive development insights.

## Features

- 🔍 **Deep Code Analysis**: Uncover patterns, issues, and optimization opportunities in your codebase
- 🤖 **AI Agent Orchestration**: Leverage specialized AI agents for different aspects of code analysis
- 📊 **Interactive Visualizations**: Explore your codebase through dynamic visualizations and dashboards
- 🔄 **Workflow Mapping**: Identify and optimize development workflows automatically
- 🔌 **Extensible Plugin System**: Add custom capabilities through the plugin framework
- 🔒 **Secure Integration**: Connect to your version control systems with end-to-end encryption

## Installation

```bash
# Clone the repository
git clone https://github.com/terrafusion/platform.git
cd platform

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
python -m services.database.migrate upgrade

# Start the application
python launcher.py
```

## Usage

### Basic Analysis

```python
from terrafusion import Repository, Analyzer

# Initialize repository
repo = Repository("https://github.com/username/repository")

# Run analysis
analysis = Analyzer(repo).analyze()

# View results
print(analysis.summary())
```

### Using the Web Interface

1. Start the server: `python launcher.py`
2. Open your browser at `http://localhost:5000`
3. Connect your repository
4. Choose analysis options
5. Explore the results

## API Reference

TerraFusion provides a comprehensive REST API for integration with other tools:

- `/api/repositories` - Manage repositories
- `/api/analysis` - Run and retrieve analysis
- `/api/agents` - Interact with specialized agents
- `/api/workflows` - Work with workflow mapping and optimization

Check our [API Documentation](docs/api.md) for details.

## Contributing

We welcome contributions to TerraFusion! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

TerraFusion is released under the MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgments

- Built on the shoulders of amazing open-source projects including Python, PyTorch, and Streamlit
- Special thanks to our early adopters and contributors
                """,
                "format": "markdown",
                "project_name": "TerraFusion",
                "sections": {
                    "TerraFusion": "![Build Status](https://img.shields.io/github/workflow/status/terrafusion/platform/CI)\n![License](https://img.shields.io/badge/license-MIT-blue.svg)\n![Version](https://img.shields.io/badge/version-1.0.0-green.svg)\n\nAn advanced AI-powered code analysis and optimization platform that provides intelligent workflow management through multi-agent AI orchestration and interactive development insights.",
                    "Features": "- 🔍 **Deep Code Analysis**: Uncover patterns, issues, and optimization opportunities in your codebase\n- 🤖 **AI Agent Orchestration**: Leverage specialized AI agents for different aspects of code analysis\n- 📊 **Interactive Visualizations**: Explore your codebase through dynamic visualizations and dashboards\n- 🔄 **Workflow Mapping**: Identify and optimize development workflows automatically\n- 🔌 **Extensible Plugin System**: Add custom capabilities through the plugin framework\n- 🔒 **Secure Integration**: Connect to your version control systems with end-to-end encryption",
                    "Installation": "```bash\n# Clone the repository\ngit clone https://github.com/terrafusion/platform.git\ncd platform\n\n# Install dependencies\npip install -r requirements.txt\n\n# Configure environment\ncp .env.example .env\n# Edit .env with your configuration\n\n# Run database migrations\npython -m services.database.migrate upgrade\n\n# Start the application\npython launcher.py\n```",
                    "Usage": "### Basic Analysis\n\n```python\nfrom terrafusion import Repository, Analyzer\n\n# Initialize repository\nrepo = Repository(\"https://github.com/username/repository\")\n\n# Run analysis\nanalysis = Analyzer(repo).analyze()\n\n# View results\nprint(analysis.summary())\n```\n\n### Using the Web Interface\n\n1. Start the server: `python launcher.py`\n2. Open your browser at `http://localhost:5000`\n3. Connect your repository\n4. Choose analysis options\n5. Explore the results",
                    "API Reference": "TerraFusion provides a comprehensive REST API for integration with other tools:\n\n- `/api/repositories` - Manage repositories\n- `/api/analysis` - Run and retrieve analysis\n- `/api/agents` - Interact with specialized agents\n- `/api/workflows` - Work with workflow mapping and optimization\n\nCheck our [API Documentation](docs/api.md) for details.",
                    "Contributing": "We welcome contributions to TerraFusion! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.",
                    "License": "TerraFusion is released under the MIT License. See [LICENSE](LICENSE) for details.",
                    "Acknowledgments": "- Built on the shoulders of amazing open-source projects including Python, PyTorch, and Streamlit\n- Special thanks to our early adopters and contributors"
                }
            }
    
    elif agent_key == "ai_integration_agent":
        if task == "Configure service":
            return {
                "success": True,
                "service": "openai",
                "config": {
                    "api_key": "sk_...redacted",
                    "api_base": "https://api.openai.com/v1",
                    "timeout": 30
                },
                "message": "OpenAI service configured successfully"
            }
        elif task == "Test connection":
            return {
                "success": True,
                "service": "openai",
                "model": "gpt-4o",
                "response": "This is a simulated test response from OpenAI's GPT-4o model.",
                "latency_ms": 520,
                "tokens": {
                    "prompt": 6,
                    "completion": 15,
                    "total": 21
                }
            }
        elif task == "Optimize prompt":
            return {
                "success": True,
                "service": "openai",
                "model": "gpt-4o",
                "original_prompt": "Tell me about quantum computing",
                "optimized_prompt": "Explain the fundamental principles of quantum computing, including superposition and entanglement, and describe how these principles enable quantum computers to solve certain problems more efficiently than classical computers. Provide specific examples of quantum algorithms like Shor's algorithm and Grover's algorithm, and explain their advantages.",
                "explanation": "The optimized prompt is more specific and structured, guiding the model to provide a comprehensive yet focused explanation of quantum computing. It explicitly requests information about key concepts (superposition, entanglement) and specific algorithms, which will result in a more informative and useful response.",
                "expected_impact": "The optimized prompt will likely result in a more detailed, organized, and technically accurate response about quantum computing fundamentals, algorithms, and applications.",
                "system_message": "You are a quantum physics professor explaining concepts to a student with a strong background in computer science but limited knowledge of quantum mechanics. Focus on conceptual clarity while maintaining technical accuracy.",
                "additional_parameters": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_tokens": 800
                }
            }
        elif task == "Implement failover":
            return {
                "success": True,
                "failover_config": {
                    "primary_service": "openai",
                    "backup_services": ["anthropic", "cohere"],
                    "strategy": "sequential",
                    "timeout": 10,
                    "retry_attempts": 3
                },
                "implementation_code": """
import os
import random
import logging
from typing import Dict, List, Any
import openai
import anthropic
import cohere

class AIServiceFailover:
    def __init__(self):
        # Configure services
        self.services = {
            "openai": {
                "api_key": os.environ.get("OPENAI_API_KEY"),
                "model": "gpt-4o"
            },
            "anthropic": {
                "api_key": os.environ.get("ANTHROPIC_API_KEY"),
                "model": "claude-3-5-sonnet-20241022"
            },
            "cohere": {
                "api_key": os.environ.get("COHERE_API_KEY"),
                "model": "command-r"
            }
        }
        
        # Failover configuration
        self.primary = "openai"
        self.backups = ["anthropic", "cohere"]
        self.timeout = 10
        self.max_retries = 3
        
    def generate_text(self, prompt: str, **kwargs):
        # Try primary service
        try:
            return self._call_openai(prompt, **kwargs)
        except Exception as e:
            logging.warning(f"Primary service failed: {str(e)}")
        
        # Try backup services
        for service in self.backups:
            try:
                if service == "anthropic":
                    return self._call_anthropic(prompt, **kwargs)
                elif service == "cohere":
                    return self._call_cohere(prompt, **kwargs)
            except Exception as e:
                logging.warning(f"Backup service {service} failed: {str(e)}")
                continue
        
        # If all services fail
        raise RuntimeError("All AI services failed")
    
    def _call_openai(self, prompt: str, **kwargs):
        # OpenAI implementation
        openai.api_key = self.services["openai"]["api_key"]
        
        response = openai.chat.completions.create(
            model=kwargs.get("model", self.services["openai"]["model"]),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=kwargs.get("max_tokens", 500),
            temperature=kwargs.get("temperature", 0.7),
            timeout=self.timeout
        )
        
        return {
            "text": response.choices[0].message.content,
            "service": "openai",
            "model": kwargs.get("model", self.services["openai"]["model"])
        }
    
    def _call_anthropic(self, prompt: str, **kwargs):
        # Anthropic implementation
        client = anthropic.Anthropic(api_key=self.services["anthropic"]["api_key"])
        
        response = client.messages.create(
            model=kwargs.get("model", self.services["anthropic"]["model"]),
            max_tokens=kwargs.get("max_tokens", 500),
            temperature=kwargs.get("temperature", 0.7),
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return {
            "text": response.content[0].text,
            "service": "anthropic",
            "model": kwargs.get("model", self.services["anthropic"]["model"])
        }
    
    def _call_cohere(self, prompt: str, **kwargs):
        # Cohere implementation
        client = cohere.Client(self.services["cohere"]["api_key"])
        
        response = client.generate(
            prompt=prompt,
            model=kwargs.get("model", self.services["cohere"]["model"]),
            max_tokens=kwargs.get("max_tokens", 500),
            temperature=kwargs.get("temperature", 0.7)
        )
        
        return {
            "text": response.generations[0].text,
            "service": "cohere",
            "model": kwargs.get("model", self.services["cohere"]["model"])
        }
                """,
                "message": "Failover configuration generated successfully for openai with 2 backup services"
            }
            
    elif agent_key == "sync_service_agent":
        if task == "Detect changes":
            return {
                "detected_changes": [
                    {
                        "record_id": "101",
                        "source_table": "properties",
                        "change_type": "update",
                        "timestamp": datetime.datetime.now().isoformat(),
                        "fields_changed": ["assessment_value", "last_sale_date", "zoning_code"]
                    },
                    {
                        "record_id": "204",
                        "source_table": "valuations",
                        "change_type": "insert",
                        "timestamp": datetime.datetime.now().isoformat(),
                        "fields_changed": ["all"]
                    },
                    {
                        "record_id": "153",
                        "source_table": "owners",
                        "change_type": "update",
                        "timestamp": datetime.datetime.now().isoformat(),
                        "fields_changed": ["mailing_address", "phone_number"]
                    }
                ],
                "change_counts": {
                    "insert": 1,
                    "update": 2,
                    "delete": 0,
                    "no_change": 0
                },
                "total_changes": 3,
                "source_system": "PACS"
            }
        elif task == "Transform data":
            return {
                "transformation_result": {
                    "records_transformed": 3,
                    "transformation_map": {
                        "pacs_property_id": "cama_parcel_id",
                        "pacs_valuation": "cama_assessed_value",
                        "pacs_owner_name": "cama_primary_owner",
                        "pacs_sale_date": "cama_last_transfer_date"
                    },
                    "enrichments_applied": [
                        "Geocoding for addresses",
                        "Owner name standardization",
                        "Valuation normalization"
                    ],
                    "validation_rules_applied": 12
                },
                "sample_transformed_record": {
                    "original": {
                        "property_id": "PA-10045",
                        "address": "123 Main St",
                        "owner_name": "SMITH, JOHN & JANE",
                        "valuation": 450000,
                        "sale_date": "2024-02-15"
                    },
                    "transformed": {
                        "parcel_id": "10045",
                        "site_address": "123 Main St",
                        "geocode": {"lat": 40.7128, "lng": -74.0060},
                        "primary_owner": "John Smith",
                        "additional_owners": ["Jane Smith"],
                        "assessed_value": 450000,
                        "last_transfer_date": "2024-02-15",
                        "last_transfer_type": "WARRANTY DEED"
                    }
                }
            }
        elif task == "Validate data":
            return {
                "validation_result": {
                    "records_validated": 3,
                    "records_valid": 2,
                    "records_invalid": 1,
                    "validation_rules": [
                        "Required fields present",
                        "Data type validation",
                        "Value range validation",
                        "Referential integrity"
                    ]
                },
                "validation_issues": [
                    {
                        "record_id": "204",
                        "field": "assessed_value",
                        "issue": "Value cannot be negative",
                        "severity": "error",
                        "recommended_fix": "Set value to zero or correct input"
                    }
                ],
                "data_quality_score": 0.85
            }
        elif task == "Perform sync":
            return {
                "sync_result": {
                    "success": True,
                    "sync_type": "incremental",
                    "start_time": (datetime.datetime.now() - datetime.timedelta(minutes=2)).isoformat(),
                    "end_time": datetime.datetime.now().isoformat(),
                    "duration_seconds": 120.5,
                    "records_processed": 3,
                    "records_succeeded": 3,
                    "records_failed": 0,
                    "tables_affected": ["properties", "valuations", "owners"]
                },
                "sync_details": {
                    "inserts": 1,
                    "updates": 2,
                    "deletes": 0,
                    "system_metrics": {
                        "cpu_usage": "45%",
                        "memory_usage": "320MB",
                        "network_io": "12MB"
                    }
                }
            }
        elif task == "Monitor sync status":
            return {
                "overall_status": "healthy",
                "sync_history": [
                    {
                        "sync_id": "sync-1123",
                        "sync_type": "full",
                        "start_time": (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat(),
                        "end_time": (datetime.datetime.now() - datetime.timedelta(days=7) + datetime.timedelta(hours=2)).isoformat(),
                        "duration_seconds": 7200,
                        "records_processed": 25000,
                        "success": True
                    },
                    {
                        "sync_id": "sync-1130",
                        "sync_type": "incremental",
                        "start_time": (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat(),
                        "end_time": (datetime.datetime.now() - datetime.timedelta(days=1) + datetime.timedelta(minutes=15)).isoformat(),
                        "duration_seconds": 900,
                        "records_processed": 45,
                        "success": True
                    },
                    {
                        "sync_id": "sync-1131",
                        "sync_type": "incremental",
                        "start_time": (datetime.datetime.now() - datetime.timedelta(minutes=5)).isoformat(),
                        "end_time": datetime.datetime.now().isoformat(),
                        "duration_seconds": 300,
                        "records_processed": 3,
                        "success": True
                    }
                ],
                "system_health": {
                    "pacs_connection": "connected",
                    "cama_connection": "connected",
                    "processor_status": "active",
                    "queue_depth": 0
                },
                "next_scheduled_sync": (datetime.datetime.now() + datetime.timedelta(hours=6)).isoformat()
            }
    
    # Default fallback response
    return {
        "agent": agent_key,
        "task": task,
        "simulated": True,
        "message": "Task completed successfully",
        "timestamp": time.time()
    }

def get_sample_task_data(agent_key: str, task: str) -> Dict[str, Any]:
    """Get sample data for a specific task"""
    
    if agent_key == "style_enforcer" and task == "Analyze code style":
        return {
            "code": """
def calculate_average(numbers):
  '''Calculate the average of a list of numbers.'''
  if not numbers:
    return 0;
  total=sum(numbers)
  average=total/len(numbers)
  return average
            """,
            "language": "python"
        }
    
    elif agent_key == "db_migration_agent" and task == "Plan migration":
        return {
            "current_models": {
                "User": {
                    "columns": [
                        {"name": "id", "type": "Integer", "primary_key": True},
                        {"name": "username", "type": "String", "nullable": False},
                        {"name": "email", "type": "String", "nullable": False},
                        {"name": "password", "type": "String", "nullable": False}
                    ]
                },
                "UserPreferences": {
                    "columns": [
                        {"name": "id", "type": "Integer", "primary_key": True},
                        {"name": "user_id", "type": "Integer", "foreign_key": "User.id"},
                        {"name": "theme", "type": "String", "nullable": True},
                        {"name": "notifications_enabled", "type": "Boolean", "default": True}
                    ]
                }
            },
            "target_models": {
                "User": {
                    "columns": [
                        {"name": "id", "type": "Integer", "primary_key": True},
                        {"name": "username", "type": "String", "nullable": False},
                        {"name": "email", "type": "String", "nullable": False},
                        {"name": "password", "type": "String", "nullable": False},
                        {"name": "email_verified", "type": "Boolean", "nullable": False, "default": False}
                    ],
                    "indices": [
                        {"name": "ix_user_email", "columns": ["email"]}
                    ]
                },
                "UserPreferences": {
                    "columns": [
                        {"name": "id", "type": "Integer", "primary_key": True},
                        {"name": "user_id", "type": "Integer", "foreign_key": "User.id"},
                        {"name": "theme", "type": "String", "nullable": True},
                        {"name": "notifications_enabled", "type": "Boolean", "default": True},
                        {"name": "language", "type": "String", "nullable": True, "default": "en"}
                    ]
                }
            }
        }
    
    elif agent_key == "tech_doc_agent" and task == "Generate API docs":
        return {
            "code_files": {
                "api/users.py": """
from fastapi import APIRouter, Depends, Query
from typing import List, Optional

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/")
async def get_users(
    page: int = Query(1, gt=0, description="Page number"),
    limit: int = Query(50, gt=0, le=100, description="Items per page"),
    sort: Optional[str] = None
):
    \"\"\"
    Get a list of all users in the system.
    
    Supports pagination, filtering, and sorting.
    \"\"\"
    # Implementation...
    return {"users": [], "meta": {"total": 0, "page": page, "pages": 0}}

@router.get("/{id}")
async def get_user(id: int):
    \"\"\"
    Get a specific user by ID.
    \"\"\"
    # Implementation...
    return {"id": id, "name": "Example User", "email": "user@example.com"}
                """
            },
            "api_specs": {
                "/api/users": {
                    "method": "GET",
                    "description": "Get a list of users",
                    "parameters": [
                        {"name": "page", "type": "integer", "required": False},
                        {"name": "limit", "type": "integer", "required": False}
                    ],
                    "responses": {
                        "200": {"description": "List of users"},
                        "401": {"description": "Unauthorized"}
                    }
                },
                "/api/users/{id}": {
                    "method": "GET",
                    "description": "Get a user by ID",
                    "parameters": [
                        {"name": "id", "type": "integer", "required": True}
                    ],
                    "responses": {
                        "200": {"description": "User details"},
                        "404": {"description": "User not found"}
                    }
                }
            },
            "language": "python",
            "format": "markdown"
        }
    
    elif agent_key == "sync_service_agent":
        if task == "Detect changes":
            return {
                "source_system": "PACS",
                "tables": ["properties", "valuations", "owners"],
                "last_sync_time": (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()
            }
        elif task == "Transform data":
            return {
                "records": [
                    {
                        "property_id": "PA-10045",
                        "address": "123 Main St",
                        "owner_name": "SMITH, JOHN & JANE",
                        "valuation": 450000,
                        "sale_date": "2024-02-15"
                    }
                ],
                "mapping_rules": {
                    "pacs_property_id": "cama_parcel_id",
                    "pacs_valuation": "cama_assessed_value",
                    "pacs_owner_name": "cama_primary_owner",
                    "pacs_sale_date": "cama_last_transfer_date"
                },
                "validation_rules": {
                    "assessed_value": "must be positive"
                }
            }
        elif task == "Validate data":
            return {
                "records": [
                    {
                        "parcel_id": "10045",
                        "site_address": "123 Main St",
                        "primary_owner": "John Smith",
                        "assessed_value": 450000
                    },
                    {
                        "parcel_id": "20078",
                        "site_address": "456 Oak Ave",
                        "primary_owner": "Sarah Johnson",
                        "assessed_value": -1000
                    }
                ],
                "validation_rules": [
                    "required_fields:parcel_id,site_address,primary_owner,assessed_value",
                    "assessed_value:positive_number",
                    "site_address:valid_address_format"
                ]
            }
        elif task == "Perform sync":
            return {
                "sync_type": "incremental",
                "source_system": "PACS",
                "target_system": "CAMA",
                "records_to_sync": 3,
                "tables": ["properties", "valuations", "owners"]
            }
        elif task == "Monitor sync status":
            return {
                "sync_history_days": 7,
                "system_health": True
            }
    
    # Default fallback data
    return {
        "task": task,
        "simulated": True
    }

def display_task_result(agent_key: str, task: str, result: Dict[str, Any]):
    """Display the result of a task in a formatted way"""
    
    # Filter out certain fields that shouldn't be displayed
    display_result = result.copy()
    for field in ['raw_output', 'raw_analysis', 'raw_plan']:
        if field in display_result:
            del display_result[field]
    
    # Format output based on agent and task
    if agent_key in ["style_enforcer", "bug_hunter"] and "issues" in display_result:
        st.subheader("Issues Found")
        for issue in display_result.get("issues", [])[:5]:  # Show first 5 issues
            st.markdown(f"**Line {issue.get('line', 'N/A')}**: {issue.get('description', 'No description')} ({issue.get('severity', 'unknown')} severity)")
        
        if "recommendations" in display_result:
            st.subheader("Recommendations")
            for rec in display_result.get("recommendations", []):
                st.markdown(f"- {rec}")
    
    elif agent_key == "db_migration_agent" and task == "Plan migration":
        if "plan" in display_result:
            plan = display_result["plan"]
            
            st.subheader("Proposed Changes")
            for change in plan.get("changes", []):
                st.markdown(f"- {change}")
                
            st.subheader("Potential Issues")
            for issue in plan.get("issues", []):
                st.markdown(f"- {issue}")
                
            st.subheader("Approach")
            st.markdown(plan.get("approach", "No approach specified"))
            
            st.subheader("Rollback Strategy")
            st.markdown(plan.get("rollback_strategy", "No rollback strategy specified"))
    
    elif agent_key == "tech_doc_agent" and task == "Generate API docs":
        if "documentation" in display_result:
            st.subheader("API Documentation")
            
            for endpoint, doc in display_result["documentation"].items():
                st.markdown(f"### `{doc.get('method', 'GET')} {endpoint}`")
                st.markdown(doc.get("description", "No description provided"))
                
                if "parameters" in doc and doc["parameters"]:
                    st.markdown("**Parameters:**")
                    params_text = "\n".join([f"- `{p.get('name')}` ({p.get('type', 'any')}): {p.get('description', 'No description')}" for p in doc["parameters"]])
                    st.markdown(params_text)
                
                if "responses" in doc and doc["responses"]:
                    st.markdown("**Responses:**")
                    resp_text = "\n".join([f"- `{code}`: {r.get('description', 'No description')}" for code, r in doc["responses"].items()])
                    st.markdown(resp_text)
                
                if "examples" in doc and doc["examples"]:
                    with st.expander("Examples"):
                        for ex in doc["examples"]:
                            st.code(f"Request: {ex.get('request', 'No request')}")
                            st.code(json.dumps(ex.get("response", {}), indent=2), language="json")
                
                st.markdown("---")
    
    elif agent_key == "tech_doc_agent" and task in ["Create user guide", "Document architecture", "Generate README"]:
        if any(k in display_result for k in ["user_guide", "architecture_doc", "readme"]):
            content = display_result.get("user_guide") or display_result.get("architecture_doc") or display_result.get("readme")
            st.markdown(content)
    
    elif agent_key == "integration_test_agent" and task == "Generate test scenarios":
        if "test_scenarios" in display_result:
            for component, scenarios in display_result["test_scenarios"].items():
                st.subheader(f"Component: {component}")
                
                for i, scenario in enumerate(scenarios):
                    st.markdown(f"### Scenario {i+1}: {scenario.get('name', 'Unnamed Scenario')}")
                    
                    st.markdown("**Prerequisites:**")
                    for prereq in scenario.get("prerequisites", []):
                        st.markdown(f"- {prereq}")
                    
                    st.markdown("**Steps:**")
                    for step in scenario.get("steps", []):
                        st.markdown(f"- {step}")
                    
                    st.markdown("**Expected Results:**")
                    for result in scenario.get("expected_results", []):
                        st.markdown(f"- {result}")
                    
                    if "edge_cases" in scenario and scenario["edge_cases"]:
                        st.markdown("**Edge Cases:**")
                        for edge in scenario["edge_cases"]:
                            st.markdown(f"- {edge}")
                    
                    st.markdown("---")
    
    elif agent_key == "ai_integration_agent" and task == "Optimize prompt":
        if "optimized_prompt" in display_result:
            st.subheader("Optimized Prompt")
            st.markdown(f"```\n{display_result['optimized_prompt']}\n```")
            
            if "explanation" in display_result:
                st.subheader("Explanation")
                st.markdown(display_result["explanation"])
            
            if "system_message" in display_result and display_result["system_message"]:
                st.subheader("Suggested System Message")
                st.markdown(f"```\n{display_result['system_message']}\n```")
            
            if "additional_parameters" in display_result and display_result["additional_parameters"]:
                st.subheader("Additional Parameters")
                for param, value in display_result["additional_parameters"].items():
                    st.markdown(f"- `{param}`: {value}")
    
    elif agent_key == "sync_service_agent":
        if task == "Detect changes":
            st.subheader("Detected Changes")
            
            # Show summary counts
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Changes", display_result.get("total_changes", 0))
            
            change_counts = display_result.get("change_counts", {})
            col2.metric("Inserts", change_counts.get("insert", 0))
            col3.metric("Updates", change_counts.get("update", 0))
            col4.metric("Deletes", change_counts.get("delete", 0))
            
            # Show details of changes
            if "detected_changes" in display_result:
                st.subheader("Change Details")
                for change in display_result["detected_changes"]:
                    with st.expander(f"{change.get('change_type', 'unknown').upper()} - {change.get('source_table', 'unknown')} (ID: {change.get('record_id', 'unknown')})"):
                        st.write(f"**Record ID:** {change.get('record_id', 'unknown')}")
                        st.write(f"**Source Table:** {change.get('source_table', 'unknown')}")
                        st.write(f"**Change Type:** {change.get('change_type', 'unknown')}")
                        st.write(f"**Timestamp:** {change.get('timestamp', 'unknown')}")
                        
                        if "fields_changed" in change:
                            st.write("**Fields Changed:**")
                            for field in change["fields_changed"]:
                                st.markdown(f"- {field}")
                                
        elif task == "Transform data":
            st.subheader("Transformation Results")
            
            # Show transformation summary
            if "transformation_result" in display_result:
                result = display_result["transformation_result"]
                st.metric("Records Transformed", result.get("records_transformed", 0))
                
                # Show mapping rules
                if "transformation_map" in result:
                    st.subheader("Transformation Mapping")
                    mapping_data = [[src, "→", tgt] for src, tgt in result["transformation_map"].items()]
                    st.table({"Source Field": [m[0] for m in mapping_data], 
                             "": [m[1] for m in mapping_data],
                             "Target Field": [m[2] for m in mapping_data]})
                
                # Show enrichments
                if "enrichments_applied" in result:
                    st.subheader("Enrichments Applied")
                    for enrichment in result["enrichments_applied"]:
                        st.markdown(f"- {enrichment}")
            
            # Show sample transformation
            if "sample_transformed_record" in display_result:
                sample = display_result["sample_transformed_record"]
                
                st.subheader("Sample Transformation")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Original Record**")
                    st.json(sample.get("original", {}))
                
                with col2:
                    st.markdown("**Transformed Record**")
                    st.json(sample.get("transformed", {}))
                    
        elif task == "Validate data":
            st.subheader("Validation Results")
            
            # Show validation summary
            if "validation_result" in display_result:
                result = display_result["validation_result"]
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Records Validated", result.get("records_validated", 0))
                col2.metric("Valid Records", result.get("records_valid", 0))
                col3.metric("Invalid Records", result.get("records_invalid", 0))
                
                if "data_quality_score" in display_result:
                    score = display_result["data_quality_score"]
                    st.metric("Data Quality Score", f"{score:.2f}" if isinstance(score, (int, float)) else score)
                
                # Show validation rules
                if "validation_rules" in result:
                    st.subheader("Validation Rules Applied")
                    for rule in result["validation_rules"]:
                        st.markdown(f"- {rule}")
            
            # Show validation issues
            if "validation_issues" in display_result:
                st.subheader("Validation Issues")
                for issue in display_result["validation_issues"]:
                    with st.expander(f"{issue.get('severity', 'unknown').upper()}: {issue.get('issue', 'Unknown issue')}"):
                        st.write(f"**Record ID:** {issue.get('record_id', 'unknown')}")
                        st.write(f"**Field:** {issue.get('field', 'unknown')}")
                        st.write(f"**Issue:** {issue.get('issue', 'unknown')}")
                        st.write(f"**Severity:** {issue.get('severity', 'unknown')}")
                        
                        if "recommended_fix" in issue:
                            st.write(f"**Recommended Fix:** {issue['recommended_fix']}")
                            
        elif task == "Perform sync":
            st.subheader("Sync Results")
            
            # Show sync summary
            if "sync_result" in display_result:
                result = display_result["sync_result"]
                
                # Display sync type and success status
                st.write(f"**Sync Type:** {result.get('sync_type', 'unknown')}")
                
                if result.get("success", False):
                    st.success("Sync completed successfully")
                else:
                    st.error("Sync failed")
                
                # Display metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("Records Processed", result.get("records_processed", 0))
                col2.metric("Records Succeeded", result.get("records_succeeded", 0))
                col3.metric("Records Failed", result.get("records_failed", 0))
                
                # Display timing information
                st.subheader("Timing")
                st.write(f"**Start Time:** {result.get('start_time', 'unknown')}")
                st.write(f"**End Time:** {result.get('end_time', 'unknown')}")
                st.write(f"**Duration:** {result.get('duration_seconds', 0)} seconds")
                
                # Display affected tables
                if "tables_affected" in result:
                    st.subheader("Tables Affected")
                    for table in result["tables_affected"]:
                        st.markdown(f"- {table}")
            
            # Show sync details
            if "sync_details" in display_result:
                details = display_result["sync_details"]
                
                st.subheader("Sync Details")
                
                # Display operation counts
                col1, col2, col3 = st.columns(3)
                col1.metric("Inserts", details.get("inserts", 0))
                col2.metric("Updates", details.get("updates", 0))
                col3.metric("Deletes", details.get("deletes", 0))
                
                # Display system metrics
                if "system_metrics" in details:
                    st.subheader("System Metrics")
                    metrics = details["system_metrics"]
                    for name, value in metrics.items():
                        st.metric(name.replace("_", " ").title(), value)
                        
        elif task == "Monitor sync status":
            st.subheader("Sync Status Monitor")
            
            # Overall status
            status = display_result.get("overall_status", "unknown")
            if status.lower() == "healthy":
                st.success(f"Overall Status: {status}")
            elif status.lower() in ["warning", "degraded"]:
                st.warning(f"Overall Status: {status}")
            else:
                st.error(f"Overall Status: {status}")
            
            # System health details
            if "system_health" in display_result:
                health = display_result["system_health"]
                
                st.subheader("System Health")
                col1, col2 = st.columns(2)
                
                col1.write(f"**PACS Connection:** {health.get('pacs_connection', 'unknown')}")
                col1.write(f"**CAMA Connection:** {health.get('cama_connection', 'unknown')}")
                
                col2.write(f"**Processor Status:** {health.get('processor_status', 'unknown')}")
                col2.write(f"**Queue Depth:** {health.get('queue_depth', 'unknown')}")
            
            # Next scheduled sync
            if "next_scheduled_sync" in display_result:
                st.subheader("Schedule")
                st.write(f"**Next Scheduled Sync:** {display_result['next_scheduled_sync']}")
            
            # Sync history
            if "sync_history" in display_result:
                st.subheader("Sync History")
                
                # Create a table for sync history
                history_data = []
                for sync in display_result["sync_history"]:
                    history_data.append({
                        "Sync ID": sync.get("sync_id", "unknown"),
                        "Type": sync.get("sync_type", "unknown"),
                        "Start Time": sync.get("start_time", "unknown"),
                        "Duration (s)": sync.get("duration_seconds", "unknown"),
                        "Records": sync.get("records_processed", 0),
                        "Status": "✅" if sync.get("success", False) else "❌"
                    })
                
                # Construct a markdown table
                if history_data:
                    table_md = "| Sync ID | Type | Start Time | Duration (s) | Records | Status |\n"
                    table_md += "|---------|------|------------|-------------|---------|--------|\n"
                    
                    for entry in history_data:
                        table_md += f"| {entry['Sync ID']} | {entry['Type']} | {entry['Start Time']} | {entry['Duration (s)']} | {entry['Records']} | {entry['Status']} |\n"
                    
                    st.markdown(table_md)
    
    else:
        # Generic JSON display for other results
        st.json(display_result)

def render_task_history():
    """Render the task history"""
    
    if not st.session_state.task_history:
        st.info("No tasks have been run yet.")
        return
    
    st.subheader("Task History")
    
    for i, task in enumerate(reversed(st.session_state.task_history[-10:])):  # Show latest 10 tasks
        agent_key = task["agent"]
        agent_info = get_agent_info(agent_key)
        
        with st.expander(f"{agent_info['name']} - {task['task']} ({time.strftime('%H:%M:%S', time.localtime(task['timestamp']))})", expanded=(i == 0)):
            if st.button("Run Again", key=f"again_{i}_{agent_key}_{task['task']}"):
                result = run_demo_task(agent_key, task["task"])
                st.session_state.demo_results[agent_key][task["task"]] = result
                st.rerun()
            
            if agent_key in st.session_state.demo_results and task["task"] in st.session_state.demo_results[agent_key]:
                display_task_result(agent_key, task["task"], st.session_state.demo_results[agent_key][task["task"]])

def main():
    """Main function for the app"""
    
    # Initialize session state
    initialize_session_state()
    
    # Add sidebar content
    st.sidebar.title("Agent Demo UI")
    
    # Add sidebar navigation
    sidebar_options = ["Agent Dashboard", "Task History", "Workflow Optimizer", "Domain Knowledge", "Pattern Recognition", "Integrated Analysis"]
    selected_view = st.sidebar.radio("Navigation", sidebar_options)
    
    # Display main content
    if selected_view == "Agent Dashboard":
        render_agent_cards()
        st.markdown("---")
        render_demo_tabs()
    elif selected_view == "Task History":
        render_task_history()
    elif selected_view == "Workflow Optimizer":
        if WORKFLOW_MAPPER_AVAILABLE:
            # Set the repo path to the current directory for the workflow mapper
            if 'repo_path' not in st.session_state:
                st.session_state.repo_path = os.getcwd()
            render_workflow_mapper_tab()
        else:
            st.error("Workflow Mapper functionality is not available. Please check the installation.")
    elif selected_view == "Domain Knowledge":
        if DOMAIN_KNOWLEDGE_AVAILABLE:
            render_domain_knowledge_ui()
        else:
            st.error("Domain Knowledge functionality is not available. Please check the installation.")
    elif selected_view == "Pattern Recognition":
        if PATTERN_RECOGNITION_AVAILABLE:
            # Set the repo path to the current directory for the pattern recognition
            if 'repo_path' not in st.session_state:
                st.session_state.repo_path = os.getcwd()
            render_pattern_recognition_tab()
        else:
            st.error("Pattern Recognition functionality is not available. Please check the installation.")
    elif selected_view == "Integrated Analysis":
        if INTEGRATED_ANALYSIS_AVAILABLE:
            # Set the repo path to the current directory for the integrated analysis
            if 'repo_path' not in st.session_state:
                st.session_state.repo_path = os.getcwd()
            render_integrated_analysis_tab()
        else:
            st.error("Integrated Analysis functionality is not available. Please check the installation.")

if __name__ == "__main__":
    main()