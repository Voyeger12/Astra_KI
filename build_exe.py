"""
ASTRA AI - Build Script
=======================
Kompiliert die Anwendung zu einer EXE mit PyInstaller.
Enthält alle Module, Assets und Abhängigkeiten.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def build_exe():
    """Baut die EXE mit PyInstaller"""
    
    print("=" * 60)
    print("ASTRA AI - PyInstaller Build v2.1")
    print("=" * 60)
    
    # Prüfe PyInstaller
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__} gefunden")
    except ImportError:
        print("❌ PyInstaller nicht installiert!")
        print("Installieren Sie: pip install pyinstaller")
        return False
    
    # Health-Check vor Build
    print("\n🩺 Führe Health-Check durch...")
    try:
        from modules.utils import HealthChecker
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            health_ok = HealthChecker.check(verbose=False)
        if not health_ok:
            print("⚠️  Health-Check hat Warnungen — Build wird fortgesetzt")
        else:
            print("✅ Health-Check bestanden")
    except Exception as e:
        print(f"⚠️  Health-Check übersprungen: {e}")
    
    # Verzeichnisse
    app_dir = Path(__file__).parent
    build_dir = app_dir / "build"
    dist_dir = app_dir / "dist"
    
    # Cleanup alte Builds
    print("\n🧹 Räume auf...")
    for directory in [build_dir, dist_dir]:
        if directory.exists() and directory.is_dir():
            shutil.rmtree(directory)
    spec_file = app_dir / "ASTRA AI.spec"
    if spec_file.exists():
        spec_file.unlink()
    
    # Data-Files sammeln (werden in EXE eingebettet)
    data_files = []
    data_mappings = [
        # persona.py ist Teil von config/
        ("config.py",                "."),
        ("assets",                   "assets"),
        ("config/settings.json",     "config"),
    ]
    for src, dest in data_mappings:
        src_path = app_dir / src
        if src_path.exists():
            sep = ";" if sys.platform == "win32" else ":"
            data_files.append(f"--add-data={src_path}{sep}{dest}")
            print(f"  📦 {src} → {dest}/")
        else:
            print(f"  ⚠️  {src} nicht gefunden (übersprungen)")
    
    # PyInstaller-Befehl
    print("\n🔨 Baue Anwendung...")
    cmd = [
        "pyinstaller",
        "--name=ASTRA AI",
        "--onefile",
        "-w",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        
        # ── Icon ──
        *(["--icon=ASTRA.ico"] if (app_dir / "ASTRA.ico").exists() else []),
        
        # ── Data-Files ──
        *data_files,
        
        # ── PyQt6 ──
        "--hidden-import=PyQt6.QtPrintSupport",
        "--hidden-import=PyQt6.QtSvg",
        "--hidden-import=PyQt6.QtSvgWidgets",
        "--collect-all=PyQt6",
        
        # ── Code-Highlighting (Pygments) ──
        "--hidden-import=pygments",
        "--hidden-import=pygments.lexers",
        "--hidden-import=pygments.formatters",
        "--hidden-import=pygments.styles",
        "--hidden-import=pygments.styles.monokai",
        "--collect-submodules=pygments.lexers",
        
        # ── Internet-Suche ──
        "--hidden-import=ddgs",
        "--hidden-import=requests",
        "--collect-all=ddgs",
        "--collect-all=requests",
        
        # ── Datenbank & System ──
        "--hidden-import=sqlite3",
        "--hidden-import=logging",
        "--hidden-import=json",
        "--hidden-import=urllib.request",
        
        # ── ASTRA Module (explizit) ──
        "--hidden-import=modules",
        "--hidden-import=modules.database",
        "--hidden-import=modules.memory",
        "--hidden-import=modules.ollama_client",
        "--hidden-import=modules.logger",
        "--hidden-import=modules.utils",
        "--hidden-import=modules.gpu_detect",
        "--hidden-import=modules.ui",
        "--hidden-import=modules.ui.main_window",
        "--hidden-import=modules.ui.chat_display",
        "--hidden-import=modules.ui.rich_formatter",
        "--hidden-import=modules.ui.settings_dialog",
        "--hidden-import=modules.ui.settings_manager",
        "--hidden-import=modules.ui.styles",
        "--hidden-import=modules.ui.colors",
        "--hidden-import=modules.ui.workers",
        
        # ── Fallback für altes Such-Paket ──
        "--hidden-import=duckduckgo_search",
        
        # ── Einstiegspunkt ──
        str(app_dir / "main.py")
    ]
    
    try:
        result = subprocess.run(cmd, cwd=app_dir, check=True)
        
        exe_path = dist_dir / "ASTRA AI.exe"
        
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / 1024 / 1024
            print(f"\n{'=' * 60}")
            print(f"✅ Build erfolgreich!")
            print(f"📦 EXE: {exe_path}")
            print(f"📊 Größe: {size_mb:.1f} MB")
            print(f"{'=' * 60}")
            return True
        else:
            print("❌ Build fehlgeschlagen — EXE nicht gefunden")
            return False
    
    except subprocess.CalledProcessError as e:
        print(f"❌ Build fehlgeschlagen: {e}")
        return False


if __name__ == "__main__":
    success = build_exe()
    sys.exit(0 if success else 1)
