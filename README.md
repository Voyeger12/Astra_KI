# ASTRA 2.0 - AI Chat Assistant

Intelligente Chat-Anwendung mit lokalem LLM (Ollama), Auto-Learning und Langzeitgedächtnis.
Production-ready mit Sicherheit, Fehlerbehandlung und umfassenden Tests.

## Installation

### Voraussetzungen
- Python 3.8+
- Ollama (https://ollama.ai) - installiert und läuft
- Ein Ollama-Modell (z.B. `ollama pull qwen2.5:14b`)

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

- **Chat mit KI**: Lokale LLM-Integration via Ollama
- **Langzeitgedächtnis**: Auto-Learning von Namen, Alter, Ort, Interessen
- **Internet-Suche**: Automatische Web-Recherche via DuckDuckGo
- **Multi-Chat**: Mehrere parallele Chat-Sessions
- **Modernes UI**: PyQt6 mit Gradient-Design (Rot/Orange)
- **Sicherheit**: Input-Sanitization, Rate-Limiting, SQLite WAL
- **Fehlerbehandlung**: Crash-Recovery, Database-Integrität Check
- **Robustheit**: Concurrent Database Access, Error Scenarios

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

Siehe [tests/README.md](tests/README.md) für Details zu Test-Struktur.

## Struktur

```
modules/          → Core-Funktionalität
  ├── database.py → SQLite mit WAL, Concurrent Access
  ├── memory.py   → Auto-Learning & Memory Management
  ├── logger.py   → Zentrales Logging
  ├── ui.py       → PyQt6 Interface mit Rate-Limiting
  ├── ollama_client.py → LLM-Integration
  ├── utils.py    → Security, RateLimiter, Sanitization
  └── debug.py    → Diagnostik-Tools

tests/            → Test-Suite (22 Tests)
  ├── test_quick.py     → Schnelle Tests (4)
  ├── test_errors.py    → Error-Szenarien (6)
  ├── test_suite.py     → Komplette Suite (18)
  └── runner.py         → Menu-basierter Runner

main.py           → Hauptprogramm mit Crash-Recovery
config.py         → Konfiguration
requirements.txt  → Dependencies (Production-ready)
```

## Sicherheit & Robustheit

- ✅ **Input Validation**: XSS-Protection, SQL Injection Prevention
- ✅ **Rate-Limiting**: Max 30 Messages/Minute gegen Abuse
- ✅ **Database**: WAL-Journaling, Concurrent Access, Integrity Checks
- ✅ **Fehlerbehandlung**: Graceful Recovery, No Data Loss
- ✅ **Logging**: Zentral, strukturiert, mit Error-Tracking

## Konfiguration

Editiere `config.py` für:
- Ollama-Modell und Host
- UI-Einstellungen (Farben, Größe)
- Security-Limits (Message-Länge, Rate-Limits)
- Database-Pfad und Timeouts

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
# EXE erstellen
python build_exe.py

# Validierung
python validate.py
```

## Lizenz

MIT License - Frei zur Verwendung und Modifikation.
