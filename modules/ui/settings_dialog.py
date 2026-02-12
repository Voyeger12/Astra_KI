"""
ASTRA UI - Settings Dialog
===========================
Dialog für Benutzereinstellungen mit Tabs
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QFrame, QLabel,
    QComboBox, QCheckBox, QPushButton, QTabWidget,
    QMessageBox, QSlider, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from pathlib import Path

from config import COLORS, OLLAMA_MODELS, DEFAULT_MODEL
from modules.ui.styles import StyleSheet
from modules.ui.settings_manager import SettingsManager


class SettingsDialog(QDialog):
    """Dialog für Einstellungen - Modernes Design"""
    
    # Signale für Änderungen
    text_size_changed = pyqtSignal(int)
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None, memory_manager=None, settings_manager=None):
        super().__init__(parent)
        self.setWindowTitle("Einstellungen - ASTRA")
        self.setGeometry(200, 150, 700, 600)
        self.setStyleSheet(StyleSheet.get_stylesheet())
        self.memory_manager = memory_manager
        self.settings_manager = settings_manager or SettingsManager()
        
        # Icon setzen
        try:
            icon_path = Path(__file__).parent.parent.parent / "assets" / "astra_icon.ico"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
        except Exception:
            pass
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Baut die gesamte UI auf"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # Header
        self._create_header(main_layout)
        
        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet(
            f"QTabBar::tab {{ padding: 10px 20px; border-radius: 8px; margin-right: 2px; }}"
            f"QTabBar::tab:selected {{ background: linear-gradient(90deg, {COLORS['primary']}, {COLORS['accent']}); color: white; font-weight: bold; }}"
        )
        
        tabs.addTab(self._create_model_tab(), "🤖 Modell")
        tabs.addTab(self._create_features_tab(), "🔧 Funktionen")
        tabs.addTab(self._create_memory_tab(), "🧠 Gedächtnis")
        tabs.addTab(self._create_appearance_tab(), "🎨 Erscheinungsbild")
        
        main_layout.addWidget(tabs)
        
        # Bottom OK-Button
        ok_btn = QPushButton("✅ Schließen")
        ok_btn.setMinimumHeight(40)
        ok_btn.setStyleSheet(
            f"background-color: {COLORS['primary']}; color: white; border: none; "
            f"border-radius: 8px; font-weight: bold; font-size: 11pt;"
        )
        ok_btn.clicked.connect(self.accept)
        main_layout.addWidget(ok_btn)
    
    def _create_header(self, layout):
        """Erstellt den Header des Dialogs"""
        header = QFrame()
        header.setStyleSheet(
            f"background: linear-gradient(90deg, {COLORS['primary']} 0%, {COLORS['accent']} 100%); "
            f"border-radius: 12px;"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        
        header_title = QLabel("⚙️ Einstellungen")
        header_title_font = QFont()
        header_title_font.setPointSize(14)
        header_title_font.setBold(True)
        header_title.setFont(header_title_font)
        header_title.setStyleSheet("color: white; font-weight: bold;")
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        
        header.setMaximumHeight(50)
        layout.addWidget(header)
    
    def _create_model_tab(self) -> QWidget:
        """TAB 1: Modell-Auswahl"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: {COLORS['surface']}; border: 1px solid {COLORS['primary']}; border-radius: 10px;"
        )
        inner = QVBoxLayout(frame)
        inner.setContentsMargins(12, 12, 12, 12)
        inner.setSpacing(8)
        
        label = QLabel("🤖 KI-Modell wählen:")
        label.setStyleSheet(f"color: {COLORS['primary']}; font-weight: bold; font-size: 11pt;")
        inner.addWidget(label)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(OLLAMA_MODELS)
        # Lade gespeicherte Auswahl
        saved_model = self.settings_manager.get('selected_model', DEFAULT_MODEL)
        if saved_model in OLLAMA_MODELS:
            self.model_combo.setCurrentText(saved_model)
        else:
            self.model_combo.setCurrentText(DEFAULT_MODEL)
        
        self.model_combo.setMinimumHeight(36)
        self.model_combo.setStyleSheet(
            f"QComboBox {{ background-color: {COLORS['background']}; color: {COLORS['text']}; "
            f"border: 2px solid {COLORS['primary']}; border-radius: 8px; padding: 6px; }}"
        )
        # Speichere bei Änderung
        self.model_combo.currentTextChanged.connect(
            lambda text: self.settings_manager.set('selected_model', text)
        )
        inner.addWidget(self.model_combo)
        
        info = QLabel("Dies ist das KI-Modell, das für alle Antworten verwendet wird.")
        info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 9pt; font-style: italic;")
        inner.addWidget(info)
        
        layout.addWidget(frame)
        layout.addStretch()
        
        return widget
    
    def _create_features_tab(self) -> QWidget:
        """TAB 2: Funktionen-Schalter"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: {COLORS['surface']}; border: 1px solid {COLORS['primary']}; border-radius: 10px;"
        )
        inner = QVBoxLayout(frame)
        inner.setContentsMargins(12, 12, 12, 12)
        inner.setSpacing(10)
        
        title = QLabel("🔧 Funktionen")
        title.setStyleSheet(f"color: {COLORS['primary']}; font-weight: bold; font-size: 11pt;")
        inner.addWidget(title)
        
        # Checkbox-Style
        checkbox_style = StyleSheet.get_checkbox_style()
        
        # Internet-Suche
        self.search_check = QCheckBox("🔍 Internet-Suche aktiviert")
        self.search_check.setChecked(self.settings_manager.get('search_enabled', True))
        self.search_check.setStyleSheet(checkbox_style)
        self.search_check.setMinimumHeight(28)
        self.search_check.stateChanged.connect(
            lambda: self.settings_manager.set('search_enabled', self.search_check.isChecked())
        )
        inner.addWidget(self.search_check)
        
        # Gedächtnis-Speicherung
        self.memory_check = QCheckBox("🧠 Gedächtnis-Speicherung aktiviert")
        self.memory_check.setChecked(self.settings_manager.get('memory_enabled', True))
        self.memory_check.setStyleSheet(checkbox_style)
        self.memory_check.setMinimumHeight(28)
        self.memory_check.stateChanged.connect(
            lambda: self.settings_manager.set('memory_enabled', self.memory_check.isChecked())
        )
        inner.addWidget(self.memory_check)
        
        # Temperature-Regler
        temp_label = QLabel("🌡️ KI-Kreativität (Temperature):")
        temp_label.setStyleSheet(f"color: {COLORS['primary']}; font-weight: bold; font-size: 10pt; margin-top: 16px;")
        inner.addWidget(temp_label)
        
        temp_layout = QHBoxLayout()
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setMinimum(0)
        self.temp_slider.setMaximum(100)
        temp_value = int(self.settings_manager.get('temperature', 0.7) * 100)
        self.temp_slider.setValue(temp_value)
        self.temp_slider.setStyleSheet(
            f"QSlider::groove:horizontal {{ background: {COLORS['primary']}; height: 6px; margin: 0px; }}"
            f"QSlider::handle:horizontal {{ background: {COLORS['accent']}; width: 16px; margin: -5px 0px; border-radius: 8px; }}"
        )
        
        self.temp_value_label = QLabel(f"{self.temp_slider.value()/100:.2f}")
        self.temp_value_label.setStyleSheet(f"color: {COLORS['accent']}; font-weight: bold; width: 40px;")
        
        def update_temp():
            value = self.temp_slider.value() / 100
            self.temp_value_label.setText(f"{value:.2f}")
            self.settings_manager.set('temperature', value)
        
        self.temp_slider.valueChanged.connect(update_temp)
        temp_layout.addWidget(self.temp_slider)
        temp_layout.addWidget(self.temp_value_label)
        inner.addLayout(temp_layout)
        
        temp_info = QLabel("0 = Präzise, 1.0 = Kreativ")
        temp_info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 9pt; font-style: italic;")
        inner.addWidget(temp_info)
        
        layout.addWidget(frame)
        layout.addStretch()
        
        return widget
    
    def _create_memory_tab(self) -> QWidget:
        """TAB 3: Gedächtnis-Verwaltung mit Einzellöschung"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header mit Anzahl
        self.memory_header = QLabel("📖 Gespeicherte Informationen:")
        self.memory_header.setStyleSheet(f"color: {COLORS['primary']}; font-weight: bold; font-size: 11pt;")
        layout.addWidget(self.memory_header)
        
        # Memory-Liste (statt QTextEdit) - Mehrfachauswahl möglich
        self.memory_list = QListWidget()
        self.memory_list.setMinimumHeight(280)
        self.memory_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.memory_list.setStyleSheet(
            f"QListWidget {{ background-color: {COLORS['surface']}; color: {COLORS['text']}; "
            f"border: 1px solid {COLORS['primary']}; border-radius: 8px; padding: 6px; }}"
            f"QListWidget::item {{ padding: 6px; border-bottom: 1px solid {COLORS['background']}; }}"
            f"QListWidget::item:selected {{ background-color: {COLORS['primary']}; color: white; }}"
        )
        self.update_memory_display()
        layout.addWidget(self.memory_list)
        
        # Info-Label
        info_label = QLabel("💡 Tipp: Einträge mit Klick auswählen (Strg/Shift für Mehrfachauswahl)")
        info_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 9pt; font-style: italic;")
        layout.addWidget(info_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        refresh_btn = QPushButton("🔄 Aktualisieren")
        refresh_btn.setMinimumHeight(36)
        refresh_btn.setStyleSheet(
            f"background-color: {COLORS['primary']}; color: white; border: none; "
            f"border-radius: 8px; font-weight: bold;"
        )
        refresh_btn.clicked.connect(self.update_memory_display)
        button_layout.addWidget(refresh_btn)
        
        delete_selected_btn = QPushButton("🗑️ Ausgewählte löschen")
        delete_selected_btn.setMinimumHeight(36)
        delete_selected_btn.setStyleSheet(
            f"background-color: {COLORS['warning']}; color: #000; border: none; "
            f"border-radius: 8px; font-weight: bold;"
        )
        delete_selected_btn.clicked.connect(self.delete_selected_memories)
        button_layout.addWidget(delete_selected_btn)
        
        clear_btn = QPushButton("⚠️ Alles löschen")
        clear_btn.setMinimumHeight(36)
        clear_btn.setStyleSheet(
            f"background-color: {COLORS['error']}; color: white; border: none; "
            f"border-radius: 8px; font-weight: bold;"
        )
        clear_btn.clicked.connect(self.clear_memory)
        button_layout.addWidget(clear_btn)
        
        layout.addLayout(button_layout)
        
        return widget
    
    def _create_appearance_tab(self) -> QWidget:
        """TAB 4: Erscheinungsbild"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Text-Größe Frame
        frame = QFrame()
        frame.setStyleSheet(
            f"background-color: {COLORS['surface']}; border: 1px solid {COLORS['primary']}; border-radius: 10px;"
        )
        inner = QVBoxLayout(frame)
        inner.setContentsMargins(12, 12, 12, 12)
        inner.setSpacing(10)
        
        title = QLabel("📝 Chat-Text Größe")
        title.setStyleSheet(f"color: {COLORS['primary']}; font-weight: bold; font-size: 11pt;")
        inner.addWidget(title)
        
        # Slider
        size_layout = QHBoxLayout()
        size_layout.setSpacing(10)
        
        size_label = QLabel("Klein")
        size_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        size_layout.addWidget(size_label)
        
        # Lade gespeicherte Textgröße
        saved_size = self.settings_manager.get('text_size', 11)
        
        self.text_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.text_size_slider.setMinimum(9)
        self.text_size_slider.setMaximum(16)
        self.text_size_slider.setValue(saved_size)
        self.text_size_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.text_size_slider.setTickInterval(1)
        self.text_size_slider.setStyleSheet(
            f"QSlider::groove:horizontal {{ background: {COLORS['surface']}; height: 6px; border-radius: 3px; }}"
            f"QSlider::handle:horizontal {{ background: {COLORS['primary']}; width: 18px; margin: -6px 0; border-radius: 9px; }}"
        )
        size_layout.addWidget(self.text_size_slider, 1)
        
        self.size_value_label = QLabel(f"{saved_size}pt")
        self.size_value_label.setStyleSheet(f"color: {COLORS['primary']}; font-weight: bold; min-width: 40px;")
        size_layout.addWidget(self.size_value_label)
        
        size_large = QLabel("Groß")
        size_large.setStyleSheet(f"color: {COLORS['text_secondary']};")
        size_layout.addWidget(size_large)
        
        inner.addLayout(size_layout)
        
        # Preview
        preview_label = QLabel("👀 Vorschau:")
        preview_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 9pt;")
        inner.addWidget(preview_label)
        
        self.preview_user = QLabel("👤 Das ist eine Benutzer-Nachricht")
        self.preview_user.setStyleSheet(
            f"background: {COLORS['primary']}; color: white; border-radius: 12px; padding: 8px 12px; font-size: {saved_size}pt;"
        )
        inner.addWidget(self.preview_user)
        
        self.preview_ai = QLabel("🤖 Das ist eine KI-Nachricht")
        self.preview_ai.setStyleSheet(
            f"background: #2a2a2a; color: {COLORS['text']}; border: 1px solid {COLORS['primary']}; border-radius: 12px; padding: 8px 12px; font-size: {saved_size}pt;"
        )
        inner.addWidget(self.preview_ai)
        
        # Connect slider - Preview UND Signal bei jeder Änderung
        self.text_size_slider.valueChanged.connect(self._on_text_size_changed)
        
        layout.addWidget(frame)
        layout.addStretch()
        
        return widget
    
    def update_memory_display(self):
        """Aktualisiert die Memory-Anzeige als selektierbare Liste"""
        self.memory_list.clear()
        
        if self.memory_manager:
            try:
                entries = self.memory_manager.get_memory_entries()
                if not entries:
                    item = QListWidgetItem("📭 Noch keine Einträge vorhanden.")
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                    self.memory_list.addItem(item)
                    self.memory_header.setText("📖 Gespeicherte Informationen (0):")
                else:
                    self.memory_header.setText(f"📖 Gespeicherte Informationen ({len(entries)}):")
                    for entry in entries:
                        text = f"#{entry['id']} | [{entry['category']}] {entry['content']}"
                        item = QListWidgetItem(text)
                        item.setData(Qt.ItemDataRole.UserRole, entry['id'])
                        self.memory_list.addItem(item)
            except Exception as e:
                item = QListWidgetItem(f"❌ Fehler beim Laden: {e}")
                self.memory_list.addItem(item)
        else:
            item = QListWidgetItem("⚠️ Memory Manager nicht verfügbar")
            self.memory_list.addItem(item)
    
    def delete_selected_memories(self):
        """Löscht die ausgewählten Memory-Einträge"""
        selected = self.memory_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "⚠️", "Bitte wähle Einträge zum Löschen aus")
            return
        
        ids_to_delete = []
        for item in selected:
            memory_id = item.data(Qt.ItemDataRole.UserRole)
            if memory_id is not None:
                ids_to_delete.append(memory_id)
        
        if not ids_to_delete:
            return
        
        reply = QMessageBox.question(
            self,
            "⚠️ Einträge löschen?",
            f"{len(ids_to_delete)} Eintrag/Einträge endgültig löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            deleted = 0
            for mid in ids_to_delete:
                if self.memory_manager.delete_memory(mid):
                    deleted += 1
            
            QMessageBox.information(self, "✅", f"{deleted} Einträge gelöscht")
            self.update_memory_display()
    
    def clear_memory(self):
        """Löscht das gesamte Gedächtnis"""
        if self.memory_manager:
            reply = QMessageBox.question(
                self,
                "⚠️ Gedächtnis löschen?",
                "Möchtest du wirklich das gesamte Gedächtnis löschen?\n\n"
                "Astra wird sich nach dem Löschen nichts mehr über dich merken.\n"
                "Diese Aktion kann nicht rückgängig gemacht werden.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                if self.memory_manager.clear_memory():
                    QMessageBox.information(self, "✅", "Gedächtnis erfolgreich gelöscht!")
                    self.update_memory_display()
                else:
                    QMessageBox.critical(self, "❌", "Fehler beim Löschen des Gedächtnisses")
        else:
            QMessageBox.warning(self, "⚠️", "Memory Manager nicht verfügbar")
    
    def _on_text_size_changed(self):
        """Aktualisiert die Vorschau UND emittiert das Signal"""
        size = self.text_size_slider.value()
        self.size_value_label.setText(f"{size}pt")
        
        self.preview_user.setStyleSheet(
            f"background: {COLORS['primary']}; color: white; border-radius: 12px; "
            f"padding: 8px 12px; font-size: {size}pt; font-weight: 500;"
        )
        self.preview_ai.setStyleSheet(
            f"background: #2a2a2a; color: {COLORS['text']}; border: 2px solid {COLORS['primary']}; "
            f"border-radius: 12px; padding: 8px 12px; font-size: {size}pt;"
        )
        
        # Speichere Einstellung
        self.settings_manager.set('text_size', size)
        
        # Emittiere Signal an ChatWindow
        self.text_size_changed.emit(size)


__all__ = ['SettingsDialog']
