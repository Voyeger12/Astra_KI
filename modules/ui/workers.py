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
    
    def __init__(self, ollama: OllamaClient, model: str, messages: List[Dict], temperature: float = 0.7):
        super().__init__()
        self.ollama = ollama
        self.model = model
        self.messages = messages
        self.temperature = temperature
        self.full_response = ""
    
    def run(self):
        try:
            # Nutze die neue streaming Methode mit Temperature
            for chunk in self.ollama.chat_stream(self.model, self.messages, self.temperature):
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


class RichFormatterWorker(QThread):
    """Worker-Thread für RichFormatter - verhindert UI-Blockierung!
    
    Nutzerfall:
    1. Streaming zeigt Plain-Text (super schnell)
    2. Response fertig → starte RichFormatterWorker
    3. Worker formatiert mit RichFormatter (im Hintergrund)
    4. Signal mit HML zurück an Main-Thread
    5. insertHtml() ist super schnell (nur append, kein format)
    """
    
    finished = pyqtSignal(str)  # Formatiertes HTML
    error = pyqtSignal(str)
    
    def __init__(self, text: str, source: str = "llm", confidence: float = None):
        super().__init__()
        self.text = text
        self.source = source
        self.confidence = confidence
    
    def run(self):
        """Formatiert Text mit RichFormatter im Worker-Thread"""
        try:
            from modules.ui.rich_formatter import RichFormatter
            
            # Formatiere den Text (diese Operation kann langsam sein)
            formatted_html = RichFormatter.format_text(self.text)
            
            # Baue die komplette Bubble mit Badges
            html = self._build_bubble_html(formatted_html)
            
            self.finished.emit(html)
        except Exception as e:
            self.error.emit(f"RichFormatter: {str(e)[:100]}")
    
    def _build_bubble_html(self, formatted_content: str) -> str:
        """Baue komplett fertige Bubble (kein formatieren mehr nötig!)"""
        from modules.ui.colors import COLORS
        
        # Badge für Source
        source_badge = ""
        if self.source == "search":
            source_badge = '<div style="font-size:10px;color:#a8f5a8;margin-bottom:4px;">🔍 Gesucht im Web</div>'
        elif self.source == "llm":
            source_badge = '<div style="font-size:10px;color:#a8d5f5;margin-bottom:4px;">🤖 KI-Antwort</div>'
        elif self.source == "memory":
            conf_pct = int(self.confidence * 100) if self.confidence else 0
            conf_color = "#a8f5a8" if self.confidence >= 0.8 else "#f5d8a8" if self.confidence >= 0.6 else "#f5a8a8"
            source_badge = f'<div style="font-size:10px;color:{conf_color};margin-bottom:4px;">💾 Erinnerung ({conf_pct}%)</div>'
        elif self.source:
            source_badge = f'<div style="font-size:10px;color:#aaa;margin-bottom:4px;">📝 {self.source}</div>'
        
        text_color = COLORS['text']
        primary_color = COLORS['primary']
        font_size = 10  # Default
        
        html = (
            '<table width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td align="left" style="padding:8px 4px;">'
            f'{source_badge}'
            f'<div style="display:inline-block;background:#2a2a2a;color:{text_color};border-radius:20px;padding:12px 18px;margin:8px 4px;border:2px solid {primary_color};max-width:85%;word-wrap:break-word;font-size:{font_size}pt;box-shadow:0 2px 8px rgba(0,0,0,0.5);">'
            f'{formatted_content}'
            '</div>'
            '</td>'
            '<td width="10%"></td>'
            '</tr></table>'
        )
        return html


