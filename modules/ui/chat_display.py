"""
ASTRA AI - Chat Display Widget
================================
Modernes Chat-Display mit echten runden Bubbles (WhatsApp-Style).
Nutzt QScrollArea + QLabel-Widgets statt QTextEdit,
weil QTextEdit kein CSS border-radius unterstützt.
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from config import COLORS


class BubbleWidget(QFrame):
    """Einzelne Chat-Bubble mit echten runden Ecken via Qt Stylesheet"""

    def __init__(self, html_content: str, role: str = "assistant",
                 timestamp: str = "", source: str = None,
                 confidence: float = None, text_size: int = 11,
                 stats: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("BubbleWidget")
        self.role = role
        self.text_size = text_size

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 4)
        layout.setSpacing(2)

        # Nachrichtentext
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        self.label.setOpenExternalLinks(True)
        self.label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.label.customContextMenuRequested.connect(self._show_context_menu)
        self.label.setText(html_content)
        self.label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        layout.addWidget(self.label)

        # Footer: Source-Badge + Timestamp
        footer = QLabel()
        footer.setTextFormat(Qt.TextFormat.RichText)

        badge = ""
        if source == "search":
            badge = '<span style="color:#a8f5a8;">🔍 Web · </span>'
        elif source == "llm":
            badge = '<span style="color:#ff8080;">⚡ Astra · </span>'
        elif source == "memory":
            pct = int(confidence * 100) if confidence else 0
            badge = f'<span style="color:#a8f5a8;">💾 Erinnerung ({pct}%) · </span>'

        ts = timestamp or datetime.now().strftime("%H:%M")
        if role == "user":
            footer.setText(f'<span style="color:rgba(255,255,255,0.5);font-size:7pt;">{ts}</span>')
            footer.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            stats_html = ""
            if stats:
                stats_html = f'<span style="color:#888;font-size:7pt;">{stats} · </span>'
            footer.setText(f'<span style="font-size:7pt;">{badge}{stats_html}<span style="color:#555;">{ts}</span></span>')
            footer.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.footer = footer  # Referenz für spätere Stats-Aktualisierung
        layout.addWidget(footer)

        # Styling
        self._apply_style()

    def _show_context_menu(self, pos):
        """Zeigt Kontextmenü mit Kopieren-Aktion"""
        selected = self.label.selectedText()
        if not selected:
            return
        
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background-color: #2a2a2a; border: 1px solid #555; padding: 4px; }"
            "QMenu::item { background-color: #2a2a2a; color: #e8e8e8; padding: 6px 28px; }"
            "QMenu::item:selected { background-color: #ff4b4b; color: white; }"
        )
        
        copy_action = menu.addAction("Kopieren")
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(selected))
        
        menu.exec(self.label.mapToGlobal(pos))

    def _apply_style(self):
        """Wendet das Bubble-Stylesheet an — echte runde Ecken!"""
        if self.role == "user":
            bg = COLORS['primary']
            self.setStyleSheet(f"""
                BubbleWidget {{
                    background-color: {bg};
                    border-top-left-radius: 18px;
                    border-top-right-radius: 18px;
                    border-bottom-left-radius: 18px;
                    border-bottom-right-radius: 4px;
                }}
                QLabel {{
                    background: transparent;
                    color: #ffffff;
                    font-size: {self.text_size}pt;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                BubbleWidget {{
                    background-color: #1e1e1e;
                    border-top-left-radius: 18px;
                    border-top-right-radius: 18px;
                    border-bottom-left-radius: 4px;
                    border-bottom-right-radius: 18px;
                }}
                QLabel {{
                    background: transparent;
                    color: {COLORS['text']};
                    font-size: {self.text_size}pt;
                }}
            """)


class ChatDisplayWidget(QScrollArea):
    """Scrollbares Chat-Display mit Widget-basierten Bubbles"""

    def __init__(self, text_size: int = 11, parent=None):
        super().__init__(parent)
        self.text_size = text_size
        self._streaming_bubble = None  # Referenz auf aktive Streaming-Bubble

        # Container-Widget
        self._container = QWidget()
        self._container.setStyleSheet(f"background: {COLORS['background']};")
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(10, 6, 10, 6)
        self._layout.setSpacing(2)
        self._layout.addStretch()  # Pushed Bubbles nach oben

        self.setWidget(self._container)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(f"""
            QScrollArea {{
                background: {COLORS['background']};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {COLORS['background']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: #444;
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

    def add_bubble(self, html_content: str, role: str = "assistant",
                   timestamp: str = "", source: str = None,
                   confidence: float = None, stats: str = None) -> BubbleWidget:
        """Fügt eine neue Bubble hinzu und gibt sie zurück."""
        bubble = BubbleWidget(
            html_content, role=role, timestamp=timestamp,
            source=source, confidence=confidence,
            text_size=self.text_size, stats=stats
        )

        # Alignment: User rechts, Assistant links
        wrapper = QHBoxLayout()
        wrapper.setContentsMargins(0, 0, 0, 0)

        if role == "user":
            wrapper.addStretch(1)
            bubble.setMaximumWidth(600)
            wrapper.addWidget(bubble)
        else:
            bubble.setMaximumWidth(700)
            wrapper.addWidget(bubble)
            wrapper.addStretch(1)

        wrapper_widget = QWidget()
        wrapper_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        wrapper_widget.setStyleSheet("background: transparent; border: none; margin: 0; padding: 0;")
        wrapper_widget.setLayout(wrapper)

        # Vor dem Stretch einfügen
        self._layout.insertWidget(self._layout.count() - 1, wrapper_widget)

        # Auto-Scroll nach unten
        QTimer.singleShot(20, self._scroll_to_bottom)
        return bubble

    def start_streaming_bubble(self, source: str = "llm") -> BubbleWidget:
        """Erstellt eine Streaming-Bubble die laufend aktualisiert wird."""
        self._streaming_bubble = self.add_bubble(
            "▌", role="assistant", source=source
        )
        return self._streaming_bubble

    def update_streaming_bubble(self, html_content: str):
        """Aktualisiert den Text der aktiven Streaming-Bubble."""
        if self._streaming_bubble:
            self._streaming_bubble.label.setText(html_content + " ▌")
            QTimer.singleShot(10, self._scroll_to_bottom)

    def finish_streaming_bubble(self, final_html: str, source: str = "llm", stats: str = None):
        """Ersetzt die Streaming-Bubble mit der final formatierten Version."""
        if self._streaming_bubble:
            self._streaming_bubble.label.setText(final_html)
            # Stats im Footer aktualisieren
            if stats and hasattr(self._streaming_bubble, 'footer'):
                from datetime import datetime
                ts = datetime.now().strftime("%H:%M")
                badge = '<span style="color:#ff8080;">⚡ Astra · </span>' if source == "llm" else ""
                stats_html = f'<span style="color:#888;font-size:7pt;">{stats} · </span>'
                self._streaming_bubble.footer.setText(
                    f'<span style="font-size:7pt;">{badge}{stats_html}<span style="color:#555;">{ts}</span></span>'
                )
            self._streaming_bubble = None
            QTimer.singleShot(10, self._scroll_to_bottom)

    def remove_last_bubble(self):
        """Entfernt die letzte Bubble (z.B. Streaming-Bubble vor Ersetzung)."""
        count = self._layout.count()
        if count > 1:  # Mindestens Stretch bleibt
            item = self._layout.itemAt(count - 2)  # Letztes Widget vor Stretch
            if item and item.widget():
                widget = item.widget()
                self._layout.removeWidget(widget)
                widget.deleteLater()
        self._streaming_bubble = None

    def clear_all(self):
        """Entfernt alle Bubbles."""
        while self._layout.count() > 1:  # Stretch bleibt
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._streaming_bubble = None

    def show_empty_state(self, message: str = "Keine Chats vorhanden"):
        """Zeigt eine zentrierte Info-Nachricht."""
        self.clear_all()
        lbl = QLabel(message)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #666; font-size: 12pt; margin-top: 60px; background: transparent;")
        self._layout.insertWidget(0, lbl)

    def update_search_bubble(self, old_text: str, new_text: str):
        """Aktualisiert den Text einer Such-Bubble (sucht nach old_text)."""
        for i in range(self._layout.count()):
            item = self._layout.itemAt(i)
            if item and item.widget():
                wrapper = item.widget()
                for child in wrapper.findChildren(BubbleWidget):
                    current = child.label.text()
                    # Robuster Vergleich: sowohl exakt als auch plain-text
                    if old_text in current:
                        child.label.setText(current.replace(old_text, new_text))
                        return True
                    # Fallback: Vergleiche ohne HTML-Tags
                    import re
                    plain = re.sub(r'<[^>]+>', '', current)
                    if old_text in plain:
                        child.label.setText(new_text)
                        return True
        return False

    def set_text_size(self, size: int):
        """Aktualisiert die Textgröße aller Bubbles."""
        self.text_size = size

    def _scroll_to_bottom(self):
        """Scrollt zum Ende."""
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())
