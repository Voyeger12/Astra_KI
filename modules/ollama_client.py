"""
ASTRA AI - Ollama Client
========================
Kommunikation mit Ollama LLM mit adaptiven Timeouts
"""

import requests
import json
from typing import List, Dict
from config import OLLAMA_HOST, OLLAMA_TIMEOUTS, OLLAMA_RETRY_ATTEMPTS, OLLAMA_RETRY_DELAY, OLLAMA_PERFORMANCE


class OllamaClient:
    """Client für Ollama LLM-Anfragen mit intelligenten Timeouts"""
    
    def __init__(self, host: str = OLLAMA_HOST):
        self.host = host
        self.base_url = f"{host}/api"
        # Adaptive Timeouts aus config.py laden
        self.model_timeouts = OLLAMA_TIMEOUTS
        self.max_retries = OLLAMA_RETRY_ATTEMPTS
        self.initial_retry_delay = OLLAMA_RETRY_DELAY
        # ⚡ Performance-Optionen
        self.performance = OLLAMA_PERFORMANCE
    
    def _get_timeout(self, model: str) -> int:
        """Intelligent Timeout basierend auf Modell bestimmen"""
        for model_key, timeout in self.model_timeouts.items():
            if model_key in model:
                return timeout
        return self.model_timeouts.get('default', 120)
    
    def is_alive(self) -> bool:
        """Prüft ob Ollama erreichbar ist"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_available_models(self) -> List[str]:
        """Holt Liste der verfügbaren Modelle"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except Exception:
            return []
    
    def preload_model(self, model: str) -> bool:
        """Lädt ein Modell vorab in den VRAM für sofortige Antworten"""
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={
                    "model": model,
                    "messages": [],
                    "keep_alive": self.performance.get("keep_alive", "30m"),
                },
                timeout=60
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def extract_fact(self, text: str, model: str) -> str:
        """Extrahiert strukturierte Fakten aus natürlicher Sprache via LLM.
        
        Sendet einen kurzen Prompt an das lokale Ollama-Modell um Fakten
        wie Name, Alter, Wohnort etc. aus Freitext zu extrahieren.
        
        Args:
            text: Der zu analysierende Text (z.B. "ich heiße Duncan")
            model: Das zu verwendende Modell
        
        Returns:
            Strukturierter Fakt (z.B. "Name: Duncan") oder Originaltext als Fallback
        """
        prompt = (
            "Du bist ein Daten-Extraktor. Extrahiere den Fakt und antworte EXAKT im Format:\n"
            "Kategorie: Wert\n\n"
            "Kategorien: Name, Alter, Wohnort, Beruf, Lieblingsfarbe, "
            "Lieblingsessen, Hobby, Mag, Rolle, Fakt\n\n"
            "Beispiele:\n"
            "Eingabe: ich heiße Duncan → Name: Duncan\n"
            "Eingabe: ich bin 25 Jahre alt → Alter: 25\n"
            "Eingabe: ich wohne in Berlin → Wohnort: Berlin\n"
            "Eingabe: ich arbeite als Programmierer → Beruf: Programmierer\n"
            "Eingabe: ich mag Pizza → Mag: Pizza\n"
            "Eingabe: meine Lieblingsfarbe ist Rot → Lieblingsfarbe: Rot\n"
            "Eingabe: ich Duncan heiße → Name: Duncan\n"
            "Eingabe: ich in Berlin wohne → Wohnort: Berlin\n"
            "Eingabe: Katzen sind cool → Fakt: Katzen sind cool\n\n"
            f"Eingabe: {text}\n\n"
            "Ausgabe:"
        )
        
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "Du extrahierst Fakten im Format 'Kategorie: Wert'. Antworte NUR mit dem Ergebnis, kein ganzer Satz, keine Anführungszeichen."},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "num_predict": 30,
                    },
                },
                timeout=15
            )
            if response.status_code == 200:
                result = response.json().get("message", {}).get("content", "").strip()
                # Bereinigen: Anführungszeichen, Whitespace, nur erste Zeile
                result = result.strip('"\'\'→ ').strip()
                result = result.split('\n')[0].strip()
                # Validierung: Muss "Kategorie: Wert" Format haben
                if ":" in result and len(result) < 200:
                    # Kategorie und Wert splitten für finale Validierung
                    parts = result.split(":", 1)
                    category = parts[0].strip()
                    value = parts[1].strip() if len(parts) > 1 else ""
                    if value and len(category) < 30:
                        return f"{category}: {value}"
            return text  # Fallback: Originaltext
        except Exception:
            return text  # Fallback: Originaltext
    
    def chat_stream(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.7, callback=None, cancel_check=None):
        """
        Sendet eine Chat-Anfrage mit STREAMING (Text wird in Echtzeit empfangen)
        
        Args:
            model: Modellname
            messages: Chat-Nachrichtenhistorie
            temperature: Kreativitätsgrad
            callback: Funktion die für jeden Text-Chunk aufgerufen wird: callback(chunk_text)
            cancel_check: Optionale Funktion die True zurückgibt wenn abgebrochen werden soll
        
        Yields:
            Einzelne Text-Chunks wie sie vom LLM kommen
        """
        import time
        from .logger import astra_logger
        
        retry_delay = self.initial_retry_delay
        
        for attempt in range(1, self.max_retries + 1):
            try:
                # ⚡ WICHTIG: Zeitouts für Produktionsumgebung
                # - Connect: 10s (Ollama muss schnell antworten)
                # - Read: Adaptiv basierend auf Modell aus config.py!
                connect_timeout = 10
                read_timeout = self._get_timeout(model)
                
                astra_logger.info(f"Chat-Stream an {model} (Attempt {attempt}/{self.max_retries}, Timeout: {read_timeout}s)")
                
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": True,  # WICHTIG: Streaming aktivieren
                    "options": {
                        "temperature": temperature,
                        "num_ctx": self.performance.get("num_ctx", 4096),
                        "num_batch": self.performance.get("num_batch", 512),
                        "num_predict": self.performance.get("num_predict", -1),
                    },
                    "keep_alive": self.performance.get("keep_alive", "30m"),
                }
                
                # 🔥 POST mit reduzierten Timeouts für schnelleres Failover
                astra_logger.info(f"POST request to {self.base_url}/chat (timeout={read_timeout}s)")
                response = requests.post(
                    f"{self.base_url}/chat",
                    json=payload,
                    timeout=(connect_timeout, read_timeout),  # ⚡ (connect, read) timeouts!
                    stream=True
                )
                
                astra_logger.info(f"POST Response: {response.status_code}")
                
                if response.status_code == 200:
                    full_response = ""
                    chunk_count = 0
                    
                    try:
                        for line in response.iter_lines(decode_unicode=True):
                            # ✅ Cancellation-Check
                            if cancel_check and cancel_check():
                                astra_logger.info("⛔ Stream abgebrochen (cancel_check)")
                                return
                            
                            if line:
                                try:
                                    chunk = json.loads(line)
                                    text = chunk.get("message", {}).get("content", "")
                                    if text:
                                        full_response += text
                                        chunk_count += 1
                                        if callback:
                                            callback(text)
                                        yield text
                                except json.JSONDecodeError:
                                    continue
                    finally:
                        response.close()  # ✅ HTTP-Stream IMMER schließen (auch bei cancel/return)
                    
                    astra_logger.info(f"Stream fertig: {len(full_response)} Zeichen, {chunk_count} Chunks")
                    return
                else:
                    response.close()  # ✅ Auch bei Fehler schließen
                    astra_logger.error(f"HTTP {response.status_code}")
                    if attempt < self.max_retries:
                        time.sleep(retry_delay)
                        retry_delay *= 1.5
                        continue
                    yield f"\u274c Ollama HTTP-Fehler: {response.status_code}"
                    return
            except requests.ConnectTimeout as ct:
                msg = f"Connection Timeout (Attempt {attempt}/{self.max_retries})"
                astra_logger.warning(msg)
                if attempt < self.max_retries:
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                    continue
                yield "❌ Verbindung zu Ollama fehlgeschlagen"
                return
                
            except requests.ReadTimeout as rt:
                msg = f"Read Timeout (Attempt {attempt}/{self.max_retries}) - Modell generiert zu langsam!"
                astra_logger.warning(msg)
                if attempt < self.max_retries:
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                    continue
                yield "⏱️ Generierung hat zu lange gedauert - Modell zu langsam?"
                return
                
            except Exception as e:
                msg = f"Stream Error: {str(e)}"
                astra_logger.error(msg, exc_info=True)
                yield f"❌ Fehler: {str(e)}"
                return
