import unittest
import os
import tempfile
import shutil
from pathlib import Path
import json

# Import modules to test
from repository_handler import clone_repository, get_repository_structure
from code_analyzer import perform_code_review, analyze_python_file
from database_analyzer import find_database_files, analyze_database_structures
from modularization_analyzer import analyze_modularization, find_python_files
from agent_readiness_analyzer import analyze_agent_readiness, find_ml_files
from workflow_analyzer import analyze_workflow_patterns
from report_generator import generate_summary_report
from utils import sanitize_filename, count_lines_of_code, detect_programming_language

class TestRepositoryHandler(unittest.TestCase):
    """Tests for repository handling functions"""
    
    def setUp(self):
        # Create a temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        
        # Create a simple test repository structure
        self.repo_path = os.path.join(self.test_dir, "test_repo")
        os.makedirs(self.repo_path)
        
        # Create some test files
        self.create_test_file(os.path.join(self.repo_path, "test_file.py"), "print('Hello World')")
        self.create_test_file(os.path.join(self.repo_path, "models.py"), "class User:\n    pass")
        
        # Create a subdirectory
        os.makedirs(os.path.join(self.repo_path, "subdir"))
        self.create_test_file(os.path.join(self.repo_path, "subdir", "test_sub.py"), "# A test file")
    
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
    
    def create_test_file(self, path, content):
        with open(path, 'w') as f:
            f.write(content)
    
    def test_get_repository_structure(self):
        """Test repository structure analysis"""
        structure = get_repository_structure(self.repo_path)
        
        # Check that basic structure information is present
        self.assertIn('file_count', structure)
        self.assertIn('directory_count', structure)
        self.assertIn('file_types', structure)
        
        # There should be files in the test directory
        self.assertGreater(structure['file_count'], 0)
        
        # Check directory count (excluding root)
        self.assertEqual(structure['directory_count'], 1)
        
        # Check file types
        file_types = [ft['extension'] for ft in structure['file_types']]
        self.assertIn('.py', file_types)

class TestCodeAnalyzer(unittest.TestCase):
    """Tests for code analysis functions"""
    
    def setUp(self):
        # Create a temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        
        # Create a test Python file with some code to analyze
        self.test_file = os.path.join(self.test_dir, "test_code.py")
        test_code = """
import os
import sys

# A global variable
GLOBAL_VAR = 42

class TestClass:
    def __init__(self):
        self.value = 10
    
    def long_method(self, a, b, c, d, e):
        # This method has too many parameters
        result = 0
        if a > 0:
            if b > 0:
                if c > 0:
                    # Nested conditionals
                    result = 100
        return result

def complex_function():
    # This function has high cyclomatic complexity
    for i in range(10):
        if i % 2 == 0:
            print("Even")
        else:
            print("Odd")
            
        if i > 5:
            print("Greater than 5")
"""
        with open(self.test_file, 'w') as f:
            f.write(test_code)
    
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_analyze_python_file(self):
        """Test Python file analysis"""
        analysis = analyze_python_file(self.test_file)
        
        # Check that analysis contains expected sections
        self.assertIn('functions', analysis)
        self.assertIn('classes', analysis)
        self.assertIn('imports', analysis)
        self.assertIn('issues', analysis)
        
        # Check import detection
        self.assertEqual(len(analysis['imports']), 2)
        
        # Check class detection
        self.assertEqual(len(analysis['classes']), 1)
        self.assertEqual(analysis['classes'][0]['name'], 'TestClass')
        
        # Check function detection
        functions = [f['name'] for f in analysis['functions']]
        self.assertIn('complex_function', functions)
        
        # Check issue detection (at least some issues should be found)
        self.assertGreater(len(analysis['issues']), 0)

class TestDatabaseAnalyzer(unittest.TestCase):
    """Tests for database analysis functions"""
    
    def setUp(self):
        # Create a temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        
        # Create a test file with database models
        self.models_file = os.path.join(self.test_dir, "models.py")
        models_code = """
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String)
    
    posts = relationship("Post", back_populates="author")

class Post(Base):
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    author = relationship("User", back_populates="posts")
"""
        with open(self.models_file, 'w') as f:
            f.write(models_code)
    
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_find_database_files(self):
        """Test finding database-related files"""
        db_files = find_database_files(self.test_dir)
        
        # Check that our models file was detected
        self.assertEqual(len(db_files), 1)
        self.assertIn("models.py", db_files[0])

class TestUtils(unittest.TestCase):
    """Tests for utility functions"""
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        # Test with invalid characters
        self.assertEqual(sanitize_filename("file:name?"), "file_name_")
        
        # Test with long filename
        long_name = "a" * 300 + ".txt"
        sanitized = sanitize_filename(long_name)
        self.assertLess(len(sanitized), 256)
    
    def test_detect_programming_language(self):
        """Test programming language detection"""
        self.assertEqual(detect_programming_language("test.py"), "Python")
        self.assertEqual(detect_programming_language("test.js"), "JavaScript")
        self.assertEqual(detect_programming_language("test.unknown"), "unknown")

if __name__ == "__main__":
    unittest.main()