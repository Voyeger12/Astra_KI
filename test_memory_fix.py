#!/usr/bin/env python3
"""
Test für Memory System Fix
Testet dass "Merke" Kommandos strukturiert speichern
"""

import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.memory import MemoryManager
from modules.database import Database
import tempfile

def test_smart_learn_with_extraction():
    """Test dass smart_learn die Info extrahiert und formatiert"""
    
    # Create temp database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = Path(tmp.name)
    
    try:
        db = Database(db_path)
        mm = MemoryManager(db)
        
        print("=" * 60)
        print("TEST: Memory System Extraction & Formatting")
        print("=" * 60)
        
        # Test 1: Direct extraction
        message = "dir das ich duncan Heiße und 30 jahre alt bin"
        print(f"\n1️⃣  Message: {message!r}")
        
        extracted = mm.extract_personal_info(message)
        print(f"\n   Extracted:")
        for category, info in extracted.items():
            print(f"     - {category}: {info['value']}")
        
        # Test 2: smart_learn should now format extracted values
        print(f"\n2️⃣  Calling smart_learn({message!r})...")
        result = mm.smart_learn(message)
        print(f"   Result: {result}")
        
        # Get memory
        all_memory = db.get_memory()
        print(f"\n3️⃣  Memory stored:")
        for line in all_memory.split('\n'):
            if line.strip():
                print(f"     • {line}")
        
        # Verify it's NOT storing the raw text
        if "dir das ich" in all_memory.lower():
            print("\n❌ FAIL: Raw text 'dir das ich' found in memory!")
            return False
        
        # Verify it IS storing formatted values
        success = True
        if "name:" in all_memory.lower() or "duncan" in all_memory.lower():
            print("\n✅ PASS: Name information properly formatted!")
        else:
            print("\n❌ FAIL: Name not found in memory")
            success = False
        
        if "alter:" in all_memory.lower() or "30" in all_memory.lower():
            print("✅ PASS: Age information properly stored!")
        else:
            print("❌ FAIL: Age not found in memory")
            success = False
        
        return success
        
    finally:
        # Cleanup
        import os
        if db_path.exists():
            try:
                os.remove(db_path)
            except:
                pass

if __name__ == "__main__":
    success = test_smart_learn_with_extraction()
    sys.exit(0 if success else 1)
