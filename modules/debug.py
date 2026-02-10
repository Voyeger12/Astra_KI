"""
ASTRA Debug Utility - Debugging & Diagnostics
==============================================
Hilfsfunktionen für Debugging und Systemdiagnose
"""

import psutil
import sqlite3
from pathlib import Path
from datetime import datetime
from modules.logger import log_info, log_error

class SystemDiagnostics:
    """Diagnostik-Tools für System-Überblick"""
    
    @staticmethod
    def get_system_info() -> dict:
        """Sammelt System-Informationen"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "process_count": len(psutil.pids()),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            log_error(f"System-Info Fehler: {e}", "DIAGNOSTICS")
            return {}
    
    @staticmethod
    def get_db_stats(db_path: Path) -> dict:
        """Sammelt Datenbank-Statistiken"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Chat-Statistiken
            cursor.execute("SELECT COUNT(*) FROM chats")
            stats['total_chats'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM messages")
            stats['total_messages'] = cursor.fetchone()[0]
            
            # Memory-Statistiken
            cursor.execute("SELECT COUNT(*) FROM memory")
            stats['memory_entries'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT category) FROM memory")
            stats['memory_categories'] = cursor.fetchone()[0]
            
            # Memory-Kategorien Liste
            cursor.execute("SELECT category, COUNT(*) FROM memory GROUP BY category")
            stats['categories_breakdown'] = {cat: count for cat, count in cursor.fetchall()}
            
            conn.close()
            return stats
            
        except Exception as e:
            log_error(f"DB-Stats Fehler: {e}", "DIAGNOSTICS")
            return {}
    
    @staticmethod
    def print_diagnostic_report(db_path: Path) -> None:
        """Druckt einen kompletten Diagnostic-Report"""
        print("\n" + "="*70)
        print("[DIAGNOSTICS] ASTRA SYSTEM DIAGNOSTIC REPORT")
        print("="*70 + "\n")
        
        # System Info
        print("[SYSTEM] RESSOURCEN")
        print("-"*70)
        sys_info = SystemDiagnostics.get_system_info()
        if sys_info:
            print(f"  CPU:             {sys_info.get('cpu_percent', 'N/A')}%")
            print(f"  Memory:          {sys_info.get('memory_percent', 'N/A')}%")
            print(f"  Disk:            {sys_info.get('disk_percent', 'N/A')}%")
            print(f"  Prozesse:        {sys_info.get('process_count', 'N/A')}")
        
        # DB Stats
        print("\n[DB] DATENBANK STATISTIKEN")
        print("-"*70)
        db_stats = SystemDiagnostics.get_db_stats(db_path)
        
        if db_stats:
            print(f"  Chats:           {db_stats.get('total_chats', 0)}")
            print(f"  Messages:        {db_stats.get('total_messages', 0)}")
            print(f"  Memory Entries:  {db_stats.get('memory_entries', 0)}")
            print(f"  Kategorien:      {db_stats.get('memory_categories', 0)}")
            
            if db_stats.get('categories_breakdown'):
                print("\n  Memory nach Kategorie:")
                for category, count in db_stats['categories_breakdown'].items():
                    print(f"    - {category:15} {count:3} Eintraege")
        
        print("\n" + "="*70 + "\n")


class DebugHelper:
    """Hilfsklasse für schnelles Debugging"""
    
    @staticmethod
    def print_memory_content(memory_manager) -> None:
        """Zeigt aktuellen Memory-Inhalt"""
        print("\n[MEMORY] AKTUELLER MEMORY-INHALT")
        print("-"*70)
        
        try:
            memory = memory_manager.get_memory_string()
            if memory:
                print(memory)
            else:
                print("  (leer)")
        except Exception as e:
            print(f"  [ERROR] Fehler: {e}")
        
        print("-"*70 + "\n")
    
    @staticmethod
    def print_chat_history(db, chat_name: str) -> None:
        """Zeigt Chat-Historie"""
        print(f"\n[CHAT] CHAT-HISTORIE: {chat_name}")
        print("-"*70)
        
        try:
            chats = db.get_all_chats()
            if chat_name in chats:
                messages = chats[chat_name]
                for i, msg in enumerate(messages, 1):
                    role = "[U]" if msg['role'] == 'user' else "[AI]"
                    content = msg['content'][:60] + "..." if len(msg['content']) > 60 else msg['content']
                    print(f"  {i}. {role} [{msg['role'].upper()}]: {content}")
            else:
                print("  Chat nicht gefunden")
        except Exception as e:
            print(f"  [ERROR] Fehler: {e}")
        
        print("-"*70 + "\n")
    
    @staticmethod
    def quick_test() -> None:
        """Schnell-Test aller Komponenten"""
        print("\n[QUICK-TEST] Ausfuehrung")
        print("-"*70)
        
        try:
            from modules.database import Database
            from modules.memory import MemoryManager
            from modules.ollama_client import OllamaClient
            
            # DB Test
            db = Database()
            print("[OK] Database geladen")
            
            # Memory Test
            mem = MemoryManager(db)
            print("[OK] MemoryManager geladen")
            
            # Ollama Test
            ollama = OllamaClient()
            if ollama.is_alive():
                print("[OK] Ollama verfuegbar")
            else:
                print("[WARN] Ollama nicht erreichbar")
            
            print("-"*70 + "\n")
        
        except Exception as e:
            print(f"[ERROR] Fehler: {e}")
            print("-"*70 + "\n")
