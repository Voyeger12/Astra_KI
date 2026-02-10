# Tests - ASTRA Test-Suite

Übersicht der Test-Struktur und Verwendung.

## Schnelle Tests (test_quick.py)

**Dauer:** ~2 Sekunden | **Tests:** 4

Prüft grundlegende Funktionalität ohne UI:
- Logger-System
- Datenbank-Tabellen
- Memory-Speicherung
- Auto-Learning

```bash
python tests/test_quick.py
```

## Error-Szenarien (test_errors.py)

**Dauer:** ~5 Sekunden | **Tests:** 6

Testet kritische Fehlerszenarien:
- Corrupted Database Recovery
- Rate-Limiting Funktionalität
- Invalid UTF-8 Handling
- Concurrent Database Access
- Memory mit langen Texten
- Input Validation

```bash
python tests/test_errors.py
```

## Komplette Suite (test_suite.py)

**Dauer:** ~5 Sekunden | **Tests:** 18

Umfangreiche Tests aller Module:
- Database (4 Tests)
- Memory Storage (2 Tests)
- Memory Auto-Learning (1 Test)
- Memory System-Prompt (2 Tests)
- Memory Clear (1 Test)
- Text Utilities (3 Tests)

```bash
python tests/test_suite.py
```

## Interaktiver Runner (runner.py)

**Menü-basiertes Tool** mit 6 Optionen:

1. [TEST] Komplette Test-Suite
2. [DIAG] System-Diagnose
3. [DB] Datenbank-Info
4. [MEM] Memory-Inhalt
5. [QUICK] Schnell-Test
6. [CHAT] Chat-Historie

```bash
python tests/runner.py
```

## Alle Tests ausführen

```bash
# Komplett
python tests/test_quick.py && python tests/test_errors.py && python tests/test_suite.py

# oder
python tests/runner.py  # Option 1
```

## Test-Ergebnisse

Alle Tests sollten mit **100% erfolgreich** abschließen:

```
[SUMMARY] TEST-ZUSAMMENFASSUNG
========================================================
[OK] - Logger System
[OK] - Database
[OK] - Memory
[OK] - Auto-Learning
[OK] - Corrupted Database Recovery
[OK] - Rate-Limiting
[OK] - Invalid UTF-8 & XSS
[OK] - Concurrent DB Access
[OK] - Memory with Long Text
[OK] - Input Validation
...
Gesamt: 22/22 Tests erfolgreich (100.0%)
========================================================
```

## Logs & Debugging

Test-Ausgaben finden sich in:
- Console: Echtzeit-Feedback
- Log-Datei: `astra_YYYYMMDD.log`

```bash
# Letzte Logs anschauen
tail -f astra_*.log
```

## Schnelle Integrations-Check

```bash
python -m pytest --tb=short tests/  # Falls pytest installiert
```

oder manuell:

```bash
# Database OK?
python -c "from modules.database import Database; db=Database(); print('OK')"

# Ollama OK?
python -c "from modules.ollama_client import OllamaClient; c=OllamaClient(); print('ALIVE' if c.is_alive() else 'DEAD')"

# Memory OK?
python -c "from modules.database import Database; from modules.memory import MemoryManager; m=MemoryManager(Database()); print('OK')"
```
