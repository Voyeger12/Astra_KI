"""
ASTRA AI - Utility Funktionen
============================
Verschiedene Hilfsfunktionen + Security Utils
"""

import re
import time
import threading
from typing import List, Dict
from html import escape as html_escape
from collections import defaultdict


class RateLimiter:
    """Rate-Limiting gegen Abuse (thread-safe)"""
    
    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        self._lock = threading.Lock()  # ✅ Thread-Safety
    
    def is_allowed(self, user_id: str = "default") -> bool:
        """Prüft ob Request erlaubt ist"""
        now = time.time()
        with self._lock:
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
        with self._lock:
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
        Sanitiert User-Input — KEIN HTML-Escaping!
        
        HTML-Escaping gehört ausschließlich in die UI-Rendering-Schicht
        (RichFormatter, BubbleWidget). Hier wird nur:
        1. Länge begrenzt
        2. Gefährliche Injection-Pattern blockiert
        
        Args:
            text: Zu sanitierender Text
            max_length: Maximale Länge
        
        Returns:
            Sanitierter Text (raw, kein Escaping)
        """
        if not text:
            return ""
        
        # Länge begrenzen
        if len(text) > max_length:
            text = text[:max_length]
        
        # Blockierte Muster prüfen (auf Raw-Text, VOR jedem Escaping)
        for pattern in SecurityUtils.BLOCKED_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                text = re.sub(pattern, '[BLOCKED]', text, flags=re.IGNORECASE)
        
        return text.strip()

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
        NUR für spezifische Fragen, nicht für allgemeine Aussagen
        
        Args:
            user_message: Benutzer-Nachricht
        
        Returns:
            True wenn Search nötig, False sonst
        """
        import re
        
        message_lower = user_message.lower().strip()
        
        # Nachricht muss mindestens eine Frage sein (? oder Fragekonstruktion)
        # ODER sehr spezifische Such-Keywords enthalten
        
        # Pattern für echte Fragen
        question_patterns = [
            r'wie\s+ist.*(?:wetter|temperatur|prognose)',  # "Wie ist das Wetter"
            r'(?:wetter|temperatur).*(?:morgen|heute|jetzt|prognose)',  # "Wetter morgen"
            r'regen.*(?:heute|morgen)',  # "Regen heute/morgen"
            r'wetter\s*\?',  # "Wetter?"
            r'nachrichten\s*\?',  # "Nachrichten?"
            r'preis\s*\?',  # "Preis?"
            r'kurs\s*\?',  # "Kurs?"
            r'bitcoin.*(?:\?|kurs|preis)',  # "Bitcoin Kurs/Preis?"
            r'(?:gold|dax|dow|nasdaq).*\?',  # Börsen-Indizes
            r'(?:wer|was|wo|wann).*(?:ist|war|aktuell|aktuell).*\?',  # Spezifische Fragen
        ]
        
        # Prüfe die Frage-Patterns
        for pattern in question_patterns:
            if re.search(pattern, message_lower):
                return True
        
        # Spezifische Suchwörter NUR wenn sie allein in der Nachricht stehen
        # oder mit sehr klarem Such-Kontext
        specific_keywords = {
            'bitcoin': [r'\bbitcoin\b.*(?:preis|kurs)', r'(?:preis|kurs).*bitcoin'],
            'dax': [r'\bdax\b.*(?:index|kurs)', r'(?:index|kurs).*dax'],
            'gold': [r'\bgold.*(?:preis|kurs)', r'(?:preis|kurs).*gold'],
        }
        
        for keyword, patterns in specific_keywords.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
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
            
            # Sanitiere Query (nur Länge begrenzen, KEIN HTML-Escape für Suchbegriffe)
            original_query = query
            if len(query) > 200:
                query = query[:200]
            query = query.strip()
            
            astra_logger.info(f"🔍 Suche gestartet: '{query}'")
            
            results = []
            
            # Versuche DuckDuckGo mit neuem Paket
            try:
                from ddgs import DDGS  # type: ignore  # Neu: ddgs statt duckduckgo_search!
                astra_logger.info(f"📡 Nutze DuckDuckGo API (ddgs)...")
                
                ddgs = DDGS(timeout=15)
                search_results = ddgs.text(query, max_results=max_results)
                
                # Konvertiere Iterator zu Liste mit Exception-Handling
                results = []
                for i, result in enumerate(search_results):
                    if i >= max_results:
                        break
                    results.append(result)
                    astra_logger.debug(f"  Result {i+1}: {result.get('title', 'N/A')[:50]}")
                
                astra_logger.info(f"✅ DuckDuckGo: {len(results)} Ergebnisse gefunden")
            
            except ImportError as import_error:
                astra_logger.warning(f"⚠️ Paket 'ddgs' nicht gefunden, versuche altes Paket...")
                try:
                    from duckduckgo_search import DDGS  # type: ignore  # Fallback zu altem Paket
                    astra_logger.info(f"📡 Nutze DuckDuckGo API (duckduckgo_search - veraltet)...")
                    
                    ddgs = DDGS(timeout=15, proxies=None)
                    search_results = ddgs.text(query, max_results=max_results)
                    
                    results = []
                    for i, result in enumerate(search_results):
                        if i >= max_results:
                            break
                        results.append(result)
                    
                    astra_logger.info(f"✅ DuckDuckGo (alt): {len(results)} Ergebnisse gefunden")
                    astra_logger.warning(f"⚠️ BITTE UPDATEN: pip install ddgs")
                
                except Exception as fallback_error:
                    astra_logger.error(f"❌ Beide DuckDuckGo Pakete fehlgeschlagen: {str(fallback_error)[:80]}")
                    results = []
            
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
        
        found_info = False
        
        # Sammle relevante Infos aus den Ergebnissen
        for result in results[:2]:
            beschreibung = result['beschreibung'].lower()
            titel = result['titel']
            
            # Extrahiere Temperatur
            temp_match = re.search(r'(-?\d+)\s*°?c', beschreibung, re.IGNORECASE)
            if temp_match:
                temp = temp_match.group(1)
                summary += f"🌡️ Temperatur: {temp}°C\n"
                found_info = True
            
            # Extrahiere Regen
            if 'regen' in beschreibung or 'rain' in beschreibung:
                summary += f"🌧️ Regen wahrscheinlich\n"
                found_info = True
            
            if 'sonne' in beschreibung or 'sonnig' in beschreibung:
                summary += f"☀️ Sonnig\n"
                found_info = True
            
            if 'bewölkt' in beschreibung or 'cloudy' in beschreibung:
                summary += f"☁️ Bewölkt\n"
                found_info = True
        
        # Fallback: Wenn NICHTS extrahiert werden konnte, nutze rohe Beschreibung
        if not found_info and results:
            summary += f"{results[0]['beschreibung'][:200]}\n"
        
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


class HealthChecker:
    """
    Umfassender Health-Check für ASTRA AI
    ======================================
    Prüft Module, Konnektivität, Dateisystem und Abhängigkeiten.
    Kategorisiert Ergebnisse in KRITISCH / WARNUNG / INFO.
    """

    # Ergebnis-Level
    OK = "OK"
    WARN = "WARN"
    FAIL = "FAIL"
    INFO = "INFO"

    @staticmethod
    def check(verbose: bool = False) -> bool:
        """
        Schneller Health-Check für start.bat (< 2s).
        Prüft nur kritische Module und gibt kompakte Ausgabe.

        Returns:
            True wenn alle kritischen Checks bestanden
        """
        results = HealthChecker.run_all_checks(verbose=verbose)
        HealthChecker._print_results(results, verbose=verbose)
        # Kritisch = nur FAIL-Ergebnisse
        return not any(r["level"] == HealthChecker.FAIL for r in results)

    @staticmethod
    def run_all_checks(verbose: bool = False) -> list:
        """
        Führt alle Health-Checks durch und gibt strukturierte Ergebnisse zurück.

        Returns:
            Liste von Dicts: {"category", "name", "level", "message"}
        """
        results = []
        results.extend(HealthChecker._check_imports())
        results.extend(HealthChecker._check_filesystem())
        results.extend(HealthChecker._check_config())
        results.extend(HealthChecker._check_database())
        results.extend(HealthChecker._check_ollama())
        results.extend(HealthChecker._check_gpu())
        results.extend(HealthChecker._check_dependencies())
        return results

    # ------------------------------------------------------------------
    # 1. Import-Checks (kritisch)
    # ------------------------------------------------------------------
    @staticmethod
    def _check_imports() -> list:
        """Prüft ob alle kritischen Module importierbar sind"""
        results = []
        modules = [
            ("Database",      "modules.database",      "Database"),
            ("Memory",        "modules.memory",        "MemoryManager"),
            ("OllamaClient",  "modules.ollama_client", "OllamaClient"),
            ("UI",            "modules.ui",            "ChatWindow"),
            ("Logger",        "modules.logger",        "astra_logger"),
            ("GPU-Detect",    "modules.gpu_detect",    "detect_gpu"),
            ("RichFormatter", "modules.ui.rich_formatter", "RichFormatter"),
        ]
        for name, mod_path, attr in modules:
            try:
                mod = __import__(mod_path, fromlist=[attr])
                getattr(mod, attr)
                results.append({
                    "category": "Module",
                    "name": name,
                    "level": HealthChecker.OK,
                    "message": "Import OK"
                })
            except Exception as e:
                results.append({
                    "category": "Module",
                    "name": name,
                    "level": HealthChecker.FAIL,
                    "message": str(e)[:120]
                })
        return results

    # ------------------------------------------------------------------
    # 2. Dateisystem-Checks
    # ------------------------------------------------------------------
    @staticmethod
    def _check_filesystem() -> list:
        """Prüft benötigte Verzeichnisse und Dateien"""
        from pathlib import Path
        results = []
        app_dir = Path(__file__).parent.parent

        # Kritische Verzeichnisse
        for name, path in [
            ("data/",   app_dir / "data"),
            ("logs/",   app_dir / "logs"),
            ("config/", app_dir / "config"),
            ("assets/", app_dir / "assets"),
        ]:
            exists = path.exists()
            results.append({
                "category": "Dateisystem",
                "name": name,
                "level": HealthChecker.OK if exists else HealthChecker.WARN,
                "message": "Vorhanden" if exists else "Fehlt — wird bei Start erstellt"
            })

        # Kritische Dateien
        for name, path, critical in [
            ("config.py",          app_dir / "config.py", True),
            ("persona.txt",        app_dir / "persona.txt", False),
            ("assets/check.svg",   app_dir / "assets" / "check.svg", False),
            ("config/settings.json", app_dir / "config" / "settings.json", False),
        ]:
            exists = path.exists()
            level = HealthChecker.OK if exists else (
                HealthChecker.FAIL if critical else HealthChecker.WARN
            )
            results.append({
                "category": "Dateisystem",
                "name": name,
                "level": level,
                "message": "Vorhanden" if exists else ("FEHLT (kritisch)" if critical else "Fehlt")
            })
        return results

    # ------------------------------------------------------------------
    # 3. Config-Checks
    # ------------------------------------------------------------------
    @staticmethod
    def _check_config() -> list:
        """Prüft ob Config-Werte plausibel sind"""
        results = []
        try:
            from config import (
                OLLAMA_HOST, OLLAMA_TIMEOUTS, DEFAULT_MODEL,
                OLLAMA_MODELS, MAX_MESSAGE_LENGTH, COLORS, DATA_DIR
            )

            # Host-Format
            if OLLAMA_HOST.startswith("http"):
                results.append({
                    "category": "Config",
                    "name": "OLLAMA_HOST",
                    "level": HealthChecker.OK,
                    "message": OLLAMA_HOST
                })
            else:
                results.append({
                    "category": "Config",
                    "name": "OLLAMA_HOST",
                    "level": HealthChecker.FAIL,
                    "message": f"Ungültiges Format: {OLLAMA_HOST}"
                })

            # Default-Model in Liste
            if DEFAULT_MODEL in OLLAMA_MODELS:
                results.append({
                    "category": "Config",
                    "name": "DEFAULT_MODEL",
                    "level": HealthChecker.OK,
                    "message": DEFAULT_MODEL
                })
            else:
                results.append({
                    "category": "Config",
                    "name": "DEFAULT_MODEL",
                    "level": HealthChecker.WARN,
                    "message": f"{DEFAULT_MODEL} nicht in OLLAMA_MODELS"
                })

            # Timeouts plausibel
            bad_timeouts = [k for k, v in OLLAMA_TIMEOUTS.items()
                           if not (10 <= v <= 600)]
            if not bad_timeouts:
                results.append({
                    "category": "Config",
                    "name": "Timeouts",
                    "level": HealthChecker.OK,
                    "message": f"{len(OLLAMA_TIMEOUTS)} konfiguriert"
                })
            else:
                results.append({
                    "category": "Config",
                    "name": "Timeouts",
                    "level": HealthChecker.WARN,
                    "message": f"Unplausible Werte: {bad_timeouts}"
                })

        except Exception as e:
            results.append({
                "category": "Config",
                "name": "config.py",
                "level": HealthChecker.FAIL,
                "message": f"Fehler beim Laden: {str(e)[:100]}"
            })
        return results

    # ------------------------------------------------------------------
    # 4. Datenbank-Check (Schnell-Test)
    # ------------------------------------------------------------------
    @staticmethod
    def _check_database() -> list:
        """Prüft DB-Zugriff mit echtem Read-Test"""
        results = []
        try:
            from config import DB_PATH
            if DB_PATH.exists():
                import sqlite3
                conn = sqlite3.connect(str(DB_PATH), timeout=2)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = {row[0] for row in cursor.fetchall()}
                conn.close()

                expected = {'chats', 'messages', 'memory'}
                missing = expected - tables
                if not missing:
                    results.append({
                        "category": "Datenbank",
                        "name": "Tabellen",
                        "level": HealthChecker.OK,
                        "message": f"{len(tables)} Tabellen OK"
                    })
                else:
                    results.append({
                        "category": "Datenbank",
                        "name": "Tabellen",
                        "level": HealthChecker.WARN,
                        "message": f"Fehlende Tabellen: {missing}"
                    })
            else:
                results.append({
                    "category": "Datenbank",
                    "name": "astra.db",
                    "level": HealthChecker.INFO,
                    "message": "Noch nicht erstellt (Erststart)"
                })
        except Exception as e:
            results.append({
                "category": "Datenbank",
                "name": "Zugriff",
                "level": HealthChecker.FAIL,
                "message": str(e)[:120]
            })
        return results

    # ------------------------------------------------------------------
    # 5. Ollama-Konnektivität
    # ------------------------------------------------------------------
    @staticmethod
    def _check_ollama() -> list:
        """Prüft Ollama-Server-Erreichbarkeit und Modelle"""
        results = []
        try:
            import urllib.request
            from config import OLLAMA_HOST, DEFAULT_MODEL

            # Ping API
            req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    import json
                    data = json.loads(resp.read().decode())
                    models = [m.get("name", "") for m in data.get("models", [])]
                    results.append({
                        "category": "Ollama",
                        "name": "Server",
                        "level": HealthChecker.OK,
                        "message": f"Erreichbar — {len(models)} Modelle geladen"
                    })

                    # Prüfe Default-Model
                    # Model-Names können ":latest" enthalten
                    model_base_names = [m.split(":")[0] for m in models]
                    default_base = DEFAULT_MODEL.split(":")[0]
                    if DEFAULT_MODEL in models or default_base in model_base_names:
                        results.append({
                            "category": "Ollama",
                            "name": "Default-Model",
                            "level": HealthChecker.OK,
                            "message": f"{DEFAULT_MODEL} verfügbar"
                        })
                    else:
                        results.append({
                            "category": "Ollama",
                            "name": "Default-Model",
                            "level": HealthChecker.WARN,
                            "message": f"{DEFAULT_MODEL} nicht geladen — pull nötig"
                        })
                else:
                    results.append({
                        "category": "Ollama",
                        "name": "Server",
                        "level": HealthChecker.WARN,
                        "message": f"HTTP {resp.status}"
                    })
        except Exception:
            results.append({
                "category": "Ollama",
                "name": "Server",
                "level": HealthChecker.WARN,
                "message": "Nicht erreichbar — bitte 'ollama serve' starten"
            })
        return results

    # ------------------------------------------------------------------
    # 6. GPU-Erkennung
    # ------------------------------------------------------------------
    @staticmethod
    def _check_gpu() -> list:
        """Prüft GPU-Erkennung"""
        results = []
        try:
            from modules.gpu_detect import detect_gpu
            gpu_info = detect_gpu()
            gpu_name = gpu_info.name if hasattr(gpu_info, 'name') else "Unbekannt"
            backend = gpu_info.backend if hasattr(gpu_info, 'backend') else "cpu"
            results.append({
                "category": "Hardware",
                "name": "GPU",
                "level": HealthChecker.OK if backend != "cpu" else HealthChecker.INFO,
                "message": f"{gpu_name} ({backend.upper()})"
            })
        except Exception as e:
            results.append({
                "category": "Hardware",
                "name": "GPU",
                "level": HealthChecker.INFO,
                "message": f"Erkennung fehlgeschlagen: {str(e)[:80]} — CPU-Fallback"
            })
        return results

    # ------------------------------------------------------------------
    # 7. Abhängigkeiten
    # ------------------------------------------------------------------
    @staticmethod
    def _check_dependencies() -> list:
        """Prüft kritische Python-Pakete"""
        results = []
        # (Anzeigename, Import-Name, Kritisch?)
        packages = [
            ("PyQt6",    "PyQt6",    True),
            ("pygments", "pygments", True),
            ("requests", "requests", True),
            ("ddgs",     "ddgs",     False),  # Optional für Suche
        ]
        for display_name, import_name, critical in packages:
            try:
                __import__(import_name)
                results.append({
                    "category": "Pakete",
                    "name": display_name,
                    "level": HealthChecker.OK,
                    "message": "Installiert"
                })
            except ImportError:
                results.append({
                    "category": "Pakete",
                    "name": display_name,
                    "level": HealthChecker.FAIL if critical else HealthChecker.WARN,
                    "message": "Nicht installiert" + (" (kritisch)" if critical else " (optional)")
                })
        return results

    # ------------------------------------------------------------------
    # Ausgabe
    # ------------------------------------------------------------------
    @staticmethod
    def _print_results(results: list, verbose: bool = False):
        """Gibt Health-Check-Ergebnisse formatiert aus"""
        icons = {
            HealthChecker.OK:   "[  OK  ]",
            HealthChecker.WARN: "[ WARN ]",
            HealthChecker.FAIL: "[ FAIL ]",
            HealthChecker.INFO: "[ INFO ]",
        }

        current_category = None
        ok_count = warn_count = fail_count = 0

        for r in results:
            level = r["level"]
            if level == HealthChecker.OK:
                ok_count += 1
            elif level == HealthChecker.WARN:
                warn_count += 1
            elif level == HealthChecker.FAIL:
                fail_count += 1

            # Im nicht-verbose-Modus nur Warnungen und Fehler zeigen
            if not verbose and level == HealthChecker.OK:
                continue

            # Kategorie-Header
            if r["category"] != current_category:
                current_category = r["category"]
                print(f"\n  --- {current_category} ---")

            icon = icons.get(level, "[????]")
            print(f"  {icon} {r['name']}: {r['message']}")

        # Zusammenfassung
        print(f"\n  {'=' * 50}")
        total = ok_count + warn_count + fail_count
        print(f"  Ergebnis: {ok_count}/{total} OK", end="")
        if warn_count:
            print(f", {warn_count} Warnungen", end="")
        if fail_count:
            print(f", {fail_count} FEHLER", end="")
        print()

        if fail_count == 0:
            print("  Status: BEREIT")
        else:
            print("  Status: KRITISCHE FEHLER — Start nicht empfohlen")
