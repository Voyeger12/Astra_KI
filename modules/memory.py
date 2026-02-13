"""
ASTRA AI - Memory Manager
=========================
Verwaltet Langzeitgedächtnis und System-Prompts
Memory wird AUSSCHLIESSLICH über [MERKEN:...]-Tags oder "Merke:"-Kommandos gespeichert
"""

import time
from pathlib import Path
from config import SYSTEM_PROMPT_TEMPLATE
from modules.database import Database


class MemoryManager:
    """Verwaltet Memory und System-Prompts"""
    
    def __init__(self, db: Database):
        self.db = db
        # ⚡ Cache-Variablen initialisieren
        self._cached_system_prompt = None
        self._last_prompt_time = None
    
    def learn(self, information: str, category: str = "general") -> bool:
        """
        Speichert neue Information im Gedächtnis.
        Enforced Memory-Limit automatisch (älteste Einträge werden entfernt).
        
        Args:
            information: Die zu speichernde Information
            category: Kategorie (general, personal, technical, etc.)
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        # 🔥 WICHTIG: Cache invalidieren wenn neue Memory gespeichert wird!
        self._cached_system_prompt = None
        self._last_prompt_time = None
        
        result = self.db.add_memory(information, category)
        
        # Memory-Limit enforcing: Älteste Einträge auto-löschen
        if result:
            from config import MAX_MEMORY_ENTRIES
            self.db.trim_old_memory(MAX_MEMORY_ENTRIES)
        
        return result
    
    
    def get_memory_string(self) -> str:
        """Holt das gesamte Gedächtnis als deduplizierter String"""
        return self.get_memory_string_deduplicated()
    
    def clear_memory(self) -> bool:
        """Löscht das gesamte Gedächtnis"""
        return self.db.clear_memory()
    
    def get_system_prompt(self) -> str:
        """
        Generiert den System-Prompt mit integriertem Memory
        ⚡ GECACHT für bessere Performance!
        Lädt optional persona.txt wenn vorhanden
        
        Returns:
            Vollständiger System-Prompt für die KI
        """

        try:
            # ⚡ CACHING: Wenn prompt nicht älter als 5s ist, nutze Cache  
            current_time = time.time()
            # ✅ Sicher: Prüfe OB Cache-Variablen existieren UND nicht None sind
            cached = getattr(self, '_cached_system_prompt', None)
            last_time = getattr(self, '_last_prompt_time', None)
            
            if cached is not None and last_time is not None:
                try:
                    if current_time - last_time < 5:
                        return cached
                except (TypeError, ValueError):
                    # Cache ist kaputt, ignoriert
                    pass
            
            # Versuche Memory zu laden
            try:
                memory = self.get_memory_string()
            except Exception as e:
                print(f"⚠️  Fehler bei get_memory_string(): {e}")
                memory = ""
            
            # Versuche persona.txt zu laden (optional)
            result = None
            persona_path = Path(__file__).parent.parent / "persona.txt"
            if persona_path.exists():
                try:
                    with open(persona_path, 'r', encoding='utf-8') as f:
                        persona_content = f.read()
                        result = persona_content.format(wissen=memory)
                except Exception as e:
                    print(f"⚠️  Fehler bei persona.txt: {e}")
                    result = None
            
            # Fallback auf Standard-Template
            if result is None:
                try:
                    result = SYSTEM_PROMPT_TEMPLATE.format(memory=memory)
                except Exception as e:
                    print(f"⚠️  Fehler bei SYSTEM_PROMPT_TEMPLATE.format(): {e}")
                    # LETZTER FALLBACK: Gib einfach den Template direkt zurück
                    result = SYSTEM_PROMPT_TEMPLATE
            
            # ⚡ Cache das Ergebnis
            self._cached_system_prompt = result
            self._last_prompt_time = current_time
            
            return result
            
        except Exception as e:
            print(f"❌ KRITISCHER FEHLER in get_system_prompt(): {e}")
            import traceback
            traceback.print_exc()
            # ABSOLUTE ZURÜCKFALL: Gib einen minimalen Prompt zurück
            return "Du bist ein hilfreicher KI-Assistent. Antworte auf Deutsch."
    
    def extract_memory_from_response(self, text: str) -> list:
        """
        Extrahiert ALLE [MERKEN: ...] Tags aus Response.
        Unterstützt verschachtelte Klammern (z.B. [MERKEN: Array ist [1,2,3]])
        
        Returns:
            Liste von extrahierten Memory-Einträgen (kann leer sein)
        """
        if "[MERKEN:" not in text:
            return []
        
        memories = []
        temp_text = text
        
        while "[MERKEN:" in temp_text:
            start = temp_text.find("[MERKEN:") + 8
            # Bracket-sicheres Parsing: Zähle [ und ] um verschachtelte Klammern zu handhaben
            depth = 1
            pos = start
            while pos < len(temp_text) and depth > 0:
                if temp_text[pos] == '[':
                    depth += 1
                elif temp_text[pos] == ']':
                    depth -= 1
                pos += 1
            
            if depth == 0:
                memory_text = temp_text[start:pos - 1].strip()
                if memory_text:
                    memories.append(memory_text)
                temp_text = temp_text[pos:]
            else:
                break  # Unbalancierte Klammern — abbrechen
        
        return memories
    
    def remove_tags_from_response(self, text: str) -> str:
        """Entfernt [MERKEN:...] und [SUCHE:...] Tags aus der Response (bracket-sicher)"""
        for tag in ["[MERKEN:", "[SUCHE:"]:
            while tag in text:
                tag_start = text.find(tag)
                # Bracket-sicheres Parsing
                depth = 1
                pos = tag_start + len(tag)
                while pos < len(text) and depth > 0:
                    if text[pos] == '[':
                        depth += 1
                    elif text[pos] == ']':
                        depth -= 1
                    pos += 1
                
                if depth == 0:
                    text = text[:tag_start] + text[pos:]
                else:
                    break  # Unbalanciert — aufhören
        
        return text.strip()
    
    def get_memory_entries(self) -> list:
        """Gibt alle Memory-Einträge als strukturierte Daten zurück (für Settings-UI)"""
        return self.db.get_memory_entries()
    
    def delete_memory(self, memory_id: int) -> bool:
        """Löscht einen einzelnen Memory-Eintrag"""
        self._cached_system_prompt = None
        self._last_prompt_time = None
        return self.db.delete_memory_by_id(memory_id)
    
    def get_memory_string_deduplicated(self) -> str:
        """
        Holt Memory mit echter Content-basierter Deduplizierung.
        Entfernt exakte Duplikate, behält neueste Version.
        
        Returns:
            Formatierter, deduplizierter Memory-String
        """
        try:
            entries = self.db.get_memory_entries()
            
            if not entries:
                return "Noch keine Gedächtnisfragmente vorhanden."
            
            # Echte Deduplizierung: Normalisierter Content als Key
            # Spätere Einträge überschreiben frühere (neueste Version gewinnt)
            seen = {}
            for entry in entries:
                normalized = entry['content'].strip().lower()
                seen[normalized] = entry
            
            unique = sorted(seen.values(), key=lambda x: x['id'])
            
            if not unique:
                return "Noch keine Gedächtnisfragmente vorhanden."
            
            return "\n".join(f"[{e['created_at']}] {e['content']}" for e in unique)
        
        except Exception as e:
            print(f"⚠️  Fehler bei get_memory_string_deduplicated(): {e}")
            return "Fehler beim Memory laden - Weitermachen ohne Memory"
