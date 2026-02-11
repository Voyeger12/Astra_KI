"""
ASTRA AI - Build Script
=======================
Kompiliert die Anwendung zu einer EXE mit PyInstaller
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def build_exe():
    """Baut die EXE mit PyInstaller"""
    
    print("=" * 60)
    print("ASTRA AI - PyInstaller Build")
    print("=" * 60)
    
    # Prüfe PyInstaller
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__} gefunden")
    except ImportError:
        print("❌ PyInstaller nicht installiert!")
        print("Installieren Sie: pip install pyinstaller")
        return False
    
    # Verzeichnisse
    app_dir = Path(__file__).parent
    build_dir = app_dir / "build"
    dist_dir = app_dir / "dist"
    
    # Cleanup alte Builds
    print("\n🧹 Räume auf...")
    for directory in [build_dir, dist_dir, app_dir / "ASTRA AI.spec"]:
        if isinstance(directory, Path) and directory.exists():
            if directory.is_dir():
                shutil.rmtree(directory)
            else:
                directory.unlink()
    
    # PyInstaller-Befehl
    print("\n🔨 Baue Anwendung...")
    cmd = [
        "pyinstaller",
        "--name=ASTRA AI",
        "--onefile",
        "-w",
        "--icon=ASTRA.ico" if (app_dir / "ASTRA.ico").exists() else "",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        # PyQt6 Hidden Imports
        "--hidden-import=PyQt6.QtPrintSupport",
        "--hidden-import=PyQt6.QtSvg",
        "--collect-all=PyQt6",
        # Internet Search Dependencies
        "--hidden-import=ddgs",
        "--hidden-import=requests",
        "--collect-all=ddgs",
        "--collect-all=requests",
        # Datenbank & Logging
        "--hidden-import=sqlite3",
        "--hidden-import=logging",
        # Fallback für altes Paket (falls noch entfernt nicht werden kann)
        "--hidden-import=duckduckgo_search",
        # Module
        str(app_dir / "main.py")
    ]
    
    # Entferne leere Strings
    cmd = [arg for arg in cmd if arg]
    
    try:
        result = subprocess.run(cmd, cwd=app_dir, check=True)
        
        exe_path = dist_dir / "ASTRA AI.exe"
        
        if exe_path.exists():
            print(f"\n✅ Build erfolgreich!")
            print(f"📦 EXE erstellt: {exe_path}")
            print(f"📊 Größe: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
            return True
        else:
            print("❌ Build fehlgeschlagen - EXE nicht gefunden")
            return False
    
    except subprocess.CalledProcessError as e:
        print(f"❌ Build fehlgeschlagen: {e}")
        return False


if __name__ == "__main__":
    success = build_exe()
    sys.exit(0 if success else 1)
