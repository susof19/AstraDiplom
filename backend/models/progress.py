"""Модели прогресса и геймификации"""
from datetime import datetime
from typing import Dict, List, Optional, Any
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
        self.level_progress: Dict[str, int] = {"A": 0}
        self.achievements: List[str] = []
        self.user_data: Dict[str, Any] = {}  # Дополнительные данные пользователя (настройки и т.д.)
        self.last_updated: Optional[datetime] = None
        
    def load(self):
        """Загрузить прогресс из файла"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.missions_completed = data.get("missions_completed", {})
                    self.total_score = data.get("total_score", 0)
                    self.level_progress = data.get("level_progress", {"A": 0})
                    self.achievements = data.get("achievements", [])
                    self.user_data = data.get("user_data", {})
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
            "user_data": self.user_data,
            "last_updated": datetime.now().isoformat()
        }
        
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения прогресса: {e}")
    
    def complete_mission(self, mission_id: str, level: str, score: int) -> Dict[str, Any]:
        """Отметить миссию как выполненную
        
        Args:
            mission_id: ID миссии
            level: Уровень миссии
            score: Оценка в процентах (0-100)
        
        Returns:
            dict с ключами:
            - is_new: bool - первое прохождение миссии
            - is_improved: bool - улучшен результат
            - old_score: int - предыдущий результат (None если первое прохождение)
        """
        result = {
            "is_new": False,
            "is_improved": False,
            "old_score": None
        }
        
        if mission_id not in self.missions_completed:
            # Первое прохождение миссии
            self.missions_completed[mission_id] = {
                "level": level,
                "score": score,
                "completed_at": datetime.now().isoformat(),
                "attempts": 1
            }
            # НЕ добавляем score в total_score здесь - XP будет рассчитываться отдельно в grader
            self.level_progress[level] = self.level_progress.get(level, 0) + 1
            self._check_achievements(mission_id, level, score)
            result["is_new"] = True
        else:
            # Повторное прохождение
            old_score = self.missions_completed[mission_id]["score"]
            result["old_score"] = old_score
            
            if score > old_score:
                # Улучшен результат - обновляем score
                self.missions_completed[mission_id]["score"] = score
                result["is_improved"] = True
            # Если результат не лучше или равен - не обновляем score
            
            self.missions_completed[mission_id]["attempts"] += 1
        
        self.save()
        return result
    
    def _check_achievements(self, mission_id: str, level: str, score: int):
        """Проверить и выдать достижения"""
        achievements_to_check = [
            ("first_mission", lambda: len(self.missions_completed) == 1),
            ("perfect_score", lambda: score == 100),
            ("level_a_master", lambda: self.level_progress.get("A", 0) >= 5),
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

