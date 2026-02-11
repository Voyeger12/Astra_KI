"""
ASTRA UI - Worker Threads
==========================
Alle QThread-basierte Worker für non-blocking Operationen
"""

from typing import List, Dict
from PyQt6.QtCore import QThread, pyqtSignal
from modules.ollama_client import OllamaClient


class LLMWorker(QThread):
    """Worker-Thread für LLM-Anfragen (non-blocking)"""
    
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, ollama: OllamaClient, model: str, messages: List[Dict]):
        super().__init__()
        self.ollama = ollama
        self.model = model
        self.messages = messages
    
    def run(self):
        try:
            response = self.ollama.chat(self.model, self.messages)
            if response:
                self.finished.emit(response)
            else:
                self.error.emit("Keine Antwort von Ollama")
        except Exception as e:
            self.error.emit(f"Fehler: {str(e)}")


class LLMStreamWorker(QThread):
    """Worker-Thread für STREAMING LLM-Anfragen - Text kommt in Echtzeit!"""
    
    chunk_received = pyqtSignal(str)  # Einzelner Text-Chunk
    finished = pyqtSignal(str)         # Komplette Antwort
    error = pyqtSignal(str)
    
    def __init__(self, ollama: OllamaClient, model: str, messages: List[Dict]):
        super().__init__()
        self.ollama = ollama
        self.model = model
        self.messages = messages
        self.full_response = ""
    
    def run(self):
        try:
            # Nutze die neue streaming Methode
            for chunk in self.ollama.chat_stream(self.model, self.messages):
                if chunk:
                    self.full_response += chunk
                    self.chunk_received.emit(chunk)  # Emit jeden Chunk sofort!
            
            self.finished.emit(self.full_response)
        except Exception as e:
            self.error.emit(f"Fehler: {str(e)}")


class HealthWorker(QThread):
    """Background thread to periodically check Ollama health without blocking UI."""
    alive = pyqtSignal(bool)

    def __init__(self, ollama: OllamaClient, interval: float = 2.0):
        super().__init__()
        self.ollama = ollama
        self.interval = interval
        self._stopped = False

    def run(self):
        import time
        while not self._stopped:
            try:
                ok = self.ollama.is_alive()
            except Exception:
                ok = False
            self.alive.emit(ok)
            time.sleep(self.interval)

    def stop(self):
        self._stopped = True


class SearchWorker(QThread):
    """Worker-Thread für Internet-Suche (non-blocking UI)"""
    
    finished = pyqtSignal(dict)  # Sendet Suchergebnisse zurück
    error = pyqtSignal(str)
    
    def __init__(self, query: str, max_results: int = 5):
        super().__init__()
        self.query = query
        self.max_results = max_results
    
    def run(self):
        """Führt die Suche in einem separaten Thread durch"""
        try:
            from modules.utils import SearchEngine
            from modules.logger import astra_logger
            
            astra_logger.info(f"SearchWorker: Suche startet für '{self.query}'")
            
            # Führe Suche durch (blockiert nur diesen Worker, nicht die UI!)
            results = SearchEngine.search(self.query, self.max_results)
            
            astra_logger.info(f"SearchWorker: Suche abgeschlossen - erfolg={results.get('erfolg')}")
            
            self.finished.emit(results)
        except Exception as e:
            astra_logger.error(f"SearchWorker Exception: {str(e)[:150]}")
            self.error.emit(f"SearchWorker: {str(e)[:100]}")


__all__ = ['LLMWorker', 'LLMStreamWorker', 'HealthWorker', 'SearchWorker']
