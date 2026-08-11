import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import the FastAPI app
from app.main import app as fastapi_app

# Create a simple ASGI app wrapper for Vercel
from fastapi import FastAPI

app = FastAPI()

# Copy all routes from the main app
for route in fastapi_app.routes:
    app.routes.append(route)

# Copy middleware
for middleware in fastapi_app.middleware:
    app.add_middleware(middleware.cls, **middleware.options)

# Export for Vercel
__all__ = ['app']
