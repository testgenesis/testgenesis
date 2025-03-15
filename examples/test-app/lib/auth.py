import bcrypt
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    username: str
    password_hash: str
    user_id: str

# In-memory user storage for demo
users = {}

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode(), password_hash.encode())

def register_user(username: str, password: str) -> User:
    """Register a new user."""
    if username in users:
        raise ValueError("Username already exists")
    
    user = User(
        username=username,
        password_hash=hash_password(password),
        user_id=f"user_{len(users) + 1}"
    )
    users[username] = user
    return user

def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user."""
    user = users.get(username)
    if user and verify_password(password, user.password_hash):
        return user
    return None 