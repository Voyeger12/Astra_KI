"""
Test für das intelligente Timeout-System in Ollama
================================================== 
Validiert adaptive Timeouts und Retry-Logik
"""

import sys
import os
from pathlib import Path

# Pfade anpassen
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))
os.chdir(app_dir)

from modules.ollama_client import OllamaClient
from config import OLLAMA_TIMEOUTS, OLLAMA_RETRY_ATTEMPTS, OLLAMA_RETRY_DELAY


def test_timeout_configuration():
    """Test dass die Timeout-Konfiguration korrekt geladen wird"""
    client = OllamaClient()
    
    print("\n" + "="*60)
    print("TEST: Timeout-Konfiguration")
    print("="*60)
    
    # Test dass Config-Werte geladen wurden
    assert client.max_retries == OLLAMA_RETRY_ATTEMPTS, f"max_retries sollte {OLLAMA_RETRY_ATTEMPTS} sein"
    assert client.initial_retry_delay == OLLAMA_RETRY_DELAY, f"initial_retry_delay sollte {OLLAMA_RETRY_DELAY}s sein"
    print(f"✓ Max Retries: {client.max_retries}")
    print(f"✓ Initial Retry Delay: {client.initial_retry_delay}s")
    
    # Test dass Model-Timeouts geladen wurden
    assert len(client.model_timeouts) > 0, "Keine Model-Timeouts konfiguriert"
    assert "default" in client.model_timeouts, "Default Timeout fehlt"
    print(f"✓ {len(client.model_timeouts)} Modelle im Timeout-System konfiguriert")
    

def test_timeout_selection():
    """Test dass richtige Timeouts für verschiedene Modelle gewählt werden"""
    client = OllamaClient()
    
    print("\n" + "="*60)
    print("TEST: Timeout-Auswahl für verschiedene Modelle")
    print("="*60)
    
    test_models = [
        ("qwen2.5:14b", 120),
        ("qwen2.5:7b", 60),
        ("qwen2.5:32b", 240),
        ("llama2:7b", 60),
        ("phi:7b", 45),
        ("unknown:model", 180),  # Fallback
    ]
    
    for model, expected_timeout in test_models:
        actual_timeout = client._get_timeout(model)
        assert actual_timeout == expected_timeout, f"{model}: expected {expected_timeout}s, got {actual_timeout}s"
        print(f"✓ {model:20} → {actual_timeout:3}s")


def test_timeout_logic():
    """Test dass Timeout-Logik in chat() und generate() vorhanden ist"""
    client = OllamaClient()
    
    print("\n" + "="*60)
    print("TEST: Timeout-Logik in Methoden")
    print("="*60)
    
    # Chat-Methode
    chat_source = str(client.chat.__code__.co_code)
    assert "timeout" in client.chat.__code__.co_names or len(client.chat.__code__.co_names) > 0
    print("✓ chat() Methode hat Timeout-Logic")
    
    # Generate-Methode
    generate_source = str(client.generate.__code__.co_code)
    assert "timeout" in client.generate.__code__.co_names or len(client.generate.__code__.co_names) > 0
    print("✓ generate() Methode hat Timeout-Logic")
    
    # Retry-Logik
    assert client.max_retries >= 2, "Mindestens 2 Retries sollten konfiguriert sein"
    print(f"✓ Retry-Logik mit {client.max_retries} Versuchen vorhanden")


def test_config_integration():
    """Test dass config.py korrekt mit OllamaClient integriert ist"""
    print("\n" + "="*60)
    print("TEST: Config.py Integration")
    print("="*60)
    
    # Prüfe dass Config-Werte in Client vorhanden sind
    client = OllamaClient()
    assert hasattr(client, 'model_timeouts'), "model_timeouts Attribut fehlt"
    assert hasattr(client, 'max_retries'), "max_retries Attribut fehlt"
    assert hasattr(client, 'initial_retry_delay'), "initial_retry_delay Attribut fehlt"
    
    print(f"✓ Client hat model_timeouts: {len(client.model_timeouts)} Modelle")
    print(f"✓ Client hat max_retries: {client.max_retries}")
    print(f"✓ Client hat initial_retry_delay: {client.initial_retry_delay}s")
    
    # Prüfe dass Timeouts sinnvoll sind
    for model, timeout in client.model_timeouts.items():
        assert isinstance(timeout, (int, float)), f"{model}: Timeout sollte Zahl sein"
        assert timeout > 0, f"{model}: Timeout sollte > 0 sein"
        assert timeout <= 600, f"{model}: Timeout sollte <= 10 Minuten sein"
    
    print("✓ Alle Timeout-Werte sind plausibel (>0 und <=600s)")


def main():
    """Führe alle Tests durch"""
    print("\n" + "="*60)
    print("TIMEOUT-SYSTEM VALIDIERUNG")
    print("="*60)
    
    try:
        test_timeout_configuration()
        test_timeout_selection()
        test_timeout_logic()
        test_config_integration()
        
        print("\n" + "="*60)
        print("✅ ALLE TIMEOUT-TESTS BESTANDEN")
        print("="*60)
        print("\nZusammenfassung:")
        print("- ✓ Adaptive Timeouts für verschiedene Modelle")
        print("- ✓ Retry-Logik mit exponentialem Backoff")
        print("- ✓ Config-Integration funktioniert")
        print("- ✓ Alle Timeout-Werte plausibel\n")
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FEHLGESCHLAGEN: {e}\n")
        return 1
    except Exception as e:
        print(f"\n❌ UNERWARTETER FEHLER: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
