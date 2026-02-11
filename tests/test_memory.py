#!/usr/bin/env python3
"""
Memory System - Unit & Robustness Tests
========================================
Tests für Memory-Extraction, Formatierung und Robustheit
"""

import sys
import tempfile
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.memory import MemoryManager
from modules.database import Database


class MemoryTestResult:
    """Test Result Container"""
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
    
    def print_result(self):
        status = "✅ PASSED" if self.failed == 0 else "❌ FAILED"
        print(f"\n{status} - {self.name}")
        print(f"  Passed: {self.passed}/{self.total()}")
        print(f"  Success Rate: {self.success_rate():.1f}%")
        if self.errors:
            print("  Errors:")
            for error in self.errors:
                print(f"    - {error}")


class MemoryTestSuite:
    """Comprehensive Memory System Tests"""
    
    def __init__(self):
        # Create temp database for testing
        self.tmp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = Path(self.tmp_file.name)
        self.db = None
        self.mm = None
    
    def setup(self):
        """Initialize database and memory manager"""
        self.db = Database(self.db_path)
        self.mm = MemoryManager(self.db)
    
    def cleanup(self):
        """Clean up temporary files"""
        import os
        if self.db_path.exists():
            try:
                os.remove(self.db_path)
            except:
                pass
    
    def test_extraction_fixing(self) -> MemoryTestResult:
        """Test dass smart_learn die Info extrahiert und formatiert"""
        result = MemoryTestResult("Memory Extraction Fixing")
        
        try:
            # Test: User sagt "dir das ich duncan Heiße und 30 jahre alt bin"
            message = "dir das ich duncan Heiße und 30 jahre alt bin"
            
            extracted = self.mm.extract_personal_info(message)
            
            # Check for age
            if "age" in extracted and extracted["age"]["value"] == "30":
                result.add_pass()
            else:
                result.add_fail("Age extraction failed")
            
            # Check for name
            if "name" in extracted and extracted["name"]["value"].lower() == "duncan":
                result.add_pass()
            else:
                result.add_fail("Name extraction failed")
            
            # Test smart_learn formatting
            self.mm.smart_learn(message)
            memory = self.db.get_memory()
            
            if "name: duncan" in memory.lower() or "Name: Duncan" in memory:
                result.add_pass()
            else:
                result.add_fail("Name not properly formatted in memory")
            
            if "alter: 30" in memory.lower() or "Alter: 30" in memory:
                result.add_pass()
            else:
                result.add_fail("Age not properly formatted in memory")
            
        except Exception as e:
            result.add_fail(f"Exception: {e}")
        
        return result
    
    def test_extraction_robustness(self) -> MemoryTestResult:
        """Test verschiedene Input-Varianten"""
        result = MemoryTestResult("Memory Extraction Robustness (14 Cases)")
        
        test_cases = [
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
            ("mal schauen ob ich alice heiße", ["name"]),
            ("ich bin verheiratet", ["relationship"]),
            ("ich studiere Informatik", ["profession"]),
        ]
        
        try:
            for message, expected_keys in test_cases:
                extracted = self.mm.extract_personal_info(message)
                extracted_keys = list(extracted.keys())
                
                # Check if all expected keys are in extracted
                success = all(key in extracted_keys for key in expected_keys)
                
                if success:
                    result.add_pass()
                else:
                    result.add_fail(f"Input: {message!r} | Expected: {expected_keys}, Got: {extracted_keys}")
        
        except Exception as e:
            result.add_fail(f"Exception: {e}")
        
        return result


def run_memory_tests() -> Dict[str, MemoryTestResult]:
    """Run all memory tests"""
    print("\n" + "=" * 70)
    print("MEMORY SYSTEM TESTS")
    print("=" * 70)
    
    suite = MemoryTestSuite()
    suite.setup()
    
    results = {}
    
    try:
        # Test 1: Extraction fixing
        results["extraction_fixing"] = suite.test_extraction_fixing()
        results["extraction_fixing"].print_result()
        
        # Test 2: Robustness
        results["robustness"] = suite.test_extraction_robustness()
        results["robustness"].print_result()
        
    finally:
        suite.cleanup()
    
    return results


if __name__ == "__main__":
    results = run_memory_tests()
    
    # Summary
    total_passed = sum(r.passed for r in results.values())
    total_failed = sum(r.failed for r in results.values())
    total_tests = total_passed + total_failed
    
    print("\n" + "=" * 70)
    print(f"SUMMARY: {total_passed}/{total_tests} tests passed ({(total_passed/total_tests)*100:.1f}%)")
    print("=" * 70 + "\n")
    
    sys.exit(0 if total_failed == 0 else 1)
