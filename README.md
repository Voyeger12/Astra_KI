# ASTRA v0.2 - AI Chat Assistant

Intelligente Chat-Anwendung mit lokalem LLM (Ollama), **Live Internet-Suche**, Auto-Learning und Langzeitgedächtnis.
Production-ready mit Sicherheit, Fehlerbehandlung und umfassenden Tests.

### Aktuell (v0.2 Pre-Release)
- ✨ Internet-Suche mit DuckDuckGo (asynchron, non-blocking)
- 🚀 Intelligente Zusammenfassungen für Wetter, Nachrichten, Preise
- 🎯 KI antwortet mit echten, aktuellen Daten
- 📊 Streaming-Output vom LLM (Text kommt in Echtzeit)
- 🔐 Sicherheit & Robustheit auf Beta-Level

## Installation

### Voraussetzungen
- Python 3.8+
- Ollama (https://ollama.ai) - installiert und läuft
- Ein Ollama-Modell (z.B. `ollama pull qwen2.5:14b`)
- Internet-Verbindung (für Web-Suche via DuckDuckGo)

### Setup

```bash
# 1. Virtual Environment erstellen
python -m venv venv
.\venv\Scripts\Activate

# 2. Dependencies installieren
pip install -r requirements.txt

# 3. Ollama starten (separates Terminal)
ollama serve

# 4. App starten
python main.py
```

## Features

- **Chat mit KI**: Lokale LLM-Integration via Ollama mit Stream-Output
- **🔍 Internet-Suche** (NEU): 
  - Automatische Web-Recherche via DuckDuckGo (asynchron!)
  - Intelligente Zusammenfassung für Wetter, Nachrichten, Preise
  - KI antwortet mit echten, aktuellen Daten
  - Erkennt automatisch wenn Suche nötig ist
  - UI bleibt responsive während Suche läuft (non-blocking!)
- **💾 Langzeitgedächtnis**: Auto-Learning von Namen, Alter, Ort, Interessen
- **📱 Multi-Chat**: Mehrere parallele Chat-Sessions
- **🎨 Modernes UI**: PyQt6 mit Gradient-Design (Rot/Orange)
- **🔐 Sicherheit**: Input-Sanitization, Rate-Limiting, SQLite WAL
- **🛡️ Fehlerbehandlung**: Crash-Recovery, Database-Integrität Check
- **⚡ Robustheit**: Concurrent Database Access, Error Scenarios, Retry-Logic

## Testing

```bash
# Schnelle Tests (4 Tests, ~2s)
python tests/test_quick.py

# Fehler-Szenarien (6 Tests, ~5s)
python tests/test_errors.py

# Komplette Suite (18 Tests, ~5s)
python tests/test_suite.py

# Interaktiver Test-Runner
python tests/runner.py
```

## Internet-Suche (v0.2 Feature)

Die KI kann jetzt **automatisch im Internet suchen** für aktuelle Informationen!

### Wie funktioniert es?

1. **Automatische Erkennung**: KI erkennt automatisch wenn Suche nötig ist
   - Wetter-Fragen: "Wie ist das Wetter in Berlin?"
   - Nachrichten: "Aktuelle News zu..."
   - Preise: "Bitcoin Kurs", "Aktien"
   - Oder manuell: "Suche nach...

2. **Asynchrone Suche**: 
   - SearchWorker läuft in separatem QThread
   - UI bleibt immer responsive!
   - Du siehst: "🔍 Suche im Internet..."

3. **Intelligente Zusammenfassung**:
   - Wetter: 🌡️ Temperatur, 🌧️ Regen, ☀️ Sonne
   - Nachrichten: Top 3 Schlagzeilen
   - Allgemein: Zusammengefasste Top 3 Ergebnisse

4. **KI antwortet mit echten Daten**:
   ```
   Du:    "Wie ist das Wetter in Essen?"
   ASTRA: "Das Wetter in Essen ist sonnig mit 12°C, 
           geringer Wind... (mit echten Daten)"
   ```

### Technisch

- **Engine**: DuckDuckGo via [`ddgs`](https://github.com/deedy5/ddgs) Paket
- **Non-blocking**: Läuft asynchron (UI Freeze ❌)
- **Intelligent**: Extrahiert nur relevante Infos
- **Fallback**: Nutzt altes Paket wenn neues nicht da

Siehe [config.py](config.py) für DuckDuckGo-Einstellungen.



```
modules/                    → Core-Funktionalität
  ├── database.py          → SQLite mit WAL, Concurrent Access
  ├── memory.py            → Auto-Learning & Memory Management
  ├── logger.py            → Zentrales Logging
  ├── ollama_client.py     → LLM-Integration mit Streaming
  ├── utils.py             → Security, SearchEngine (🔍 Internet-Suche), RateLimiter
  ├── debug.py             → Diagnostik-Tools
  └── ui/                  → PyQt6 Interface
      ├── main_window.py   → Hauptfenster
      ├── workers.py       → QThread Worker (LLM, Suche, Health Check)
      ├── styles.py        → CSS/Design
      ├── settings_*.py    → Settings Manager & Dialog
      └── colors.py        → UI-Farben

tests/                      → Test-Suite (22 Tests)
  ├── test_quick.py        → Schnelle Tests (4)
  ├── test_errors.py       → Error-Szenarien (6)
  ├── test_suite.py        → Komplette Suite (18)
  └── runner.py            → Menu-basierter Runner

benchmarks/                 → Performance-Tests
  └── bench.py            → Benchmark-Suite

main.py                     → Hauptprogramm mit Crash-Recovery
config.py                   → Centralisierte Konfiguration
requirements.txt            → Dependencies (mit ddgs für Web-Suche!)
build_exe.py               → PyInstaller Build-Script
start.bat                  → Windows Quick-Start
```

## Sicherheit & Robustheit

- ✅ **Input Validation**: XSS-Protection, SQL Injection Prevention
- ✅ **Rate-Limiting**: Max 30 Messages/Minute gegen Abuse
- ✅ **Database**: WAL-Journaling, Concurrent Access, Integrity Checks
- ✅ **Fehlerbehandlung**: Graceful Recovery, No Data Loss
- ✅ **Logging**: Zentral, strukturiert, mit Error-Tracking

## Konfiguration

Editiere `config.py` für:
- Ollama-Modell und Host (Standard: http://localhost:11434)
- Internet-Suche Einstellungen (DuckDuckGo Timeouts, Proxy)
- UI-Einstellungen (Farben, Größe, Fenster-Position)
- Security-Limits (Message-Länge, Rate-Limits)
- Database-Pfad und Timeouts
- Logging Level und Format

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| "Ollama nicht erreichbar" | `ollama serve` in separatem Terminal starten |
| UI startet nicht | `pip install PyQt6>=6.6.0` |
| Database-Fehler | Automatisch beim nächsten Start repariert |
| Rate-Limit erreicht | 60 Sekunden warten bis Limit zurückgesetzt |
| Tests schlagen fehl | `python tests/runner.py` zur Diagnose |

## Build & Release

```bash
# EXE erstellen (mit Internet-Suche!)
python build_exe.py

# Das erstellt: dist/ASTRA AI.exe
# Größe: ~100-150 MB (inkl. PyQt6, ddgs, requests)

# Validierung vor Release
python tests/validate.py

# Perfekt für: GitHub Releases als .exe downloaden
```

Siehe [build_exe.py](build_exe.py) für Details zur Build-Konfiguration.

## Lizenz

MIT License - Frei zur Verwendung und Modifikation.
