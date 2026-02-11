"""
ASTRA AI - Modul-Initializer
"""

__version__ = "0.2"
__author__ = "Astra Project Contributors"
__description__ = "ASTRA AI - Neural Intelligence Desktop Application"

# Module importieren
from modules.database import Database
from modules.ollama_client import OllamaClient
from modules.memory import MemoryManager
from modules.utils import SearchEngine, TextUtils, SecurityUtils

__all__ = [
    "Database",
    "OllamaClient",
    "MemoryManager",
    "SearchEngine",
    "TextUtils",
    "SecurityUtils"
]
