"""API Module"""

import sys
import os

# Ensure parent directory is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes import router

__all__ = ["router"]
