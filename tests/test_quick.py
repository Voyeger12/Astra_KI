#!/usr/bin/env python3
"""
Standalone Test Suite - Keine UI-Dependencies
"""

import sys
import sqlite3
from pathlib import Path

# Setup Path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_logger():
    """Test Logger-System"""
    print("\n[OK] Testing Logger...")
    from modules.logger import log_info, log_error, get_log_file
    
    log_info("Test-Info Nachricht", "TEST")
    log_error("Test-Error Nachricht", "TEST")
    
    log_file = get_log_file()
    if log_file.exists():
        print(f"  [OK] Log-Datei erstellt: {log_file}")
        return True
    return False


def test_database():
    """Test Datenbank"""
    print("\n[OK] Testing Database...")
    from modules.database import Database
    
    db = Database()
    
    # Check tables
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    tables = ['chats', 'messages', 'memory', 'logs']
    all_exist = True
    
    for table in tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if cursor.fetchone():
            print(f"  [OK] Tabelle '{table}' vorhanden")
        else:
            print(f"  [FAIL] Tabelle '{table}' FEHLT")
            all_exist = False
    
    conn.close()
    return all_exist


def test_memory():
    """Test Memory"""
    print("\n[OK] Testing Memory...")
    from modules.database import Database
    from modules.memory import MemoryManager
    
    db = Database()
    mem = MemoryManager(db)
    
    # Test speichern
    success = mem.learn("Test Memory Entry", "test")
    status = "[OK]" if success else "[FAIL]"
    print(f"  {status} Memory speichern: {success}")
    
    # Test abrufen
    memory_str = mem.get_memory_string()
    has_content = len(memory_str) > 0 and "Noch keine" not in memory_str
    status = "[OK]" if has_content else "[FAIL]"
    print(f"  {status} Memory abrufen: {has_content}")
    
    return success and has_content


def test_auto_learn():
    """Test Auto-Learning"""
    print("\n[OK] Testing Auto-Learning...")
    from modules.database import Database
    from modules.memory import MemoryManager
    
    db = Database()
    mem = MemoryManager(db)
    
    # Test
    result = mem.auto_learn_from_message("Mein Name ist User")
    success = len(result) > 0
    
    if success:
        print(f"  [OK] Auto-Learn erfolgreich: {result}")
    else:
        print(f"  [FAIL] Auto-Learn fehlgeschlagen")
    
    return success


def run_all_tests():
    """Alle Tests ausführen"""
    print("\n" + "="*60)
    print("[TEST] ASTRA STANDALONE TEST SUITE")
    print("="*60)
    
    tests = [
        ("Logger System", test_logger),
        ("Database", test_database),
        ("Memory", test_memory),
        ("Auto-Learning", test_auto_learn),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  [FAIL] Fehler: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("[SUMMARY] TEST-ZUSAMMENFASSUNG")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} - {test_name}")
    
    print(f"\nGesamt: {passed}/{total} Tests erfolgreich ({(passed/total*100):.1f}%)")
    print("="*60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
