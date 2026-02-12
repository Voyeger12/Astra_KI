@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
cls

REM =========================================================
REM ASTRA AI - Windows Launcher
REM v2.0
REM =========================================================

echo.
echo [START] ASTRA AI v2.0
echo =========================================================
echo Features:
echo   - Streaming LLM-Antworten (Echtzeit)
echo   - MERKEN-Tag Memory System
echo   - Rich Markdown und Code-Highlighting
echo   - DuckDuckGo Internet-Suche
echo   - Crash-Recovery und Backup-System
echo.

REM Pruefe Python Installation
REM Aktiviere venv falls vorhanden
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Aktiviere Virtual Environment...
    call venv\Scripts\activate.bat
)

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python nicht gefunden!
    echo Bitte installieren Sie Python von https://www.python.org
    pause
    exit /b 1
)

REM Pruefe und installiere Abhaengigkeiten
echo [INFO] Pruefe Abhaengigkeiten...
pip show PyQt6 >nul 2>&1
if errorlevel 1 (
    echo [INFO] Abhaengigkeiten nicht installiert. Installiere jetzt...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Installation fehlgeschlagen!
        pause
        exit /b 1
    )
)

REM Pruefe Ollama-Verbindung
echo.
echo [INFO] Pruefe Ollama-Verbindung...
python -c "from modules.ollama_client import OllamaClient; client = OllamaClient(); exit(0 if client.is_alive() else 1)" >nul 2>&1

if errorlevel 1 (
    echo [WARN] Ollama laeuft nicht auf http://localhost:11434
    echo.
    echo Starten Sie Ollama mit einem neuen Terminal-Fenster:
    echo   ollama serve
    echo.
    echo Die Anwendung wird trotzdem gestartet.
    echo.
    pause
)

REM Health-Check Module
echo.
echo [INFO] Health-Check Module...
python -c "from modules.utils import HealthChecker; exit(0 if HealthChecker.check() else 1)"

if errorlevel 1 (
    echo.
    echo [ERROR] Module-Check fehlgeschlagen!
    echo Bitte ueberpruefen Sie die Installation.
    pause
    exit /b 1
)

REM Starte Anwendung
echo.
echo [START] Starte ASTRA AI...
echo.
python main.py

pause
