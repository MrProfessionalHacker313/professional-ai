import sys
import os

# Add backend to path (from api/ go up to root, then into backend/)
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
sys.path.insert(0, backend_path)

# Import the FastAPI app directly
from app.main import app

# Export for Vercel
__all__ = ['app']
