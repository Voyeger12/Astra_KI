"""
ASTRA AI - Ollama Client
========================
Kommunikation mit Ollama LLM mit adaptiven Timeouts
"""

import requests
import json
from typing import Optional, List, Dict
from config import OLLAMA_HOST, OLLAMA_TIMEOUTS, OLLAMA_RETRY_ATTEMPTS, OLLAMA_RETRY_DELAY


class OllamaClient:
    """Client für Ollama LLM-Anfragen mit intelligenten Timeouts"""
    
    def __init__(self, host: str = OLLAMA_HOST):
        self.host = host
        self.base_url = f"{host}/api"
        # Adaptive Timeouts aus config.py laden
        self.model_timeouts = OLLAMA_TIMEOUTS
        self.max_retries = OLLAMA_RETRY_ATTEMPTS
        self.initial_retry_delay = OLLAMA_RETRY_DELAY
    
    def _get_timeout(self, model: str) -> int:
        """Intelligent Timeout basierend auf Modell bestimmen"""
        for model_key, timeout in self.model_timeouts.items():
            if model_key != "default" and model_key in model:
                return timeout
        return self.model_timeouts["default"]
    
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
    
    def chat_stream(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.7, callback=None):
        """
        Sendet eine Chat-Anfrage mit STREAMING (Text wird in Echtzeit empfangen)
        
        Args:
            model: Modellname
            messages: Chat-Nachrichtenhistorie
            temperature: Kreativitätsgrad
            callback: Funktion die für jeden Text-Chunk aufgerufen wird: callback(chunk_text)
        
        Yields:
            Einzelne Text-Chunks wie sie vom LLM kommen
        """
        import time
        from .logger import astra_logger
        
        retry_delay = self.initial_retry_delay
        
        for attempt in range(1, self.max_retries + 1):
            try:
                timeout = self._get_timeout(model)
                astra_logger.info(f"Chat-Stream an {model} (Attempt {attempt}/{self.max_retries})")
                
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": True,  # WICHTIG: Streaming aktivieren
                    "temperature": temperature
                }
                
                response = requests.post(
                    f"{self.base_url}/chat",
                    json=payload,
                    timeout=timeout,
                    stream=True
                )
                
                if response.status_code == 200:
                    full_response = ""
                    for line in response.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                text = chunk.get("message", {}).get("content", "")
                                if text:
                                    full_response += text
                                    if callback:
                                        callback(text)
                                    yield text
                            except json.JSONDecodeError:
                                continue
                    astra_logger.info(f"Stream abgeschlossen, {len(full_response)} Zeichen empfangen")
                    return
                else:
                    astra_logger.error(f"HTTP {response.status_code}")
                    if attempt < self.max_retries:
                        time.sleep(retry_delay)
                        retry_delay *= 1.5
                        continue
                    
            except requests.Timeout:
                astra_logger.warning(f"Stream Timeout (Attempt {attempt}/{self.max_retries})")
                if attempt < self.max_retries:
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                    continue
                yield "⏱️ Stream Timeout"
                return
                
            except Exception as e:
                astra_logger.error(f"Stream Error: {str(e)}")
                yield f"❌ Fehler: {str(e)}"
                return
    
    def chat(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.7) -> Optional[str]:
        """
        Sendet eine Chat-Anfrage an Ollama mit intelligenter Retry-Logik
        
        Args:
            model: Modellname
            messages: List of {"role": "user"/"assistant"/"system", "content": "..."}
            temperature: Kreativität (0.0-1.0)
        
        Returns:
            Vollständige Antwort als String oder None bei Fehler
        """
        import time
        from .logger import astra_logger
        
        retry_delay = self.initial_retry_delay
        
        for attempt in range(1, self.max_retries + 1):
            try:
                timeout = self._get_timeout(model)
                astra_logger.info(f"Chat-Anfrage an {model} (Attempt {attempt}/{self.max_retries}, Timeout: {timeout}s)")
                
                start_time = time.time()
                
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "temperature": temperature
                }
                
                response = requests.post(
                    f"{self.base_url}/chat",
                    json=payload,
                    timeout=timeout
                )
                
                elapsed = time.time() - start_time
                astra_logger.info(f"Chat-Response erhalten in {elapsed:.2f}s")
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("message", {}).get("content", "")
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text[:100]}"
                    astra_logger.error(f"Chat-Fehler: {error_msg}")
                    if attempt < self.max_retries:
                        astra_logger.info(f"Retry in {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay *= 1.5
                        continue
                    return f"❌ Ollama-Fehler: {response.status_code}"
                    
            except requests.Timeout:
                elapsed = time.time() - start_time
                astra_logger.warning(f"Timeout nach {elapsed:.1f}s (Attempt {attempt}/{self.max_retries})")
                
                if attempt < self.max_retries:
                    # Adaptives Backoff-Delay
                    astra_logger.info(f"Retry mit erhöhtem Timeout...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                    continue
                else:
                    timeout = self._get_timeout(model)
                    msg = f"⏱️ Ollama antwortet nicht schnell genug (Timeout nach {attempt} Versuchen)"
                    astra_logger.error(msg)
                    return msg
                    
            except requests.ConnectionError:
                astra_logger.error(f"Verbindungsfehler zu Ollama (Attempt {attempt}/{self.max_retries})")
                if attempt < self.max_retries:
                    astra_logger.info(f"Retry in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                    continue
                return "🔴 Verbindungsfehler: Ollama läuft nicht"
                
            except Exception as e:
                astra_logger.error(f"Fehler in chat(): {str(e)}")
                return f"❌ Fehler: {str(e)}"
        
        return "❌ Alle Versuche aufgebraucht"
    
    def generate(self, model: str, prompt: str, temperature: float = 0.7) -> Optional[str]:
        """
        Einfacher Generate-Call (nicht chat-basiert) mit Retry-Logik
        
        Args:
            model: Modellname
            prompt: Der Prompt
            temperature: Kreativität
        
        Returns:
            Vollständige Antwort oder None
        """
        import time
        from .logger import astra_logger
        
        retry_delay = self.initial_retry_delay
        
        for attempt in range(1, self.max_retries + 1):
            try:
                timeout = self._get_timeout(model)
                astra_logger.info(f"Generate-Anfrage an {model} (Attempt {attempt}/{self.max_retries}, Timeout: {timeout}s)")
                
                start_time = time.time()
                
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature
                }
                
                response = requests.post(
                    f"{self.base_url}/generate",
                    json=payload,
                    timeout=timeout
                )
                
                elapsed = time.time() - start_time
                astra_logger.info(f"Generate-Response erhalten in {elapsed:.2f}s")
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "")
                else:
                    astra_logger.error(f"Generate-Fehler: HTTP {response.status_code}")
                    if attempt < self.max_retries:
                        time.sleep(retry_delay)
                        retry_delay *= 1.5
                        continue
                    return f"❌ Ollama-Fehler: {response.status_code}"
                    
            except requests.Timeout:
                astra_logger.warning(f"Timeout in generate() (Attempt {attempt}/{self.max_retries})")
                if attempt < self.max_retries:
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                    continue
                return "⏱️ Timeout"
                
            except requests.ConnectionError:
                astra_logger.error(f"ConnectionError in generate() (Attempt {attempt}/{self.max_retries})")
                if attempt < self.max_retries:
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                    continue
                return "🔴 Ollama läuft nicht"
                
            except Exception as e:
                astra_logger.error(f"Fehler in generate(): {str(e)}")
                return f"❌ Fehler: {str(e)}"
        
        return "❌ Alle Versuche aufgebraucht"
