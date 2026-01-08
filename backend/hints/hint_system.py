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
    
    async def get_hints(
        self,
        username: str,
        mission_id: str,
        level: str,
        error_message: Optional[str] = None,
        command: Optional[str] = None,
        check_result: Optional[Dict[str, Any]] = None,
        use_ml: bool = True,
        os_type: Optional[str] = None
    ) -> List[str]:
        """Получить подсказки для пользователя"""
        hints = []
        
        # Если миссия пройдена успешно, не показываем подсказки
        if check_result:
            result_status = check_result.get("result", "failed")
            score = check_result.get("score", 0)
            is_passed = result_status == "passed" or (result_status == "partial" and score >= 70)
            
            if is_passed:
                # Миссия пройдена - не показываем подсказки
                return []
        
        # Получаем проваленные проверки
        failed_checks = []
        if check_result:
            failed_checks = [
                c for c in check_result.get("checks", [])
                if not c.get("passed", False)
            ]
        
        # Если нет проваленных проверок и нет ошибок, но use_ml=True, все равно генерируем ML подсказки
        if not failed_checks and not error_message and not use_ml:
            return []
        
        # Получаем подсказки от rule-based системы
        rule_hint = self.rule_based.get_hint_for_error(
            error_message=error_message or "",
            command=command,
            check_result=check_result,
            mission_id=mission_id,
            level=level
        )
        
        if rule_hint:
            hints.append({
                "text": rule_hint,
                "source": "rule_based",
                "priority": 1
            })
        
        # Получаем подсказки от ML системы (если включено и есть проблемы)
        if use_ml and (failed_checks or error_message):
            try:
                # Загружаем конфигурацию миссии для ML
                import yaml
                from backend.config import settings
                mission_path = settings.MISSIONS_DIR / f"level_{level.lower()}" / mission_id
                config_file = mission_path / "mission.yaml"
                mission_config = {}
                if config_file.exists():
                    with open(config_file, 'r', encoding='utf-8') as f:
                        mission_config = yaml.safe_load(f) or {}
                
                # Вызываем async метод ML системы
                # Добавляем уровень в контекст для LLM
                if not mission_config.get("level"):
                    mission_config["level"] = level
                
                ml_hint = await self.ml_system.predict_hint(
                    mission_id=mission_id,
                    command=command,
                    error_message=error_message,
                    failed_checks=failed_checks,
                    mission_config=mission_config,
                    check_result=check_result,
                    os_type=os_type
                )
                
                if ml_hint:
                    hints.append({
                        "text": ml_hint,
                        "source": "ml",
                        "priority": 2
                    })
            except Exception as e:
                logger.warning(f"Ошибка получения ML подсказки: {e}", exc_info=True)
        
        # Если есть проваленные проверки, получаем специфичные подсказки
        if failed_checks:
            check_hints = self.rule_based.get_hints_for_failed_checks(failed_checks, level=level)
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

