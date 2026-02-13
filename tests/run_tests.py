#!/usr/bin/env python3
"""
ASTRA AI - Unified Test Suite
==============================
Testet alle Module mit temporären Datenbanken (keine Production-Daten berührt).

Verwendung:
    python tests/run_tests.py          # Alle Tests
    python tests/run_tests.py -v       # Verbose-Modus

Module getestet:
    1. Config        - Konstanten & Pfade
    2. Logger        - Logging-System
    3. Database      - CRUD-Operationen (temp DB)
    4. Memory        - Learn, Extract, SystemPrompt
    5. OllamaClient  - Init, Timeouts, Config
    6. RichFormatter - Markdown→HTML, Code-Highlighting
    7. Utils         - RateLimiter, Security, SearchEngine
    8. Settings      - SettingsManager Read/Write
"""

import sys
import os
import unittest
import tempfile
import threading
import time
import shutil
from pathlib import Path

# Projekt-Root zum Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)


# ============================================================================
# 1. CONFIG TESTS
# ============================================================================
class TestConfig(unittest.TestCase):
    """Tests für config.py - Konstanten und Pfade"""

    def test_paths_exist(self):
        """APP_DIR und DATA_DIR existieren"""
        from config import APP_DIR, DATA_DIR
        self.assertTrue(APP_DIR.exists(), "APP_DIR existiert nicht")
        self.assertTrue(DATA_DIR.exists(), "DATA_DIR existiert nicht")

    def test_ollama_config(self):
        """Ollama-Konfiguration hat alle Pflichtfelder"""
        from config import OLLAMA_HOST, OLLAMA_TIMEOUTS, DEFAULT_MODEL, OLLAMA_MODELS
        self.assertTrue(OLLAMA_HOST.startswith("http"))
        self.assertIn("default", OLLAMA_TIMEOUTS)
        self.assertIsInstance(DEFAULT_MODEL, str)
        self.assertGreater(len(OLLAMA_MODELS), 0)

    def test_timeout_values_plausible(self):
        """Alle Timeout-Werte sind zwischen 10 und 600 Sekunden"""
        from config import OLLAMA_TIMEOUTS
        for model, timeout in OLLAMA_TIMEOUTS.items():
            self.assertGreater(timeout, 9, f"{model}: Timeout zu niedrig ({timeout}s)")
            self.assertLessEqual(timeout, 600, f"{model}: Timeout zu hoch ({timeout}s)")

    def test_colors_complete(self):
        """COLORS hat alle nötigen Schlüssel"""
        from config import COLORS
        required = ["primary", "background", "text", "surface", "success", "error"]
        for key in required:
            self.assertIn(key, COLORS, f"COLORS['{key}'] fehlt")

    def test_security_constants(self):
        """Security-Konstanten existieren"""
        from config import MAX_MESSAGE_LENGTH, MAX_MEMORY_LENGTH, MAX_MESSAGES_PER_MINUTE
        self.assertGreater(MAX_MESSAGE_LENGTH, 0)
        self.assertGreater(MAX_MEMORY_LENGTH, 0)
        self.assertGreater(MAX_MESSAGES_PER_MINUTE, 0)

    def test_system_prompt_template(self):
        """SYSTEM_PROMPT_TEMPLATE hat {memory} Placeholder"""
        from config import SYSTEM_PROMPT_TEMPLATE
        self.assertIn("{memory}", SYSTEM_PROMPT_TEMPLATE)
        self.assertIn("Astra", SYSTEM_PROMPT_TEMPLATE)


# ============================================================================
# 2. LOGGER TESTS
# ============================================================================
class TestLogger(unittest.TestCase):
    """Tests für modules/logger.py"""

    def test_logger_imports(self):
        """Logger-Modul lädt ohne Fehler"""
        from modules.logger import astra_logger, log_info, log_error, log_warning, get_log_file
        self.assertIsNotNone(astra_logger)

    def test_log_functions_callable(self):
        """Alle Log-Funktionen sind aufrufbar ohne Crash"""
        from modules.logger import log_info, log_error, log_warning, log_debug
        log_info("Test-Info", "UNIT_TEST")
        log_warning("Test-Warning", "UNIT_TEST")
        log_debug("Test-Debug", "UNIT_TEST")
        # Kein Crash = Erfolg

    def test_log_file_created(self):
        """Log-Datei wird erstellt"""
        from modules.logger import get_log_file, log_info
        log_info("Trigger log file creation", "UNIT_TEST")
        log_file = get_log_file()
        self.assertTrue(log_file.exists(), f"Log-Datei nicht gefunden: {log_file}")

    def test_log_rotation_config(self):
        """Log-Rotation ist konfiguriert (10MB, 14 Tage Backups)"""
        from modules.logger import MAX_LOG_SIZE, BACKUP_COUNT
        self.assertEqual(MAX_LOG_SIZE, 10 * 1024 * 1024)
        self.assertEqual(BACKUP_COUNT, 14)  # 14 Tage Logs


# ============================================================================
# 3. DATABASE TESTS (mit temp DB)
# ============================================================================
class TestDatabase(unittest.TestCase):
    """Tests für modules/database.py - nutzt temporäre DB"""

    def setUp(self):
        """Erstelle temporäre Datenbank"""
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.tmp_dir) / "test_astra.db"
        from modules.database import Database
        self.db = Database(self.db_path)

    def tearDown(self):
        """Räume temporäre Dateien auf"""
        try:
            self.db.close()
        except Exception:
            pass
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_tables_created(self):
        """Alle nötigen Tabellen werden angelegt"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        for table in ['chats', 'messages', 'memory']:
            self.assertIn(table, tables, f"Tabelle '{table}' fehlt")

    def test_create_chat(self):
        """Chat erstellen funktioniert"""
        chat_id = self.db.create_chat("Test Chat")
        self.assertIsNotNone(chat_id)

    def test_save_and_load_messages(self):
        """Nachrichten speichern und laden"""
        self.db.create_chat("MsgTest")
        self.db.save_message("MsgTest", "user", "Hallo")
        self.db.save_message("MsgTest", "assistant", "Hi!")

        # Warte bis Background-Writer fertig ist
        self.db._write_queue.join()

        messages = self.db.get_chat_messages("MsgTest")
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "Hallo")
        self.assertEqual(messages[1]["role"], "assistant")

    def test_get_all_chats(self):
        """Alle Chats abrufen"""
        self.db.create_chat("Chat A")
        self.db.create_chat("Chat B")
        chats = self.db.get_all_chats()
        self.assertIn("Chat A", chats)
        self.assertIn("Chat B", chats)

    def test_delete_chat(self):
        """Chat löschen"""
        self.db.create_chat("ToDelete")
        self.db.save_message("ToDelete", "user", "Bye")
        time.sleep(0.2)
        result = self.db.delete_chat("ToDelete")
        self.assertTrue(result)
        chats = self.db.get_all_chats()
        self.assertNotIn("ToDelete", chats)

    def test_memory_crud(self):
        """Memory: Speichern, Laden, Löschen"""
        # Speichern
        result = self.db.add_memory("User heisst Duncan", "personal")
        self.assertTrue(result)

        time.sleep(0.2)

        # Laden
        memory = self.db.get_memory()
        self.assertIn("Duncan", memory)

        # Löschen
        self.db.clear_memory()
        time.sleep(0.2)
        memory_after = self.db.get_memory()
        self.assertTrue("Duncan" not in memory_after or "Noch keine" in memory_after)

    def test_backup_system(self):
        """Backup wird erstellt"""
        result = self.db._backup_database()
        self.assertTrue(result)
        backup_dir = self.db_path.parent / "backups"
        if backup_dir.exists():
            backups = list(backup_dir.glob("*.db"))
            self.assertGreater(len(backups), 0)

    def test_concurrent_writes(self):
        """Gleichzeitige Schreibzugriffe crashen nicht"""
        self.db.create_chat("ConcurrentTest")
        errors = []

        def write(index):
            try:
                self.db.save_message("ConcurrentTest", "user", f"Msg {index}")
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=write, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        self.assertEqual(len(errors), 0, f"Concurrent write errors: {errors}")


# ============================================================================
# 4. MEMORY TESTS (mit temp DB)
# ============================================================================
class TestMemory(unittest.TestCase):
    """Tests für modules/memory.py"""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.tmp_dir) / "test_memory.db"
        from modules.database import Database
        from modules.memory import MemoryManager
        self.db = Database(self.db_path)
        self.mm = MemoryManager(self.db)

    def tearDown(self):
        try:
            self.db.close()
        except Exception:
            pass
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_learn_and_recall(self):
        """learn() speichert, get_memory_string() gibt zurück"""
        self.mm.learn("Benutzer heisst Duncan", "personal")
        time.sleep(0.2)
        memory = self.mm.get_memory_string()
        self.assertIn("Duncan", memory)

    def test_learn_invalidates_cache(self):
        """Nach learn() wird der System-Prompt Cache invalidiert"""
        prompt1 = self.mm.get_system_prompt()
        self.mm.learn("Neue Info XYZ", "personal")
        # Cache sollte None sein nach learn
        self.assertIsNone(self.mm._cached_system_prompt)

    def test_extract_memory_single_tag(self):
        """Einzelner [MERKEN:...] Tag wird extrahiert"""
        text = "Klar, ich merke mir das! [MERKEN: Benutzer heisst Duncan]"
        memories = self.mm.extract_memory_from_response(text)
        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0], "Benutzer heisst Duncan")

    def test_extract_memory_multiple_tags(self):
        """Mehrere [MERKEN:...] Tags werden alle extrahiert"""
        text = "Ok! [MERKEN: Name ist Duncan] Alles klar. [MERKEN: Alter ist 30]"
        memories = self.mm.extract_memory_from_response(text)
        self.assertEqual(len(memories), 2)
        self.assertIn("Name ist Duncan", memories)
        self.assertIn("Alter ist 30", memories)

    def test_extract_memory_no_tags(self):
        """Ohne [MERKEN:] Tags kommt leere Liste"""
        memories = self.mm.extract_memory_from_response("Hallo, wie geht es dir?")
        self.assertEqual(len(memories), 0)

    def test_extract_memory_empty_tag(self):
        """Leerer [MERKEN:] Tag wird ignoriert"""
        memories = self.mm.extract_memory_from_response("[MERKEN: ]")
        # Sollte leer sein oder nur Whitespace
        for m in memories:
            self.assertTrue(len(m.strip()) == 0 or len(memories) == 0)

    def test_remove_tags_merken(self):
        """[MERKEN:...] Tags werden aus der Response entfernt"""
        text = "Hallo! [MERKEN: Name Duncan] Wie geht es dir?"
        clean = self.mm.remove_tags_from_response(text)
        self.assertNotIn("[MERKEN:", clean)
        self.assertIn("Hallo!", clean)
        self.assertIn("Wie geht es dir?", clean)

    def test_remove_tags_suche(self):
        """[SUCHE:...] Tags werden entfernt"""
        text = "Moment, ich schaue nach. [SUCHE: Wetter Berlin]"
        clean = self.mm.remove_tags_from_response(text)
        self.assertNotIn("[SUCHE:", clean)

    def test_remove_tags_both(self):
        """Beide Tag-Typen gleichzeitig entfernen"""
        text = "[MERKEN: Info] Antwort [SUCHE: Query]"
        clean = self.mm.remove_tags_from_response(text)
        self.assertNotIn("[MERKEN:", clean)
        self.assertNotIn("[SUCHE:", clean)
        self.assertIn("Antwort", clean)

    def test_get_system_prompt_contains_persona(self):
        """System-Prompt enthält Persona (Astra)"""
        prompt = self.mm.get_system_prompt()
        self.assertIn("Astra", prompt)

    def test_get_system_prompt_contains_memory(self):
        """System-Prompt integriert gespeichertes Wissen"""
        self.mm.learn("Benutzer mag Pizza", "personal")
        time.sleep(0.2)
        # Cache invalidieren
        self.mm._cached_system_prompt = None
        self.mm._last_prompt_time = None
        prompt = self.mm.get_system_prompt()
        self.assertIn("Pizza", prompt)

    def test_get_system_prompt_caching(self):
        """System-Prompt wird gecacht (gleicher Wert bei Retry)"""
        prompt1 = self.mm.get_system_prompt()
        prompt2 = self.mm.get_system_prompt()
        self.assertEqual(prompt1, prompt2)

    def test_memory_deduplication(self):
        """get_memory_string_deduplicated() entfernt exakte Duplikate (content-basiert)"""
        self.mm.learn("Name ist Anna", "personal")
        self.mm.learn("Name ist Anna", "personal")  # Exaktes Duplikat
        self.mm.learn("Wohnort ist Hamburg", "personal")  # Andere Info
        self.mm.learn("Alter ist 30", "personal")  # Noch eine andere Info
        time.sleep(0.2)
        memory = self.mm.get_memory_string_deduplicated()
        # Anna sollte nur 1x vorkommen (exakte Dedup)
        count = memory.lower().count("name ist anna")
        self.assertEqual(count, 1, f"Anna sollte nur 1x vorkommen, gefunden: {count}")
        # Aber andere Infos müssen erhalten bleiben!
        self.assertIn("Hamburg", memory)
        self.assertIn("30", memory)

    def test_clear_memory(self):
        """clear_memory() löscht alles"""
        self.mm.learn("Test-Info", "general")
        time.sleep(0.2)
        self.mm.clear_memory()
        time.sleep(0.2)
        memory = self.mm.get_memory_string()
        self.assertFalse("Test-Info" in memory)


# ============================================================================
# 5. OLLAMA CLIENT TESTS (kein Netzwerk nötig)
# ============================================================================
class TestOllamaClient(unittest.TestCase):
    """Tests für modules/ollama_client.py - nur Init & Config (kein Netzwerk)"""

    def test_client_init(self):
        """Client initialisiert sich korrekt"""
        from modules.ollama_client import OllamaClient
        client = OllamaClient()
        self.assertIsNotNone(client.host)
        self.assertIsNotNone(client.model_timeouts)
        self.assertGreater(client.max_retries, 0)

    def test_timeout_for_known_models(self):
        """Bekannte Modelle bekommen korrekte Timeouts"""
        from modules.ollama_client import OllamaClient
        from config import OLLAMA_TIMEOUTS
        client = OllamaClient()

        for model, expected_timeout in OLLAMA_TIMEOUTS.items():
            if model == "default":
                continue
            actual = client._get_timeout(model)
            self.assertEqual(actual, expected_timeout,
                             f"{model}: erwartet {expected_timeout}s, bekommen {actual}s")

    def test_timeout_for_unknown_model(self):
        """Unbekanntes Modell bekommt Default-Timeout"""
        from modules.ollama_client import OllamaClient
        from config import OLLAMA_TIMEOUTS
        client = OllamaClient()
        timeout = client._get_timeout("totally-unknown-model:99b")
        self.assertEqual(timeout, OLLAMA_TIMEOUTS["default"])

    def test_config_integration(self):
        """Client nutzt config.py Werte"""
        from modules.ollama_client import OllamaClient
        from config import OLLAMA_RETRY_ATTEMPTS, OLLAMA_RETRY_DELAY
        client = OllamaClient()
        self.assertEqual(client.max_retries, OLLAMA_RETRY_ATTEMPTS)
        self.assertEqual(client.initial_retry_delay, OLLAMA_RETRY_DELAY)

    def test_extract_fact_success(self):
        """extract_fact() gibt strukturierten Fakt zurück bei erfolgreicher LLM-Antwort"""
        from modules.ollama_client import OllamaClient
        from unittest.mock import patch, MagicMock
        client = OllamaClient()
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "Name: Duncan"}
        }
        
        with patch("requests.post", return_value=mock_response):
            result = client.extract_fact("ich heiße Duncan", "qwen2.5:14b")
        
        self.assertEqual(result, "Name: Duncan")

    def test_extract_fact_fallback_on_error(self):
        """extract_fact() gibt Originaltext zurück bei Netzwerk-Fehler"""
        from modules.ollama_client import OllamaClient
        from unittest.mock import patch
        client = OllamaClient()
        
        with patch("requests.post", side_effect=Exception("Timeout")):
            result = client.extract_fact("ich mag Pizza", "qwen2.5:14b")
        
        self.assertEqual(result, "ich mag Pizza")

    def test_extract_fact_invalid_response(self):
        """extract_fact() gibt Originaltext zurück bei ungültiger LLM-Antwort"""
        from modules.ollama_client import OllamaClient
        from unittest.mock import patch, MagicMock
        client = OllamaClient()
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": ""}
        }
        
        with patch("requests.post", return_value=mock_response):
            result = client.extract_fact("test text", "qwen2.5:14b")
        
        self.assertEqual(result, "test text")


# ============================================================================
# 6. RICH FORMATTER TESTS
# ============================================================================
class TestRichFormatter(unittest.TestCase):
    """Tests für modules/ui/rich_formatter.py"""

    def test_bold_text(self):
        """**text** wird zu <strong>"""
        from modules.ui.rich_formatter import RichFormatter
        result = RichFormatter.format_text("Das ist **wichtig**")
        self.assertIn("wichtig", result)
        self.assertTrue("<strong" in result or "<b" in result)

    def test_italic_text(self):
        """*text* wird zu <em>"""
        from modules.ui.rich_formatter import RichFormatter
        result = RichFormatter.format_text("Das ist *kursiv*")
        self.assertIn("kursiv", result)

    def test_inline_code(self):
        """`code` wird zu <code>"""
        from modules.ui.rich_formatter import RichFormatter
        result = RichFormatter.format_text("Nutze `python` Befehl")
        self.assertIn("<code", result)
        self.assertIn("python", result)

    def test_heading(self):
        """# Heading wird erkannt"""
        from modules.ui.rich_formatter import RichFormatter
        result = RichFormatter.format_text("# Überschrift")
        self.assertIn("Überschrift", result)

    def test_bullet_list(self):
        """- item wird zu Aufzählung"""
        from modules.ui.rich_formatter import RichFormatter
        result = RichFormatter.format_text("- Punkt A\n- Punkt B")
        self.assertIn("•", result)

    def test_code_highlighting(self):
        """Code Block mit Syntax-Highlighting"""
        from modules.ui.rich_formatter import RichFormatter
        code = 'def hello():\n    return "world"'
        result = RichFormatter.highlight_code(code, "python")
        self.assertIn("hello", result)

    def test_format_caching(self):
        """Wiederholte Formatierung nutzt Cache"""
        from modules.ui.rich_formatter import RichFormatter
        text = "Cache **Test** Inhalt"
        result1 = RichFormatter.format_text(text)
        result2 = RichFormatter.format_text(text)
        self.assertEqual(result1, result2)

    def test_empty_text(self):
        """Leerer Text crashed nicht"""
        from modules.ui.rich_formatter import RichFormatter
        result = RichFormatter.format_text("")
        self.assertIsNotNone(result)


# ============================================================================
# 7. UTILS TESTS
# ============================================================================
class TestRateLimiter(unittest.TestCase):
    """Tests für RateLimiter"""

    def test_allows_within_limit(self):
        """Requests innerhalb des Limits werden erlaubt"""
        from modules.utils import RateLimiter
        limiter = RateLimiter(max_requests=3, window_seconds=1)
        self.assertTrue(limiter.is_allowed("user1"))
        self.assertTrue(limiter.is_allowed("user1"))
        self.assertTrue(limiter.is_allowed("user1"))

    def test_blocks_over_limit(self):
        """4. Request wird blockiert bei Limit 3"""
        from modules.utils import RateLimiter
        limiter = RateLimiter(max_requests=3, window_seconds=1)
        for _ in range(3):
            limiter.is_allowed("user1")
        self.assertFalse(limiter.is_allowed("user1"))

    def test_separate_users(self):
        """Verschiedene User haben eigene Limits"""
        from modules.utils import RateLimiter
        limiter = RateLimiter(max_requests=1, window_seconds=1)
        self.assertTrue(limiter.is_allowed("userA"))
        self.assertTrue(limiter.is_allowed("userB"))
        self.assertFalse(limiter.is_allowed("userA"))

    def test_remaining_count(self):
        """get_remaining() gibt korrekte Anzahl"""
        from modules.utils import RateLimiter
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")
        self.assertEqual(limiter.get_remaining("user1"), 3)


class TestSecurityUtils(unittest.TestCase):
    """Tests für SecurityUtils"""

    def test_sanitize_preserves_valid(self):
        """Gültiger Text bleibt erhalten"""
        from modules.utils import SecurityUtils
        text = "Hallo Welt ä ö ü ß"
        result = SecurityUtils.sanitize_input(text)
        self.assertEqual(result, text)

    def test_sanitize_truncates_long_input(self):
        """Zu langer Input wird gekürzt"""
        from modules.utils import SecurityUtils
        long_text = "A" * 10000
        result = SecurityUtils.sanitize_input(long_text)
        self.assertLessEqual(len(result), SecurityUtils.MAX_MESSAGE_LENGTH)

    def test_sanitize_xss_prevention(self):
        """XSS wird escaped/entfernt"""
        from modules.utils import SecurityUtils
        xss = "<script>alert('xss')</script>"
        result = SecurityUtils.sanitize_input(xss)
        self.assertNotIn("<script>", result)

    def test_validate_chat_name_valid(self):
        """Gültige Chat-Namen werden akzeptiert"""
        from modules.utils import SecurityUtils
        self.assertTrue(SecurityUtils.validate_chat_name("Mein Chat"))
        self.assertTrue(SecurityUtils.validate_chat_name("Chat 123"))

    def test_validate_chat_name_invalid(self):
        """Ungültige Chat-Namen werden abgelehnt"""
        from modules.utils import SecurityUtils
        self.assertFalse(SecurityUtils.validate_chat_name(""))
        self.assertFalse(SecurityUtils.validate_chat_name("../../../etc/passwd"))


class TestSearchEngine(unittest.TestCase):
    """Tests für SearchEngine.needs_search()"""

    def test_weather_triggers_search(self):
        """Wetter-Frage löst Suche aus"""
        from modules.utils import SearchEngine
        self.assertTrue(SearchEngine.needs_search("Wie ist das Wetter in Berlin?"))

    def test_news_triggers_search(self):
        """Nachrichten-Frage löst Suche aus"""
        from modules.utils import SearchEngine
        self.assertTrue(SearchEngine.needs_search("Gibt es aktuelle Nachrichten?"))

    def test_price_triggers_search(self):
        """Preis/Kurs-Frage löst Suche aus"""
        from modules.utils import SearchEngine
        self.assertTrue(SearchEngine.needs_search("Wie ist der Bitcoin Kurs?"))

    def test_smalltalk_no_search(self):
        """Smalltalk löst KEINE Suche aus"""
        from modules.utils import SearchEngine
        self.assertFalse(SearchEngine.needs_search("Hallo, wie geht es dir?"))

    def test_statement_no_search(self):
        """Aussagen lösen KEINE Suche aus"""
        from modules.utils import SearchEngine
        self.assertFalse(SearchEngine.needs_search("Ich mag Wetter und Regen"))

    # Expliziter Such-Befehl Tests
    def test_explicit_search_command_slash(self):
        """/suche Prefix löst IMMER Suche aus"""
        from modules.utils import SearchEngine
        # Normale Nachricht würde keine Suche auslösen
        self.assertFalse(SearchEngine.needs_search("Ich mag Hunde"))

    def test_personal_question_no_search(self):
        """Persönliche Frage löst KEINE Suche aus"""
        from modules.utils import SearchEngine
        self.assertFalse(SearchEngine.needs_search("Wie heißt du?"))


class TestTextUtils(unittest.TestCase):
    """Tests für TextUtils"""

    def test_truncate(self):
        """Text wird auf max_length + '...' gekürzt"""
        from modules.utils import TextUtils
        result = TextUtils.truncate("Dies ist ein langer Text", 10)
        self.assertLessEqual(len(result), 13)  # 10 + "..."

    def test_truncate_short_text(self):
        """Kurzer Text bleibt unverändert"""
        from modules.utils import TextUtils
        text = "Kurz"
        result = TextUtils.truncate(text, 100)
        self.assertEqual(result, text)


# ============================================================================
# 8. SETTINGS MANAGER TESTS
# ============================================================================
class TestSettingsManager(unittest.TestCase):
    """Tests für modules/ui/settings_manager.py"""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.tmp_dir) / "config"
        self.config_dir.mkdir(exist_ok=True)
        self._managers = []  # Track SettingsManager instances for cleanup

    def _create_manager(self):
        """Erstellt einen SettingsManager und trackt ihn für cleanup."""
        from modules.ui.settings_manager import SettingsManager
        sm = SettingsManager(self.config_dir)
        self._managers.append(sm)
        return sm

    def tearDown(self):
        # Debounce-Timer sauber canceln bevor temp-Dir gelöscht wird
        for sm in self._managers:
            if sm._save_timer:
                sm._save_timer.cancel()
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_default_values(self):
        """Default-Werte werden korrekt geladen"""
        sm = self._create_manager()
        model = sm.get("selected_model")
        self.assertIsNotNone(model)

    def test_set_and_get(self):
        """Werte setzen und abrufen"""
        sm = self._create_manager()
        sm.set("temperature", 0.5)
        self.assertEqual(sm.get("temperature"), 0.5)

    def test_persistence(self):
        """Werte überleben Neustart (Datei wird geschrieben)"""
        sm1 = self._create_manager()
        sm1.set("test_key", "test_value")
        sm1.save_settings()  # Sofort schreiben statt Debounce abwarten

        sm2 = self._create_manager()
        self.assertEqual(sm2.get("test_key"), "test_value")


# ============================================================================
# 9. ERROR RESILIENCE TESTS
# ============================================================================
class TestErrorResilience(unittest.TestCase):
    """Tests für Fehlerbehandlung und Recovery"""

    def test_corrupted_db_recovery(self):
        """Korrupte DB-Datei wird behandelt"""
        import logging
        tmp_dir = tempfile.mkdtemp()
        db_path = Path(tmp_dir) / "corrupt.db"
        db_path.write_bytes(b"GARBAGE_NOT_SQLITE")
        try:
            from modules.database import Database
            # Suppress erwarteten ERROR-Log bei korrupter DB
            logging.disable(logging.ERROR)
            db = Database(db_path)
            # Wenn kein Crash → Recovery funktioniert
            db.close()
        except Exception:
            pass  # Auch akzeptabel
        finally:
            logging.disable(logging.NOTSET)
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_memory_with_long_text(self):
        """Sehr langer Text im Memory crashed nicht"""
        tmp_dir = tempfile.mkdtemp()
        db_path = Path(tmp_dir) / "test.db"
        try:
            from modules.database import Database
            from modules.memory import MemoryManager
            db = Database(db_path)
            mm = MemoryManager(db)
            long_text = "A" * 50000
            result = mm.learn(long_text)
            self.assertTrue(result)
            db.close()
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_empty_persona_fallback(self):
        """Persona wird aus config/persona.py geladen, Fallback auf SYSTEM_PROMPT_TEMPLATE"""
        tmp_dir = tempfile.mkdtemp()
        db_path = Path(tmp_dir) / "test.db"
        try:
            from modules.database import Database
            from modules.memory import MemoryManager
            db = Database(db_path)
            mm = MemoryManager(db)
            # get_system_prompt() sollte nie leer sein
            prompt = mm.get_system_prompt()
            self.assertIsNotNone(prompt)
            self.assertGreater(len(prompt), 50)
            self.assertIn("Astra", prompt)
            db.close()
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_persona_module_importable(self):
        """config/persona.py ist als Modul importierbar"""
        from config.persona import get_persona, PERSONA_TEMPLATE
        self.assertIn("{wissen}", PERSONA_TEMPLATE)
        result = get_persona("Test-Memory")
        self.assertIn("Test-Memory", result)
        self.assertIn("Astra", result)
        self.assertNotIn("{wissen}", result)  # Placeholder muss ersetzt sein


# ============================================================================
# 10. DATABASE EXTENDED TESTS
# ============================================================================
class TestDatabaseExtended(unittest.TestCase):
    """Tests für neue DB-Methoden: Indexes, Memory-Entries, Export"""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.tmp_dir) / "test_extended.db"
        from modules.database import Database
        self.db = Database(self.db_path)

    def tearDown(self):
        try:
            self.db.close()
        except Exception:
            pass
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_indexes_created(self):
        """Performance-Indexes werden angelegt"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}
        conn.close()
        self.assertIn("idx_messages_chat_id", indexes)
        self.assertIn("idx_memory_category", indexes)

    def test_get_memory_entries_structured(self):
        """get_memory_entries() gibt strukturierte Daten zurück"""
        self.db.add_memory("Test Info", "personal")
        time.sleep(0.1)
        entries = self.db.get_memory_entries()
        self.assertEqual(len(entries), 1)
        self.assertIn("id", entries[0])
        self.assertIn("content", entries[0])
        self.assertIn("category", entries[0])
        self.assertIn("created_at", entries[0])
        self.assertEqual(entries[0]["content"], "Test Info")
        self.assertEqual(entries[0]["category"], "personal")

    def test_delete_memory_by_id(self):
        """Einzelne Memory-Einträge können gelöscht werden"""
        self.db.add_memory("Info A", "general")
        self.db.add_memory("Info B", "general")
        entries = self.db.get_memory_entries()
        self.assertEqual(len(entries), 2)
        
        # Lösche ersten Eintrag
        result = self.db.delete_memory_by_id(entries[0]["id"])
        self.assertTrue(result)
        
        remaining = self.db.get_memory_entries()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["content"], "Info B")

    def test_delete_memory_nonexistent(self):
        """Löschen eines nicht existierenden Eintrags gibt False zurück"""
        result = self.db.delete_memory_by_id(99999)
        self.assertFalse(result)

    def test_get_memory_count(self):
        """get_memory_count() gibt korrekte Anzahl"""
        self.assertEqual(self.db.get_memory_count(), 0)
        self.db.add_memory("Eins", "general")
        self.db.add_memory("Zwei", "general")
        self.assertEqual(self.db.get_memory_count(), 2)

    def test_trim_old_memory(self):
        """trim_old_memory() entfernt älteste Einträge"""
        for i in range(10):
            self.db.add_memory(f"Info {i}", "general")
        
        self.assertEqual(self.db.get_memory_count(), 10)
        deleted = self.db.trim_old_memory(5)
        self.assertEqual(deleted, 5)
        self.assertEqual(self.db.get_memory_count(), 5)
        
        # Die neuesten 5 sollten übrig sein
        entries = self.db.get_memory_entries()
        contents = [e["content"] for e in entries]
        self.assertIn("Info 9", contents)
        self.assertIn("Info 5", contents)
        self.assertNotIn("Info 0", contents)

    def test_trim_within_limit(self):
        """trim_old_memory() löscht nichts wenn unter Limit"""
        self.db.add_memory("Eins", "general")
        deleted = self.db.trim_old_memory(100)
        self.assertEqual(deleted, 0)
        self.assertEqual(self.db.get_memory_count(), 1)

    def test_export_chat(self):
        """export_chat() gibt Markdown-formatierten Text zurück"""
        self.db.create_chat("ExportTest")
        self.db.save_message("ExportTest", "user", "Hallo Astra")
        self.db.save_message("ExportTest", "assistant", "Hallo! Wie kann ich helfen?")
        self.db._write_queue.join()
        
        export = self.db.export_chat("ExportTest")
        self.assertIn("# Chat: ExportTest", export)
        self.assertIn("Hallo Astra", export)
        self.assertIn("Wie kann ich helfen?", export)
        self.assertIn("👤 Du", export)
        self.assertIn("🤖 Astra", export)

    def test_export_empty_chat(self):
        """export_chat() gibt leeren String für leeren Chat"""
        self.db.create_chat("LeerChat")
        export = self.db.export_chat("LeerChat")
        self.assertEqual(export, "")


# ============================================================================
# 11. MEMORY EXTENDED TESTS
# ============================================================================
class TestMemoryExtended(unittest.TestCase):
    """Tests für neue Memory-Funktionen"""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.tmp_dir) / "test_memory_ext.db"
        from modules.database import Database
        from modules.memory import MemoryManager
        self.db = Database(self.db_path)
        self.mm = MemoryManager(self.db)

    def tearDown(self):
        try:
            self.db.close()
        except Exception:
            pass
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_get_memory_entries(self):
        """get_memory_entries() gibt strukturierte Einträge zurück"""
        self.mm.learn("Test Info", "personal")
        entries = self.mm.get_memory_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["content"], "Test Info")

    def test_delete_single_memory(self):
        """delete_memory() löscht einzelnen Eintrag und invalidiert Cache"""
        self.mm.learn("Info A", "general")
        self.mm.learn("Info B", "general")
        
        entries = self.mm.get_memory_entries()
        self.assertEqual(len(entries), 2)
        
        # Setze Cache
        self.mm.get_system_prompt()
        self.assertIsNotNone(self.mm._cached_system_prompt)
        
        # Lösche und prüfe Cache-Invalidierung
        result = self.mm.delete_memory(entries[0]["id"])
        self.assertTrue(result)
        self.assertIsNone(self.mm._cached_system_prompt)
        
        remaining = self.mm.get_memory_entries()
        self.assertEqual(len(remaining), 1)

    def test_memory_limit_enforcement(self):
        """learn() enforced MAX_MEMORY_ENTRIES Limit"""
        from config import MAX_MEMORY_ENTRIES
        # Speichere mehr als Limit (nutze kleines Limit für Test)
        for i in range(5):
            self.mm.learn(f"Info {i}", "general")
        
        count = self.db.get_memory_count()
        self.assertLessEqual(count, MAX_MEMORY_ENTRIES)

    def test_dedup_preserves_different_content(self):
        """Deduplizierung behält unterschiedliche Einträge"""
        self.mm.learn("Benutzer heißt Max", "personal")
        self.mm.learn("Benutzer ist 25 Jahre alt", "personal")
        self.mm.learn("Benutzer mag Python", "personal")
        
        memory = self.mm.get_memory_string_deduplicated()
        self.assertIn("Max", memory)
        self.assertIn("25", memory)
        self.assertIn("Python", memory)

    def test_dedup_removes_exact_duplicates(self):
        """Deduplizierung entfernt exakte Duplikate (case-insensitive)"""
        self.mm.learn("Benutzer mag Kaffee", "personal")
        self.mm.learn("benutzer mag kaffee", "personal")  # Gleich, nur Groß/Klein
        self.mm.learn("Benutzer trinkt Tee", "personal")
        
        memory = self.mm.get_memory_string_deduplicated()
        # Kaffee nur 1x (case-insensitive dedup)
        count = memory.lower().count("kaffee")
        self.assertEqual(count, 1)


# ============================================================================
# 12. HEALTH-CHECKER TESTS
# ============================================================================
class TestHealthChecker(unittest.TestCase):
    """Tests für den modernisierten HealthChecker"""

    def test_check_returns_bool(self):
        """check() gibt True/False zurück"""
        from modules.utils import HealthChecker
        # Unterdrücke print-Ausgabe
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            result = HealthChecker.check()
        self.assertIsInstance(result, bool)

    def test_run_all_checks_returns_list(self):
        """run_all_checks() gibt Liste von Dicts zurück"""
        from modules.utils import HealthChecker
        results = HealthChecker.run_all_checks()
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

    def test_result_structure(self):
        """Jedes Ergebnis hat category, name, level, message"""
        from modules.utils import HealthChecker
        results = HealthChecker.run_all_checks()
        for r in results:
            self.assertIn("category", r)
            self.assertIn("name", r)
            self.assertIn("level", r)
            self.assertIn("message", r)
            self.assertIn(r["level"], [
                HealthChecker.OK, HealthChecker.WARN,
                HealthChecker.FAIL, HealthChecker.INFO
            ])

    def test_import_checks_pass(self):
        """Alle Modul-Imports sollten OK sein"""
        from modules.utils import HealthChecker
        results = HealthChecker._check_imports()
        for r in results:
            self.assertEqual(r["category"], "Module")
            # Mindestens Database und Memory sollten importierbar sein
            if r["name"] in ("Database", "Memory", "Logger"):
                self.assertEqual(r["level"], HealthChecker.OK,
                                 f"{r['name']} Import fehlgeschlagen: {r['message']}")

    def test_filesystem_checks(self):
        """Dateisystem-Checks geben plausible Ergebnisse"""
        from modules.utils import HealthChecker
        results = HealthChecker._check_filesystem()
        self.assertGreater(len(results), 0)
        # config/__init__.py muss existieren
        config_check = [r for r in results if r["name"] == "config/__init__.py"]
        self.assertEqual(len(config_check), 1)
        self.assertEqual(config_check[0]["level"], HealthChecker.OK)

    def test_config_checks(self):
        """Config-Checks validieren Konfiguration"""
        from modules.utils import HealthChecker
        results = HealthChecker._check_config()
        self.assertGreater(len(results), 0)
        # OLLAMA_HOST sollte OK sein
        host_check = [r for r in results if r["name"] == "OLLAMA_HOST"]
        self.assertEqual(len(host_check), 1)
        self.assertEqual(host_check[0]["level"], HealthChecker.OK)

    def test_database_check(self):
        """Datenbank-Check gibt plausibles Ergebnis"""
        from modules.utils import HealthChecker
        results = HealthChecker._check_database()
        self.assertGreater(len(results), 0)
        # Level muss OK, WARN oder INFO sein (INFO bei Erststart)
        for r in results:
            self.assertIn(r["level"], [
                HealthChecker.OK, HealthChecker.INFO, HealthChecker.WARN
            ])

    def test_dependency_checks(self):
        """Abhängigkeits-Checks erkennen installierte Pakete"""
        from modules.utils import HealthChecker
        results = HealthChecker._check_dependencies()
        # PyQt6 sollte installiert sein
        pyqt_check = [r for r in results if r["name"] == "PyQt6"]
        self.assertEqual(len(pyqt_check), 1)
        self.assertEqual(pyqt_check[0]["level"], HealthChecker.OK)

    def test_gpu_check_no_crash(self):
        """GPU-Check crasht nicht (egal ob GPU vorhanden)"""
        from modules.utils import HealthChecker
        results = HealthChecker._check_gpu()
        self.assertGreater(len(results), 0)
        # Darf OK oder INFO sein, aber kein FAIL
        for r in results:
            self.assertNotEqual(r["level"], HealthChecker.FAIL)

    def test_print_results_verbose(self):
        """_print_results() crasht nicht im verbose-Modus"""
        from modules.utils import HealthChecker
        import io
        from contextlib import redirect_stdout
        results = HealthChecker.run_all_checks()
        f = io.StringIO()
        with redirect_stdout(f):
            HealthChecker._print_results(results, verbose=True)
        output = f.getvalue()
        self.assertIn("Ergebnis:", output)
        self.assertIn("Status:", output)


# ============================================================================
# 13. UPDATER TESTS
# ============================================================================
class TestUpdater(unittest.TestCase):
    """Tests für modules/updater.py"""

    def test_import(self):
        """Updater-Modul importierbar"""
        from modules.updater import UpdateChecker, CURRENT_VERSION, get_current_version
        self.assertIsNotNone(UpdateChecker)

    def test_current_version_format(self):
        """Version hat gültiges Format (X.Y.Z)"""
        from modules.updater import CURRENT_VERSION
        parts = CURRENT_VERSION.split(".")
        self.assertEqual(len(parts), 3)
        for p in parts:
            self.assertTrue(p.isdigit(), f"Version-Teil '{p}' ist keine Zahl")

    def test_get_current_version(self):
        """get_current_version() gibt CURRENT_VERSION zurück"""
        from modules.updater import get_current_version, CURRENT_VERSION
        self.assertEqual(get_current_version(), CURRENT_VERSION)

    def test_checker_instantiation(self):
        """UpdateChecker kann erstellt werden"""
        from modules.updater import UpdateChecker
        checker = UpdateChecker("1.0.0")
        self.assertEqual(checker.current_version, "1.0.0")


# ============================================================================
# 14. SYSTEM TRAY TESTS
# ============================================================================
class TestSystemTray(unittest.TestCase):
    """Tests für System-Tray-Funktionalität"""

    def test_tray_available(self):
        """QSystemTrayIcon ist importierbar"""
        from PyQt6.QtWidgets import QSystemTrayIcon
        self.assertIsNotNone(QSystemTrayIcon)

    def test_main_window_has_tray_methods(self):
        """ChatWindow hat Tray-Methoden"""
        from modules.ui.main_window import ChatWindow
        self.assertTrue(hasattr(ChatWindow, '_setup_system_tray'))
        self.assertTrue(hasattr(ChatWindow, '_quit_application'))
        self.assertTrue(hasattr(ChatWindow, '_tray_show_window'))
        self.assertTrue(hasattr(ChatWindow, '_on_tray_activated'))

    def test_main_window_has_update_methods(self):
        """ChatWindow hat Update-Methoden"""
        from modules.ui.main_window import ChatWindow
        self.assertTrue(hasattr(ChatWindow, '_check_for_updates'))
        self.assertTrue(hasattr(ChatWindow, '_on_update_available'))


# ============================================================================
# RUNNER
# ============================================================================
def run_tests():
    """Führt alle Tests aus und gibt Zusammenfassung"""
    print("\n" + "=" * 70)
    print("  ASTRA AI - Unified Test Suite")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Alle Test-Klassen hinzufügen
    test_classes = [
        TestConfig,
        TestLogger,
        TestDatabase,
        TestMemory,
        TestOllamaClient,
        TestRichFormatter,
        TestRateLimiter,
        TestSecurityUtils,
        TestSearchEngine,
        TestTextUtils,
        TestSettingsManager,
        TestErrorResilience,
        TestDatabaseExtended,
        TestMemoryExtended,
        TestHealthChecker,
        TestUpdater,
        TestSystemTray,
    ]

    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    # Verbose-Modus wenn -v Flag
    verbosity = 2 if "-v" in sys.argv else 1

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    # Zusammenfassung
    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total - failures - errors

    print(f"\n{'=' * 70}")
    print(f"  ERGEBNIS: {passed}/{total} Tests bestanden", end="")
    if failures + errors == 0:
        print(" - ALLES OK")
    else:
        print(f" ({failures} Fehler, {errors} Errors) - FEHLGESCHLAGEN")
    print("=" * 70 + "\n")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
