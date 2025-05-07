"""
Scaffold Generator for TerraFlow Platform

This module provides a scaffold generator that creates code templates
for common development patterns in the TerraFlow platform.
"""

import os
import json
import time
import uuid
import logging
import shutil
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Set, Tuple, Union
from string import Template

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScaffoldType(Enum):
    """Types of scaffolds that can be generated"""
    AGENT = "agent"  # AI agent scaffold
    DASHBOARD = "dashboard"  # Dashboard UI scaffold
    API = "api"  # API scaffold
    SERVICE = "service"  # Service scaffold
    WORKFLOW = "workflow"  # Workflow scaffold
    PLUGIN = "plugin"  # Plugin scaffold
    EXTENSION = "extension"  # Extension scaffold
    COMPONENT = "component"  # UI component scaffold
    MODEL = "model"  # Data model scaffold
    TEST = "test"  # Test scaffold

class LanguageType(Enum):
    """Programming languages for scaffolds"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    CSHARP = "csharp"

class ScaffoldTemplate:
    """
    A template for generating scaffolds
    
    This class represents a template for generating code scaffolds
    for a specific pattern.
    """
    
    def __init__(self, 
                template_id: str,
                name: str,
                description: str,
                scaffold_type: ScaffoldType,
                language: LanguageType,
                files: List[Dict[str, Any]],
                parameters: Dict[str, Any] = None,
                version: str = "1.0.0",
                tags: List[str] = None):
        """
        Initialize a new scaffold template
        
        Args:
            template_id: Unique identifier for this template
            name: Human-readable name
            description: Description of the template
            scaffold_type: Type of scaffold
            language: Programming language
            files: List of file templates
            parameters: Parameters for the template
            version: Template version
            tags: Template tags
        """
        self.template_id = template_id
        self.name = name
        self.description = description
        self.scaffold_type = scaffold_type
        self.language = language
        self.files = files
        self.parameters = parameters or {}
        self.version = version
        self.tags = tags or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scaffold template to dictionary for serialization"""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "scaffold_type": self.scaffold_type.value,
            "language": self.language.value,
            "files": self.files,
            "parameters": self.parameters,
            "version": self.version,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScaffoldTemplate':
        """Create scaffold template from dictionary"""
        return cls(
            template_id=data["template_id"],
            name=data["name"],
            description=data["description"],
            scaffold_type=ScaffoldType(data["scaffold_type"]),
            language=LanguageType(data["language"]),
            files=data["files"],
            parameters=data.get("parameters", {}),
            version=data.get("version", "1.0.0"),
            tags=data.get("tags", [])
        )

class ScaffoldGenerator:
    """
    Generator for code scaffolds
    
    This class generates code scaffolds from templates.
    """
    
    def __init__(self, templates_dir: str = "data/scaffold_templates"):
        """
        Initialize a new scaffold generator
        
        Args:
            templates_dir: Directory for scaffold templates
        """
        self.templates_dir = templates_dir
        self.templates = {}  # template_id -> ScaffoldTemplate
        
        # Create templates directory if it doesn't exist
        os.makedirs(templates_dir, exist_ok=True)
        
        # Load templates
        self._load_templates()
    
    def _load_templates(self):
        """Load templates from disk"""
        # Check if templates directory exists
        if not os.path.exists(self.templates_dir):
            logger.warning(f"Templates directory {self.templates_dir} does not exist")
            return
        
        # Load templates from JSON files
        for filename in os.listdir(self.templates_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.templates_dir, filename), "r") as f:
                        template_data = json.load(f)
                        template = ScaffoldTemplate.from_dict(template_data)
                        self.templates[template.template_id] = template
                        
                except Exception as e:
                    logger.error(f"Error loading template {filename}: {str(e)}")
        
        logger.info(f"Loaded {len(self.templates)} scaffold templates")
        
        # Create default templates if none exist
        if not self.templates:
            self._create_default_templates()
    
    def _save_template(self, template: ScaffoldTemplate):
        """Save template to disk"""
        template_path = os.path.join(self.templates_dir, f"{template.template_id}.json")
        
        try:
            with open(template_path, "w") as f:
                json.dump(template.to_dict(), f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving template {template.template_id}: {str(e)}")
    
    def _create_default_templates(self):
        """Create default templates"""
        # Create Python agent template
        python_agent_template = ScaffoldTemplate(
            template_id="python-agent",
            name="Python Agent",
            description="A Python-based agent for the TerraFlow platform",
            scaffold_type=ScaffoldType.AGENT,
            language=LanguageType.PYTHON,
            files=[
                {
                    "path": "$name_snake.py",
                    "content": """\"\"\"
$name Agent for TerraFlow Platform

This module provides a $name agent for the TerraFlow platform.
$description
\"\"\"

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional

from infrastructure.architecture.enhanced_agent_base import EnhancedAgent, AgentCategory, Task

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class $name_pascal(EnhancedAgent):
    \"\"\"
    $name agent for the TerraFlow platform
    
    $description
    \"\"\"
    
    def __init__(self, agent_id: str, capabilities: List[str], 
                 preferred_model: Optional[str] = None,
                 message_broker=None):
        \"\"\"
        Initialize a new $name agent
        
        Args:
            agent_id: Unique identifier for this agent
            capabilities: List of capabilities this agent provides
            preferred_model: Optional preferred AI model to use
            message_broker: Message broker for agent communication
        \"\"\"
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentCategory.$agent_category,
            capabilities=capabilities,
            preferred_model=preferred_model,
            message_broker=message_broker
        )
    
    def _get_max_concurrent_tasks(self) -> int:
        \"\"\"Get the maximum number of concurrent tasks this agent can handle\"\"\"
        return $max_tasks  # $name agent can handle $max_tasks tasks at once
    
    def _execute_task(self, task: Task) -> Dict[str, Any]:
        \"\"\"
        Execute a task assigned to this agent
        
        Args:
            task: The task to execute
            
        Returns:
            Dict[str, Any]: The result of the task execution
        \"\"\"
        capability = task.capability
        parameters = task.parameters
        
        logger.info(f"Executing task {task.task_id} with capability {capability}")
        
        # Handle different capabilities
        if capability == "capability1":
            return self._handle_capability1(parameters)
        elif capability == "capability2":
            return self._handle_capability2(parameters)
        else:
            raise ValueError(f"Unsupported capability: {capability}")
    
    def _handle_capability1(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"
        Handle capability1
        
        Args:
            parameters: Task parameters
            
        Returns:
            Dict[str, Any]: Task result
        \"\"\"
        # TODO: Implement capability1
        return {
            "success": True,
            "message": "Capability1 executed successfully",
            "result": {}
        }
    
    def _handle_capability2(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"
        Handle capability2
        
        Args:
            parameters: Task parameters
            
        Returns:
            Dict[str, Any]: Task result
        \"\"\"
        # TODO: Implement capability2
        return {
            "success": True,
            "message": "Capability2 executed successfully",
            "result": {}
        }
"""
                },
                {
                    "path": "tests/$name_snake_test.py",
                    "content": """\"\"\"
Tests for $name Agent

This module provides tests for the $name agent.
\"\"\"

import unittest
from unittest.mock import MagicMock, patch

from $name_snake import $name_pascal
from infrastructure.architecture.enhanced_agent_base import Task

class $name_pascalTest(unittest.TestCase):
    \"\"\"Tests for the $name agent\"\"\"
    
    def setUp(self):
        \"\"\"Set up test fixtures\"\"\"
        self.agent = $name_pascal(
            agent_id="test-agent",
            capabilities=["capability1", "capability2"]
        )
    
    def test_get_max_concurrent_tasks(self):
        \"\"\"Test getting maximum concurrent tasks\"\"\"
        self.assertEqual(self.agent._get_max_concurrent_tasks(), $max_tasks)
    
    def test_handle_capability1(self):
        \"\"\"Test handling capability1\"\"\"
        result = self.agent._handle_capability1({})
        self.assertTrue(result["success"])
    
    def test_handle_capability2(self):
        \"\"\"Test handling capability2\"\"\"
        result = self.agent._handle_capability2({})
        self.assertTrue(result["success"])
    
    def test_execute_task_capability1(self):
        \"\"\"Test executing a task with capability1\"\"\"
        task = Task(
            task_id="test-task",
            agent_id="test-agent",
            capability="capability1",
            parameters={}
        )
        
        result = self.agent._execute_task(task)
        self.assertTrue(result["success"])
    
    def test_execute_task_capability2(self):
        \"\"\"Test executing a task with capability2\"\"\"
        task = Task(
            task_id="test-task",
            agent_id="test-agent",
            capability="capability2",
            parameters={}
        )
        
        result = self.agent._execute_task(task)
        self.assertTrue(result["success"])
    
    def test_execute_task_unsupported_capability(self):
        \"\"\"Test executing a task with an unsupported capability\"\"\"
        task = Task(
            task_id="test-task",
            agent_id="test-agent",
            capability="unsupported",
            parameters={}
        )
        
        with self.assertRaises(ValueError):
            self.agent._execute_task(task)

if __name__ == "__main__":
    unittest.main()
"""
                },
                {
                    "path": "README.md",
                    "content": """# $name Agent

$description

## Overview

The $name agent is a specialized agent for the TerraFlow platform that provides the following capabilities:

- `capability1`: Description of capability1
- `capability2`: Description of capability2

## Usage

Here's how to use the $name agent:

```python
from $name_snake import $name_pascal

# Create an agent instance
agent = $name_pascal(
    agent_id="my-agent",
    capabilities=["capability1", "capability2"]
)

# Start the agent
agent.start()

# Stop the agent when done
agent.stop()
```

## Configuration

The $name agent supports the following configuration options:

- `preferred_model`: The preferred AI model to use for this agent

## Development

To run the tests:

```bash
python -m unittest tests.$name_snake_test
```
"""
                }
            ],
            parameters={
                "name": {
                    "description": "Name of the agent",
                    "type": "string",
                    "required": True
                },
                "description": {
                    "description": "Description of the agent",
                    "type": "string",
                    "required": True
                },
                "agent_category": {
                    "description": "Category of the agent",
                    "type": "enum",
                    "enum_values": [
                        "CODE_QUALITY",
                        "ARCHITECTURE",
                        "DATABASE",
                        "DOCUMENTATION",
                        "SECURITY",
                        "PERFORMANCE",
                        "TESTING",
                        "AGENT_READINESS",
                        "LEARNING_COORDINATOR",
                        "AI_INTEGRATION",
                        "WORKFLOW_AUTOMATION"
                    ],
                    "required": True
                },
                "max_tasks": {
                    "description": "Maximum number of concurrent tasks",
                    "type": "integer",
                    "default": 2,
                    "required": False
                }
            },
            tags=["python", "agent", "template"]
        )
        
        # Create JavaScript API template
        javascript_api_template = ScaffoldTemplate(
            template_id="javascript-api",
            name="JavaScript API",
            description="A JavaScript API for the TerraFlow platform",
            scaffold_type=ScaffoldType.API,
            language=LanguageType.JAVASCRIPT,
            files=[
                {
                    "path": "src/routes/$name_kebab.js",
                    "content": """/**
 * $name API Routes
 * 
 * $description
 */

const express = require('express');
const router = express.Router();
const $name_camel = require('../controllers/$name_camel.controller');

/**
 * @swagger
 * /$name_kebab:
 *   get:
 *     summary: Get all $name_plural
 *     description: Retrieve a list of all $name_plural
 *     responses:
 *       200:
 *         description: A list of $name_plural
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 $ref: '#/components/schemas/$name_pascal'
 */
router.get('/', $name_camel.getAll);

/**
 * @swagger
 * /$name_kebab/{id}:
 *   get:
 *     summary: Get a $name by ID
 *     description: Retrieve a $name by its ID
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *         description: ID of the $name to retrieve
 *     responses:
 *       200:
 *         description: A $name object
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/$name_pascal'
 *       404:
 *         description: $name not found
 */
router.get('/:id', $name_camel.getById);

/**
 * @swagger
 * /$name_kebab:
 *   post:
 *     summary: Create a new $name
 *     description: Create a new $name
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/$name_pascal'
 *     responses:
 *       201:
 *         description: Created $name
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/$name_pascal'
 *       400:
 *         description: Invalid input
 */
router.post('/', $name_camel.create);

/**
 * @swagger
 * /$name_kebab/{id}:
 *   put:
 *     summary: Update a $name
 *     description: Update a $name by its ID
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *         description: ID of the $name to update
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/$name_pascal'
 *     responses:
 *       200:
 *         description: Updated $name
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/$name_pascal'
 *       400:
 *         description: Invalid input
 *       404:
 *         description: $name not found
 */
router.put('/:id', $name_camel.update);

/**
 * @swagger
 * /$name_kebab/{id}:
 *   delete:
 *     summary: Delete a $name
 *     description: Delete a $name by its ID
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *         description: ID of the $name to delete
 *     responses:
 *       204:
 *         description: $name deleted
 *       404:
 *         description: $name not found
 */
router.delete('/:id', $name_camel.delete);

module.exports = router;
"""
                },
                {
                    "path": "src/controllers/$name_camel.controller.js",
                    "content": """/**
 * $name Controller
 * 
 * $description
 */

const $name_pascal = require('../models/$name_camel.model');

/**
 * Get all $name_plural
 * 
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 */
exports.getAll = async (req, res, next) => {
    try {
        const $name_plural_camel = await $name_pascal.find();
        res.status(200).json($name_plural_camel);
    } catch (error) {
        next(error);
    }
};

/**
 * Get a $name by ID
 * 
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 */
exports.getById = async (req, res, next) => {
    try {
        const $name_camel = await $name_pascal.findById(req.params.id);
        
        if (!$name_camel) {
            return res.status(404).json({ message: '$name not found' });
        }
        
        res.status(200).json($name_camel);
    } catch (error) {
        next(error);
    }
};

/**
 * Create a new $name
 * 
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 */
exports.create = async (req, res, next) => {
    try {
        const $name_camel = new $name_pascal(req.body);
        const saved$name_pascal = await $name_camel.save();
        
        res.status(201).json(saved$name_pascal);
    } catch (error) {
        next(error);
    }
};

/**
 * Update a $name
 * 
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 */
exports.update = async (req, res, next) => {
    try {
        const $name_camel = await $name_pascal.findByIdAndUpdate(
            req.params.id,
            req.body,
            { new: true, runValidators: true }
        );
        
        if (!$name_camel) {
            return res.status(404).json({ message: '$name not found' });
        }
        
        res.status(200).json($name_camel);
    } catch (error) {
        next(error);
    }
};

/**
 * Delete a $name
 * 
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 */
exports.delete = async (req, res, next) => {
    try {
        const $name_camel = await $name_pascal.findByIdAndDelete(req.params.id);
        
        if (!$name_camel) {
            return res.status(404).json({ message: '$name not found' });
        }
        
        res.status(204).send();
    } catch (error) {
        next(error);
    }
};
"""
                },
                {
                    "path": "src/models/$name_camel.model.js",
                    "content": """/**
 * $name Model
 * 
 * $description
 */

const mongoose = require('mongoose');
const Schema = mongoose.Schema;

/**
 * $name Schema
 */
const $name_pascalSchema = new Schema({
    name: {
        type: String,
        required: true,
        trim: true
    },
    description: {
        type: String,
        trim: true
    },
    // Add more fields here based on your requirements
    createdAt: {
        type: Date,
        default: Date.now
    },
    updatedAt: {
        type: Date,
        default: Date.now
    }
}, {
    timestamps: true
});

// Add any pre/post hooks or methods here
$name_pascalSchema.pre('save', function(next) {
    this.updatedAt = Date.now();
    next();
});

module.exports = mongoose.model('$name_pascal', $name_pascalSchema);
"""
                },
                {
                    "path": "test/$name_camel.test.js",
                    "content": """/**
 * Tests for $name API
 */

const request = require('supertest');
const mongoose = require('mongoose');
const app = require('../src/app');
const $name_pascal = require('../src/models/$name_camel.model');

describe('$name API', () => {
    beforeAll(async () => {
        // Connect to test database
        await mongoose.connect(process.env.MONGODB_URI_TEST, {
            useNewUrlParser: true,
            useUnifiedTopology: true
        });
    });

    afterAll(async () => {
        // Disconnect from test database
        await mongoose.connection.close();
    });

    beforeEach(async () => {
        // Clear the database before each test
        await $name_pascal.deleteMany({});
    });

    describe('GET /$name_kebab', () => {
        it('should get all $name_plural', async () => {
            // Create test data
            await $name_pascal.create({
                name: 'Test $name 1',
                description: 'Test description 1'
            });
            
            await $name_pascal.create({
                name: 'Test $name 2',
                description: 'Test description 2'
            });

            const res = await request(app).get('/$name_kebab');
            
            expect(res.statusCode).toEqual(200);
            expect(Array.isArray(res.body)).toBe(true);
            expect(res.body.length).toEqual(2);
        });
    });

    describe('GET /$name_kebab/:id', () => {
        it('should get a $name by ID', async () => {
            const $name_camel = await $name_pascal.create({
                name: 'Test $name',
                description: 'Test description'
            });

            const res = await request(app).get(`/$name_kebab/${$name_camel._id}`);
            
            expect(res.statusCode).toEqual(200);
            expect(res.body._id).toEqual($name_camel._id.toString());
            expect(res.body.name).toEqual('Test $name');
        });

        it('should return 404 if $name not found', async () => {
            const res = await request(app).get(`/$name_kebab/${new mongoose.Types.ObjectId()}`);
            
            expect(res.statusCode).toEqual(404);
        });
    });

    describe('POST /$name_kebab', () => {
        it('should create a new $name', async () => {
            const $name_camel = {
                name: 'New $name',
                description: 'New description'
            };

            const res = await request(app)
                .post('/$name_kebab')
                .send($name_camel);
            
            expect(res.statusCode).toEqual(201);
            expect(res.body.name).toEqual($name_camel.name);
            expect(res.body.description).toEqual($name_camel.description);
        });
    });

    describe('PUT /$name_kebab/:id', () => {
        it('should update a $name', async () => {
            const $name_camel = await $name_pascal.create({
                name: 'Test $name',
                description: 'Test description'
            });

            const update = {
                name: 'Updated $name',
                description: 'Updated description'
            };

            const res = await request(app)
                .put(`/$name_kebab/${$name_camel._id}`)
                .send(update);
            
            expect(res.statusCode).toEqual(200);
            expect(res.body.name).toEqual(update.name);
            expect(res.body.description).toEqual(update.description);
        });

        it('should return 404 if $name not found', async () => {
            const res = await request(app)
                .put(`/$name_kebab/${new mongoose.Types.ObjectId()}`)
                .send({
                    name: 'Updated $name',
                    description: 'Updated description'
                });
            
            expect(res.statusCode).toEqual(404);
        });
    });

    describe('DELETE /$name_kebab/:id', () => {
        it('should delete a $name', async () => {
            const $name_camel = await $name_pascal.create({
                name: 'Test $name',
                description: 'Test description'
            });

            const res = await request(app).delete(`/$name_kebab/${$name_camel._id}`);
            
            expect(res.statusCode).toEqual(204);
            
            const found = await $name_pascal.findById($name_camel._id);
            expect(found).toBeNull();
        });

        it('should return 404 if $name not found', async () => {
            const res = await request(app).delete(`/$name_kebab/${new mongoose.Types.ObjectId()}`);
            
            expect(res.statusCode).toEqual(404);
        });
    });
});
"""
                },
                {
                    "path": "README.md",
                    "content": """# $name API

$description

## Endpoints

The API provides the following endpoints:

- `GET /$name_kebab` - Get all $name_plural
- `GET /$name_kebab/:id` - Get a $name by ID
- `POST /$name_kebab` - Create a new $name
- `PUT /$name_kebab/:id` - Update a $name
- `DELETE /$name_kebab/:id` - Delete a $name

## Model

The $name model has the following schema:

```javascript
{
    name: String,          // Required
    description: String,
    createdAt: Date,
    updatedAt: Date
}
```

## Usage

Here's an example of how to use the API:

```javascript
// Get all $name_plural
fetch('/$name_kebab')
    .then(response => response.json())
    .then(data => console.log(data));

// Get a $name by ID
fetch('/$name_kebab/123')
    .then(response => response.json())
    .then(data => console.log(data));

// Create a new $name
fetch('/$name_kebab', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        name: 'New $name',
        description: 'New description'
    })
})
    .then(response => response.json())
    .then(data => console.log(data));

// Update a $name
fetch('/$name_kebab/123', {
    method: 'PUT',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        name: 'Updated $name',
        description: 'Updated description'
    })
})
    .then(response => response.json())
    .then(data => console.log(data));

// Delete a $name
fetch('/$name_kebab/123', {
    method: 'DELETE'
})
    .then(response => console.log(response.status));
```
"""
                }
            ],
            parameters={
                "name": {
                    "description": "Name of the API resource (singular)",
                    "type": "string",
                    "required": True
                },
                "name_plural": {
                    "description": "Plural form of the API resource name",
                    "type": "string",
                    "required": True
                },
                "description": {
                    "description": "Description of the API",
                    "type": "string",
                    "required": True
                }
            },
            tags=["javascript", "api", "express", "template"]
        )
        
        # Create Streamlit dashboard template
        streamlit_dashboard_template = ScaffoldTemplate(
            template_id="streamlit-dashboard",
            name="Streamlit Dashboard",
            description="A Streamlit dashboard for the TerraFlow platform",
            scaffold_type=ScaffoldType.DASHBOARD,
            language=LanguageType.PYTHON,
            files=[
                {
                    "path": "pages/$order_$name_snake.py",
                    "content": """\"\"\"
$name Dashboard for TerraFlow Platform

$description
\"\"\"

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import time
import json
import os

# Set page config
st.set_page_config(
    page_title="$name",
    page_icon="$icon",
    layout="wide"
)

# Apply custom styling
st.markdown('''
<style>
    .main-header {
        color: #0f6cbd;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0;
    }
    .sub-header {
        color: #666;
        font-weight: 500;
        font-size: 1.5rem;
        margin-top: 0;
    }
    .card {
        border-radius: 10px;
        padding: 20px;
        background-color: #f8f9fa;
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .metric-card {
        text-align: center;
        padding: 15px 10px;
        border-radius: 5px;
        background-color: #ffffff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        margin: 0;
    }
    hr {
        margin-top: 0;
    }
</style>
''', unsafe_allow_html=True)

# Helper functions
def load_data():
    \"\"\"
    Load or generate sample data for the dashboard
    
    In a real implementation, this would load actual data from a database or API
    \"\"\"
    # Sample data generation
    n_rows = 100
    
    # Generate dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
    
    # Generate random data
    data = {
        'date': np.random.choice(dates, n_rows),
        'value': np.random.normal(100, 20, n_rows),
        'category': np.random.choice(['A', 'B', 'C'], n_rows),
        'group': np.random.choice(['Group 1', 'Group 2', 'Group 3'], n_rows),
        'status': np.random.choice(['Completed', 'In Progress', 'Failed'], n_rows, p=[0.7, 0.2, 0.1])
    }
    
    return pd.DataFrame(data)

def create_time_series_chart(df):
    \"\"\"Create a time series chart\"\"\"
    # Group by date and calculate mean
    df_grouped = df.groupby('date')['value'].mean().reset_index()
    
    # Create line chart
    fig = px.line(
        df_grouped, 
        x='date', 
        y='value',
        title='Time Series',
        labels={'date': 'Date', 'value': 'Value'}
    )
    
    # Customize layout
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        title_x=0.5,
        title_font_size=16
    )
    
    return fig

def create_category_chart(df):
    \"\"\"Create a chart by category\"\"\"
    # Group by category
    df_grouped = df.groupby('category')['value'].mean().reset_index()
    
    # Create bar chart
    fig = px.bar(
        df_grouped,
        x='category',
        y='value',
        title='Average by Category',
        labels={'category': 'Category', 'value': 'Average Value'},
        color='category'
    )
    
    # Customize layout
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        title_x=0.5,
        title_font_size=16
    )
    
    return fig

def create_status_chart(df):
    \"\"\"Create a chart by status\"\"\"
    # Count by status
    status_counts = df['status'].value_counts().reset_index()
    status_counts.columns = ['status', 'count']
    
    # Create pie chart
    fig = px.pie(
        status_counts,
        values='count',
        names='status',
        title='Status Distribution',
        color='status',
        color_discrete_map={
            'Completed': '#4CAF50',
            'In Progress': '#2196F3',
            'Failed': '#F44336'
        }
    )
    
    # Customize layout
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        title_x=0.5,
        title_font_size=16
    )
    
    return fig

def create_group_chart(df):
    \"\"\"Create a chart by group\"\"\"
    # Group by group and category
    df_grouped = df.groupby(['group', 'category'])['value'].mean().reset_index()
    
    # Create grouped bar chart
    fig = px.bar(
        df_grouped,
        x='group',
        y='value',
        color='category',
        barmode='group',
        title='Average by Group and Category',
        labels={'group': 'Group', 'value': 'Average Value', 'category': 'Category'}
    )
    
    # Customize layout
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        title_x=0.5,
        title_font_size=16
    )
    
    return fig

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = load_data()

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()

# Page header
st.markdown('<h1 class="main-header">$name Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">$description</p>', unsafe_allow_html=True)
st.markdown('---')

# Sidebar
with st.sidebar:
    st.title("$name")
    
    # Date filter
    st.subheader("Date Range")
    min_date = st.session_state.data['date'].min()
    max_date = st.session_state.data['date'].max()
    
    start_date = st.date_input(
        "Start Date",
        value=min_date,
        min_value=min_date,
        max_value=max_date
    )
    
    end_date = st.date_input(
        "End Date",
        value=max_date,
        min_value=start_date,
        max_value=max_date
    )
    
    # Category filter
    st.subheader("Filters")
    categories = st.multiselect(
        "Categories",
        options=sorted(st.session_state.data['category'].unique()),
        default=sorted(st.session_state.data['category'].unique())
    )
    
    groups = st.multiselect(
        "Groups",
        options=sorted(st.session_state.data['group'].unique()),
        default=sorted(st.session_state.data['group'].unique())
    )
    
    statuses = st.multiselect(
        "Statuses",
        options=sorted(st.session_state.data['status'].unique()),
        default=sorted(st.session_state.data['status'].unique())
    )
    
    # Refresh button
    if st.button("Refresh Data"):
        st.session_state.data = load_data()
        st.session_state.last_refresh = datetime.now()
        st.success("Data refreshed successfully!")
    
    st.caption(f"Last refreshed: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")

# Filter data based on selections
filtered_data = st.session_state.data.copy()

# Date filter
filtered_data = filtered_data[(filtered_data['date'].dt.date >= pd.Timestamp(start_date).date()) & 
                             (filtered_data['date'].dt.date <= pd.Timestamp(end_date).date())]

# Category, group, and status filters
filtered_data = filtered_data[filtered_data['category'].isin(categories)]
filtered_data = filtered_data[filtered_data['group'].isin(groups)]
filtered_data = filtered_data[filtered_data['status'].isin(statuses)]

# Overview metrics
st.subheader("Overview")

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

with metric_col1:
    value_avg = filtered_data['value'].mean()
    value_diff = value_avg - st.session_state.data['value'].mean()
    
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-value">{value_avg:.2f}</p>', unsafe_allow_html=True)
    st.markdown('<p class="metric-label">Average Value</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with metric_col2:
    count = len(filtered_data)
    total = len(st.session_state.data)
    percentage = (count / total) * 100 if total > 0 else 0
    
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-value">{count}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-label">Items ({percentage:.1f}%)</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with metric_col3:
    completed_count = filtered_data[filtered_data['status'] == 'Completed'].shape[0]
    completion_rate = (completed_count / count) * 100 if count > 0 else 0
    
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-value">{completion_rate:.1f}%</p>', unsafe_allow_html=True)
    st.markdown('<p class="metric-label">Completion Rate</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with metric_col4:
    failed_count = filtered_data[filtered_data['status'] == 'Failed'].shape[0]
    failure_rate = (failed_count / count) * 100 if count > 0 else 0
    
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-value">{failure_rate:.1f}%</p>', unsafe_allow_html=True)
    st.markdown('<p class="metric-label">Failure Rate</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Charts
st.subheader("Analysis")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    # Time series chart
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.plotly_chart(create_time_series_chart(filtered_data), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Group chart
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.plotly_chart(create_group_chart(filtered_data), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with chart_col2:
    # Category chart
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.plotly_chart(create_category_chart(filtered_data), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Status chart
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.plotly_chart(create_status_chart(filtered_data), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Data table
st.subheader("Data")

show_data = st.checkbox("Show Raw Data")
if show_data:
    st.dataframe(filtered_data)
"""
                },
                {
                    "path": "README.md",
                    "content": """# $name Dashboard

$description

## Overview

This dashboard provides visualization and analysis of $name data. It includes:

- Time series analysis
- Category breakdowns
- Status distribution
- Group comparisons

## Features

- Interactive filters for date range, categories, groups, and status
- Overview metrics with key indicators
- Multiple visualization types (line charts, bar charts, pie charts)
- Raw data table

## Usage

To run the dashboard:

```bash
streamlit run pages/$order_$name_snake.py
```

The dashboard will be available at http://localhost:5000

## Customization

To customize the dashboard:

1. Modify the `load_data()` function to use your own data source
2. Adjust the filters in the sidebar to match your data structure
3. Customize the charts in the chart creation functions
4. Update the metrics in the "Overview" section

## Dependencies

- streamlit
- pandas
- numpy
- plotly
"""
                }
            ],
            parameters={
                "name": {
                    "description": "Name of the dashboard",
                    "type": "string",
                    "required": True
                },
                "description": {
                    "description": "Description of the dashboard",
                    "type": "string",
                    "required": True
                },
                "order": {
                    "description": "Order number for the dashboard page",
                    "type": "integer",
                    "default": 1,
                    "required": False
                },
                "icon": {
                    "description": "Icon for the dashboard",
                    "type": "string",
                    "default": "📊",
                    "required": False
                }
            },
            tags=["python", "dashboard", "streamlit", "template"]
        )
        
        # Register the templates
        self.templates[python_agent_template.template_id] = python_agent_template
        self._save_template(python_agent_template)
        
        self.templates[javascript_api_template.template_id] = javascript_api_template
        self._save_template(javascript_api_template)
        
        self.templates[streamlit_dashboard_template.template_id] = streamlit_dashboard_template
        self._save_template(streamlit_dashboard_template)
        
        logger.info(f"Created {len(self.templates)} default templates")
    
    def register_template(self, template: ScaffoldTemplate) -> bool:
        """
        Register a new scaffold template
        
        Args:
            template: The template to register
            
        Returns:
            bool: True if the template was registered, False if a template with the same ID already exists
        """
        if template.template_id in self.templates:
            logger.warning(f"Template with ID {template.template_id} already exists")
            return False
        
        self.templates[template.template_id] = template
        self._save_template(template)
        
        logger.info(f"Registered template {template.template_id}")
        return True
    
    def get_template(self, template_id: str) -> Optional[ScaffoldTemplate]:
        """
        Get a template by ID
        
        Args:
            template_id: ID of the template to get
            
        Returns:
            Optional[ScaffoldTemplate]: The template, or None if not found
        """
        return self.templates.get(template_id)
    
    def get_templates_by_type(self, scaffold_type: ScaffoldType) -> List[ScaffoldTemplate]:
        """
        Get templates by type
        
        Args:
            scaffold_type: Type of templates to get
            
        Returns:
            List[ScaffoldTemplate]: List of templates of the specified type
        """
        return [t for t in self.templates.values() if t.scaffold_type == scaffold_type]
    
    def get_templates_by_language(self, language: LanguageType) -> List[ScaffoldTemplate]:
        """
        Get templates by language
        
        Args:
            language: Language of templates to get
            
        Returns:
            List[ScaffoldTemplate]: List of templates in the specified language
        """
        return [t for t in self.templates.values() if t.language == language]
    
    def get_templates_by_tag(self, tag: str) -> List[ScaffoldTemplate]:
        """
        Get templates by tag
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List[ScaffoldTemplate]: List of templates with the specified tag
        """
        return [t for t in self.templates.values() if tag in t.tags]
    
    def get_all_templates(self) -> List[ScaffoldTemplate]:
        """
        Get all templates
        
        Returns:
            List[ScaffoldTemplate]: List of all templates
        """
        return list(self.templates.values())
    
    def generate_scaffold(self, template_id: str, output_dir: str, parameters: Dict[str, Any],
                        overwrite: bool = False) -> bool:
        """
        Generate a scaffold from a template
        
        Args:
            template_id: ID of the template to use
            output_dir: Directory to output the generated scaffold
            parameters: Parameters for the template
            overwrite: Whether to overwrite existing files
            
        Returns:
            bool: True if the scaffold was generated successfully, False otherwise
        """
        # Get the template
        template = self.get_template(template_id)
        
        if not template:
            logger.error(f"Template {template_id} not found")
            return False
        
        # Validate parameters
        for param_name, param_info in template.parameters.items():
            if param_info.get("required", False) and param_name not in parameters:
                logger.error(f"Required parameter {param_name} not provided")
                return False
            
            if param_name not in parameters and "default" in param_info:
                parameters[param_name] = param_info["default"]
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate files
        for file_template in template.files:
            # Process file path with parameters
            file_path = file_template["path"]
            for param_name, param_value in parameters.items():
                
                # Handle special transformations
                if f"${param_name}_snake" in file_path:
                    snake_value = self._to_snake_case(param_value)
                    file_path = file_path.replace(f"${param_name}_snake", snake_value)
                
                elif f"${param_name}_kebab" in file_path:
                    kebab_value = self._to_kebab_case(param_value)
                    file_path = file_path.replace(f"${param_name}_kebab", kebab_value)
                
                elif f"${param_name}_camel" in file_path:
                    camel_value = self._to_camel_case(param_value)
                    file_path = file_path.replace(f"${param_name}_camel", camel_value)
                
                elif f"${param_name}_pascal" in file_path:
                    pascal_value = self._to_pascal_case(param_value)
                    file_path = file_path.replace(f"${param_name}_pascal", pascal_value)
                
                else:
                    file_path = file_path.replace(f"${param_name}", str(param_value))
            
            # Process file content with parameters
            content = file_template["content"]
            
            # Create a dictionary with all case variations of each parameter
            template_params = {}
            for param_name, param_value in parameters.items():
                if isinstance(param_value, str):
                    template_params[param_name] = param_value
                    template_params[f"{param_name}_snake"] = self._to_snake_case(param_value)
                    template_params[f"{param_name}_kebab"] = self._to_kebab_case(param_value)
                    template_params[f"{param_name}_camel"] = self._to_camel_case(param_value)
                    template_params[f"{param_name}_pascal"] = self._to_pascal_case(param_value)
                else:
                    template_params[param_name] = param_value
            
            # Apply template substitution
            content_template = Template(content)
            rendered_content = content_template.safe_substitute(template_params)
            
            # Ensure the output directory for this file exists
            file_dir = os.path.dirname(os.path.join(output_dir, file_path))
            os.makedirs(file_dir, exist_ok=True)
            
            # Check if file exists and we're not overwriting
            full_path = os.path.join(output_dir, file_path)
            if os.path.exists(full_path) and not overwrite:
                logger.warning(f"File {full_path} already exists, skipping (use overwrite=True to overwrite)")
                continue
            
            # Write the file
            with open(full_path, "w") as f:
                f.write(rendered_content)
            
            logger.info(f"Generated file {full_path}")
        
        return True
    
    def _to_snake_case(self, s: str) -> str:
        """Convert string to snake_case"""
        # Replace spaces and hyphens with underscores
        s = s.replace(" ", "_").replace("-", "_")
        
        # Insert underscores between lowercase and uppercase letters
        import re
        s = re.sub(r'([a-z])([A-Z])', r'\1_\2', s)
        
        # Convert to lowercase
        return s.lower()
    
    def _to_kebab_case(self, s: str) -> str:
        """Convert string to kebab-case"""
        # First convert to snake case
        snake = self._to_snake_case(s)
        
        # Replace underscores with hyphens
        return snake.replace("_", "-")
    
    def _to_camel_case(self, s: str) -> str:
        """Convert string to camelCase"""
        # First convert to snake case
        snake = self._to_snake_case(s)
        
        # Split by underscore and join with title case for all but the first word
        words = snake.split("_")
        return words[0] + "".join(word.title() for word in words[1:])
    
    def _to_pascal_case(self, s: str) -> str:
        """Convert string to PascalCase"""
        # First convert to snake case
        snake = self._to_snake_case(s)
        
        # Split by underscore and join with title case
        words = snake.split("_")
        return "".join(word.title() for word in words)

# Example usage function
def create_example_scaffold(scaffold_type: str, output_dir: str, parameters: Dict[str, Any]) -> bool:
    """
    Create an example scaffold
    
    Args:
        scaffold_type: Type of scaffold to create (agent, api, dashboard)
        output_dir: Directory to output the generated scaffold
        parameters: Parameters for the template
        
    Returns:
        bool: True if the scaffold was generated successfully, False otherwise
    """
    # Initialize generator
    generator = ScaffoldGenerator()
    
    # Map scaffold type to template ID
    template_id_map = {
        "agent": "python-agent",
        "api": "javascript-api",
        "dashboard": "streamlit-dashboard"
    }
    
    if scaffold_type not in template_id_map:
        logger.error(f"Unsupported scaffold type: {scaffold_type}")
        return False
    
    template_id = template_id_map[scaffold_type]
    
    # Generate scaffold
    return generator.generate_scaffold(template_id, output_dir, parameters)