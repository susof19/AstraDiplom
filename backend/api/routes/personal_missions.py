"""Роуты для персональных миссий"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging
import yaml
from pathlib import Path
import re
from difflib import SequenceMatcher

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


def _normalize_text(text: str) -> str:
    """Нормализация текста для сравнения"""
    if not text:
        return ""
    # Приводим к нижнему регистру и убираем лишние пробелы
    text = text.lower().strip()
    # Убираем знаки препинания
    text = re.sub(r'[^\w\s]', ' ', text)
    # Убираем множественные пробелы
    text = re.sub(r'\s+', ' ', text)
    return text


def _calculate_similarity(text1: str, text2: str) -> float:
    """Вычисляет схожесть двух текстов (0.0 - 1.0)"""
    if not text1 or not text2:
        return 0.0
    
    norm1 = _normalize_text(text1)
    norm2 = _normalize_text(text2)
    
    if not norm1 or not norm2:
        return 0.0
    
    # Используем SequenceMatcher для вычисления схожести
    similarity = SequenceMatcher(None, norm1, norm2).ratio()
    
    # Также проверяем наличие ключевых слов
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if words1 and words2:
        # Вычисляем долю общих слов
        common_words = words1.intersection(words2)
        word_similarity = len(common_words) / max(len(words1), len(words2))
        # Комбинируем метрики
        similarity = max(similarity, word_similarity * 0.8)
    
    return similarity


async def _find_similar_mission(
    user_request: str,
    level: str,
    username: str
) -> Optional[Dict[str, Any]]:
    """Найти похожую существующую миссию"""
    normalized_request = _normalize_text(user_request)
    
    # Извлекаем ключевые слова из запроса
    request_words = set(normalized_request.split())
    # Убираем стоп-слова
    stop_words = {"хочу", "научиться", "научить", "создать", "создавать", "на", "в", "с", "из", "по", "как", "что"}
    request_keywords = request_words - stop_words
    
    best_match = None
    best_similarity = 0.0
    threshold = 0.6  # Порог схожести (60%)
    
    # Проверяем стандартные миссии
    for level_dir in ["a", "b"]:
        level_path = settings.MISSIONS_DIR / f"level_{level_dir}"
        if not level_path.exists():
            continue
        
        for mission_dir in level_path.iterdir():
            if not mission_dir.is_dir():
                continue
            
            config_file = mission_dir / "mission.yaml"
            if not config_file.exists():
                continue
            
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    if not config:
                        continue
                    
                    # Проверяем схожесть с названием
                    name_sim = _calculate_similarity(user_request, config.get("name", ""))
                    
                    # Проверяем схожесть с описанием
                    desc_sim = _calculate_similarity(user_request, config.get("description", ""))
                    
                    # Проверяем схожесть с целями
                    objectives = config.get("objectives", [])
                    obj_text = " ".join(str(obj) for obj in objectives)
                    obj_sim = _calculate_similarity(user_request, obj_text)
                    
                    # Вычисляем общую схожесть (максимум из всех метрик)
                    total_similarity = max(name_sim, desc_sim, obj_sim)
                    
                    # Дополнительная проверка по ключевым словам
                    mission_text = f"{config.get('name', '')} {config.get('description', '')} {obj_text}"
                    mission_words = set(_normalize_text(mission_text).split())
                    mission_keywords = mission_words - stop_words
                    
                    if request_keywords and mission_keywords:
                        keyword_match = len(request_keywords.intersection(mission_keywords)) / len(request_keywords)
                        total_similarity = max(total_similarity, keyword_match * 0.9)
                    
                    if total_similarity > best_similarity and total_similarity >= threshold:
                        best_similarity = total_similarity
                        best_match = {
                            "id": mission_dir.name,
                            "level": level_dir.upper(),
                            "is_personal": False,
                            "similarity": total_similarity,
                            **config
                        }
            except Exception as e:
                logger.warning(f"Ошибка при проверке миссии {mission_dir.name}: {e}")
                continue
    
    # Проверяем персональные миссии пользователя
    personal_missions_dir = settings.MISSIONS_DIR / "personal" / username
    if personal_missions_dir.exists():
        for mission_dir in personal_missions_dir.iterdir():
            if not mission_dir.is_dir():
                continue
            
            config_file = mission_dir / "mission.yaml"
            if not config_file.exists():
                continue
            
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    if not config:
                        continue
                    
                    mission_level = config.get("level", "A").upper()
                    # Проверяем только миссии того же уровня
                    if mission_level != level.upper():
                        continue
                    
                    # Проверяем схожесть
                    name_sim = _calculate_similarity(user_request, config.get("name", ""))
                    desc_sim = _calculate_similarity(user_request, config.get("description", ""))
                    objectives = config.get("objectives", [])
                    obj_text = " ".join(str(obj) for obj in objectives)
                    obj_sim = _calculate_similarity(user_request, obj_text)
                    
                    total_similarity = max(name_sim, desc_sim, obj_sim)
                    
                    if total_similarity > best_similarity and total_similarity >= threshold:
                        best_similarity = total_similarity
                        best_match = {
                            "id": mission_dir.name,
                            "level": mission_level,
                            "is_personal": True,
                            "owner": username,
                            "similarity": total_similarity,
                            **config
                        }
            except Exception as e:
                logger.warning(f"Ошибка при проверке персональной миссии {mission_dir.name}: {e}")
                continue
    
    return best_match


@router.post("/personal-missions/generate")
async def generate_personal_mission(
    request: GenerateMissionRequest,
    username: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Сгенерировать персональную миссию через LLM"""
    
    if request.level.upper() not in ["A", "B"]:
        raise HTTPException(status_code=400, detail="Уровень должен быть A или B")
    
    # Проверяем, нет ли уже похожей миссии
    similar_mission = await _find_similar_mission(
        request.request,
        request.level.upper(),
        username
    )
    
    if similar_mission:
        similarity_percent = int(similar_mission.get("similarity", 0) * 100)
        logger.info(f"Найдена похожая миссия {similar_mission['id']} (схожесть: {similarity_percent}%)")
        
        return {
            "success": True,
            "mission_id": similar_mission["id"],
            "message": f"Найдена похожая миссия! (схожесть: {similarity_percent}%)",
            "mission": similar_mission,
            "is_existing": True,
            "similarity": similarity_percent
        }
    
    # Если похожей миссии нет, генерируем новую
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
        },
        "is_existing": False
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
    
    # Генерируем ответ через LLM для чата (без YAML)
    response = await generator._generate_chat_response(
        last_message.content,
        conversation_history[:-1],  # Без последнего сообщения, оно будет в промпте
        level
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
