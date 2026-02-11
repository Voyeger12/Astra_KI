"""
Enhanced Memory System
======================
Fügt Confidence-Scores und intelligente Bereinigung zum Memory hinzu
Automatic merging ähnlicher Patterns mit Confidence-Scores
"""

import json
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from difflib import SequenceMatcher


class MemoryEnhancer:
    """Erweitert das Memory-System mit Scoring und Deduplication"""
    
    # Confidence Score Thresholds
    EXACT_MATCH_CONFIDENCE = 1.0
    SIMILAR_MATCH_CONFIDENCE = 0.85
    PATTERN_MATCH_CONFIDENCE = 0.7
    AUTO_LEARN_CONFIDENCE = 0.6
    
    # Cleanup Settings
    LOW_CONFIDENCE_THRESHOLD = 0.4  # Unter 40% wird gelöscht
    SIMILARITY_THRESHOLD = 0.85  # Für Merging
    MIN_OCCURRENCES_FOR_CONFIDENCE_BOOST = 3  # Nach 3x Vorkommen -> 0.95
    
    def __init__(self, db_connection):
        """
        Args:
            db_connection: Verbindung zur Memory-DB
        """
        self.db = db_connection
        self.memory_metadata = {}  # {memory_id: {confidence, count, last_used, source}}
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """
        Berechnet Ähnlichkeit zwischen zwei Texten (0.0-1.0)
        
        Args:
            text1: Erster Text
            text2: Zweiter Text
        
        Returns:
            Ähnlichkeits-Score zwischen 0.0 und 1.0
        """
        # Normalisiere beide Texte
        t1 = text1.lower().strip()
        t2 = text2.lower().strip()
        
        if t1 == t2:
            return 1.0
        
        # Nutze SequenceMatcher für Ähnlichkeitsberechnung
        matcher = SequenceMatcher(None, t1, t2)
        return matcher.ratio()
    
    def find_similar_memories(self, new_memory: str, min_similarity: float = 0.7) -> List[Tuple[str, float]]:
        """
        Findet ähnliche Erinnerungen in der DB
        
        Args:
            new_memory: Neue Memory-Information
            min_similarity: Minimale Ähnlichkeit (default 0.7)
        
        Returns:
            Liste von (memory_text, similarity_score) Tupeln
        """
        similar = []
        
        # Lade alle existierenden Memories (würde mit echter DB-Query arbeiten)
        # Dies ist ein Placeholder für die echte Implementation
        # In Produktion würde man hier mit der echten DB arbeiten
        
        return similar
    
    def calculate_confidence_score(
        self, 
        memory_text: str, 
        source: str = "auto_learn",  # "user" | "auto_learn" | "search" | "pattern"
        occurrences: int = 1,
        similarity_to_existing: float = 1.0
    ) -> float:
        """
        Berechnet Confidence-Score für neue Memory
        
        Args:
            memory_text: Der Memory-Eintrag
            source: Quelle (user/auto/search/pattern)
            occurrences: Häufigkeit des Auftretens
            similarity_to_existing: Ähnlichkeit zu existierenden Memories
        
        Returns:
            Confidence-Score zwischen 0.0 und 1.0
        """
        base_confidence = {
            "user": 0.95,        # User-Input sehr zuverlässig
            "auto_learn": 0.60,  # Auto-Learning niedrig, kann falsch sein
            "search": 0.75,      # Web-Search mittelhoch
            "pattern": 0.70,     # Pattern-Matching mittel
        }.get(source, 0.5)
        
        # Boost bei Duplikaten
        if occurrences >= self.MIN_OCCURRENCES_FOR_CONFIDENCE_BOOST:
            base_confidence = min(0.95, base_confidence + 0.35)  # Max 0.95
        elif occurrences >= 2:
            base_confidence = min(0.85, base_confidence + 0.15)
        
        # Reduziere wenn zu ähnlich zu existierenden (könnte Duplikat sein)
        if similarity_to_existing < 0.5:
            base_confidence *= 0.8
        
        return min(1.0, max(0.0, base_confidence))
    
    def merge_similar_memories(
        self,
        memory1: Dict,  # {text, confidence, source, created_at}
        memory2: Dict
    ) -> Dict:
        """
        Mergt zwei ähnliche Memories zu einer
        
        Args:
            memory1: Erste Memory
            memory2: Zweite Memory
        
        Returns:
            Gemergter Memory mit höchster Confidence
        """
        similarity = self.calculate_similarity(memory1["text"], memory2["text"])
        
        if similarity < self.SIMILARITY_THRESHOLD:
            return None  # Nicht ähnlich genug zum Mergen
        
        # Wähle den Memory mit höherer Confidence
        primary = memory1 if memory1.get("confidence", 0.5) >= memory2.get("confidence", 0.5) else memory2
        secondary = memory2 if primary == memory1 else memory1
        
        # Erhöhe Confidence des Primary durch Bestätigung
        new_confidence = min(
            1.0,
            primary.get("confidence", 0.5) + (0.1 * secondary.get("confidence", 0.5))
        )
        
        return {
            "text": primary["text"],
            "confidence": new_confidence,
            "source": "merged",
            "created_at": primary.get("created_at"),
            "merged_from": [memory1["text"], memory2["text"]]
        }
    
    def cleanup_low_confidence_memories(self, threshold: float = None) -> Dict:
        """
        Entfernt Memories unter Confidence-Threshold
        
        Args:
            threshold: Confidence-Schwelle (default: LOW_CONFIDENCE_THRESHOLD)
        
        Returns:
            {deleted_count, deleted_memories}
        """
        threshold = threshold or self.LOW_CONFIDENCE_THRESHOLD
        deleted = {"count": 0, "memories": []}
        
        # In echter Implementation würde man hier die DB auslesen
        # und Einträge unter dem Threshold löschen
        
        return deleted
    
    def boost_memory_confidence(self, memory_id: str, boost_amount: float = 0.1) -> float:
        """
        Erhöht Confidence eines Memories wenn es wiederholt bestätigt wird
        
        Args:
            memory_id: ID des Memories
            boost_amount: Wie viel hinzufügen (0.0-0.1)
        
        Returns:
            Neue Confidence
        """
        # Placeholder für DB-Update
        return 0.0
    
    def format_memory_with_confidence(self, memory_text: str, confidence: float) -> str:
        """
        Formatiert Memory mit visueller Confidence-Anzeige
        
        Args:
            memory_text: Der Memory-Text
            confidence: Confidence-Score (0.0-1.0)
        
        Returns:
            Formatierter Text mit Confidence-Badge
        """
        # Farbcodierung basierend auf Confidence
        if confidence >= 0.9:
            badge = "🟢 sehr sicher"  # Grün: sehr zuverlässig
        elif confidence >= 0.75:
            badge = "🟡 wahrscheinlich"  # Gelb: wahrscheinlich
        elif confidence >= 0.5:
            badge = "🟠 möglich"  # Orange: unsicher
        else:
            badge = "🔴 zweifelhaft"  # Rot: sehr unsicher
        
        return f"{memory_text} [{badge} {int(confidence*100)}%]"
    
    def extract_confidence_from_memory(self, memory_entry: str) -> Tuple[str, Optional[float]]:
        """
        Extrahiert Confidence-Score aus formattiertem Memory
        
        Args:
            memory_entry: Formatierter Memory-Eintrag
        
        Returns:
            (memory_text, confidence_score) oder (text, None) wenn kein Score
        """
        # Pattern: "Text [🟢 sehr sicher 95%]"
        pattern = r'\[.*?(\d+)%\]'
        match = re.search(pattern, memory_entry)
        
        if match:
            confidence = int(match.group(1)) / 100.0
            text = re.sub(pattern, '', memory_entry).strip()
            return text, confidence
        
        return memory_entry, None
    
    def get_memory_statistics(self) -> Dict:
        """
        Gibt Statistiken über das Memory-System
        
        Returns:
            {
                total_memories: int,
                avg_confidence: float,
                high_confidence_count: int,
                low_confidence_count: int,
                suggested_cleanups: int
            }
        """
        return {
            "total_memories": 0,  # Würde aus DB kommen
            "avg_confidence": 0.0,
            "high_confidence_count": 0,
            "low_confidence_count": 0,
            "suggested_cleanups": 0,
        }


class SmartMemoryIntegration:
    """Integriert Enhanced Memory in die bestehende MemoryManager"""
    
    def __init__(self, memory_manager, db_connection):
        self.memory = memory_manager
        self.enhancer = MemoryEnhancer(db_connection)
    
    def smart_learn_with_confidence(
        self,
        text: str,
        category: str = "general",
        source: str = "user",
        expected_confidence: float = None
    ) -> Tuple[bool, float]:
        """
        Speichert Memory mit intelligenter Confidence-Berechnung
        
        Returns:
            (success, confidence_score)
        """
        # Finde ähnliche Memories
        similar = self.enhancer.find_similar_memories(text)
        similarity_score = max([s[1] for s in similar]) if similar else 1.0
        
        # Berechne Confidence
        confidence = self.enhancer.calculate_confidence_score(
            text,
            source=source,
            occurrences=len(similar),
            similarity_to_existing=similarity_score
        )
        
        # Wenn zu niedrig, speichere trotzdem aber mit Warnung
        if confidence < self.enhancer.LOW_CONFIDENCE_THRESHOLD and source == "auto_learn":
            return False, confidence
        
        # Speichere Memory
        success = self.memory.learn(text, category)
        
        return success, confidence
    
    def cleanup_unreliable_memories(self) -> Dict:
        """
        Bereinigt Memory-System von unreliablen Einträgen
        
        Returns:
            Statistiken über gelöschte Memories
        """
        return self.enhancer.cleanup_low_confidence_memories()


# Test-Beispiel
if __name__ == "__main__":
    enhancer = MemoryEnhancer(None)
    
    # Test Similarity
    sim1 = enhancer.calculate_similarity("Mein Name ist Duncan", "Ich heiße Duncan")
    print(f"Similarity Test 1: {sim1:.2f}")
    
    sim2 = enhancer.calculate_similarity("Ich programmiere in Python", "Mein Lieblingsprogrammierer ist Python")
    print(f"Similarity Test 2: {sim2:.2f}")
    
    # Test Confidence Scoring
    conf1 = enhancer.calculate_confidence_score("Name: Duncan", source="user")
    print(f"User Confidence: {conf1:.2f}")
    
    conf2 = enhancer.calculate_confidence_score("mag Pizza", source="auto_learn", occurrences=1)
    print(f"Auto-Learn Confidence (1x): {conf2:.2f}")
    
    conf3 = enhancer.calculate_confidence_score("mag Pizza", source="auto_learn", occurrences=5)
    print(f"Auto-Learn Confidence (5x): {conf3:.2f}")
    
    # Test Formatting
    fmt = enhancer.format_memory_with_confidence("Name: Duncan", 0.95)
    print(f"Formatted: {fmt}")
