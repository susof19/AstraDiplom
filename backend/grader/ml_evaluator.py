"""ML Evaluator - дополнительный слой оценки миссий поверх rule-based проверки"""
import logging
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from backend.config import settings

logger = logging.getLogger(__name__)


class MLEvaluator:
    """
    ML Evaluator - оценивает выполнение миссии по смыслу, а не только по правилам.
    
    Работает как дополнительный слой поверх rule-based проверки:
    - Если rule-based проверка пройдена -> возвращаем PASSED
    - Если rule-based проверка провалена -> ML оценивает, выполнена ли миссия по смыслу
    """
    
    def __init__(self):
        self.evaluation_cache = {}
        self.evaluation_data_file = Path(settings.SANDBOX_DATA_DIR) / "ml_evaluations.json"
        self._load_evaluation_data()
    
    def _load_evaluation_data(self):
        """Загрузить историю оценок для обучения"""
        if self.evaluation_data_file.exists():
            try:
                with open(self.evaluation_data_file, 'r', encoding='utf-8') as f:
                    self.evaluation_cache = json.load(f)
            except Exception as e:
                logger.error(f"Ошибка загрузки данных оценок: {e}")
                self.evaluation_cache = {}
        else:
            self.evaluation_cache = {}
    
    def _save_evaluation_data(self):
        """Сохранить историю оценок"""
        try:
            self.evaluation_data_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.evaluation_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.evaluation_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения данных оценок: {e}")
    
    async def evaluate(
        self,
        mission_id: str,
        mission_config: Dict[str, Any],
        check_results: List[Dict[str, Any]],
        sandbox_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Оценить выполнение миссии с помощью ML подхода.
        
        Args:
            mission_id: ID миссии
            mission_config: Конфигурация миссии из YAML
            check_results: Результаты rule-based проверок
            sandbox_context: Дополнительный контекст из песочницы
        
        Returns:
            dict с ключами:
            - score: float (0.0-1.0) - оценка выполнения по смыслу
            - reason: str - объяснение оценки
            - hint: Optional[str] - подсказка для улучшения
            - should_override: bool - следует ли переопределить rule-based результат
        """
        # Если все проверки пройдены, ML не нужен
        all_passed = all(c.get("passed", False) for c in check_results)
        if all_passed:
            return {
                "score": 1.0,
                "reason": "Все проверки пройдены",
                "hint": None,
                "should_override": False
            }
        
        # Анализируем проваленные проверки
        failed_checks = [c for c in check_results if not c.get("passed", False)]
        
        # Используем простую эвристическую оценку (можно заменить на LLM или более сложную модель)
        evaluation = self._heuristic_evaluation(
            mission_id=mission_id,
            mission_config=mission_config,
            failed_checks=failed_checks,
            passed_checks=[c for c in check_results if c.get("passed", False)],
            sandbox_context=sandbox_context
        )
        
        # Сохраняем оценку для обучения
        self._save_evaluation(mission_id, evaluation)
        
        return evaluation
    
    def _heuristic_evaluation(
        self,
        mission_id: str,
        mission_config: Dict[str, Any],
        failed_checks: List[Dict[str, Any]],
        passed_checks: List[Dict[str, Any]],
        sandbox_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Эвристическая оценка выполнения миссии.
        
        В будущем можно заменить на LLM-as-judge или обученную модель.
        """
        objectives = mission_config.get("objectives", [])
        total_checks = len(failed_checks) + len(passed_checks)
        passed_ratio = len(passed_checks) / total_checks if total_checks > 0 else 0
        
        # Базовый score на основе пройденных проверок
        base_score = passed_ratio
        
        # Анализируем типы проваленных проверок
        evaluation_reasons = []
        hints = []
        
        for check in failed_checks:
            check_type = check.get("type", "")
            check_name = check.get("name", "")
            check_message = check.get("message", "")
            
            # Анализ по типу проверки
            if check_type == "file_exists":
                # Файл не найден - проверяем, может быть похожий файл
                if "не найден" in check_message.lower():
                    # Частичный балл, если есть похожие файлы
                    base_score += 0.1
                    evaluation_reasons.append(f"Файл не найден: {check_name}")
                    hints.append(f"Проверьте путь к файлу. Используйте 'ls' для просмотра содержимого директории.")
            
            elif check_type == "file_content":
                # Содержимое не совпадает - может быть близко
                base_score += 0.15
                evaluation_reasons.append(f"Содержимое файла не соответствует: {check_name}")
                hints.append(f"Проверьте содержимое файла командой 'cat <файл>' и сравните с требованиями.")
            
            elif check_type == "command_output":
                # Команда не дала ожидаемый результат
                base_score += 0.1
                evaluation_reasons.append(f"Команда не дала ожидаемый результат: {check_name}")
                hints.append(f"Проверьте вывод команды и убедитесь, что он соответствует требованиям.")
        
        # Ограничиваем score в пределах [0, 1]
        final_score = min(max(base_score, 0.0), 1.0)
        
        # Формируем reason
        if evaluation_reasons:
            reason = f"Частичное выполнение: {', '.join(evaluation_reasons[:2])}"
            if len(evaluation_reasons) > 2:
                reason += f" и ещё {len(evaluation_reasons) - 2} проблем"
        else:
            reason = "Выполнение близко к успешному"
        
        # Выбираем наиболее релевантную подсказку
        hint = hints[0] if hints else None
        
        # Решаем, следует ли переопределить rule-based результат
        # Переопределяем только если score >= 0.7 (миссия выполнена по смыслу)
        should_override = final_score >= 0.7
        
        return {
            "score": final_score,
            "reason": reason,
            "hint": hint,
            "should_override": should_override,
            "evaluation_method": "heuristic"
        }
    
    def _save_evaluation(self, mission_id: str, evaluation: Dict[str, Any]):
        """Сохранить оценку для последующего обучения"""
        if mission_id not in self.evaluation_cache:
            self.evaluation_cache[mission_id] = []
        
        self.evaluation_cache[mission_id].append({
            "score": evaluation["score"],
            "reason": evaluation["reason"],
            "timestamp": json.dumps({"timestamp": "now"})  # Можно использовать datetime
        })
        
        # Ограничиваем размер истории
        if len(self.evaluation_cache[mission_id]) > 100:
            self.evaluation_cache[mission_id] = self.evaluation_cache[mission_id][-100:]
        
        self._save_evaluation_data()
    
    async def evaluate_with_llm(
        self,
        mission_id: str,
        mission_config: Dict[str, Any],
        check_results: List[Dict[str, Any]],
        sandbox_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Оценка с помощью LLM (будущая реализация).
        
        Можно использовать OpenAI API, локальную модель или другой LLM сервис.
        """
        # TODO: Реализовать LLM-as-judge подход
        # Пример промпта:
        # """
        # Ты — автоматический проверяющий учебных миссий Linux.
        # 
        # Цель миссии: {mission_config['description']}
        # 
        # Результаты проверок:
        # {check_results}
        # 
        # Вопрос: Выполнил ли пользователь миссию по смыслу?
        # Оцени выполнение от 0 до 1 и объясни почему.
        # """
        
        logger.warning("LLM evaluation not implemented yet, using heuristic")
        return await self.evaluate(mission_id, mission_config, check_results, sandbox_context)


def get_ml_evaluator() -> MLEvaluator:
    """Получить экземпляр ML evaluator"""
    return MLEvaluator()

