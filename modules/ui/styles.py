"""
ASTRA UI - StyleSheet Manager
=============================
Zentrale Verwaltung aller Stylesheets
"""

from modules.ui.colors import COLORS


class StyleSheet:
    """CSS/Stylesheet für die Anwendung - MODERN & SLEEK"""
    
    @staticmethod
    def get_stylesheet() -> str:
        return f"""
        /* ===== MAIN WINDOW ===== */
        QMainWindow, QWidget {{
            background-color: {COLORS['background']};
            color: {COLORS['text']};
            font-family: 'Segoe UI', 'Consolas', 'Courier New', monospace;
            font-size: 10pt;
            border: none;
        }}
        
        QMainWindow::separator {{
            width: 4px;
            height: 4px;
            background-color: {COLORS['primary']};
        }}
        
        /* ===== INPUTS (Modern Glassmorphism Style) ===== */
        QTextEdit {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 2px solid {COLORS['primary']};
            border-radius: 12px;
            padding: 12px;
            font-size: 10pt;
            selection-background-color: {COLORS['primary']};
            margin: 4px;
        }}
        
        QTextEdit:focus {{
            border: 2px solid {COLORS['accent']};
            background-color: {COLORS['surface']};
        }}
        
        QTextEdit:hover {{
            border: 2px solid {COLORS['accent']};
        }}
        
        QLineEdit {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 2px solid {COLORS['primary']};
            border-radius: 10px;
            padding: 10px 15px;
            font-size: 10pt;
            selection-background-color: {COLORS['primary']};
        }}
        
        QLineEdit:focus {{
            border: 2px solid {COLORS['accent']};
            background-color: {COLORS['surface']};
        }}
        
        QLineEdit:hover {{
            border: 2px solid {COLORS['accent']};
        }}
        
        QLineEdit::placeholder {{
            color: {COLORS['text_secondary']};
        }}
        
        /* ===== BUTTONS (Modern Gradient Style) ===== */
        QPushButton {{
            background-color: {COLORS['primary']};
            color: white;
            border: none;
            border-radius: 10px;
            padding: 12px 24px;
            font-weight: bold;
            font-size: 10pt;
            min-height: 40px;
            font-family: 'Segoe UI', Arial;
            outline: none;
        }}
        
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                       stop:0 {COLORS['accent']},
                                       stop:1 {COLORS['primary']});
            border: 2px solid white;
            font-weight: bold;
            padding: 10px 22px;
        }}
        
        QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                       stop:0 {COLORS['primary_dark']},
                                       stop:1 {COLORS['primary']});
            padding: 13px 23px;
        }}
        
        QPushButton:disabled {{
            background-color: {COLORS['text_secondary']};
            color: {COLORS['surface']};
            opacity: 0.5;
        }}
        
        QPushButton#secondary {{
            background-color: {COLORS['secondary']};
            border: 2px solid {COLORS['primary']};
            color: {COLORS['primary']};
        }}
        
        QPushButton#secondary:hover {{
            background: {COLORS['primary']};
            border: 2px solid {COLORS['accent']};
            color: white;
        }}
        
        QPushButton#danger {{
            background-color: {COLORS['error']};
        }}
        
        QPushButton#danger:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                       stop:0 #ff6b6b,
                                       stop:1 {COLORS['error']});
        }}
        
        /* ===== LIST WIDGET ===== */
        QListWidget {{
            background-color: {COLORS['surface']};
            border: 2px solid {COLORS['primary']};
            border-radius: 12px;
            outline: none;
            margin: 4px;
            show-decoration-selected: 1;
        }}
        
        QListWidget::item {{
            padding: 10px 12px;
            border-radius: 8px;
            margin: 4px 4px;
        }}
        
        QListWidget::item:selected {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                       stop:0 {COLORS['primary']},
                                       stop:1 {COLORS['accent']});
            color: white;
            font-weight: bold;
            border-left: 4px solid {COLORS['accent']};
        }}
        
        QListWidget::item:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                       stop:0 {COLORS['primary']},
                                       stop:0.5 {COLORS['surface']},
                                       stop:1 {COLORS['surface']});
            color: {COLORS['primary']};
            border-radius: 8px;
            font-weight: bold;
        }}
        
        QListWidget::item:focus {{
            outline: none;
        }}
        
        /* ===== COMBO BOX ===== */
        QComboBox {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 2px solid {COLORS['primary']};
            border-radius: 10px;
            padding: 8px 12px;
            min-height: 30px;
        }}
        
        QComboBox:focus {{
            border: 2px solid {COLORS['accent']};
            background-color: {COLORS['surface']};
        }}
        
        QComboBox:hover {{
            border: 2px solid {COLORS['accent']};
        }}
        
        QComboBox::drop-down {{
            border: none;
            background-color: {COLORS['primary']};
            border-radius: 8px;
            width: 35px;
            subcontrol-origin: padding;
            subcontrol-position: top right;
            margin: 2px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            background-color: white;
            border-radius: 4px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            selection-background-color: {COLORS['primary']};
            border: 2px solid {COLORS['primary']};
            border-radius: 8px;
        }}
        
        /* ===== LABELS ===== */
        QLabel {{
            color: {COLORS['text']};
            font-weight: 500;
        }}
        
        QLabel#title {{
            font-size: 14pt;
            font-weight: bold;
            color: {COLORS['primary']};
        }}
        
        QLabel#subtitle {{
            font-size: 11pt;
            color: {COLORS['text_secondary']};
        }}
        
        /* ===== TABS ===== */
        QTabBar::tab {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            padding: 10px 25px;
            border: 2px solid {COLORS['primary']};
            border-radius: 10px 10px 0 0;
            margin-right: 2px;
            font-weight: 500;
        }}
        
        QTabBar::tab:selected {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                       stop:0 {COLORS['primary']},
                                       stop:1 {COLORS['accent']});
            color: white;
            font-weight: bold;
            border: 2px solid {COLORS['accent']};
            padding: 10px 25px;
        }}
        
        QTabBar::tab:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                       stop:0 {COLORS['primary']},
                                       stop:0.5 {COLORS['surface']},
                                       stop:1 {COLORS['surface']});
            color: {COLORS['primary']};
            font-weight: bold;
        }}
        
        QTabWidget::pane {{
            border: 2px solid {COLORS['primary']};
            border-radius: 8px;
            background-color: {COLORS['background']};
            top: -1px;
        }}
        
        QTabBar {{
            background-color: {COLORS['background']};
        }}
        
        /* ===== SCROLLBAR ===== */
        QScrollBar:vertical {{
            background-color: {COLORS['surface']};
            width: 14px;
            border: none;
            border-radius: 7px;
            margin: 0;
        }}
        
        QScrollBar::handle:vertical {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                       stop:0 {COLORS['primary']},
                                       stop:1 {COLORS['accent']});
            border-radius: 7px;
            min-height: 40px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                       stop:0 {COLORS['accent']},
                                       stop:1 {COLORS['primary']});
            min-height: 45px;
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background-color: {COLORS['surface']};
            height: 14px;
            border: none;
            border-radius: 7px;
            margin: 0;
        }}
        
        QScrollBar::handle:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                       stop:0 {COLORS['primary']},
                                       stop:1 {COLORS['accent']});
            border-radius: 7px;
            min-width: 40px;
            margin: 2px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                       stop:0 {COLORS['accent']},
                                       stop:1 {COLORS['primary']});
            min-width: 45px;
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            border: none;
            background: none;
            width: 0px;
        }}
        
        /* ===== DIALOGS ===== */
        QDialog {{
            background-color: {COLORS['background']};
            color: {COLORS['text']};
        }}
        
        QMessageBox {{
            background-color: {COLORS['background']};
            color: {COLORS['text']};
        }}
        
        /* ===== FRAME ===== */
        QFrame {{
            border: none;
            background-color: transparent;
        }}
        
        QFrame#modern {{
            background-color: {COLORS['surface']};
            border: 2px solid {COLORS['primary']};
            border-radius: 12px;
            margin: 4px;
            padding: 8px;
        }}
        
        /* ===== SPLITTER ===== */
        QSplitter::handle {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                       stop:0 {COLORS['primary']},
                                       stop:1 {COLORS['accent']});
            width: 4px;
            height: 4px;
            border-radius: 2px;
        }}
        
        QSplitter::handle:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                       stop:0 {COLORS['accent']},
                                       stop:1 {COLORS['primary']});
        }}
        
        /* ===== SPINBOX & SLIDER ===== */
        QSpinBox {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 2px solid {COLORS['primary']};
            border-radius: 8px;
            padding: 5px 10px;
        }}
        
        QSpinBox::up-button, QSpinBox::down-button {{
            background-color: {COLORS['primary']};
            border: 1px solid {COLORS['primary']};
            width: 20px;
        }}
        
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
            background-color: {COLORS['accent']};
        }}
        
        QSlider::groove:horizontal {{
            background-color: {COLORS['surface']};
            border: 2px solid {COLORS['primary']};
            height: 10px;
            border-radius: 5px;
            margin: 2px 0px;
        }}
        
        QSlider::handle:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                       stop:0 {COLORS['primary']},
                                       stop:1 {COLORS['accent']});
            border: 2px solid {COLORS['accent']};
            width: 18px;
            margin: -4px 0px;
            border-radius: 9px;
        }}
        
        QSlider::handle:horizontal:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                       stop:0 {COLORS['accent']},
                                       stop:1 {COLORS['primary']});
            border: 2px solid white;
        }}
        
        /* ===== SPECIAL STYLING ===== */
        QWidget#loading {{
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                             stop:0 {COLORS['primary']},
                                             stop:0.5 {COLORS['accent']},
                                             stop:1 {COLORS['primary']});
            border-radius: 10px;
        }}
        
        QWidget#success {{
            background-color: #00cc44;
            border-radius: 10px;
        }}
        
        QWidget#error {{
            background-color: {COLORS['error']};
            border-radius: 10px;
        }}
        
        QWidget#warning {{
            background-color: #ffaa00;
            border-radius: 10px;
        }}
        """

    @staticmethod
    def get_checkbox_style() -> str:
        """Styling für Checkboxen in den Einstellungen"""
        return (
            f"QCheckBox {{ "
            f"color: {COLORS['text']}; "
            f"font-size: 10pt; "
            f"spacing: 10px; "
            f"}} "
            f"QCheckBox::indicator {{ "
            f"width: 20px; "
            f"height: 20px; "
            f"border-radius: 4px; "
            f"border: 2px solid {COLORS['primary']}; "
            f"background-color: {COLORS['background']}; "
            f"}} "
            f"QCheckBox::indicator:checked {{ "
            f"background-color: {COLORS['primary']}; "
            f"}} "
            f"QCheckBox::indicator:hover {{ "
            f"border: 2px solid {COLORS['accent']}; "
            f"}}"
        )

__all__ = ['StyleSheet']
