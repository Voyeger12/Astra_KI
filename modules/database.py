"""
ASTRA AI - Datenbank-Modul
==========================
Verwaltet alle Datenbankoperationen (Chats, Memory, Logs)
Mit Sicherheits-Features und Auto-Backups
"""

import sqlite3
import json
import os
import threading
import queue
import time
import shutil
import glob
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from config import DB_PATH
from .logger import astra_logger


class Database:
    """SQLite-Datenbank für Chats, Memory und Logs"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.init_db()
        self._secure_database()  # 🔒 Secure file permissions
        # Background writer queue to serialize writes and avoid "database is locked"
        self._write_queue: "queue.Queue[tuple]" = queue.Queue()
        self._stop_event = threading.Event()
        self._writer_thread = threading.Thread(target=self._writer_loop, daemon=True)
        self._writer_thread.start()
    
    def _secure_database(self) -> None:
        """🔒 Setzt restriktive Dateiberechtigungen (owner only)"""
        try:
            if self.db_path.exists():
                # Windows: Ignorieren (Berechtigungen anders)
                # Linux/Mac: 0o600 = rw------- (nur Owner)
                os.chmod(self.db_path, 0o600)
        except Exception as e:
            print(f"⚠️ Konnte Dateiberechtigungen nicht setzen: {e}")
    
    def _backup_database(self) -> bool:
        """
        Erstellt automatische Sicherung vor destruktiven Operationen
        Behält nur die 5 neuesten Backups (Auto-Cleanup)
        """
        try:
            if not self.db_path.exists():
                return False
            
            # Backup-Verzeichnis
            backup_dir = self.db_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            # Zeitstempel für Backup-Dateiname
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"astra_backup_{timestamp}.db"
            
            # Datenbank kopieren
            shutil.copy2(self.db_path, backup_file)
            
            # Cleanup: Behalte nur die 5 neuesten Backups
            backups = sorted(backup_dir.glob("astra_backup_*.db"), reverse=True)
            for old_backup in backups[5:]:  # Alles außer die 5 neuesten
                try:
                    old_backup.unlink()
                except Exception:
                    pass
            
            return True
        except Exception as e:
            astra_logger.error(f"Fehler beim Erstellen der Backup: {e}")
            return False
    
    def init_db(self) -> None:
        """Initialisiert Datenbanktabellen"""
        try:
            # Use a timeout and allow access from other threads; enable WAL for concurrency
            conn = sqlite3.connect(self.db_path, timeout=5, check_same_thread=False)
            # Enable WAL journaling for better concurrent reads/writes
            conn.execute('PRAGMA journal_mode=WAL;')
            # Set busy timeout to wait a short time if DB is locked by another writer (ms)
            conn.execute('PRAGMA busy_timeout = 5000;')
            conn.execute('PRAGMA synchronous=NORMAL;')
            cursor = conn.cursor()
            
            # Chats-Tabelle
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Messages-Tabelle
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY(chat_id) REFERENCES chats(id) ON DELETE CASCADE
                )
            """)
            
            # Memory-Tabelle (Langzeitgedächtnis)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    category TEXT DEFAULT 'general'
                )
            """)
            
            # Logs-Tabelle
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL
                )
            """)
            
            conn.commit()
            conn.close()
        except Exception as e:
            astra_logger.error(f"Fehler bei DB-Initialisierung: {e}")
    
    def create_chat(self, name: str) -> int:
        """Erstellt einen neuen Chat (mit kurzem Timeout)"""
        try:
            # Kurzer Timeout (1s statt 5s)
            conn = sqlite3.connect(self.db_path, timeout=1, check_same_thread=False)
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO chats (name, created_at, updated_at) VALUES (?, ?, ?)",
                (name, now, now)
            )
            conn.commit()
            chat_id = cursor.lastrowid
            conn.close()
            return chat_id
        except sqlite3.IntegrityError:
            return None
        except sqlite3.OperationalError:
            # Wenn DB momentan locked, retry später mit get_chat_id()
            return None
    
    def get_chat_id(self, name: str) -> Optional[int]:
        """Holt die ID eines Chats (mit kurzem Timeout, non-blocking)"""
        try:
            # Kurzer Timeout (1s statt 5s) - verhindert UI-Blockierung
            conn = sqlite3.connect(self.db_path, timeout=1, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM chats WHERE name = ?", (name,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except sqlite3.OperationalError:
            # Wenn DB locked, return None und lass retry-logic in save_message() das fixen
            return None
        except Exception:
            return None
    
    def get_all_chats(self) -> Dict[str, List[Dict]]:
        """Lädt alle Chats mit ihren Messages"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5, check_same_thread=False)
            cursor = conn.cursor()
            
            chats = {}
            cursor.execute("SELECT id, name FROM chats ORDER BY id ASC")
            chat_rows = cursor.fetchall()
            
            for chat_id, chat_name in chat_rows:
                cursor.execute(
                    "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id ASC",
                    (chat_id,)
                )
                messages = [
                    {"role": role, "content": content}
                    for role, content in cursor.fetchall()
                ]
                chats[chat_name] = messages
            
            conn.close()
            return chats
        except Exception as e:
            astra_logger.error(f"Fehler beim Laden der Chats: {e}")
            return {}
    
    def save_message(self, chat_name: str, role: str, content: str) -> bool:
        """Enqueue eine Nachricht zum asynchronen Speichern.

        Diese Methode ist nicht-blockierend und stellt sicher, dass
        mehrere gleichzeitige Schreibanforderungen serialisiert werden.
        """
        try:
            # Ensure chat exists (mit Retry-Logic)
            chat_id = self.get_chat_id(chat_name)
            if not chat_id:
                chat_id = self.create_chat(chat_name)
            
            # Wenn immer noch keine ID, versuche nochmal nach kurzem Wait
            if not chat_id:
                time.sleep(0.1)
                chat_id = self.get_chat_id(chat_name)
                if not chat_id:
                    # Last resort: Erstelle mit Timeout=5s
                    conn = sqlite3.connect(self.db_path, timeout=5, check_same_thread=False)
                    cursor = conn.cursor()
                    now = datetime.now().isoformat()
                    cursor.execute(
                        "INSERT INTO chats (name, created_at, updated_at) VALUES (?, ?, ?)",
                        (name, now, now) if 'name' in locals() else (chat_name, now, now)
                    )
                    conn.commit()
                    chat_id = cursor.lastrowid
                    conn.close()
            
            # Enqueue actual write job
            if chat_id:
                self._write_queue.put((chat_name, role, content))
                return True
            else:
                astra_logger.error(f"Konnte Chat-ID für '{chat_name}' nicht erstellen")
                return False
        except Exception as e:
            astra_logger.error(f"Fehler beim Enqueue der Nachricht: {e}")
            return False

    def _write_message_sync(self, chat_name: str, role: str, content: str) -> bool:
        """Synchroner Schreib-Pfad, verwendet vom Hintergrund-Worker."""
        try:
            chat_id = self.get_chat_id(chat_name)
            if not chat_id:
                chat_id = self.create_chat(chat_name)

            attempts = 3
            for attempt in range(attempts):
                try:
                    conn = sqlite3.connect(self.db_path, timeout=5, check_same_thread=False)
                    cursor = conn.cursor()
                    now = datetime.now().isoformat()
                    cursor.execute(
                        "INSERT INTO messages (chat_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                        (chat_id, role, content, now)
                    )
                    cursor.execute(
                        "UPDATE chats SET updated_at = ? WHERE id = ?",
                        (now, chat_id)
                    )
                    conn.commit()
                    conn.close()
                    return True
                except sqlite3.OperationalError as oe:
                    if 'locked' in str(oe).lower() and attempt < attempts - 1:
                        time.sleep(0.1 * (attempt + 1))
                        continue
                    else:
                        astra_logger.error(f"Fehler beim synchronen Speichern der Nachricht: {oe}")
                        return False
        except Exception as e:
            astra_logger.error(f"Fehler beim synchronen Speichern der Nachricht: {e}")
            return False

    def _writer_loop(self) -> None:
        """Hintergrund-Thread, der Schreibaufträge seriell abarbeitet."""
        while not self._stop_event.is_set():
            try:
                job = self._write_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if job is None:
                # Shutdown sentinel
                break

            try:
                chat_name, role, content = job
                success = self._write_message_sync(chat_name, role, content)
                if not success:
                    # Fallback: log the failure
                    try:
                        self.write_log(f"DB-Write failed for chat {chat_name}", level="ERROR")
                    except Exception:
                        pass
            finally:
                try:
                    self._write_queue.task_done()
                except Exception:
                    pass

    def close(self) -> None:
        """Sauberes Herunterfahren des Hintergrund-Writers."""
        try:
            self._stop_event.set()
            # Wake the thread if waiting
            self._write_queue.put(None)
            self._writer_thread.join(timeout=2.0)
        except Exception:
            pass
    
    def delete_chat(self, chat_name: str) -> bool:
        """Löscht einen Chat (mit automatischer Sicherung)"""
        try:
            # Erstelle Backup vor destruktiver Operation
            self._backup_database()
            
            chat_id = self.get_chat_id(chat_name)
            if not chat_id:
                return False
            
            conn = sqlite3.connect(self.db_path, timeout=5, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            astra_logger.error(f"Fehler beim Löschen des Chats: {e}")
            return False
    
    def rename_chat(self, old_name: str, new_name: str) -> bool:
        """Benennt einen Chat um"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5, check_same_thread=False)
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute(
                "UPDATE chats SET name = ?, updated_at = ? WHERE name = ?",
                (new_name, now, old_name)
            )
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            return success
        except sqlite3.IntegrityError:
            return False
        except Exception:
            return False
    
    # ========================================================================
    # MEMORY (Langzeitgedächtnis)
    # ========================================================================
    
    def add_memory(self, content: str, category: str = "general") -> bool:
        """Fügt einen Memory-Eintrag hinzu"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5, check_same_thread=False)
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO memory (content, created_at, category) VALUES (?, ?, ?)",
                (content, now, category)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            astra_logger.error(f"Fehler beim Speichern des Memory: {e}")
            return False
    
    def get_memory(self) -> str:
        """Lädt alle Memory-Einträge als formatierter String"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT content, created_at FROM memory ORDER BY id ASC")
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return "Noch keine Gedächtnisfragmente vorhanden."
            
            formatted = []
            for content, timestamp in rows:
                formatted.append(f"[{timestamp}] {content}")
            
            return "\n".join(formatted)
        except Exception as e:
            return f"Fehler beim Laden des Memory: {e}"
    
    def clear_memory(self) -> bool:
        """Löscht alle Memory-Einträge (mit automatischer Sicherung)"""
        try:
            # Erstelle Backup vor destruktiver Operation
            self._backup_database()
            
            conn = sqlite3.connect(self.db_path, timeout=5, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memory")
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    # ========================================================================
    # LOGGING
    # ========================================================================
    
    def write_log(self, message: str, level: str = "INFO") -> bool:
        """Schreibt einen Log-Eintrag"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5, check_same_thread=False)
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?)",
                (now, level, message)
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
