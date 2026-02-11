#!/usr/bin/env python3
"""
Test - Memory System Robustheit
Testet verschiedene Input-Varianten für die Extraction
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from modules.memory import MemoryManager
from modules.database import Database
import tempfile

def test_extraction_variants():
    """Test verschiedene Eingabe-Formate"""
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = Path(tmp.name)
    
    try:
        db = Database(db_path)
        mm = MemoryManager(db)
        
        test_cases = [
            # (Input, Expected Keys)
            ("ich heiße Duncan", ["name"]),
            ("mein name ist Duncan", ["name"]),
            ("ich bin 30 jahre alt", ["age"]),
            ("dir das ich duncan Heiße und 30 jahre alt bin", ["name", "age"]),
            ("ich heiße Müller und bin 25 Jahre alt", ["name", "age"]),
            ("my name is John", ["name"]),
            ("i am 40 years old", ["age"]),
            ("also ich bin Sarah und 35 Jahre alt", ["name", "age"]),
            ("hey ich lebe in Berlin", ["location"]),
            ("meine hobbys sind lesen und programmieren", ["hobbies"]),
            ("ich mag Pizza und Sushi", ["likes"]),
            ("mal schauen ob ich alice heiße", ["name"]),  # "alice" lowercase
            ("ich bin verheiratet", ["relationship"]),
            ("ich studiere Informatik", ["profession"]),
        ]
        
        print("=" * 70)
        print("MEMORY PATTERN ROBUSTNESS TEST")
        print("=" * 70)
        
        passed = 0
        failed = 0
        
        for message, expected_keys in test_cases:
            extracted = mm.extract_personal_info(message)
            extracted_keys = list(extracted.keys())
            
            # Check if extraction worked
            success = all(key in extracted_keys for key in expected_keys)
            
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"\n{status} | Input: {message!r}")
            
            if extracted:
                for key, info in extracted.items():
                    print(f"       → {key}: {info['value']}")
            else:
                print(f"       → (keine Extraktion)")
            
            if expected_keys:
                print(f"       Expected: {expected_keys}, Got: {extracted_keys}")
            
            if success:
                passed += 1
            else:
                failed += 1
        
        print("\n" + "=" * 70)
        print(f"ERGEBNIS: {passed} PASS, {failed} FAIL")
        print("=" * 70)
        
        return failed == 0
        
    finally:
        import os
        if db_path.exists():
            try:
                os.remove(db_path)
            except:
                pass

if __name__ == "__main__":
    success = test_extraction_variants()
    sys.exit(0 if success else 1)
