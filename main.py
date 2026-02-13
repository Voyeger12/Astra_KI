"""
ASTRA AI - Haupteinstieg
========================
Main entry point für die Anwendung
Mit Crash-Recovery und Error-Handling
"""

import sys
import os
import traceback
from pathlib import Path

# Stelle sicher, dass wir im richtigen Verzeichnis sind
os.chdir(Path(__file__).parent)

def safe_init_database():
    """Sicheres Initialisieren der Datenbank mit Recovery"""
    try:
        from modules.database import Database
        db = Database()
        
        # Test Database-Integrität über die bestehende Connection (kein zweiter SQLite-Handle!)
        try:
            with db._db_lock:
                conn = db._get_connection()
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check;")
                result = cursor.fetchone()
                
                if result[0] != "ok":
                    print(f"⚠️  Database integrity issue detected: {result[0]}")
                    print("   Versuche zu reparieren...")
        except Exception as integrity_err:
            print(f"⚠️  Integrity-Check fehlgeschlagen: {integrity_err}")
        
        return db
    except Exception as e:
        print(f"❌ Kritischer Database-Fehler: {e}")
        print("   Bitte überprüfen Sie die astra.db Datei")
        raise
try:
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from modules.ui import ChatWindow
    from modules.ollama_client import OllamaClient
    from config import OLLAMA_HOST
    from modules.logger import log_error, log_info
    
    def main():
        """Startet die ASTRA-Anwendung mit Crash-Recovery"""
        
        try:
            # ⚡ Windows: Eigene AppUserModelID setzen
            # Damit zeigt die Taskbar das ASTRA-Icon statt das Python-Icon
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("astra.ai.desktop.v2")
            except Exception:
                pass  # Nicht-Windows oder fehlende Rechte — ignorieren
            
            # PyQt6 App erstellen
            app = QApplication(sys.argv)
            
            # App-Icon global setzen (für Taskbar, Alt+Tab, etc.)
            from PyQt6.QtGui import QIcon
            icon_path = Path(__file__).parent / "assets" / "astra_icon.ico"
            if icon_path.exists():
                app.setWindowIcon(QIcon(str(icon_path)))
            
            # Sichere Database-Initialisierung
            try:
                db = safe_init_database()
                log_info("Database initialisiert", "STARTUP")
            except Exception as e:
                log_error(f"Database-Init fehlgeschlagen: {e}", "STARTUP", e)
                QMessageBox.critical(
                    None,
                    "❌ Kritischer Fehler",
                    f"Datenbank konnte nicht initialisiert werden:\n\n{str(e)}\n\n"
                    "Bitte versuchen Sie die Anwendung später erneut zu starten."
                )
                return 1
            
            # ⚡ GPU erkennen & Ollama konfigurieren
            from modules.gpu_detect import configure_ollama_gpu
            gpu_info = configure_ollama_gpu()
            print(f"🎮 GPU: {gpu_info.summary()}")
            log_info(f"GPU erkannt: {gpu_info.summary()}", "STARTUP")
            
            # Prüfe Ollama-Verbindung
            print("🔍 Prüfe Ollama-Verbindung...")
            ollama = OllamaClient(OLLAMA_HOST)
            
            if not ollama.is_alive():
                print(f"❌ Ollama nicht erreichbar unter {OLLAMA_HOST}")
                
                # Zeige Fehlerdialog
                msg_box = QMessageBox()
                msg_box.setWindowTitle("🔴 Ollama nicht erreichbar")
                msg_box.setText(
                    f"Ollama läuft nicht auf {OLLAMA_HOST}\n\n"
                    "Bitte starten Sie Ollama mit:\n"
                    "  ollama serve\n\n"
                    "Die Anwendung wird trotzdem gestartet, "
                    "aber Sie können keine KI-Anfragen senden."
                )
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.exec()
            else:
                print("✅ Ollama erreichbar")
                models = ollama.get_available_models()
                if models:
                    print(f"✅ Verfügbare Modelle: {', '.join(models)}")
                else:
                    print("⚠️ Keine Modelle verfügbar. Bitte laden Sie ein Modell mit:")
                    print("  ollama pull qwen2.5:14b")
            
            # Starte Hauptfenster
            print("🚀 Starte ASTRA AI...")
            log_info("Starte ChatWindow", "STARTUP")
            window = ChatWindow(db=db)
            window._gpu_info = gpu_info  # GPU-Info für Statusanzeige
            window.show()
            
            log_info("Anwendung erfolgreich gestartet", "STARTUP")
            return app.exec()
        
        except Exception as e:
            # Unerwarteter Fehler
            error_msg = f"Unerwarteter Fehler:\n\n{str(e)}\n\n{traceback.format_exc()}"
            log_error(error_msg, "STARTUP", e)
            
            # Versuche Dialog zu zeigen
            try:
                msg_box = QMessageBox()
                msg_box.setWindowTitle("❌ Kritischer Fehler")
                msg_box.setText(
                    f"Anwendung ist abgestürzt:\n\n{str(e)}\n\n"
                    "Siehe Logdatei für Details."
                )
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.exec()
            except Exception:
                print(error_msg)
            
            return 1
    
    if __name__ == "__main__":
        try:
            exit_code = main()
            sys.exit(exit_code)
        except KeyboardInterrupt:
            print("\n\n[SHUTDOWN] Benutzer hat Anwendung beendet")
            log_info("Anwendung durch Benutzer beendet", "SHUTDOWN")
            sys.exit(0)
        except Exception as e:
            print(f"\n[FATAL] Kritischer Fehler beim Starten: {e}")
            traceback.print_exc()
            log_error(f"Kritischer Fehler: {e}", "FATAL", e)
            sys.exit(1)

except ImportError as e:
    print(f"❌ Fehler beim Import: {e}")
    print("\nBitte installieren Sie die Abhängigkeiten:")
    print("  pip install -r requirements.txt")
    sys.exit(1)

except Exception as e:
    print(f"❌ Fehler beim Starten: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
