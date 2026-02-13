"""
Rich Message Formatter
======================
Konvertiert Markdown zu HTML mit Syntax-Highlighting für Code-Blöcke
Unterstützt: Code-Blocks, Inline-Code, Bold, Italic, Links, Listen

KEIN Double-Escaping: Code-Blöcke werden VOR escape() extrahiert!
"""

import re
import threading
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
    
    # Cache für formatierte Strings (thread-safe!)
    _format_cache = {}
    _cache_max_size = 500
    _cache_lock = threading.Lock()
    
    @staticmethod
    def highlight_code(code: str, language: str = "text") -> str:
        """Syntax-Highlighting für Code-Block mit Pygments.
        
        WICHTIG: Erhält RAW Code-Text — escape() passiert NUR hier intern!
        """
        if not PYGMENTS_AVAILABLE:
            escaped_code = escape(code)
            return (
                f'<pre style="background:#1e1e1e;color:#d4d4d4;padding:12px;'
                f'border-radius:8px;overflow-x:auto;">'
                f'<code>{escaped_code}</code></pre>'
            )
        
        try:
            try:
                lexer = get_lexer_by_name(language.lower()) if language else TextLexer()
            except Exception:
                lexer = TextLexer()
            
            formatter = HtmlFormatter(
                style='monokai',
                full=False,
                linenos=False,
                noclasses=True,
            )
            
            highlighted = highlight(code, lexer, formatter)
            
            return (
                f'<div style="background:#1e1e1e;border-radius:8px;'
                f'overflow-x:auto;margin:8px 0;border-left:4px solid #ff4b4b;">'
                f'{highlighted}</div>'
            )
        except Exception:
            escaped_code = escape(code)
            return (
                f'<pre style="background:#1e1e1e;color:#d4d4d4;padding:12px;'
                f'border-radius:8px;overflow-x:auto;">'
                f'<code>{escaped_code}</code></pre>'
            )
    
    @staticmethod
    def format_text(text: str) -> str:
        """Konvertiert Markdown zu HTML — OHNE Double-Escaping!
        
        Strategie: Code-Blöcke und Inline-Code ZUERST extrahieren (raw),
        dann nur den restlichen Text escapen, dann alles zusammenbauen.
        """
        # Check Cache first (thread-safe)
        cache_key = hash(text)
        with RichFormatter._cache_lock:
            if cache_key in RichFormatter._format_cache:
                return RichFormatter._format_cache[cache_key]
            if len(RichFormatter._format_cache) > RichFormatter._cache_max_size:
                RichFormatter._format_cache.clear()
        
        # === Phase 1: Code-Blöcke extrahieren (BEVOR escape!) ===
        code_blocks = {}
        block_counter = [0]
        
        def extract_code_block(match):
            language = match.group(1).strip() or "text"
            code = match.group(2)  # RAW code — kein escape!
            placeholder = f"\x00CODEBLOCK{block_counter[0]}\x00"
            code_blocks[placeholder] = RichFormatter.highlight_code(code, language)
            block_counter[0] += 1
            return placeholder
        
        text = RichFormatter.CODE_BLOCK_PATTERN.sub(extract_code_block, text)
        
        # === Phase 2: Inline-Code extrahieren (BEVOR escape!) ===
        inline_codes = {}
        inline_counter = [0]
        
        def extract_inline_code(match):
            code = escape(match.group(1))  # Inline-Code Inhalt escapen
            placeholder = f"\x00INLINECODE{inline_counter[0]}\x00"
            inline_codes[placeholder] = (
                f'<code style="background:#2a2a2a;color:#ff9f43;padding:2px 6px;'
                f'border-radius:4px;font-family:Consolas,monospace;">{code}</code>'
            )
            inline_counter[0] += 1
            return placeholder
        
        text = RichFormatter.INLINE_CODE_PATTERN.sub(extract_inline_code, text)
        
        # === Phase 3: Restlichen Text escapen (kein Code mehr drin!) ===
        text = escape(text)
        
        # === Phase 4: Markdown-Formatierung auf escaped Text ===
        
        # Bold (vor Italic!)
        text = re.sub(
            RichFormatter.BOLD_PATTERN,
            r'<strong style="color:#ff9f43;font-weight:700;">\1</strong>',
            text
        )
        
        # Italic
        text = re.sub(
            RichFormatter.ITALIC_PATTERN,
            r'<em style="color:#a8dadc;font-style:italic;">\1</em>',
            text
        )
        
        # Links
        text = re.sub(
            RichFormatter.LINK_PATTERN,
            r'<a href="\2" style="color:#ff4b4b;text-decoration:underline;">\1</a>',
            text
        )
        
        # Überschriften
        def replace_heading(match):
            level = len(match.group(1))
            title = match.group(2)
            size = max(20 - level * 2, 12)
            return (
                f'<div style="font-size:{size}pt;font-weight:700;color:#ff4b4b;'
                f'margin-top:8px;margin-bottom:4px;border-bottom:1px solid #ff4b4b;">'
                f'{title}</div>'
            )
        
        text = RichFormatter.HEADING_PATTERN.sub(replace_heading, text)
        
        # Bullet-Listen
        text = re.sub(
            RichFormatter.BULLET_PATTERN,
            '<div style="margin-left:16px;padding:2px 0;">\u2022 \\1</div>',
            text
        )
        
        # Zeilenumbrüche zu <br>
        text = text.replace('\n', '<br/>')
        
        # === Phase 5: Placeholders zurück durch fertige HTML-Blöcke ersetzen ===
        for placeholder, html in code_blocks.items():
            text = text.replace(placeholder, html)
        for placeholder, html in inline_codes.items():
            text = text.replace(placeholder, html)
        
        # Cache das Ergebnis (thread-safe)
        with RichFormatter._cache_lock:
            RichFormatter._format_cache[cache_key] = text
        return text


