import streamlit as st
import pandas as pd
import numpy as np
import time
import re
import json
import os
import base64
import random
from model_interface import ModelInterface
from io import StringIO

# Set page configuration
st.set_page_config(
    page_title="Repository Analysis",
    page_icon="📁",
    layout="wide"
)

# Define custom CSS
st.markdown("""
<style>
    .file-card {
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        border: 1px solid #ddd;
        background-color: #f8f9fa;
    }
    .file-name {
        font-weight: bold;
        color: #333;
        margin-bottom: 5px;
    }
    .file-path {
        font-size: 12px;
        color: #666;
        margin-bottom: 10px;
    }
    .file-metrics {
        display: flex;
        flex-wrap: wrap;
        margin-bottom: 10px;
    }
    .file-metric {
        padding: 3px 10px;
        margin-right: 10px;
        margin-bottom: 5px;
        border-radius: 12px;
        font-size: 12px;
        background-color: #e0e0e0;
    }
    .file-description {
        margin-top: 10px;
        font-size: 14px;
    }
    .insight-card {
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 4px solid #2196f3;
        background-color: #e3f2fd;
    }
    .insight-title {
        font-weight: bold;
        color: #333;
        margin-bottom: 5px;
    }
    .quality-score {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        margin-right: 10px;
    }
    .quality-score-container {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }
    .quality-label {
        font-size: 16px;
        font-weight: bold;
    }
    .repo-metric-card {
        border-radius: 5px;
        padding: 15px;
        text-align: center;
        background-color: #f0f0f0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        height: 100%;
    }
    .repo-metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #333;
        margin: 10px 0;
    }
    .repo-metric-label {
        font-size: 14px;
        color: #666;
    }
    .issue-container {
        margin-top: 20px;
    }
    .issue-card {
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 5px;
        background-color: #fff8e1;
        border-left: 4px solid #ffc107;
    }
    .issue-title {
        font-weight: bold;
        color: #333;
    }
    .code-snippet {
        padding: 10px;
        font-family: monospace;
        background-color: #f5f5f5;
        border-radius: 5px;
        overflow-x: auto;
        margin: 10px 0;
    }
    .low-score {
        background-color: #f44336;
    }
    .medium-score {
        background-color: #ff9800;
    }
    .high-score {
        background-color: #4caf50;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'model_interface' not in st.session_state:
    st.session_state.model_interface = ModelInterface()
    
if 'repo_analysis' not in st.session_state:
    st.session_state.repo_analysis = None
    
if 'files_analysis' not in st.session_state:
    st.session_state.files_analysis = {}
    
if 'current_file' not in st.session_state:
    st.session_state.current_file = None
    
if 'file_contents' not in st.session_state:
    st.session_state.file_contents = {}

# Helper functions
def get_score_class(score):
    """Get the CSS class for a score"""
    if score >= 8:
        return "high-score"
    elif score >= 5:
        return "medium-score"
    else:
        return "low-score"

def parse_repository_contents(file_contents):
    """Parse the file contents to extract repository information"""
    files = []
    for file_path, content in file_contents.items():
        # Skip directories
        if not content:
            continue
        
        file_info = {
            "path": file_path,
            "name": os.path.basename(file_path),
            "extension": os.path.splitext(file_path)[1].lower(),
            "content": content,
            "size": len(content)
        }
        
        # Get language based on file extension
        ext = file_info["extension"]
        if ext in ['.py']:
            file_info["language"] = "Python"
        elif ext in ['.js']:
            file_info["language"] = "JavaScript"
        elif ext in ['.ts']:
            file_info["language"] = "TypeScript"
        elif ext in ['.java']:
            file_info["language"] = "Java"
        elif ext in ['.go']:
            file_info["language"] = "Go"
        elif ext in ['.cs']:
            file_info["language"] = "C#"
        elif ext in ['.cpp', '.cc', '.c', '.h']:
            file_info["language"] = "C/C++"
        elif ext in ['.rb']:
            file_info["language"] = "Ruby"
        elif ext in ['.php']:
            file_info["language"] = "PHP"
        elif ext in ['.swift']:
            file_info["language"] = "Swift"
        elif ext in ['.rs']:
            file_info["language"] = "Rust"
        elif ext in ['.sql']:
            file_info["language"] = "SQL"
        elif ext in ['.html', '.htm']:
            file_info["language"] = "HTML"
        elif ext in ['.css', '.scss', '.sass']:
            file_info["language"] = "CSS"
        elif ext in ['.md', '.markdown']:
            file_info["language"] = "Markdown"
        elif ext in ['.json']:
            file_info["language"] = "JSON"
        elif ext in ['.xml']:
            file_info["language"] = "XML"
        elif ext in ['.yaml', '.yml']:
            file_info["language"] = "YAML"
        else:
            file_info["language"] = "Other"
        
        files.append(file_info)
    
    return files

def analyze_repository(file_contents):
    """Analyze repository structure and quality"""
    if not st.session_state.model_interface.check_openai_status() and not st.session_state.model_interface.check_anthropic_status():
        st.error("No AI services available. Please configure API keys.")
        return None
    
    # Parse repository
    files = parse_repository_contents(file_contents)
    
    # Calculate repository metrics
    languages = {}
    file_count = len(files)
    total_size = 0
    
    for file in files:
        total_size += file["size"]
        if file["language"] in languages:
            languages[file["language"]] += 1
        else:
            languages[file["language"]] = 1
    
    # Create a summary of the repository structure
    file_paths = "\n".join([f"{f['path']} ({f['language']})" for f in files[:20]])
    if len(files) > 20:
        file_paths += f"\n... and {len(files) - 20} more files"
    
    lang_summary = "\n".join([f"{lang}: {count} files" for lang, count in languages.items()])
    
    # Create prompt for repository analysis
    prompt = f"""
    Analyze the following repository structure:
    
    Number of files: {file_count}
    Total size: {total_size} bytes
    
    Language distribution:
    {lang_summary}
    
    Files (top 20):
    {file_paths}
    
    Please provide a comprehensive analysis of this repository including:
    1. Overall repository quality assessment
    2. Repository architecture evaluation
    3. Code organization insights
    4. Potential issues or improvements
    5. Best practices observed
    
    Format your response as a JSON object with the following structure:
    {{
        "quality_score": number from 1-10,
        "overview": "Overall description of the repository",
        "architecture": {{
            "score": number from 1-10,
            "evaluation": "Evaluation of the architecture",
            "patterns": ["pattern1", "pattern2"]
        }},
        "organization": {{
            "score": number from 1-10,
            "evaluation": "Evaluation of code organization",
            "strengths": ["strength1", "strength2"],
            "weaknesses": ["weakness1", "weakness2"]
        }},
        "issues": [
            {{
                "title": "Issue title",
                "description": "Issue description",
                "severity": "high, medium, or low"
            }}
        ],
        "recommendations": [
            "recommendation1",
            "recommendation2"
        ]
    }}
    """
    
    try:
        # Use available model
        provider = "openai" if st.session_state.model_interface.check_openai_status() else "anthropic"
        system_message = "You are an expert code quality analyst specializing in repository structure assessment."
        
        response = st.session_state.model_interface.generate_text(
            prompt=prompt,
            system_message=system_message,
            provider=provider
        )
        
        # Extract JSON from the response
        json_match = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON without the markdown code block
            json_match = re.search(r"({.*})", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response
        
        # Remove any non-JSON text before or after
        cleaned_json = re.sub(r"^[^{]*", "", json_str)
        cleaned_json = re.sub(r"[^}]*$", "", cleaned_json)
        
        # Parse JSON
        analysis = json.loads(cleaned_json)
        
        # Add repository stats
        analysis["stats"] = {
            "file_count": file_count,
            "total_size": total_size,
            "languages": languages
        }
        
        return analysis
    except Exception as e:
        st.error(f"Error analyzing repository: {str(e)}")
        return None

def analyze_file(file_info):
    """Analyze a single file for quality and insights"""
    if not st.session_state.model_interface.check_openai_status() and not st.session_state.model_interface.check_anthropic_status():
        st.error("No AI services available. Please configure API keys.")
        return None
    
    # Extract file details
    file_path = file_info["path"]
    language = file_info["language"]
    content = file_info["content"]
    
    # Create prompt for file analysis
    prompt = f"""
    Analyze the following {language} file:
    
    Path: {file_path}
    
    ```{language.lower()}
    {content[:10000]}  # Limit to first 10,000 characters for token limits
    {'...' if len(content) > 10000 else ''}
    ```
    
    Please provide a comprehensive analysis of this file including:
    1. Overall file quality assessment
    2. Code complexity and maintainability
    3. Documentation quality
    4. Potential issues or improvements
    5. Best practices observed or violated
    
    Format your response as a JSON object with the following structure:
    {{
        "quality_score": number from 1-10,
        "summary": "Brief summary of the file's purpose",
        "complexity": {{
            "score": number from 1-10,
            "evaluation": "Evaluation of code complexity"
        }},
        "documentation": {{
            "score": number from 1-10,
            "evaluation": "Evaluation of documentation quality"
        }},
        "maintainability": {{
            "score": number from 1-10,
            "evaluation": "Evaluation of code maintainability"
        }},
        "issues": [
            {{
                "title": "Issue title",
                "description": "Issue description",
                "severity": "high, medium, or low",
                "line_numbers": [optional list of relevant line numbers]
            }}
        ],
        "best_practices": [
            {{
                "title": "Practice title",
                "observed": true or false,
                "description": "Description of the practice"
            }}
        ],
        "recommendations": [
            "recommendation1",
            "recommendation2"
        ]
    }}
    """
    
    try:
        # Use available model
        provider = "openai" if st.session_state.model_interface.check_openai_status() else "anthropic"
        system_message = f"You are an expert {language} developer specializing in code quality analysis."
        
        response = st.session_state.model_interface.generate_text(
            prompt=prompt,
            system_message=system_message,
            provider=provider
        )
        
        # Extract JSON from the response
        json_match = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON without the markdown code block
            json_match = re.search(r"({.*})", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response
        
        # Remove any non-JSON text before or after
        cleaned_json = re.sub(r"^[^{]*", "", json_str)
        cleaned_json = re.sub(r"[^}]*$", "", cleaned_json)
        
        # Parse JSON
        analysis = json.loads(cleaned_json)
        
        # Add file info
        analysis["file_info"] = {
            "path": file_path,
            "name": os.path.basename(file_path),
            "language": language,
            "size": len(content)
        }
        
        return analysis
    except Exception as e:
        st.error(f"Error analyzing file: {str(e)}")
        return None

# Sample code repositories for demos
SAMPLE_REPOSITORIES = {
    "E-commerce API": {
        "src/api/index.js": """
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const morgan = require('morgan');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');

const productRoutes = require('./routes/products');
const userRoutes = require('./routes/users');
const orderRoutes = require('./routes/orders');
const authRoutes = require('./routes/auth');
const cartRoutes = require('./routes/cart');

const { errorHandler } = require('./middleware/errorHandler');
const { authMiddleware } = require('./middleware/auth');

const app = express();
const PORT = process.env.PORT || 3000;

// Apply security middleware
app.use(helmet());
app.use(cors());

// Apply rate limiting
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});
app.use('/api/', apiLimiter);

// Logging
app.use(morgan('dev'));

// Parse JSON bodies
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// API Routes
app.use('/api/auth', authRoutes);
app.use('/api/products', productRoutes);
app.use('/api/users', authMiddleware, userRoutes);
app.use('/api/orders', authMiddleware, orderRoutes);
app.use('/api/cart', authMiddleware, cartRoutes);

// Error handling middleware
app.use(errorHandler);

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = app;
""",
        "src/api/routes/products.js": """
const express = require('express');
const router = express.Router();
const ProductController = require('../controllers/productController');
const { adminMiddleware } = require('../middleware/auth');

/**
 * @route GET /api/products
 * @desc Get all products with optional filtering
 * @access Public
 */
router.get('/', ProductController.getAllProducts);

/**
 * @route GET /api/products/:id
 * @desc Get a single product by ID
 * @access Public
 */
router.get('/:id', ProductController.getProductById);

/**
 * @route POST /api/products
 * @desc Create a new product
 * @access Admin only
 */
router.post('/', adminMiddleware, ProductController.createProduct);

/**
 * @route PUT /api/products/:id
 * @desc Update a product
 * @access Admin only
 */
router.put('/:id', adminMiddleware, ProductController.updateProduct);

/**
 * @route DELETE /api/products/:id
 * @desc Delete a product
 * @access Admin only
 */
router.delete('/:id', adminMiddleware, ProductController.deleteProduct);

/**
 * @route GET /api/products/category/:category
 * @desc Get products by category
 * @access Public
 */
router.get('/category/:category', ProductController.getProductsByCategory);

/**
 * @route GET /api/products/search/:query
 * @desc Search products
 * @access Public
 */
router.get('/search/:query', ProductController.searchProducts);

module.exports = router;
""",
        "src/api/controllers/productController.js": """
const Product = require('../models/Product');
const { asyncHandler } = require('../middleware/asyncHandler');
const AppError = require('../utils/appError');

// Get all products with filtering, sorting, and pagination
exports.getAllProducts = asyncHandler(async (req, res) => {
  const page = parseInt(req.query.page, 10) || 1;
  const limit = parseInt(req.query.limit, 10) || 10;
  const skip = (page - 1) * limit;
  
  // Build query
  let query = {};
  
  // Filter by category if provided
  if (req.query.category) {
    query.category = req.query.category;
  }
  
  // Filter by price range if provided
  if (req.query.minPrice || req.query.maxPrice) {
    query.price = {};
    if (req.query.minPrice) query.price.$gte = parseFloat(req.query.minPrice);
    if (req.query.maxPrice) query.price.$lte = parseFloat(req.query.maxPrice);
  }
  
  // Filter by availability
  if (req.query.inStock === 'true') {
    query.stockQuantity = { $gt: 0 };
  }
  
  // Execute query with pagination
  const products = await Product.find(query)
    .skip(skip)
    .limit(limit)
    .sort(req.query.sort || '-createdAt');
  
  // Get total count for pagination
  const totalProducts = await Product.countDocuments(query);
  
  res.status(200).json({
    success: true,
    count: products.length,
    totalPages: Math.ceil(totalProducts / limit),
    currentPage: page,
    data: products
  });
});

// Get single product by ID
exports.getProductById = asyncHandler(async (req, res, next) => {
  const product = await Product.findById(req.params.id);
  
  if (!product) {
    return next(new AppError(`Product not found with id ${req.params.id}`, 404));
  }
  
  res.status(200).json({
    success: true,
    data: product
  });
});

// Create new product
exports.createProduct = asyncHandler(async (req, res) => {
  const product = await Product.create(req.body);
  
  res.status(201).json({
    success: true,
    data: product
  });
});

// Update product
exports.updateProduct = asyncHandler(async (req, res, next) => {
  let product = await Product.findById(req.params.id);
  
  if (!product) {
    return next(new AppError(`Product not found with id ${req.params.id}`, 404));
  }
  
  product = await Product.findByIdAndUpdate(req.params.id, req.body, {
    new: true,
    runValidators: true
  });
  
  res.status(200).json({
    success: true,
    data: product
  });
});

// Delete product
exports.deleteProduct = asyncHandler(async (req, res, next) => {
  const product = await Product.findById(req.params.id);
  
  if (!product) {
    return next(new AppError(`Product not found with id ${req.params.id}`, 404));
  }
  
  await product.remove();
  
  res.status(200).json({
    success: true,
    data: {}
  });
});

// Get products by category
exports.getProductsByCategory = asyncHandler(async (req, res) => {
  const products = await Product.find({ category: req.params.category });
  
  res.status(200).json({
    success: true,
    count: products.length,
    data: products
  });
});

// Search products
exports.searchProducts = asyncHandler(async (req, res) => {
  const query = req.params.query;
  
  const products = await Product.find({
    $or: [
      { name: { $regex: query, $options: 'i' } },
      { description: { $regex: query, $options: 'i' } },
      { brand: { $regex: query, $options: 'i' } }
    ]
  });
  
  res.status(200).json({
    success: true,
    count: products.length,
    data: products
  });
});
""",
        "src/api/models/Product.js": """
const mongoose = require('mongoose');

const ProductSchema = new mongoose.Schema({
  name: {
    type: String,
    required: [true, 'Please add a product name'],
    trim: true,
    maxlength: [100, 'Name cannot be more than 100 characters']
  },
  description: {
    type: String,
    required: [true, 'Please add a description'],
    maxlength: [1000, 'Description cannot be more than 1000 characters']
  },
  price: {
    type: Number,
    required: [true, 'Please add a price'],
    min: [0, 'Price must be positive']
  },
  category: {
    type: String,
    required: [true, 'Please add a category'],
    enum: [
      'electronics',
      'clothing',
      'furniture',
      'books',
      'beauty',
      'sports',
      'food',
      'toys',
      'other'
    ]
  },
  brand: {
    type: String,
    required: false
  },
  stockQuantity: {
    type: Number,
    required: [true, 'Please add a stock quantity'],
    min: [0, 'Stock quantity cannot be negative'],
    default: 0
  },
  images: {
    type: [String],
    default: ['default.jpg']
  },
  featured: {
    type: Boolean,
    default: false
  },
  rating: {
    type: Number,
    min: [0, 'Rating must be at least 0'],
    max: [5, 'Rating cannot be more than 5'],
    default: 0
  },
  numReviews: {
    type: Number,
    default: 0
  },
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
});

// Method to update the 'updatedAt' field on save
ProductSchema.pre('save', function(next) {
  this.updatedAt = Date.now();
  next();
});

// Create a text index for search functionality
ProductSchema.index({ name: 'text', description: 'text', brand: 'text' });

module.exports = mongoose.model('Product', ProductSchema);
""",
        "src/api/middleware/auth.js": """
const jwt = require('jsonwebtoken');
const asyncHandler = require('./asyncHandler');
const AppError = require('../utils/appError');
const User = require('../models/User');

// Protect routes
exports.authMiddleware = asyncHandler(async (req, res, next) => {
  let token;
  
  // Check for token in headers
  if (req.headers.authorization && req.headers.authorization.startsWith('Bearer')) {
    token = req.headers.authorization.split(' ')[1];
  } else if (req.cookies && req.cookies.token) {
    // Check for token in cookies
    token = req.cookies.token;
  }
  
  // Make sure token exists
  if (!token) {
    return next(new AppError('Not authorized to access this route', 401));
  }
  
  try {
    // Verify token
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    
    // Get user from the token
    req.user = await User.findById(decoded.id);
    
    next();
  } catch (err) {
    return next(new AppError('Not authorized to access this route', 401));
  }
});

// Grant access to specific roles
exports.authorizeRoles = (...roles) => {
  return (req, res, next) => {
    if (!roles.includes(req.user.role)) {
      return next(new AppError(`User role ${req.user.role} is not authorized to access this route`, 403));
    }
    next();
  };
};

// Admin only middleware
exports.adminMiddleware = [
  exports.authMiddleware,
  exports.authorizeRoles('admin')
];
""",
        "src/api/utils/appError.js": """
class AppError extends Error {
  constructor(message, statusCode) {
    super(message);
    this.statusCode = statusCode;
    this.status = `${statusCode}`.startsWith('4') ? 'fail' : 'error';
    this.isOperational = true;

    Error.captureStackTrace(this, this.constructor);
  }
}

module.exports = AppError;
""",
    },
    "Data Analysis Library": {
        "data_processor/__init__.py": """
"""
"""
Data Processor Library

A comprehensive toolkit for data processing, transformation, and analysis.
"""

from .processor import DataProcessor
from .transformers import DataTransformer, NumericTransformer, CategoricalTransformer, TextTransformer
from .validators import DataValidator, SchemaValidator, RangeValidator, FormatValidator
from .loaders import CsvLoader, JsonLoader, DatabaseLoader, ExcelLoader
from .exporters import CsvExporter, JsonExporter, DatabaseExporter, ExcelExporter
from .analyzers import DataAnalyzer, StatisticalAnalyzer, CorrelationAnalyzer, OutlierDetector
from .visualization import DataVisualizer, TimeSeriesPlotter, DistributionPlotter, CorrelationPlotter

__version__ = "0.1.0"
""",
        "data_processor/processor.py": """
"""
Main processor module that orchestrates data processing workflows.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union, Callable
import logging

from .transformers import DataTransformer
from .validators import DataValidator
from .analyzers import DataAnalyzer

# Configure logging
logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Main class for orchestrating data processing workflows.
    
    This class serves as the central coordinator for data processing operations,
    including loading, validation, transformation, analysis, and export.
    
    Attributes:
        data (pd.DataFrame): The data being processed
        transformers (List[DataTransformer]): List of transformers to apply
        validators (List[DataValidator]): List of validators to apply
        analyzers (List[DataAnalyzer]): List of analyzers to apply
    """
    
    def __init__(self, data: Optional[pd.DataFrame] = None):
        """
        Initialize a new DataProcessor.
        
        Args:
            data: Optional initial data to process
        """
        self.data = data if data is not None else pd.DataFrame()
        self.transformers = []
        self.validators = []
        self.analyzers = []
        self.processing_history = []
        logger.info("DataProcessor initialized")
        
    def load_data(self, loader: Any) -> "DataProcessor":
        """
        Load data using the provided loader.
        
        Args:
            loader: Data loader instance
            
        Returns:
            Self for method chaining
        """
        self.data = loader.load()
        self.processing_history.append({
            "operation": "load_data",
            "loader": loader.__class__.__name__,
            "rows": len(self.data),
            "columns": list(self.data.columns)
        })
        logger.info(f"Loaded data with {len(self.data)} rows and {len(self.data.columns)} columns")
        return self
        
    def add_transformer(self, transformer: DataTransformer) -> "DataProcessor":
        """
        Add a transformer to the processing pipeline.
        
        Args:
            transformer: Transformer to add
            
        Returns:
            Self for method chaining
        """
        self.transformers.append(transformer)
        logger.info(f"Added transformer: {transformer.__class__.__name__}")
        return self
        
    def add_validator(self, validator: DataValidator) -> "DataProcessor":
        """
        Add a validator to the processing pipeline.
        
        Args:
            validator: Validator to add
            
        Returns:
            Self for method chaining
        """
        self.validators.append(validator)
        logger.info(f"Added validator: {validator.__class__.__name__}")
        return self
        
    def add_analyzer(self, analyzer: DataAnalyzer) -> "DataProcessor":
        """
        Add an analyzer to the processing pipeline.
        
        Args:
            analyzer: Analyzer to add
            
        Returns:
            Self for method chaining
        """
        self.analyzers.append(analyzer)
        logger.info(f"Added analyzer: {analyzer.__class__.__name__}")
        return self
        
    def transform(self) -> "DataProcessor":
        """
        Apply all transformers to the data.
        
        Returns:
            Self for method chaining
        """
        for transformer in self.transformers:
            self.data = transformer.transform(self.data)
            self.processing_history.append({
                "operation": "transform",
                "transformer": transformer.__class__.__name__
            })
        logger.info(f"Applied {len(self.transformers)} transformers")
        return self
        
    def validate(self) -> Dict[str, Any]:
        """
        Apply all validators to the data.
        
        Returns:
            Dictionary with validation results
        """
        results = {}
        for validator in self.validators:
            result = validator.validate(self.data)
            results[validator.__class__.__name__] = result
            self.processing_history.append({
                "operation": "validate",
                "validator": validator.__class__.__name__,
                "result": result
            })
        logger.info(f"Applied {len(self.validators)} validators")
        return results
        
    def analyze(self) -> Dict[str, Any]:
        """
        Apply all analyzers to the data.
        
        Returns:
            Dictionary with analysis results
        """
        results = {}
        for analyzer in self.analyzers:
            result = analyzer.analyze(self.data)
            results[analyzer.__class__.__name__] = result
            self.processing_history.append({
                "operation": "analyze",
                "analyzer": analyzer.__class__.__name__
            })
        logger.info(f"Applied {len(self.analyzers)} analyzers")
        return results
        
    def export_data(self, exporter: Any) -> Any:
        """
        Export data using the provided exporter.
        
        Args:
            exporter: Data exporter instance
            
        Returns:
            Result of the export operation
        """
        result = exporter.export(self.data)
        self.processing_history.append({
            "operation": "export_data",
            "exporter": exporter.__class__.__name__
        })
        logger.info(f"Exported data using {exporter.__class__.__name__}")
        return result
        
    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get the processing history.
        
        Returns:
            List of processing steps
        """
        return self.processing_history
        
    def get_data_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current data.
        
        Returns:
            Dictionary with data summary
        """
        summary = {
            "rows": len(self.data),
            "columns": list(self.data.columns),
            "dtypes": {col: str(dtype) for col, dtype in self.data.dtypes.items()},
            "missing_values": self.data.isnull().sum().to_dict(),
            "memory_usage": self.data.memory_usage(deep=True).sum()
        }
        logger.info(f"Generated data summary")
        return summary
""",
        "data_processor/transformers.py": """
"""
Data transformation modules for various data types.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union, Callable
from abc import ABC, abstractmethod
import logging

# Configure logging
logger = logging.getLogger(__name__)

class DataTransformer(ABC):
    """
    Abstract base class for data transformers.
    
    All data transformers should inherit from this class and implement
    the transform method.
    """
    
    @abstractmethod
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the input data.
        
        Args:
            data: Input DataFrame to transform
            
        Returns:
            Transformed DataFrame
        """
        pass

    def fit(self, data: pd.DataFrame) -> "DataTransformer":
        """
        Fit the transformer to the data (if needed).
        
        This method is optional and does nothing by default.
        Subclasses that need to learn parameters from the data
        should override this method.
        
        Args:
            data: Input DataFrame to fit to
            
        Returns:
            Self for method chaining
        """
        return self
        
    def fit_transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Fit the transformer to the data and then transform it.
        
        Args:
            data: Input DataFrame to fit and transform
            
        Returns:
            Transformed DataFrame
        """
        self.fit(data)
        return self.transform(data)

class NumericTransformer(DataTransformer):
    """
    Transformer for numeric data operations.
    
    This transformer handles operations like scaling, normalization,
    and other numeric transformations.
    """
    
    def __init__(self, 
                 columns: List[str],
                 operation: str = "scale",
                 params: Optional[Dict[str, Any]] = None):
        """
        Initialize a new NumericTransformer.
        
        Args:
            columns: List of column names to transform
            operation: Transformation operation to apply
            params: Additional parameters for the operation
        """
        self.columns = columns
        self.operation = operation
        self.params = params or {}
        self.fitted_params = {}
        logger.info(f"NumericTransformer initialized with operation: {operation}")
        
    def fit(self, data: pd.DataFrame) -> "NumericTransformer":
        """
        Fit the transformer to the data.
        
        For operations like scaling, this computes the necessary
        statistics (e.g., mean and standard deviation).
        
        Args:
            data: Input DataFrame to fit to
            
        Returns:
            Self for method chaining
        """
        # Check that all columns exist
        missing_cols = [col for col in self.columns if col not in data.columns]
        if missing_cols:
            raise ValueError(f"Columns not found in data: {missing_cols}")
        
        if self.operation == "scale":
            # Compute mean and std for scaling
            self.fitted_params["mean"] = {col: data[col].mean() for col in self.columns}
            self.fitted_params["std"] = {col: data[col].std() for col in self.columns}
            
        elif self.operation == "normalize":
            # Compute min and max for normalization
            self.fitted_params["min"] = {col: data[col].min() for col in self.columns}
            self.fitted_params["max"] = {col: data[col].max() for col in self.columns}
            
        elif self.operation == "log":
            # Nothing to fit
            pass
            
        logger.info(f"NumericTransformer fitted for {len(self.columns)} columns")
        return self
        
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the numeric columns.
        
        Args:
            data: Input DataFrame to transform
            
        Returns:
            DataFrame with transformed columns
        """
        # Make a copy to avoid modifying the original
        result = data.copy()
        
        # Apply the chosen operation
        if self.operation == "scale":
            if not self.fitted_params:
                raise ValueError("Transformer not fitted. Call fit() first.")
            
            for col in self.columns:
                mean = self.fitted_params["mean"][col]
                std = self.fitted_params["std"][col]
                result[col] = (result[col] - mean) / (std if std > 0 else 1)
                
        elif self.operation == "normalize":
            if not self.fitted_params:
                raise ValueError("Transformer not fitted. Call fit() first.")
            
            for col in self.columns:
                min_val = self.fitted_params["min"][col]
                max_val = self.fitted_params["max"][col]
                range_val = max_val - min_val
                result[col] = (result[col] - min_val) / (range_val if range_val > 0 else 1)
                
        elif self.operation == "log":
            for col in self.columns:
                # Handle non-positive values
                if (result[col] <= 0).any():
                    min_val = result[col].min()
                    offset = abs(min_val) + 1 if min_val <= 0 else 0
                    result[col] = np.log(result[col] + offset)
                else:
                    result[col] = np.log(result[col])
        
        logger.info(f"NumericTransformer applied {self.operation} to {len(self.columns)} columns")
        return result

class CategoricalTransformer(DataTransformer):
    """
    Transformer for categorical data operations.
    
    This transformer handles operations like one-hot encoding,
    label encoding, and other categorical transformations.
    """
    
    def __init__(self, 
                 columns: List[str],
                 operation: str = "one_hot",
                 params: Optional[Dict[str, Any]] = None):
        """
        Initialize a new CategoricalTransformer.
        
        Args:
            columns: List of column names to transform
            operation: Transformation operation to apply
            params: Additional parameters for the operation
        """
        self.columns = columns
        self.operation = operation
        self.params = params or {}
        self.fitted_params = {}
        logger.info(f"CategoricalTransformer initialized with operation: {operation}")
        
    def fit(self, data: pd.DataFrame) -> "CategoricalTransformer":
        """
        Fit the transformer to the data.
        
        For operations like label encoding, this determines
        the unique categories and their mappings.
        
        Args:
            data: Input DataFrame to fit to
            
        Returns:
            Self for method chaining
        """
        # Check that all columns exist
        missing_cols = [col for col in self.columns if col not in data.columns]
        if missing_cols:
            raise ValueError(f"Columns not found in data: {missing_cols}")
        
        if self.operation == "label_encode":
            # Create mapping from categories to integers
            self.fitted_params["mappings"] = {}
            for col in self.columns:
                unique_values = data[col].dropna().unique()
                self.fitted_params["mappings"][col] = {
                    val: i for i, val in enumerate(unique_values)
                }
        
        logger.info(f"CategoricalTransformer fitted for {len(self.columns)} columns")
        return self
        
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the categorical columns.
        
        Args:
            data: Input DataFrame to transform
            
        Returns:
            DataFrame with transformed columns
        """
        # Make a copy to avoid modifying the original
        result = data.copy()
        
        # Apply the chosen operation
        if self.operation == "one_hot":
            # Use pandas get_dummies for one-hot encoding
            dummies = pd.get_dummies(result[self.columns], drop_first=self.params.get("drop_first", False))
            # Drop original columns and join encoded ones
            result = result.drop(columns=self.columns)
            result = pd.concat([result, dummies], axis=1)
                
        elif self.operation == "label_encode":
            if not self.fitted_params:
                raise ValueError("Transformer not fitted. Call fit() first.")
            
            for col in self.columns:
                mapping = self.fitted_params["mappings"][col]
                # Apply mapping and handle unknown values
                result[col] = result[col].map(mapping)
                if self.params.get("handle_unknown", "error") == "ignore":
                    result[col] = result[col].fillna(-1).astype(int)
                
        logger.info(f"CategoricalTransformer applied {self.operation} to {len(self.columns)} columns")
        return result

class TextTransformer(DataTransformer):
    """
    Transformer for text data operations.
    
    This transformer handles operations like tokenization,
    stemming, and other text transformations.
    """
    
    def __init__(self, 
                 columns: List[str],
                 operation: str = "lowercase",
                 params: Optional[Dict[str, Any]] = None):
        """
        Initialize a new TextTransformer.
        
        Args:
            columns: List of column names to transform
            operation: Transformation operation to apply
            params: Additional parameters for the operation
        """
        self.columns = columns
        self.operation = operation
        self.params = params or {}
        logger.info(f"TextTransformer initialized with operation: {operation}")
        
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the text columns.
        
        Args:
            data: Input DataFrame to transform
            
        Returns:
            DataFrame with transformed columns
        """
        # Make a copy to avoid modifying the original
        result = data.copy()
        
        # Apply the chosen operation
        if self.operation == "lowercase":
            for col in self.columns:
                result[col] = result[col].str.lower()
                
        elif self.operation == "strip":
            for col in self.columns:
                result[col] = result[col].str.strip()
                
        elif self.operation == "replace":
            pattern = self.params.get("pattern", "")
            replacement = self.params.get("replacement", "")
            if not pattern:
                raise ValueError("Pattern parameter required for replace operation")
            
            for col in self.columns:
                result[col] = result[col].str.replace(pattern, replacement, regex=True)
        
        logger.info(f"TextTransformer applied {self.operation} to {len(self.columns)} columns")
        return result
""",
        "data_processor/validators.py": """
"""
Data validation modules for various validation rules.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union, Callable
from abc import ABC, abstractmethod
import logging
import re

# Configure logging
logger = logging.getLogger(__name__)

class DataValidator(ABC):
    """
    Abstract base class for data validators.
    
    All data validators should inherit from this class and implement
    the validate method.
    """
    
    @abstractmethod
    def validate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate the input data.
        
        Args:
            data: Input DataFrame to validate
            
        Returns:
            Dictionary with validation results
        """
        pass

class SchemaValidator(DataValidator):
    """
    Validator for checking data schema conformity.
    
    This validator checks that the data conforms to a specified schema,
    including column presence, data types, and optionally non-null constraints.
    """
    
    def __init__(self, 
                 schema: Dict[str, Any],
                 require_all_columns: bool = True,
                 allow_extra_columns: bool = False):
        """
        Initialize a new SchemaValidator.
        
        Args:
            schema: Dictionary mapping column names to expected data types
            require_all_columns: Whether all schema columns must be present
            allow_extra_columns: Whether extra columns not in schema are allowed
        """
        self.schema = schema
        self.require_all_columns = require_all_columns
        self.allow_extra_columns = allow_extra_columns
        logger.info(f"SchemaValidator initialized with {len(schema)} columns")
        
    def validate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate the data against the schema.
        
        Args:
            data: Input DataFrame to validate
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check for required columns
        if self.require_all_columns:
            missing_cols = [col for col in self.schema if col not in data.columns]
            if missing_cols:
                results["valid"] = False
                results["errors"].append({
                    "type": "missing_columns",
                    "columns": missing_cols
                })
        
        # Check for extra columns
        if not self.allow_extra_columns:
            extra_cols = [col for col in data.columns if col not in self.schema]
            if extra_cols:
                results["valid"] = False
                results["errors"].append({
                    "type": "extra_columns",
                    "columns": extra_cols
                })
        
        # Check column data types
        dtype_errors = []
        for col, expected_type in self.schema.items():
            if col in data.columns:
                # Get actual type and check compatibility
                actual_type = data[col].dtype
                if not self._check_type_compatibility(actual_type, expected_type):
                    dtype_errors.append({
                        "column": col,
                        "expected_type": str(expected_type),
                        "actual_type": str(actual_type)
                    })
        
        if dtype_errors:
            results["valid"] = False
            results["errors"].append({
                "type": "dtype_mismatch",
                "mismatches": dtype_errors
            })
        
        logger.info(f"Schema validation completed: {'valid' if results['valid'] else 'invalid'}")
        return results
    
    def _check_type_compatibility(self, actual_type, expected_type) -> bool:
        """
        Check if the actual data type is compatible with the expected type.
        
        Args:
            actual_type: Actual data type
            expected_type: Expected data type
            
        Returns:
            True if compatible, False otherwise
        """
        # Convert types to strings for comparison
        actual_str = str(actual_type).lower()
        expected_str = str(expected_type).lower()
        
        # Direct match
        if actual_str == expected_str:
            return True
        
        # Check for broader categories
        if expected_str in ["int", "integer"] and "int" in actual_str:
            return True
        if expected_str in ["float", "double"] and ("float" in actual_str or "double" in actual_str):
            return True
        if expected_str in ["str", "string", "object"] and ("object" in actual_str or "str" in actual_str):
            return True
        if expected_str in ["bool", "boolean"] and ("bool" in actual_str):
            return True
        
        return False

class RangeValidator(DataValidator):
    """
    Validator for checking data values within specified ranges.
    
    This validator checks that the data values in specified columns
    fall within expected ranges.
    """
    
    def __init__(self, 
                 ranges: Dict[str, Dict[str, Any]]):
        """
        Initialize a new RangeValidator.
        
        Args:
            ranges: Dictionary mapping column names to range constraints
                   Each constraint can have 'min', 'max', 'include_min', 'include_max'
        """
        self.ranges = ranges
        logger.info(f"RangeValidator initialized with {len(ranges)} columns")
        
    def validate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate the data against the specified ranges.
        
        Args:
            data: Input DataFrame to validate
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "valid": True,
            "errors": [],
            "column_results": {}
        }
        
        for col, range_spec in self.ranges.items():
            if col not in data.columns:
                results["errors"].append({
                    "type": "missing_column",
                    "column": col
                })
                results["valid"] = False
                continue
            
            # Extract range specifications with defaults
            min_val = range_spec.get("min")
            max_val = range_spec.get("max")
            include_min = range_spec.get("include_min", True)
            include_max = range_spec.get("include_max", True)
            
            # Prepare result for this column
            col_result = {
                "valid": True,
                "out_of_range_count": 0
            }
            
            # Validate minimum
            if min_val is not None:
                if include_min:
                    invalid_mask = data[col] < min_val
                else:
                    invalid_mask = data[col] <= min_val
                
                num_invalid = invalid_mask.sum()
                if num_invalid > 0:
                    col_result["valid"] = False
                    col_result["out_of_range_count"] += num_invalid
                    col_result["min_violations"] = num_invalid
            
            # Validate maximum
            if max_val is not None:
                if include_max:
                    invalid_mask = data[col] > max_val
                else:
                    invalid_mask = data[col] >= max_val
                
                num_invalid = invalid_mask.sum()
                if num_invalid > 0:
                    col_result["valid"] = False
                    col_result["out_of_range_count"] += num_invalid
                    col_result["max_violations"] = num_invalid
            
            # Update overall result
            results["column_results"][col] = col_result
            if not col_result["valid"]:
                results["valid"] = False
        
        logger.info(f"Range validation completed: {'valid' if results['valid'] else 'invalid'}")
        return results

class FormatValidator(DataValidator):
    """
    Validator for checking data format conformity.
    
    This validator checks that the data values in specified columns
    conform to expected formats, such as email, phone number, etc.
    """
    
    # Predefined regex patterns for common formats
    PATTERNS = {
        "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "phone": r"^\+?[0-9]{10,15}$",
        "date_iso": r"^\d{4}-\d{2}-\d{2}$",
        "datetime_iso": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
        "url": r"^(http|https)://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$",
        "zipcode_us": r"^\d{5}(-\d{4})?$"
    }
    
    def __init__(self, 
                 formats: Dict[str, str]):
        """
        Initialize a new FormatValidator.
        
        Args:
            formats: Dictionary mapping column names to format names or regex patterns
        """
        self.formats = formats
        # Compile patterns for efficiency
        self.compiled_patterns = {}
        for col, format_spec in formats.items():
            pattern = self.PATTERNS.get(format_spec, format_spec)
            self.compiled_patterns[col] = re.compile(pattern)
        
        logger.info(f"FormatValidator initialized with {len(formats)} columns")
        
    def validate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate the data against the specified formats.
        
        Args:
            data: Input DataFrame to validate
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "valid": True,
            "errors": [],
            "column_results": {}
        }
        
        for col, pattern in self.compiled_patterns.items():
            if col not in data.columns:
                results["errors"].append({
                    "type": "missing_column",
                    "column": col
                })
                results["valid"] = False
                continue
            
            # Convert column to string for regex validation
            str_series = data[col].astype(str)
            
            # Apply regex validation
            invalid_mask = ~str_series.str.match(pattern)
            
            # Handle NaN values (they don't match any pattern)
            if data[col].isna().any():
                # Adjust mask to not count NaN as invalid
                invalid_mask = invalid_mask & ~data[col].isna()
            
            num_invalid = invalid_mask.sum()
            
            # Prepare result for this column
            col_result = {
                "valid": num_invalid == 0,
                "invalid_count": num_invalid
            }
            
            if num_invalid > 0:
                # Get examples of invalid values (limit to 5)
                invalid_examples = str_series[invalid_mask].head(5).tolist()
                col_result["invalid_examples"] = invalid_examples
            
            # Update overall result
            results["column_results"][col] = col_result
            if not col_result["valid"]:
                results["valid"] = False
        
        logger.info(f"Format validation completed: {'valid' if results['valid'] else 'invalid'}")
        return results
""",
    },
    "Fitness Tracking App": {
        "lib/main.dart": """
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'screens/home_screen.dart';
import 'screens/workout_screen.dart';
import 'screens/nutrition_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/auth_screen.dart';
import 'services/auth_service.dart';
import 'services/workout_service.dart';
import 'services/nutrition_service.dart';
import 'services/user_service.dart';
import 'models/user_model.dart';
import 'theme/app_theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  
  final prefs = await SharedPreferences.getInstance();
  final bool useDarkMode = prefs.getBool('darkMode') ?? false;
  
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (ctx) => AuthService()),
        ChangeNotifierProxyProvider<AuthService, UserService>(
          create: (ctx) => UserService(null, null),
          update: (ctx, auth, previous) => UserService(
            auth.token,
            auth.userId,
          ),
        ),
        ChangeNotifierProxyProvider<UserService, WorkoutService>(
          create: (ctx) => WorkoutService(null, null, null),
          update: (ctx, userService, previous) => WorkoutService(
            userService.token,
            userService.userId,
            userService.user,
          ),
        ),
        ChangeNotifierProxyProvider<UserService, NutritionService>(
          create: (ctx) => NutritionService(null, null, null),
          update: (ctx, userService, previous) => NutritionService(
            userService.token,
            userService.userId,
            userService.user,
          ),
        ),
        ChangeNotifierProvider(
          create: (ctx) => ThemeProvider(useDarkMode ? ThemeMode.dark : ThemeMode.light),
        ),
      ],
      child: FitnessApp(),
    ),
  );
}

class FitnessApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final themeProvider = Provider.of<ThemeProvider>(context);
    
    return MaterialApp(
      title: 'Fitness Tracker',
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: themeProvider.themeMode,
      home: AuthWrapper(),
      routes: {
        HomeScreen.routeName: (ctx) => HomeScreen(),
        WorkoutScreen.routeName: (ctx) => WorkoutScreen(),
        NutritionScreen.routeName: (ctx) => NutritionScreen(),
        ProfileScreen.routeName: (ctx) => ProfileScreen(),
        AuthScreen.routeName: (ctx) => AuthScreen(),
      },
    );
  }
}

class AuthWrapper extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final authService = Provider.of<AuthService>(context);
    
    return StreamBuilder<UserModel?>(
      stream: authService.user,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.active) {
          final UserModel? user = snapshot.data;
          
          if (user == null) {
            return AuthScreen();
          }
          
          // User is logged in
          return HomeScreen();
        }
        
        // Checking authentication status
        return Scaffold(
          body: Center(
            child: CircularProgressIndicator(),
          ),
        );
      },
    );
  }
}

class ThemeProvider with ChangeNotifier {
  ThemeMode _themeMode;
  
  ThemeProvider(this._themeMode);
  
  ThemeMode get themeMode => _themeMode;
  
  bool get isDarkMode => _themeMode == ThemeMode.dark;
  
  Future<void> toggleTheme() async {
    _themeMode = _themeMode == ThemeMode.light ? ThemeMode.dark : ThemeMode.light;
    notifyListeners();
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('darkMode', isDarkMode);
  }
}
""",
        "lib/screens/home_screen.dart": """
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:charts_flutter/flutter.dart' as charts;
import 'package:intl/intl.dart';

import '../widgets/main_drawer.dart';
import '../widgets/workout_summary_card.dart';
import '../widgets/nutrition_summary_card.dart';
import '../widgets/activity_chart.dart';
import '../widgets/goal_progress_card.dart';
import '../services/workout_service.dart';
import '../services/nutrition_service.dart';
import '../services/user_service.dart';
import '../models/workout_model.dart';
import '../models/nutrition_model.dart';
import '../models/user_model.dart';
import 'workout_screen.dart';
import 'nutrition_screen.dart';

class HomeScreen extends StatefulWidget {
  static const routeName = '/home';

  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  bool _isLoading = false;
  List<WorkoutModel> _recentWorkouts = [];
  List<NutritionModel> _recentMeals = [];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final workoutService = Provider.of<WorkoutService>(context, listen: false);
      final nutritionService = Provider.of<NutritionService>(context, listen: false);

      // Fetch recent workouts and meals in parallel
      await Future.wait([
        workoutService.fetchRecentWorkouts().then((workouts) {
          _recentWorkouts = workouts;
        }),
        nutritionService.fetchRecentMeals().then((meals) {
          _recentMeals = meals;
        }),
      ]);
    } catch (error) {
      print('Error loading data: $error');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to load your data. Please try again.'),
          duration: Duration(seconds: 3),
        ),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final userService = Provider.of<UserService>(context);
    final user = userService.user;
    final now = DateTime.now();
    final today = DateFormat('EEEE, MMMM d').format(now);

    return Scaffold(
      appBar: AppBar(
        title: Text('Dashboard'),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: _loadData,
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: [
            Tab(text: 'Daily'),
            Tab(text: 'Weekly'),
            Tab(text: 'Monthly'),
          ],
        ),
      ),
      drawer: MainDrawer(),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadData,
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildWelcomeHeader(user, today),
                    SizedBox(height: 24),
                    _buildGoalProgress(user),
                    SizedBox(height: 24),
                    _buildActivityChart(),
                    SizedBox(height: 24),
                    _buildRecentWorkouts(),
                    SizedBox(height: 24),
                    _buildRecentMeals(),
                  ],
                ),
              ),
            ),
      floatingActionButton: FloatingActionButton(
        child: Icon(Icons.add),
        onPressed: () {
          _showAddActivityDialog(context);
        },
      ),
    );
  }

  Widget _buildWelcomeHeader(UserModel? user, String today) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          children: [
            CircleAvatar(
              radius: 30,
              backgroundImage: user?.profileImageUrl != null
                  ? NetworkImage(user!.profileImageUrl!)
                  : null,
              child: user?.profileImageUrl == null
                  ? Icon(Icons.person, size: 30)
                  : null,
            ),
            SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Hello, ${user?.displayName ?? "Fitness Enthusiast"}!',
                    style: Theme.of(context).textTheme.headline6,
                  ),
                  SizedBox(height: 4),
                  Text(
                    today,
                    style: Theme.of(context).textTheme.subtitle1,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildGoalProgress(UserModel? user) {
    final goals = user?.fitnessGoals ?? [];
    
    if (goals.isEmpty) {
      return Card(
        elevation: 2,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Fitness Goals',
                style: Theme.of(context).textTheme.headline6,
              ),
              SizedBox(height: 16),
              Center(
                child: Text(
                  'You haven\'t set any fitness goals yet.',
                  style: Theme.of(context).textTheme.subtitle1,
                ),
              ),
              SizedBox(height: 8),
              Center(
                child: ElevatedButton(
                  onPressed: () {
                    Navigator.of(context).pushNamed(ProfileScreen.routeName);
                  },
                  child: Text('Set Goals'),
                ),
              ),
            ],
          ),
        ),
      );
    }
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Your Goals',
          style: Theme.of(context).textTheme.headline6,
        ),
        SizedBox(height: 8),
        GridView.builder(
          shrinkWrap: true,
          physics: NeverScrollableScrollPhysics(),
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            childAspectRatio: 1.5,
            crossAxisSpacing: 10,
            mainAxisSpacing: 10,
          ),
          itemCount: goals.length > 4 ? 4 : goals.length,
          itemBuilder: (ctx, index) => GoalProgressCard(goal: goals[index]),
        ),
        if (goals.length > 4)
          Align(
            alignment: Alignment.centerRight,
            child: TextButton(
              onPressed: () {
                Navigator.of(context).pushNamed(ProfileScreen.routeName);
              },
              child: Text('View All Goals'),
            ),
          ),
      ],
    );
  }

  Widget _buildActivityChart() {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Activity Overview',
              style: Theme.of(context).textTheme.headline6,
            ),
            SizedBox(height: 16),
            Container(
              height: 200,
              child: TabBarView(
                controller: _tabController,
                children: [
                  ActivityChart(period: 'daily'),
                  ActivityChart(period: 'weekly'),
                  ActivityChart(period: 'monthly'),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRecentWorkouts() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Recent Workouts',
              style: Theme.of(context).textTheme.headline6,
            ),
            TextButton(
              onPressed: () {
                Navigator.of(context).pushNamed(WorkoutScreen.routeName);
              },
              child: Text('See All'),
            ),
          ],
        ),
        SizedBox(height: 8),
        _recentWorkouts.isEmpty
            ? Center(
                child: Text('No recent workouts found.'),
              )
            : ListView.builder(
                shrinkWrap: true,
                physics: NeverScrollableScrollPhysics(),
                itemCount: _recentWorkouts.length > 3
                    ? 3
                    : _recentWorkouts.length,
                itemBuilder: (ctx, index) => WorkoutSummaryCard(
                  workout: _recentWorkouts[index],
                ),
              ),
      ],
    );
  }

  Widget _buildRecentMeals() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Recent Meals',
              style: Theme.of(context).textTheme.headline6,
            ),
            TextButton(
              onPressed: () {
                Navigator.of(context).pushNamed(NutritionScreen.routeName);
              },
              child: Text('See All'),
            ),
          ],
        ),
        SizedBox(height: 8),
        _recentMeals.isEmpty
            ? Center(
                child: Text('No recent meals found.'),
              )
            : ListView.builder(
                shrinkWrap: true,
                physics: NeverScrollableScrollPhysics(),
                itemCount:
                    _recentMeals.length > 3 ? 3 : _recentMeals.length,
                itemBuilder: (ctx, index) => NutritionSummaryCard(
                  meal: _recentMeals[index],
                ),
              ),
      ],
    );
  }

  void _showAddActivityDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Add Activity'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: Icon(Icons.fitness_center),
              title: Text('Add Workout'),
              onTap: () {
                Navigator.of(ctx).pop();
                Navigator.of(context).pushNamed(WorkoutScreen.routeName, arguments: {'addNew': true});
              },
            ),
            ListTile(
              leading: Icon(Icons.restaurant),
              title: Text('Add Meal'),
              onTap: () {
                Navigator.of(ctx).pop();
                Navigator.of(context).pushNamed(NutritionScreen.routeName, arguments: {'addNew': true});
              },
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(ctx).pop();
            },
            child: Text('Cancel'),
          ),
        ],
      ),
    );
  }
}
""",
        "lib/models/user_model.dart": """
import 'package:cloud_firestore/cloud_firestore.dart';

class UserModel {
  final String id;
  final String email;
  final String? displayName;
  final String? profileImageUrl;
  final DateTime? dateOfBirth;
  final double? height; // in cm
  final double? weight; // in kg
  final String? gender;
  final List<FitnessGoal> fitnessGoals;
  final UserPreferences preferences;
  final UserStats stats;

  UserModel({
    required this.id,
    required this.email,
    this.displayName,
    this.profileImageUrl,
    this.dateOfBirth,
    this.height,
    this.weight,
    this.gender,
    List<FitnessGoal>? fitnessGoals,
    UserPreferences? preferences,
    UserStats? stats,
  })  : this.fitnessGoals = fitnessGoals ?? [],
        this.preferences = preferences ?? UserPreferences(),
        this.stats = stats ?? UserStats();

  factory UserModel.fromFirestore(DocumentSnapshot doc) {
    Map<String, dynamic> data = doc.data() as Map<String, dynamic>;
    
    List<FitnessGoal> goals = [];
    if (data['fitnessGoals'] != null) {
      goals = (data['fitnessGoals'] as List)
          .map((goal) => FitnessGoal.fromMap(goal))
          .toList();
    }
    
    return UserModel(
      id: doc.id,
      email: data['email'] ?? '',
      displayName: data['displayName'],
      profileImageUrl: data['profileImageUrl'],
      dateOfBirth: data['dateOfBirth'] != null
          ? (data['dateOfBirth'] as Timestamp).toDate()
          : null,
      height: data['height']?.toDouble(),
      weight: data['weight']?.toDouble(),
      gender: data['gender'],
      fitnessGoals: goals,
      preferences: data['preferences'] != null
          ? UserPreferences.fromMap(data['preferences'])
          : null,
      stats: data['stats'] != null
          ? UserStats.fromMap(data['stats'])
          : null,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'email': email,
      'displayName': displayName,
      'profileImageUrl': profileImageUrl,
      'dateOfBirth': dateOfBirth != null ? Timestamp.fromDate(dateOfBirth!) : null,
      'height': height,
      'weight': weight,
      'gender': gender,
      'fitnessGoals': fitnessGoals.map((goal) => goal.toMap()).toList(),
      'preferences': preferences.toMap(),
      'stats': stats.toMap(),
    };
  }

  UserModel copyWith({
    String? displayName,
    String? profileImageUrl,
    DateTime? dateOfBirth,
    double? height,
    double? weight,
    String? gender,
    List<FitnessGoal>? fitnessGoals,
    UserPreferences? preferences,
    UserStats? stats,
  }) {
    return UserModel(
      id: this.id,
      email: this.email,
      displayName: displayName ?? this.displayName,
      profileImageUrl: profileImageUrl ?? this.profileImageUrl,
      dateOfBirth: dateOfBirth ?? this.dateOfBirth,
      height: height ?? this.height,
      weight: weight ?? this.weight,
      gender: gender ?? this.gender,
      fitnessGoals: fitnessGoals ?? this.fitnessGoals,
      preferences: preferences ?? this.preferences,
      stats: stats ?? this.stats,
    );
  }

  String get bmi {
    if (height == null || weight == null || height! <= 0) return 'N/A';
    final heightInMeters = height! / 100;
    final bmiValue = weight! / (heightInMeters * heightInMeters);
    return bmiValue.toStringAsFixed(1);
  }

  String get bmiCategory {
    if (height == null || weight == null || height! <= 0) return 'Unknown';
    
    final bmiValue = double.parse(bmi);
    
    if (bmiValue < 18.5) return 'Underweight';
    if (bmiValue < 25) return 'Normal';
    if (bmiValue < 30) return 'Overweight';
    return 'Obese';
  }

  int get age {
    if (dateOfBirth == null) return 0;
    
    final now = DateTime.now();
    int age = now.year - dateOfBirth!.year;
    
    if (now.month < dateOfBirth!.month || 
        (now.month == dateOfBirth!.month && now.day < dateOfBirth!.day)) {
      age--;
    }
    
    return age;
  }
}

class FitnessGoal {
  final String id;
  final String title;
  final String description;
  final DateTime targetDate;
  final double targetValue;
  final double currentValue;
  final String unit;
  final String type; // weight, steps, workout, etc.
  final bool completed;

  FitnessGoal({
    required this.id,
    required this.title,
    required this.description,
    required this.targetDate,
    required this.targetValue,
    required this.currentValue,
    required this.unit,
    required this.type,
    this.completed = false,
  });

  factory FitnessGoal.fromMap(Map<String, dynamic> map) {
    return FitnessGoal(
      id: map['id'] ?? DateTime.now().millisecondsSinceEpoch.toString(),
      title: map['title'] ?? '',
      description: map['description'] ?? '',
      targetDate: map['targetDate'] != null
          ? (map['targetDate'] as Timestamp).toDate()
          : DateTime.now().add(Duration(days: 30)),
      targetValue: map['targetValue']?.toDouble() ?? 0.0,
      currentValue: map['currentValue']?.toDouble() ?? 0.0,
      unit: map['unit'] ?? '',
      type: map['type'] ?? '',
      completed: map['completed'] ?? false,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'targetDate': Timestamp.fromDate(targetDate),
      'targetValue': targetValue,
      'currentValue': currentValue,
      'unit': unit,
      'type': type,
      'completed': completed,
    };
  }

  double get progressPercentage {
    if (targetValue == 0) return 0;
    
    // For weight loss, the progress is inverted
    if (type == 'weight' && targetValue < currentValue) {
      final startValue = currentValue * 2 - targetValue; // Calculate the starting point
      final totalChange = startValue - targetValue;
      final currentChange = startValue - currentValue;
      return (currentChange / totalChange).clamp(0.0, 1.0);
    }
    
    return (currentValue / targetValue).clamp(0.0, 1.0);
  }

  FitnessGoal copyWith({
    String? title,
    String? description,
    DateTime? targetDate,
    double? targetValue,
    double? currentValue,
    String? unit,
    String? type,
    bool? completed,
  }) {
    return FitnessGoal(
      id: this.id,
      title: title ?? this.title,
      description: description ?? this.description,
      targetDate: targetDate ?? this.targetDate,
      targetValue: targetValue ?? this.targetValue,
      currentValue: currentValue ?? this.currentValue,
      unit: unit ?? this.unit,
      type: type ?? this.type,
      completed: completed ?? this.completed,
    );
  }
}

class UserPreferences {
  final bool useDarkMode;
  final String unitSystem; // metric or imperial
  final List<String> workoutPreferences;
  final List<String> dietaryRestrictions;
  final Map<String, bool> notifications;

  UserPreferences({
    this.useDarkMode = false,
    this.unitSystem = 'metric',
    List<String>? workoutPreferences,
    List<String>? dietaryRestrictions,
    Map<String, bool>? notifications,
  })  : this.workoutPreferences = workoutPreferences ?? [],
        this.dietaryRestrictions = dietaryRestrictions ?? [],
        this.notifications = notifications ?? {
          'workoutReminders': true,
          'mealReminders': true,
          'goalUpdates': true,
          'weeklyRecap': true,
        };

  factory UserPreferences.fromMap(Map<String, dynamic> map) {
    return UserPreferences(
      useDarkMode: map['useDarkMode'] ?? false,
      unitSystem: map['unitSystem'] ?? 'metric',
      workoutPreferences: map['workoutPreferences'] != null
          ? List<String>.from(map['workoutPreferences'])
          : null,
      dietaryRestrictions: map['dietaryRestrictions'] != null
          ? List<String>.from(map['dietaryRestrictions'])
          : null,
      notifications: map['notifications'] != null
          ? Map<String, bool>.from(map['notifications'])
          : null,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'useDarkMode': useDarkMode,
      'unitSystem': unitSystem,
      'workoutPreferences': workoutPreferences,
      'dietaryRestrictions': dietaryRestrictions,
      'notifications': notifications,
    };
  }

  UserPreferences copyWith({
    bool? useDarkMode,
    String? unitSystem,
    List<String>? workoutPreferences,
    List<String>? dietaryRestrictions,
    Map<String, bool>? notifications,
  }) {
    return UserPreferences(
      useDarkMode: useDarkMode ?? this.useDarkMode,
      unitSystem: unitSystem ?? this.unitSystem,
      workoutPreferences: workoutPreferences ?? this.workoutPreferences,
      dietaryRestrictions: dietaryRestrictions ?? this.dietaryRestrictions,
      notifications: notifications ?? this.notifications,
    );
  }
}

class UserStats {
  final int totalWorkouts;
  final int workoutStreak;
  final Duration totalWorkoutTime;
  final double totalCaloriesBurned;
  final double totalDistanceCovered; // in km
  final Map<String, int> workoutTypeCount;
  final Map<String, double> nutritionAverages;

  UserStats({
    this.totalWorkouts = 0,
    this.workoutStreak = 0,
    Duration? totalWorkoutTime,
    this.totalCaloriesBurned = 0,
    this.totalDistanceCovered = 0,
    Map<String, int>? workoutTypeCount,
    Map<String, double>? nutritionAverages,
  })  : this.totalWorkoutTime = totalWorkoutTime ?? Duration.zero,
        this.workoutTypeCount = workoutTypeCount ?? {},
        this.nutritionAverages = nutritionAverages ?? {};

  factory UserStats.fromMap(Map<String, dynamic> map) {
    return UserStats(
      totalWorkouts: map['totalWorkouts'] ?? 0,
      workoutStreak: map['workoutStreak'] ?? 0,
      totalWorkoutTime: map['totalWorkoutTimeMinutes'] != null
          ? Duration(minutes: map['totalWorkoutTimeMinutes'])
          : null,
      totalCaloriesBurned: map['totalCaloriesBurned']?.toDouble() ?? 0,
      totalDistanceCovered: map['totalDistanceCovered']?.toDouble() ?? 0,
      workoutTypeCount: map['workoutTypeCount'] != null
          ? Map<String, int>.from(map['workoutTypeCount'])
          : null,
      nutritionAverages: map['nutritionAverages'] != null
          ? Map<String, double>.from(map['nutritionAverages'])
          : null,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'totalWorkouts': totalWorkouts,
      'workoutStreak': workoutStreak,
      'totalWorkoutTimeMinutes': totalWorkoutTime.inMinutes,
      'totalCaloriesBurned': totalCaloriesBurned,
      'totalDistanceCovered': totalDistanceCovered,
      'workoutTypeCount': workoutTypeCount,
      'nutritionAverages': nutritionAverages,
    };
  }

  UserStats copyWith({
    int? totalWorkouts,
    int? workoutStreak,
    Duration? totalWorkoutTime,
    double? totalCaloriesBurned,
    double? totalDistanceCovered,
    Map<String, int>? workoutTypeCount,
    Map<String, double>? nutritionAverages,
  }) {
    return UserStats(
      totalWorkouts: totalWorkouts ?? this.totalWorkouts,
      workoutStreak: workoutStreak ?? this.workoutStreak,
      totalWorkoutTime: totalWorkoutTime ?? this.totalWorkoutTime,
      totalCaloriesBurned: totalCaloriesBurned ?? this.totalCaloriesBurned,
      totalDistanceCovered: totalDistanceCovered ?? this.totalDistanceCovered,
      workoutTypeCount: workoutTypeCount ?? this.workoutTypeCount,
      nutritionAverages: nutritionAverages ?? this.nutritionAverages,
    );
  }
}
""",
    },
}

# Sidebar
st.sidebar.title("Repository Analysis")

# Repository selection
repository_source = st.sidebar.radio(
    "Repository Source",
    ["Sample Repository", "GitHub URL", "Upload Files"]
)

if repository_source == "Sample Repository":
    # Sample repository selection
    selected_repo = st.sidebar.selectbox(
        "Select Sample Repository",
        list(SAMPLE_REPOSITORIES.keys())
    )
    
    # Add repository to session state
    if st.sidebar.button("Analyze Repository"):
        with st.spinner("Analyzing repository..."):
            # Store file contents in session state
            st.session_state.file_contents = SAMPLE_REPOSITORIES[selected_repo]
            
            # Analyze repository
            repo_analysis = analyze_repository(st.session_state.file_contents)
            if repo_analysis:
                st.session_state.repo_analysis = repo_analysis
                st.sidebar.success("Repository analysis completed!")

elif repository_source == "GitHub URL":
    # GitHub URL input
    github_url = st.sidebar.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/username/repo"
    )
    
    # Add note about limitations
    st.sidebar.info("Note: Due to platform limitations, only public repositories can be analyzed, and large repositories may time out.")
    
    # Add repository to session state
    if st.sidebar.button("Analyze Repository") and github_url:
        st.sidebar.error("GitHub analysis is not implemented in this demo. Please use Sample Repository option.")

elif repository_source == "Upload Files":
    # File upload
    uploaded_files = st.sidebar.file_uploader(
        "Upload Repository Files",
        accept_multiple_files=True,
        type=["py", "js", "java", "cpp", "c", "h", "cs", "go", "rb", "php", "ts", "html", "css", "dart", "swift", "json", "yaml", "yml"]
    )
    
    # Add repository to session state
    if st.sidebar.button("Analyze Repository") and uploaded_files:
        with st.spinner("Analyzing uploaded files..."):
            # Process uploaded files
            file_contents = {}
            for file in uploaded_files:
                file_contents[file.name] = file.getvalue().decode("utf-8")
            
            # Store file contents in session state
            st.session_state.file_contents = file_contents
            
            # Analyze repository
            repo_analysis = analyze_repository(file_contents)
            if repo_analysis:
                st.session_state.repo_analysis = repo_analysis
                st.sidebar.success("Repository analysis completed!")

# File analysis
if st.session_state.repo_analysis and st.session_state.file_contents:
    selected_file = st.sidebar.selectbox(
        "Select File for Analysis",
        options=list(st.session_state.file_contents.keys()),
        format_func=lambda x: os.path.basename(x)
    )
    
    if st.sidebar.button("Analyze File"):
        with st.spinner("Analyzing file..."):
            file_info = {
                "path": selected_file,
                "name": os.path.basename(selected_file),
                "extension": os.path.splitext(selected_file)[1].lower(),
                "content": st.session_state.file_contents[selected_file],
                "size": len(st.session_state.file_contents[selected_file])
            }
            
            # Get language based on file extension
            ext = file_info["extension"]
            if ext in ['.py']:
                file_info["language"] = "Python"
            elif ext in ['.js']:
                file_info["language"] = "JavaScript"
            elif ext in ['.ts']:
                file_info["language"] = "TypeScript"
            elif ext in ['.java']:
                file_info["language"] = "Java"
            elif ext in ['.go']:
                file_info["language"] = "Go"
            elif ext in ['.cs']:
                file_info["language"] = "C#"
            elif ext in ['.cpp', '.cc', '.c', '.h']:
                file_info["language"] = "C/C++"
            elif ext in ['.rb']:
                file_info["language"] = "Ruby"
            elif ext in ['.php']:
                file_info["language"] = "PHP"
            elif ext in ['.swift']:
                file_info["language"] = "Swift"
            elif ext in ['.dart']:
                file_info["language"] = "Dart"
            else:
                file_info["language"] = "Other"
            
            # Analyze file
            file_analysis = analyze_file(file_info)
            if file_analysis:
                st.session_state.files_analysis[selected_file] = file_analysis
                st.session_state.current_file = selected_file
                st.sidebar.success("File analysis completed!")

# Add navigation back to homepage
if st.sidebar.button("Back to Home"):
    st.switch_page("app.py")

# Main content
st.title("Repository Analysis")

# Display repository analysis
if st.session_state.repo_analysis:
    repo_analysis = st.session_state.repo_analysis
    
    # Repository overview
    st.header("Repository Overview")
    
    # Quality score
    quality_score = repo_analysis.get("quality_score", 5)
    score_class = get_score_class(quality_score)
    
    st.markdown(
        f"<div class='quality-score-container'>"
        f"<div class='quality-score {score_class}'>{quality_score}</div>"
        f"<div class='quality-label'>Overall Quality Score</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # Repository metrics
    stats = repo_analysis.get("stats", {})
    languages = stats.get("languages", {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            f"<div class='repo-metric-card'>"
            f"<div class='repo-metric-value'>{stats.get('file_count', 0)}</div>"
            f"<div class='repo-metric-label'>Files</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    with col2:
        total_size = stats.get('total_size', 0)
        size_str = f"{total_size / 1024:.1f} KB" if total_size > 1024 else f"{total_size} bytes"
        
        st.markdown(
            f"<div class='repo-metric-card'>"
            f"<div class='repo-metric-value'>{size_str}</div>"
            f"<div class='repo-metric-label'>Total Size</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    with col3:
        lang_count = len(languages)
        
        st.markdown(
            f"<div class='repo-metric-card'>"
            f"<div class='repo-metric-value'>{lang_count}</div>"
            f"<div class='repo-metric-label'>Languages</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    # Language distribution
    if languages:
        st.subheader("Language Distribution")
        
        # Create pie chart
        lang_data = pd.DataFrame({
            "Language": list(languages.keys()),
            "Files": list(languages.values())
        })
        
        fig = px.pie(
            lang_data, 
            values="Files", 
            names="Language",
            title="Language Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Overview text
    st.subheader("Analysis")
    st.markdown(repo_analysis.get("overview", "No overview available"))
    
    # Tabs for different analysis aspects
    tab1, tab2, tab3 = st.tabs(["Architecture", "Code Organization", "Issues & Recommendations"])
    
    with tab1:
        architecture = repo_analysis.get("architecture", {})
        
        arch_score = architecture.get("score", 0)
        arch_score_class = get_score_class(arch_score)
        
        st.markdown(
            f"<div class='quality-score-container'>"
            f"<div class='quality-score {arch_score_class}'>{arch_score}</div>"
            f"<div class='quality-label'>Architecture Score</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        st.markdown(architecture.get("evaluation", "No architecture evaluation available"))
        
        patterns = architecture.get("patterns", [])
        if patterns:
            st.subheader("Architecture Patterns")
            for pattern in patterns:
                st.markdown(f"- {pattern}")
    
    with tab2:
        organization = repo_analysis.get("organization", {})
        
        org_score = organization.get("score", 0)
        org_score_class = get_score_class(org_score)
        
        st.markdown(
            f"<div class='quality-score-container'>"
            f"<div class='quality-score {org_score_class}'>{org_score}</div>"
            f"<div class='quality-label'>Organization Score</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        st.markdown(organization.get("evaluation", "No organization evaluation available"))
        
        # Strengths and weaknesses
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Strengths")
            strengths = organization.get("strengths", [])
            if strengths:
                for strength in strengths:
                    st.markdown(f"- {strength}")
            else:
                st.info("No strengths identified")
        
        with col2:
            st.subheader("Weaknesses")
            weaknesses = organization.get("weaknesses", [])
            if weaknesses:
                for weakness in weaknesses:
                    st.markdown(f"- {weakness}")
            else:
                st.info("No weaknesses identified")
    
    with tab3:
        # Issues
        st.subheader("Issues")
        issues = repo_analysis.get("issues", [])
        
        if issues:
            for issue in issues:
                severity = issue.get("severity", "medium")
                severity_color = {
                    "high": "#f44336",
                    "medium": "#ff9800",
                    "low": "#4caf50"
                }.get(severity.lower(), "#ff9800")
                
                st.markdown(
                    f"<div class='issue-card'>"
                    f"<div class='issue-title'>{issue.get('title', 'Unknown Issue')}</div>"
                    f"<div>Severity: <span style='color: {severity_color}; font-weight: bold;'>{severity.upper()}</span></div>"
                    f"<div>{issue.get('description', 'No description available')}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No issues identified")
        
        # Recommendations
        st.subheader("Recommendations")
        recommendations = repo_analysis.get("recommendations", [])
        
        if recommendations:
            for i, recommendation in enumerate(recommendations):
                st.markdown(f"{i+1}. {recommendation}")
        else:
            st.info("No recommendations provided")
    
    # File analysis
    if st.session_state.current_file and st.session_state.current_file in st.session_state.files_analysis:
        st.header("File Analysis")
        
        file_analysis = st.session_state.files_analysis[st.session_state.current_file]
        file_info = file_analysis.get("file_info", {})
        
        # File header
        st.markdown(
            f"<div class='file-card'>"
            f"<div class='file-name'>{file_info.get('name', 'Unknown file')}</div>"
            f"<div class='file-path'>{file_info.get('path', '')}</div>"
            f"<div class='file-metrics'>"
            f"<span class='file-metric'>Language: {file_info.get('language', 'Unknown')}</span>"
            f"<span class='file-metric'>Size: {file_info.get('size', 0)} bytes</span>"
            f"</div>"
            f"<div class='file-description'>{file_analysis.get('summary', 'No summary available')}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        # Quality scores
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            quality_score = file_analysis.get("quality_score", 5)
            score_class = get_score_class(quality_score)
            
            st.markdown(
                f"<div class='repo-metric-card'>"
                f"<div class='quality-score {score_class}' style='margin: 0 auto;'>{quality_score}</div>"
                f"<div class='repo-metric-label'>Overall Quality</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        
        with col2:
            complexity = file_analysis.get("complexity", {})
            complexity_score = complexity.get("score", 5)
            score_class = get_score_class(complexity_score)
            
            st.markdown(
                f"<div class='repo-metric-card'>"
                f"<div class='quality-score {score_class}' style='margin: 0 auto;'>{complexity_score}</div>"
                f"<div class='repo-metric-label'>Complexity</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        
        with col3:
            documentation = file_analysis.get("documentation", {})
            documentation_score = documentation.get("score", 5)
            score_class = get_score_class(documentation_score)
            
            st.markdown(
                f"<div class='repo-metric-card'>"
                f"<div class='quality-score {score_class}' style='margin: 0 auto;'>{documentation_score}</div>"
                f"<div class='repo-metric-label'>Documentation</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        
        with col4:
            maintainability = file_analysis.get("maintainability", {})
            maintainability_score = maintainability.get("score", 5)
            score_class = get_score_class(maintainability_score)
            
            st.markdown(
                f"<div class='repo-metric-card'>"
                f"<div class='quality-score {score_class}' style='margin: 0 auto;'>{maintainability_score}</div>"
                f"<div class='repo-metric-label'>Maintainability</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        
        # File analysis tabs
        tab1, tab2, tab3 = st.tabs(["Analysis", "Issues", "Best Practices"])
        
        with tab1:
            # Complexity
            st.subheader("Complexity Analysis")
            st.markdown(complexity.get("evaluation", "No complexity evaluation available"))
            
            # Documentation
            st.subheader("Documentation Analysis")
            st.markdown(documentation.get("evaluation", "No documentation evaluation available"))
            
            # Maintainability
            st.subheader("Maintainability Analysis")
            st.markdown(maintainability.get("evaluation", "No maintainability evaluation available"))
        
        with tab2:
            # Issues
            st.subheader("Issues")
            issues = file_analysis.get("issues", [])
            
            if issues:
                for issue in issues:
                    severity = issue.get("severity", "medium")
                    severity_color = {
                        "high": "#f44336",
                        "medium": "#ff9800",
                        "low": "#4caf50"
                    }.get(severity.lower(), "#ff9800")
                    
                    line_numbers = issue.get("line_numbers", [])
                    line_str = f"Lines: {', '.join(map(str, line_numbers))}" if line_numbers else ""
                    
                    st.markdown(
                        f"<div class='issue-card'>"
                        f"<div class='issue-title'>{issue.get('title', 'Unknown Issue')}</div>"
                        f"<div>Severity: <span style='color: {severity_color}; font-weight: bold;'>{severity.upper()}</span> {line_str}</div>"
                        f"<div>{issue.get('description', 'No description available')}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
            else:
                st.info("No issues identified in this file")
            
            # Recommendations
            st.subheader("Recommendations")
            recommendations = file_analysis.get("recommendations", [])
            
            if recommendations:
                for i, recommendation in enumerate(recommendations):
                    st.markdown(f"{i+1}. {recommendation}")
            else:
                st.info("No recommendations provided for this file")
        
        with tab3:
            # Best practices
            st.subheader("Best Practices")
            practices = file_analysis.get("best_practices", [])
            
            if practices:
                for practice in practices:
                    title = practice.get("title", "Unknown practice")
                    observed = practice.get("observed", False)
                    description = practice.get("description", "No description available")
                    
                    if observed:
                        icon = "✅"
                        status = "Observed"
                    else:
                        icon = "❌"
                        status = "Not observed"
                    
                    st.markdown(
                        f"<div class='issue-card'>"
                        f"<div class='issue-title'>{title} {icon}</div>"
                        f"<div>Status: <strong>{status}</strong></div>"
                        f"<div>{description}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
            else:
                st.info("No best practices evaluated for this file")
        
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
             use_column_width=True)# End of file
