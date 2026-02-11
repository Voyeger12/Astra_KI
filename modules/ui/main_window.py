"""
ASTRA AI - PyQt6 UI Main Window
================================
Moderne Desktop-Oberfläche mit Rot-Schwarz Design
Modularisierte Struktur für bessere Wartbarkeit
"""

import sys
from typing import List, Dict
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTextEdit, QPushButton, QListWidget, QListWidgetItem, QLineEdit,
    QComboBox, QFrame, QMessageBox, QApplication, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QTextCursor
from pathlib import Path

from config import COLORS, WINDOW_WIDTH, WINDOW_HEIGHT, OLLAMA_MODELS, DEFAULT_MODEL
from modules.database import Database
from modules.utils import SecurityUtils, RateLimiter
from modules.ollama_client import OllamaClient
from modules.memory import MemoryManager
from modules.memory_enhanced import SmartMemoryIntegration
from modules.utils import SearchEngine, TextUtils

# Modularisierte Imports aus ui Submodule
from modules.ui.styles import StyleSheet
from modules.ui.workers import LLMWorker, LLMStreamWorker, HealthWorker, SearchWorker
from modules.ui.settings_manager import SettingsManager
from modules.ui.settings_dialog import SettingsDialog
from modules.ui.rich_formatter import RichFormatter


class ChatWindow(QMainWindow):
    """Hauptfenster der ASTRA-Anwendung"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ASTRA AI - Neural Intelligence")
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(800, 600)
        self.setStyleSheet(StyleSheet.get_stylesheet())
        
        # Icon setzen
        try:
            icon_path = Path(__file__).parent.parent.parent / "assets" / "astra_icon.ico"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
        except Exception:
            pass
        
        # Initialise Komponenten
        self.db = Database()
        self.ollama = OllamaClient()
        self.memory_manager = MemoryManager(self.db)
        self.smart_memory = SmartMemoryIntegration(self.memory_manager, self.db)  # Enhanced Memory
        self.settings_manager = SettingsManager()
        
        # Rate-Limiting
        self.rate_limiter = RateLimiter(max_requests=30, window_seconds=60)
        
        # Lade Textgröße aus Settings VOR setup_ui() da es dort verwendet wird
        self.current_text_size = self.settings_manager.get('text_size', 11)
        self._selected_model = self.settings_manager.get('selected_model', DEFAULT_MODEL)
        
        # UI Setup
        self.setup_ui()
        
        # Worker-Thread
        self.llm_worker = None
        self.search_worker = None
        self._ollama_alive = False
        self.health_worker = None
        
        # Status
        self.current_chat = None
        self.is_waiting_for_response = False
        self._streaming_started = False
        self._pending_user_message = ""
        
        # Timer für Status-Updates
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(500)
        
        self.load_chats()
        # Start background health worker
        try:
            self.health_worker = HealthWorker(self.ollama, interval=2.0)
            self.health_worker.alive.connect(self._on_health_update)
            self.health_worker.start()
        except Exception:
            self._ollama_alive = False
    
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        central_widget = QWidget()
        central_widget.setStyleSheet(f"background-color: {COLORS['background']};")
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # LINKE SEITE: SIDEBAR
        left_panel = QWidget()
        left_panel.setMaximumWidth(280)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)
        left_panel.setStyleSheet(f"background: linear-gradient(180deg, {COLORS['surface']} 0%, {COLORS['background']} 100%);")
        
        # ASTRA HEADER
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(3)
        
        astra_title = QLabel("⚡ ASTRA")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        astra_title.setFont(title_font)
        astra_title.setStyleSheet(f"color: {COLORS['accent']}; padding: 4px;")
        astra_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(astra_title)
        
        subtitle = QLabel("AI Assistant")
        subtitle_font = QFont()
        subtitle_font.setPointSize(8)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 2px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle)
        
        left_layout.addWidget(header_widget)
        
        # Trennlinie
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setStyleSheet(f"border: 1px solid {COLORS['primary']};")
        left_layout.addWidget(sep1)
        
        # Chat-Liste
        chats_label = QLabel("💬 CHATS")
        chats_label.setStyleSheet(f"color: {COLORS['primary']}; font-weight: bold; font-size: 9pt;")
        left_layout.addWidget(chats_label)
        
        self.chat_list = QListWidget()
        self.chat_list.setMinimumHeight(180)
        self.chat_list.setMaximumHeight(320)
        left_layout.addWidget(self.chat_list)
        self.chat_list.itemClicked.connect(self.on_chat_selected)
        
        # Action-Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(6)
        
        new_chat_btn = QPushButton("➕ Neu")
        new_chat_btn.setMinimumHeight(36)
        new_chat_btn.setStyleSheet(
            f"background-color: {COLORS['primary']}; color: white; border: none; "
            f"border-radius: 8px; font-weight: bold; font-size: 9pt;"
        )
        new_chat_btn.clicked.connect(self.create_new_chat)
        button_layout.addWidget(new_chat_btn)
        
        delete_chat_btn = QPushButton("🗑️ Löschen")
        delete_chat_btn.setMinimumHeight(36)
        delete_chat_btn.setStyleSheet(
            f"background-color: {COLORS['error']}; color: white; border: none; border-radius: 8px; font-weight: bold; font-size: 9pt;"
        )
        delete_chat_btn.clicked.connect(self.delete_current_chat)
        button_layout.addWidget(delete_chat_btn)
        
        left_layout.addLayout(button_layout)
        left_layout.addStretch()
        
        # Bottom Section
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"border: 1px solid {COLORS['primary']};")
        left_layout.addWidget(sep2)
        
        settings_btn = QPushButton("⚙️ Einstellungen")
        settings_btn.setMinimumHeight(36)
        settings_btn.setStyleSheet(
            f"background-color: {COLORS['surface']}; color: {COLORS['text']}; "
            f"border: 2px solid {COLORS['primary']}; border-radius: 8px; font-weight: bold; font-size: 9pt;"
        )
        settings_btn.clicked.connect(self.open_settings)
        left_layout.addWidget(settings_btn)
        
        # Status
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(8, 6, 8, 6)
        status_layout.setSpacing(6)
        status_frame.setStyleSheet(
            f"background-color: {COLORS['surface']}; border: 1px solid {COLORS['primary']}; border-radius: 8px;"
        )
        
        status_dot = QLabel("🟢")
        status_layout.addWidget(status_dot)
        
        self.status_text = QLabel("Online")
        self.status_text.setStyleSheet(f"color: #00cc44; font-weight: bold; font-size: 9pt;")
        status_layout.addWidget(self.status_text)
        status_layout.addStretch()
        left_layout.addWidget(status_frame)
        
        # RECHTE SEITE: CHAT
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(12)
        
        # Chat-Header
        chat_header_frame = QFrame()
        chat_header_frame.setStyleSheet(
            f"background: linear-gradient(90deg, {COLORS['primary']} 0%, {COLORS['accent']} 100%); "
            f"border-radius: 12px;"
        )
        chat_header_layout = QHBoxLayout(chat_header_frame)
        chat_header_layout.setContentsMargins(14, 12, 14, 12)
        
        chat_label = QLabel("🤖 ASTRA Chat")
        chat_label_font = QFont()
        chat_label_font.setPointSize(13)
        chat_label_font.setBold(True)
        chat_label.setFont(chat_label_font)
        chat_label.setStyleSheet("color: white;")
        chat_header_layout.addWidget(chat_label)
        chat_header_layout.addStretch()
        chat_header_frame.setMaximumHeight(48)
        right_layout.addWidget(chat_header_frame)
        
        # Chat-Display
        chat_frame = QFrame()
        chat_frame.setStyleSheet(
            f"background-color: {COLORS['surface']}; border: 1px solid {COLORS['primary']}; border-radius: 12px;"
        )
        chat_layout = QVBoxLayout(chat_frame)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMarkdown("")
        self.chat_display.setMinimumHeight(300)
        # Nutze aktuelle Textgröße
        self.chat_display.setStyleSheet(
            f"QTextEdit {{ "
            f"background: {COLORS['background']}; "
            f"color: {COLORS['text']}; "
            f"border: 2px solid {COLORS['primary']}33; "
            f"padding: 16px; "
            f"border-radius: 14px; "
            f"font-size: {self.current_text_size}pt; "
            f"line-height: 1.6; "
            f"}}"
        )
        self.chat_display.setFrameShape(QFrame.Shape.NoFrame)
        chat_layout.addWidget(self.chat_display)
        chat_frame.setLayout(chat_layout)
        right_layout.addWidget(chat_frame)
        
        # Input-Bereich
        input_frame = QFrame()
        input_frame.setStyleSheet(
            f"background: {COLORS['surface']}; border: 2px solid {COLORS['primary']}; border-radius: 16px;"
        )
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(14, 10, 10, 10)
        input_layout.setSpacing(10)
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("💬 Schreib deine Nachricht...")
        self.message_input.setMinimumHeight(46)
        self.message_input.setStyleSheet(
            f"QLineEdit {{ "
            f"background-color: {COLORS['primary']}11; "
            f"color: {COLORS['text']}; "
            f"border: 1px solid {COLORS['primary']}33; "
            f"border-radius: 10px; "
            f"padding: 10px 14px; "
            f"font-size: 11pt; "
            f"font-weight: 500; "
            f"}}"
        )
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        
        send_btn = QPushButton("⚡ SENDEN")
        send_btn.setMaximumWidth(110)
        send_btn.setMinimumHeight(46)
        send_btn.setStyleSheet(
            f"QPushButton {{ "
            f"background-color: {COLORS['primary']}; "
            f"color: white; "
            f"border: none; "
            f"border-radius: 10px; "
            f"font-weight: bold; "
            f"font-size: 10pt; "
            f"padding: 8px 12px; "
            f"}} "
            f"QPushButton:hover {{ background-color: {COLORS['primary_dark']}; }}"
        )
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)
        
        input_frame.setLayout(input_layout)
        right_layout.addWidget(input_frame)
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        # Check Ollama
        if not self.ollama.is_alive():
            self.status_text.setText("🔴 Offline (Ollama nicht erreichbar)")
            self.status_text.setStyleSheet(f"color: {COLORS['error']}; font-weight: bold; font-size: 9pt;")
            QMessageBox.warning(
                self,
                "⚠️ Ollama nicht erreichbar",
                "Ollama läuft nicht auf http://localhost:11434\n\n"
                "Bitte starten Sie Ollama mit: ollama serve"
            )
        else:
            self.status_text.setText("🟢 Online & Ready")
            self.status_text.setStyleSheet(f"color: #00cc44; font-weight: bold; font-size: 9pt;")
    
    def load_chats(self):
        """Lädt alle Chats aus der Datenbank"""
        self.chat_list.clear()
        chats = self.db.get_all_chats()
        
        normalized_names = []
        idx = 1
        for chat_name in list(chats.keys()):
            if chat_name.lower().startswith("log "):
                new_name = f"Chat {idx:02d}"
                counter = 1
                candidate = new_name
                while candidate in chats:
                    candidate = f"{new_name} ({counter})"
                    counter += 1
                renamed = self.db.rename_chat(chat_name, candidate)
                if renamed:
                    chats[candidate] = chats.pop(chat_name)
                    chat_name = candidate
            item = QListWidgetItem(chat_name)
            self.chat_list.addItem(item)
            normalized_names.append(chat_name)
            idx += 1

        if normalized_names:
            first_chat = normalized_names[0]
            self.select_chat(first_chat)
    
    def update_status(self):
        """Aktualisiert den Verbindungsstatus"""
        if self.is_waiting_for_response:
            self.status_text.setText("⏳ Verarbeitung...")
            self.status_text.setStyleSheet(f"color: {COLORS['accent']}; font-weight: bold; font-size: 9pt;")
        elif self._ollama_alive:
            self.status_text.setText("🟢 Online & Ready")
            self.status_text.setStyleSheet(f"color: #00cc44; font-weight: bold; font-size: 9pt;")
        else:
            self.status_text.setText("🔴 Offline")
            self.status_text.setStyleSheet(f"color: {COLORS['error']}; font-weight: bold; font-size: 9pt;")

    def _on_health_update(self, alive: bool):
        """Signal-Handler für Ollama Health-Updates"""
        try:
            self._ollama_alive = bool(alive)
        except Exception:
            pass

    def _user_bubble_html(self, safe_text: str, source: str = None) -> str:
        """HTML für User-Bubbles (Rot) mit Rich Formatting"""
        # Nutze RichFormatter für Markdown und Code-Highlighting
        formatted_content = RichFormatter.format_text(safe_text)
        
        # Badge für Source
        source_badge = ""
        if source:
            source_badge = '<div style="font-size:10px;color:#aaa;margin-bottom:4px;">💬 Du</div>'
        
        primary_color = COLORS['primary']
        html = (
            '<table width="100%" cellpadding="0" cellspacing="0"><tr>'
            '<td width="10%"></td>'
            f'<td align="right" style="padding:8px 4px;">'
            f'{source_badge}'
            f'<div style="display:inline-block;background:{primary_color};color:#ffffff;border-radius:20px;padding:12px 18px;margin:8px 4px;max-width:80%;word-wrap:break-word;font-size:{self.current_text_size}pt;font-weight:500;box-shadow:0 2px 8px rgba(255,75,75,0.3);">'
            f'{formatted_content}'
            '</div>'
            '</td>'
            '</tr></table>'
        )
        return html

    def _assistant_bubble_html(self, safe_text: str, source: str = None, confidence: float = None) -> str:
        """HTML für KI-Bubbles (Dunkelgrau) mit Rich Formatting und Source-Badge"""
        # Nutze RichFormatter für Markdown und Code-Highlighting
        formatted_content = RichFormatter.format_text(safe_text)
        
        # Badge für Source
        source_badge = ""
        if source == "search":
            source_badge = '<div style="font-size:10px;color:#a8f5a8;margin-bottom:4px;">🔍 Gesucht im Web</div>'
        elif source == "llm":
            source_badge = '<div style="font-size:10px;color:#a8d5f5;margin-bottom:4px;">🤖 KI-Antwort</div>'
        elif source == "memory":
            conf_pct = int(confidence * 100) if confidence else 0
            conf_color = "#a8f5a8" if confidence >= 0.8 else "#f5d8a8" if confidence >= 0.6 else "#f5a8a8"
            source_badge = f'<div style="font-size:10px;color:{conf_color};margin-bottom:4px;">💾 Erinnerung ({conf_pct}%)</div>'
        elif source:
            source_badge = f'<div style="font-size:10px;color:#aaa;margin-bottom:4px;">📝 {source}</div>'
        
        text_color = COLORS['text']
        primary_color = COLORS['primary']
        html = (
            '<table width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td align="left" style="padding:8px 4px;">'
            f'{source_badge}'
            f'<div style="display:inline-block;background:#2a2a2a;color:{text_color};border-radius:20px;padding:12px 18px;margin:8px 4px;border:2px solid {primary_color};max-width:85%;word-wrap:break-word;font-size:{self.current_text_size}pt;box-shadow:0 2px 8px rgba(0,0,0,0.5);">'
            f'{formatted_content}'
            '</div>'
            '</td>'
            '<td width="10%"></td>'
            '</tr></table>'
        )
        return html
    
    def on_chat_selected(self, item: QListWidgetItem):
        """Chat selected from list"""
        self.select_chat(item.text())
    
    def select_chat(self, chat_name: str):
        """Wählt einen Chat und zeigt ihn an"""
        self.current_chat = chat_name
        chats = self.db.get_all_chats()
        messages = chats.get(chat_name, [])

        html_parts = []
        html_parts.append('<html><head><meta charset="utf-8"></head><body style="font-family: Segoe UI, Arial, sans-serif; background: transparent; color: ' + COLORS['text'] + ';">')

        # Lade und zeige alle Messages mit Rich Formatting
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            # RichFormatter macht HTML-escaping automatisch!
            if role == "user":
                html_parts.append(self._user_bubble_html(content))
            else:
                html_parts.append(self._assistant_bubble_html(content))

        html_parts.append('</body></html>')
        self.chat_display.setHtml(''.join(html_parts))
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)
        
        # CRITICAL FIX: Stelle sicher dass das Eingabefeld aktiviert ist
        self.message_input.setEnabled(True)
        self.is_waiting_for_response = False
    
    def send_message(self):
        """Sendet eine Nachricht an Astra"""
        if not self.current_chat:
            QMessageBox.warning(self, "⚠️", "Bitte wähle erst einen Chat aus")
            return
        
        message = self.message_input.text().strip()
        if not message:
            return
        
        if not self.rate_limiter.is_allowed():
            QMessageBox.warning(self, "⏱️", "Zu viele Nachrichten!\n\nBitte warten Sie.")
            return
        
        message = SecurityUtils.sanitize_input(message)
        
        if len(message) > SecurityUtils.MAX_MESSAGE_LENGTH:
            QMessageBox.warning(self, "⚠️", f"Nachricht zu lang (max {SecurityUtils.MAX_MESSAGE_LENGTH} Zeichen)")
            return
        
        if self.is_waiting_for_response:
            QMessageBox.information(self, "⏳", "Warte noch auf Antwort...")
            return
        
        # "Merke" Funktion
        if message.lower().startswith("merke"):
            memory_text = message[5:].strip()
            if memory_text:
                self.memory_manager.smart_learn(memory_text)
                
                html_content = self.chat_display.toHtml()
                # RichFormatter eschapt automatisch, nicht doppelt escapen!
                user_bubble = self._user_bubble_html(message)
                success_bubble = self._assistant_bubble_html(f"✅ Gespeichert! Ich merke mir: {memory_text}", source="memory", confidence=0.95)

                if '</body>' in html_content:
                    html_content = html_content.replace('</body>', user_bubble + success_bubble + '</body>')
                else:
                    html_content += user_bubble + success_bubble

                self.chat_display.setHtml(html_content)
                self.db.save_message(self.current_chat, "user", message)
                self.db.save_message(self.current_chat, "assistant", f"✅ Gespeichert! Ich merke mir: {memory_text}")
                self.message_input.clear()
                return
        
        # User-Message anzeigen
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)
        # RichFormatter eschapt automatisch - NIE doppelt escapen!
        self.chat_display.insertHtml(self._user_bubble_html(message))
        self.db.save_message(self.current_chat, "user", message)
        self.message_input.clear()
        # WICHTIG: Inputfeld NICHT disablen - nur is_waiting_for_response Flag sperrt neue Messages
        # das gibt bessere UX weil Benutzer kann tippen statt auf Antwort zu warten
        self.is_waiting_for_response = True
        
        # Auto-learn wird ASYNCHRON im Background gemacht - blockiert UI nicht
        def do_auto_learn():
            """Background: Auto-Learn für Memory"""
            try:
                saved_info = self.memory_manager.auto_learn_from_message(message)
                if saved_info:
                    saved_items = ", ".join([f"{cat}" for cat, val in saved_info])
                    # Zeige Info nur wenn etwas gelernt wurde (optional)
                    # (Kommentiert aus um UI zu beschleunigen)
            except Exception:
                pass  # Fehler beim Background-Lernen ignorieren
        
        # Starte Background-Thread für Auto-Learn
        from threading import Thread
        learn_thread = Thread(target=do_auto_learn, daemon=True)
        learn_thread.start()
        
        # === ASYNCHRONE INTERNET SEARCH INTEGRATION ===
        if SearchEngine.needs_search(message):
            # Speichere Message für später
            self._pending_user_message = message
            
            # Zeige Such-Status mit besserer Visualisierung
            self.chat_display.moveCursor(QTextCursor.MoveOperation.End)
            self.chat_display.insertHtml(self._assistant_bubble_html(
                '⏳ Suche im Internet nach relevanten Informationen...',
                source="search"
            ))
            self.is_waiting_for_response = True
            
            # Starte SearchWorker (asynchron, blockiert UI nicht!)
            self.search_worker = SearchWorker(message, max_results=5)
            self.search_worker.finished.connect(self.on_search_finished)
            self.search_worker.error.connect(self.on_search_error)
            self.search_worker.start()
        else:
            # Keine Suche nötig - starte LLM direkt
            self._pending_user_message = message
            self._start_llm_request(message, "")
    
    def on_search_finished(self, search_results: Dict):
        """Wird aufgerufen wenn die Internet-Suche fertig ist"""
        from modules.logger import astra_logger
        
        search_context = ""
        
        if search_results.get('erfolg'):
            zusammenfassung = search_results.get('zusammenfassung', '')
            num_results = search_results.get('anzahl_ergebnisse', 0)
            astra_logger.info(f"✅ Suche erfolgreich: {num_results} Ergebnisse gefunden")
            
            # Formatiere die Zusammenfassung besser für die KI
            search_context = (
                f"\n\n[INTERNET SEARCH RESULTS FOR: {search_results.get('original_query', '')}]\n"
                f"{zusammenfassung}\n"
                f"[END SEARCH RESULTS]\n\n"
            )
            
            # Ersetze alte Such-Bubble mit Erfolgs-Nachricht
            html = self.chat_display.toHtml()
            html = html.replace(
                '⏳ Suche im Internet nach relevanten Informationen...',
                f'✅ Suche erfolgreich - **{num_results}** Ergebnisse gefunden'
            )
            self.chat_display.setHtml(html)
            astra_logger.info("✅ Suche-Bubble aktualisiert, starte LLM...")
        else:
            # Fehler bei Suche
            error_msg = search_results.get('zusammenfassung', 'Unbekannter Fehler')
            astra_logger.warning(f"⚠️ Suche fehlgeschlagen: {error_msg}")
            
            search_context = f"\n[SEARCH ERROR: {error_msg} - PROCEEDING WITHOUT SEARCH RESULTS]\n"
            
            # Ersetze alte Such-Bubble mit Fehlergrund
            html = self.chat_display.toHtml()
            html = html.replace(
                '⏳ Suche im Internet nach relevanten Informationen...',
                f'⚠️ Suche konnte nicht durchgeführt werden\n**Grund:** {error_msg}\n\nIch beantworte Ihre Frage ohne Web-Recherche.'
            )
            self.chat_display.setHtml(html)
            astra_logger.warning("⚠️ Suche fehlgeschlagen, starte LLM ohne Suchergebnisse...")
        
        # Starte LLM mit Such-Ergebnissen (oder Fehler-Info)
        self._start_llm_request(self._pending_user_message, search_context)
    
    def on_search_error(self, error: str):
        """Wird aufgerufen wenn Suche fehlschlägt"""
        from modules.logger import astra_logger
        
        astra_logger.error(f"❌ SearchWorker Error: {error}")
        
        # Besseres Error Communication für User
        html = self.chat_display.toHtml()
        html = html.replace(
            '⏳ Suche im Internet nach relevanten Informationen...',
            f'❌ Suche konnte nicht durchgeführt werden\n**Fehler:** {error}\n\nIch beantworte Sie trotzdem, ohne Web-Recherche.'
        )
        self.chat_display.setHtml(html)
        
        search_context = f"\n[INTERNET SEARCH FAILED: {error}]\n"
        
        # Starte LLM trotzdem, aber mit Fehler-Info
        astra_logger.info("⚠️ Starte LLM ohne Suchergebnisse (Fehler)")
        self._start_llm_request(self._pending_user_message, search_context)
    
    def _start_llm_request(self, user_message: str, search_context: str = ""):
        """Startet die LLM-Anfrage mit optionalem Such-Kontext"""
        # Loading
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)
        self.chat_display.insertHtml(self._assistant_bubble_html(
            '⏳ Im Gedanken... (KI generiert eine Antwort)',
            source="llm"
        ))
        self.is_waiting_for_response = True
        
        # Vorbereitung der Messages
        chats = self.db.get_all_chats()
        chat_history = chats.get(self.current_chat, [])
        
        # Erweitere die Benutzer-Nachricht mit Such-Kontext falls vorhanden
        user_content = user_message
        if search_context:
            user_content = f"{user_message}{search_context}"
        
        messages = [
            {"role": "system", "content": self.memory_manager.get_system_prompt()}
        ] + chat_history + [
            {"role": "user", "content": user_content}
        ]
        
        # Start LLM-STREAMING Worker
        selected_model = getattr(self, '_selected_model', DEFAULT_MODEL)
        temperature = self.settings_manager.get('temperature', 0.7)
        self.llm_worker = LLMStreamWorker(
            self.ollama,
            selected_model,
            messages,
            temperature
        )
        self.llm_worker.chunk_received.connect(self.on_chunk_received)
        self.llm_worker.finished.connect(self.on_response_received)
        self.llm_worker.error.connect(self.on_response_error)
        self.llm_worker.start()
    
    def on_chunk_received(self, chunk: str):
        """Wird aufgerufen wenn ein Text-Chunk vom LLM kommt"""
        if not self._streaming_started:
            # Erster Chunk: Entferne das "Im Gedanken..." Placeholder
            self._streaming_started = True
            html = self.chat_display.toHtml()
            # Entferne den Placeholder (suche nach der gesamten Bubble)
            html = html.replace('⏳ Im Gedanken... (KI generiert eine Antwort)', '')
            # WICHTIG: Das aktualisierte HTML zurücksetzen
            self.chat_display.setHtml(html)
            # Initialisiere den Response Buffer
            self._current_response = ""
        
        # Sammle den Chunk (KEIN HTML-ESCAPING hier!)
        self._current_response += chunk
        
        # Aktualisiere das Chat-Display mit dem bisherigen Response
        # Entferne das letzte Bubble und setze es mit dem neuen Content neu
        html = self.chat_display.toHtml()
        
        # Entferne das letzte (unvollständige) Assistant-Bubble
        # Suche nach dem letzten <table> und entferne alles danach
        last_table_idx = html.rfind('<table')
        if last_table_idx != -1:
            last_table_end = html.rfind('</table>') + len('</table>')
            if last_table_end > last_table_idx:
                # Entferne das letzte Bubble
                html = html[:last_table_idx]
        
        # Füge ein neues Bubble mit dem aktuellen Response hinzu
        # RichFormatter macht das HTML-Escaping und Formatting!
        html += self._assistant_bubble_html(self._current_response, source="llm")
        self.chat_display.setHtml(html)
        
        # Scrolle zum Ende
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)
        self.chat_display.ensureCursorVisible()
    
    def on_response_received(self, response: str):
        """Wird aufgerufen wenn die komplette Antwort fertig ist"""
        self.is_waiting_for_response = False
        self.message_input.setEnabled(True)
        self._streaming_started = False
        
        memory_texts = self.memory_manager.extract_memory_from_response(response)
        for memory_text in memory_texts:
            if memory_text:
                self.memory_manager.learn(memory_text)
        
        clean_response = self.memory_manager.remove_tags_from_response(response)
        self.db.save_message(self.current_chat, "assistant", clean_response)
    
    def on_response_error(self, error: str):
        """Wird aufgerufen bei Fehler"""
        self.is_waiting_for_response = False
        self.message_input.setEnabled(True)
        
        # Bessere Error Communication mit Details
        error_message = f"""❌ **Fehler bei der KI-Antwort**

**Fehler:** {error}

**Mögliche Ursachen:**
- Die Ollama-Verbindung ist unterbrochen
- Das KI-Modell (`{self._selected_model}`) ist nicht verfügbar
- Die KI hat zu lange für die Antwort gebraucht"""
        
        self.chat_display.moveCursor(QTextCursor.MoveOperation.End)
        self.chat_display.insertHtml(self._assistant_bubble_html(error_message, source="llm"))
        
        astra_logger = __import__('modules.logger', fromlist=['astra_logger']).astra_logger
        astra_logger.error(f"❌ LLM Error: {error}")
    
    def create_new_chat(self):
        """Erstellt einen neuen Chat"""
        from datetime import datetime
        
        chats = self.db.get_all_chats()
        
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
        new_name = f"Chat {timestamp}"
        
        counter = 1
        original_name = new_name
        while new_name in chats:
            new_name = f"{original_name} ({counter})"
            counter += 1
        
        if self.db.create_chat(new_name):
            self.load_chats()
            self.select_chat(new_name)
            QMessageBox.information(self, "✅", f"Chat '{new_name}' erstellt")
        else:
            QMessageBox.critical(self, "❌", f"Chat '{new_name}' existiert bereits")

    def closeEvent(self, event):
        """Cleanup beim Beenden - schnell und effizient"""
        # Stoppe Timer sofort
        try:
            if hasattr(self, 'status_timer'):
                self.status_timer.stop()
        except Exception:
            pass
        
        # Stoppe LLM Worker falls noch laufen
        try:
            if hasattr(self, 'llm_worker') and self.llm_worker and self.llm_worker.isRunning():
                self.llm_worker.quit()
                self.llm_worker.wait(500)  # Kurz warten
        except Exception:
            pass
        
        # Stoppe Health Worker
        try:
            if self.health_worker and self.health_worker.isRunning():
                self.health_worker.stop()
                self.health_worker.wait(500)  # Verkürzt von 2000ms auf 500ms
        except Exception:
            pass
        
        # Schließe Datenbankverbindung
        try:
            if hasattr(self, 'db') and self.db:
                try:
                    self.db.close()
                except Exception:
                    pass
        except Exception:
            pass
        
        super().closeEvent(event)
    
    def delete_current_chat(self):
        """Löscht den aktuellen Chat"""
        if not self.current_chat:
            QMessageBox.warning(self, "⚠️", "Bitte wähle einen Chat zum Löschen")
            return
        
        reply = QMessageBox.question(
            self,
            "⚠️ Chat löschen?",
            f"Möchtest du '{self.current_chat}' wirklich löschen?\nDiese Aktion ist nicht rückgängig zu machen.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_chat(self.current_chat):
                self.load_chats()
                if self.chat_list.count() > 0:
                    self.chat_list.setCurrentRow(0)
                    self.on_chat_selected(self.chat_list.item(0))
                else:
                    self.chat_display.setHtml("<center style='margin-top: 50px; color: #999;'>Keine Chats vorhanden</center>")
                    self.current_chat = None
                QMessageBox.information(self, "✅", "Chat erfolgreich gelöscht")
            else:
                QMessageBox.critical(self, "❌", "Fehler beim Löschen des Chats")
    
    def open_settings(self):
        """Öffnet die Einstellungen"""
        settings_dialog = SettingsDialog(
            self, 
            memory_manager=self.memory_manager,
            settings_manager=self.settings_manager
        )
        
        # Verbinde Signal für Textgröße-Änderungen
        settings_dialog.text_size_changed.connect(self.on_text_size_changed)
        
        if settings_dialog.exec():
            # Aktualisiere das ausgewählte Model
            self._selected_model = settings_dialog.model_combo.currentText()
    
    def on_text_size_changed(self, new_size: int):
        """Wird aufgerufen wenn die Textgröße geändert wird"""
        self.current_text_size = new_size
        
        # Aktualisiere Chat-Display Fontgröße
        self.chat_display.setStyleSheet(
            f"QTextEdit {{ "
            f"background: {COLORS['background']}; "
            f"color: {COLORS['text']}; "
            f"border: 2px solid {COLORS['primary']}33; "
            f"padding: 16px; "
            f"border-radius: 14px; "
            f"font-size: {new_size}pt; "
            f"line-height: 1.6; "
            f"}}"
        )
        
        # Aktualisiere den Chat im Display durch Neuzeichnen
        if self.current_chat:
            self.select_chat(self.current_chat)
