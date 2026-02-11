"""
Test für neue Features
=====================
Tests für RichFormatter und MemoryEnhancer
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.ui.rich_formatter import RichFormatter
from modules.memory_enhanced import MemoryEnhancer


class TestRichFormatter:
    """Tests für RichFormatter - Markdown & Code-Highlighting"""
    
    def test_markdown_bold(self):
        """Test Bold Text (**text**)"""
        result = RichFormatter.format_text("Das ist **wichtig**")
        assert "<strong" in result
        assert "wichtig" in result
        print("✅ Bold Text Test")
    
    def test_markdown_italic(self):
        """Test Italic Text (*text*)"""
        result = RichFormatter.format_text("Das ist *kursiv*")
        assert "<em" in result
        assert "kursiv" in result
        print("✅ Italic Text Test")
    
    def test_inline_code(self):
        """Test Inline Code (`code`)"""
        result = RichFormatter.format_text("Nutze `python` für...")
        assert "<code" in result
        assert "python" in result
        print("✅ Inline Code Test")
    
    def test_heading(self):
        """Test Headings (#, ##, etc.)"""
        result = RichFormatter.format_text("# Main Title\n## Subtitle")
        assert "Main Title" in result
        assert "Subtitle" in result
        print("✅ Heading Test")
    
    def test_bullet_list(self):
        """Test Bullet Points (- item)"""
        result = RichFormatter.format_text("- Punkt 1\n- Punkt 2")
        assert "•" in result
        print("✅ Bullet List Test")
    
    def test_code_highlighting(self):
        """Test Code Block Highlighting"""
        code = 'def hello():\n    return "world"'
        result = RichFormatter.highlight_code(code, "python")
        assert "hello" in result
        assert "#1e1e1e" in result  # Dark background
        print("✅ Code Highlighting Test")
    
    def test_source_badge_llm(self):
        """Test Source-Badge für KI"""
        result = RichFormatter.format_message_with_metadata("Test", "assistant", source="llm")
        assert "🤖" in result
        assert "KI" in result
        print("✅ Source Badge (LLM) Test")
    
    def test_source_badge_search(self):
        """Test Source-Badge für Search"""
        result = RichFormatter.format_message_with_metadata("Test", "assistant", source="search")
        assert "🔍" in result
        assert "Gesucht" in result
        print("✅ Source Badge (Search) Test")
    
    def test_source_badge_memory(self):
        """Test Source-Badge für Memory mit Confidence"""
        result = RichFormatter.format_message_with_metadata(
            "Test", "assistant", source="memory", confidence=0.95
        )
        assert "💾" in result
        assert "95" in result
        print("✅ Source Badge (Memory) Test")


class TestMemoryEnhancer:
    """Tests für MemoryEnhancer - Confidence Scoring & Analysis"""
    
    def test_similarity_exact_match(self):
        """Test Similarity für identische Texte"""
        sim = MemoryEnhancer.calculate_similarity("Hallo", "Hallo")
        assert sim == 1.0
        print("✅ Similarity (Exact Match) Test")
    
    def test_similarity_different(self):
        """Test Similarity für unterschiedliche Texte"""
        sim = MemoryEnhancer.calculate_similarity("Hallo", "Auf Wiedersehen")
        assert sim < 0.5
        print("✅ Similarity (Different) Test")
    
    def test_similarity_similar(self):
        """Test Similarity für ähnliche Texte"""
        sim = MemoryEnhancer.calculate_similarity(
            "Ich heiße Duncan",
            "Mein Name ist Duncan"
        )
        assert 0.4 < sim < 1.0  # Sollte ähnlich sein
        print("✅ Similarity (Similar) Test")
    
    def test_confidence_user_input(self):
        """Test Confidence für User Input (sollte hoch sein)"""
        enhancer = MemoryEnhancer(None)
        conf = enhancer.calculate_confidence_score("Name: Duncan", source="user")
        assert conf >= 0.9  # User-Input sollte 0.95 sein
        print("✅ Confidence (User Input) Test")
    
    def test_confidence_auto_learn_low(self):
        """Test Confidence für Auto-Learn (sollte niedrig sein)"""
        enhancer = MemoryEnhancer(None)
        conf = enhancer.calculate_confidence_score("mag Pizza", source="auto_learn", occurrences=1)
        assert 0.5 <= conf <= 0.7  # Auto-Learn sollte 0.60 sein
        print("✅ Confidence (Auto-Learn, 1x) Test")
    
    def test_confidence_auto_learn_boosted(self):
        """Test Confidence Boost bei mehrfachem Vorkommen"""
        enhancer = MemoryEnhancer(None)
        conf_1x = enhancer.calculate_confidence_score("mag Pizza", source="auto_learn", occurrences=1)
        conf_5x = enhancer.calculate_confidence_score("mag Pizza", source="auto_learn", occurrences=5)
        assert conf_5x > conf_1x  # Mit 5x sollte Confidence höher sein
        assert conf_5x >= 0.9  # Mit 5x sollte über 0.9 sein
        print("✅ Confidence (Boost bei Wiederholung) Test")
    
    def test_format_memory_confidence(self):
        """Test Memory Formatting mit Confidence"""
        enhancer = MemoryEnhancer(None)
        formatted = enhancer.format_memory_with_confidence("Name: Duncan", 0.95)
        assert "Duncan" in formatted
        assert "95" in formatted
        assert "🟢" in formatted  # Grüner Badge für hohe Confidence
        print("✅ Memory Formatting (Confidence) Test")
    
    def test_format_memory_low_confidence(self):
        """Test Memory Formatting mit niedriger Confidence"""
        enhancer = MemoryEnhancer(None)
        formatted = enhancer.format_memory_with_confidence("mag Pizza", 0.3)
        assert "Pizza" in formatted
        assert "30" in formatted
        assert "🔴" in formatted  # Roter Badge für niedrige Confidence
        print("✅ Memory Formatting (Low Confidence) Test")
    
    def test_extract_confidence_from_memory(self):
        """Test Extraction von Confidence aus Memory"""
        enhancer = MemoryEnhancer(None)
        original_formatted = enhancer.format_memory_with_confidence("Test", 0.85)
        extracted_text, extracted_conf = enhancer.extract_confidence_from_memory(original_formatted)
        assert "Test" in extracted_text
        assert extracted_conf is not None
        assert 0.8 <= extracted_conf <= 0.9
        print("✅ Extract Confidence Test")


def run_all_tests():
    """Führt alle Tests aus"""
    print("=" * 60)
    print("TESTING NEW FEATURES")
    print("=" * 60)
    
    # RichFormatter Tests
    print("\n📝 RichFormatter Tests:")
    print("-" * 60)
    test_formatter = TestRichFormatter()
    test_formatter.test_markdown_bold()
    test_formatter.test_markdown_italic()
    test_formatter.test_inline_code()
    test_formatter.test_heading()
    test_formatter.test_bullet_list()
    test_formatter.test_code_highlighting()
    test_formatter.test_source_badge_llm()
    test_formatter.test_source_badge_search()
    test_formatter.test_source_badge_memory()
    
    # MemoryEnhancer Tests
    print("\n🧠 MemoryEnhancer Tests:")
    print("-" * 60)
    test_memory = TestMemoryEnhancer()
    test_memory.test_similarity_exact_match()
    test_memory.test_similarity_different()
    test_memory.test_similarity_similar()
    test_memory.test_confidence_user_input()
    test_memory.test_confidence_auto_learn_low()
    test_memory.test_confidence_auto_learn_boosted()
    test_memory.test_format_memory_confidence()
    test_memory.test_format_memory_low_confidence()
    test_memory.test_extract_confidence_from_memory()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
