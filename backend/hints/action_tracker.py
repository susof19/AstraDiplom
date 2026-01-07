"""Отслеживание действий пользователя для обучения ML модели"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict

from backend.config import settings

logger = logging.getLogger(__name__)


class ActionTracker:
    """Отслеживание действий пользователя в песочнице"""
    
    def __init__(self, username: str):
        self.username = username
        self.actions_dir = Path(settings.SANDBOX_DATA_DIR) / "user_actions"
        self.actions_dir.mkdir(parents=True, exist_ok=True)
        self.actions_file = self.actions_dir / f"{username}_actions.json"
        self.actions: List[Dict[str, Any]] = []
        self._load_actions()
    
    def _load_actions(self):
        """Загрузить историю действий пользователя"""
        if self.actions_file.exists():
            try:
                with open(self.actions_file, 'r', encoding='utf-8') as f:
                    self.actions = json.load(f)
            except Exception as e:
                logger.error(f"Ошибка загрузки действий пользователя {self.username}: {e}")
                self.actions = []
        else:
            self.actions = []
    
    def _save_actions(self):
        """Сохранить историю действий"""
        try:
            with open(self.actions_file, 'w', encoding='utf-8') as f:
                json.dump(self.actions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения действий пользователя {self.username}: {e}")
    
    def track_action(
        self,
        mission_id: str,
        level: str,
        action_type: str,
        command: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Записать действие пользователя"""
        action = {
            "timestamp": datetime.now().isoformat(),
            "mission_id": mission_id,
            "level": level,
            "action_type": action_type,  # "command", "file_operation", "check_mission", etc.
            "command": command,
            "result": result,
            "error": error,
            "context": context or {}
        }
        
        self.actions.append(action)
        
        # Ограничиваем размер истории (последние 1000 действий)
        if len(self.actions) > 1000:
            self.actions = self.actions[-1000:]
        
        self._save_actions()
        logger.debug(f"Записано действие пользователя {self.username}: {action_type} для миссии {mission_id}")
    
    def track_command(self, mission_id: str, level: str, command: str, exit_code: int, output: str):
        """Записать выполнение команды"""
        self.track_action(
            mission_id=mission_id,
            level=level,
            action_type="command",
            command=command,
            result={
                "exit_code": exit_code,
                "output_length": len(output),
                "success": exit_code == 0
            }
        )
    
    def track_check_result(self, mission_id: str, level: str, check_result: Dict[str, Any]):
        """Записать результат проверки миссии"""
        failed_checks = [c for c in check_result.get("checks", []) if not c.get("passed", False)]
        
        self.track_action(
            mission_id=mission_id,
            level=level,
            action_type="check_mission",
            result={
                "score": check_result.get("score", 0),
                "result": check_result.get("result", "failed"),
                "failed_checks": [
                    {
                        "name": c.get("name"),
                        "type": c.get("type"),
                        "message": c.get("message")
                    }
                    for c in failed_checks
                ]
            }
        )
    
    def get_mission_statistics(self, mission_id: str) -> Dict[str, Any]:
        """Получить статистику по миссии"""
        mission_actions = [a for a in self.actions if a.get("mission_id") == mission_id]
        
        if not mission_actions:
            return {
                "total_actions": 0,
                "successful_commands": 0,
                "failed_commands": 0,
                "common_errors": {},
                "common_commands": {}
            }
        
        successful_commands = sum(
            1 for a in mission_actions 
            if a.get("action_type") == "command" and a.get("result", {}).get("success", False)
        )
        failed_commands = sum(
            1 for a in mission_actions 
            if a.get("action_type") == "command" and not a.get("result", {}).get("success", True)
        )
        
        # Подсчет частых команд
        command_counts = defaultdict(int)
        for a in mission_actions:
            if a.get("action_type") == "command" and a.get("command"):
                cmd_base = a["command"].split()[0] if a["command"] else ""
                command_counts[cmd_base] += 1
        
        # Подсчет частых ошибок
        error_counts = defaultdict(int)
        for a in mission_actions:
            if a.get("error"):
                error_counts[a["error"]] += 1
        
        return {
            "total_actions": len(mission_actions),
            "successful_commands": successful_commands,
            "failed_commands": failed_commands,
            "common_errors": dict(error_counts),
            "common_commands": dict(command_counts)
        }
    
    def get_user_patterns(self) -> Dict[str, Any]:
        """Получить паттерны поведения пользователя для ML модели"""
        if not self.actions:
            return {}
        
        # Анализ успешных паттернов
        successful_patterns = []
        failed_patterns = []
        
        for action in self.actions:
            if action.get("action_type") == "command":
                pattern = {
                    "command_base": action.get("command", "").split()[0] if action.get("command") else "",
                    "mission_id": action.get("mission_id"),
                    "level": action.get("level"),
                    "success": action.get("result", {}).get("success", False)
                }
                
                if pattern["success"]:
                    successful_patterns.append(pattern)
                else:
                    failed_patterns.append(pattern)
        
        return {
            "successful_patterns": successful_patterns,
            "failed_patterns": failed_patterns,
            "total_actions": len(self.actions)
        }


def get_action_tracker(username: str) -> ActionTracker:
    """Получить трекер действий для пользователя"""
    return ActionTracker(username)

