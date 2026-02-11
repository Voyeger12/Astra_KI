# ASTRA AI - Release Notes

## Version 2.0.0 - 11. Februar 2026

### 🎉 Highlights
- **Standalone Executable**: Vollständig eigenständige EXE-Datei ohne Python-Installation erforderlich
- **PyQt6 GUI**: Moderne grafische Benutzeroberfläche mit responsivem Design
- **Ollama Integration**: Unterstützung für lokale und Remote-Ollama-Server
- **Datenbankunterstützung**: Persistente Speicherung von Einstellungen und Verlauf

### ✨ Neue Features
- **User Profiles**: Personalisierte Einstellungen pro Benutzer
- **Theme Support**: Helle und dunkle Themes
- **Settings Dialog**: Umfassende Konfigurationsoptionen
- **Performance Monitoring**: Integierte Benchmarking-Tools
- **Logging System**: Detailliertes Logging für Debugging

### 🐛 Bug Fixes
- **PyInstaller 6.18.0 Kompatibilität**: Fixed veraltete Parameter (`--windowed` → `-w`, `--buildpath` → `--workpath`)
- **Module Loading**: Verbesserte Hidden-Import-Konfiguration für PyQt6
- **Error Handling**: Robustere Fehlerbehandlung beim Start

### 📋 System Requirements
- Windows 10 / 11 (64-bit)
- Mindestens 2GB RAM
- Optional: Ollama Installation für erweiterte Features

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

### 🔍 Known Issues
- Erstmaliges Starten kann 10-20 Sekunden dauern (Extraktion der Ressourcen)
- Bei schwacher Internet-Verbindung können Timeouts auftreten

### 📝 Changelog

#### 2.0.0 (11.02.2026)
- Initial Release mit EXE-Build
- Vollständige PyQt6 GUI
- Ollama-Integration
- Datenbank & Logging

### 🤝 Support & Feedback
Probleme gefunden? Issue auf GitHub erstellen oder Kontakt aufnehmen.

### 📄 Lizenz
Siehe LICENSE.md für Details.

---

**Hinweis**: Dies ist eine automatisierte Build. Für neueste Updates, siehe GitHub Releases.
