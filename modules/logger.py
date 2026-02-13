"""
ASTRA Logger - Zentrales Logging-System mit Log-Rotation
==========================================================
Einheitliche Logging-Struktur für alle Module
Mit automatischer Log-Rotation (10MB pro Datei)
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

# Log-Verzeichnis
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Log-Konfiguration
# Nutze TimedRotatingFileHandler für tägliche Rotation statt fixen Dateinamen
LOG_FILE = LOG_DIR / "astra.log"  # Basis-Dateiname, Handler rotiert automatisch
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB (als Fallback-Limit)
BACKUP_COUNT = 14  # Halte 14 Tage Logs


class ColoredFormatter(logging.Formatter):
    """Formatter mit Farben für Console-Ausgabe"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[41m',   # Red Background
    }
    RESET = '\033[0m'
    
    def format(self, record):
        if sys.platform == 'win32':
            # Keine Farben auf Windows
            return super().format(record)
        
        levelname = record.levelname
        color = self.COLORS.get(levelname, self.RESET)
        record.levelname = f"{color}{levelname}{self.RESET}"
        return super().format(record)


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Erstellt einen konfigurierten Logger
    
    Args:
        name: Name des Loggers (meist __name__)
        level: Logging-Level
    
    Returns:
        Konfigurierter Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Entferne existierende Handler
    logger.handlers.clear()
    
    # ===== FILE HANDLER MIT TAGESROTATION =====
    file_handler = TimedRotatingFileHandler(
        LOG_FILE, 
        when='midnight',  # Rotiere um Mitternacht
        interval=1,
        backupCount=BACKUP_COUNT,  # Halte 14 Tage
        encoding='utf-8'
    )
    file_handler.suffix = '%Y%m%d'  # astra.log.20250614
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # ===== CONSOLE HANDLER =====
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter(
        '[%(levelname)s] %(name)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


# Global Logger für ASTRA
astra_logger = setup_logger('ASTRA')


def log_debug(message: str, module: str = 'CORE'):
    """Log Debug-Nachricht"""
    astra_logger.debug(f"[{module}] {message}")


def log_info(message: str, module: str = 'CORE'):
    """Log Info-Nachricht"""
    astra_logger.info(f"[{module}] {message}")


def log_warning(message: str, module: str = 'CORE'):
    """Log Warnung"""
    astra_logger.warning(f"[{module}] {message}")


def log_error(message: str, module: str = 'CORE', exception: Exception = None):
    """Log Fehler"""
    if exception:
        astra_logger.error(f"[{module}] {message}", exc_info=exception)
    else:
        astra_logger.error(f"[{module}] {message}")


def log_critical(message: str, module: str = 'CORE'):
    """Log kritischer Fehler"""
    astra_logger.critical(f"[{module}] {message}")


def get_log_file() -> Path:
    """Gibt den Pfad zur aktuellen Log-Datei zurück"""
    return LOG_FILE
