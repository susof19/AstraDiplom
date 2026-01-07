"""Главная система подсказок, объединяющая Rule-based и ML подходы"""
import logging
from typing import Dict, List, Optional, Any

from backend.hints.rule_based_hints import RuleBasedHintSystem
from backend.hints.ml_hints import MLHintSystem
from backend.hints.action_tracker import ActionTracker

logger = logging.getLogger(__name__)


class HintSystem:
    """Главная система подсказок"""
    
    def __init__(self):
        self.rule_based = RuleBasedHintSystem()
        self.ml_system = MLHintSystem()
    
    def get_hints(
        self,
        username: str,
        mission_id: str,
        level: str,
        error_message: Optional[str] = None,
        command: Optional[str] = None,
        check_result: Optional[Dict[str, Any]] = None,
        use_ml: bool = True
    ) -> List[str]:
        """Получить подсказки для пользователя"""
        hints = []
        
        # Получаем подсказки от rule-based системы
        rule_hint = self.rule_based.get_hint_for_error(
            error_message=error_message or "",
            command=command,
            check_result=check_result,
            mission_id=mission_id
        )
        
        if rule_hint:
            hints.append({
                "text": rule_hint,
                "source": "rule_based",
                "priority": 1
            })
        
        # Получаем подсказки от ML системы (если включено)
        if use_ml:
            failed_checks = []
            if check_result:
                failed_checks = [
                    c for c in check_result.get("checks", [])
                    if not c.get("passed", False)
                ]
            
            ml_hint = self.ml_system.predict_hint(
                mission_id=mission_id,
                command=command,
                error_message=error_message,
                failed_checks=failed_checks
            )
            
            if ml_hint:
                hints.append({
                    "text": ml_hint,
                    "source": "ml",
                    "priority": 2
                })
        
        # Если есть проваленные проверки, получаем специфичные подсказки
        if check_result:
            failed_checks = [
                c for c in check_result.get("checks", [])
                if not c.get("passed", False)
            ]
            
            if failed_checks:
                check_hints = self.rule_based.get_hints_for_failed_checks(failed_checks)
                for hint_text in check_hints:
                    if hint_text not in [h["text"] for h in hints]:
                        hints.append({
                            "text": hint_text,
                            "source": "rule_based",
                            "priority": 1
                        })
        
        # Сортируем по приоритету
        hints.sort(key=lambda x: x["priority"])
        
        return [h["text"] for h in hints]
    
    def track_and_learn(
        self,
        username: str,
        mission_id: str,
        level: str,
        command: Optional[str] = None,
        check_result: Optional[Dict[str, Any]] = None,
        success: bool = False
    ):
        """Отследить действие и обучить модель"""
        tracker = ActionTracker(username)
        
        # Отслеживаем действие
        if command:
            exit_code = 0 if success else 1
            tracker.track_command(
                mission_id=mission_id,
                level=level,
                command=command,
                exit_code=exit_code,
                output=""
            )
        
        if check_result:
            tracker.track_check_result(
                mission_id=mission_id,
                level=level,
                check_result=check_result
            )
            
            # Если миссия успешно выполнена, обучаем модель на успехе
            if success and command:
                self.ml_system.learn_from_success(
                    mission_id=mission_id,
                    command=command,
                    check_results=check_result.get("checks", [])
                )
        
        # Периодически переобучаем модель на действиях пользователя
        # (можно сделать это асинхронно или по расписанию)
        try:
            self.ml_system.train_on_user_actions(username)
        except Exception as e:
            logger.warning(f"Ошибка обучения ML модели: {e}")


def get_hint_system() -> HintSystem:
    """Получить экземпляр системы подсказок"""
    return HintSystem()

