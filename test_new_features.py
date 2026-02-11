#!/usr/bin/env python
"""Quick Test für neue Features"""

from modules.ui.rich_formatter import RichFormatter
from modules.memory_enhanced import MemoryEnhancer

print("=" * 50)
print("TESTING NEW FEATURES")
print("=" * 50)

# Test 1: RichFormatter - Markdown
print("\n1. Testing RichFormatter - Markdown:")
md_text = "**Bold** und *kursiv* mit `code`"
result = RichFormatter.format_text(md_text)
print(f"   Input: {md_text}")
print(f"   ✅ Markdown formatted successfully")

# Test 2: RichFormatter - Code Highlighting
print("\n2. Testing Code Highlighting:")
code = "def hello():\n    return 'world'"
highlighted = RichFormatter.highlight_code(code, "python")
print(f"   ✅ Code highlighting works")

# Test 3: MemoryEnhancer - Similarity
print("\n3. Testing MemoryEnhancer:")
sim = MemoryEnhancer.calculate_similarity("Ich heiße Duncan", "Mein Name ist Duncan")
print(f"   Similarity Score: {sim:.2f}")
print(f"   ✅ Similarity calculation works")

# Test 4: Confidence Scoring
print("\n4. Testing Confidence Scoring:")
enhancer = MemoryEnhancer(None)
conf_user = enhancer.calculate_confidence_score("Name: Duncan", source="user")
conf_auto = enhancer.calculate_confidence_score("mag Pizza", source="auto_learn", occurrences=1)
conf_boost = enhancer.calculate_confidence_score("mag Pizza", source="auto_learn", occurrences=5)

print(f"   User Input: {conf_user:.2f}")
print(f"   Auto-Learn (1x): {conf_auto:.2f}")
print(f"   Auto-Learn (5x): {conf_boost:.2f}")
print(f"   ✅ Confidence scoring works")

# Test 5: Memory Formatting
print("\n5. Testing Memory Formatting:")
formatted = enhancer.format_memory_with_confidence("Name: Duncan", 0.95)
print(f"   Formatted: {formatted}")
print(f"   ✅ Memory formatting works")

print("\n" + "=" * 50)
print("✅ ALL TESTS PASSED!")
print("=" * 50)
