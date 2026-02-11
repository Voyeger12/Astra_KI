# ASTRA AI - Release Notes

## Version 2.0.0 - 11. Februar 2026

### 🎉 Highlights
- **Standalone Executable**: Vollständig eigenständige EXE-Datei ohne Python-Installation erforderlich
- **🔍 Live Internet-Suche**: Automatische Web-Recherche mit intelligenter Zusammenfassung (asynchron!)
- **PyQt6 GUI**: Moderne grafische Benutzeroberfläche mit responsivem Design
- **Ollama Integration**: Unterstützung für lokale und Remote-Ollama-Server mit LLM-Streaming
- **💾 Langzeitgedächtnis**: Auto-Learning von persönlichen Informationen

### ✨ Neue Features
- **🌐 Internet-Suche** (HAUPTFEATURE!):
  - DuckDuckGo Integration für aktuelle Daten
  - Intelligente Zusammenfassung (Wetter, Nachrichten, Preise)
  - Asynchrone Suche - UI bleibt immer responsive
  - KI antwortet mit echten, aktuellen Informationen
  - Automatische Erkennung wenn Suche nötig ist
  
- **Stream-Output**: LLM-Antworten kommen in Echtzeit (Text-Chunks)
- **User Profiles**: Personalisierte Einstellungen pro Benutzer
- **Theme Support**: Helle und dunkle Themes mit Custom-Colors
- **Settings Dialog**: Umfassende Konfigurationsoptionen
- **Performance Monitoring**: Integrierte Benchmarking-Tools

### 🐛 Bug Fixes & Improvements
- **PyInstaller Kompatibilität**: Fixed für v6.18.0 (`--windowed` → `-w`, `--buildpath` → `--workpath`)
- **ddgs Paket Upgrade**: Internet-Suche nutzt neues `ddgs` Paket (duckduckgo-search umbenannt)
- **PyQt6 Module Loading**: Verbesserte Hidden-Import-Konfiguration
- **Asynchrone Suche**: SearchWorker blockiert UI nicht mehr
- **Error Handling**: Robustere Fehlerbehandlung mit besseren Fallbacks
- **Logging**: Detailliertes Logging für Debugging aller Features

### 📋 System Requirements
- Windows 10 / 11 (64-bit)
- Mindestens 2GB RAM (4GB empfohlen für snelle Suche)
- **Ollama Installation** (https://ollama.ai) - für LLM Funktionalität
- **Internet-Verbindung** - für Live-Suche Feature
- Optional: Ein LLM-Modell (z.B. qwen2.5:14b, llama2, mistral)

### 📦 Installation & Download
1. Die `ASTRA AI.exe` herunterladen
2. Auf dem Zielcomputer ausführen (keine Installation nötig!)
3. Beim ersten Start werden erforderliche Dateien konfiguriert

### ⚙️ Einstellungen (Optional)
Nach dem ersten Start können folgende Aspekte konfiguriert werden:
- **Server**: Ollama Server-Adresse (lokal oder remote)
- **Modell**: Auswahl des zu verwendenden LLM-Modells
- **Sprache**: UI Sprachauswahl
- **Theme**: UI Erscheinungsbild anpassen

### 🔍 Known Issues / Limitations
- Erstmaliges Starten kann 10-20 Sekunden dauern (Extraktion der Ressourcen)
- DuckDuckGo kann manchmal erhalten leere Ergebnisse (Fallback: KI antwortet aus Wissen)
- Bei sehr schwacher Internet-Verbindung können Timeouts auftreten (10-15 Sekunden)

### 📝 Changelog

#### 2.0.0 (11.02.2026) - Production Ready mit Internet-Suche
**MAJOR:**
- 🔍 Live Internet-Suche mit DuckDuckGo (neu!)
- Asynchrone SearchWorker - UI bleibt responsive (neu!)
- Intelligente Zusammenfassung für Wetter, Nachrichten (neu!)
- System-Prompt aktualisiert für neue Features
- ddgs Paket Integration (Upgrade von duckduckgo_search)

**FEATURES:**
- LLM-Response Streaming (Text kommt in Echtzeit)
- Intelligente Such-Erkennung (auto-detekt wenn nötig)
- Fallback-Handling (altes/neues Paket)
- Detailliertes Logging für alle Such-Operationen
- PyInstaller optimiert für neue Pakete (ddgs, requests)

**FIXES:**
- PyInstaller 6.18.0 Kompatibilität (`-w` statt `--windowed`)
- Fehlerbehandlung für leere DuckDuckGo-Responses
- SearchWorker Exception-Handling
- Pylance Type-Ignore für dynamische Imports
- Build-Script mit allen neuen Hidden-Imports 

### 🤝 Support & Feedback
Probleme gefunden? Issue auf GitHub erstellen oder Kontakt aufnehmen.

### 📄 Lizenz
Siehe LICENSE.md für Details.

---

**Hinweis**: Dies ist eine automatisierte Build. Für neueste Updates, siehe GitHub Releases.
