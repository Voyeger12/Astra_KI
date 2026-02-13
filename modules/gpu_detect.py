"""
ASTRA AI - GPU Erkennung & Konfiguration
=========================================
Erkennt automatisch die verfügbare GPU und konfiguriert
Ollama für optimale Performance (CUDA / ROCm / Vulkan / CPU).
"""

import os
import subprocess
import re
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class GPUInfo:
    """Informationen über die erkannte GPU"""
    vendor: str          # "nvidia", "amd", "intel", "none"
    name: str            # z.B. "NVIDIA GeForce RTX 4070"
    vram_mb: int         # VRAM in MB (0 wenn unbekannt)
    backend: str         # "cuda", "rocm", "vulkan", "cpu"
    driver_info: str     # Treiberversion
    
    @property
    def vram_gb(self) -> float:
        return round(self.vram_mb / 1024, 1) if self.vram_mb > 0 else 0
    
    def summary(self) -> str:
        """Kurze Zusammenfassung für Logging"""
        vram = f" ({self.vram_gb}GB VRAM)" if self.vram_mb > 0 else ""
        return f"{self.name}{vram} → Backend: {self.backend.upper()}"


# AMD GPUs die von ROCm auf Windows unterstützt werden (Stand 2025/2026)
ROCM_WINDOWS_SUPPORTED = [
    "7900 XTX", "7900 XT", "7900 GRE", "7800 XT", "7700 XT",
    "7600 XT", "7600",
    "6950 XT", "6900 XTX", "6900 XT", "6800 XT", "6800",
    "W7900", "W7800", "W7700", "W7600", "W7500",
    "W6900X", "W6800X", "W6800", "V620",
]

# AMD GPUs die NUR Vulkan unterstützen (RDNA 4, ältere, etc.)
# Alles was nicht in ROCM_WINDOWS_SUPPORTED ist, bekommt Vulkan
AMD_VULKAN_KEYWORDS = [
    "9070", "9060",  # RDNA 4
    "RX 5",          # RDNA 1
    "Vega",
]


def _run_command(cmd: str, timeout: int = 10) -> Optional[str]:
    """Führt einen Befehl aus und gibt stdout zurück"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def _detect_nvidia() -> Optional[GPUInfo]:
    """Erkennt NVIDIA GPUs via nvidia-smi"""
    output = _run_command('nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits')
    if not output:
        return None
    
    try:
        parts = output.split('\n')[0].split(',')
        name = parts[0].strip()
        vram = int(float(parts[1].strip())) if len(parts) > 1 else 0
        driver = parts[2].strip() if len(parts) > 2 else "unbekannt"
        
        return GPUInfo(
            vendor="nvidia",
            name=name,
            vram_mb=vram,
            backend="cuda",
            driver_info=f"Driver {driver}"
        )
    except Exception:
        return None


def _detect_amd_or_intel_wmic() -> Optional[GPUInfo]:
    """Erkennt AMD/Intel GPUs via Windows WMI (PowerShell)"""
    # Nutze PowerShell für zuverlässige GPU-Erkennung
    ps_cmd = (
        'powershell -NoProfile -Command "'
        'Get-CimInstance Win32_VideoController | '
        'Select-Object Name, AdapterRAM, DriverVersion | '
        'ConvertTo-Json -Compress'
        '"'
    )
    output = _run_command(ps_cmd, timeout=15)
    if not output:
        return None
    
    try:
        import json
        data = json.loads(output)
        
        # Kann einzelnes Objekt oder Liste sein
        if isinstance(data, dict):
            data = [data]
        
        # Suche nach dedizierter GPU (nicht integrierte)
        # Priorisiere: AMD dGPU > NVIDIA > Intel dGPU > Intel iGPU
        best_gpu = None
        for gpu in data:
            name = gpu.get("Name", "")
            vram_bytes = gpu.get("AdapterRAM", 0) or 0
            driver = gpu.get("DriverVersion", "unbekannt")
            
            # Überspringe Microsoft Basic Display Adapter
            if "Microsoft" in name or "Basic" in name:
                continue
            
            is_amd = any(k in name.upper() for k in ["AMD", "RADEON", "ATI"])
            is_nvidia = "NVIDIA" in name.upper()
            is_intel = "INTEL" in name.upper()
            
            # VRAM: WMI gibt manchmal 0 oder 4GB-Cap zurück
            vram_mb = int(vram_bytes / 1024 / 1024) if vram_bytes > 0 else 0
            # WMI limitiert AdapterRAM auf 4GB (uint32), echte VRAM könnte höher sein
            if vram_mb > 0 and vram_mb <= 4096 and (is_amd or is_nvidia):
                vram_mb = 0  # Unzuverlässig, lieber nicht anzeigen
            
            gpu_info = {
                "name": name, "vram_mb": vram_mb, "driver": driver,
                "is_amd": is_amd, "is_nvidia": is_nvidia, "is_intel": is_intel
            }
            
            # Priorisierung: dedizierte GPU bevorzugen
            if is_amd and not best_gpu:
                best_gpu = gpu_info
            elif is_amd and best_gpu and not best_gpu["is_amd"]:
                best_gpu = gpu_info
            elif is_nvidia and not best_gpu:
                best_gpu = gpu_info
            elif not best_gpu:
                best_gpu = gpu_info
        
        if not best_gpu:
            return None
        
        # Backend bestimmen
        if best_gpu["is_nvidia"]:
            return GPUInfo(
                vendor="nvidia", name=best_gpu["name"],
                vram_mb=best_gpu["vram_mb"], backend="cuda",
                driver_info=f"Driver {best_gpu['driver']}"
            )
        
        if best_gpu["is_amd"]:
            backend = _determine_amd_backend(best_gpu["name"])
            return GPUInfo(
                vendor="amd", name=best_gpu["name"],
                vram_mb=best_gpu["vram_mb"], backend=backend,
                driver_info=f"Driver {best_gpu['driver']}"
            )
        
        if best_gpu["is_intel"]:
            return GPUInfo(
                vendor="intel", name=best_gpu["name"],
                vram_mb=best_gpu["vram_mb"], backend="vulkan",
                driver_info=f"Driver {best_gpu['driver']}"
            )
        
    except Exception:
        pass
    
    return None


def _determine_amd_backend(gpu_name: str) -> str:
    """Bestimmt ob eine AMD GPU ROCm oder Vulkan nutzen soll"""
    name_upper = gpu_name.upper()
    
    # Prüfe ob die GPU explizit Vulkan braucht (RDNA 4 etc.)
    for keyword in AMD_VULKAN_KEYWORDS:
        if keyword.upper() in name_upper:
            return "vulkan"
    
    # Prüfe ob die GPU von ROCm auf Windows unterstützt wird
    for supported in ROCM_WINDOWS_SUPPORTED:
        if supported.upper() in name_upper:
            return "rocm"
    
    # Fallback: Vulkan ist sicherer (funktioniert mit mehr GPUs)
    return "vulkan"


def detect_gpu() -> GPUInfo:
    """
    Erkennt die beste verfügbare GPU im System.
    
    Prüf-Reihenfolge:
    1. NVIDIA (via nvidia-smi) → CUDA
    2. AMD/Intel (via WMI) → ROCm oder Vulkan
    3. Fallback → CPU
    """
    # 1. Versuche NVIDIA
    nvidia = _detect_nvidia()
    if nvidia:
        return nvidia
    
    # 2. Versuche AMD/Intel via Windows WMI
    wmi_gpu = _detect_amd_or_intel_wmic()
    if wmi_gpu:
        return wmi_gpu
    
    # 3. Fallback: Keine GPU erkannt
    return GPUInfo(
        vendor="none",
        name="Keine dedizierte GPU erkannt",
        vram_mb=0,
        backend="cpu",
        driver_info=""
    )


def configure_ollama_gpu(gpu: GPUInfo = None) -> GPUInfo:
    """
    Erkennt die GPU und setzt die passenden Umgebungsvariablen für Ollama.
    
    Returns:
        GPUInfo mit den Details der erkannten GPU
    """
    if gpu is None:
        gpu = detect_gpu()
    
    if gpu.backend == "vulkan":
        os.environ["OLLAMA_VULKAN"] = "1"
    elif gpu.backend == "cuda":
        # CUDA ist Standard bei NVIDIA, keine spezielle Env-Variable nötig
        # Stelle sicher, dass Vulkan nicht aktiv ist
        os.environ.pop("OLLAMA_VULKAN", None)
    elif gpu.backend == "rocm":
        # ROCm ist Standard bei unterstützten AMD GPUs
        os.environ.pop("OLLAMA_VULKAN", None)
    else:
        # CPU-Fallback
        os.environ.pop("OLLAMA_VULKAN", None)
    
    return gpu


if __name__ == "__main__":
    # Standalone-Test
    print("🔍 GPU-Erkennung...")
    gpu = detect_gpu()
    print(f"\n✅ {gpu.summary()}")
    print(f"   Vendor:  {gpu.vendor}")
    print(f"   Backend: {gpu.backend}")
    print(f"   Driver:  {gpu.driver_info}")
    
    print(f"\n⚙️  Konfiguriere Ollama...")
    configure_ollama_gpu(gpu)
    
    vulkan = os.environ.get("OLLAMA_VULKAN", "0")
    print(f"   OLLAMA_VULKAN = {vulkan}")
    print(f"\n{'='*50}")
    print(f"   Empfehlung: ollama serve  →  {gpu.backend.upper()} wird genutzt")
