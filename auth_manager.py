"""
TerraFusion Platform Authentication Module

This module provides basic authentication functionality for TerraFusion platform.
It handles user authentication, session management, and access control.
"""

import os
import json
import hashlib
import secrets
import time
from datetime import datetime, timedelta

# Constants
AUTH_DIR = "auth"
USERS_FILE = os.path.join(AUTH_DIR, "users.json")
SESSIONS_FILE = os.path.join(AUTH_DIR, "sessions.json")
SESSION_EXPIRY = 24  # Hours

# Ensure auth directory exists
if not os.path.exists(AUTH_DIR):
    os.makedirs(AUTH_DIR)

# Initialize users file if it doesn't exist
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({"users": {}}, f)

# Initialize sessions file if it doesn't exist
if not os.path.exists(SESSIONS_FILE):
    with open(SESSIONS_FILE, 'w') as f:
        json.dump({"sessions": {}}, f)


def hash_password(password, salt=None):
    """
    Hash a password with a salt using SHA-256.
    
    Args:
        password: The password to hash
        salt: Optional salt to use (generates new one if None)
        
    Returns:
        Tuple of (hash, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return password_hash, salt


def create_user(username, password, role="user"):
    """
    Create a new user.
    
    Args:
        username: Username for the new user
        password: Password for the new user
        role: Role for the new user (default: "user")
        
    Returns:
        True if user created successfully, False if username already exists
    """
    # Load existing users
    with open(USERS_FILE, 'r') as f:
        data = json.load(f)
    
    # Check if username already exists
    if username in data["users"]:
        return False
    
    # Hash password with salt
    password_hash, salt = hash_password(password)
    
    # Create user
    data["users"][username] = {
        "password_hash": password_hash,
        "salt": salt,
        "role": role,
        "created_at": time.time()
    }
    
    # Save updated users
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    
    return True


def authenticate(username, password):
    """
    Authenticate a user.
    
    Args:
        username: Username to authenticate
        password: Password to authenticate
        
    Returns:
        Session token if authentication successful, None otherwise
    """
    # Load users
    with open(USERS_FILE, 'r') as f:
        data = json.load(f)
    
    # Check if username exists
    if username not in data["users"]:
        return None
    
    # Get user data
    user = data["users"][username]
    
    # Hash provided password with user's salt
    password_hash, _ = hash_password(password, user["salt"])
    
    # Check if password matches
    if password_hash != user["password_hash"]:
        return None
    
    # Create session
    session_token = create_session(username, user["role"])
    
    return session_token


def create_session(username, role):
    """
    Create a new session for a user.
    
    Args:
        username: Username for the session
        role: Role of the user
        
    Returns:
        Session token
    """
    # Generate session token
    session_token = secrets.token_hex(32)
    
    # Calculate expiry time
    expiry = datetime.now() + timedelta(hours=SESSION_EXPIRY)
    expiry_timestamp = expiry.timestamp()
    
    # Load existing sessions
    with open(SESSIONS_FILE, 'r') as f:
        data = json.load(f)
    
    # Add new session
    data["sessions"][session_token] = {
        "username": username,
        "role": role,
        "created_at": time.time(),
        "expires_at": expiry_timestamp
    }
    
    # Save updated sessions
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    
    return session_token


def validate_session(session_token):
    """
    Validate a session token.
    
    Args:
        session_token: Session token to validate
        
    Returns:
        User data if session is valid, None otherwise
    """
    # If no token provided, session is invalid
    if not session_token:
        return None
    
    # Load sessions
    with open(SESSIONS_FILE, 'r') as f:
        data = json.load(f)
    
    # Check if session exists
    if session_token not in data["sessions"]:
        return None
    
    # Get session data
    session = data["sessions"][session_token]
    
    # Check if session has expired
    if session["expires_at"] < time.time():
        # Remove expired session
        del data["sessions"][session_token]
        
        # Save updated sessions
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        
        return None
    
    # Get user data
    username = session["username"]
    
    # Load users
    with open(USERS_FILE, 'r') as f:
        user_data = json.load(f)
    
    # Check if user still exists
    if username not in user_data["users"]:
        # Remove session for non-existent user
        del data["sessions"][session_token]
        
        # Save updated sessions
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        
        return None
    
    # Return user data
    return {
        "username": username,
        "role": session["role"]
    }


def invalidate_session(session_token):
    """
    Invalidate a session.
    
    Args:
        session_token: Session token to invalidate
        
    Returns:
        True if session invalidated successfully, False otherwise
    """
    # Load sessions
    with open(SESSIONS_FILE, 'r') as f:
        data = json.load(f)
    
    # Check if session exists
    if session_token not in data["sessions"]:
        return False
    
    # Remove session
    del data["sessions"][session_token]
    
    # Save updated sessions
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    
    return True


def cleanup_expired_sessions():
    """
    Clean up expired sessions.
    
    Returns:
        Number of expired sessions removed
    """
    # Load sessions
    with open(SESSIONS_FILE, 'r') as f:
        data = json.load(f)
    
    # Current time
    current_time = time.time()
    
    # Find expired sessions
    expired_sessions = [
        token for token, session in data["sessions"].items()
        if session["expires_at"] < current_time
    ]
    
    # Remove expired sessions
    for token in expired_sessions:
        del data["sessions"][token]
    
    # Save updated sessions
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    
    return len(expired_sessions)


def create_default_admin():
    """
    Create a default admin user if no users exist.
    
    Returns:
        True if default admin created, False otherwise
    """
    # Load users
    with open(USERS_FILE, 'r') as f:
        data = json.load(f)
    
    # Check if any users exist
    if data["users"]:
        return False
    
    # Create default admin
    return create_user("admin", "terrafusion", "admin")


# Create default admin user if no users exist
create_default_admin()