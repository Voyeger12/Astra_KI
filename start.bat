@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
cls

REM =========================================================
REM ASTRA AI - Windows Launcher v2.1
REM =========================================================

echo.
echo [START] ASTRA AI v2.0
echo =========================================================
echo Features:
echo   - Streaming LLM-Antworten (Echtzeit)
echo   - Mehrzeilige Eingabe (Shift+Enter)
echo   - Modell-Auto-Erkennung (Live von Ollama)
echo   - Antwort-Statistiken (Tokens/s, Dauer)
echo   - MERKEN-Tag Memory System
echo   - Rich Markdown und Code-Highlighting
echo   - DuckDuckGo Internet-Suche
echo   - Crash-Recovery und Backup-System
echo   - GPU Auto-Erkennung (CUDA/Vulkan/ROCm)
echo.

REM Aktiviere venv falls vorhanden
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Aktiviere Virtual Environment...
    call venv\Scripts\activate.bat
)

REM =========================================================
REM AUTO-UPDATE von GitHub
REM =========================================================
git --version >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Pruefe auf Updates...
    git pull --ff-only 2>nul
    if not errorlevel 1 (
        echo [OK] Neueste Version geladen.
    ) else (
        echo [WARN] Auto-Update fehlgeschlagen - starte mit lokaler Version.
    )
) else (
    echo [INFO] Git nicht installiert - ueberspringe Auto-Update.
)
echo.

REM Pruefe Python Installation
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

REM =========================================================
REM HEALTH-CHECK (modernisiert)
REM =========================================================
echo.
echo [INFO] Health-Check laeuft...
echo ---------------------------------------------------------
python -c "from modules.utils import HealthChecker; import sys; sys.exit(0 if HealthChecker.check(verbose=True) else 1)"
set HC_RESULT=%errorlevel%
echo ---------------------------------------------------------

if %HC_RESULT% NEQ 0 (
    echo.
    echo [ERROR] Health-Check fehlgeschlagen! Kritische Fehler gefunden.
    echo         Bitte ueberpruefen Sie die Installation.
    echo.
    set /p FORCE_START="Trotzdem starten? (j/N): "
    if /i "!FORCE_START!" NEQ "j" (
        echo [ABBRUCH] Start abgebrochen.
        pause
        exit /b 1
    )
    echo [WARN] Start wird trotz Fehlern erzwungen...
)

REM Starte Anwendung (Konsole schliesst sich automatisch nach App-Ende)
echo.
echo [START] Starte ASTRA AI...
echo.
python main.py
exit
