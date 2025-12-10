"""Модели прогресса и геймификации"""
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import json

from backend.config import settings


class UserProgress:
    """Прогресс пользователя"""
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.progress_file = settings.SANDBOX_DATA_DIR / f"progress_{user_id}.json"
        self.missions_completed: Dict[str, Dict] = {}
        self.total_score: int = 0
        self.level_progress: Dict[str, int] = {"A": 0, "B": 0, "C": 0}
        self.achievements: List[str] = []
        self.last_updated: Optional[datetime] = None
        
    def load(self):
        """Загрузить прогресс из файла"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.missions_completed = data.get("missions_completed", {})
                    self.total_score = data.get("total_score", 0)
                    self.level_progress = data.get("level_progress", {"A": 0, "B": 0, "C": 0})
                    self.achievements = data.get("achievements", [])
                    if data.get("last_updated"):
                        self.last_updated = datetime.fromisoformat(data["last_updated"])
            except Exception as e:
                print(f"Ошибка загрузки прогресса: {e}")
    
    def save(self):
        """Сохранить прогресс в файл"""
        settings.SANDBOX_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        data = {
            "user_id": self.user_id,
            "missions_completed": self.missions_completed,
            "total_score": self.total_score,
            "level_progress": self.level_progress,
            "achievements": self.achievements,
            "last_updated": datetime.now().isoformat()
        }
        
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения прогресса: {e}")
    
    def complete_mission(self, mission_id: str, level: str, score: int):
        """Отметить миссию как выполненную"""
        if mission_id not in self.missions_completed:
            self.missions_completed[mission_id] = {
                "level": level,
                "score": score,
                "completed_at": datetime.now().isoformat(),
                "attempts": 1
            }
            self.total_score += score
            self.level_progress[level] = self.level_progress.get(level, 0) + 1
            self._check_achievements(mission_id, level, score)
        else:
            # Обновляем, если результат лучше
            old_score = self.missions_completed[mission_id]["score"]
            if score > old_score:
                self.total_score += (score - old_score)
                self.missions_completed[mission_id]["score"] = score
            self.missions_completed[mission_id]["attempts"] += 1
        
        self.save()
    
    def _check_achievements(self, mission_id: str, level: str, score: int):
        """Проверить и выдать достижения"""
        achievements_to_check = [
            ("first_mission", lambda: len(self.missions_completed) == 1),
            ("perfect_score", lambda: score == 100),
            ("level_a_master", lambda: self.level_progress.get("A", 0) >= 5),
            ("level_b_master", lambda: self.level_progress.get("B", 0) >= 5),
            ("level_c_master", lambda: self.level_progress.get("C", 0) >= 5),
            ("all_levels", lambda: all(self.level_progress.get(l, 0) > 0 for l in ["A", "B", "C"])),
            ("high_score", lambda: self.total_score >= 1000),
        ]
        
        for achievement_id, condition in achievements_to_check:
            if achievement_id not in self.achievements and condition():
                self.achievements.append(achievement_id)
    
    def get_stats(self) -> Dict:
        """Получить статистику"""
        total_missions = len(self.missions_completed)
        avg_score = self.total_score / total_missions if total_missions > 0 else 0
        
        return {
            "user_id": self.user_id,
            "total_missions_completed": total_missions,
            "total_score": self.total_score,
            "average_score": round(avg_score, 2),
            "level_progress": self.level_progress,
            "achievements": self.achievements,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }


# Глобальное хранилище прогресса (в продакшене использовать БД)
_progress_store: Dict[str, UserProgress] = {}


def get_user_progress(user_id: str = "default") -> UserProgress:
    """Получить прогресс пользователя"""
    if user_id not in _progress_store:
        progress = UserProgress(user_id)
        progress.load()
        _progress_store[user_id] = progress
    return _progress_store[user_id]

