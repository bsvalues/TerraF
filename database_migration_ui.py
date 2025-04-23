"""
Database Migration UI

This module provides a Streamlit UI for managing database migrations in the TerraFusion platform.
"""

import os
import sys
import logging
import json
import time
import streamlit as st
from typing import Dict, Any, List, Optional, Tuple
from services.database.migration_manager import MigrationManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_migration_state():
    """Initialize session state for database migrations."""
    if 'migration_manager' not in st.session_state:
        try:
            st.session_state.migration_manager = MigrationManager()
            logger.info("Initialized migration manager")
        except Exception as e:
            logger.error(f"Error initializing migration manager: {e}")
            st.session_state.migration_manager = None
    
    if 'migration_status' not in st.session_state:
        st.session_state.migration_status = None
    
    if 'db_structure' not in st.session_state:
        st.session_state.db_structure = None
    
    if 'migration_result' not in st.session_state:
        st.session_state.migration_result = None
    
    if 'migration_error' not in st.session_state:
        st.session_state.migration_error = None

def refresh_migration_status():
    """Refresh the migration status in the session state."""
    if st.session_state.migration_manager:
        try:
            st.session_state.migration_status = st.session_state.migration_manager.get_migration_status()
            logger.info("Refreshed migration status")
        except Exception as e:
            logger.error(f"Error getting migration status: {e}")
            st.session_state.migration_error = str(e)

def refresh_db_structure():
    """Refresh the database structure in the session state."""
    if st.session_state.migration_manager:
        try:
            st.session_state.db_structure = st.session_state.migration_manager.check_database()
            logger.info("Refreshed database structure")
        except Exception as e:
            logger.error(f"Error checking database structure: {e}")
            st.session_state.migration_error = str(e)

def create_migration(message: str, autogenerate: bool = True) -> Tuple[bool, str]:
    """Create a new database migration."""
    if not st.session_state.migration_manager:
        return False, "Migration manager not initialized"
    
    try:
        script_path = st.session_state.migration_manager.create_migration(message, autogenerate)
        logger.info(f"Created migration script: {script_path}")
        return True, f"Created migration script: {script_path}"
    except Exception as e:
        logger.error(f"Error creating migration: {e}")
        return False, f"Error creating migration: {str(e)}"

def upgrade_database(target: str = 'head') -> Tuple[bool, str]:
    """Upgrade the database to a specific revision."""
    if not st.session_state.migration_manager:
        return False, "Migration manager not initialized"
    
    try:
        success, message = st.session_state.migration_manager.upgrade(target)
        logger.info(f"Database upgrade result: {message}")
        return success, message
    except Exception as e:
        logger.error(f"Error upgrading database: {e}")
        return False, f"Error upgrading database: {str(e)}"

def downgrade_database(target: str) -> Tuple[bool, str]:
    """Downgrade the database to a specific revision."""
    if not st.session_state.migration_manager:
        return False, "Migration manager not initialized"
    
    try:
        success, message = st.session_state.migration_manager.downgrade(target)
        logger.info(f"Database downgrade result: {message}")
        return success, message
    except Exception as e:
        logger.error(f"Error downgrading database: {e}")
        return False, f"Error downgrading database: {str(e)}"

def render_migration_status(status: Dict[str, Any]):
    """Render the migration status UI."""
    st.subheader("Migration Status")
    
    # Current status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        current_rev = status['current_revision'] or "None"
        st.metric("Current Revision", current_rev[:8] if current_rev != "None" else "None")
    
    with col2:
        head_rev = status['head_revision'] or "None"
        st.metric("Latest Revision", head_rev[:8] if head_rev != "None" else "None")
    
    with col3:
        st.metric("Pending Migrations", status['migrations_pending'])
    
    # Migration lists
    if status['applied_migrations']:
        with st.expander("Applied Migrations", expanded=False):
            for m in status['applied_migrations']:
                st.markdown(f"**{m['revision'][:8]}** - {m['created']} - {m['description']}")
    
    if status['pending_migrations']:
        with st.expander("Pending Migrations", expanded=True):
            for m in status['pending_migrations']:
                st.markdown(f"**{m['revision'][:8]}** - {m['created']} - {m['description']}")

def render_database_structure(structure: Dict[str, Any]):
    """Render the database structure UI."""
    st.subheader("Database Structure")
    
    # Table count
    st.metric("Tables", structure['table_count'])
    
    # Tables
    if structure['tables']:
        for table in structure['tables']:
            with st.expander(f"{table['name']} ({table['column_count']} columns)", expanded=False):
                # Columns
                st.markdown("**Columns:**")
                columns_data = []
                
                for col in table['columns']:
                    pk_marker = "✓" if col['primary_key'] else ""
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    default = str(col['default']) if col['default'] else ""
                    
                    columns_data.append({
                        "Name": col['name'],
                        "Type": col['type'],
                        "Nullable": nullable,
                        "Default": default,
                        "Primary Key": pk_marker
                    })
                
                st.table(columns_data)
                
                # Indexes
                if table['indexes']:
                    st.markdown("**Indexes:**")
                    indexes_data = []
                    
                    for idx in table['indexes']:
                        unique = "✓" if idx['unique'] else ""
                        
                        indexes_data.append({
                            "Name": idx['name'],
                            "Columns": ", ".join(idx['columns']),
                            "Unique": unique
                        })
                    
                    st.table(indexes_data)
                
                # Foreign Keys
                if table['foreign_keys']:
                    st.markdown("**Foreign Keys:**")
                    fk_data = []
                    
                    for fk in table['foreign_keys']:
                        fk_data.append({
                            "Name": fk['name'],
                            "Columns": ", ".join(fk['columns']),
                            "References": f"{fk['referred_table']}({', '.join(fk['referred_columns'])})"
                        })
                    
                    st.table(fk_data)

def render_migration_ui():
    """Render the main migration management UI."""
    st.title("🔄 Database Migration Manager")
    st.markdown("""
    Manage database schema migrations for the TerraFusion platform.
    This tool allows you to create, apply, and track database schema changes.
    """)
    
    # Initialize state
    initialize_migration_state()
    
    # Show error if any
    if st.session_state.migration_error:
        st.error(f"Error: {st.session_state.migration_error}")
        if st.button("Clear Error"):
            st.session_state.migration_error = None
            st.experimental_rerun()
    
    # Actions tabs
    tabs = st.tabs(["Status", "Create Migration", "Apply Migrations", "Database Structure"])
    
    # Status tab
    with tabs[0]:
        st.header("Migration Status")
        
        if st.button("Refresh Status", key="refresh_status"):
            refresh_migration_status()
        
        if st.session_state.migration_status is None:
            refresh_migration_status()
        
        if st.session_state.migration_status:
            render_migration_status(st.session_state.migration_status)
        else:
            st.info("Migration status not available. Try refreshing.")
    
    # Create Migration tab
    with tabs[1]:
        st.header("Create Migration")
        
        migration_message = st.text_input(
            "Migration Message",
            placeholder="e.g., add_user_table",
            help="A short description of the migration"
        )
        
        autogenerate = st.checkbox(
            "Auto-generate",
            value=True,
            help="Automatically generate migration based on model changes"
        )
        
        create_col, _ = st.columns([1, 3])
        
        with create_col:
            if st.button("Create Migration", key="create_migration"):
                if not migration_message:
                    st.error("Migration message is required")
                else:
                    success, message = create_migration(migration_message, autogenerate)
                    
                    if success:
                        st.session_state.migration_result = {"success": True, "message": message}
                        refresh_migration_status()
                    else:
                        st.session_state.migration_result = {"success": False, "message": message}
        
        if st.session_state.migration_result:
            if st.session_state.migration_result["success"]:
                st.success(st.session_state.migration_result["message"])
            else:
                st.error(st.session_state.migration_result["message"])
    
    # Apply Migrations tab
    with tabs[2]:
        st.header("Apply Migrations")
        
        # Get current status for reference
        if st.session_state.migration_status is None:
            refresh_migration_status()
        
        if not st.session_state.migration_status:
            st.info("Migration status not available. Please check the Status tab.")
        else:
            # Upgrade section
            st.subheader("Upgrade Database")
            
            upgrade_options = ["head"]
            if st.session_state.migration_status['pending_migrations']:
                for m in st.session_state.migration_status['pending_migrations']:
                    upgrade_options.append(f"{m['revision'][:8]} - {m['description']}")
            
            upgrade_target = st.selectbox(
                "Upgrade Target",
                options=upgrade_options,
                help="Select the target revision to upgrade to"
            )
            
            # Extract revision ID from selection
            if upgrade_target != "head":
                upgrade_target = upgrade_target.split(" - ")[0].strip()
            
            upgrade_col, _ = st.columns([1, 3])
            
            with upgrade_col:
                if st.button("Upgrade Database", key="upgrade_db"):
                    success, message = upgrade_database(upgrade_target)
                    
                    if success:
                        st.session_state.migration_result = {"success": True, "message": message}
                        refresh_migration_status()
                        refresh_db_structure()
                    else:
                        st.session_state.migration_result = {"success": False, "message": message}
            
            # Downgrade section
            st.markdown("---")
            st.subheader("Downgrade Database")
            
            downgrade_options = []
            if st.session_state.migration_status['applied_migrations']:
                for m in st.session_state.migration_status['applied_migrations']:
                    downgrade_options.append(f"{m['revision'][:8]} - {m['description']}")
            
            if downgrade_options:
                downgrade_target = st.selectbox(
                    "Downgrade Target",
                    options=downgrade_options,
                    help="Select the target revision to downgrade to"
                )
                
                # Extract revision ID from selection
                downgrade_target = downgrade_target.split(" - ")[0].strip()
                
                downgrade_col, _ = st.columns([1, 3])
                
                with downgrade_col:
                    if st.button("Downgrade Database", key="downgrade_db"):
                        success, message = downgrade_database(downgrade_target)
                        
                        if success:
                            st.session_state.migration_result = {"success": True, "message": message}
                            refresh_migration_status()
                            refresh_db_structure()
                        else:
                            st.session_state.migration_result = {"success": False, "message": message}
            else:
                st.info("No applied migrations to downgrade to.")
        
        # Show result
        if st.session_state.migration_result:
            st.markdown("---")
            st.subheader("Operation Result")
            
            if st.session_state.migration_result["success"]:
                st.success(st.session_state.migration_result["message"])
            else:
                st.error(st.session_state.migration_result["message"])
    
    # Database Structure tab
    with tabs[3]:
        st.header("Database Structure")
        
        if st.button("Refresh Structure", key="refresh_structure"):
            refresh_db_structure()
        
        if st.session_state.db_structure is None:
            refresh_db_structure()
        
        if st.session_state.db_structure:
            render_database_structure(st.session_state.db_structure)
        else:
            st.info("Database structure not available. Try refreshing.")

def add_migration_tab():
    """Add database migration tab to the sidebar."""
    if "enhanced_tabs" in st.session_state and "Database Migrations" not in st.session_state.enhanced_tabs:
        st.session_state.enhanced_tabs.append("Database Migrations")

def render_database_migration_tab():
    """Render the database migration tab."""
    render_migration_ui()

if __name__ == "__main__":
    # For standalone testing
    render_migration_ui()