#!/usr/bin/env python3
"""
ASTRA Test Runner - Master-Testprogramm
========================================
Zentrale Test- und Diagnose-Plattform
"""

import sys
from pathlib import Path

# Füge Projekt-Root zu Path hinzu
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.logger import setup_logger, log_info
from test_suite import AstraTestSuite
from modules.debug import SystemDiagnostics, DebugHelper
from modules.database import Database

# Setup Logger
logger = setup_logger(__name__)


def print_menu() -> None:
    """Zeigt Haupt-Menü"""
    print("\n" + "="*70)
    print("[TEST] ASTRA SYSTEM - Test & Diagnose Center")
    print("="*70)
    print("\nMenü:")
    print("  1. [TEST] Komplette Test-Suite ausführen")
    print("  2. [DIAG] System-Diagnose")
    print("  3. [DB] Datenbank-Info")
    print("  4. [MEM] Memory-Inhalt anzeigen")
    print("  5. [QUICK] Schnell-Test")
    print("  6. [CHAT] Chat-Historie anzeigen")
    print("  0. [EXIT] Beenden")
    print("="*70 + "\n")


def run_tests() -> None:
    """Führt komplette Test-Suite aus"""
    log_info("Starte komplette Test-Suite", "MAIN")
    suite = AstraTestSuite()
    suite.run_all_tests()


def show_diagnostics() -> None:
    """Zeigt System-Diagnostik"""
    db_path = PROJECT_ROOT / "astra.db"
    SystemDiagnostics.print_diagnostic_report(db_path)


def show_db_info() -> None:
    """Zeigt Datenbank-Infos"""
    try:
        db = Database()
        print("\n[DB] DATENBANK INFORMATIONEN")
        print("-"*70)
        
        chats = db.get_all_chats()
        print(f"Chats:           {len(chats)}")
        
        for chat_name, messages in chats.items():
            print(f"\n  '{chat_name}':")
            print(f"    - Nachrichten: {len(messages)}")
            if messages:
                print(f"    - Erste:       {messages[0]['content'][:50]}...")
                print(f"    - Letzte:      {messages[-1]['content'][:50]}...")
        
        print("-"*70 + "\n")
    
    except Exception as e:
        print(f"[ERROR] Fehler: {e}\n")


def show_memory() -> None:
    """Zeigt Memory-Inhalt"""
    try:
        from modules.database import Database
        from modules.memory import MemoryManager
        
        db = Database()
        mem = MemoryManager(db)
        DebugHelper.print_memory_content(mem)
    
    except Exception as e:
        print(f"❌ Fehler: {e}\n")


def show_quick_test() -> None:
    """Führt Schnell-Test aus"""
    DebugHelper.quick_test()


def show_chat_history() -> None:
    """Zeigt Chat-Historie"""
    try:
        db = Database()
        chats = db.get_all_chats()
        
        if not chats:
            print("\nKeine Chats vorhanden.\n")
            return
        
        print("\n[CHAT] VERFUEGBARE CHATS:")
        for i, chat_name in enumerate(chats.keys(), 1):
            print(f"  {i}. {chat_name}")
        
        choice = input("\nWelchen Chat anzeigen? (Nr oder Name): ").strip()
        
        # Versuche zu matchen
        selected_chat = None
        
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(chats):
                selected_chat = list(chats.keys())[idx]
        else:
            # Nach Name suchen
            for chat_name in chats.keys():
                if choice.lower() in chat_name.lower():
                    selected_chat = chat_name
                    break
        
        if selected_chat:
            DebugHelper.print_chat_history(db, selected_chat)
        else:
            print("\n[ERROR] Chat nicht gefunden.\n")
    
    except Exception as e:
        print(f"[ERROR] Fehler: {e}\n")


def main() -> None:
    """Haupt-Schleife"""
    log_info("Test-Runner gestartet", "MAIN")
    
    while True:
        print_menu()
        choice = input("Wähle eine Option (0-6): ").strip()
        
        if choice == "1":
            run_tests()
        elif choice == "2":
            show_diagnostics()
        elif choice == "3":
            show_db_info()
        elif choice == "4":
            show_memory()
        elif choice == "5":
            show_quick_test()
        elif choice == "6":
            show_chat_history()
        elif choice == "0":
            print("\n[EXIT] Auf Wiedersehen!\n")
            log_info("Test-Runner beendet", "MAIN")
            break
        else:
            print("\n[ERROR] Ungültige Eingabe. Bitte versuche erneut.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARN] Unterbrochen durch Benutzer\n")
        log_info("Test-Runner unterbrochen", "MAIN")
    except Exception as e:
        print(f"\n[ERROR] Kritischer Fehler: {e}\n")
        log_info(f"Test-Runner kritischer Fehler: {e}", "MAIN")
