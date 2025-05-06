import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import networkx as nx
import json
import os
import re
import time
import random
from datetime import datetime
import uuid
import zipfile
import io
from collections import defaultdict

# Set page configuration
st.set_page_config(page_title="Repository Analysis", page_icon="📂", layout="wide")

# Define custom CSS
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 16px;
        background-color: #111;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #0E53A7 !important;
    }
    
    /* Repository card styling */
    .repo-card {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #333;
    }
    
    .repo-title {
        color: #4C9AFF;
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    .repo-desc {
        color: #CCC;
        font-size: 14px;
        margin-bottom: 15px;
    }
    
    .repo-meta {
        display: flex;
        justify-content: space-between;
        color: #999;
        font-size: 12px;
    }
    
    /* Metrics styling */
    .metric-container {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        height: 100%;
    }
    
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        margin: 10px 0;
    }
    
    .metric-label {
        font-size: 14px;
        color: #AAA;
    }
    
    .good {
        color: #4CAF50;
    }
    
    .average {
        color: #FFC107;
    }
    
    .poor {
        color: #F44336;
    }
    
    /* Summary box */
    .summary-box {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 15px;
        border-left: 4px solid #4C9AFF;
        margin-bottom: 20px;
    }
    
    .summary-title {
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 10px;
        color: #4C9AFF;
    }
    
    /* Issue/recommendation box */
    .issue-box {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 4px solid #F44336;
    }
    
    .strength-box {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 4px solid #4CAF50;
    }
    
    .weakness-box {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 4px solid #FFC107;
    }
    
    .recommendation-box {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 4px solid #4C9AFF;
    }
    
    .issue-title {
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    
    .critical {
        color: #F44336;
    }
    
    .high {
        color: #FF9800;
    }
    
    .medium {
        color: #FFC107;
    }
    
    .low {
        color: #4CAF50;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    
    .badge-critical {
        background-color: rgba(244, 67, 54, 0.2);
        color: #F44336;
        border: 1px solid rgba(244, 67, 54, 0.4);
    }
    
    .badge-high {
        background-color: rgba(255, 152, 0, 0.2);
        color: #FF9800;
        border: 1px solid rgba(255, 152, 0, 0.4);
    }
    
    .badge-medium {
        background-color: rgba(255, 193, 7, 0.2);
        color: #FFC107;
        border: 1px solid rgba(255, 193, 7, 0.4);
    }
    
    .badge-low {
        background-color: rgba(76, 175, 80, 0.2);
        color: #4CAF50;
        border: 1px solid rgba(76, 175, 80, 0.4);
    }
    
    .badge-info {
        background-color: rgba(76, 154, 255, 0.2);
        color: #4C9AFF;
        border: 1px solid rgba(76, 154, 255, 0.4);
    }
    
    /* File browser */
    .file-item {
        padding: 8px 15px;
        border-radius: 5px;
        cursor: pointer;
        transition: background-color 0.2s;
        margin-bottom: 5px;
    }
    
    .file-item:hover {
        background-color: #333;
    }
    
    .file-item.selected {
        background-color: #0E53A7;
    }
    
    .file-name {
        font-size: 14px;
        color: #CCC;
    }
    
    .directory {
        color: #4C9AFF;
        font-weight: bold;
    }
    
    .file-meta {
        font-size: 12px;
        color: #999;
    }
    
    /* Divider */
    .divider {
        height: 1px;
        background-color: #333;
        margin: 20px 0;
    }
    
    /* Progress bar */
    .progress-container {
        width: 100%;
        background-color: #222;
        border-radius: 5px;
        margin: 10px 0;
        height: 8px;
    }
    
    .progress-bar {
        height: 100%;
        border-radius: 5px;
    }
    
    .progress-good {
        background-color: #4CAF50;
    }
    
    .progress-average {
        background-color: #FFC107;
    }
    
    .progress-poor {
        background-color: #F44336;
    }
</style>
""", unsafe_allow_html=True)

# Hardcoded sample repositories
sample_repositories = {
    "nodejs-express-api": {
        "name": "Node.js Express API",
        "description": "A RESTful API built with Express.js and Node.js",
        "language": "JavaScript",
        "files": 12,
        "loc": 1450,
        "structure": {
            "src": {
                "controllers": {
                    "userController.js": {
                        "language": "JavaScript",
                        "loc": 120,
                        "complexity": 8
                    },
                    "authController.js": {
                        "language": "JavaScript",
                        "loc": 150,
                        "complexity": 9
                    },
                    "productController.js": {
                        "language": "JavaScript",
                        "loc": 185,
                        "complexity": 10
                    }
                },
                "models": {
                    "userModel.js": {
                        "language": "JavaScript",
                        "loc": 85,
                        "complexity": 5
                    },
                    "productModel.js": {
                        "language": "JavaScript",
                        "loc": 95,
                        "complexity": 6
                    }
                },
                "middleware": {
                    "authMiddleware.js": {
                        "language": "JavaScript",
                        "loc": 75,
                        "complexity": 7
                    },
                    "errorHandler.js": {
                        "language": "JavaScript",
                        "loc": 60,
                        "complexity": 6
                    }
                },
                "routes": {
                    "userRoutes.js": {
                        "language": "JavaScript",
                        "loc": 45,
                        "complexity": 4
                    },
                    "authRoutes.js": {
                        "language": "JavaScript",
                        "loc": 35,
                        "complexity": 3
                    },
                    "productRoutes.js": {
                        "language": "JavaScript",
                        "loc": 50,
                        "complexity": 4
                    }
                },
                "utils": {
                    "logger.js": {
                        "language": "JavaScript",
                        "loc": 40,
                        "complexity": 3
                    },
                    "validators.js": {
                        "language": "JavaScript",
                        "loc": 65,
                        "complexity": 5
                    }
                },
                "app.js": {
                    "language": "JavaScript",
                    "loc": 95,
                    "complexity": 6
                },
                "server.js": {
                    "language": "JavaScript",
                    "loc": 45,
                    "complexity": 4
                }
            },
            "tests": {
                "unit": {
                    "userController.test.js": {
                        "language": "JavaScript",
                        "loc": 85,
                        "complexity": 5
                    },
                    "authController.test.js": {
                        "language": "JavaScript",
                        "loc": 95,
                        "complexity": 6
                    }
                },
                "integration": {
                    "auth.test.js": {
                        "language": "JavaScript",
                        "loc": 110,
                        "complexity": 7
                    },
                    "products.test.js": {
                        "language": "JavaScript",
                        "loc": 130,
                        "complexity": 8
                    }
                }
            },
            "package.json": {
                "language": "JSON",
                "loc": 35,
                "complexity": 1
            },
            "README.md": {
                "language": "Markdown",
                "loc": 85,
                "complexity": 1
            }
        }
    },
    "django-web-app": {
        "name": "Django Web Application",
        "description": "A web application built with Django framework",
        "language": "Python",
        "files": 18,
        "loc": 2250,
        "structure": {
            "myproject": {
                "settings.py": {
                    "language": "Python",
                    "loc": 120,
                    "complexity": 5
                },
                "urls.py": {
                    "language": "Python",
                    "loc": 45,
                    "complexity": 3
                },
                "wsgi.py": {
                    "language": "Python",
                    "loc": 25,
                    "complexity": 2
                },
                "asgi.py": {
                    "language": "Python",
                    "loc": 25,
                    "complexity": 2
                }
            },
            "apps": {
                "users": {
                    "models.py": {
                        "language": "Python",
                        "loc": 95,
                        "complexity": 6
                    },
                    "views.py": {
                        "language": "Python",
                        "loc": 185,
                        "complexity": 10
                    },
                    "forms.py": {
                        "language": "Python",
                        "loc": 75,
                        "complexity": 5
                    },
                    "urls.py": {
                        "language": "Python",
                        "loc": 35,
                        "complexity": 3
                    },
                    "admin.py": {
                        "language": "Python",
                        "loc": 45,
                        "complexity": 4
                    },
                    "tests.py": {
                        "language": "Python",
                        "loc": 110,
                        "complexity": 7
                    }
                },
                "dashboard": {
                    "models.py": {
                        "language": "Python",
                        "loc": 85,
                        "complexity": 6
                    },
                    "views.py": {
                        "language": "Python",
                        "loc": 175,
                        "complexity": 9
                    },
                    "forms.py": {
                        "language": "Python",
                        "loc": 65,
                        "complexity": 5
                    },
                    "urls.py": {
                        "language": "Python",
                        "loc": 30,
                        "complexity": 3
                    },
                    "admin.py": {
                        "language": "Python",
                        "loc": 40,
                        "complexity": 4
                    },
                    "tests.py": {
                        "language": "Python",
                        "loc": 95,
                        "complexity": 6
                    }
                }
            },
            "templates": {
                "base.html": {
                    "language": "HTML",
                    "loc": 85,
                    "complexity": 4
                },
                "users": {
                    "login.html": {
                        "language": "HTML",
                        "loc": 65,
                        "complexity": 3
                    },
                    "profile.html": {
                        "language": "HTML",
                        "loc": 75,
                        "complexity": 4
                    },
                    "register.html": {
                        "language": "HTML",
                        "loc": 70,
                        "complexity": 3
                    }
                },
                "dashboard": {
                    "index.html": {
                        "language": "HTML",
                        "loc": 95,
                        "complexity": 5
                    },
                    "details.html": {
                        "language": "HTML",
                        "loc": 85,
                        "complexity": 4
                    }
                }
            },
            "static": {
                "css": {
                    "main.css": {
                        "language": "CSS",
                        "loc": 150,
                        "complexity": 5
                    }
                },
                "js": {
                    "main.js": {
                        "language": "JavaScript",
                        "loc": 120,
                        "complexity": 6
                    },
                    "dashboard.js": {
                        "language": "JavaScript",
                        "loc": 135,
                        "complexity": 7
                    }
                }
            },
            "requirements.txt": {
                "language": "Text",
                "loc": 25,
                "complexity": 1
            },
            "manage.py": {
                "language": "Python",
                "loc": 20,
                "complexity": 2
            },
            "README.md": {
                "language": "Markdown",
                "loc": 95,
                "complexity": 1
            }
        }
    },
    "flutter-mobile-app": {
        "name": "Flutter Mobile App",
        "description": "A cross-platform mobile application built with Flutter",
        "language": "Dart",
        "files": 22,
        "loc": 2850,
        "structure": {
            "lib": {
                "main.dart": {
                    "language": "Dart",
                    "loc": 75,
                    "complexity": 5
                },
                "screens": {
                    "home_screen.dart": {
                        "language": "Dart",
                        "loc": 185,
                        "complexity": 8
                    },
                    "login_screen.dart": {
                        "language": "Dart",
                        "loc": 165,
                        "complexity": 7
                    },
                    "profile_screen.dart": {
                        "language": "Dart",
                        "loc": 175,
                        "complexity": 7
                    },
                    "settings_screen.dart": {
                        "language": "Dart",
                        "loc": 155,
                        "complexity": 6
                    },
                    "detail_screen.dart": {
                        "language": "Dart",
                        "loc": 145,
                        "complexity": 6
                    }
                },
                "widgets": {
                    "custom_button.dart": {
                        "language": "Dart",
                        "loc": 85,
                        "complexity": 4
                    },
                    "custom_text_field.dart": {
                        "language": "Dart",
                        "loc": 95,
                        "complexity": 5
                    },
                    "item_card.dart": {
                        "language": "Dart",
                        "loc": 110,
                        "complexity": 5
                    },
                    "loading_indicator.dart": {
                        "language": "Dart",
                        "loc": 45,
                        "complexity": 3
                    }
                },
                "models": {
                    "user_model.dart": {
                        "language": "Dart",
                        "loc": 65,
                        "complexity": 3
                    },
                    "item_model.dart": {
                        "language": "Dart",
                        "loc": 55,
                        "complexity": 3
                    },
                    "settings_model.dart": {
                        "language": "Dart",
                        "loc": 45,
                        "complexity": 2
                    }
                },
                "services": {
                    "api_service.dart": {
                        "language": "Dart",
                        "loc": 145,
                        "complexity": 8
                    },
                    "auth_service.dart": {
                        "language": "Dart",
                        "loc": 165,
                        "complexity": 9
                    },
                    "storage_service.dart": {
                        "language": "Dart",
                        "loc": 125,
                        "complexity": 7
                    }
                },
                "utils": {
                    "constants.dart": {
                        "language": "Dart",
                        "loc": 35,
                        "complexity": 1
                    },
                    "theme.dart": {
                        "language": "Dart",
                        "loc": 95,
                        "complexity": 4
                    },
                    "validators.dart": {
                        "language": "Dart",
                        "loc": 85,
                        "complexity": 5
                    }
                }
            },
            "test": {
                "widget_test.dart": {
                    "language": "Dart",
                    "loc": 75,
                    "complexity": 4
                },
                "unit_tests": {
                    "auth_test.dart": {
                        "language": "Dart",
                        "loc": 110,
                        "complexity": 6
                    },
                    "api_test.dart": {
                        "language": "Dart",
                        "loc": 130,
                        "complexity": 7
                    }
                }
            },
            "pubspec.yaml": {
                "language": "YAML",
                "loc": 85,
                "complexity": 3
            },
            "README.md": {
                "language": "Markdown",
                "loc": 120,
                "complexity": 1
            }
        }
    },
    "spring-boot-microservice": {
        "name": "Spring Boot Microservice",
        "description": "A microservice built with Spring Boot",
        "language": "Java",
        "files": 25,
        "loc": 3150,
        "structure": {
            "src": {
                "main": {
                    "java": {
                        "com": {
                            "example": {
                                "microservice": {
                                    "controllers": {
                                        "UserController.java": {
                                            "language": "Java",
                                            "loc": 185,
                                            "complexity": 9
                                        },
                                        "ProductController.java": {
                                            "language": "Java",
                                            "loc": 175,
                                            "complexity": 8
                                        },
                                        "OrderController.java": {
                                            "language": "Java",
                                            "loc": 195,
                                            "complexity": 10
                                        }
                                    },
                                    "services": {
                                        "UserService.java": {
                                            "language": "Java",
                                            "loc": 145,
                                            "complexity": 8
                                        },
                                        "ProductService.java": {
                                            "language": "Java",
                                            "loc": 135,
                                            "complexity": 7
                                        },
                                        "OrderService.java": {
                                            "language": "Java",
                                            "loc": 165,
                                            "complexity": 9
                                        }
                                    },
                                    "repositories": {
                                        "UserRepository.java": {
                                            "language": "Java",
                                            "loc": 45,
                                            "complexity": 3
                                        },
                                        "ProductRepository.java": {
                                            "language": "Java",
                                            "loc": 40,
                                            "complexity": 3
                                        },
                                        "OrderRepository.java": {
                                            "language": "Java",
                                            "loc": 50,
                                            "complexity": 4
                                        }
                                    },
                                    "models": {
                                        "User.java": {
                                            "language": "Java",
                                            "loc": 85,
                                            "complexity": 4
                                        },
                                        "Product.java": {
                                            "language": "Java",
                                            "loc": 75,
                                            "complexity": 4
                                        },
                                        "Order.java": {
                                            "language": "Java",
                                            "loc": 95,
                                            "complexity": 5
                                        }
                                    },
                                    "exceptions": {
                                        "ResourceNotFoundException.java": {
                                            "language": "Java",
                                            "loc": 35,
                                            "complexity": 2
                                        },
                                        "BadRequestException.java": {
                                            "language": "Java",
                                            "loc": 30,
                                            "complexity": 2
                                        }
                                    },
                                    "config": {
                                        "SecurityConfig.java": {
                                            "language": "Java",
                                            "loc": 110,
                                            "complexity": 6
                                        },
                                        "SwaggerConfig.java": {
                                            "language": "Java",
                                            "loc": 65,
                                            "complexity": 4
                                        }
                                    },
                                    "utils": {
                                        "Constants.java": {
                                            "language": "Java",
                                            "loc": 25,
                                            "complexity": 1
                                        },
                                        "DateUtils.java": {
                                            "language": "Java",
                                            "loc": 45,
                                            "complexity": 3
                                        }
                                    },
                                    "Application.java": {
                                        "language": "Java",
                                        "loc": 35,
                                        "complexity": 2
                                    }
                                }
                            }
                        }
                    },
                    "resources": {
                        "application.properties": {
                            "language": "Properties",
                            "loc": 45,
                            "complexity": 2
                        },
                        "application-dev.properties": {
                            "language": "Properties",
                            "loc": 55,
                            "complexity": 2
                        },
                        "application-prod.properties": {
                            "language": "Properties",
                            "loc": 50,
                            "complexity": 2
                        }
                    }
                },
                "test": {
                    "java": {
                        "com": {
                            "example": {
                                "microservice": {
                                    "controllers": {
                                        "UserControllerTest.java": {
                                            "language": "Java",
                                            "loc": 175,
                                            "complexity": 8
                                        },
                                        "ProductControllerTest.java": {
                                            "language": "Java",
                                            "loc": 165,
                                            "complexity": 7
                                        }
                                    },
                                    "services": {
                                        "UserServiceTest.java": {
                                            "language": "Java",
                                            "loc": 145,
                                            "complexity": 7
                                        },
                                        "ProductServiceTest.java": {
                                            "language": "Java",
                                            "loc": 135,
                                            "complexity": 6
                                        }
                                    },
                                    "integration": {
                                        "ApiIntegrationTest.java": {
                                            "language": "Java",
                                            "loc": 195,
                                            "complexity": 9
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "pom.xml": {
                "language": "XML",
                "loc": 95,
                "complexity": 3
            },
            "README.md": {
                "language": "Markdown",
                "loc": 110,
                "complexity": 1
            }
        }
    }
}

# Sample file contents
sample_file_contents = {
    "nodejs-express-api": {
        "src/app.js": """const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const helmet = require('helmet');
const errorHandler = require('./middleware/errorHandler');
const userRoutes = require('./routes/userRoutes');
const authRoutes = require('./routes/authRoutes');
const productRoutes = require('./routes/productRoutes');

// Initialize express app
const app = express();

// Apply middleware
app.use(helmet()); // Security headers
app.use(cors()); // Enable CORS
app.use(morgan('dev')); // Request logging
app.use(express.json()); // Parse JSON bodies

// API routes
app.use('/api/users', userRoutes);
app.use('/api/auth', authRoutes);
app.use('/api/products', productRoutes);

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'UP', timestamp: new Date() });
});

// Not found handler
app.use((req, res, next) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Route ${req.method} ${req.url} not found`,
    path: req.url,
    timestamp: new Date()
  });
});

// Global error handler
app.use(errorHandler);

module.exports = app;
""",
        "src/controllers/userController.js": """const UserModel = require('../models/userModel');
const logger = require('../utils/logger');
const validators = require('../utils/validators');

/**
 * Get all users with pagination
 */
exports.getUsers = async (req, res, next) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    const skip = (page - 1) * limit;
    
    const users = await UserModel.find()
      .select('-password')
      .skip(skip)
      .limit(limit);
      
    const total = await UserModel.countDocuments();
    
    logger.info(`Retrieved ${users.length} users`);
    
    res.status(200).json({
      success: true,
      count: users.length,
      pagination: {
        total,
        page,
        pages: Math.ceil(total / limit)
      },
      data: users
    });
  } catch (error) {
    logger.error(`Error retrieving users: ${error.message}`);
    next(error);
  }
};

/**
 * Get user by ID
 */
exports.getUserById = async (req, res, next) => {
  try {
    const { id } = req.params;
    
    if (!validators.isValidId(id)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid user ID format'
      });
    }
    
    const user = await UserModel.findById(id).select('-password');
    
    if (!user) {
      return res.status(404).json({
        success: false,
        error: 'User not found'
      });
    }
    
    logger.info(`Retrieved user: ${id}`);
    
    res.status(200).json({
      success: true,
      data: user
    });
  } catch (error) {
    logger.error(`Error retrieving user by ID: ${error.message}`);
    next(error);
  }
};

/**
 * Create new user
 */
exports.createUser = async (req, res, next) => {
  try {
    const { name, email, password, role } = req.body;
    
    // Validate required fields
    if (!name || !email || !password) {
      return res.status(400).json({
        success: false,
        error: 'Please provide name, email and password'
      });
    }
    
    // Check if email is valid
    if (!validators.isValidEmail(email)) {
      return res.status(400).json({
        success: false,
        error: 'Please provide a valid email'
      });
    }
    
    // Check if user with this email already exists
    const existingUser = await UserModel.findOne({ email });
    
    if (existingUser) {
      return res.status(400).json({
        success: false,
        error: 'Email already in use'
      });
    }
    
    // Create new user
    const user = await UserModel.create({
      name,
      email,
      password, // Password will be hashed in the model
      role: role || 'user'
    });
    
    logger.info(`Created new user: ${user._id}`);
    
    // Remove password from response
    const userResponse = {
      _id: user._id,
      name: user.name,
      email: user.email,
      role: user.role,
      createdAt: user.createdAt
    };
    
    res.status(201).json({
      success: true,
      data: userResponse
    });
  } catch (error) {
    logger.error(`Error creating user: ${error.message}`);
    next(error);
  }
};

/**
 * Update user by ID
 */
exports.updateUser = async (req, res, next) => {
  try {
    const { id } = req.params;
    const { name, email, role } = req.body;
    
    if (!validators.isValidId(id)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid user ID format'
      });
    }
    
    // Find user first to check if exists
    const user = await UserModel.findById(id);
    
    if (!user) {
      return res.status(404).json({
        success: false,
        error: 'User not found'
      });
    }
    
    // Check if email is being updated and is already in use
    if (email && email !== user.email) {
      if (!validators.isValidEmail(email)) {
        return res.status(400).json({
          success: false,
          error: 'Please provide a valid email'
        });
      }
      
      const existingUser = await UserModel.findOne({ email });
      
      if (existingUser) {
        return res.status(400).json({
          success: false,
          error: 'Email already in use'
        });
      }
    }
    
    // Update user
    const updatedUser = await UserModel.findByIdAndUpdate(
      id,
      { name, email, role },
      { new: true, runValidators: true }
    ).select('-password');
    
    logger.info(`Updated user: ${id}`);
    
    res.status(200).json({
      success: true,
      data: updatedUser
    });
  } catch (error) {
    logger.error(`Error updating user: ${error.message}`);
    next(error);
  }
};

/**
 * Delete user by ID
 */
exports.deleteUser = async (req, res, next) => {
  try {
    const { id } = req.params;
    
    if (!validators.isValidId(id)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid user ID format'
      });
    }
    
    const user = await UserModel.findById(id);
    
    if (!user) {
      return res.status(404).json({
        success: false,
        error: 'User not found'
      });
    }
    
    await user.remove();
    
    logger.info(`Deleted user: ${id}`);
    
    res.status(200).json({
      success: true,
      data: {}
    });
  } catch (error) {
    logger.error(`Error deleting user: ${error.message}`);
    next(error);
  }
};
""",
        "src/middleware/errorHandler.js": """const logger = require('../utils/logger');

/**
 * Global error handling middleware
 */
const errorHandler = (err, req, res, next) => {
  // Log the error
  logger.error(`${err.name}: ${err.message}`);
  
  // MongoDB duplicate key error
  if (err.code === 11000) {
    const field = Object.keys(err.keyValue)[0];
    return res.status(400).json({
      success: false,
      error: `Duplicate value for ${field}. Please use another value.`,
      errorCode: 'DUPLICATE_VALUE'
    });
  }
  
  // Mongoose validation error
  if (err.name === 'ValidationError') {
    const errors = Object.values(err.errors).map(val => val.message);
    return res.status(400).json({
      success: false,
      error: errors.join(', '),
      errorCode: 'VALIDATION_ERROR'
    });
  }
  
  // Mongoose cast error (usually invalid ID)
  if (err.name === 'CastError') {
    return res.status(400).json({
      success: false,
      error: `Invalid ${err.path}: ${err.value}`,
      errorCode: 'INVALID_ID'
    });
  }
  
  // JSON parse error
  if (err instanceof SyntaxError && err.status === 400 && 'body' in err) {
    return res.status(400).json({
      success: false,
      error: 'Invalid JSON payload',
      errorCode: 'INVALID_JSON'
    });
  }
  
  // Default server error
  const statusCode = err.statusCode || 500;
  
  res.status(statusCode).json({
    success: false,
    error: statusCode === 500 ? 'Server Error' : err.message,
    errorCode: err.errorCode || 'SERVER_ERROR',
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
  });
};

module.exports = errorHandler;
"""
    },
    "django-web-app": {
        "apps/users/views.py": """from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.core.paginator import Paginator

from .models import CustomUser
from .forms import UserRegistrationForm, UserLoginForm, UserUpdateForm

def register_view(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect('dashboard:index')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful. Welcome!")
            return redirect('dashboard:index')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserRegistrationForm()
        
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('dashboard:index')
        
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, "Login successful. Welcome back!")
                
                # Get the next page from query parameters
                next_page = request.GET.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect('dashboard:index')
            else:
                messages.error(request, "Invalid email or password.")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserLoginForm()
        
    return render(request, 'users/login.html', {'form': form})

@login_required
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('users:login')

@login_required
def profile_view(request):
    """User profile view and update"""
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect('users:profile')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserUpdateForm(instance=request.user)
        
    return render(request, 'users/profile.html', {'form': form})

@login_required
@require_http_methods(["GET"])
def user_list_view(request):
    """Admin only view for listing all users"""
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('dashboard:index')
        
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(users, 10)  # 10 users per page
    users_page = paginator.get_page(page)
    
    return render(request, 'users/user_list.html', {'users': users_page})

@login_required
@require_http_methods(["GET"])
def user_detail_view(request, user_id):
    """Admin only view for user details"""
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('dashboard:index')
        
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('users:user_list')
        
    return render(request, 'users/user_detail.html', {'user_profile': user})

@login_required
@require_http_methods(["POST"])
def toggle_user_status(request, user_id):
    """Admin only view for activating/deactivating users"""
    if not request.user.is_staff:
        return JsonResponse({"success": False, "error": "Permission denied."}, status=403)
        
    try:
        user = CustomUser.objects.get(id=user_id)
        
        # Don't allow deactivating yourself
        if user == request.user:
            return JsonResponse({"success": False, "error": "You cannot deactivate your own account."}, status=400)
            
        user.is_active = not user.is_active
        user.save()
        
        status = "activated" if user.is_active else "deactivated"
        
        return JsonResponse({
            "success": True, 
            "message": f"User {user.email} has been {status}.",
            "is_active": user.is_active
        })
    except CustomUser.DoesNotExist:
        return JsonResponse({"success": False, "error": "User not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
""",
        "apps/users/models.py": """from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import EmailValidator, MinLengthValidator
import uuid

class CustomUserManager(BaseUserManager):
    """Manager for custom user model"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user"""
        if not email:
            raise ValueError('Email is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Custom user model that uses email instead of username"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        max_length=255, 
        unique=True,
        validators=[EmailValidator(message="Please enter a valid email address")]
    )
    first_name = models.CharField(
        max_length=150, 
        validators=[MinLengthValidator(2, message="First name must be at least 2 characters long")]
    )
    last_name = models.CharField(
        max_length=150,
        validators=[MinLengthValidator(2, message="Last name must be at least 2 characters long")]
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    
    # Settings
    email_notifications = models.BooleanField(default=True)
    dark_mode = models.BooleanField(default=False)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        """Return the full name of the user"""
        return f"{self.first_name} {self.last_name}"
    
    def update_last_login(self):
        """Update the last login timestamp"""
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])
        
    def has_profile_picture(self):
        """Check if user has a profile picture"""
        return bool(self.profile_picture)

class UserActivity(models.Model):
    """Model to track user activities"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = 'user activity'
        verbose_name_plural = 'user activities'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.email} - {self.activity_type} - {self.timestamp}"
"""
    },
    "flutter-mobile-app": {
        "lib/main.dart": """import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/detail_screen.dart';
import 'services/auth_service.dart';
import 'services/api_service.dart';
import 'services/storage_service.dart';
import 'utils/theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize services
  final storageService = await StorageService.init();
  final authService = AuthService(storageService: storageService);
  final apiService = ApiService(authService: authService);
  
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => authService),
        Provider.value(value: apiService),
        Provider.value(value: storageService),
      ],
      child: MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final authService = context.watch<AuthService>();
    
    return MaterialApp(
      title: 'Flutter Demo App',
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: authService.darkMode ? ThemeMode.dark : ThemeMode.light,
      debugShowCheckedModeBanner: false,
      initialRoute: authService.isAuthenticated ? '/home' : '/login',
      routes: {
        '/login': (context) => LoginScreen(),
        '/home': (context) => HomeScreen(),
        '/profile': (context) => ProfileScreen(),
        '/settings': (context) => SettingsScreen(),
        '/detail': (context) => DetailScreen(),
      },
    );
  }
}
""",
        "lib/screens/home_screen.dart": """import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/item_model.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../widgets/item_card.dart';
import '../widgets/loading_indicator.dart';
import '../widgets/custom_button.dart';
import '../utils/constants.dart';

class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _isLoading = false;
  List<ItemModel> _items = [];
  String? _error;
  int _page = 1;
  bool _hasMoreItems = true;
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _loadItems();
    
    // Add scroll listener for pagination
    _scrollController.addListener(() {
      if (_scrollController.position.pixels >= _scrollController.position.maxScrollExtent - 200 &&
          !_isLoading &&
          _hasMoreItems) {
        _loadMoreItems();
      }
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _loadItems() async {
    if (_isLoading) return;
    
    setState(() {
      _isLoading = true;
      _error = null;
    });
    
    try {
      final apiService = Provider.of<ApiService>(context, listen: false);
      final items = await apiService.fetchItems(page: _page);
      
      setState(() {
        _items = items;
        _isLoading = false;
        _hasMoreItems = items.length >= Constants.itemsPerPage;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to load items: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> _loadMoreItems() async {
    if (_isLoading) return;
    
    setState(() {
      _isLoading = true;
      _error = null;
    });
    
    try {
      final apiService = Provider.of<ApiService>(context, listen: false);
      final nextPage = _page + 1;
      final newItems = await apiService.fetchItems(page: nextPage);
      
      setState(() {
        _items.addAll(newItems);
        _page = nextPage;
        _isLoading = false;
        _hasMoreItems = newItems.length >= Constants.itemsPerPage;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to load more items: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> _refreshItems() async {
    setState(() {
      _page = 1;
      _hasMoreItems = true;
    });
    await _loadItems();
  }

  void _navigateToItemDetail(ItemModel item) {
    Navigator.pushNamed(
      context,
      '/detail',
      arguments: item,
    );
  }

  void _navigateToProfile() {
    Navigator.pushNamed(context, '/profile');
  }

  void _navigateToSettings() {
    Navigator.pushNamed(context, '/settings');
  }

  void _logout() {
    final authService = Provider.of<AuthService>(context, listen: false);
    authService.logout();
  }

  @override
  Widget build(BuildContext context) {
    final authService = Provider.of<AuthService>(context);
    final user = authService.currentUser;
    
    return Scaffold(
      appBar: AppBar(
        title: Text('Home'),
        actions: [
          IconButton(
            icon: Icon(Icons.settings),
            onPressed: _navigateToSettings,
          ),
          IconButton(
            icon: Icon(Icons.person),
            onPressed: _navigateToProfile,
          ),
        ],
      ),
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          children: <Widget>[
            DrawerHeader(
              decoration: BoxDecoration(
                color: Theme.of(context).primaryColor,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  CircleAvatar(
                    radius: 30,
                    backgroundImage: user?.profilePictureUrl != null
                        ? NetworkImage(user!.profilePictureUrl!)
                        : null,
                    child: user?.profilePictureUrl == null
                        ? Icon(Icons.person, size: 30)
                        : null,
                  ),
                  SizedBox(height: 10),
                  Text(
                    user?.displayName ?? 'Guest',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                    ),
                  ),
                  SizedBox(height: 5),
                  Text(
                    user?.email ?? '',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
            ListTile(
              leading: Icon(Icons.home),
              title: Text('Home'),
              selected: true,
              onTap: () {
                Navigator.pop(context);
              },
            ),
            ListTile(
              leading: Icon(Icons.person),
              title: Text('Profile'),
              onTap: () {
                Navigator.pop(context);
                _navigateToProfile();
              },
            ),
            ListTile(
              leading: Icon(Icons.settings),
              title: Text('Settings'),
              onTap: () {
                Navigator.pop(context);
                _navigateToSettings();
              },
            ),
            Divider(),
            ListTile(
              leading: Icon(Icons.exit_to_app),
              title: Text('Logout'),
              onTap: () {
                Navigator.pop(context);
                _logout();
              },
            ),
          ],
        ),
      ),
      body: RefreshIndicator(
        onRefresh: _refreshItems,
        child: _error != null
            ? Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(_error!, style: TextStyle(color: Colors.red)),
                    SizedBox(height: 20),
                    CustomButton(
                      label: 'Retry',
                      onPressed: _loadItems,
                    ),
                  ],
                ),
              )
            : Column(
                children: [
                  Expanded(
                    child: _items.isEmpty && _isLoading
                        ? Center(child: LoadingIndicator())
                        : _items.isEmpty
                            ? Center(child: Text('No items found'))
                            : GridView.builder(
                                controller: _scrollController,
                                padding: EdgeInsets.all(16),
                                gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                                  crossAxisCount: 2,
                                  childAspectRatio: 0.7,
                                  crossAxisSpacing: 16,
                                  mainAxisSpacing: 16,
                                ),
                                itemCount: _items.length,
                                itemBuilder: (context, index) {
                                  final item = _items[index];
                                  return ItemCard(
                                    item: item,
                                    onTap: () => _navigateToItemDetail(item),
                                  );
                                },
                              ),
                  ),
                  if (_isLoading && _items.isNotEmpty)
                    Padding(
                      padding: EdgeInsets.all(16),
                      child: LoadingIndicator(),
                    ),
                ],
              ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // Add new item functionality
        },
        child: Icon(Icons.add),
        tooltip: 'Add new item',
      ),
    );
  }
}
""",
        "lib/models/user_model.dart": """import 'dart:convert';

class UserModel {
  final String id;
  final String email;
  final String displayName;
  final String? profilePictureUrl;
  final String? bio;
  final bool emailNotifications;
  final bool darkMode;
  final DateTime createdAt;
  final DateTime? lastLogin;

  UserModel({
    required this.id,
    required this.email,
    required this.displayName,
    this.profilePictureUrl,
    this.bio,
    required this.emailNotifications,
    required this.darkMode,
    required this.createdAt,
    this.lastLogin,
  });

  UserModel copyWith({
    String? id,
    String? email,
    String? displayName,
    String? profilePictureUrl,
    String? bio,
    bool? emailNotifications,
    bool? darkMode,
    DateTime? createdAt,
    DateTime? lastLogin,
  }) {
    return UserModel(
      id: id ?? this.id,
      email: email ?? this.email,
      displayName: displayName ?? this.displayName,
      profilePictureUrl: profilePictureUrl ?? this.profilePictureUrl,
      bio: bio ?? this.bio,
      emailNotifications: emailNotifications ?? this.emailNotifications,
      darkMode: darkMode ?? this.darkMode,
      createdAt: createdAt ?? this.createdAt,
      lastLogin: lastLogin ?? this.lastLogin,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'email': email,
      'displayName': displayName,
      'profilePictureUrl': profilePictureUrl,
      'bio': bio,
      'emailNotifications': emailNotifications,
      'darkMode': darkMode,
      'createdAt': createdAt.toIso8601String(),
      'lastLogin': lastLogin?.toIso8601String(),
    };
  }

  factory UserModel.fromMap(Map<String, dynamic> map) {
    return UserModel(
      id: map['id'],
      email: map['email'],
      displayName: map['displayName'] ?? map['display_name'],
      profilePictureUrl: map['profilePictureUrl'] ?? map['profile_picture_url'],
      bio: map['bio'],
      emailNotifications: map['emailNotifications'] ?? map['email_notifications'] ?? true,
      darkMode: map['darkMode'] ?? map['dark_mode'] ?? false,
      createdAt: DateTime.parse(map['createdAt'] ?? map['created_at']),
      lastLogin: map['lastLogin'] != null || map['last_login'] != null
          ? DateTime.parse(map['lastLogin'] ?? map['last_login'])
          : null,
    );
  }

  String toJson() => json.encode(toMap());

  factory UserModel.fromJson(String source) => UserModel.fromMap(json.decode(source));

  @override
  String toString() {
    return 'UserModel(id: $id, email: $email, displayName: $displayName, '
        'profilePictureUrl: $profilePictureUrl, bio: $bio, '
        'emailNotifications: $emailNotifications, darkMode: $darkMode, '
        'createdAt: $createdAt, lastLogin: $lastLogin)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
  
    return other is UserModel &&
      other.id == id &&
      other.email == email &&
      other.displayName == displayName &&
      other.profilePictureUrl == profilePictureUrl &&
      other.bio == bio &&
      other.emailNotifications == emailNotifications &&
      other.darkMode == darkMode &&
      other.createdAt == createdAt &&
      other.lastLogin == lastLogin;
  }

  @override
  int get hashCode {
    return id.hashCode ^
      email.hashCode ^
      displayName.hashCode ^
      profilePictureUrl.hashCode ^
      bio.hashCode ^
      emailNotifications.hashCode ^
      darkMode.hashCode ^
      createdAt.hashCode ^
      lastLogin.hashCode;
  }
}
"""
    },
    "spring-boot-microservice": {
        "src/main/java/com/example/microservice/controllers/UserController.java": """package com.example.microservice.controllers;

import com.example.microservice.models.User;
import com.example.microservice.services.UserService;
import com.example.microservice.exceptions.ResourceNotFoundException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/users")
@Validated
public class UserController {

    private final UserService userService;

    @Autowired
    public UserController(UserService userService) {
        this.userService = userService;
    }

    /**
     * Get all users with pagination and sorting
     *
     * @param page Page number (zero-based)
     * @param size Page size
     * @param sort Sort field
     * @param order Sort order (asc or desc)
     * @return List of users
     */
    @GetMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Map<String, Object>> getAllUsers(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(defaultValue = "createdAt") String sort,
            @RequestParam(defaultValue = "desc") String order) {
        
        Map<String, Object> response = userService.getAllUsers(page, size, sort, order);
        return ResponseEntity.ok(response);
    }

    /**
     * Get user by ID
     *
     * @param id User ID
     * @return User details
     */
    @GetMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN') or @userSecurity.isCurrentUser(#id)")
    public ResponseEntity<User> getUserById(@PathVariable UUID id) {
        User user = userService.getUserById(id)
                .orElseThrow(() -> new ResourceNotFoundException("User not found with id: " + id));
        return ResponseEntity.ok(user);
    }

    /**
     * Create a new user
     *
     * @param user User details
     * @return Created user
     */
    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<User> createUser(@Valid @RequestBody User user) {
        User createdUser = userService.createUser(user);
        return new ResponseEntity<>(createdUser, HttpStatus.CREATED);
    }

    /**
     * Update user details
     *
     * @param id User ID
     * @param userDetails Updated user details
     * @return Updated user
     */
    @PutMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN') or @userSecurity.isCurrentUser(#id)")
    public ResponseEntity<User> updateUser(
            @PathVariable UUID id,
            @Valid @RequestBody User userDetails) {
        
        User updatedUser = userService.updateUser(id, userDetails);
        return ResponseEntity.ok(updatedUser);
    }

    /**
     * Delete a user
     *
     * @param id User ID
     * @return Deletion confirmation
     */
    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Map<String, Boolean>> deleteUser(@PathVariable UUID id) {
        userService.deleteUser(id);
        
        Map<String, Boolean> response = new HashMap<>();
        response.put("deleted", Boolean.TRUE);
        return ResponseEntity.ok(response);
    }

    /**
     * Change user password
     *
     * @param id User ID
     * @param passwordRequest Password change request
     * @return Status message
     */
    @PostMapping("/{id}/change-password")
    @PreAuthorize("hasRole('ADMIN') or @userSecurity.isCurrentUser(#id)")
    public ResponseEntity<Map<String, String>> changePassword(
            @PathVariable UUID id,
            @Valid @RequestBody Map<String, String> passwordRequest) {
        
        String currentPassword = passwordRequest.get("currentPassword");
        String newPassword = passwordRequest.get("newPassword");
        
        if (currentPassword == null || newPassword == null) {
            throw new IllegalArgumentException("Current password and new password are required");
        }
        
        userService.changePassword(id, currentPassword, newPassword);
        
        Map<String, String> response = new HashMap<>();
        response.put("message", "Password changed successfully");
        return ResponseEntity.ok(response);
    }

    /**
     * Toggle user active status
     *
     * @param id User ID
     * @return Updated user
     */
    @PostMapping("/{id}/toggle-status")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<User> toggleUserStatus(@PathVariable UUID id) {
        User user = userService.toggleUserStatus(id);
        return ResponseEntity.ok(user);
    }

    /**
     * Get current user profile
     *
     * @return Current user details
     */
    @GetMapping("/me")
    public ResponseEntity<User> getCurrentUser() {
        User currentUser = userService.getCurrentUser();
        return ResponseEntity.ok(currentUser);
    }

    /**
     * Search users
     *
     * @param query Search query
     * @param page Page number
     * @param size Page size
     * @return Search results
     */
    @GetMapping("/search")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Map<String, Object>> searchUsers(
            @RequestParam @NotNull String query,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {
        
        Map<String, Object> results = userService.searchUsers(query, page, size);
        return ResponseEntity.ok(results);
    }
}
""",
        "src/main/java/com/example/microservice/config/SecurityConfig.java": """package com.example.microservice.config;

import com.example.microservice.security.CustomUserDetailsService;
import com.example.microservice.security.JwtAuthenticationEntryPoint;
import com.example.microservice.security.JwtAuthenticationFilter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.builders.AuthenticationManagerBuilder;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.filter.CorsFilter;

import java.util.Arrays;
import java.util.Collections;

@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(
    securedEnabled = true,
    jsr250Enabled = true,
    prePostEnabled = true
)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    @Autowired
    private CustomUserDetailsService userDetailsService;

    @Autowired
    private JwtAuthenticationEntryPoint unauthorizedHandler;

    @Bean
    public JwtAuthenticationFilter jwtAuthenticationFilter() {
        return new JwtAuthenticationFilter();
    }

    @Override
    protected void configure(AuthenticationManagerBuilder auth) throws Exception {
        auth.userDetailsService(userDetailsService).passwordEncoder(passwordEncoder());
    }

    @Bean
    @Override
    public AuthenticationManager authenticationManagerBean() throws Exception {
        return super.authenticationManagerBean();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            .cors()
                .and()
            .csrf()
                .disable()
            .exceptionHandling()
                .authenticationEntryPoint(unauthorizedHandler)
                .and()
            .sessionManagement()
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                .and()
            .authorizeRequests()
                .antMatchers("/",
                    "/favicon.ico",
                    "/**/*.png",
                    "/**/*.gif",
                    "/**/*.svg",
                    "/**/*.jpg",
                    "/**/*.html",
                    "/**/*.css",
                    "/**/*.js")
                    .permitAll()
                .antMatchers("/api/auth/**")
                    .permitAll()
                .antMatchers("/api/health/**")
                    .permitAll()
                .antMatchers("/v3/api-docs/**", "/swagger-ui/**", "/swagger-ui.html")
                    .permitAll()
                .antMatchers(HttpMethod.GET, "/api/products")
                    .permitAll()
                .anyRequest()
                    .authenticated();

        // Add our custom JWT security filter
        http.addFilterBefore(jwtAuthenticationFilter(), UsernamePasswordAuthenticationFilter.class);
    }

    @Bean
    public CorsFilter corsFilter() {
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        CorsConfiguration config = new CorsConfiguration();
        
        config.setAllowCredentials(true);
        config.setAllowedOriginPatterns(Collections.singletonList("*"));
        config.setAllowedHeaders(Arrays.asList("Origin", "Content-Type", "Accept", "Authorization"));
        config.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"));
        
        source.registerCorsConfiguration("/**", config);
        return new CorsFilter(source);
    }
}
"""
    }
}

# Function to flatten a nested directory structure
def flatten_directory_structure(structure, prefix=""):
    files = []
    for name, value in structure.items():
        path = f"{prefix}/{name}" if prefix else name
        if isinstance(value, dict) and not all(k in ["language", "loc", "complexity"] for k in value.keys()):
            # This is a directory
            files.extend(flatten_directory_structure(value, path))
        else:
            # This is a file
            files.append({
                "path": path,
                "language": value.get("language", "Unknown"),
                "loc": value.get("loc", 0),
                "complexity": value.get("complexity", 0)
            })
    return files

# Initialize session state variables if not already set
if "selected_repository" not in st.session_state:
    st.session_state.selected_repository = None

if "repository_files" not in st.session_state:
    st.session_state.repository_files = []

if "repository_name" not in st.session_state:
    st.session_state.repository_name = ""

if "repository_language" not in st.session_state:
    st.session_state.repository_language = ""

if "file_contents" not in st.session_state:
    st.session_state.file_contents = {}

if "current_file" not in st.session_state:
    st.session_state.current_file = None

if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

if "file_analysis" not in st.session_state:
    st.session_state.file_analysis = {}

if "repository_metrics" not in st.session_state:
    st.session_state.repository_metrics = None

# Sidebar - Repository selector
st.sidebar.title("Repository Analysis")

# Option to select sample repositories or upload your own
repository_source = st.sidebar.radio(
    "Repository Source",
    ["Sample Repositories", "Upload Repository"]
)

if repository_source == "Sample Repositories":
    selected_repo_key = st.sidebar.selectbox(
        "Select Repository",
        list(sample_repositories.keys()),
        format_func=lambda x: sample_repositories[x]["name"]
    )
    
    if st.sidebar.button("Analyze Repository"):
        # Set the selected repository
        st.session_state.selected_repository = selected_repo_key
        st.session_state.repository_name = sample_repositories[selected_repo_key]["name"]
        st.session_state.repository_language = sample_repositories[selected_repo_key]["language"]
        
        # Flatten the directory structure
        repo_structure = sample_repositories[selected_repo_key]["structure"]
        st.session_state.repository_files = flatten_directory_structure(repo_structure)
        
        # Load sample file contents
        if selected_repo_key in sample_file_contents:
            st.session_state.file_contents = sample_file_contents[selected_repo_key]
        else:
            st.session_state.file_contents = {}
        
        # Reset current file selection
        st.session_state.current_file = None
        
        # Generate analysis results
        st.session_state.analysis_results = generate_repository_analysis(
            st.session_state.repository_files,
            st.session_state.repository_language
        )
        
        # Generate repository metrics
        st.session_state.repository_metrics = generate_repository_metrics(
            st.session_state.repository_files
        )

else:  # Upload Repository
    uploaded_files = st.sidebar.file_uploader(
        "Upload repository files",
        accept_multiple_files=True,
        type=["py", "js", "java", "html", "css", "dart", "json", "xml", "md"]
    )
    
    if uploaded_files and st.sidebar.button("Analyze Uploaded Files"):
        # Process uploaded files
        repository_files = []
        file_contents = {}
        
        for uploaded_file in uploaded_files:
            file_path = uploaded_file.name
            contents = uploaded_file.getvalue().decode("utf-8")
            
            # Determine language from file extension
            extension = file_path.split(".")[-1].lower()
            language = {
                "py": "Python",
                "js": "JavaScript",
                "java": "Java",
                "html": "HTML",
                "css": "CSS",
                "dart": "Dart",
                "json": "JSON",
                "xml": "XML",
                "md": "Markdown"
            }.get(extension, "Other")
            
            # Count lines of code
            loc = len(contents.split("\n"))
            
            # Simplified complexity estimation (just a placeholder)
            complexity = min(10, max(1, loc // 20))
            
            repository_files.append({
                "path": file_path,
                "language": language,
                "loc": loc,
                "complexity": complexity
            })
            
            file_contents[file_path] = contents
        
        # Set session state
        st.session_state.repository_files = repository_files
        st.session_state.file_contents = file_contents
        st.session_state.selected_repository = "uploaded"
        st.session_state.repository_name = "Uploaded Repository"
        
        # Determine primary language
        language_counts = {}
        for file in repository_files:
            lang = file["language"]
            language_counts[lang] = language_counts.get(lang, 0) + file["loc"]
        
        if language_counts:
            primary_language = max(language_counts.items(), key=lambda x: x[1])[0]
            st.session_state.repository_language = primary_language
        else:
            st.session_state.repository_language = "Unknown"
        
        # Reset current file selection
        st.session_state.current_file = None
        
        # Generate analysis results
        st.session_state.analysis_results = generate_repository_analysis(
            st.session_state.repository_files,
            st.session_state.repository_language
        )
        
        # Generate repository metrics
        st.session_state.repository_metrics = generate_repository_metrics(
            st.session_state.repository_files
        )

# If a repository is selected, show file browser in sidebar
if st.session_state.selected_repository:
    st.sidebar.markdown("### File Browser")
    
    # Group files by directory
    directories = {}
    for file in st.session_state.repository_files:
        path = file["path"]
        parts = path.split("/")
        
        # Skip the file name (last part)
        current_dir = directories
        for i, part in enumerate(parts[:-1]):
            if part not in current_dir:
                current_dir[part] = {}
            current_dir = current_dir[part]
        
        # Add the file to the current directory
        current_dir[parts[-1]] = file
    
    # Function to render the file tree recursively
    def render_directory(dir_dict, path_prefix="", depth=0):
        # Sort directories first, then files
        items = sorted(dir_dict.items(), key=lambda x: (0 if isinstance(x[1], dict) else 1, x[0]))
        
        for name, value in items:
            current_path = f"{path_prefix}/{name}" if path_prefix else name
            
            if isinstance(value, dict) and not all(k in ["path", "language", "loc", "complexity"] for k in value.keys()):
                # This is a directory
                st.sidebar.markdown(
                    f"<div style='margin-left: {depth * 16}px;'>"
                    f"<span class='directory'>📁 {name}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                render_directory(value, current_path, depth + 1)
            else:
                # This is a file
                is_selected = st.session_state.current_file == current_path
                
                if st.sidebar.button(
                    f"📄 {name}",
                    key=f"file_{current_path}",
                    help=f"Lines: {value.get('loc', 0)}, Language: {value.get('language', 'Unknown')}",
                    on_click=select_file,
                    args=(current_path,),
                ):
                    pass
    
    # Function to handle file selection
    def select_file(file_path):
        st.session_state.current_file = file_path
        
        # Generate file analysis if this is a new file selection
        if file_path not in st.session_state.file_analysis:
            # Find the file info
            file_info = next((f for f in st.session_state.repository_files if f["path"] == file_path), None)
            
            if file_info:
                # Check if we have the file contents
                if file_path in st.session_state.file_contents:
                    content = st.session_state.file_contents[file_path]
                else:
                    # Generate dummy content based on the file type
                    content = f"// Sample content for {file_path}\n// (Actual file content not available)"
                
                # Generate analysis
                st.session_state.file_analysis[file_path] = generate_file_analysis(
                    file_path,
                    file_info,
                    content,
                    st.session_state.repository_language
                )
    
    # Render the file tree
    render_directory(directories)
    
# Main content area
if st.session_state.selected_repository:
    # Display repository information
    st.title(st.session_state.repository_name)
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Get metrics from repository metrics
    metrics = st.session_state.repository_metrics
    quality_score = metrics["quality_score"]
    maintainability = metrics["maintainability"] 
    testability = metrics["testability"]
    security_score = metrics["security_score"]
    
    # Display metrics
    with col1:
        quality_class = "good" if quality_score >= 75 else "average" if quality_score >= 50 else "poor"
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Quality Score</div>
            <div class="metric-value {quality_class}">{quality_score}/100</div>
            <div class="progress-container">
                <div class="progress-bar progress-{quality_class}" style="width: {quality_score}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        maintainability_class = "good" if maintainability >= 75 else "average" if maintainability >= 50 else "poor"
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Maintainability</div>
            <div class="metric-value {maintainability_class}">{maintainability}/100</div>
            <div class="progress-container">
                <div class="progress-bar progress-{maintainability_class}" style="width: {maintainability}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        testability_class = "good" if testability >= 75 else "average" if testability >= 50 else "poor"
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Testability</div>
            <div class="metric-value {testability_class}">{testability}/100</div>
            <div class="progress-container">
                <div class="progress-bar progress-{testability_class}" style="width: {testability}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        security_class = "good" if security_score >= 75 else "average" if security_score >= 50 else "poor"
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Security</div>
            <div class="metric-value {security_class}">{security_score}/100</div>
            <div class="progress-container">
                <div class="progress-bar progress-{security_class}" style="width: {security_score}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Add some spacing
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    # Create tabs for different analysis views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Files", "Issues", "Architecture", "Recommendations"])
    
    with tab1:  # Overview tab
        # Display repository summary
        st.markdown("### Repository Summary")
        st.markdown(f"""
        <div class="summary-box">
            <p>
            <strong>Language:</strong> {st.session_state.repository_language}<br>
            <strong>Files:</strong> {len(st.session_state.repository_files)}<br>
            <strong>Lines of Code:</strong> {sum(f["loc"] for f in st.session_state.repository_files)}<br>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display language distribution
        st.markdown("### Language Distribution")
        
        language_counts = {}
        for file in st.session_state.repository_files:
            lang = file["language"]
            loc = file["loc"]
            language_counts[lang] = language_counts.get(lang, 0) + loc
        
        # Create data for pie chart
        languages = list(language_counts.keys())
        loc_counts = list(language_counts.values())
        
        fig = px.pie(
            values=loc_counts,
            names=languages,
            title="Code Distribution by Language",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display complexity distribution
        st.markdown("### Code Complexity Distribution")
        
        complexity_data = []
        for file in st.session_state.repository_files:
            complexity = file["complexity"]
            complexity_data.append({
                "file": file["path"],
                "complexity": complexity,
                "category": "High" if complexity > 7 else "Medium" if complexity > 4 else "Low"
            })
        
        complexity_df = pd.DataFrame(complexity_data)
        
        # Count files in each complexity category
        complexity_counts = complexity_df["category"].value_counts().reset_index()
        complexity_counts.columns = ["Complexity", "Files"]
        
        # Sort by complexity level
        complexity_order = {"Low": 0, "Medium": 1, "High": 2}
        complexity_counts["SortOrder"] = complexity_counts["Complexity"].map(complexity_order)
        complexity_counts = complexity_counts.sort_values("SortOrder")
        
        # Create bar chart
        fig = px.bar(
            complexity_counts,
            x="Complexity",
            y="Files",
            color="Complexity",
            title="Files by Complexity Level",
            color_discrete_map={
                "Low": "#4CAF50",
                "Medium": "#FFC107",
                "High": "#F44336"
            }
        )
        
        fig.update_layout(xaxis_title=None)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display code quality strengths and weaknesses
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Strengths")
            strengths = st.session_state.analysis_results.get("strengths", [])
            
            if strengths:
                for strength in strengths[:3]:  # Show top 3 strengths
                    st.markdown(f"""
                    <div class="strength-box">
                        <div class="issue-title">{strength["title"]}</div>
                        <p>{strength["description"]}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No strengths identified")
        
        with col2:
            st.markdown("### Weaknesses")
            weaknesses = st.session_state.analysis_results.get("weaknesses", [])
            
            if weaknesses:
                for weakness in weaknesses[:3]:  # Show top 3 weaknesses
                    st.markdown(f"""
                    <div class="weakness-box">
                        <div class="issue-title">{weakness["title"]}</div>
                        <p>{weakness["description"]}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No weaknesses identified")
    
    with tab2:  # Files tab
        # File metrics and details
        st.markdown("### File Metrics")
        
        # Create data for table
        file_data = []
        for file in st.session_state.repository_files:
            path = file["path"]
            language = file["language"]
            loc = file["loc"]
            complexity = file["complexity"]
            
            # Calculate a quality score for each file
            # This is a simplified calculation
            quality = 100 - (complexity * 10) if complexity < 10 else 0
            quality = max(0, min(100, quality))
            
            file_data.append({
                "File": path,
                "Language": language,
                "LOC": loc,
                "Complexity": complexity,
                "Quality": quality
            })
        
        file_df = pd.DataFrame(file_data)
        
        # Add sorting and filtering
        st.markdown("#### Filter and Sort Files")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filter by language
            languages = ["All"] + sorted(set(file["language"] for file in st.session_state.repository_files))
            selected_language = st.selectbox("Language", languages)
        
        with col2:
            # Sort by column
            sort_columns = ["File", "Language", "LOC", "Complexity", "Quality"]
            sort_by = st.selectbox("Sort by", sort_columns)
        
        with col3:
            # Sort order
            sort_order = st.radio("Order", ["Ascending", "Descending"], horizontal=True)
        
        # Apply filters and sorting
        if selected_language != "All":
            filtered_df = file_df[file_df["Language"] == selected_language]
        else:
            filtered_df = file_df
        
        # Apply sorting
        ascending = sort_order == "Ascending"
        filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)
        
        # Display file table
        st.markdown(f"#### {len(filtered_df)} Files")
        st.dataframe(
            filtered_df,
            hide_index=True,
            use_container_width=True
        )
        
        # Display file distribution by directory
        st.markdown("### Files by Directory")
        
        # Count files by directory
        directory_counts = {}
        for file in st.session_state.repository_files:
            path = file["path"]
            parts = path.split("/")
            
            # Get the top-level directory
            if len(parts) > 1:
                directory = parts[0]
            else:
                directory = "Root"
            
            directory_counts[directory] = directory_counts.get(directory, 0) + 1
        
        # Create data for bar chart
        directory_df = pd.DataFrame({
            "Directory": list(directory_counts.keys()),
            "Files": list(directory_counts.values())
        })
        
        # Sort by number of files
        directory_df = directory_df.sort_values("Files", ascending=False)
        
        fig = px.bar(
            directory_df,
            x="Directory",
            y="Files",
            title="Files by Directory",
            color="Files",
            color_continuous_scale=px.colors.sequential.Viridis
        )
        
        fig.update_layout(xaxis_title=None)
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:  # Issues tab
        # Display issues found in the repository
        st.markdown("### Issues")
        
        issues = st.session_state.analysis_results.get("issues", [])
        
        if issues:
            # Add filtering by severity
            severity_options = ["All", "Critical", "High", "Medium", "Low"]
            selected_severity = st.radio("Filter by Severity", severity_options, horizontal=True)
            
            # Filter issues by severity
            if selected_severity != "All":
                filtered_issues = [issue for issue in issues if issue["severity"] == selected_severity.lower()]
            else:
                filtered_issues = issues
            
            # Display filtered issues
            st.markdown(f"#### {len(filtered_issues)} Issues Found")
            
            for issue in filtered_issues:
                severity = issue["severity"]
                title = issue["title"]
                description = issue["description"]
                file_path = issue.get("file_path", "Multiple files")
                line = issue.get("line", "N/A")
                
                st.markdown(f"""
                <div class="issue-box">
                    <div class="issue-title {severity}">
                        <span class="badge badge-{severity}">{severity.title()}</span> {title}
                    </div>
                    <p>{description}</p>
                    <div class="file-meta">
                        <strong>Location:</strong> {file_path}{f" (line {line})" if line != "N/A" else ""}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No issues identified")
        
    with tab4:  # Architecture tab
        # Display architecture analysis
        st.markdown("### Architecture Overview")
        
        # Architecture quality score
        architecture_score = st.session_state.analysis_results.get("architecture_score", 70)
        architecture_class = "good" if architecture_score >= 75 else "average" if architecture_score >= 50 else "poor"
        
        st.markdown(f"""
        <div class="summary-box">
            <div class="metric-label">Architecture Quality</div>
            <div class="metric-value {architecture_class}" style="font-size: 2rem;">{architecture_score}/100</div>
            <div class="progress-container">
                <div class="progress-bar progress-{architecture_class}" style="width: {architecture_score}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Architecture visualization
        st.markdown("### Component Dependencies")
        
        # Create a directed graph
        G = nx.DiGraph()
        
        # Create nodes and edges based on repository structure
        # This is highly simplified and would be more sophisticated in a real application
        
        if st.session_state.repository_language == "JavaScript":
            components = ["Controllers", "Models", "Routes", "Middleware", "Utils", "App"]
            # Add nodes
            for component in components:
                G.add_node(component)
            
            # Add edges (dependencies)
            G.add_edge("App", "Routes")
            G.add_edge("App", "Middleware")
            G.add_edge("Routes", "Controllers")
            G.add_edge("Controllers", "Models")
            G.add_edge("Controllers", "Utils")
            G.add_edge("Middleware", "Utils")
        
        elif st.session_state.repository_language == "Python":
            components = ["Views", "Models", "Forms", "Templates", "Admin", "Utils"]
            # Add nodes
            for component in components:
                G.add_node(component)
            
            # Add edges (dependencies)
            G.add_edge("Views", "Models")
            G.add_edge("Views", "Forms")
            G.add_edge("Views", "Templates")
            G.add_edge("Forms", "Models")
            G.add_edge("Admin", "Models")
            G.add_edge("Models", "Utils")
        
        elif st.session_state.repository_language == "Dart":
            components = ["Screens", "Widgets", "Models", "Services", "Utils"]
            # Add nodes
            for component in components:
                G.add_node(component)
            
            # Add edges (dependencies)
            G.add_edge("Screens", "Widgets")
            G.add_edge("Screens", "Models")
            G.add_edge("Screens", "Services")
            G.add_edge("Widgets", "Models")
            G.add_edge("Services", "Models")
            G.add_edge("Services", "Utils")
        
        elif st.session_state.repository_language == "Java":
            components = ["Controllers", "Services", "Repositories", "Models", "Config", "Exceptions", "Utils"]
            # Add nodes
            for component in components:
                G.add_node(component)
            
            # Add edges (dependencies)
            G.add_edge("Controllers", "Services")
            G.add_edge("Services", "Repositories")
            G.add_edge("Services", "Models")
            G.add_edge("Repositories", "Models")
            G.add_edge("Controllers", "Exceptions")
            G.add_edge("Services", "Exceptions")
            G.add_edge("Config", "Services")
            G.add_edge("Services", "Utils")
        
        else:
            components = ["Component A", "Component B", "Component C", "Component D", "Component E"]
            # Add nodes
            for component in components:
                G.add_node(component)
            
            # Add edges (dependencies)
            G.add_edge("Component A", "Component B")
            G.add_edge("Component A", "Component C")
            G.add_edge("Component B", "Component D")
            G.add_edge("Component C", "Component D")
            G.add_edge("Component D", "Component E")
        
        # Create a figure with a dark background
        plt.figure(figsize=(10, 7), facecolor='#0E1117')
        
        # Draw the graph
        pos = nx.spring_layout(G, k=0.3, iterations=50)
        
        # Draw nodes
        nx.draw_networkx_nodes(
            G, pos,
            node_size=1000,
            node_color='#1976D2',
            alpha=0.8,
            linewidths=2,
            edgecolors='white'
        )
        
        # Draw edges
        nx.draw_networkx_edges(
            G, pos,
            width=2,
            alpha=0.7,
            edge_color='#4CAF50',
            arrows=True,
            arrowsize=20,
            arrowstyle='-|>',
            connectionstyle='arc3,rad=0.1'
        )
        
        # Draw labels
        nx.draw_networkx_labels(
            G, pos,
            font_size=12,
            font_family='sans-serif',
            font_weight='bold',
            font_color='white'
        )
        
        # Remove axes
        plt.axis('off')
        
        # Display the graph
        st.pyplot(plt)
        
        # Architecture metrics
        st.markdown("### Architecture Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Coupling</div>
                <div class="metric-value average">Medium</div>
                <p style="font-size: 0.9rem;">The components have a moderate level of interdependence.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Cohesion</div>
                <div class="metric-value good">High</div>
                <p style="font-size: 0.9rem;">Components have a good level of internal cohesion.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Complexity</div>
                <div class="metric-value average">Medium</div>
                <p style="font-size: 0.9rem;">The architectural complexity is manageable but could be improved.</p>
            </div>
            """, unsafe_allow_html=True)
    
    with tab5:  # Recommendations tab
        # Display recommendations for improving the codebase
        st.markdown("### Recommendations")
        
        recommendations = st.session_state.analysis_results.get("recommendations", [])
        
        if recommendations:
            for rec in recommendations:
                title = rec["title"]
                description = rec["description"]
                priority = rec["priority"].lower()
                
                st.markdown(f"""
                <div class="recommendation-box">
                    <div class="issue-title">
                        <span class="badge badge-{priority}">{rec["priority"]}</span> {title}
                    </div>
                    <p>{description}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recommendations provided")
    
    # If a file is selected, show file details
    if st.session_state.current_file:
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown(f"## File Analysis: {st.session_state.current_file}")
        
        # Get file info and analysis
        file_info = next((f for f in st.session_state.repository_files if f["path"] == st.session_state.current_file), None)
        file_analysis = st.session_state.file_analysis.get(st.session_state.current_file, None)
        
        if file_info and file_analysis:
            # File metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-label">Language</div>
                    <div class="metric-value" style="font-size: 1.5rem;">{file_info["language"]}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-label">Lines of Code</div>
                    <div class="metric-value" style="font-size: 1.5rem;">{file_info["loc"]}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                complexity = file_info["complexity"]
                complexity_class = "good" if complexity <= 4 else "average" if complexity <= 7 else "poor"
                
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-label">Complexity</div>
                    <div class="metric-value {complexity_class}" style="font-size: 1.5rem;">{complexity}/10</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                quality = file_analysis["quality_score"]
                quality_class = "good" if quality >= 75 else "average" if quality >= 50 else "poor"
                
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-label">Quality Score</div>
                    <div class="metric-value {quality_class}" style="font-size: 1.5rem;">{quality}/100</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Create tabs for file analysis
            file_tab1, file_tab2, file_tab3 = st.tabs(["Issues", "Best Practices", "Content"])
            
            with file_tab1:
                # File-specific issues
                st.markdown("### File Issues")
                
                issues = file_analysis.get("issues", [])
                
                if issues:
                    for issue in issues:
                        severity = issue["severity"]
                        title = issue["title"]
                        description = issue["description"]
                        line = issue.get("line", "N/A")
                        
                        st.markdown(f"""
                        <div class="issue-box">
                            <div class="issue-title {severity}">
                                <span class="badge badge-{severity}">{severity.title()}</span> {title}
                            </div>
                            <p>{description}</p>
                            <div class="file-meta">
                                <strong>Line:</strong> {line}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No issues identified in this file")
            
            with file_tab2:
                # Best practices analysis
                st.markdown("### Best Practices")
                
                best_practices = file_analysis.get("best_practices", [])
                
                if best_practices:
                    for practice in best_practices:
                        status = practice["status"]
                        title = practice["title"]
                        description = practice["description"]
                        
                        status_class = "good" if status else "poor"
                        status_text = "✓ Followed" if status else "✗ Not Followed"
                        
                        st.markdown(f"""
                        <div class="{'strength-box' if status else 'weakness-box'}">
                            <div class="issue-title">
                                <span class="{status_class}">{status_text}</span> {title}
                            </div>
                            <p>{description}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No best practices evaluated for this file")
            
            with file_tab3:
                # Show file content
                with st.expander("View File Content", expanded=False):
                    st.code(st.session_state.file_contents[st.session_state.current_file], language=file_info.get("language", "").lower())
else:
    # Welcome message
    st.info("""
    ### Repository Analysis Tool
    
    This tool analyzes code repositories to provide insights on:
    - Overall code quality and architecture
    - Code organization and structure
    - Potential issues and improvement opportunities
    - Best practices implementation
    
    To get started:
    1. Select a sample repository or upload your own files
    2. Click "Analyze Repository" to generate insights
    3. Select a specific file for detailed analysis
    
    The analysis will provide you with quality scores, architecture evaluation,
    identified issues, and improvement recommendations.
    """)
    
    # Sample preview
    st.image("https://miro.medium.com/max/1400/1*RIrV8tSF-L-Gnh9G1qUjYQ.png", 
             caption="Example repository analysis", 
             use_column_width=True)
# Helper functions for repository analysis
def generate_repository_analysis(files, primary_language):
    """Generate analysis results for a repository"""
    
    # In a real implementation, this would perform actual code analysis
    # For demonstration purposes, we're using simulated data
    
    analysis = {
        "strengths": [
            {
                "title": "Well-structured code organization",
                "description": "The code is organized into clear, logical components with good separation of concerns."
            },
            {
                "title": "Consistent naming conventions",
                "description": "The codebase follows consistent naming conventions, making it more readable and maintainable."
            },
            {
                "title": "Comprehensive test coverage",
                "description": "The codebase includes tests for core functionality, reducing the risk of regressions."
            }
        ],
        "weaknesses": [
            {
                "title": "High complexity in some modules",
                "description": "Several modules have high cyclomatic complexity, making them harder to understand and test."
            },
            {
                "title": "Limited documentation",
                "description": "Some parts of the codebase lack sufficient documentation, which may impede understanding and maintenance."
            },
            {
                "title": "Inconsistent error handling",
                "description": "Error handling approaches vary across the codebase, potentially leading to unpredictable behavior."
            }
        ],
        "issues": [
            {
                "title": "Potential security vulnerability",
                "description": "Possible SQL injection vulnerability in database queries",
                "severity": "critical",
                "file_path": "src/controllers/userController.js",
                "line": 42
            },
            {
                "title": "Performance concern",
                "description": "Inefficient data processing could lead to performance issues with large datasets",
                "severity": "high",
                "file_path": "src/services/dataService.js",
                "line": 78
            },
            {
                "title": "Code duplication",
                "description": "Similar code patterns repeated across multiple modules",
                "severity": "medium"
            },
            {
                "title": "Unused variables",
                "description": "Several unused variables found throughout the codebase",
                "severity": "low"
            }
        ],
        "architecture_score": 75,
        "recommendations": [
            {
                "title": "Refactor high-complexity modules",
                "description": "Break down complex modules into smaller, more manageable components to improve readability and testability.",
                "priority": "High"
            },
            {
                "title": "Implement consistent error handling",
                "description": "Establish and follow a consistent error handling pattern throughout the codebase.",
                "priority": "Medium"
            },
            {
                "title": "Add missing documentation",
                "description": "Improve documentation, especially for core modules and public APIs.",
                "priority": "Medium"
            },
            {
                "title": "Address security vulnerabilities",
                "description": "Fix identified security vulnerabilities, particularly in data handling and authentication.",
                "priority": "Critical"
            }
        ]
    }
    
    return analysis

def generate_repository_metrics(files):
    """Generate metrics for a repository"""
    
    # Calculate quality score based on complexity
    total_loc = sum(f["loc"] for f in files)
    avg_complexity = sum(f["complexity"] * f["loc"] for f in files) / total_loc if total_loc > 0 else 0
    
    # Simplified quality score calculation
    quality_score = max(0, min(100, int(100 - avg_complexity * 8)))
    
    # Calculate other metrics
    high_complexity_files = sum(1 for f in files if f["complexity"] > 7)
    high_complexity_percentage = (high_complexity_files / len(files)) * 100 if files else 0
    
    # Calculate maintainability
    maintainability = max(0, min(100, int(quality_score * 0.7 + (100 - high_complexity_percentage) * 0.3)))
    
    # Calculate testability
    testability = max(0, min(100, int(maintainability * 0.9)))
    
    # Calculate security score (simplified)
    security_score = max(0, min(100, int(quality_score * 0.8)))
    
    return {
        "quality_score": quality_score,
        "maintainability": maintainability,
        "testability": testability,
        "security_score": security_score,
        "high_complexity_files": high_complexity_files,
        "high_complexity_percentage": high_complexity_percentage
    }

def generate_file_analysis(file_path, file_info, content, primary_language):
    """Generate analysis for a specific file"""
    
    # In a real implementation, this would perform actual code analysis
    # For demonstration purposes, we're using simulated data based on file info
    
    loc = file_info["loc"]
    complexity = file_info["complexity"]
    language = file_info["language"]
    
    # Calculate a quality score for the file
    quality_score = 100 - (complexity * 10) if complexity < 10 else 0
    quality_score = max(0, min(100, quality_score))
    
    # Generate issues based on complexity and other factors
    issues = []
    
    if complexity > 7:
        issues.append({
            "title": "High cyclomatic complexity",
            "description": "This file has high complexity, making it harder to understand and maintain.",
            "severity": "high",
            "line": "N/A"
        })
    
    if "TODO" in content:
        todo_line = content.split("\n").index([line for line in content.split("\n") if "TODO" in line][0]) + 1
        issues.append({
            "title": "TODO comment found",
            "description": "There are TODO comments in the code that should be addressed.",
            "severity": "low",
            "line": todo_line
        })
    
    if language == "JavaScript" and "===" not in content and "==" in content:
        issues.append({
            "title": "Non-strict equality",
            "description": "Using non-strict equality (==) instead of strict equality (===) can lead to unexpected behavior.",
            "severity": "medium",
            "line": "N/A"
        })
    
    if language == "Python" and "except:" in content and "except Exception:" not in content:
        issues.append({
            "title": "Bare except clause",
            "description": "Using bare except clauses can catch unexpected exceptions and hide errors.",
            "severity": "medium",
            "line": "N/A"
        })
    
    # Generate best practices analysis
    best_practices = []
    
    # Add language-specific best practices
    if language == "JavaScript":
        best_practices.extend([
            {
                "title": "Use strict equality",
                "description": "Always use === instead of == for equality comparisons",
                "status": "===" in content
            },
            {
                "title": "Use const/let instead of var",
                "description": "Prefer const and let over var for variable declarations",
                "status": "var " not in content or ("const " in content and "let " in content)
            },
            {
                "title": "Error handling",
                "description": "Implement proper error handling with try/catch blocks",
                "status": "try {" in content and "catch" in content
            }
        ])
    elif language == "Python":
        best_practices.extend([
            {
                "title": "Use meaningful variable names",
                "description": "Variables should have descriptive names",
                "status": True  # Simplified check, would need more sophisticated analysis
            },
            {
                "title": "Proper exception handling",
                "description": "Use specific exception types instead of bare except clauses",
                "status": "except:" not in content or "except Exception:" in content
            },
            {
                "title": "Follow PEP 8 style guide",
                "description": "Code should follow the PEP 8 style guide for Python code",
                "status": True  # Simplified check
            }
        ])
    elif language == "Java":
        best_practices.extend([
            {
                "title": "Use proper access modifiers",
                "description": "Fields and methods should have appropriate access modifiers",
                "status": "private " in content or "protected " in content or "public " in content
            },
            {
                "title": "Include Javadoc comments",
                "description": "Public methods should include Javadoc comments",
                "status": "/**" in content and "*/" in content
            },
            {
                "title": "Proper exception handling",
                "description": "Exceptions should be either handled or declared",
                "status": "try {" in content and "catch" in content
            }
        ])
    
    # Add generic best practices
    best_practices.extend([
        {
            "title": "Code is modular",
            "description": "Code is divided into manageable, focused modules/functions",
            "status": loc < 300
        },
        {
            "title": "Comment quality",
            "description": "Comments explain 'why' not 'what' and are kept updated",
            "status": True  # Simplified check
        }
    ])
    
    return {
        "quality_score": quality_score,
        "issues": issues,
        "best_practices": best_practices
    }