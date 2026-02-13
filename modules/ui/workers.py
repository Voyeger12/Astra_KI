"""
ASTRA UI - Worker Threads
==========================
QThread-basierte Worker für non-blocking Operationen
"""

from PyQt6.QtCore import QThread, pyqtSignal
from modules.ollama_client import OllamaClient


class LLMStreamWorker(QThread):
    """Worker-Thread für STREAMING LLM-Anfragen - Text kommt in Echtzeit!"""
    
    chunk_received = pyqtSignal(str)  # Einzelner Text-Chunk
    finished = pyqtSignal(str)         # Komplette Antwort
    error = pyqtSignal(str)
    
    def __init__(self, ollama: OllamaClient, model: str, messages: list[dict], temperature: float = 0.7):
        super().__init__()
        self.ollama = ollama
        self.model = model
        self.messages = messages
        self.temperature = temperature
        self.full_response = ""
        self._cancelled = False  # ✅ Cancellation-Flag
    
    def cancel(self):
        """Fordert saubere Abbruch des Workers an."""
        self._cancelled = True
    
    def run(self):
        try:
            from modules.logger import astra_logger
            
            astra_logger.info(f"🚀 LLMStreamWorker.run() started für {self.model}")
            
            chunk_count = 0
            
            # Nutze die neue streaming Methode mit Temperature + Cancel-Check
            for chunk in self.ollama.chat_stream(
                self.model, self.messages, self.temperature,
                cancel_check=lambda: self._cancelled
            ):
                if self._cancelled:
                    astra_logger.info("⛔ LLMStreamWorker abgebrochen")
                    break
                
                chunk_count += 1
                
                if chunk:
                    self.full_response += chunk
                    self.chunk_received.emit(chunk)  # Emit jeden Chunk sofort!
            
            if not self._cancelled:
                astra_logger.info(f"✅ Stream fertig: {chunk_count} Chunks, {len(self.full_response)} Zeichen total")
                self.finished.emit(self.full_response)
            
        except Exception as e:
            if not self._cancelled:
                msg = f"❌ LLMStreamWorker Error: {e}"
                from modules.logger import astra_logger
                astra_logger.error(msg, exc_info=True)
                self.error.emit(f"Fehler: {str(e)}")


class HealthWorker(QThread):
    """Background thread to periodically check Ollama health without blocking UI."""
    alive = pyqtSignal(bool)
    model_loaded = pyqtSignal(bool)  # Signal wenn Model vorgeladen wurde

    def __init__(self, ollama: OllamaClient, interval: float = 2.0, preload_model: str = None):
        super().__init__()
        self.ollama = ollama
        self.interval = interval
        self._stopped = False
        self._preload_model = preload_model
        self._preloaded = False

    def run(self):
        import time
        # ⚡ Beim ersten Start: Modell vorab in VRAM laden
        if self._preload_model and not self._preloaded:
            try:
                ok = self.ollama.preload_model(self._preload_model)
                self._preloaded = True
                self.model_loaded.emit(ok)
            except Exception:
                self.model_loaded.emit(False)
        
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
        self._cancelled = False  # ✅ Cancellation-Flag
    
    def cancel(self):
        """Fordert saubere Abbruch des Workers an."""
        self._cancelled = True
    
    def run(self):
        """Führt die Suche in einem separaten Thread durch"""
        try:
            from modules.utils import SearchEngine
            from modules.logger import astra_logger
            
            astra_logger.info(f"SearchWorker: Suche startet für '{self.query}'")
            
            if self._cancelled:
                return
            
            # Führe Suche durch (blockiert nur diesen Worker, nicht die UI!)
            results = SearchEngine.search(self.query, self.max_results)
            
            if self._cancelled:
                return
            
            astra_logger.info(f"SearchWorker: Suche abgeschlossen - erfolg={results.get('erfolg')}")
            
            self.finished.emit(results)
        except Exception as e:
            if not self._cancelled:
                astra_logger.error(f"SearchWorker Exception: {str(e)[:150]}")
                self.error.emit(f"SearchWorker: {str(e)[:100]}")


class RichFormatterWorker(QThread):
    """Worker-Thread für RichFormatter - verhindert UI-Blockierung!
    
    Nutzerfall:
    1. Streaming zeigt Plain-Text (super schnell)
    2. Response fertig → starte RichFormatterWorker
    3. Worker formatiert mit RichFormatter (im Hintergrund)
    4. Signal mit HTML zurück an Main-Thread
    5. insertHtml() ist super schnell (nur append, kein format)
    """
    
    finished = pyqtSignal(str)  # Formatiertes HTML
    error = pyqtSignal(str)
    
    def __init__(self, text: str, source: str = "llm", confidence: float = None, text_size: int = 10):
        super().__init__()
        self.text = text
        self.source = source
        self.confidence = confidence
        self.text_size = text_size  # Wichtig für einheitliche Schriftgröße!
        self._cancelled = False  # ✅ Cancellation-Flag
    
    def cancel(self):
        """Fordert saubere Abbruch des Workers an."""
        self._cancelled = True
    
    def run(self):
        """Formatiert Text mit RichFormatter im Worker-Thread"""
        try:
            if self._cancelled:
                return
            
            from modules.ui.rich_formatter import RichFormatter
            
            # Formatiere den Text (diese Operation kann langsam sein)
            formatted_html = RichFormatter.format_text(self.text)
            
            if self._cancelled:
                return
            
            self.finished.emit(formatted_html)
        except Exception as e:
            if not self._cancelled:
                self.error.emit(f"RichFormatter: {str(e)[:100]}")


