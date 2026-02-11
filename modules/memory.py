"""
ASTRA AI - Memory Manager
=========================
Verwaltet Langzeitgedächtnis und System-Prompts
Intelligente automatische Erkennung von persönlichen Informationen
Hybrid Mode: Auto-Learning + Structured Manual Memory
"""

import re
import json
from config import SYSTEM_PROMPT_TEMPLATE
from modules.database import Database


class MemoryManager:
    """Verwaltet Memory und System-Prompts mit intelligenter Auto-Erkennung"""
    
    # Patterns für automatische Memory-Erkennung (Deutsch + Englisch)
    # WICHTIG: [\w\s\-äöüÄÖÜß] erlaubt Umlaute und Wörter mit Bindestrichen
    MEMORY_PATTERNS = {
        # NAME: Nur eindeutige Patterns für Namen (nicht "ich bin" - zu viel Noise!)
        r"(?:ich hei[ß]e|mein name ist|my name is|call me)\s+([A-Z][a-zäöüß\-]*(?:\s+[A-Z][a-zäöüß\-]*)*)": ("name", "personal"),
        # AGE: "ich bin X Jahre alt"
        r"(?:ich bin|i am|i\'m)\s+(\d+)\s+(?:jahr|Jahre|years|year)(?:\s+alt)?": ("age", "personal"),
        # LOCATION: "ich lebe/wohne in X"
        r"(?:ich lebe|ich wohne|i live|i\'m from)\s+(?:in\s+)?([\w\s\-äöüÄÖÜß]+?)(?:\.|,|!|$)": ("location", "personal"),
        # LIKES: "ich mag X"
        r"(?:ich mag|i like|i love|mein lieblings|my favorite|my favorit)\s+([\w\s\-äöüÄÖÜß]+?)(?:\.|,|!|und|$)": ("likes", "personal"),
        # RELATIONSHIP: "ich bin verheiratet/single/..."
        r"(?:ich bin|i\'m|i am)\s+(?:verheiratet|married|ledig|single|in einer beziehung|in a relationship|verlobt)": ("relationship", "personal"),
        # PROFESSION: "ich mache/studiere X als Y"
        r"(?:ich mache|ich mach|i\'m doing|i do|i\'m studying|ich studiere)\s+(?:eine\s+)?(?:umschulung\s+)?(?:als\s+)?([\w\s\-äöüÄÖÜß]+?)(?:\.|,|!|$)": ("profession", "personal"),
        # HOBBIES: "meine hobbys sind X, Y, Z"
        r"(?:meine hobbys|my hobbies|meine interessen|my interests|meine hobby|meine hobby)\s+(?:sind\s+)?([\w\s,\-äöüÄÖÜß]+?)(?:\.|,|!|$)": ("hobbies", "personal"),
        # CREATOR: "du bist von X erschaffen"
        r"(?:du bist|you are|you\'re)\s+(?:von|from)?\s+([\w\s\-äöüÄÖÜß]+?)\s+(?:erschaffen|created|gebaut|built)": ("creator", "personal"),
    }
    
    def __init__(self, db: Database):
        self.db = db
    
    def learn(self, information: str, category: str = "general") -> bool:
        """
        Speichert neue Information im Gedächtnis
        
        Args:
            information: Die zu speichernde Information
            category: Kategorie (general, personal, technical, etc.)
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        return self.db.add_memory(information, category)
    
    def extract_personal_info(self, text: str) -> dict:
        """
        Extrahiert automatisch persönliche Informationen aus Text
        SMART: Sucht nach Patterns + Fallback zu Name/Alter Extraction
        
        Args:
            text: Der zu analysierende Text
        
        Returns:
            Dict mit extrahierten Informationen {category: (value, type)}
        """
        # ✅ NORMALISIERUNG: Entferne Fluff-Worte am Anfang
        # "dir das ich" → "ich" | "also" → "" | "hey" → ""
        # Pattern: Entferne ALLES VOR dem ersten "ich/mein/my/i'm" etc  
        text_clean = re.sub(r'^.*?\b(ich|mein|my|i am|i\'m|i\'ve)\b', r'\1', text, flags=re.IGNORECASE)
        
        extracted = {}
        
        for pattern, (category, info_type) in self.MEMORY_PATTERNS.items():
            # Try both original and cleaned text
            for search_text in [text_clean, text]:  # Try cleaned first, then original
                matches = re.finditer(pattern, search_text, re.IGNORECASE)
                for match in matches:
                    if category not in extracted:  # Nur erste Übereinstimmung
                        value = match.group(1).strip() if match.lastindex else match.group(0).strip()
                        if value and len(value) > 1:
                            extracted[category] = {
                                "value": value,
                                "type": info_type
                            }
                    if category in extracted:  # Break inner loop if found
                        break
                if category in extracted:  # Break middle loop if found
                    break
        
        # ✅ FALLBACK: Wenn patterns nichts finden, nutze Heuristiken
        # Fall: "ich [Name] [number] Jahre" → Extract Name + Age
        if not extracted:
            text_clean_lower = text_clean.lower()
            
            # Age fallback: Find number + "jahr/year/alt"
            age_match = re.search(r'(\d+)\s+(?:jahr|Jahre|years|year|alt)', text_clean_lower)
            if age_match:
                extracted["age"] = {
                    "value": age_match.group(1),
                    "type": "personal"
                }
            
            # Name fallback: Nach "ich " das erste Wort (egal gross/klein)
            # Konvertiere zu Capitalized form: "duncan" → "Duncan"
            name_match = re.search(r'ich\s+(\w+)', text_clean_lower)
            if name_match:
                name_value = name_match.group(1)
                # Capitalize: "duncan" → "Duncan"
                name_value = name_value.capitalize()
                extracted["name"] = {
                    "value": name_value,
                    "type": "personal"
                }
        
        return extracted
    
    def auto_learn_from_message(self, message: str) -> list:
        """
        Versucht automatisch persönliche Informationen zu speichern
        
        Args:
            message: Die Benutzer-Nachricht
        
        Returns:
            Liste mit (category, value) für gespeicherte Informationen
        """
        extracted = self.extract_personal_info(message)
        saved = []
        
        for category, info in extracted.items():
            value = info["value"]
            if value and len(value) > 1:
                # Formatiere die Information
                formatted = self._format_memory(category, value)
                if self.learn(formatted, info["type"]):
                    saved.append((category, value))
        
        return saved
    
    def _format_memory(self, category: str, value: str) -> str:
        """Formatiert Informationen für Storage"""
        formatting = {
            "name": f"Name: {value}",
            "age": f"Alter: {value} Jahre",
            "location": f"Wohnort: {value}",
            "likes": f"Mag: {value}",
            "relationship": f"Beziehungsstatus: {value}",
            "profession": f"Beruf/Ausbildung: {value}",
            "hobbies": f"Hobbys: {value}",
            "creator": f"Ersteller/in: {value}",
        }
        return formatting.get(category, f"{category}: {value}")
    
    def get_memory_string(self) -> str:
        """
        Holt das gesamte Gedächtnis als deduplizierter String
        (optimiert für LLM System-Prompt)
        """
        return self.get_memory_string_deduplicated()
    
    def clear_memory(self) -> bool:
        """Löscht das gesamte Gedächtnis"""
        return self.db.clear_memory()
    
    def get_system_prompt(self) -> str:
        """
        Generiert den System-Prompt mit integriertem Memory
        Lädt optional persona.txt wenn vorhanden
        
        Returns:
            Vollständiger System-Prompt für die KI
        """
        from pathlib import Path
        
        memory = self.get_memory_string()
        
        # Versuche persona.txt zu laden (optional, Benutzer-Konfigurierbar)
        persona_path = Path(__file__).parent.parent / "persona.txt"
        if persona_path.exists():
            try:
                with open(persona_path, 'r', encoding='utf-8') as f:
                    persona_content = f.read()
                    # Ersetze {wissen} Platzhalter mit Memory
                    return persona_content.format(wissen=memory)
            except Exception:
                # Fallback auf Standard-Template
                pass
        
        # Fallback auf Standard SYSTEM_PROMPT_TEMPLATE
        return SYSTEM_PROMPT_TEMPLATE.format(memory=memory)
    
    def extract_memory_from_response(self, text: str) -> list:
        """
        Extrahiert ALLE [MERKEN: ...] Tags aus Response
        
        Returns:
            Liste von extrahierten Memory-Einträgen (kann leer sein)
        """
        if "[MERKEN:" not in text:
            return []
        
        memories = []
        temp_text = text
        
        # Finde alle [MERKEN:...] Tags
        while "[MERKEN:" in temp_text:
            start = temp_text.find("[MERKEN:") + 8
            end = temp_text.find("]", start)
            
            if end != -1:
                memory_text = temp_text[start:end].strip()
                if memory_text:  # Nur wenn nicht leer
                    memories.append(memory_text)
                temp_text = temp_text[end+1:]  # Weitermachen nach diesem Tag
            else:
                break
        
        return memories
    
    def extract_search_query(self, text: str) -> str:
        """
        Extrahiert [SUCHE: ...] Tag aus Response
        
        Returns:
            Extrahierter Suchbegriff oder None
        """
        if "[SUCHE:" not in text:
            return None
        
        start = text.find("[SUCHE:") + 7
        end = text.find("]", start)
        
        if end != -1:
            return text[start:end].strip()
        
        return None
    
    def remove_tags_from_response(self, text: str) -> str:
        """Entfernt [MERKEN:...] und [SUCHE:...] Tags aus der Response"""
        # Entferne MERKEN-Tags
        while "[MERKEN:" in text:
            start = text.find("[MERKEN:")
            end = text.find("]", start)
            if end != -1:
                text = text[:start] + text[end+1:]
            else:
                break
        
        # Entferne SUCHE-Tags
        while "[SUCHE:" in text:
            start = text.find("[SUCHE:")
            end = text.find("]", start)
            if end != -1:
                text = text[:start] + text[end+1:]
            else:
                break
        
        return text.strip()
    
    # ========================================================================
    # HYBRID MODE: Strukturiertes Merken (nicht Auto-Learning)
    # ========================================================================
    
    def smart_learn(self, information: str) -> bool:
        """
        Intelligentes strukturiertes Lernen mit Deduplizierung
        
        Used für "Merke:" Kommandos - nicht für Auto-Learning
        Speichert strukturiert und dedupliziert bestehende Einträge
        
        Args:
            information: Die zu speichernde Information
        
        Returns:
            True bei Erfolg
        """
        # ✅ WICHTIG: Versuche Info mit PATTERNS zu extrahieren
        extracted = self.extract_personal_info(information)
        
        if extracted:
            # Wir have strukturierte Einträge - speichere sie formatiert
            saved_any = False
            for category, info in extracted.items():
                value = info["value"]
                if value and len(value) > 1:
                    formatted = self._format_memory(category, value)
                    if self.db.add_memory(formatted, info["type"]):
                        saved_any = True
            return saved_any
        else:
            # Fallback: Keine Patterns gefunden - kategorisiere und speichere direkt
            category = self._infer_category(information)
            return self.db.add_memory(information, category)
    
    def _infer_category(self, text: str) -> str:
        """Versucht die beste Kategorie für die Information zu erraten"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["name", "heiße", "ich bin", "call me"]):
            return "personal"
        elif any(word in text_lower for word in ["wohne", "lebe", "stadt", "ort", "land"]):
            return "personal"
        elif any(word in text_lower for word in ["alt", "jahre", "age", "year"]):
            return "personal"
        elif any(word in text_lower for word in ["mag", "like", "liebe", "hobby", "interest"]):
            return "personal"
        elif any(word in text_lower for word in ["beruf", "job", "arbeit", "work", "profession"]):
            return "personal"
        else:
            return "general"
    
    def get_memory_string_deduplicated(self) -> str:
        """
        Holt Memory mit intelligenter Deduplizierung
        Zeigt nur neueste Version pro Info-Typ
        
        Returns:
            Formatierter, deduplizierter Memory-String
        """
        # Direkt von DB laden, nicht über get_memory_string()!
        memory = self.db.get_memory()
        
        if "Noch keine" in memory:
            return memory
        
        # Parse Einträge
        lines = memory.split("\n")
        seen_categories = {}
        result = []
        
        # Gehe reverse (neueste zuerst)
        for line in reversed(lines):
            if not line.strip():
                continue
            
            # Extrahiere Kategorie (erste paar Worte)
            words = line.split("]", 1)[-1].strip().split(":")
            if len(words) > 0:
                category_hint = words[0].lower()
                
                # Ignoriere Duplikate
                if category_hint not in seen_categories:
                    result.append(line)
                    seen_categories[category_hint] = True
        
        if not result:
            return "Noch keine Gedächtnisfragmente vorhanden."
        
        return "\n".join(reversed(result))  # Richtige Reihenfolge zurück
