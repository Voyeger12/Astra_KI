<div align="center">

# 🔴 ASTRA AI

**Dein lokaler KI-Assistent — privat, schnell, intelligent.**

Moderne Desktop-App mit Echtzeit-Streaming, Langzeitgedächtnis, Internet-Suche und automatischer GPU-Beschleunigung. Läuft komplett lokal über [Ollama](https://ollama.ai).

[![Python 3.13+](https://img.shields.io/badge/Python-3.13+-blue?logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/UI-PyQt6-green?logo=qt)](https://pypi.org/project/PyQt6/)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-black?logo=ollama)](https://ollama.ai)
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
| 🎨 **Rich Formatting** | Markdown-Rendering, Syntax-Highlighting, Code-Blöcke |
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

# Option 2: Über das Start-Skript (Windows)
start.bat
```

> **Hinweis:** Ollama muss im Hintergrund laufen (`ollama serve` oder Ollama Desktop-App). ASTRA erkennt automatisch deine GPU und konfiguriert Ollama für maximale Performance.

---

## 🎮 GPU-Unterstützung

ASTRA erkennt beim Start automatisch die GPU und setzt die optimalen Ollama-Einstellungen:

| GPU | Backend | Automatisch |
|-----|---------|-------------|
| NVIDIA (alle) | CUDA | ✅  |
| AMD RX 7000 (RDNA 3) | ROCm | ✅ |
| AMD RX 9000 (RDNA 4) | Vulkan | ✅ |
| Intel Arc | Vulkan | ✅ |
| Keine dedizierte GPU | CPU | ✅ |

Die Statusleiste zeigt den aktiven Modus: `🟢 Online ⚡VULKAN` / `⚡CUDA` / `🐢CPU`

---

## 📁 Projektstruktur

```
ASTRA 2.0/
├── main.py                         # Einstiegspunkt mit Crash-Recovery
├── config.py                       # Zentrale Konfiguration
├── start.bat                       # Windows-Launcher
├── requirements.txt                # Python-Dependencies
├── build_exe.py                    # PyInstaller → Standalone EXE
│
├── modules/
│   ├── database.py                 # SQLite mit WAL-Journaling
│   ├── memory.py                   # Langzeitgedächtnis (MERKEN-Tags)
│   ├── ollama_client.py            # LLM-Streaming mit adaptiven Timeouts
│   ├── gpu_detect.py               # Auto GPU-Erkennung & Konfiguration
│   ├── logger.py                   # Strukturiertes Logging
│   ├── utils.py                    # Security, Rate-Limiting, Suche
│   └── ui/
│       ├── main_window.py          # Hauptfenster (PyQt6)
│       ├── chat_display.py         # Chat-Bubbles & Streaming-Anzeige
│       ├── rich_formatter.py       # Markdown → HTML Rendering
│       ├── settings_dialog.py      # Einstellungs-Dialog
│       ├── settings_manager.py     # JSON-basierte Settings
│       ├── workers.py              # QThread-Worker (LLM, Suche, Format)
│       ├── styles.py               # Qt Stylesheets
│       └── colors.py               # Farbkonstanten
│
├── config/settings.json            # Benutzer-Einstellungen
├── data/                           # SQLite-Datenbank & Backups
├── logs/                           # Log-Dateien
├── tests/                          # Test-Suite
└── assets/                         # Icons & Assets
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

## 🔧 Troubleshooting

| Problem | Lösung |
|---------|--------|
| 🔴 Offline-Status | Ollama starten: `ollama serve` |
| 🐢 Langsame Antworten | GPU-Backend in Statusleiste prüfen — `CPU` = keine GPU-Beschleunigung |
| Kein Modell verfügbar | `ollama pull qwen2.5:14b` |
| ModuleNotFoundError | `pip install -r requirements.txt` |
| Database locked | App neustarten |
| Suche liefert nichts | Internet-Verbindung prüfen |

---

## 📦 Build (Windows EXE)

```bash
python build_exe.py
# Ergebnis: dist/ASTRA AI.exe (~150 MB, standalone)
```

---

## 🛡️ Sicherheit

- **Input-Validation** — XSS- und SQL-Injection-Schutz
- **Rate-Limiting** — Max. 30 Nachrichten pro Minute
- **SQLite WAL** — Crash-sichere Datenbank
- **Graceful Recovery** — Automatischer Neuversuch bei Fehlern (3x Retry)

---

## 📄 Lizenz

MIT License — Frei zur Verwendung und Modifikation.
