"""
Vector Database Service Module

Refactored to follow SOLID principles:
- DatabaseManager: Handles database operations
- TextProcessor: Handles text chunking
- VectorDBService: Main service with dependency injection
"""

from .database_manager import DatabaseManager
from .text_processor import TextProcessor
from .vector_db_service import VectorDBService

__all__ = [
    "DatabaseManager",
    "TextProcessor", 
    "VectorDBService"
] 