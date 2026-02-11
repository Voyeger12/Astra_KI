# ASTRA v0.2 - AI Chat Assistant

**Production-Ready** Intelligente Chat-Anwendung mit lokalem LLM (Ollama), Live Internet-Suche, Auto-Learning und Langzeitgedächtnis.

## v0.2 Status: ✅ PRODUCTION READY

- ✨ **Internet-Suche**: DuckDuckGo Integration (asynchron, non-blocking)
- 🚀 **Auto-Learning**: Intelligentes Memory-System (Namen, Ort, Interessen)
- 📊 **Streaming LLM**: Text kommt in Echtzeit
- ⚡ **Performance**: Nachricht sofort sichtbar, <1s UI-Response
- 🔐 **Sicherheit**: Input-Validation, Rate-Limiting, Database-Integrity
- 🧪 **Getestet**: 26/26 Tests ✅ (Database, Memory, Search, Utils)

---

## Installation

### Voraussetzungen

- **Python 3.8+** (getestet mit 3.11)
- **Ollama**: https://ollama.ai (installiert und laufen gelassen)
- **Ein Model**: z.B. `ollama pull qwen2.5:14b` (empfohlen, ~14GB)
  - Alternativen: dolphin-llama3:latest, llama3.2
- **Internet**: Für Web-Suche Feature (optional deaktivierbar)

### Quick Start

**Windows:**
```bash
# 1. Virtual Environment
python -m venv venv
.\venv\Scripts\activate

# 2. Dependencies
pip install -r requirements.txt

# 3. Ollama starten (separates Terminal ZUERST!)
ollama serve

# 4. App starten (im ersten Terminal)
python main.py
```

**Linux/Mac:**
```bash
# 1. Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 2. Dependencies  
pip install -r requirements.txt

# 3. Ollama (separates Terminal)
ollama serve

# 4. App
python main.py
```

### Oder direkt aus Windows EXE
```bash
python build_exe.py        # Erstellt standalone EXE
# Dann: dist/ASTRA\ AI.exe doppelklick
```

---

## Features

### 🔍 Internet-Suche (v0.2)

**Intelligente Web-Recherche mit DuckDuckGo:**
- ✅ Automatische Aktivierung für Info-Fragen
- ✅ Asynchron/Non-Blocking (UI bleibt fluent)
- ✅ Intelligente Zusammenfassung
- ✅ Fallback bei Fehler

**Beispiel:**
```
Du: "Wie ist das Wetter in München?"
ASTRA: "Das Wetter in München ist derzeit sonnig mit 12°C..."
       (mit echten aktuellen Daten von DuckDuckGo)
```

### 💾 Auto-Learning Memory

**Intelligente Informationen-Erfassung:**
- 👤 Namen: "Ich heiße Duncan"
- 📍 Orte: "Ich bin in Essen"
- 🎂 Alter: "Ich bin 28 Jahre alt"
- ❤️ Interessen: "Ich mag Programmierung"

### 📱 Multi-Chat Sessions
- Unbegrenzte parallele Chats
- Jeder Chat mit separater History
- Auto-Delete & Rename

---

## Testing

```bash
# Komplette Suite (26 Tests, ~10s) ✅ ALL PASSING
python tests/test_suite.py

# Mit Details & Interaktiv
python tests/runner.py
```

**Test Coverage:**
- ✅ Database (4 Tests)
- ✅ Memory & Auto-Learning (8 Tests) 
- ✅ Memory System Prompt (2 Tests)
- ✅ Text Utilities (2 Tests)
- ✅ Search Logic (8 Tests)
- **Total: 26/26 PASSING**

---

## Projekt-Struktur

```
📁 ASTRA 2.0
├── main.py                    Hauptprogramm
├── config.py                  Zentrale Konfiguration
├── persona.txt                KI Persona
├── requirements.txt           Dependencies
├── build_exe.py               PyInstaller Builder
│
├── 📁 modules/                Core-Engine
│   ├── database.py            SQLite + WAL
│   ├── memory.py              Auto-Learning
│   ├── ollama_client.py       LLM Integration
│   ├── utils.py               Security, Search
│   └── 📁 ui/                 PyQt6 Interface
│
├── 📁 tests/                  26 Tests ✅
├── 📁 data/                   Datenbank & Backups
├── 📁 logs/                   Logging Output
└── 📁 config/                 Settings (JSON)
```

---

## Sicherheit & Robustheit

| Feature | Status |
|---------|--------|
| Input Validation | ✅ XSS & SQLi Protection |
| Rate-Limiting | ✅ Max 30 Messages/Minute |
| Database | ✅ WAL-Journaling, Concurrent Safe |
| Error Handling | ✅ Graceful Recovery, Retry 3x |
| Async Safety | ✅ Thread-safe Design |
| Logging | ✅ Zentral strukturiert |

---

## Konfiguration

### config.py
```python
OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:14b"
MAX_MESSAGE_LENGTH = 10000
INTERNET_SEARCH_ENABLED = True
```

### config/settings.json (UI-Persistiert)
```json
{
  "text_size": 12,
  "selected_model": "qwen2.5:14b",
  "temperature": 0.77,
  "search_enabled": true,
  "memory_enabled": true
}
```

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| "🔴 Offline" Status | `ollama serve` in separatem Terminal |
| ModuleNotFoundError: PyQt6 | `pip install PyQt6>=6.6.0` |
| database is locked | App neustarten |
| Message nicht sichtbar | `taskkill /F /IM python.exe` |
| Search hängt | Internet-Verbindung prüfen |
| Model zu langsam | `ollama pull llama3.2` (kleiner/schneller) |

---

## Build & Distribution

### Windows EXE
```bash
python build_exe.py   # Erstellt: dist/ASTRA AI.exe (~150MB)
```

**Includes:**
- PyQt6 UI ✅
- Internet-Search ✅  
- Ollama Support ✅
- Keine Python-Installation auf Ziel-PC nötig

### GitHub Release
```bash
git tag v0.2
git push origin v0.2
# Upload: dist/ASTRA AI.exe
```

---

## Roadmap (v0.3+)

- [ ] Speech-to-Text
- [ ] Text-to-Speech  
- [ ] More Models (GPT-4, Claude API)
- [ ] Learning Optimization
- [ ] Dark Mode Toggle

---

## Lizenz

MIT License - Frei zur Verwendung und Modifikation.

---

**Status:** ✅ v0.2 Production Ready | 🧪 26/26 Tests ✅ | ⚡ Optimized & Stable
