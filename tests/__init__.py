"""
ASTRA Test Suite
================
Einheitliches Test-Framework für ASTRA 2.0

Verwendung:
    - tests/test_quick.py       : Schnelle Tests (keine UI-Dependencies)
    - tests/runner.py           : Interaktiver Test-Runner mit Diagnose
    - tests/test_suite.py       : Komplette Test-Suite

Beispiel:
    python -m tests.runner      # Interaktiv
    python tests/test_quick.py  # Schnell
"""

__version__ = "0.2"
__all__ = ["test_suite", "test_quick", "runner"]
