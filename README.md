<div align="center">

# 🔴 ASTRA AI

**Dein lokaler KI-Assistent — privat, schnell, intelligent.**

[![Python 3.13+](https://img.shields.io/badge/Python-3.13+-blue?logo=python&logoColor=white)](https://python.org)
[![Tests](https://github.com/Voyeger12/Astra_KI/actions/workflows/python-tests.yml/badge.svg?label=110%20Tests%20Passed)](https://github.com/Voyeger12/Astra_KI/actions)
[![Security](https://img.shields.io/badge/Security-CodeQL-brightgreen?logo=github-actions&logoColor=white)](https://github.com/Voyeger12/Astra_KI/security/code-scanning)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

Moderne Desktop-App mit Echtzeit-Streaming, Langzeitgedächtnis, Internet-Suche und automatischer GPU-Beschleunigung. Läuft komplett lokal über [Ollama](https://ollama.ai).

[![Python 3.13+](https://img.shields.io/badge/Python-3.13+-blue?logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/UI-PyQt6-green?logo=qt)](https://pypi.org/project/PyQt6/)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-black?logo=ollama)](https://ollama.ai)
[![Tests](https://img.shields.io/badge/Tests-99%2F99-brightgreen)](tests/run_tests.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

</div>

---

## ✨ Features

| Feature | Beschreibung |
|---------|-------------|
| 🚀 **Streaming-Antworten** | Text erscheint in Echtzeit, Chunk für Chunk |
| 🧠 **Langzeitgedächtnis** | Merkt sich Namen, Vorlieben, Fakten über `[MERKEN:]`-Tags |
| 🔍 **Internet-Suche** | DuckDuckGo-Integration für aktuelle Infos (Wetter, News, etc.) |
| 🎮 **Auto GPU-Erkennung** | NVIDIA → CUDA, AMD RDNA 3 → ROCm, AMD RDNA 4 → Vulkan, Intel → Vulkan |
| 💬 **Multi-Chat** | Unbegrenzte parallele Chat-Sessions mit separater History |
| ✏️ **Chat-Umbenennung** | Doppelklick oder F2 zum Umbenennen von Chats |
| 🎨 **Rich Formatting** | Markdown-Rendering, Code-Highlighting mit Pygments (Monokai-Theme) |
| 📥 **System-Tray** | Minimiert in die Taskleiste, läuft im Hintergrund weiter |
| 🔄 **Auto-Update** | Prüft GitHub-Releases automatisch auf neue Versionen |
| ⌨️ **Keyboard Shortcuts** | Strg+N, Strg+E, Strg+D, F2, Esc — für schnelles Arbeiten |
| 🩺 **Health-Check** | 7-Kategorien-Systemcheck beim Start (Module, DB, Ollama, GPU, Pakete) |
| ⚙️ **Konfigurierbar** | Modell, Temperatur, Textgröße, Theme über Settings-Dialog |
| 🔒 **Sicherheit** | Input-Validation, Rate-Limiting, XSS/SQLi-Schutz |
| 📦 **Standalone EXE** | Kann als Windows-EXE gebaut werden (keine Python-Installation nötig) |

---

## 🚀 Quick Start

### Voraussetzungen

- **Python 3.13+**
- **Ollama** — [ollama.ai](https://ollama.ai) installieren
- Ein LLM-Modell herunterladen:
  ```bash
  ollama pull qwen2.5:14b    # Empfohlen (~9 GB)
  ```

### Installation

```bash
# Repository klonen
git clone https://github.com/Voyeger12/Astra_KI.git
cd Astra_KI

# Virtual Environment erstellen & aktivieren
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # Linux/Mac

# Dependencies installieren
pip install -r requirements.txt
```

### Starten

```bash
# Option 1: Direkt starten
python main.py

# Option 2: Über das Start-Skript (inkl. Health-Check)
start.bat
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Aktion |
|----------|--------|
| `Strg+N` | Neuer Chat |
| `Strg+,` | Einstellungen öffnen |
| `Strg+E` | Chat exportieren |
| `Strg+D` | Chat löschen |
| `Strg+F` | Eingabefeld fokussieren |
| `F2` | Chat umbenennen |
| `Esc` | Generierung stoppen |

---

## 🎮 GPU-Unterstützung

ASTRA erkennt beim Start automatisch die GPU und setzt die optimalen Ollama-Einstellungen:

| GPU | Backend | Automatisch |
|-----|---------|-------------|
| NVIDIA (alle) | CUDA | ✅ |
| AMD RX 7000 (RDNA 3) | ROCm | ✅ |
| AMD RX 9000 (RDNA 4) | Vulkan | ✅ |
| Intel Arc | Vulkan | ✅ |
| Keine dedizierte GPU | CPU | ✅ |

Die Statusleiste zeigt den aktiven Modus: `🟢 Online ⚡VULKAN` / `⚡CUDA` / `🐢CPU`

---

## 🩺 Health-Check

Der integrierte Health-Check prüft beim Start 7 Kategorien:

```
  --- Module ---        7 kritische Module (DB, Memory, Ollama, UI, GPU, ...)
  --- Dateisystem ---   Verzeichnisse und Konfigurationsdateien
  --- Config ---        Ollama-Host, Modell, Timeouts
  --- Datenbank ---     SQLite-Tabellen und Zugriff
  --- Ollama ---        Server-Erreichbarkeit + Modell-Verfügbarkeit
  --- Hardware ---      GPU-Erkennung (z.B. AMD RX 9070 XT → VULKAN)
  --- Pakete ---        PyQt6, Pygments, Requests, DDGS
```

Ergebnisse: `[OK]` / `[WARN]` / `[FAIL]` / `[INFO]` — bei kritischen Fehlern wird Force-Start angeboten.

---

## 📁 Projektstruktur

```
ASTRA 2.0/
├── main.py                         # Einstiegspunkt mit Crash-Recovery
├── config.py                       # Zentrale Konfiguration
├── start.bat                       # Windows-Launcher mit Health-Check
├── requirements.txt                # Python-Dependencies
├── build_exe.py                    # PyInstaller → Standalone EXE
│
├── modules/
│   ├── database.py                 # SQLite mit WAL-Journaling
│   ├── memory.py                   # Langzeitgedächtnis (MERKEN-Tags)
│   ├── ollama_client.py            # LLM-Streaming mit adaptiven Timeouts
│   ├── gpu_detect.py               # Auto GPU-Erkennung & Konfiguration
│   ├── logger.py                   # Strukturiertes Logging (14-Tage-Rotation)
│   ├── utils.py                    # Security, Rate-Limiting, Suche, HealthCheck
│   ├── updater.py                  # Auto-Update Checker (GitHub Releases)
│   └── ui/
│       ├── main_window.py          # Hauptfenster + System-Tray + Shortcuts
│       ├── chat_display.py         # Chat-Bubbles & Streaming-Anzeige
│       ├── rich_formatter.py       # Markdown → HTML + Pygments Code-Highlighting
│       ├── settings_dialog.py      # Einstellungs-Dialog
│       ├── settings_manager.py     # JSON-basierte Settings (Debounced Save)
│       ├── workers.py              # QThread-Worker (LLM, Suche, Health)
│       ├── styles.py               # Modernes Qt Stylesheet (Pill-Buttons, etc.)
│       └── colors.py               # Farbkonstanten
│
├── config/settings.json            # Benutzer-Einstellungen
├── data/                           # SQLite-Datenbank & Backups
├── logs/                           # Log-Dateien (14-Tage-Rotation)
├── tests/run_tests.py              # 99 Unit-Tests (15 Testklassen)
└── assets/                         # Icons & SVG-Assets
```

---

## ⚙️ Konfiguration

### Settings-Dialog (in der App)

Über das Zahnrad-Icon in der UI einstellbar:
- **Modell** — LLM-Modell wechseln (z.B. qwen2.5:14b, llama3.2, mistral)
- **Temperatur** — Kreativität der Antworten (0.0 = präzise, 1.0 = kreativ)
- **Textgröße** — Schriftgröße im Chat
- **Internet-Suche** — Ein/Aus
- **Gedächtnis** — Ein/Aus

### config.py (für Entwickler)

```python
OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:14b"

# Performance-Tuning
OLLAMA_PERFORMANCE = {
    "keep_alive": "30m",    # Modell im VRAM behalten
    "num_ctx": 4096,        # Context-Window
    "num_batch": 512,       # Batch-Größe
}
MAX_CHAT_HISTORY_MESSAGES = 20  # Kontext-Limit
```

---

## 🧪 Tests

```bash
# Alle 99 Tests ausführen
python tests/run_tests.py

# Verbose-Modus
python tests/run_tests.py -v
```

Getestete Module: Config, Logger, Database, Memory, OllamaClient, RichFormatter, RateLimiter, Security, SearchEngine, TextUtils, SettingsManager, ErrorResilience, HealthChecker, Updater, SystemTray.

---

## 🔧 Troubleshooting

| Problem | Lösung |
|---------|--------|
| 🔴 Offline-Status | Ollama starten: `ollama serve` |
| 🐢 Langsame Antworten | GPU-Backend in Statusleiste prüfen — `CPU` = keine GPU-Beschleunigung |
| Kein Modell verfügbar | `ollama pull qwen2.5:14b` |
| ModuleNotFoundError | `pip install -r requirements.txt` |
| Database locked | App neustarten |
| Suche liefert nichts | Internet-Verbindung prüfen |
| Health-Check FAIL | Fehlende Pakete nachinstallieren |
| Tray-Icon nicht sichtbar | Systemtray-Überlauf in Windows-Einstellungen prüfen |

---

## 📦 Build (Windows EXE)

```bash
python build_exe.py
# inkl. Health-Check vor Build
# Ergebnis: dist/ASTRA AI.exe (~150 MB, standalone)
```

---

## 🔄 Auto-Update

ASTRA prüft beim Start automatisch auf neue GitHub-Releases. Bei verfügbaren Updates erscheint:
- Tray-Benachrichtigung
- Dialog mit Release-Notes und Download-Link

---

## 🛡️ Sicherheit

- **Input-Validation** — XSS- und SQL-Injection-Schutz
- **Rate-Limiting** — Max. 30 Nachrichten pro Minute (thread-safe)
- **SQLite WAL** — Crash-sichere Datenbank mit Thread-Locking
- **Graceful Recovery** — Automatischer Neuversuch bei Fehlern (3x Retry)
- **Chat-Name Validation** — Nur sichere Zeichen erlaubt

---

## 📄 Lizenz

MIT License — Frei zur Verwendung und Modifikation.
