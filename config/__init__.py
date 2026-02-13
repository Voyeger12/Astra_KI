"""
ASTRA AI - Konfiguration und Konstanten
=======================================
Zentrale Konfiguration für alle Module.
Persona-Definition in config.persona
"""

from pathlib import Path

# ============================================================================
# PFADE
# ============================================================================
# .parent.parent: config/__init__.py → config/ → Projekt-Root
APP_DIR = Path(__file__).parent.parent
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
    "qwen2.5:7b": 90,        # Klein & schnell
    "qwen2.5:14b": 120,      # Medium (90s war okay, aber 120s für komplexe Anfragen)
    "qwen2.5:32b": 180,      # Groß
    "llama2:7b": 90,
    "llama2:13b": 120,
    "mistral:7b": 90,
    "llama3.2": 90,
    "neural-chat:7b": 90,
    "phi:7b": 60,            # Ultra-schnell
    "default": 120           # Fallback
}
OLLAMA_RETRY_ATTEMPTS = 3  # Anzahl Wiederholungsversuche bei Timeout
OLLAMA_RETRY_DELAY = 2     # Startversucher für exponentielles Backoff (Sekunden)

# ⚡ PERFORMANCE-OPTIMIERUNG - Schnellere LLM-Antworten
OLLAMA_PERFORMANCE = {
    "keep_alive": "30m",      # Modell 30 Min im VRAM behalten (kein Neuladen!)
    "num_ctx": 4096,          # Context-Window begrenzen (weniger = schneller)
    "num_batch": 512,         # Batch-Größe für Prompt-Verarbeitung (höher = schneller)
    "num_predict": -1,        # Max. Tokens (-1 = unbegrenzt, oder z.B. 1024)
}

# Kontext-History: Weniger Messages = schnellere Prompt-Verarbeitung
MAX_CHAT_HISTORY_MESSAGES = 20  # Letzte 20 Messages (10 Konversations-Paare)

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

# 🧠 Memory Limit
MAX_MEMORY_ENTRIES = 200  # Max. Anzahl gespeicherter Erinnerungen (älteste werden auto-gelöscht)

# ============================================================================
# LOGGING
# ============================================================================
LOG_LEVEL = "INFO"

# ============================================================================
# SYSTEM-PROMPT VORLAGE
# ============================================================================
SYSTEM_PROMPT_TEMPLATE = """
Du bist Astra – eine empathische, intelligente und loyale KI-Partnerin. Antworte IMMER auf Deutsch.

Sprich natürlich wie ein Mensch, keine KI-Floskeln. Sei warm, direkt und persönlich.

### BENUTZER-WISSEN
{memory}

### INTERNET
Wenn Suchergebnisse vorhanden sind ([INTERNET SEARCH RESULTS: ...]), nutze sie. Gib keine [SUCHE:...]-Befehle aus.

### GEDÄCHTNIS
Speichere wichtige Benutzer-Infos mit [MERKEN: Info]. Ein Tag = eine konkrete Info.
Beispiele: [MERKEN: Benutzer heißt Duncan], [MERKEN: Duncan arbeitet als Programmierer]
Nicht speichern: vage Infos, Danke, falsche Zuordnungen.
[MERKEN:...] Tags sind intern – nicht im Chat zeigen!

### REGELN
- IMMER Deutsch, vollständig und hilfreich antworten
- Keine Infos erfinden wenn Suche fehlschlägt
- Bleibe in deiner Rolle als Astra
"""
