"""ASTRA AI - Datenbank-Modul"""

import sqlite3
import os
import threading
import queue
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from config import DB_PATH
from .logger import astra_logger


class Database:
    """SQLite-Datenbank für Chats und Memory - mit persistenter Connection
    
    Thread-Safety:
    - _db_lock schützt ALLE Lese- und Schreib-Operationen auf der Connection
    - Background-Writer serialisiert save_message() Aufrufe via Queue
    - Alle anderen Writes (Memory, Chat-CRUD) sind ebenfalls gelockt
    """
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._conn_lock = threading.Lock()
        self._db_lock = threading.RLock()  # Schützt ALLE DB-Operationen (reentrant)
        self._conn: Optional[sqlite3.Connection] = None
        self.init_db()
        self._secure_database()
        # Background writer queue to serialize writes
        self._write_queue: "queue.Queue[tuple]" = queue.Queue()
        self._stop_event = threading.Event()
        self._writer_thread = threading.Thread(target=self._writer_loop, daemon=True)
        self._writer_thread.start()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Gibt persistente Connection zurück (thread-safe)"""
        with self._conn_lock:
            if self._conn is None:
                self._conn = sqlite3.connect(
                    self.db_path, timeout=10, check_same_thread=False
                )
                self._conn.execute('PRAGMA journal_mode=WAL;')
                self._conn.execute('PRAGMA busy_timeout=3000;')
                self._conn.execute('PRAGMA synchronous=NORMAL;')
                self._conn.execute('PRAGMA cache_size=10000;')
                self._conn.execute('PRAGMA temp_store=MEMORY;')
                self._conn.execute('PRAGMA foreign_keys=ON;')
            return self._conn
    
    def _secure_database(self) -> None:
        """🔒 Setzt restriktive Dateiberechtigungen (owner only)"""
        try:
            if self.db_path.exists():
                # Windows: Ignorieren (Berechtigungen anders)
                # Linux/Mac: 0o600 = rw------- (nur Owner)
                os.chmod(self.db_path, 0o600)
        except Exception as e:
            astra_logger.debug(f"Konnte Dateiberechtigungen nicht setzen: {e}")
    
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
        """Initialisiert Datenbanktabellen und Performance-Indexes"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
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
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    category TEXT DEFAULT 'general'
                )
            """)
            
            # Performance-Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_category ON memory(category)")
            
            conn.commit()
        except Exception as e:
            astra_logger.error(f"Fehler bei DB-Initialisierung: {e}")
    
    def create_chat(self, name: str) -> Optional[int]:
        """Erstellt einen neuen Chat"""
        try:
            with self._db_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                cursor.execute(
                    "INSERT INTO chats (name, created_at, updated_at) VALUES (?, ?, ?)",
                    (name, now, now)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
        except sqlite3.OperationalError:
            return None
    
    def get_chat_id(self, name: str) -> Optional[int]:
        """Holt die ID eines Chats"""
        try:
            with self._db_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM chats WHERE name = ?", (name,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception:
            return None
    
    def get_all_chats(self) -> Dict[str, List[Dict]]:
        """Lädt alle Chats mit ihren Messages"""
        try:
            with self._db_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                chats = {}
                cursor.execute("SELECT id, name FROM chats ORDER BY id ASC")
                chat_rows = cursor.fetchall()
                
                for chat_id, chat_name in chat_rows:
                    cursor.execute(
                        "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id ASC",
                        (chat_id,)
                    )
                    chats[chat_name] = [
                        {"role": role, "content": content}
                        for role, content in cursor.fetchall()
                    ]
                
                return chats
        except Exception as e:
            astra_logger.error(f"Fehler beim Laden der Chats: {e}")
            return {}
    
    def get_chat_messages(self, chat_name: str) -> List[Dict]:
        """Lädt die Messages eines einzelnen Chats"""
        try:
            with self._db_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("SELECT id FROM chats WHERE name = ?", (chat_name,))
                result = cursor.fetchone()
                if not result:
                    return []
                
                cursor.execute(
                    "SELECT role, content, timestamp FROM messages WHERE chat_id = ? ORDER BY id ASC",
                    (result[0],)
                )
                return [
                    {"role": role, "content": content, "timestamp": timestamp}
                    for role, content, timestamp in cursor.fetchall()
                ]
        except Exception as e:
            astra_logger.error(f"Fehler beim Laden der Chat-Messages: {e}")
            return []
    
    def get_all_chat_names(self) -> List[str]:
        """Lädt nur die Chat-Namen"""
        try:
            with self._db_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM chats ORDER BY id ASC")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            astra_logger.error(f"Fehler beim Laden der Chat-Namen: {e}")
            return []
    
    def save_message(self, chat_name: str, role: str, content: str) -> bool:
        """Enqueue eine Nachricht zum asynchronen Speichern (non-blocking)."""
        try:
            chat_id = self.get_chat_id(chat_name)
            if not chat_id:
                chat_id = self.create_chat(chat_name)
            
            if not chat_id:
                # Einmal kurz warten und nochmal versuchen
                time.sleep(0.1)
                chat_id = self.get_chat_id(chat_name)
            
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
        """Synchroner Schreib-Pfad, verwendet vom Hintergrund-Worker.
        Gelockt via _db_lock für Thread-Safety."""
        try:
            with self._db_lock:
                chat_id = self._get_chat_id_unlocked(chat_name)
                if not chat_id:
                    chat_id = self._create_chat_unlocked(chat_name)

                if not chat_id:
                    astra_logger.error(f"Konnte Chat-ID für '{chat_name}' nicht erstellen")
                    return False

                conn = self._get_connection()
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
                return True
        except Exception as e:
            astra_logger.error(f"Fehler beim synchronen Speichern der Nachricht: {e}")
            return False
    
    def _get_chat_id_unlocked(self, name: str) -> Optional[int]:
        """Interne Methode — Aufrufer MUSS _db_lock halten!"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM chats WHERE name = ?", (name,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def _create_chat_unlocked(self, name: str) -> Optional[int]:
        """Interne Methode — Aufrufer MUSS _db_lock halten!"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO chats (name, created_at, updated_at) VALUES (?, ?, ?)",
                (name, now, now)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Chat existiert → ID holen
            return self._get_chat_id_unlocked(name)
        except Exception:
            return None

    def _writer_loop(self) -> None:
        """Hintergrund-Thread, der Schreibaufträge seriell abarbeitet."""
        while True:
            try:
                job = self._write_queue.get(timeout=0.5)
            except queue.Empty:
                if self._stop_event.is_set():
                    break  # Nur beenden wenn Queue leer UND stop gesetzt
                continue

            if job is None:
                self._write_queue.task_done()
                break  # Sentinel → sauber beenden

            try:
                chat_name, role, content = job
                self._write_message_sync(chat_name, role, content)
            except Exception as e:
                astra_logger.error(f"Writer-Loop Fehler: {e}")
            finally:
                try:
                    self._write_queue.task_done()
                except Exception:
                    pass

    def close(self) -> None:
        """Sauberes Herunterfahren — Queue wird erst komplett abgearbeitet."""
        try:
            # 1. Sentinel in Queue → Writer verarbeitet alles davor
            self._write_queue.put(None)
            # 2. Warte bis Queue leer ist (max 5s)
            try:
                self._write_queue.join()
            except Exception:
                pass
            # 3. Jetzt erst stop signalisieren
            self._stop_event.set()
            self._writer_thread.join(timeout=3.0)
        except Exception:
            pass
        # Persistente Connection schließen
        with self._conn_lock:
            if self._conn:
                try:
                    self._conn.close()
                except Exception:
                    pass
                self._conn = None
    
    def delete_chat(self, chat_name: str) -> bool:
        """Löscht einen Chat mit allen Messages (mit Backup)"""
        try:
            self._backup_database()
            with self._db_lock:
                chat_id = self._get_chat_id_unlocked(chat_name)
                if not chat_id:
                    return False
                
                conn = self._get_connection()
                cursor = conn.cursor()
                # Messages werden via ON DELETE CASCADE automatisch gelöscht
                cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
                conn.commit()
                return True
        except Exception as e:
            astra_logger.error(f"Fehler beim Löschen des Chats: {e}")
            return False
    
    def rename_chat(self, old_name: str, new_name: str) -> bool:
        """Benennt einen Chat um"""
        try:
            with self._db_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                cursor.execute(
                    "UPDATE chats SET name = ?, updated_at = ? WHERE name = ?",
                    (new_name, now, old_name)
                )
                conn.commit()
                return cursor.rowcount > 0
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
            with self._db_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                cursor.execute(
                    "INSERT INTO memory (content, created_at, category) VALUES (?, ?, ?)",
                    (content, now, category)
                )
                conn.commit()
                return True
        except Exception as e:
            astra_logger.error(f"Fehler beim Speichern des Memory: {e}")
            return False

    def update_or_add_memory(self, content: str, category: str = "general") -> bool:
        """Aktualisiert bestehenden Memory-Eintrag wenn gleiche Kategorie-Prefix existiert.
        
        z.B. 'Alter: 25' überschreibt vorhandenes 'Alter: 30'.
        Wenn kein ':' im Content oder kein bestehender Eintrag → neuer Eintrag.
        """
        try:
            if ":" in content:
                prefix = content.split(":")[0].strip().lower()
                
                with self._db_lock:
                    conn = self._get_connection()
                    cursor = conn.cursor()
                    
                    # Suche bestehenden Eintrag mit gleichem Kategorie-Prefix
                    cursor.execute(
                        "SELECT id, content FROM memory WHERE LOWER(TRIM(content)) LIKE ? ORDER BY id DESC LIMIT 1",
                        (f"{prefix}:%",)
                    )
                    existing = cursor.fetchone()
                    
                    if existing:
                        old_id, old_content = existing
                        now = datetime.now().isoformat()
                        cursor.execute(
                            "UPDATE memory SET content = ?, created_at = ?, category = ? WHERE id = ?",
                            (content, now, category, old_id)
                        )
                        conn.commit()
                        astra_logger.info(f"🔄 Memory aktualisiert: '{old_content}' → '{content}'")
                        return True
            
            # Kein Prefix-Match oder kein Doppelpunkt → neuer Eintrag
            return self.add_memory(content, category)
        except Exception as e:
            astra_logger.error(f"Fehler bei update_or_add_memory: {e}")
            return self.add_memory(content, category)
    
    def get_memory(self) -> str:
        """Lädt alle Memory-Einträge als formatierter String"""
        try:
            with self._db_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT content, created_at FROM memory ORDER BY id ASC")
                rows = cursor.fetchall()
                
                if not rows:
                    return "Noch keine Gedächtnisfragmente vorhanden."
                
                return "\n".join(f"[{ts}] {content}" for content, ts in rows)
        except Exception as e:
            return f"Fehler beim Laden des Memory: {e}"
    
    def clear_memory(self) -> bool:
        """Löscht alle Memory-Einträge (mit automatischer Sicherung)"""
        try:
            self._backup_database()
            with self._db_lock:
                conn = self._get_connection()
                conn.execute("DELETE FROM memory")
                conn.commit()
                return True
        except Exception:
            return False
    
    def get_memory_entries(self) -> List[Dict]:
        """Gibt alle Memory-Einträge als strukturierte Daten zurück"""
        try:
            with self._db_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id, content, category, created_at FROM memory ORDER BY id ASC")
                return [
                    {"id": r[0], "content": r[1], "category": r[2], "created_at": r[3]}
                    for r in cursor.fetchall()
                ]
        except Exception as e:
            astra_logger.error(f"Fehler beim Laden der Memory-Einträge: {e}")
            return []
    
    def delete_memory_by_id(self, memory_id: int) -> bool:
        """Löscht einen einzelnen Memory-Eintrag nach ID"""
        try:
            with self._db_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM memory WHERE id = ?", (memory_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            astra_logger.error(f"Fehler beim Löschen des Memory-Eintrags: {e}")
            return False
    
    def get_memory_count(self) -> int:
        """Gibt die Anzahl der Memory-Einträge zurück"""
        try:
            with self._db_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM memory")
                return cursor.fetchone()[0]
        except Exception:
            return 0
    
    def trim_old_memory(self, max_entries: int) -> int:
        """Entfernt älteste Memory-Einträge wenn Limit überschritten"""
        try:
            with self._db_lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM memory")
                count = cursor.fetchone()[0]
                if count <= max_entries:
                    return 0
                
                to_delete = count - max_entries
                cursor.execute(
                    "DELETE FROM memory WHERE id IN (SELECT id FROM memory ORDER BY id ASC LIMIT ?)",
                    (to_delete,)
                )
                conn.commit()
                deleted = cursor.rowcount
                astra_logger.info(f"🧹 {deleted} alte Memory-Einträge entfernt (Limit: {max_entries})")
                return deleted
        except Exception as e:
            astra_logger.error(f"Fehler beim Trimmen alter Memory-Einträge: {e}")
            return 0
    
    def export_chat(self, chat_name: str) -> str:
        """Exportiert einen Chat als formatierten Markdown-Text"""
        try:
            messages = self.get_chat_messages(chat_name)
            if not messages:
                return ""
            
            lines = [f"# Chat: {chat_name}\n"]
            for msg in messages:
                role = "👤 Du" if msg["role"] == "user" else "🤖 Astra"
                lines.append(f"\n{role}:\n{msg['content']}\n")
            
            return "\n".join(lines)
        except Exception as e:
            astra_logger.error(f"Fehler beim Exportieren des Chats: {e}")
            return ""
