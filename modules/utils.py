"""
ASTRA AI - Utility Funktionen
============================
Verschiedene Hilfsfunktionen + Security Utils
"""

import requests
import html
import re
import time
from typing import List, Dict
from html import escape as html_escape
from collections import defaultdict


class RateLimiter:
    """Rate-Limiting gegen Abuse"""
    
    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, user_id: str = "default") -> bool:
        """Prüft ob Request erlaubt ist"""
        now = time.time()
        
        # Alte Requests entfernen
        cutoff = now - self.window_seconds
        self.requests[user_id] = [t for t in self.requests[user_id] if t > cutoff]
        
        # Prüfe Limit
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        # Registriere neuen Request
        self.requests[user_id].append(now)
        return True
    
    def get_remaining(self, user_id: str = "default") -> int:
        """Gibt verbleibende Requests zurück"""
        now = time.time()
        cutoff = now - self.window_seconds
        self.requests[user_id] = [t for t in self.requests[user_id] if t > cutoff]
        return max(0, self.max_requests - len(self.requests[user_id]))


class SecurityUtils:
    """Sicherheits-Utility-Funktionen"""
    
    # Maximale Input-Größen
    MAX_MESSAGE_LENGTH = 5000
    MAX_MEMORY_LENGTH = 1000
    MAX_CHAT_NAME_LENGTH = 100
    
    # Blockierte Muster (XSS, Injection)
    BLOCKED_PATTERNS = [
        r'<script',
        r'javascript:',
        r'on\w+\s*=',  # Event handler
        r'<iframe',
        r'<object',
        r'<embed',
    ]
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> str:
        """
        Sanitiert User-Input gegen XSS und Injection
        
        Args:
            text: Zu sanitierender Text
            max_length: Maximale Länge
        
        Returns:
            Sanitierter Text
        """
        if not text:
            return ""
        
        # Länge begrenzen
        if len(text) > max_length:
            text = text[:max_length]
        
        # HTML-Entities escapen (gegen XSS)
        text = html_escape(text, quote=True)
        
        # Blockierte Muster prüfen
        for pattern in SecurityUtils.BLOCKED_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                text = re.sub(pattern, '[BLOCKED]', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Entfernt/escaped HTML-Tags aus Text"""
        # Escape alle HTML-Tags
        text = html_escape(text)
        # Ersetze escapedte HTML-Tags mit sicheren Varianten
        text = text.replace('&lt;b&gt;', '<b>')
        text = text.replace('&lt;/b&gt;', '</b>')
        text = text.replace('&lt;i&gt;', '<i>')
        text = text.replace('&lt;/i&gt;', '</i>')
        return text
    
    @staticmethod
    def safe_database_path(path: str) -> str:
        """Prüft ob Pfad sicher ist"""
        import os
        from pathlib import Path
        
        # Vermeide Path Traversal
        if '..' in path or path.startswith('/'):
            raise ValueError("Unsicherer Pfad!")
        
        # Absolute Path
        full_path = Path(path).resolve()
        return str(full_path)
    
    @staticmethod
    def validate_chat_name(name: str) -> bool:
        """Validiert Chat-Namen"""
        if not name or len(name) > SecurityUtils.MAX_CHAT_NAME_LENGTH:
            return False
        # Nur alphanumeric, Umlaute, Leerzeichen, - und _
        return bool(re.match(r'^[a-zA-ZäöüßÄÖÜ0-9\s\-_]+$', name))


class SearchEngine:
    """Internet-Suche mit DuckDuckGo"""
    
    @staticmethod
    def search(query: str, max_results: int = 3) -> str:
        """
        Führt eine Suche mit DuckDuckGo durch
        
        Args:
            query: Suchbegriff
            max_results: Maximale Ergebnisse
        
        Returns:
            Formatierte Suchergebnisse oder Fehlermeldung
        """
        try:
            # Sanitiere Query
            query = SecurityUtils.sanitize_input(query, max_length=200)
            
            from duckduckgo_search import DDGS
            
            results = DDGS().text(query, max_results=max_results)
            
            if not results:
                return "Keine Suchergebnisse gefunden."
            
            formatted = []
            for i, r in enumerate(results, 1):
                title = html_escape(r.get('title', 'Kein Titel'))
                body = html_escape(r.get('body', 'Keine Beschreibung'))
                href = html_escape(r.get('href', 'N/A'))
                
                formatted.append(
                    f"{i}. **{title}**\n"
                    f"   {body}\n"
                    f"   Quelle: {href}"
                )
            
            return "\n\n".join(formatted)
        
        except ImportError:
            return "⚠️ duckduckgo_search nicht installiert"
        except Exception as e:
            return f"Fehler bei der Suche: [Blocked]"


class TextUtils:
    """Text-Hilfsfunktionen"""
    
    @staticmethod
    def truncate(text: str, max_length: int = 100) -> str:
        """Kürzt Text auf maximale Länge"""
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text
    
    @staticmethod
    def format_timestamp(iso_string: str) -> str:
        """Formatiert ISO-Timestamp in lesbares Format"""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(iso_string)
            return dt.strftime("%d.%m.%Y %H:%M")
        except:
            return iso_string


class HealthChecker:
    """Schneller Health-Check für Start-Zeit (< 500ms)"""
    
    @staticmethod
    def check() -> bool:
        """
        Prüft ob alle kritischen Module laden
        Schnell: Nur Imports, keine echten Tests
        
        Returns:
            True wenn alles OK, False wenn Fehler
        """
        checks = []
        
        # Check 1: Database Module
        try:
            from modules.database import Database
            checks.append(("Database", True, None))
        except Exception as e:
            checks.append(("Database", False, str(e)))
        
        # Check 2: Memory Module
        try:
            from modules.memory import MemoryManager
            checks.append(("Memory", True, None))
        except Exception as e:
            checks.append(("Memory", False, str(e)))
        
        # Check 3: Ollama Client
        try:
            from modules.ollama_client import OllamaClient
            checks.append(("OllamaClient", True, None))
        except Exception as e:
            checks.append(("OllamaClient", False, str(e)))
        
        # Check 4: UI Module
        try:
            from modules.ui import ChatWindow
            checks.append(("UI", True, None))
        except Exception as e:
            checks.append(("UI", False, str(e)))
        
        # Check 5: Utils Module
        try:
            from modules.utils import SecurityUtils, RateLimiter
            checks.append(("Utils", True, None))
        except Exception as e:
            checks.append(("Utils", False, str(e)))
        
        # Ausgabe
        all_ok = True
        for name, ok, error in checks:
            status = "[OK]" if ok else "[FAIL]"
            print(f"  {status} {name}")
            if not ok:
                print(f"       Fehler: {error}")
                all_ok = False
        
        return all_ok
