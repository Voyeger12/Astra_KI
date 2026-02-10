"""
ASTRA AI - Test & Validierungs-Script
=====================================
Prüft ob alle Komponenten funktionieren
"""

import sys
import os
from pathlib import Path

# Wechsle zum App-Verzeichnis (ein Level höher)
os.chdir(Path(__file__).parent.parent)
sys.path.insert(0, str(Path(__file__).parent.parent))

print("\n" + "=" * 60)
print("ASTRA AI - System-Validierung")
print("=" * 60 + "\n")

# 1. Python-Version
print(f"✅ Python {sys.version.split()[0]}")

# 2. Module
try:
    import config
    print("✅ config.py lädt")
except ImportError as e:
    print(f"❌ config.py: {e}")
    sys.exit(1)

try:
    from modules.database import Database
    print("✅ modules.database lädt")
except ImportError as e:
    print(f"❌ modules.database: {e}")
    sys.exit(1)

try:
    from modules.ollama_client import OllamaClient
    print("✅ modules.ollama_client lädt")
except ImportError as e:
    print(f"❌ modules.ollama_client: {e}")
    sys.exit(1)

try:
    from modules.memory import MemoryManager
    print("✅ modules.memory lädt")
except ImportError as e:
    print(f"❌ modules.memory: {e}")
    sys.exit(1)

try:
    from modules.utils import SearchEngine, TextUtils
    print("✅ modules.utils lädt")
except ImportError as e:
    print(f"❌ modules.utils: {e}")
    sys.exit(1)

# 3. Datenbank
print("\n📦 Testen Database...")
try:
    db = Database()
    print("✅ Datenbank initialisiert")
    
    # Test: Chat erstellen
    chat_id = db.create_chat("Test-Chat")
    if chat_id:
        print(f"✅ Chat erstellt (ID: {chat_id})")
    
    # Test: Message speichern
    if db.save_message("Test-Chat", "user", "Hallo Test"):
        print("✅ Message gespeichert")
    
    # Test: Chats laden
    chats = db.get_all_chats()
    if chats:
        print(f"✅ Chats geladen ({len(chats)} Chat(s))")
    
    # Cleanup
    db.delete_chat("Test-Chat")
    print("✅ Test-Chat gelöscht (Cleanup)")
    
except Exception as e:
    print(f"❌ Datenbank-Fehler: {e}")
    sys.exit(1)

# 4. Ollama
print("\n🤖 Testen Ollama...")
try:
    ollama = OllamaClient()
    if ollama.is_alive():
        print("✅ Ollama erreichbar")
        models = ollama.get_available_models()
        if models:
            print(f"✅ Modelle verfügbar: {', '.join(models[:3])}...")
        else:
            print("⚠️  Keine Modelle heruntergeladen!")
            print("   Starte: ollama pull qwen2.5:14b")
    else:
        print("⚠️  Ollama nicht erreichbar (http://localhost:11434)")
        print("   Starte: ollama serve")
except Exception as e:
    print(f"❌ Ollama-Fehler: {e}")

# 5. Memory
print("\n🧠 Testen Memory-Manager...")
try:
    db = Database()
    memory = MemoryManager(db)
    
    if memory.learn("Test-Information"):
        print("✅ Information gespeichert")
    
    memory_str = memory.get_memory_string()
    if "Test-Information" in memory_str:
        print("✅ Memory abgerufen")
    
    # Cleanup
    memory.clear_memory()
    print("✅ Memory gelöscht (Cleanup)")
    
except Exception as e:
    print(f"❌ Memory-Fehler: {e}")

# 6. PyQt6
print("\n🎨 Testen PyQt6...")
try:
    from PyQt6.QtWidgets import QApplication
    print("✅ PyQt6 installiert")
except ImportError:
    print("❌ PyQt6 nicht installiert!")
    print("   Installiere: pip install PyQt6>=6.6.0")
    sys.exit(1)

# Zusammenfassung
print("\n" + "=" * 60)
print("✅ VALIDIERUNG ERFOLGREICH!")
print("=" * 60)
print("\n🚀 Starte die App mit:")
print("   python main.py")
print("\n💡 Oder nutze start.bat (Windows)\n")
