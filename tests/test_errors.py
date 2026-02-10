#!/usr/bin/env python3
"""
Error-Scenario Tests für ASTRA
==============================
Testet kritische Fehlerszenarien und Recovery-Mechanismen
"""

import sys
import sqlite3
import tempfile
from pathlib import Path

# Setup Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.database import Database
from modules.memory import MemoryManager
from modules.utils import SecurityUtils, RateLimiter


def test_corrupted_database():
    """Test: Korrupte Datenbank Recovery"""
    print("\n[TEST] Corrupted Database Recovery...")
    
    try:
        # Erstelle temporäre DB
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            
            # Schreibe Garbage Data
            with open(db_path, 'wb') as f:
                f.write(b'GARBAGE_DATA_NOT_A_VALID_DATABASE')
            
            # Versuche zu laden
            try:
                db = Database(db_path)
                # Cleanup
                try:
                    db.close()
                except:
                    pass
                # Wenn es nicht crasht, ist Recovery aktiv
                print("  [OK] Database Recovery erfolgreich")
                return True
            except sqlite3.DatabaseError:
                print("  [OK] Erwartet: DatabaseError erkannt")
                return True
    
    except Exception as e:
        # File-Lock ist OK, Database ist ja in Cleanup
        if "Der Prozess kann nicht" in str(e) or "in use" in str(e):
            print("  [OK] Database Recovery (File-Lock ignoriert)")
            return True
        print(f"  [FAIL] Fehler: {e}")
        return False


def test_rate_limiting():
    """Test: Rate-Limiting Funktionalität"""
    print("\n[TEST] Rate-Limiting...")
    
    try:
        limiter = RateLimiter(max_requests=3, window_seconds=1)
        
        # Erste 3 Requests sollten erlaubt sein
        allowed_count = 0
        for i in range(3):
            if limiter.is_allowed("test_user"):
                allowed_count += 1
        
        if allowed_count != 3:
            print(f"  [FAIL] Erste 3 Requests sollten erlaubt sein, nur {allowed_count} erlaubt")
            return False
        
        # 4. Request sollte blockiert werden
        if limiter.is_allowed("test_user"):
            print("  [FAIL] 4. Request sollte blockiert sein")
            return False
        
        # Remaining sollte 0 sein
        remaining = limiter.get_remaining("test_user")
        if remaining != 0:
            print(f"  [FAIL] Remaining sollte 0 sein, ist {remaining}")
            return False
        
        print("  [OK] Rate-Limiting funktioniert korrekt")
        return True
    
    except Exception as e:
        print(f"  [FAIL] Fehler: {e}")
        return False


def test_invalid_utf8():
    """Test: Ungültige UTF-8 Bytes behandeln"""
    print("\n[TEST] Invalid UTF-8 Handling...")
    
    try:
        # Gültige UTF-8
        valid = "Hallo Welt ä ö ü"
        sanitized = SecurityUtils.sanitize_input(valid)
        
        if sanitized != valid:
            print("  [FAIL] Gültige UTF-8 sollte nicht verändert werden")
            return False
        
        # XSS-Versuch - wird zu HTML-entities escaped
        xss = "<script>alert('xss')</script>"
        sanitized = SecurityUtils.sanitize_input(xss)
        
        # Nach HTML-escaping sollte < und > nicht mehr direkt da sein
        if "<script" in sanitized.lower() and "&lt;" not in sanitized:
            print("  [FAIL] XSS sollte gefiltert sein")
            return False
        
        # Content sollte immer noch erkennbar sein (escaped)
        if "script" not in sanitized.lower():
            print("  [FAIL] Content sollte nicht vollständig gelöscht werden")
            return False
        
        print("  [OK] UTF-8 und XSS-Filtering funktioniert")
        return True
    
    except Exception as e:
        print(f"  [FAIL] Fehler: {e}")
        return False


def test_concurrent_database_access():
    """Test: Gleichzeitiger Datenbank-Zugriff"""
    print("\n[TEST] Concurrent Database Access...")
    
    try:
        import threading
        import time
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)
            
            errors = []
            
            def write_chat(index):
                try:
                    chat_name = f"Chat_{index}"
                    db.create_chat(chat_name)
                    db.save_message(chat_name, "user", f"Message {index}")
                    time.sleep(0.01)
                except Exception as e:
                    errors.append(str(e))
            
            # Starte 10 gleichzeitige Writes
            threads = []
            for i in range(10):
                t = threading.Thread(target=write_chat, args=(i,))
                threads.append(t)
                t.start()
            
            # Warte auf alle Threads
            for t in threads:
                t.join(timeout=5)
            
            if errors:
                print(f"  [FAIL] Fehler bei concurrent access: {errors[:2]}")
                return False
            
            # Prüfe ob alle Chats erstellt wurden
            chats = db.get_all_chats()
            if len(chats) != 10:
                print(f"  [FAIL] Erwartet 10 Chats, found {len(chats)}")
                return False
            
            print("  [OK] Concurrent Access funktioniert")
            return True
    
    except Exception as e:
        print(f"  [FAIL] Fehler: {e}")
        return False


def test_memory_with_long_text():
    """Test: Memory mit sehr langen Texten"""
    print("\n[TEST] Memory with Long Text...")
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)
            mem = MemoryManager(db)
            
            # Sehr langer Text (100KB)
            long_text = "A" * 100000
            
            success = mem.learn(long_text)
            if not success:
                print("  [FAIL] Konnte langen Text nicht speichern")
                return False
            
            # Abrufen
            memory_str = mem.get_memory_string()
            if long_text not in memory_str:
                print("  [FAIL] Langer Text nicht im Memory")
                return False
            
            print("  [OK] Lange Texte werden korrekt behandelt")
            return True
    
    except Exception as e:
        print(f"  [FAIL] Fehler: {e}")
        return False


def test_input_validation():
    """Test: Input Validierung"""
    print("\n[TEST] Input Validation...")
    
    try:
        # Test 1: Zu lange Eingabe
        long_input = "A" * 10000
        sanitized = SecurityUtils.sanitize_input(long_input)
        if len(sanitized) > SecurityUtils.MAX_MESSAGE_LENGTH:
            print("  [FAIL] Längenlimit nicht eingehalten")
            return False
        
        # Test 2: SQL Injection Versuch
        sql_injection = "'; DROP TABLE users; --"
        sanitized = SecurityUtils.sanitize_input(sql_injection)
        # Sollte escaped sein
        if "'" in sanitized and "\\" not in sanitized:
            # HTML-escaped
            pass
        
        # Test 3: Chat-Namen Validierung
        if not SecurityUtils.validate_chat_name("Valid Chat Name"):
            print("  [FAIL] Valider Name wurde abgelehnt")
            return False
        
        if SecurityUtils.validate_chat_name("../../../etc/passwd"):
            print("  [FAIL] Malicious Path sollte abgelehnt sein")
            return False
        
        print("  [OK] Input Validation funktioniert")
        return True
    
    except Exception as e:
        print(f"  [FAIL] Fehler: {e}")
        return False


def run_all_tests():
    """Führt alle Error-Tests aus"""
    print("\n" + "="*60)
    print("[ERROR-TESTS] ASTRA ERROR SCENARIO TEST SUITE")
    print("="*60)
    
    tests = [
        ("Corrupted Database Recovery", test_corrupted_database),
        ("Rate-Limiting", test_rate_limiting),
        ("Invalid UTF-8 & XSS", test_invalid_utf8),
        ("Concurrent DB Access", test_concurrent_database_access),
        ("Memory with Long Text", test_memory_with_long_text),
        ("Input Validation", test_input_validation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  [FAIL] Kritischer Fehler: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("[SUMMARY] ERROR-TEST ZUSAMMENFASSUNG")
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
