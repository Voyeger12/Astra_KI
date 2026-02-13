"""
ASTRA UI - StyleSheet Manager
=============================
Modernes, abgerundetes Design ohne harte Borders
Glassmorphism-inspiriert mit subtilen Akzenten
"""

from pathlib import Path

from modules.ui.colors import COLORS


class StyleSheet:
    """CSS/Stylesheet für die Anwendung - MODERN, RUND & CLEAN"""
    
    @staticmethod
    def get_stylesheet() -> str:
        return f"""
        /* ===== MAIN WINDOW ===== */
        QMainWindow, QWidget {{
            background-color: {COLORS['background']};
            color: {COLORS['text']};
            font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif;
            font-size: 10pt;
            border: none;
        }}
        
        QMainWindow::separator {{
            width: 1px;
            background-color: #252525;
        }}
        
        /* ===== INPUTS (Subtile, abgerundete Felder) ===== */
        QTextEdit {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 1px solid #2a2a2a;
            border-radius: 14px;
            padding: 12px;
            font-size: 10pt;
            selection-background-color: {COLORS['primary']};
        }}
        
        QTextEdit:focus {{
            border: 1px solid {COLORS['primary']}80;
        }}
        
        QLineEdit {{
            background-color: #161616;
            color: {COLORS['text']};
            border: 1px solid #2a2a2a;
            border-radius: 14px;
            padding: 10px 16px;
            font-size: 10pt;
            selection-background-color: {COLORS['primary']};
        }}
        
        QLineEdit:focus {{
            border: 1px solid {COLORS['primary']}80;
        }}
        
        QLineEdit::placeholder {{
            color: #555;
        }}
        
        /* ===== BUTTONS (Pill-Shape, sanfte Hover) ===== */
        QPushButton {{
            background-color: {COLORS['primary']};
            color: white;
            border: none;
            border-radius: 14px;
            padding: 10px 22px;
            font-weight: 600;
            font-size: 10pt;
            min-height: 36px;
            font-family: 'Segoe UI', sans-serif;
        }}
        
        QPushButton:hover {{
            background-color: {COLORS['accent']};
        }}
        
        QPushButton:pressed {{
            background-color: {COLORS['primary_dark']};
        }}
        
        QPushButton:disabled {{
            background-color: #333;
            color: #666;
        }}
        
        /* ===== LIST WIDGET (Kein Border, subtile Items) ===== */
        QListWidget {{
            background-color: transparent;
            border: none;
            outline: none;
            show-decoration-selected: 1;
        }}
        
        QListWidget::item {{
            padding: 10px 14px;
            border-radius: 12px;
            margin: 2px 4px;
            color: {COLORS['text_secondary']};
        }}
        
        QListWidget::item:selected {{
            background-color: {COLORS['primary']};
            color: white;
            font-weight: 600;
        }}
        
        QListWidget::item:hover:!selected {{
            background-color: #1e1e1e;
            color: {COLORS['text']};
        }}
        
        QListWidget::item:focus {{
            outline: none;
        }}
        
        /* ===== COMBO BOX ===== */
        QComboBox {{
            background-color: #161616;
            color: {COLORS['text']};
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            padding: 10px 14px;
            min-height: 32px;
        }}
        
        QComboBox:hover {{
            border: 1px solid {COLORS['primary']}60;
        }}
        
        QComboBox::drop-down {{
            border: none;
            background: transparent;
            width: 30px;
            subcontrol-origin: padding;
            subcontrol-position: center right;
            margin-right: 8px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {COLORS['text_secondary']};
            margin-right: 4px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: #1a1a1a;
            color: {COLORS['text']};
            selection-background-color: {COLORS['primary']};
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            padding: 4px;
        }}
        
        /* ===== LABELS ===== */
        QLabel {{
            color: {COLORS['text']};
            background: transparent;
            border: none;
        }}
        
        /* ===== TABS (Pill-Tabs, kein Border am Pane) ===== */
        QTabBar {{
            background-color: transparent;
        }}
        
        QTabBar::tab {{
            background-color: #1a1a1a;
            color: {COLORS['text_secondary']};
            padding: 10px 22px;
            border: none;
            border-radius: 12px;
            margin: 2px 3px;
            font-weight: 500;
        }}
        
        QTabBar::tab:selected {{
            background-color: {COLORS['primary']};
            color: white;
            font-weight: 700;
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: #252525;
            color: {COLORS['text']};
        }}
        
        QTabWidget::pane {{
            border: none;
            background-color: {COLORS['background']};
            border-radius: 12px;
        }}
        
        /* ===== SCROLLBAR (Schlank & dezent) ===== */
        QScrollBar:vertical {{
            background-color: transparent;
            width: 8px;
            border: none;
            margin: 4px 2px;
        }}
        
        QScrollBar::handle:vertical {{
            background: #333;
            border-radius: 4px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {COLORS['primary']}80;
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background-color: transparent;
            height: 8px;
            border: none;
            margin: 2px 4px;
        }}
        
        QScrollBar::handle:horizontal {{
            background: #333;
            border-radius: 4px;
            min-width: 30px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background: {COLORS['primary']}80;
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
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
        
        /* ===== SPLITTER (Dezente Linie) ===== */
        QSplitter::handle {{
            background: #252525;
            width: 1px;
        }}
        
        QSplitter::handle:hover {{
            background: {COLORS['primary']}60;
        }}
        
        /* ===== SLIDER (Modern, rund) ===== */
        QSlider::groove:horizontal {{
            background-color: #252525;
            border: none;
            height: 6px;
            border-radius: 3px;
        }}
        
        QSlider::sub-page:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 {COLORS['primary']},
                                    stop:1 {COLORS['accent']});
            border-radius: 3px;
        }}
        
        QSlider::handle:horizontal {{
            background: white;
            border: 2px solid {COLORS['primary']};
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 9px;
        }}
        
        QSlider::handle:horizontal:hover {{
            background: {COLORS['accent']};
            border-color: {COLORS['accent']};
        }}
        
        /* ===== SPINBOX ===== */
        QSpinBox {{
            background-color: #161616;
            color: {COLORS['text']};
            border: 1px solid #2a2a2a;
            border-radius: 10px;
            padding: 6px 10px;
        }}
        
        QSpinBox::up-button, QSpinBox::down-button {{
            background-color: #252525;
            border: none;
            width: 20px;
            border-radius: 4px;
        }}
        
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
            background-color: {COLORS['primary']};
        }}
        """

    @staticmethod
    def get_checkbox_style() -> str:
        """Modernes Checkbox-Styling mit sichtbarem Haken"""
        # SVG-Pfad für den Checkmark (forward slashes für Qt CSS)
        check_svg = (Path(__file__).parent.parent.parent / "assets" / "check.svg").as_posix()
        
        return (
            f"QCheckBox {{ "
            f"color: {COLORS['text']}; "
            f"font-size: 10pt; "
            f"spacing: 14px; "
            f"padding: 8px 4px; "
            f"}} "
            f"QCheckBox::indicator {{ "
            f"width: 26px; "
            f"height: 26px; "
            f"border-radius: 8px; "
            f"border: 2px solid #444; "
            f"background-color: #1a1a1a; "
            f"}} "
            f"QCheckBox::indicator:checked {{ "
            f"background-color: {COLORS['primary']}; "
            f"border-color: {COLORS['primary']}; "
            f"image: url({check_svg}); "
            f"}} "
            f"QCheckBox::indicator:unchecked:hover {{ "
            f"border-color: {COLORS['accent']}; "
            f"background-color: #252525; "
            f"}} "
            f"QCheckBox::indicator:checked:hover {{ "
            f"background-color: {COLORS['accent']}; "
            f"border-color: {COLORS['accent']}; "
            f"}}"
        )

__all__ = ['StyleSheet']
