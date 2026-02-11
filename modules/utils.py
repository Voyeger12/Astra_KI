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
    """Internet-Suche mit DuckDuckGo + intelligente Zusammenfassung"""
    
    @staticmethod
    def needs_search(user_message: str) -> bool:
        """
        Erkennt ob eine Internet-Suche nötig ist
        
        Args:
            user_message: Benutzer-Nachricht
        
        Returns:
            True wenn Search nötig, False sonst
        """
        # Keywords die Internet-Suche erfordern
        search_keywords = [
            # Wetter
            'wetter', 'temperatur', 'regen', 'schnee', 'wind', 'frost', 'hagel',
            'regenwahrscheinlichkeit', 'niederschlag', 'prognose',
            # Nachrichten/Aktuelle Infos
            'nachrichten', 'news', 'aktuell', 'gestern', 'heute', 'morgen',
            'passiert', 'ereignis', 'unfall', 'skandal',
            # Preise/Börse
            'preis', 'kurs', 'bitcoin', 'dollar', 'euro', 'aktie', 'börse',
            # Sportergebnisse
            'ergebnis', 'spiel', 'fußball', 'tor', 'gewonnen', 'meisterschaft',
            # Ortsgebundene Info
            'restaurant', 'hotel', 'adresse', 'öffnungszeit', 'telefon',
            'wie komme ich', 'wo ist', 'nähe von',
            # Allgemeine aktuelle Infos
            'wie ist', 'what is', 'who is', 'aktuelle'
        ]
        
        message_lower = user_message.lower()
        
        # Prüfe ob Suche nötig
        for keyword in search_keywords:
            if keyword in message_lower:
                return True
        
        return False
    
    @staticmethod
    def search(query: str, max_results: int = 5) -> Dict:
        """
        Führt eine Suche mit DuckDuckGo durch und fasst zusammen
        
        Args:
            query: Suchbegriff
            max_results: Maximale Ergebnisse
        
        Returns:
            Dict mit 'erfolg', 'ergebnisse', 'zusammenfassung'
        """
        try:
            import time
            from modules.logger import astra_logger
            
            # Sanitiere Query
            original_query = query
            query = SecurityUtils.sanitize_input(query, max_length=200)
            
            astra_logger.info(f"🔍 Suche gestartet: '{query}'")
            
            results = []
            
            # Versuche DuckDuckGo
            try:
                from duckduckgo_search import DDGS
                astra_logger.info(f"📡 Nutze DuckDuckGo API...")
                
                ddgs = DDGS(timeout=15, proxies=None)
                search_results = ddgs.text(query, max_results=max_results)
                
                # Konvertiere Iterator zu Liste mit Exception-Handling
                results = []
                for i, result in enumerate(search_results):
                    if i >= max_results:
                        break
                    results.append(result)
                    astra_logger.debug(f"  Result {i+1}: {result.get('title', 'N/A')[:50]}")
                
                astra_logger.info(f"✅ DuckDuckGo: {len(results)} Ergebnisse gefunden")
            
            except Exception as ddgs_error:
                astra_logger.warning(f"⚠️ DuckDuckGo fehlgeschlagen: {str(ddgs_error)[:80]}")
                results = []
            
            time.sleep(0.3)  # Rate limiting
            
            if not results:
                astra_logger.warning(f"❌ KEINE Suchergebnisse gefunden für: '{original_query}'")
                
                # Fallback: Vereinfachte Antwort
                return {
                    'erfolg': False,
                    'ergebnisse': [],
                    'zusammenfassung': (
                        f"Konnte keine Suchergebnisse für '{original_query}' finden. "
                        f"Bitte versuchen Sie eine andere Anfrage oder überprüfen Sie Ihre Internetverbindung."
                    )
                }
            
            # Verarbeite Ergebnisse
            formatted_results = []
            all_text = []
            
            for i, r in enumerate(results, 1):
                title = r.get('title', 'Kein Titel')
                body = r.get('body', 'Keine Beschreibung')
                href = r.get('href', 'N/A')
                
                formatted_results.append({
                    'titel': title,
                    'beschreibung': body,
                    'quelle': href,
                    'nummer': i
                })
                
                all_text.append(f"{title}. {body}")
            
            # Erstelle Zusammenfassung basierend auf Query-Typ
            zusammenfassung = SearchEngine._summarize_results(original_query, formatted_results)
            
            astra_logger.info(f"✅ Suchergebnisse verarbeitet und zusammengefasst")
            
            return {
                'erfolg': True,
                'ergebnisse': formatted_results,
                'zusammenfassung': zusammenfassung,
                'original_query': original_query
            }
        
        except ImportError as e:
            astra_logger.error(f"❌ duckduckgo-search Paket nicht verfügbar: {str(e)}")
            return {
                'erfolg': False,
                'ergebnisse': [],
                'zusammenfassung': (
                    "⚠️ Das duckduckgo-search Paket ist nicht installiert.\n"
                    "Installieren Sie es mit: pip install duckduckgo-search\n"
                    "Ich antworte basierend auf meinem Wissen, aber ohne aktuelle Daten."
                )
            }
        except Exception as e:
            astra_logger.error(f"❌ Unerwarteter Fehler bei Suche: {str(e)[:150]}")
            return {
                'erfolg': False,
                'ergebnisse': [],
                'zusammenfassung': f"Fehler bei der Internetsuche: {str(e)[:100]}"
            }
    
    @staticmethod
    def _summarize_results(query: str, results: List[Dict]) -> str:
        """
        Fasst Suchergebnisse intelligent zusammen
        
        Args:
            query: Original-Suchbegriff
            results: Liste der Suchergebnisse
        
        Returns:
            Zusammengefasster Text für die KI
        """
        if not results:
            return "Keine Ergebnisse gefunden."
        
        query_lower = query.lower()
        
        # Wetter-Spezial-Handling
        if any(w in query_lower for w in ['wetter', 'temperatur', 'regen', 'schnee']):
            return SearchEngine._summarize_weather(results, query)
        
        # Nachrichten-Spezial-Handling
        elif any(n in query_lower for n in ['nachrichten', 'news', 'aktuell', 'passiert']):
            return SearchEngine._summarize_news(results, query)
        
        # Standard-Zusammenfassung
        else:
            summary = f"Suchergebnisse zu '{query}':\n\n"
            for r in results[:3]:  # Top 3
                summary += f"• {r['titel']}: {r['beschreibung'][:150]}...\n"
                summary += f"  ({r['quelle']})\n\n"
            return summary
    
    @staticmethod
    def _summarize_weather(results: List[Dict], query: str) -> str:
        """Spezial-Zusammenfassung für Wetter"""
        summary = f"Wetter-Informationen zu '{query}':\n\n"
        
        # Sammle relevante Infos aus den Ergebnissen
        for result in results[:2]:
            beschreibung = result['beschreibung'].lower()
            titel = result['titel']
            
            # Extrahiere Temperatur
            temp_match = re.search(r'(-?\d+)\s*°?c', beschreibung, re.IGNORECASE)
            if temp_match:
                temp = temp_match.group(1)
                summary += f"🌡️ Temperatur: {temp}°C\n"
            
            # Extrahiere Regen
            if 'regen' in beschreibung or 'rain' in beschreibung:
                summary += f"🌧️ Regen wahrscheinlich\n"
            
            if 'sonne' in beschreibung or 'sonnig' in beschreibung:
                summary += f"☀️ Sonnig\n"
            
            if 'bewölkt' in beschreibung or 'cloudy' in beschreibung:
                summary += f"☁️ Bewölkt\n"
            
            # Fallback wenn nichts extrahiert
            if summary == f"Wetter-Informationen zu '{query}':\n\n":
                summary += f"{result['beschreibung'][:200]}\n"
        
        summary += f"\nQuelle: {results[0]['quelle']}"
        return summary
    
    @staticmethod
    def _summarize_news(results: List[Dict], query: str) -> str:
        """Spezial-Zusammenfassung für Nachrichten"""
        summary = f"Aktuelle Nachrichten zu '{query}':\n\n"
        
        for i, result in enumerate(results[:3], 1):
            summary += f"{i}. {result['titel']}\n"
            summary += f"   {result['beschreibung'][:150]}...\n\n"
        
        return summary


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
