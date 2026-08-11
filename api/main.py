import sys
import os

# Add backend to path (go up one level from api/ to root, then into backend/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import the FastAPI app
from app.main import app

# Export for Vercel
__all__ = ['app']
