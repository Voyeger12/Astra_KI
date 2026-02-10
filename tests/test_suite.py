"""
ASTRA Test Suite
================
Einheitliche Test-Struktur mit diagnostischen Tools
"""

import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Füge Projekt-Root zum Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.database import Database
from modules.memory import MemoryManager
from modules.logger import log_info, log_error, log_debug, get_log_file


class TestResult:
    """Speichert Test-Ergebnisse"""
    
    def __init__(self, name: str):
        self.name = name
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self):
        self.passed += 1
    
    def add_fail(self, error: str):
        self.failed += 1
        self.errors.append(error)
    
    def total(self) -> int:
        return self.passed + self.failed
    
    def success_rate(self) -> float:
        if self.total() == 0:
            return 0.0
        return (self.passed / self.total()) * 100
    
    def __str__(self) -> str:
        status = "[PASSED]" if self.failed == 0 else "[FAILED]"
        return (
            f"\n{status} - {self.name}\n"
            f"  + Passed: {self.passed}\n"
            f"  - Failed: {self.failed}\n"
            f"  Success Rate: {self.success_rate():.1f}%"
        )


class AstraTestSuite:
    """Zentrale Test-Suite für ASTRA"""
    
    def __init__(self):
        self.results: Dict[str, TestResult] = {}
        self.db = Database()
        self.memory_manager = MemoryManager(self.db)
        
        log_info("Test Suite initialisiert", "TEST")
    
    # ===== DATABASE TESTS =====
    def test_database(self) -> TestResult:
        """Testet Datenbank-Funktionalität"""
        result = TestResult("Database Module")
        
        try:
            # Test 1: Tabellen existieren
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            tables = ['chats', 'messages', 'memory', 'logs']
            for table in tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if cursor.fetchone():
                    result.add_pass()
                    log_debug(f"✓ Tabelle '{table}' existiert", "DB_TEST")
                else:
                    result.add_fail(f"Tabelle '{table}' fehlt")
                    log_error(f"✗ Tabelle '{table}' nicht gefunden", "DB_TEST")
            
            conn.close()
            
        except Exception as e:
            result.add_fail(f"Datenbank-Fehler: {e}")
            log_error(f"Datenbank-Test fehlgeschlagen: {e}", "DB_TEST", e)
        
        self.results["database"] = result
        return result
    
    # ===== MEMORY TESTS =====
    def test_memory_storage(self) -> TestResult:
        """Testet Memory-Speicherung"""
        result = TestResult("Memory Storage")
        
        try:
            # Test 1: Speichern
            test_entries = [
                ("Test Entry 1", "personal"),
                ("Test Entry 2", "general"),
                ("Test Entry 3", "professional")
            ]
            
            for content, category in test_entries:
                success = self.memory_manager.learn(content, category)
                if success:
                    result.add_pass()
                    log_debug(f"✓ Memory gespeichert: {content[:30]}...", "MEMORY_TEST")
                else:
                    result.add_fail(f"Konnte nicht speichern: {content}")
            
            # Test 2: Abrufen
            memory = self.memory_manager.get_memory_string()
            if memory and len(memory) > 0:
                result.add_pass()
                log_debug(f"✓ Memory abgerufen ({len(memory)} Zeichen)", "MEMORY_TEST")
            else:
                result.add_fail("Memory ist leer")
            
        except Exception as e:
            result.add_fail(f"Memory-Fehler: {e}")
            log_error(f"Memory-Test fehlgeschlagen: {e}", "MEMORY_TEST", e)
        
        self.results["memory"] = result
        return result
    
    def test_memory_auto_learn(self) -> TestResult:
        """Testet automatisches Erkennen von persönlichen Infos"""
        result = TestResult("Memory Auto-Learning")
        
        try:
            test_messages = [
                ("Ich heiße Max", "name"),
                ("Ich bin 25 Jahre alt", "age"),
                ("Ich lebe in München", "location"),
                ("Ich mag Pizza", "likes"),
            ]
            
            for message, expected_category in test_messages:
                saved = self.memory_manager.auto_learn_from_message(message)
                
                if saved and any(cat == expected_category for cat, val in saved):
                    result.add_pass()
                    log_debug(f"✓ Auto-Learn erkannt: {expected_category}", "AUTO_LEARN_TEST")
                else:
                    result.add_fail(f"Auto-Learn fehlgeschlagen für: {expected_category}")
                    log_debug(f"✗ Nicht erkannt: {expected_category}", "AUTO_LEARN_TEST")
            
        except Exception as e:
            result.add_fail(f"Auto-Learn Fehler: {e}")
            log_error(f"Auto-Learn Test fehlgeschlagen: {e}", "AUTO_LEARN_TEST", e)
        
        self.results["memory_auto_learn"] = result
        return result
    
    def test_memory_system_prompt(self) -> TestResult:
        """Testet System-Prompt Integration"""
        result = TestResult("Memory System Prompt")
        
        try:
            system_prompt = self.memory_manager.get_system_prompt()
            
            if system_prompt and "{memory}" not in system_prompt:
                result.add_pass()
                log_debug("✓ System-Prompt enthält Memory", "SYSTEM_PROMPT_TEST")
            else:
                result.add_fail("System-Prompt ist leer oder hat unersetzten Placeholder")
            
            if "ASTRA" in system_prompt or "Astra" in system_prompt:
                result.add_pass()
                log_debug("✓ System-Prompt hat Charakter-Definition", "SYSTEM_PROMPT_TEST")
            else:
                result.add_fail("System-Prompt hat keine Charakter-Definition")
            
        except Exception as e:
            result.add_fail(f"System-Prompt Fehler: {e}")
            log_error(f"System-Prompt Test fehlgeschlagen: {e}", "SYSTEM_PROMPT_TEST", e)
        
        self.results["system_prompt"] = result
        return result
    
    def test_memory_clear(self) -> TestResult:
        """Testet Memory-Löschen"""
        result = TestResult("Memory Clear")
        
        try:
            # Count before
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM memory")
            count_before = cursor.fetchone()[0]
            conn.close()
            
            if count_before > 0:
                # Clear
                success = self.memory_manager.clear_memory()
                if success:
                    result.add_pass()
                    log_debug("✓ Memory gelöscht", "CLEAR_TEST")
                    
                    # Count after
                    conn = sqlite3.connect(self.db.db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM memory")
                    count_after = cursor.fetchone()[0]
                    conn.close()
                    
                    if count_after == 0:
                        result.add_pass()
                        log_debug("✓ Memory komplett geleert", "CLEAR_TEST")
                    else:
                        result.add_fail(f"Memory nicht vollständig geleert: {count_after} Einträge")
                else:
                    result.add_fail("Clear-Funktion fehlgeschlagen")
            else:
                result.add_pass()  # Nichts zum Löschen
                log_debug("✓ Memory war leer", "CLEAR_TEST")
        
        except Exception as e:
            result.add_fail(f"Clear Fehler: {e}")
            log_error(f"Clear Test fehlgeschlagen: {e}", "CLEAR_TEST", e)
        
        self.results["memory_clear"] = result
        return result
    
    # ===== UTILITY TESTS =====
    def test_text_utils(self) -> TestResult:
        """Testet Text-Utilities"""
        result = TestResult("Text Utilities")
        
        try:
            from modules.utils import TextUtils
            
            # Test Truncate
            text = "This is a very long text that needs to be truncated"
            truncated = TextUtils.truncate(text, 20)
            if len(truncated) <= 23:  # 20 + "..."
                result.add_pass()
                log_debug("✓ Text truncate funktioniert", "TEXT_UTILS_TEST")
            else:
                result.add_fail("Text truncate funktioniert nicht korrekt")
            
            # Test Format Timestamp
            iso_timestamp = "2026-02-07T10:30:45"
            formatted = TextUtils.format_timestamp(iso_timestamp)
            if "2026" in formatted or "02" in formatted:
                result.add_pass()
                log_debug("✓ Timestamp-Formatierung funktioniert", "TEXT_UTILS_TEST")
            else:
                result.add_fail("Timestamp-Formatierung fehlgeschlagen")
        
        except Exception as e:
            result.add_fail(f"Utils Fehler: {e}")
            log_error(f"Utils Test fehlgeschlagen: {e}", "TEXT_UTILS_TEST", e)
        
        self.results["utils"] = result
        return result
    
    # ===== REPORT GENERATION =====
    def run_all_tests(self) -> None:
        """Führt alle Tests aus"""
        print("\n" + "="*70)
        print("[TEST] ASTRA TEST SUITE - Vollstaendiger Ueberblick")
        print("="*70)
        
        # Führe alle Tests aus
        self.test_database()
        self.test_memory_storage()
        self.test_memory_auto_learn()
        self.test_memory_system_prompt()
        self.test_memory_clear()
        self.test_text_utils()
        
        # Zeige Resultate
        total_passed = 0
        total_failed = 0
        
        for test_name, result in self.results.items():
            print(result)
            total_passed += result.passed
            total_failed += result.failed
            
            if result.errors:
                print("  Fehler:")
                for error in result.errors:
                    print(f"    - {error}")
        
        # Summary
        print("\n" + "="*70)
        print(f"[SUMMARY] GESAMT-ZUSAMMENFASSUNG")
        print("="*70)
        print(f"  [+] Gesamt Passed:  {total_passed}")
        print(f"  [-] Gesamt Failed:  {total_failed}")
        print(f"  Success Rate:     {(total_passed/(total_passed+total_failed)*100) if (total_passed+total_failed) > 0 else 0:.1f}%")
        print(f"  Log-Datei:        {get_log_file()}")
        print("="*70 + "\n")
        
        log_info(f"Test Suite abgeschlossen: {total_passed} passed, {total_failed} failed", "TEST_SUMMARY")


if __name__ == "__main__":
    suite = AstraTestSuite()
    suite.run_all_tests()
