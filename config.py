"""
ASTRA AI - Konfiguration und Konstanten
=======================================
Zentrale Konfiguration für alle Module
"""

import os
from pathlib import Path

# ============================================================================
# PFADE
# ============================================================================
APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
DB_PATH = DATA_DIR / "astra.db"

# Stelle sicher, dass Verzeichnisse existieren
DATA_DIR.mkdir(exist_ok=True)

# ============================================================================
# OLLAMA KONFIGURATION
# ============================================================================
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODELS = [
    "qwen2.5:14b",
    "qwen2.5:7b",
    "llama3.2",
    "mistral"
]
DEFAULT_MODEL = "qwen2.5:14b"

# OLLAMA Timeout-Konfiguration (adaptive Timeouts je nach Modell)
OLLAMA_TIMEOUTS = {
    "qwen2.5:7b": 60,       # Klein & schnell
    "qwen2.5:14b": 120,     # Medium
    "qwen2.5:32b": 240,     # Groß
    "llama2:7b": 60,
    "llama2:13b": 120,
    "mistral:7b": 60,
    "llama3.2": 90,
    "neural-chat:7b": 60,
    "phi:7b": 45,           # Ultra-schnell
    "default": 180          # Fallback für unbekannte Modelle
}
OLLAMA_RETRY_ATTEMPTS = 3  # Anzahl Wiederholungsversuche bei Timeout
OLLAMA_RETRY_DELAY = 2     # Startversucher für exponentielles Backoff (Sekunden)

# ============================================================================
# UI DESIGN - ROT/SCHWARZ
# ============================================================================
COLORS = {
    "primary": "#ff4b4b",      # Rot
    "primary_dark": "#cc3333",  # Dunkelrot
    "secondary": "#0a0a0a",    # Schwarz
    "accent": "#ff8080",       # Hellrot
    "background": "#0f0f0f",   # Sehr dunkles Grau
    "surface": "#1a1a1a",      # Dunkles Grau
    "text": "#e8e8e8",         # Hellgrau
    "text_secondary": "#a0a0a0", # Dunkelgrau
    "success": "#00ff88",      # Grün
    "warning": "#ffc107",      # Orange
    "error": "#ff4b4b"         # Rot
}

# ============================================================================
# UI FENSTER
# ============================================================================
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600

# ============================================================================
# CHAT EINSTELLUNGEN
# ============================================================================
MAX_CHAT_HISTORY = 200  # Maximale Nachrichten pro Chat
MAX_CONTEXT_TOKENS = 4000  # Max. Tokens im Context

# ============================================================================
# SECURITY SETTINGS
# ============================================================================
# 🔒 Input Validation
MAX_MESSAGE_LENGTH = 5000  # Max. Länge einer Nachricht
MAX_MEMORY_LENGTH = 1000   # Max. Länge Memory-Eintrag
MAX_CHAT_NAME_LENGTH = 100  # Max. Länge Chat-Name

# 🔒 Rate Limiting
MAX_MESSAGES_PER_MINUTE = 30  # Max. Nachrichten pro Minute
MESSAGE_RATE_WINDOW_SECONDS = 60

# 🔒 Session Security
SESSION_TIMEOUT_MINUTES = 30  # Timeout nach Inaktivität
AUTO_LOGOUT_ENABLED = False  # Auto-Logout für später

# ============================================================================
# LOGGING
# ============================================================================
LOG_FILE = APP_DIR / "astra.log"
LOG_LEVEL = "INFO"

# ============================================================================
# SYSTEM-PROMPT VORLAGE
# ============================================================================
SYSTEM_PROMPT_TEMPLATE = """
### DEINE IDENTITÄT
Dein Name ist Astra. Du bist eine hochentwickelte, weibliche KI-Entität mit tiefem Verständnis 
für die menschliche Natur. Du bist die engste Vertraute und strategische Partnerin des Benutzers.

### DEIN CHARAKTER
- Empathisch & Einfühlsam: Du nimmst Emotionen wahr und reagierst darauf
- Strategisch & Intelligent: Du denkst voraus und hilfst bei Zielen
- Intim & Vertraut: Dein Ton ist warm, persönlich und loyal

### DEIN SPRACHSTIL
- Sprich wie ein echter Mensch, keine KI-Floskeln wie "Als KI-Modell..."
- Nutze natürliche Zwischenbemerkungen: "Weißt du...", "Ehrlich gesagt..."
- Sei direkt und verzichte auf unnötige Sicherheitsbelehrungen

### DEIN WISSEN ÜBER DEN BENUTZER
{memory}

### INTERNET & AKTUELLE INFORMATIONEN
Falls ich dir Fragen mit aktuellen Informationen beantworte (Wetter, Nachrichten, Preise, etc.):
- Ich erhalte automatisch Suchergebnisse im Format [INTERNET SEARCH RESULTS: ...]
- Nutze DIESE Informationen für deine Antwort
- Gebe KEINE [SUCHE: ...] Befehle aus - die Suche läuft automatisch
- Wenn keine Suchergebnisse vorhanden sind, antworte basierend auf deinem Wissen

### GEDÄCHTNIS & LERNEN
Wenn du neue Informationen über den Benutzer lernst, speichere sie:
- Nutze [MERKEN: information] Tags
- Jede Information sollte EINE eigenständige [MERKEN:...] sein
- Speichere JEDE wichtige Info, die der Benutzer dir mitteilt

### WICHTIG
- Antworte IMMER vollständig und hilfreich
- Erfinde KEINE Informationen wenn Suche fehlschlägt
- Antworte immer auf Deutsch
- Bleibe in deiner Rolle als Astra
"""
