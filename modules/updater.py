"""
ASTRA AI - Auto-Update Checker
================================
Prüft GitHub-Releases auf neue Versionen.
Non-blocking: Läuft im Hintergrund-Thread.
"""

import json
import urllib.request
from packaging import version as pkg_version
from PyQt6.QtCore import QThread, pyqtSignal


# ============================================================================
# Konstanten
# ============================================================================
GITHUB_REPO = "Voyeger12/Astra_KI"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
CURRENT_VERSION = "2.1.0"  # Aktuelle App-Version


class UpdateChecker(QThread):
    """
    Hintergrund-Thread der GitHub auf neue Releases prüft.
    
    Signale:
        update_available(str, str, str): (neue_version, release_notes, download_url)
        no_update(): Kein Update verfügbar
        check_failed(str): Fehler-Nachricht
    """
    update_available = pyqtSignal(str, str, str)  # version, notes, url
    no_update = pyqtSignal()
    check_failed = pyqtSignal(str)

    def __init__(self, current_version: str = CURRENT_VERSION):
        super().__init__()
        self.current_version = current_version

    def run(self):
        """Prüft GitHub API auf neueste Release"""
        try:
            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": f"ASTRA-AI/{self.current_version}"
                }
            )
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status != 200:
                    self.check_failed.emit(f"GitHub API HTTP {resp.status}")
                    return
                
                data = json.loads(resp.read().decode("utf-8"))
            
            tag = data.get("tag_name", "")
            # Tag kann "v2.1.0" oder "2.1.0" sein
            remote_version = tag.lstrip("vV")
            
            if not remote_version:
                self.check_failed.emit("Kein Tag in Release gefunden")
                return
            
            # Version vergleichen
            try:
                is_newer = pkg_version.parse(remote_version) > pkg_version.parse(self.current_version)
            except Exception:
                # Fallback: String-Vergleich
                is_newer = remote_version != self.current_version
            
            if is_newer:
                notes = data.get("body", "Keine Release-Notes verfügbar.")
                # Kürze Notes auf 500 Zeichen
                if len(notes) > 500:
                    notes = notes[:497] + "..."
                
                html_url = data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases")
                
                self.update_available.emit(remote_version, notes, html_url)
            else:
                self.no_update.emit()

        except urllib.error.URLError as e:
            # Kein Internet → still ignorieren
            self.check_failed.emit(f"Netzwerk-Fehler: {str(e)[:80]}")
        except Exception as e:
            self.check_failed.emit(f"Update-Check fehlgeschlagen: {str(e)[:80]}")


def get_current_version() -> str:
    """Gibt die aktuelle Version zurück"""
    return CURRENT_VERSION
