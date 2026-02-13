"""
ASTRA UI - Settings Manager
============================
Verwaltet Benutzereinstellungen und speichert sie persistent
"""

import json
import threading
from pathlib import Path
from typing import Any, Dict


class SettingsManager:
    """Speichert und lädt Benutzereinstellungen in JSON
    
    Verwendet Debounce-Timer damit Slider-Änderungen nicht
    bei jedem Tick auf die Festplatte schreiben.
    """
    
    def __init__(self, config_dir: Path = None):
        """Initialisiere Settings Manager"""
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / 'config'
        
        self.config_dir = config_dir
        self.config_dir.mkdir(exist_ok=True)
        self.settings_file = self.config_dir / 'settings.json'
        self._save_timer: threading.Timer = None
        self._save_lock = threading.Lock()
        self._DEBOUNCE_SECONDS = 0.5  # Speichere frühestens nach 500ms
        
        # Lade DEFAULT_MODEL aus config
        try:
            from config import DEFAULT_MODEL
            default_model = DEFAULT_MODEL
        except ImportError:
            default_model = 'qwen2.5:14b'
        
        # Definiere Defaults mit dem aktuellen DEFAULT_MODEL
        self.DEFAULT_SETTINGS = {
            'text_size': 11,
            'theme': 'dark',
            'search_enabled': True,
            'memory_enabled': True,
            'selected_model': default_model,
            'temperature': 0.7,  # LLM Kreativität (0.0-1.0)
            'max_retries': 3,    # Ollama Verbindungs-Retries
        }
        
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Lade Settings aus Datei oder verwende Defaults"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge mit Defaults (falls neue Keys hinzugekommen)
                    merged = {**self.DEFAULT_SETTINGS, **loaded}
                    return merged
            except Exception as e:
                from modules.logger import astra_logger
                astra_logger.warning(f"Fehler beim Laden von Settings: {e}")
                return self.DEFAULT_SETTINGS.copy()
        
        return self.DEFAULT_SETTINGS.copy()
    
    def save_settings(self):
        """Speichere aktuelle Settings in Datei (sofort, ohne Debounce)"""
        try:
            with self._save_lock:
                with open(self.settings_file, 'w', encoding='utf-8') as f:
                    json.dump(self.settings, f, indent=2)
        except Exception as e:
            from modules.logger import astra_logger
            astra_logger.error(f"Fehler beim Speichern von Settings: {e}")
    
    def _schedule_save(self):
        """Debounced Save — wartet 500ms bevor gespeichert wird.
        Verhindert Festplatten-Spam bei Slider-Änderungen."""
        with self._save_lock:
            if self._save_timer:
                self._save_timer.cancel()
            self._save_timer = threading.Timer(self._DEBOUNCE_SECONDS, self.save_settings)
            self._save_timer.daemon = True
            self._save_timer.start()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Hole einen Setting-Wert"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """Setze einen Setting-Wert und speichere (debounced)"""
        self.settings[key] = value
        self._schedule_save()  # Debounced statt sofort
    
    def get_all(self) -> Dict[str, Any]:
        """Gebe alle Settings zurück"""
        return self.settings.copy()


__all__ = ['SettingsManager']
