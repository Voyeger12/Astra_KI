"""
Rich Message Formatter
======================
Konvertiert Markdown zu HTML mit Syntax-Highlighting für Code-Blöcke
Unterstützt: Code-Blocks, Inline-Code, Bold, Italic, Links, Listen
"""

import re
from html import escape

# Pygments für Syntax-Highlighting (optional)
try:
    from pygments import highlight  # type: ignore[reportMissingModuleSource]
    from pygments.lexers import get_lexer_by_name, TextLexer  # type: ignore[reportMissingModuleSource]
    from pygments.formatters import HtmlFormatter  # type: ignore[reportMissingModuleSource]
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False


class RichFormatter:
    """Formatiert Text mit Markdown und Syntax-Highlighting"""
    
    # Regex-Patterns (Pre-compiled für Performance!)
    CODE_BLOCK_PATTERN = re.compile(r'```(\w*)\n(.*?)\n```', re.DOTALL)
    INLINE_CODE_PATTERN = re.compile(r'`([^`]+)`')
    BOLD_PATTERN = re.compile(r'\*\*(.+?)\*\*')
    ITALIC_PATTERN = re.compile(r'\*(.+?)\*')
    LINK_PATTERN = re.compile(r'\[(.+?)\]\((.+?)\)')
    BULLET_PATTERN = re.compile(r'^ *[-*] (.+)$', re.MULTILINE)
    HEADING_PATTERN = re.compile(r'^(#{1,6}) (.+)$', re.MULTILINE)
    
    # Cache für formatierte Strings (verhindert Doppel-Formatierung!)
    _format_cache = {}
    _cache_max_size = 500  # Maximale Anzahl cached items
    
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
                noclasses=True,  # Inline-styles für korrektes Highlighting in QTextEdit
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
        """Konvertiert Markdown zu HTML - mit Cache für Performance!"""
        # Check Cache first (verhindert Doppel-Formatierung!)
        cache_key = hash(text)
        if cache_key in RichFormatter._format_cache:
            return RichFormatter._format_cache[cache_key]
        
        # Wenn Cache zu groß wird, leere ihn
        if len(RichFormatter._format_cache) > RichFormatter._cache_max_size:
            RichFormatter._format_cache.clear()
        
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
        
        # Cache das Ergebnis
        RichFormatter._format_cache[cache_key] = text
        return text
    

