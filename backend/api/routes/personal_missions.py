"""Роуты для персональных миссий"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging
import yaml
from pathlib import Path

from backend.config import settings
from backend.missions.mission_generator import get_mission_generator
from backend.auth.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


class GenerateMissionRequest(BaseModel):
    """Запрос на генерацию миссии"""
    request: str  # Что пользователь хочет изучить
    level: str = "A"  # Уровень миссии (A или B)
    conversation_history: Optional[List[Dict[str, str]]] = None  # История диалога


class ChatMessage(BaseModel):
    """Сообщение в чате"""
    role: str  # user или assistant
    content: str


@router.post("/personal-missions/generate")
async def generate_personal_mission(
    request: GenerateMissionRequest,
    username: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Сгенерировать персональную миссию через LLM"""
    
    if request.level.upper() not in ["A", "B"]:
        raise HTTPException(status_code=400, detail="Уровень должен быть A или B")
    
    generator = get_mission_generator()
    
    result = await generator.generate_mission(
        user_request=request.request,
        username=username,
        level=request.level.upper(),
        conversation_history=request.conversation_history
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("message", "Ошибка генерации миссии")
        )
    
    # Сохраняем миссию
    mission_id = result["mission_id"]
    mission_config = result["mission_config"]
    
    try:
        saved = await save_personal_mission(username, mission_id, mission_config, request.level.upper())
        if not saved:
            raise HTTPException(status_code=500, detail="Не удалось сохранить миссию")
    except Exception as e:
        logger.error(f"Ошибка сохранения миссии: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения миссии: {str(e)}")
    
    return {
        "success": True,
        "mission_id": mission_id,
        "message": result.get("message", "Миссия успешно создана!"),
        "mission": {
            "id": mission_id,
            "level": request.level.upper(),
            **mission_config
        }
    }


@router.post("/personal-missions/chat")
async def chat_for_mission(
    messages: List[ChatMessage],
    username: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Чат с LLM для уточнения требований к миссии"""
    
    generator = get_mission_generator()
    
    # Преобразуем сообщения в формат для генератора
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]
    
    # Последнее сообщение - это запрос пользователя
    if not messages:
        raise HTTPException(status_code=400, detail="Нет сообщений в запросе")
    
    last_message = messages[-1]
    if last_message.role != "user":
        raise HTTPException(status_code=400, detail="Последнее сообщение должно быть от пользователя")
    
    # Определяем уровень из контекста или используем A по умолчанию
    level = "A"
    for msg in reversed(messages):
        if "уровень" in msg.content.lower() or "level" in msg.content.lower():
            if "b" in msg.content.lower() or "терминал" in msg.content.lower():
                level = "B"
            break
    
    # Генерируем ответ через LLM
    response = await generator._generate_with_lm_studio(
        last_message.content,
        conversation_history[:-1]  # Без последнего сообщения, оно будет в промпте
    )
    
    if not response:
        # Fallback на другие провайдеры
        if generator.provider_type == 'ollama':
            response = await generator._generate_with_ollama(
                last_message.content,
                conversation_history[:-1]
            )
        elif generator.provider_type == 'openai':
            response = await generator._generate_with_openai(
                last_message.content,
                conversation_history[:-1]
            )
    
    if not response:
        response = "Извините, не удалось обработать запрос. Попробуйте переформулировать."
    
    return {
        "message": response,
        "role": "assistant"
    }


@router.get("/personal-missions")
async def list_personal_missions(
    username: str = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Получить список персональных миссий пользователя"""
    
    personal_missions_dir = settings.MISSIONS_DIR / "personal" / username
    missions = []
    
    if not personal_missions_dir.exists():
        return missions
    
    for mission_dir in personal_missions_dir.iterdir():
        if not mission_dir.is_dir():
            continue
        
        config_file = mission_dir / "mission.yaml"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    if not config:
                        continue
                    
                    mission_data = {
                        "id": mission_dir.name,
                        "level": config.get("level", "A"),
                        "is_personal": True,
                        "owner": username,
                        **config
                    }
                    missions.append(mission_data)
            except Exception as e:
                logger.error(f"Ошибка загрузки персональной миссии {mission_dir.name}: {e}")
                continue
    
    return missions


@router.delete("/personal-missions/{mission_id}")
async def delete_personal_mission(
    mission_id: str,
    username: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Удалить персональную миссию"""
    
    if not mission_id.startswith(f"personal_{username}_"):
        raise HTTPException(status_code=403, detail="Вы можете удалять только свои миссии")
    
    mission_path = settings.MISSIONS_DIR / "personal" / username / mission_id
    
    if not mission_path.exists():
        raise HTTPException(status_code=404, detail="Миссия не найдена")
    
    try:
        import shutil
        shutil.rmtree(mission_path)
        return {
            "success": True,
            "message": "Миссия удалена"
        }
    except Exception as e:
        logger.error(f"Ошибка удаления миссии: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка удаления: {str(e)}")


async def save_personal_mission(
    username: str,
    mission_id: str,
    mission_config: Dict[str, Any],
    level: str
) -> bool:
    """Сохранить персональную миссию в файловую систему"""
    try:
        # Создаем директорию для персональных миссий пользователя
        personal_missions_dir = settings.MISSIONS_DIR / "personal" / username
        personal_missions_dir.mkdir(parents=True, exist_ok=True)
        
        # Создаем директорию для конкретной миссии
        mission_dir = personal_missions_dir / mission_id
        mission_dir.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем конфигурацию
        config_file = mission_dir / "mission.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(mission_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Персональная миссия {mission_id} сохранена для пользователя {username}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка сохранения персональной миссии: {e}", exc_info=True)
        return False
