import os
import re
import logging
import json
from collections import defaultdict
import pandas as pd
import ast
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Patterns for identifying database-related files and code
DB_FILE_PATTERNS = [
    r'.*models\.py$',
    r'.*schema\.py$',
    r'.*repository\.py$',
    r'.*dao\.py$',
    r'.*db\.py$',
    r'.*database\.py$',
    r'.*migrations.*\.py$',
    r'.*entity\.py$',
    r'.*orm.*\.py$',
]

# SQL keywords for identifying SQL queries
SQL_KEYWORDS = [
    'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE TABLE', 'ALTER TABLE',
    'DROP TABLE', 'JOIN', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING',
    'UNION', 'INDEX', 'VIEW', 'CONSTRAINT', 'FOREIGN KEY', 'PRIMARY KEY'
]

# ORM frameworks to detect
ORM_FRAMEWORKS = {
    'sqlalchemy': ['sqlalchemy', 'Column', 'relationship', 'ForeignKey', 'Table'],
    'django': ['models.Model', 'models.CharField', 'models.ForeignKey', 'models.ManyToManyField'],
    'peewee': ['peewee', 'Model', 'CharField', 'ForeignKeyField'],
    'pony': ['pony.orm', 'Entity', 'Required', 'Optional', 'Set'],
    'tortoise': ['tortoise.models', 'Model'],
    'mongoengine': ['mongoengine', 'Document', 'StringField', 'ReferenceField']
}

class DatabaseModelExtractor(ast.NodeVisitor):
    """AST visitor for extracting database models from Python code"""
    
    def __init__(self):
        self.models = {}
        self.current_model = None
        self.orm_type = None
    
    def visit_ClassDef(self, node):
        """Process class definitions to find database models"""
        # Check for Django models
        if any(base.id == 'Model' for base in node.bases if isinstance(base, ast.Name)):
            self.orm_type = 'django'
            self._process_django_model(node)
        
        # Check for SQLAlchemy models (classes with __tablename__)
        elif any(target.id == '__tablename__' for stmt in node.body 
                if isinstance(stmt, ast.Assign) 
                for target in stmt.targets 
                if isinstance(target, ast.Name)):
            self.orm_type = 'sqlalchemy'
            self._process_sqlalchemy_model(node)
        
        # Check for Peewee models
        elif any(base.id == 'Model' for base in node.bases if isinstance(base, ast.Name)):
            # Additional check to distinguish from other frameworks
            if any(isinstance(stmt, ast.Assign) and 
                  any(isinstance(stmt.value, ast.Call) and 
                      (hasattr(stmt.value.func, 'id') and 
                       stmt.value.func.id in ['CharField', 'IntegerField', 'ForeignKeyField']) 
                      for stmt in node.body if isinstance(stmt, ast.Assign))):
                self.orm_type = 'peewee'
                self._process_peewee_model(node)
        
        # Process children nodes
        self.generic_visit(node)
    
    def _process_django_model(self, node):
        """Extract fields from a Django model"""
        model = {
            'name': node.name,
            'fields': [],
            'relationships': [],
            'orm_type': 'django'
        }
        
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        field_name = target.id
                        
                        # Skip non-field attributes
                        if field_name.startswith('_') or field_name in ['objects', 'Meta']:
                            continue
                        
                        if isinstance(stmt.value, ast.Call):
                            field_type = None
                            is_relationship = False
                            
                            # Get field type
                            if isinstance(stmt.value.func, ast.Attribute):
                                if stmt.value.func.attr in ['ForeignKey', 'OneToOneField', 'ManyToManyField']:
                                    is_relationship = True
                                    field_type = stmt.value.func.attr
                                elif hasattr(stmt.value.func, 'value') and isinstance(stmt.value.func.value, ast.Name) and stmt.value.func.value.id == 'models':
                                    field_type = stmt.value.func.attr
                            
                            # Get related model for relationships
                            related_model = None
                            if is_relationship and stmt.value.args:
                                related_arg = stmt.value.args[0]
                                if isinstance(related_arg, ast.Name):
                                    related_model = related_arg.id
                                elif isinstance(related_arg, ast.Str):
                                    related_model = related_arg.s
                            
                            if is_relationship and related_model:
                                model['relationships'].append({
                                    'name': field_name,
                                    'type': field_type,
                                    'related_model': related_model
                                })
                            elif field_type:
                                model['fields'].append({
                                    'name': field_name,
                                    'type': field_type
                                })
        
        self.models[node.name] = model
    
    def _process_sqlalchemy_model(self, node):
        """Extract fields from a SQLAlchemy model"""
        model = {
            'name': node.name,
            'fields': [],
            'relationships': [],
            'orm_type': 'sqlalchemy'
        }
        
        # Get the table name
        table_name = None
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == '__tablename__':
                        if isinstance(stmt.value, ast.Str):
                            table_name = stmt.value.s
        
        model['table_name'] = table_name
        
        # Get columns and relationships
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        field_name = target.id
                        
                        # Skip non-field attributes
                        if field_name.startswith('_') or field_name in ['__tablename__', 'metadata']:
                            continue
                        
                        if isinstance(stmt.value, ast.Call):
                            field_type = None
                            is_relationship = False
                            
                            # Check for Column
                            if hasattr(stmt.value.func, 'id') and stmt.value.func.id == 'Column':
                                field_type = 'Column'
                                # Try to get the specific column type if available
                                if stmt.value.args:
                                    arg = stmt.value.args[0]
                                    if isinstance(arg, ast.Call) and hasattr(arg.func, 'id'):
                                        field_type = arg.func.id
                            
                            # Check for relationship
                            elif hasattr(stmt.value.func, 'id') and stmt.value.func.id == 'relationship':
                                is_relationship = True
                                field_type = 'relationship'
                                
                                # Get related model
                                related_model = None
                                if stmt.value.args:
                                    related_arg = stmt.value.args[0]
                                    if isinstance(related_arg, ast.Str):
                                        related_model = related_arg.s
                            
                            if is_relationship and related_model:
                                model['relationships'].append({
                                    'name': field_name,
                                    'type': field_type,
                                    'related_model': related_model
                                })
                            elif field_type:
                                model['fields'].append({
                                    'name': field_name,
                                    'type': field_type
                                })
        
        self.models[node.name] = model
    
    def _process_peewee_model(self, node):
        """Extract fields from a Peewee model"""
        model = {
            'name': node.name,
            'fields': [],
            'relationships': [],
            'orm_type': 'peewee'
        }
        
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        field_name = target.id
                        
                        # Skip non-field attributes
                        if field_name.startswith('_') or field_name in ['Meta']:
                            continue
                        
                        if isinstance(stmt.value, ast.Call):
                            field_type = None
                            is_relationship = False
                            
                            # Get field type
                            if hasattr(stmt.value.func, 'id'):
                                field_type = stmt.value.func.id
                                if field_type in ['ForeignKeyField', 'ManyToManyField']:
                                    is_relationship = True
                            
                            # Get related model for relationships
                            related_model = None
                            if is_relationship and stmt.value.keywords:
                                for keyword in stmt.value.keywords:
                                    if keyword.arg == 'model':
                                        if isinstance(keyword.value, ast.Name):
                                            related_model = keyword.value.id
                            
                            if is_relationship and related_model:
                                model['relationships'].append({
                                    'name': field_name,
                                    'type': field_type,
                                    'related_model': related_model
                                })
                            elif field_type:
                                model['fields'].append({
                                    'name': field_name,
                                    'type': field_type
                                })
        
        self.models[node.name] = model

def find_database_files(repo_path):
    """
    Find files that are likely related to database operations
    
    Parameters:
    - repo_path: Path to the cloned repository
    
    Returns:
    - list: Database-related files
    """
    db_files = []
    
    for root, _, files in os.walk(repo_path):
        for file in files:
            # Skip hidden files
            if file.startswith('.'):
                continue
                
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, repo_path)
            
            # Skip hidden directories
            if any(part.startswith('.') for part in Path(rel_path).parts):
                continue
            
            # Check if the file matches database patterns
            if any(re.match(pattern, rel_path) for pattern in DB_FILE_PATTERNS):
                db_files.append(rel_path)
            elif file.endswith('.py'):
                # For Python files, check the content for database-related code
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read().upper()
                        # Check for SQL keywords or ORM imports
                        if any(keyword in content for keyword in SQL_KEYWORDS):
                            db_files.append(rel_path)
                        elif any(orm_keyword.lower() in content.lower() 
                                for orm_keywords in ORM_FRAMEWORKS.values() 
                                for orm_keyword in orm_keywords):
                            db_files.append(rel_path)
                except Exception:
                    pass
    
    return db_files

def extract_database_models(repo_path, db_files):
    """
    Extract database models from the identified files
    
    Parameters:
    - repo_path: Path to the cloned repository
    - db_files: List of database-related files
    
    Returns:
    - dict: Extracted database models
    """
    all_models = {}
    orm_types = set()
    
    for file_path in db_files:
        try:
            full_path = os.path.join(repo_path, file_path)
            
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Parse the file as Python code
            tree = ast.parse(content, filename=file_path)
            
            # Extract models
            extractor = DatabaseModelExtractor()
            extractor.visit(tree)
            
            # Add discovered models
            for model_name, model_info in extractor.models.items():
                all_models[model_name] = {
                    **model_info,
                    'source_file': file_path
                }
                if extractor.orm_type:
                    orm_types.add(extractor.orm_type)
        except Exception as e:
            logger.error(f"Error extracting models from {file_path}: {str(e)}")
    
    return all_models, list(orm_types)

def extract_raw_sql_queries(repo_path, db_files):
    """
    Extract raw SQL queries from the codebase
    
    Parameters:
    - repo_path: Path to the cloned repository
    - db_files: List of database-related files
    
    Returns:
    - list: Extracted SQL queries
    """
    sql_queries = []
    
    # Regular expressions for finding SQL queries
    sql_patterns = [
        r'(?i)(?:execute|executemany|query)\s*\(\s*["\']([^;"\']+?(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)[^;"\']+)["\']',
        r'(?i)(?<=r["\']|["\'])(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)[^;"\']+(?=["\'])',
        r'(?i)(?<="""|\'\'\')(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)[^;]+(?="""|\'\'\')' 
    ]
    
    for file_path in db_files:
        try:
            full_path = os.path.join(repo_path, file_path)
            
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Search for SQL patterns
            for pattern in sql_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    query = match.group(0)
                    # Clean up the query
                    query = query.strip()
                    if query:
                        sql_queries.append({
                            'query': query,
                            'file': file_path
                        })
        except Exception as e:
            logger.error(f"Error extracting SQL queries from {file_path}: {str(e)}")
    
    return sql_queries

def detect_database_redundancies(models):
    """
    Detect potential redundancies in database models
    
    Parameters:
    - models: Dict of database models
    
    Returns:
    - list: Potential redundancies
    """
    redundancies = []
    
    # Check for similar model fields
    model_fields = {}
    for model_name, model_info in models.items():
        fields = [(field['name'], field.get('type', 'unknown')) for field in model_info.get('fields', [])]
        model_fields[model_name] = fields
    
    # Compare models pairwise
    for model1, fields1 in model_fields.items():
        for model2, fields2 in model_fields.items():
            if model1 >= model2:  # Skip duplicate comparisons and self-comparisons
                continue
            
            # Find common fields (by name and type)
            common_fields = set(fields1) & set(fields2)
            if len(common_fields) >= 3:  # Arbitrary threshold for similarity
                redundancies.append({
                    'type': 'similar_models',
                    'models': [model1, model2],
                    'common_fields': list(common_fields),
                    'similarity': len(common_fields) / max(len(fields1), len(fields2))
                })
    
    # Check for duplicate field names within a model
    for model_name, model_info in models.items():
        field_names = [field['name'] for field in model_info.get('fields', [])]
        duplicate_fields = [name for name in set(field_names) if field_names.count(name) > 1]
        if duplicate_fields:
            redundancies.append({
                'type': 'duplicate_fields',
                'model': model_name,
                'fields': duplicate_fields
            })
    
    return redundancies

def generate_consolidation_recommendations(models, redundancies, orm_types):
    """
    Generate recommendations for database consolidation
    
    Parameters:
    - models: Dict of database models
    - redundancies: List of detected redundancies
    - orm_types: List of detected ORM frameworks
    
    Returns:
    - list: Consolidation recommendations
    """
    recommendations = []
    
    # Recommendations based on redundancies
    for redundancy in redundancies:
        if redundancy['type'] == 'similar_models':
            model1, model2 = redundancy['models']
            similarity = redundancy['similarity']
            if similarity > 0.7:  # High similarity
                recommendations.append(
                    f"Consider merging models '{model1}' and '{model2}' which share {len(redundancy['common_fields'])} "
                    f"common fields with {int(similarity * 100)}% similarity."
                )
            else:  # Moderate similarity
                recommendations.append(
                    f"Extract common fields between '{model1}' and '{model2}' into a shared base model or mixin."
                )
        
        elif redundancy['type'] == 'duplicate_fields':
            recommendations.append(
                f"Remove or rename duplicate field definitions in model '{redundancy['model']}': {', '.join(redundancy['fields'])}"
            )
    
    # Recommendations based on model relationships
    relationship_models = {}
    for model_name, model_info in models.items():
        for rel in model_info.get('relationships', []):
            related_model = rel.get('related_model')
            if related_model:
                key = tuple(sorted([model_name, related_model]))
                if key not in relationship_models:
                    relationship_models[key] = []
                relationship_models[key].append({
                    'model': model_name,
                    'related_model': related_model,
                    'type': rel.get('type')
                })
    
    # Check for bidirectional relationships that could be optimized
    for (model1, model2), relationships in relationship_models.items():
        if len(relationships) > 1:
            recommendations.append(
                f"Ensure the relationship between '{model1}' and '{model2}' is consistently defined "
                f"and properly optimized for querying in both directions."
            )
    
    # General recommendations based on ORM usage
    if orm_types:
        if len(orm_types) > 1:
            recommendations.append(
                f"Multiple ORM frameworks detected ({', '.join(orm_types)}). Consider standardizing on a single ORM "
                f"for consistency and easier maintenance."
            )
        
        # Framework-specific recommendations
        if 'django' in orm_types:
            recommendations.append(
                "Consider using Django's abstract base models for common fields and behaviors."
            )
        
        if 'sqlalchemy' in orm_types:
            recommendations.append(
                "Consider using SQLAlchemy mixins and inheritance for shared model attributes."
            )
    
    # General recommendations for database design
    recommendations.append(
        "Implement consistent naming conventions for models, fields, and relationships."
    )
    
    recommendations.append(
        "Ensure proper indexing on frequently queried fields and foreign keys."
    )
    
    recommendations.append(
        "Use database migrations for schema changes to maintain data integrity."
    )
    
    return recommendations

def analyze_database_structures(repo_path):
    """
    Analyze database structures in the repository
    
    Parameters:
    - repo_path: Path to the cloned repository
    
    Returns:
    - dict: Database analysis results
    """
    logger.info(f"Analyzing database structures for repository at {repo_path}...")
    
    # Initialize results
    results = {
        'database_files': [],
        'database_models': {},
        'orm_frameworks': [],
        'sql_queries': [],
        'redundancies': [],
        'consolidation_recommendations': []
    }
    
    # Find database-related files
    db_files = find_database_files(repo_path)
    if not db_files:
        logger.info("No database-related files found.")
        return results
    
    # Convert to list of dictionaries for better display
    results['database_files'] = [{'path': file} for file in db_files]
    
    # Extract database models
    models, orm_types = extract_database_models(repo_path, db_files)
    results['database_models'] = models
    results['orm_frameworks'] = orm_types
    
    # Extract raw SQL queries
    sql_queries = extract_raw_sql_queries(repo_path, db_files)
    results['sql_queries'] = sql_queries
    
    # Detect redundancies
    if models:
        redundancies = detect_database_redundancies(models)
        results['redundancies'] = redundancies
        
        # Generate consolidation recommendations
        recommendations = generate_consolidation_recommendations(models, redundancies, orm_types)
        results['consolidation_recommendations'] = recommendations
    
    # Add recommendations based on SQL usage
    if sql_queries:
        results['consolidation_recommendations'].append(
            f"Found {len(sql_queries)} raw SQL queries. Consider moving complex queries to views or stored procedures "
            f"for better maintainability."
        )
        
        # Check for potential SQL injection
        for query in sql_queries:
            if '%' in query['query'] or '{' in query['query']:
                results['consolidation_recommendations'].append(
                    f"Potential SQL injection risk in {query['file']}. Ensure all parameters are properly sanitized."
                )
                break
    
    # If no specific recommendations found, add general ones
    if not results['consolidation_recommendations']:
        results['consolidation_recommendations'] = [
            "Use a single database access layer to centralize database operations.",
            "Implement an abstraction layer to make switching database backends easier.",
            "Consider using an ORM for safer database access and easier maintenance.",
            "Document database schema and relationships for better team understanding."
        ]
    
    logger.info(f"Database analysis complete. Found {len(models)} models across {len(db_files)} files.")
    return results
