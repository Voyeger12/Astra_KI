chcp 65001 >nul
@echo off
REM ASTRA AI - Windows Batch Starter
REM Production-Ready Version mit Sicherheit & Error-Handling
REM =========================================================

echo.
echo [START] ASTRA AI - Neural Intelligence
echo =========================================================
echo Features: Hybrid Memory, Rate-Limiting, Crash-Recovery
echo.

REM Prüfe Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python nicht gefunden!
    echo Bitte installieren Sie Python von https://www.python.org
    pause
    exit /b 1
)

REM Prüfe Abhängigkeiten
echo [INFO] Prüfe Abhängigkeiten...
pip show PyQt6 >nul 2>&1
if errorlevel 1 (
    echo [INFO] Abhängigkeiten nicht installiert. Installiere jetzt...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Installation fehlgeschlagen!
        pause
        exit /b 1
    )
)

REM Prüfe Ollama
echo.
echo [INFO] Prüfe Ollama-Verbindung...
python -c "from modules.ollama_client import OllamaClient; client = OllamaClient(); exit(0 if client.is_alive() else 1)" >nul 2>&1

if errorlevel 1 (
    echo [WARN] Ollama läuft nicht auf http://localhost:11434
    echo.
    echo Starten Sie Ollama mit einem neuen Terminal-Fenster:
    echo   ollama serve
    echo.
    echo Die Anwendung wird trotzdem gestartet.
    echo.
    pause
)

REM Health-Check vor Start
echo.
echo [INFO] Health-Check Module...
python -c "from modules.utils import HealthChecker; exit(0 if HealthChecker.check() else 1)"

if errorlevel 1 (
    echo.
    echo [ERROR] Module-Check fehlgeschlagen!
    echo Bitte überprüfen Sie die Installation.
    pause
    exit /b 1
)

REM Starte Anwendung
echo.
echo [START] Starte ASTRA AI...
echo [INFO] Mit Hybrid Memory, Rate-Limiting und Crash-Recovery
echo.
python main.py

pause
