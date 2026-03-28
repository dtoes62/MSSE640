"""
Application configuration.

In production, override JWT_SECRET_KEY via the JWT_SECRET_KEY environment variable.
Demo credentials are intentionally simple for coursework; replace with a real user
store before any production deployment.
"""
import os
from typing import Dict

# --- JWT ---
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production-use-a-long-random-string")
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

# --- SQLite audit database ---
SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "audit.db")

# --- Demo user store (username → bcrypt hash of password) ---
# Hash generated from: passlib.context.CryptContext(schemes=["bcrypt"]).hash("secret")
# Password for "admin" is "secret" — change this before any real deployment.
DEMO_USERS: Dict[str, str] = {
    "admin": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
}
