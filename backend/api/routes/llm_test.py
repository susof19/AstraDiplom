"""API endpoint для тестирования LLM подключения"""
from fastapi import APIRouter, Depends
from typing import Dict, Any
import logging

from backend.hints.llm_hints import get_llm_hint_provider
from backend.auth.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/llm/test")
async def test_llm_connection(
    username: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Проверить подключение к LLM сервису"""
    provider = get_llm_hint_provider()
    result = await provider.test_connection()
    
    # Попробуем также сделать тестовый запрос, если подключение успешно
    if result.get("connected") and provider.provider_type == "lm_studio":
        try:
            test_hint = await provider.get_hint(
                mission_id="test",
                mission_config={
                    "description": "Тестовая миссия",
                    "objectives": ["Проверить работу подсказок"],
                    "level": "A"
                },
                failed_checks=[{
                    "name": "Тест",
                    "message": "Тестовая ошибка",
                    "type": "test"
                }],
                check_result={"result": "failed"},
                context={"level": "A"}
            )
            result["test_hint"] = test_hint
            result["test_success"] = bool(test_hint)
        except Exception as e:
            logger.error(f"Ошибка тестового запроса: {e}", exc_info=True)
            result["test_error"] = str(e)
            result["test_success"] = False
    
    return result
