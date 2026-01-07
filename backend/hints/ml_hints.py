"""Простая ML модель для подсказок на основе паттернов пользователя"""
import json
import logging
from typing import Dict, List, Optional, Any
from collections import defaultdict, Counter
from pathlib import Path

from backend.config import settings
from backend.hints.action_tracker import ActionTracker

logger = logging.getLogger(__name__)


class MLHintSystem:
    """Простая ML модель для обучения на действиях пользователя"""
    
    def __init__(self):
        self.model_data_file = Path(settings.SANDBOX_DATA_DIR) / "ml_model.json"
        self.model_data: Dict[str, Any] = {}
        self._load_model()
    
    def _load_model(self):
        """Загрузить модель из файла"""
        if self.model_data_file.exists():
            try:
                with open(self.model_data_file, 'r', encoding='utf-8') as f:
                    self.model_data = json.load(f)
            except Exception as e:
                logger.error(f"Ошибка загрузки ML модели: {e}")
                self.model_data = {
                    "successful_patterns": {},
                    "failed_patterns": {},
                    "command_success_rates": {},
                    "mission_patterns": {}
                }
        else:
            self.model_data = {
                "successful_patterns": {},
                "failed_patterns": {},
                "command_success_rates": {},
                "mission_patterns": {}
            }
    
    def _save_model(self):
        """Сохранить модель в файл"""
        try:
            self.model_data_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.model_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.model_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения ML модели: {e}")
    
    def train_on_user_actions(self, username: str):
        """Обучить модель на действиях пользователя"""
        tracker = ActionTracker(username)
        patterns = tracker.get_user_patterns()
        
        # Обновляем статистику успешных паттернов
        for pattern in patterns.get("successful_patterns", []):
            mission_id = pattern.get("mission_id", "")
            command_base = pattern.get("command_base", "")
            key = f"{mission_id}:{command_base}"
            
            if key not in self.model_data["successful_patterns"]:
                self.model_data["successful_patterns"][key] = {
                    "count": 0,
                    "mission_id": mission_id,
                    "command": command_base
                }
            
            self.model_data["successful_patterns"][key]["count"] += 1
        
        # Обновляем статистику неудачных паттернов
        for pattern in patterns.get("failed_patterns", []):
            mission_id = pattern.get("mission_id", "")
            command_base = pattern.get("command_base", "")
            key = f"{mission_id}:{command_base}"
            
            if key not in self.model_data["failed_patterns"]:
                self.model_data["failed_patterns"][key] = {
                    "count": 0,
                    "mission_id": mission_id,
                    "command": command_base
                }
            
            self.model_data["failed_patterns"][key]["count"] += 1
        
        # Обновляем статистику успешности команд
        self._update_command_success_rates()
        
        self._save_model()
        logger.info(f"Модель обучена на действиях пользователя {username}")
    
    def _update_command_success_rates(self):
        """Обновить статистику успешности команд"""
        command_stats = defaultdict(lambda: {"success": 0, "total": 0})
        
        # Подсчитываем успешность по всем паттернам
        for key, pattern in self.model_data["successful_patterns"].items():
            command = pattern.get("command", "")
            if command:
                command_stats[command]["success"] += pattern.get("count", 0)
                command_stats[command]["total"] += pattern.get("count", 0)
        
        for key, pattern in self.model_data["failed_patterns"].items():
            command = pattern.get("command", "")
            if command:
                command_stats[command]["total"] += pattern.get("count", 0)
        
        # Вычисляем процент успешности
        for command, stats in command_stats.items():
            if stats["total"] > 0:
                success_rate = stats["success"] / stats["total"]
                self.model_data["command_success_rates"][command] = {
                    "success_rate": success_rate,
                    "total_attempts": stats["total"]
                }
    
    def predict_hint(
        self,
        mission_id: str,
        command: Optional[str] = None,
        error_message: Optional[str] = None,
        failed_checks: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        """Предсказать подсказку на основе обученной модели"""
        hints = []
        
        # Анализ команды
        if command:
            command_base = command.split()[0] if command else ""
            
            # Ищем успешные паттерны для этой миссии и команды
            key = f"{mission_id}:{command_base}"
            if key in self.model_data["successful_patterns"]:
                success_count = self.model_data["successful_patterns"][key].get("count", 0)
                fail_count = self.model_data["failed_patterns"].get(key, {}).get("count", 0)
                
                if fail_count > success_count and fail_count > 3:
                    # Команда часто терпит неудачу в этой миссии
                    hints.append({
                        "hint": f"Команда '{command_base}' часто вызывает проблемы в этой миссии. Проверьте синтаксис и параметры.",
                        "confidence": min(fail_count / (success_count + fail_count), 1.0),
                        "type": "command_failure_pattern"
                    })
            
            # Анализ общей успешности команды
            if command_base in self.model_data["command_success_rates"]:
                success_rate = self.model_data["command_success_rates"][command_base].get("success_rate", 1.0)
                if success_rate < 0.5:
                    hints.append({
                        "hint": f"Команда '{command_base}' часто используется неправильно. Проверьте документацию: 'man {command_base}' или '{command_base} --help'.",
                        "confidence": 1.0 - success_rate,
                        "type": "low_success_rate"
                    })
        
        # Анализ проваленных проверок
        if failed_checks:
            for check in failed_checks:
                check_name = check.get("name", "")
                check_type = check.get("type", "")
                
                # Ищем паттерны для этого типа проверки
                mission_patterns = self.model_data.get("mission_patterns", {}).get(mission_id, {})
                if check_type in mission_patterns:
                    common_solutions = mission_patterns[check_type].get("common_solutions", [])
                    if common_solutions:
                        hints.append({
                            "hint": common_solutions[0],
                            "confidence": 0.7,
                            "type": "learned_solution"
                        })
        
        if not hints:
            return None
        
        # Сортируем по уверенности и возвращаем лучшую подсказку
        hints.sort(key=lambda x: x["confidence"], reverse=True)
        return hints[0]["hint"]
    
    def learn_from_success(
        self,
        mission_id: str,
        command: str,
        check_results: List[Dict[str, Any]]
    ):
        """Обучить модель на успешном выполнении"""
        command_base = command.split()[0] if command else ""
        
        # Сохраняем успешный паттерн
        key = f"{mission_id}:{command_base}"
        if key not in self.model_data["successful_patterns"]:
            self.model_data["successful_patterns"][key] = {
                "count": 0,
                "mission_id": mission_id,
                "command": command_base
            }
        
        self.model_data["successful_patterns"][key]["count"] += 1
        
        # Сохраняем решения для проверок
        if mission_id not in self.model_data["mission_patterns"]:
            self.model_data["mission_patterns"][mission_id] = {}
        
        for check in check_results:
            if check.get("passed", False):
                check_type = check.get("type", "")
                if check_type not in self.model_data["mission_patterns"][mission_id]:
                    self.model_data["mission_patterns"][mission_id][check_type] = {
                        "common_solutions": []
                    }
                
                # Сохраняем команду как решение
                solution = f"Использование команды '{command_base}' помогло пройти проверку '{check.get('name', '')}'"
                if solution not in self.model_data["mission_patterns"][mission_id][check_type]["common_solutions"]:
                    self.model_data["mission_patterns"][mission_id][check_type]["common_solutions"].append(solution)
        
        self._update_command_success_rates()
        self._save_model()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику модели"""
        return {
            "total_successful_patterns": len(self.model_data.get("successful_patterns", {})),
            "total_failed_patterns": len(self.model_data.get("failed_patterns", {})),
            "tracked_commands": len(self.model_data.get("command_success_rates", {})),
            "mission_patterns": len(self.model_data.get("mission_patterns", {}))
        }


def get_ml_hint_system() -> MLHintSystem:
    """Получить экземпляр ML системы подсказок"""
    return MLHintSystem()

