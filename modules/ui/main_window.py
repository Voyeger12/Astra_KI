"""
ASTRA AI - PyQt6 UI Main Window
================================
Moderne Desktop-Oberfläche mit Rot-Schwarz Design
Modularisierte Struktur für bessere Wartbarkeit
"""

from html import escape as html_escape
from threading import Thread
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QListWidget, QListWidgetItem, QLineEdit,
    QFrame, QMessageBox, QLabel, QFileDialog,
    QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QShortcut, QKeySequence, QAction
from pathlib import Path

from config import COLORS, WINDOW_WIDTH, WINDOW_HEIGHT, OLLAMA_MODELS, DEFAULT_MODEL
from modules.database import Database
from modules.utils import SecurityUtils, RateLimiter, SearchEngine
from modules.ollama_client import OllamaClient
from modules.memory import MemoryManager
from modules.logger import astra_logger

# Modularisierte Imports aus ui Submodule
from modules.ui.styles import StyleSheet
from modules.ui.workers import LLMStreamWorker, HealthWorker, SearchWorker
from modules.ui.settings_manager import SettingsManager
from modules.ui.settings_dialog import SettingsDialog
from modules.ui.rich_formatter import RichFormatter
from modules.ui.chat_display import ChatDisplayWidget
from modules.updater import UpdateChecker, CURRENT_VERSION


class ChatWindow(QMainWindow):
    """Hauptfenster der ASTRA-Anwendung"""
    
    def __init__(self, db: Database = None):
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
        
        # Initialise Komponenten - nutze übergebene DB oder erstelle neue
        self.db = db if db is not None else Database()
        self.ollama = OllamaClient()
        self.memory_manager = MemoryManager(self.db)
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
        self.formatter_worker = None  # Neu: muss initialisiert sein!
        self._ollama_alive = False
        self.health_worker = None
        
        # Status
        self.current_chat = None
        self.is_waiting_for_response = False
        self._streaming_started = False
        self._pending_user_message = ""
        self._current_response = ""
        self._stream_timer = None       # Timer für Echtzeit-Streaming-Anzeige
        
        # Timer für Status-Updates
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(500)
        
        self.load_chats()
        # Start background health worker + Model Preload
        try:
            self.health_worker = HealthWorker(self.ollama, interval=2.0, preload_model=self._selected_model)
            self.health_worker.alive.connect(self._on_health_update)
            self.health_worker.model_loaded.connect(self._on_model_preloaded)
            self.health_worker.start()
        except Exception:
            self._ollama_alive = False
        
        # ⌨️ Keyboard Shortcuts
        self._setup_shortcuts()
        
        # 📥 System-Tray
        self._setup_system_tray()
        self._force_quit = False  # Flag für echtes Beenden vs. Minimize
        
        # 🔄 Auto-Update Check (non-blocking)
        self._check_for_updates()
    
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
        sep1.setStyleSheet("border: none; background-color: #252525; max-height: 1px;")
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
        self.chat_list.itemDoubleClicked.connect(self._on_chat_double_clicked)
        
        # Action-Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(6)
        
        new_chat_btn = QPushButton("➕ Neu")
        new_chat_btn.setMinimumHeight(36)
        new_chat_btn.setStyleSheet(
            f"background-color: {COLORS['primary']}; color: white; border: none; "
            f"border-radius: 14px; font-weight: bold; font-size: 9pt;"
        )
        new_chat_btn.clicked.connect(self.create_new_chat)
        button_layout.addWidget(new_chat_btn)
        
        delete_chat_btn = QPushButton("🗑️ Löschen")
        delete_chat_btn.setMinimumHeight(36)
        delete_chat_btn.setStyleSheet(
            f"background-color: {COLORS['error']}; color: white; border: none; border-radius: 14px; font-weight: bold; font-size: 9pt;"
        )
        delete_chat_btn.clicked.connect(self.delete_current_chat)
        button_layout.addWidget(delete_chat_btn)
        
        left_layout.addLayout(button_layout)
        
        # Export-Button
        export_btn = QPushButton("📤 Chat exportieren")
        export_btn.setMinimumHeight(36)
        export_btn.setStyleSheet(
            f"background-color: #1e1e1e; color: {COLORS['text']}; "
            f"border: 1px solid #2a2a2a; border-radius: 14px; font-weight: bold; font-size: 9pt;"
        )
        export_btn.clicked.connect(self.export_current_chat)
        left_layout.addWidget(export_btn)
        left_layout.addStretch()
        
        # Bottom Section
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("border: none; background-color: #252525; max-height: 1px;")
        left_layout.addWidget(sep2)
        
        settings_btn = QPushButton("⚙️ Einstellungen")
        settings_btn.setMinimumHeight(36)
        settings_btn.setStyleSheet(
            f"background-color: #1e1e1e; color: {COLORS['text']}; "
            f"border: 1px solid #2a2a2a; border-radius: 14px; font-weight: bold; font-size: 9pt;"
        )
        settings_btn.clicked.connect(self.open_settings)
        left_layout.addWidget(settings_btn)
        
        # Status
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(8, 6, 8, 6)
        status_layout.setSpacing(6)
        status_frame.setStyleSheet(
            f"background-color: #161616; border: 1px solid #252525; border-radius: 14px;"
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
        
        # Chat-Display — Widget-basiert für echte runde Bubbles
        chat_frame = QFrame()
        chat_frame.setStyleSheet(
            f"background-color: {COLORS['background']}; border: none; border-radius: 12px;"
        )
        chat_layout = QVBoxLayout(chat_frame)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        
        self.chat_display = ChatDisplayWidget(text_size=self.current_text_size)
        self.chat_display.setMinimumHeight(300)
        chat_layout.addWidget(self.chat_display)
        chat_frame.setLayout(chat_layout)
        right_layout.addWidget(chat_frame)
        
        # Input-Bereich
        input_frame = QFrame()
        input_frame.setStyleSheet(
            f"background: {COLORS['surface']}; border: 1px solid #2a2a2a; border-radius: 20px;"
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
        self.send_btn = send_btn  # Referenz für Stop-Button Toggle
        
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
        """Lädt alle Chat-Namen aus der Datenbank (OPTIMIERT!)"""
        self.chat_list.clear()
        # ⚡ OPTIMIERT: Lade NUR Chat-Namen, nicht alle Messages!
        chat_names = self.db.get_all_chat_names()
        
        normalized_names = []
        idx = 1
        for chat_name in chat_names:
            if chat_name.lower().startswith("log "):
                new_name = f"Chat {idx:02d}"
                counter = 1
                candidate = new_name
                # Nutze get_all_chat_names() für den Check auch
                while candidate in chat_names:
                    candidate = f"{new_name} ({counter})"
                    counter += 1
                renamed = self.db.rename_chat(chat_name, candidate)
                if renamed:
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
        gpu_tag = ""
        if hasattr(self, '_gpu_info') and self._gpu_info:
            backend = self._gpu_info.backend.upper()
            if backend != "CPU":
                gpu_tag = f" ⚡{backend}"
            else:
                gpu_tag = " 🐢CPU"
        
        if self.is_waiting_for_response:
            self.status_text.setText(f"⏳ Verarbeitung...{gpu_tag}")
            self.status_text.setStyleSheet(f"color: {COLORS['accent']}; font-weight: bold; font-size: 9pt;")
        elif self._ollama_alive:
            self.status_text.setText(f"🟢 Online{gpu_tag}")
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

    def _on_model_preloaded(self, success: bool):
        """Signal-Handler wenn Modell vorab geladen wurde"""
        from modules.logger import astra_logger
        if success:
            astra_logger.info(f"⚡ Modell {self._selected_model} erfolgreich vorgeladen (VRAM warm)")
        else:
            astra_logger.warning("⚠️ Modell konnte nicht vorgeladen werden")

    def _add_user_bubble(self, text: str, timestamp: str = ""):
        """Fügt eine User-Bubble als Widget hinzu."""
        formatted = RichFormatter.format_text(text)
        self.chat_display.add_bubble(formatted, role="user", timestamp=timestamp)

    def _add_assistant_bubble(self, text: str, source: str = None,
                               confidence: float = None, timestamp: str = ""):
        """Fügt eine Assistant-Bubble als Widget hinzu."""
        formatted = RichFormatter.format_text(text)
        return self.chat_display.add_bubble(
            formatted, role="assistant", timestamp=timestamp,
            source=source, confidence=confidence
        )
    
    def on_chat_selected(self, item: QListWidgetItem):
        """Chat selected from list"""
        # Ignoriere Klick wenn gerade umbenannt wird (EditRole aktiv)
        if self.chat_list.state() == QListWidget.State.EditingState:
            return
        self.select_chat(item.text())
    
    def _on_chat_double_clicked(self, item: QListWidgetItem):
        """Chat-Umbenennung per Doppelklick"""
        self._rename_old_name = item.text()
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.chat_list.editItem(item)
        # Einmalig: Signal verbinden für Ende der Bearbeitung
        try:
            self.chat_list.itemDelegate().commitData.disconnect(self._on_rename_committed)
        except Exception:
            pass
        self.chat_list.itemDelegate().commitData.connect(self._on_rename_committed)
    
    def _on_rename_committed(self, editor):
        """Wird aufgerufen wenn die Umbenennung bestätigt wird"""
        new_name = editor.text().strip()
        old_name = getattr(self, '_rename_old_name', None)
        
        if not old_name or not new_name or new_name == old_name:
            # Nichts geändert — zurücksetzen
            if old_name:
                item = self.chat_list.currentItem()
                if item:
                    item.setText(old_name)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            return
        
        # Versuche Umbenennung in DB
        if self.db.rename_chat(old_name, new_name):
            # Erfolg — aktualisiere current_chat falls nötig
            if self.current_chat == old_name:
                self.current_chat = new_name
            item = self.chat_list.currentItem()
            if item:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            astra_logger.info(f"✏️ Chat umbenannt: '{old_name}' → '{new_name}'")
        else:
            # Fehlgeschlagen (z.B. Name existiert schon)
            QMessageBox.warning(self, "⚠️", f"Name '{new_name}' existiert bereits!")
            item = self.chat_list.currentItem()
            if item:
                item.setText(old_name)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    
    def select_chat(self, chat_name: str):
        """Wählt einen Chat und zeigt ihn an"""
        # ✅ Stoppe aktive Generierung beim Chat-Wechsel (verhindert Cross-Chat-Contamination)
        if self.is_waiting_for_response and chat_name != self.current_chat:
            self._stop_stream_timer()
            if self.llm_worker and self.llm_worker.isRunning():
                self.llm_worker.cancel()
                self.llm_worker.wait(500)
            if self.search_worker and self.search_worker.isRunning():
                self.search_worker.cancel()
                self.search_worker.wait(300)
            self.is_waiting_for_response = False
            self._streaming_started = False
            self.send_btn.setText("⚡ SENDEN")
            self.message_input.setEnabled(True)
            # Partielle Antwort im ALTEN Chat speichern
            if self._current_response:
                old_chat = getattr(self, '_response_target_chat', self.current_chat)
                clean = self.memory_manager.remove_tags_from_response(self._current_response)
                Thread(target=lambda c=old_chat, r=clean: self.db.save_message(c, "assistant", r + " [abgebrochen]"), daemon=True).start()
                self._current_response = ""
        
        self.current_chat = chat_name
        messages = self.db.get_chat_messages(chat_name)

        # Alle alten Bubbles entfernen
        self.chat_display.clear_all()

        # Bubbles als Widgets hinzufügen
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            raw_ts = msg.get("timestamp", "")
            
            ts_display = ""
            if raw_ts:
                try:
                    ts_display = raw_ts[11:16]
                except Exception:
                    ts_display = ""
            
            formatted = RichFormatter.format_text(content)
            self.chat_display.add_bubble(
                formatted, role=role, timestamp=ts_display
            )
        
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
        
        # Stop-Button: Wenn KI gerade generiert, stoppe stattdessen
        if self.is_waiting_for_response:
            self._stop_generation()
            return
        
        # "Merke" Funktion
        if message.lower().startswith("merke"):
            memory_text = message[5:].strip()
            if memory_text:
                self.memory_manager.learn(memory_text, "personal")
                display_text = memory_text
                
                self._add_user_bubble(message)
                self._add_assistant_bubble(
                    f"✅ Gespeichert! Ich merke mir: {display_text}",
                    source="memory", confidence=0.95
                )
                
                self.db.save_message(self.current_chat, "user", message)
                self.db.save_message(self.current_chat, "assistant", f"✅ Gespeichert! Ich merke mir: {display_text}")
                
                self.message_input.clear()
                return
        
        # User-Message anzeigen
        self._add_user_bubble(message)
        
        # ⚡ Speichere ASYNCHRON ohne UI zu blockieren!
        # WICHTIG: chat_name als lokale Variable capturen (nicht self.current_chat per Referenz!)
        target_chat = self.current_chat
        def save_user_msg(chat=target_chat, msg=message):
            try:
                self.db.save_message(chat, "user", msg)
            except Exception:
                pass
        
        Thread(target=save_user_msg, daemon=True).start()
        
        self.message_input.clear()
        # WICHTIG: Inputfeld NICHT disablen - nur is_waiting_for_response Flag sperrt neue Messages
        # das gibt bessere UX weil Benutzer kann tippen statt auf Antwort zu warten
        self.is_waiting_for_response = True
        
        # 🚫 Auto-Learn DEAKTIVIERT - verursacht fehlerhafte Einträge wie "Name: 30"
        # Memory wird NUR über explizite [MERKEN:...] Tags der KI gespeichert.
        
        # === ASYNCHRONE INTERNET SEARCH INTEGRATION ===
        search_enabled = self.settings_manager.get('search_enabled', True)
        if search_enabled and SearchEngine.needs_search(message):
            # Speichere Message für später
            self._pending_user_message = message
            
            # Zeige Such-Status mit besserer Visualisierung
            self._search_bubble = self._add_assistant_bubble(
                '⏳ Suche im Internet nach relevanten Informationen...',
                source="search"
            )
            self.is_waiting_for_response = True
            
            # Starte SearchWorker mit bereinigtem Query
            self.search_worker = SearchWorker(message, max_results=5)
            self.search_worker.finished.connect(self.on_search_finished)
            self.search_worker.error.connect(self.on_search_error)
            self.search_worker.start()
        else:
            # Keine Suche nötig - starte LLM direkt
            self._pending_user_message = message
            self._start_llm_request(message, "")
    
    def on_search_finished(self, search_results: dict):
        """Wird aufgerufen wenn die Internet-Suche fertig ist"""
        search_context = ""
        
        if search_results.get('erfolg'):
            zusammenfassung = search_results.get('zusammenfassung', '')
            ergebnisse = search_results.get('ergebnisse', [])
            num_results = len(ergebnisse)
            astra_logger.info(f"✅ Suche erfolgreich: {num_results} Ergebnisse gefunden")
            
            # Formatiere die Zusammenfassung besser für die KI
            search_context = (
                f"\n\n[INTERNET SEARCH RESULTS FOR: {search_results.get('original_query', '')}]\n"
                f"{zusammenfassung}\n"
                f"[END SEARCH RESULTS]\n\n"
            )
            
            # Ersetze alte Such-Bubble mit Erfolgs-Nachricht
            self.chat_display.update_search_bubble(
                '⏳ Suche im Internet nach relevanten Informationen...',
                f'✅ Suche erfolgreich - <b>{num_results}</b> Ergebnisse gefunden'
            )
            astra_logger.info("✅ Suche-Bubble aktualisiert, starte LLM...")
        else:
            # Fehler bei Suche
            error_msg = search_results.get('zusammenfassung', 'Unbekannter Fehler')
            astra_logger.warning(f"⚠️ Suche fehlgeschlagen: {error_msg}")
            
            search_context = f"\n[SEARCH ERROR: {error_msg} - PROCEEDING WITHOUT SEARCH RESULTS]\n"
            
            self.chat_display.update_search_bubble(
                '⏳ Suche im Internet nach relevanten Informationen...',
                f'⚠️ Suche konnte nicht durchgeführt werden<br/><b>Grund:</b> {error_msg}'
            )
            astra_logger.warning("⚠️ Suche fehlgeschlagen, starte LLM ohne Suchergebnisse...")
        
        # Starte LLM mit Such-Ergebnissen (oder Fehler-Info)
        self._start_llm_request(self._pending_user_message, search_context)
    
    def on_search_error(self, error: str):
        """Wird aufgerufen wenn Suche fehlschlägt"""
        astra_logger.error(f"❌ SearchWorker Error: {error}")
        
        # Besseres Error Communication für User
        self.chat_display.update_search_bubble(
            '⏳ Suche im Internet nach relevanten Informationen...',
            f'❌ Suche fehlgeschlagen<br/><b>Fehler:</b> {error}'
        )
        
        search_context = f"\n[INTERNET SEARCH FAILED: {error}]\n"
        
        # Starte LLM trotzdem, aber mit Fehler-Info
        astra_logger.info("⚠️ Starte LLM ohne Suchergebnisse (Fehler)")
        self._start_llm_request(self._pending_user_message, search_context)
    
    def _start_llm_request(self, user_message: str, search_context: str = ""):
        """Startet die LLM-Anfrage mit optionalem Such-Kontext"""
        try:
            # 🔥 WICHTIG: Stoppe alte Worker SOFORT!
            if self.llm_worker and self.llm_worker.isRunning():
                astra_logger.info("⚠️ Stoppe alten LLM Worker...")
                self.llm_worker.cancel()
                self.llm_worker.wait(1000)
            
            if self.formatter_worker and self.formatter_worker.isRunning():
                self.formatter_worker.cancel()
                self.formatter_worker.wait(500)
            
            if self.search_worker and self.search_worker.isRunning():
                self.search_worker.cancel()
                self.search_worker.wait(500)
            
            # 🔥 KEINE Placeholder more! Streaming zeigt sofort erste Chunk!
            self.is_waiting_for_response = True
            self._streaming_started = False  # Reset Flag
            self._current_response = ""  # Reset Response Buffer
            self._generation_id = getattr(self, '_generation_id', 0) + 1  # ✅ Generation-ID anti-stale
            self._response_target_chat = self.current_chat  # ✅ Ziel-Chat fixieren (Race-Condition-Schutz)
            astra_logger.info(f"🔥 Starting LLM Request (gen={self._generation_id})...")
            
            # ⚡ OPTIMIERT: Lade NUR den aktuellen Chat, limitiert auf letzte Messages!
            chat_history = self.db.get_chat_messages(self.current_chat)
            # 🔥 WICHTIG: Zu viele Messages = Ollama wird extrem langsam!
            # Limitiere auf die letzten MAX_CHAT_HISTORY_MESSAGES
            from config import MAX_CHAT_HISTORY_MESSAGES
            if len(chat_history) > MAX_CHAT_HISTORY_MESSAGES:
                chat_history = chat_history[-MAX_CHAT_HISTORY_MESSAGES:]
            astra_logger.info(f"📚 Loaded {len(chat_history)} messages for LLM context")
            
            # Erweitere die Benutzer-Nachricht mit Such-Kontext falls vorhanden
            user_content = user_message
            if search_context:
                user_content = f"{user_message}{search_context}"
            
            # ⚡ SICHERHEIT: get_system_prompt() KANN FEHLER WERFEN!
            try:
                system_prompt = self.memory_manager.get_system_prompt()
            except Exception as e:
                astra_logger.error(f"⚠️  get_system_prompt() fehlgeschlagen: {e}")
                system_prompt = "Du bist ein hilfreicher KI-Assistent. Antworte auf Deutsch."
            
            # WICHTIG: Nur role+content an Ollama senden (timestamp rausfiltern!)
            clean_history = [{"role": m["role"], "content": m["content"]} for m in chat_history]
            messages = [
                {"role": "system", "content": system_prompt}
            ] + clean_history + [
                {"role": "user", "content": user_content}
            ]
            
            # Start LLM-STREAMING Worker
            selected_model = getattr(self, '_selected_model', DEFAULT_MODEL)
            temperature = self.settings_manager.get('temperature', 0.7)
            
            astra_logger.info("🚀 Creating LLMStreamWorker for model={selected_model}, temp={temperature}")
            self.llm_worker = LLMStreamWorker(
                self.ollama,
                selected_model,
                messages,
                temperature
            )
            # Speichere Generation-ID am Worker für Stale-Check
            self.llm_worker._gen_id = self._generation_id
            self.llm_worker.chunk_received.connect(self.on_chunk_received)
            self.llm_worker.finished.connect(self.on_response_received)
            self.llm_worker.error.connect(self.on_response_error)
            
            # Sofort sichtbares Feedback: "Denkt nach..."-Bubble + STOP-Button
            self.send_btn.setText("⏹ STOP")
            self.message_input.setEnabled(False)
            self.chat_display.start_streaming_bubble(source="llm")
            self.chat_display.update_streaming_bubble(
                '<span style="color:#888;font-style:italic;">Astra denkt nach...</span>'
            )
            
            astra_logger.info("🚀 Starting LLMStreamWorker thread...")
            self.llm_worker.start()
            astra_logger.info("✅ LLMStreamWorker started!")
        except Exception as e:
            astra_logger.error(f"❌ Fehler in _start_llm_request: {e}", exc_info=True)
            self.on_response_error(f"Kritischer Fehler beim Starten: {e}")
    
    def _stop_generation(self):
        """Stoppt die aktuelle KI-Generierung"""
        astra_logger.info("⏹️ Generation wird gestoppt...")
        
        self._stop_stream_timer()
        
        if self.llm_worker and self.llm_worker.isRunning():
            self.llm_worker.cancel()
            self.llm_worker.wait(1000)
        
        self.is_waiting_for_response = False
        self.message_input.setEnabled(True)
        self._streaming_started = False
        self.send_btn.setText("⚡ SENDEN")
        
        # Zeige partielle Antwort mit Rich-Formatting
        if self._current_response:
            from modules.ui.workers import RichFormatterWorker
            partial = self._current_response + "\n\n⏹️ *Generierung abgebrochen*"
            self.formatter_worker = RichFormatterWorker(
                partial, source="llm", text_size=self.current_text_size
            )
            self.formatter_worker.finished.connect(self._on_formatted_response_final)
            self.formatter_worker.error.connect(self._on_formatter_error)
            self.formatter_worker.start()
            
            # Partielle Antwort speichern — in den RICHTIGEN Chat!
            target_chat = getattr(self, '_response_target_chat', self.current_chat)
            clean = self.memory_manager.remove_tags_from_response(self._current_response)
            self.db.save_message(target_chat, "assistant", clean + " [abgebrochen]")
        else:
            # Keine Chunks empfangen — "Denkt nach..." Bubble durch Abbruch ersetzen
            self.chat_display.finish_streaming_bubble(
                '<span style="color:#888;font-style:italic;">⏹️ Generierung abgebrochen</span>',
                source="llm"
            )
        
        astra_logger.info("⏹️ Generation gestoppt")
    
    def on_chunk_received(self, chunk: str):
        """Sammelt Chunks und zeigt Echtzeit-Streaming-Text."""
        try:
            # ✅ Stale-Check: Ignoriere Chunks von alten Workers
            if hasattr(self, 'llm_worker') and self.llm_worker:
                worker_gen = getattr(self.llm_worker, '_gen_id', -1)
                if worker_gen != getattr(self, '_generation_id', 0):
                    return  # Alter Worker → ignorieren
            
            self._current_response += chunk
            
            if not self._streaming_started:
                # Erstes Chunk — Streaming-Bubble existiert schon ("Denkt nach...")
                # Jetzt Timer starten für Echtzeit-Update
                self._streaming_started = True
                astra_logger.info("🔄 Streaming started, Echtzeit-Anzeige aktiv")
                
                # Sofort erste Anzeige (ersetzt "Denkt nach...")
                self._update_stream_display()
                
                # Timer: Aktualisiere Display alle 120ms
                self._stream_timer = QTimer()
                self._stream_timer.timeout.connect(self._update_stream_display)
                self._stream_timer.start(120)
                
        except Exception as e:
            astra_logger.error(f"❌ Fehler in on_chunk_received: {e}", exc_info=True)
    
    def _update_stream_display(self):
        """Aktualisiert die Streaming-Bubble mit dem bisherigen Text."""
        if not self._current_response:
            return
        try:
            # Escape für HTML-Anzeige, dann einfache Zeilenumbrüche
            safe = html_escape(self._current_response)
            safe = safe.replace('\n', '<br/>')
            self.chat_display.update_streaming_bubble(safe)
        except Exception as e:
            astra_logger.error(f"Stream-Display Update Fehler: {e}")
    
    def _stop_stream_timer(self):
        """Stoppt den Streaming-Timer sauber."""
        if self._stream_timer:
            self._stream_timer.stop()
            self._stream_timer = None

    def on_response_received(self, response: str):
        """Stream fertig → Streaming-Bubble durch Rich-formatierte Version ersetzen."""
        try:
            astra_logger.info(f"✅ Stream fertig: {len(self._current_response)} Zeichen")
            
            # Timer stoppen
            self._stop_stream_timer()
            
            # UI-State zurück
            self.is_waiting_for_response = False
            self.message_input.setEnabled(True)
            self._streaming_started = False
            self.send_btn.setText("⚡ SENDEN")
            
            full_response = self._current_response
            # ✅ Ziel-Chat aus fixierter Variable (nicht self.current_chat, der sich geändert haben könnte!)
            target_chat = getattr(self, '_response_target_chat', self.current_chat)
            
            # ⚡ BACKGROUND: Memory & Speichern (blockiert UI nicht!)
            memory_enabled = self.settings_manager.get('memory_enabled', True)
            def save_and_extract(chat=target_chat):
                try:
                    if memory_enabled:
                        memory_texts = self.memory_manager.extract_memory_from_response(full_response)
                        for i, memory_text in enumerate(memory_texts, 1):
                            if memory_text and len(memory_text) > 2:
                                try:
                                    self.memory_manager.learn(memory_text)
                                    astra_logger.info(f"✅ Memory saved: '{memory_text[:60]}'")
                                except Exception as e:
                                    astra_logger.error(f"Memory save error: {e}")
                    
                    clean_response = self.memory_manager.remove_tags_from_response(full_response)
                    self.db.save_message(chat, "assistant", clean_response)
                    astra_logger.info(f"💾 Response saved to chat '{chat}'")
                except Exception as e:
                    astra_logger.error(f"Save Error: {e}")
            
            Thread(target=save_and_extract, daemon=True).start()
            
            # Streaming-Bubble durch Rich-formatierte Version ersetzen
            from modules.ui.workers import RichFormatterWorker
            self.formatter_worker = RichFormatterWorker(
                full_response,
                source="llm",
                text_size=self.current_text_size
            )
            self.formatter_worker.finished.connect(self._on_formatted_response_final)
            self.formatter_worker.error.connect(self._on_formatter_error)
            self.formatter_worker.start()
            
        except Exception as e:
            msg = f"❌ on_response_received Error: {e}"
            astra_logger.error(msg, exc_info=True)
            self.on_response_error(msg)
    
    def _on_formatted_response_final(self, formatted_html: str):
        """Einmalige Anzeige der komplett formatierten Response."""
        try:
            astra_logger.info("✅ Response formatted, displaying...")
            
            # Ersetze Streaming-Bubble mit formatierter Version
            self.chat_display.finish_streaming_bubble(formatted_html, source="llm")
            
            astra_logger.info("✅ Response displayed")
            
        except Exception as e:
            msg = f"❌ Formatting Error: {e}"
            astra_logger.error(msg, exc_info=True)
    
    def _on_formatter_error(self, error: str):
        """Fallback wenn RichFormatter fehlschlägt - zeige Error-Bubble"""
        astra_logger.warning(f"⚠️ RichFormatter Error: {error}, nutze Fallback")
        
        fallback_text = html_escape(f"[Formatierungsfehler]\n\n{self._current_response[:200]}...")
        fallback_text = fallback_text.replace('\n', '<br/>')
        self.chat_display.finish_streaming_bubble(fallback_text, source="llm")
    
    def on_response_error(self, error: str):
        """Wird aufgerufen bei Fehler"""
        self._stop_stream_timer()
        
        self.is_waiting_for_response = False
        self.message_input.setEnabled(True)
        self.send_btn.setText("⚡ SENDEN")
        
        error_text = html_escape(f"❌ Fehler bei der KI-Antwort\n\nFehler: {error}")
        error_text = error_text.replace('\n', '<br/>')
        
        # Streaming-Bubble existiert immer (erstellt in _start_llm_request)
        # → Ersetze "Denkt nach..." / Streaming-Text durch Fehlermeldung
        self.chat_display.finish_streaming_bubble(error_text, source="llm")
        
        self._streaming_started = False
        astra_logger.error(f"❌ LLM Error: {error}")
    
    def export_current_chat(self):
        """Exportiert den aktuellen Chat als Markdown-Datei"""
        if not self.current_chat:
            QMessageBox.warning(self, "⚠️", "Bitte wähle erst einen Chat aus")
            return
        
        export_text = self.db.export_chat(self.current_chat)
        if not export_text:
            QMessageBox.warning(self, "⚠️", "Chat ist leer")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Chat exportieren", f"{self.current_chat}.md",
            "Markdown (*.md);;Text (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(export_text)
                QMessageBox.information(self, "✅", f"Chat exportiert nach:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "❌", f"Fehler beim Exportieren: {e}")
    
    def create_new_chat(self):
        """Erstellt einen neuen Chat"""
        from datetime import datetime
        
        # ⚡ OPTIMIERT: Nur Chat-Namen laden, nicht die Messages!
        existing_names = self.db.get_all_chat_names()
        
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
        new_name = f"Chat {timestamp}"
        
        counter = 1
        original_name = new_name
        while new_name in existing_names:
            new_name = f"{original_name} ({counter})"
            counter += 1
        
        if self.db.create_chat(new_name):
            self.load_chats()
            self.select_chat(new_name)
            QMessageBox.information(self, "✅", f"Chat '{new_name}' erstellt")
        else:
            QMessageBox.critical(self, "❌", f"Chat '{new_name}' existiert bereits")

    def closeEvent(self, event):
        """Minimize-to-Tray statt Beenden (außer bei Force-Quit)"""
        if not self._force_quit and QSystemTrayIcon.isSystemTrayAvailable() and hasattr(self, 'tray_icon'):
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "ASTRA AI",
                "Läuft weiter im System-Tray. Klicke das Icon zum Öffnen.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            return
        
        # Echtes Beenden — Cleanup
        self._cleanup_and_quit(event)

    def _cleanup_and_quit(self, event):
        """Cleanup aller Worker und Ressourcen beim echten Beenden"""
        # Tray-Icon entfernen
        try:
            if hasattr(self, 'tray_icon'):
                self.tray_icon.hide()
        except Exception:
            pass
        
        try:
            self._stop_stream_timer()
        except Exception:
            pass
        
        # Stoppe Timer sofort
        try:
            if hasattr(self, 'status_timer'):
                self.status_timer.stop()
        except Exception:
            pass
        
        # Stoppe LLM Worker falls noch laufen
        try:
            if hasattr(self, 'llm_worker') and self.llm_worker and self.llm_worker.isRunning():
                self.llm_worker.cancel()
                self.llm_worker.wait(1000)
        except Exception:
            pass
        
        # Stoppe Formatter Worker
        try:
            if hasattr(self, 'formatter_worker') and self.formatter_worker and self.formatter_worker.isRunning():
                self.formatter_worker.cancel()
                self.formatter_worker.wait(500)
        except Exception:
            pass
        
        # Stoppe Search Worker
        try:
            if hasattr(self, 'search_worker') and self.search_worker and self.search_worker.isRunning():
                self.search_worker.cancel()
                self.search_worker.wait(500)
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
                    self.chat_display.show_empty_state("Keine Chats vorhanden")
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
        
        settings_dialog.exec()
        
        # Model IMMER synchronisieren (auch bei Cancel/X),
        # weil SettingsManager bereits bei Änderung gespeichert hat
        self._selected_model = self.settings_manager.get('selected_model', DEFAULT_MODEL)
    
    def on_text_size_changed(self, new_size: int):
        """Wird aufgerufen wenn die Textgröße geändert wird"""
        self.current_text_size = new_size
        
        # Aktualisiere Chat-Display Textgröße
        self.chat_display.set_text_size(new_size)
        
        # Aktualisiere den Chat im Display durch Neuzeichnen
        if self.current_chat:
            self.select_chat(self.current_chat)
    
    # ================================================================
    # AUTO-UPDATE CHECKER
    # ================================================================

    def _check_for_updates(self):
        """Startet Update-Check im Hintergrund (non-blocking)"""
        try:
            self._update_checker = UpdateChecker()
            self._update_checker.update_available.connect(self._on_update_available)
            self._update_checker.no_update.connect(
                lambda: astra_logger.info(f"✅ ASTRA v{CURRENT_VERSION} ist aktuell")
            )
            self._update_checker.check_failed.connect(
                lambda msg: astra_logger.debug(f"Update-Check: {msg}")
            )
            self._update_checker.start()
        except Exception as e:
            astra_logger.debug(f"Update-Check übersprungen: {e}")

    def _on_update_available(self, new_version: str, notes: str, url: str):
        """Zeigt Update-Benachrichtigung im Tray und als Dialog"""
        astra_logger.info(f"🆕 Update verfügbar: v{new_version}")
        
        # Tray-Notification
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.tray_icon.showMessage(
                "🆕 ASTRA Update verfügbar",
                f"Version {new_version} ist verfügbar!\nKlicke für Details.",
                QSystemTrayIcon.MessageIcon.Information,
                5000
            )
        
        # Dialog mit Release-Notes
        msg = QMessageBox(self)
        msg.setWindowTitle("🆕 Update verfügbar")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(
            f"<b>ASTRA AI v{new_version}</b> ist verfügbar!<br>"
            f"Du nutzt aktuell v{CURRENT_VERSION}."
        )
        msg.setInformativeText(
            f"<b>Release-Notes:</b><br>"
            f"<pre style='font-size:10pt;'>{notes[:400]}</pre>"
        )
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {COLORS['surface']};
                color: {COLORS['text']};
            }}
            QLabel {{
                color: {COLORS['text']};
                font-size: 11pt;
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 12px;
                padding: 8px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #ff6b6b;
            }}
        """)
        
        open_button = msg.addButton("🌐 Download", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("Später", QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        
        if msg.clickedButton() == open_button:
            import webbrowser
            webbrowser.open(url)

    # ================================================================
    # SYSTEM TRAY
    # ================================================================

    def _setup_system_tray(self):
        """Richtet System-Tray-Icon mit Kontextmenü ein"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        # Icon laden
        icon_path = Path(__file__).parent.parent.parent / "assets" / "astra_icon.ico"
        icon = QIcon(str(icon_path)) if icon_path.exists() else QIcon()

        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("ASTRA AI — Neural Intelligence")

        # Kontextmenü
        tray_menu = QMenu()
        tray_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['surface']};
                color: {COLORS['text']};
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['primary']};
            }}
        """)

        show_action = QAction("🖥️ ASTRA öffnen", self)
        show_action.triggered.connect(self._tray_show_window)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        new_chat_action = QAction("💬 Neuer Chat", self)
        new_chat_action.triggered.connect(lambda: (self._tray_show_window(), self.create_new_chat()))
        tray_menu.addAction(new_chat_action)

        tray_menu.addSeparator()

        quit_action = QAction("❌ Beenden", self)
        quit_action.triggered.connect(self._quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)

        # Doppelklick auf Tray-Icon → Fenster öffnen
        self.tray_icon.activated.connect(self._on_tray_activated)

        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        """Reaktion auf Tray-Icon Interaktion"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._tray_show_window()

    def _tray_show_window(self):
        """Fenster aus Tray wiederherstellen"""
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _quit_application(self):
        """Echtes Beenden der Anwendung (aus Tray)"""
        self._force_quit = True
        self.close()

    # ================================================================
    # KEYBOARD SHORTCUTS
    # ================================================================
    
    def _setup_shortcuts(self):
        """Richtet globale Keyboard-Shortcuts ein"""
        # Strg+N = Neuer Chat
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.create_new_chat)
        
        # Strg+, = Einstellungen
        QShortcut(QKeySequence("Ctrl+,"), self).activated.connect(self.open_settings)
        
        # Strg+E = Chat exportieren
        QShortcut(QKeySequence("Ctrl+E"), self).activated.connect(self.export_current_chat)
        
        # Strg+D / Entf = Chat löschen
        QShortcut(QKeySequence("Ctrl+D"), self).activated.connect(self.delete_current_chat)
        
        # Esc = Generierung stoppen
        QShortcut(QKeySequence("Escape"), self).activated.connect(self._shortcut_stop)
        
        # Strg+F = Focus auf Eingabefeld
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(
            lambda: self.message_input.setFocus()
        )
        
        # F2 = Aktuellen Chat umbenennen
        QShortcut(QKeySequence("F2"), self).activated.connect(self._shortcut_rename_chat)
    
    def _shortcut_stop(self):
        """Esc-Shortcut: Generierung stoppen falls aktiv"""
        if self.is_waiting_for_response:
            self._stop_generation()
    
    def _shortcut_rename_chat(self):
        """F2-Shortcut: Aktuellen Chat umbenennen"""
        item = self.chat_list.currentItem()
        if item:
            self._on_chat_double_clicked(item)
