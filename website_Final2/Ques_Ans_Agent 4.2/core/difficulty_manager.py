# core/difficulty_manager.py

class DifficultyManager:
    ORDER = ["easy", "medium", "hard"]

    def __init__(self, start_level: str = "medium"):
        if start_level not in self.ORDER:
            start_level = "medium"
        self.current_level = start_level

    def adjust(self, score: float) -> str:
        """
        Simple rule:
        - score >= 8.0 → increase difficulty (if possible)
        - score <= 4.0 → decrease difficulty (if possible)
        - otherwise keep same
        """
        idx = self.ORDER.index(self.current_level)
        if score >= 8.0 and idx < len(self.ORDER) - 1:
            idx += 1
        elif score <= 4.0 and idx > 0:
            idx -= 1
        self.current_level = self.ORDER[idx]
        return self.current_level
