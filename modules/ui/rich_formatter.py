"""
Rich Message Formatter
======================
Konvertiert Markdown zu HTML mit Syntax-Highlighting für Code-Blöcke
Unterstützt: Code-Blocks, Inline-Code, Bold, Italic, Links, Listen
"""

import re
from typing import Tuple, TYPE_CHECKING
from html import escape

# Type-checking imports (nur für IDE/Pylance, nicht zur Runtime)
if TYPE_CHECKING:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, TextLexer
    from pygments.formatters import HtmlFormatter

# Runtime-imports mit try/except
try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, TextLexer
    from pygments.formatters import HtmlFormatter
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False


class RichFormatter:
    """Formatiert Text mit Markdown und Syntax-Highlighting"""
    
    # Regex-Patterns
    CODE_BLOCK_PATTERN = re.compile(r'```(\w*)\n(.*?)\n```', re.DOTALL)
    INLINE_CODE_PATTERN = re.compile(r'`([^`]+)`')
    BOLD_PATTERN = re.compile(r'\*\*(.+?)\*\*')
    ITALIC_PATTERN = re.compile(r'\*(.+?)\*')
    LINK_PATTERN = re.compile(r'\[(.+?)\]\((.+?)\)')
    BULLET_PATTERN = re.compile(r'^ *[-*] (.+)$', re.MULTILINE)
    HEADING_PATTERN = re.compile(r'^(#{1,6}) (.+)$', re.MULTILINE)
    
    @staticmethod
    def highlight_code(code: str, language: str = "text") -> str:
        """Syntax-Highlighting für Code-Block mit Pygments"""
        if not PYGMENTS_AVAILABLE:
            # Fallback ohne Pygments - einfach pre-tag
            escaped_code = escape(code)
            return f'<pre style="background:#1e1e1e;color:#d4d4d4;padding:12px;border-radius:8px;overflow-x:auto;"><code>{escaped_code}</code></pre>'
        
        try:
            # Versuche Lexer für die Sprache zu finden
            try:
                lexer = get_lexer_by_name(language.lower()) if language else TextLexer()
            except:
                lexer = TextLexer()
            
            # HTML Formatter mit dunklem Theme
            formatter = HtmlFormatter(
                style='monokai',
                full=False,  # Kein komplettes HTML Dokument
                linenos=False,
                noclasses=False,  # Keine inline-styles sondern CSS-Classes
            )
            
            highlighted = highlight(code, lexer, formatter)
            
            # Wrap in ein div mit besserem Styling
            return f'<div style="background:#1e1e1e;border-radius:8px;overflow-x:auto;margin:8px 0;border-left:4px solid #ff4b4b;">{highlighted}</div>'
        except Exception:
            # Fallback bei Fehler
            escaped_code = escape(code)
            return f'<pre style="background:#1e1e1e;color:#d4d4d4;padding:12px;border-radius:8px;overflow-x:auto;"><code>{escaped_code}</code></pre>'
    
    @staticmethod
    def format_text(text: str) -> str:
        """Konvertiert Markdown zu HTML"""
        text = escape(text)
        
        # 1. Code-Blöcke (zuerst!)
        def replace_code_block(match):
            language = match.group(1).strip() or "text"
            code = match.group(2)
            return RichFormatter.highlight_code(code, language)
        
        text = RichFormatter.CODE_BLOCK_PATTERN.sub(replace_code_block, text)
        
        # 2. Inline-Code (vor Bold/Italic!)
        text = re.sub(
            RichFormatter.INLINE_CODE_PATTERN,
            r'<code style="background:#2a2a2a;color:#ff9f43;padding:2px 6px;border-radius:4px;font-family:Consolas,monospace;">\1</code>',
            text
        )
        
        # 3. Bold (vor Italic!)
        text = re.sub(
            RichFormatter.BOLD_PATTERN,
            r'<strong style="color:#ff9f43;font-weight:700;">\1</strong>',
            text
        )
        
        # 4. Italic
        text = re.sub(
            RichFormatter.ITALIC_PATTERN,
            r'<em style="color:#a8dadc;font-style:italic;">\1</em>',
            text
        )
        
        # 5. Links
        text = re.sub(
            RichFormatter.LINK_PATTERN,
            r'<a href="\2" style="color:#ff4b4b;text-decoration:underline;">\1</a>',
            text
        )
        
        # 6. Überschriften
        def replace_heading(match):
            level = len(match.group(1))
            title = match.group(2)
            size = max(20 - level * 2, 12)  # Von h1 (20) bis h6 (10)
            return f'<div style="font-size:{size}pt;font-weight:700;color:#ff4b4b;margin-top:8px;margin-bottom:4px;border-bottom:1px solid #ff4b4b;">{title}</div>'
        
        text = RichFormatter.HEADING_PATTERN.sub(replace_heading, text)
        
        # 7. Bullet-Listen
        text = re.sub(
            RichFormatter.BULLET_PATTERN,
            r'<div style="margin-left:16px;padding:2px 0;">• \1</div>',
            text
        )
        
        # 8. Zeilenumbrüche zu <br> (preserve original newlines)
        text = text.replace('\n', '<br/>')
        
        return text
    
    @staticmethod
    def format_message_with_metadata(
        text: str, 
        role: str,
        source: str = None,  # "search" | "llm" | "memory" | None
        confidence: float = None  # 0.0-1.0 für Memory
    ) -> str:
        """
        Formatiert eine komplette Message mit Metadaten
        
        Args:
            text: Nachrichtentext mit optionalem Markdown
            role: "user" | "assistant"
            source: Quelle (search = 🔍, llm = 🤖, memory = 💾)
            confidence: Confidence-Score für Memory (0.0-1.0)
        """
        formatted_html = RichFormatter.format_text(text)
        
        # Badge für Source
        source_badge = ""
        if source == "search":
            source_badge = '<span style="display:inline-block;background:#2a6b42;color:#a8f5a8;padding:2px 8px;border-radius:12px;font-size:10px;margin-right:8px;">🔍 Gesucht</span>'
        elif source == "llm":
            source_badge = '<span style="display:inline-block;background:#2a4a6b;color:#a8d5f5;padding:2px 8px;border-radius:12px;font-size:10px;margin-right:8px;">🤖 KI</span>'
        elif source == "memory":
            badge_color = RichFormatter._confidence_color(confidence)
            source_badge = f'<span style="display:inline-block;background:{badge_color};color:#ffffff;padding:2px 8px;border-radius:12px;font-size:10px;margin-right:8px;">💾 {confidence*100:.0f}%</span>'
        
        # Wrapper mit Source-Info
        final_html = f"""
        <div style="margin:2px 0;">
            {source_badge}
            {formatted_html}
        </div>
        """
        
        return final_html
    
    @staticmethod
    def _confidence_color(confidence: float) -> str:
        """Gibt Farbe basierend auf Confidence-Score zurück"""
        if confidence >= 0.9:
            return "#2a6b2a"  # Grün
        elif confidence >= 0.7:
            return "#6b6b2a"  # Gelb
        elif confidence >= 0.5:
            return "#6b4a2a"  # Orange
        else:
            return "#6b2a2a"  # Rot


# Test-Code
if __name__ == "__main__":
    test_text = """
# Beispiel Titel

Das ist **fetter Text** und das ist *kursiv*.

Hier ist `inline code`:

```python
def hello_world():
    print("Hello, World!")
    return True
```

- Punkt 1
- Punkt 2
- Punkt 3

[Link zu Google](https://google.com)
"""
    
    result = RichFormatter.format_text(test_text)
    print("HTML Output:")
    print(result)
