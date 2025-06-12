from .rag import routes as rag_routes
from .gen import routes as gen_routes
from .file import routes as file_routes
from .web import routes as web_routes
from .api_key import routes as api_key_routes
from .conversation import routes as conversation_routes
from .system import routes as system_routes

__all__ = [
    "rag_routes", 
    "gen_routes", 
    "file_routes", 
    "web_routes", 
    "api_key_routes", 
    "conversation_routes",
    "system_routes"
]