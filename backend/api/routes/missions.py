"""Роуты для работы с миссиями"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import yaml
import logging
from pathlib import Path

from backend.config import settings
from backend.models.progress import get_user_progress
from backend.auth.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/missions")
async def list_missions(
    level: str = None,
    username: str = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Получить список всех миссий с информацией о прогрессе пользователя"""
    missions = []
    
    # Получаем прогресс пользователя для отображения статуса миссий
    progress = get_user_progress(username)
    user_missions = progress.missions_completed
    
    levels = ["a", "b"] if not level else [level.lower()]
    
    # Загружаем стандартные миссии
    for level_dir in levels:
        level_path = settings.MISSIONS_DIR / f"level_{level_dir}"
        if not level_path.exists():
            continue
        
        for mission_dir in level_path.iterdir():
            if not mission_dir.is_dir():
                continue
            
            config_file = mission_dir / "mission.yaml"
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                        if not config:
                            logger.warning(f"Пустой конфиг для миссии {mission_dir.name} в уровне {level_dir}")
                            continue
                        mission_id = mission_dir.name
                        
                        # Добавляем информацию о прогрессе пользователя
                        mission_data = {
                            "id": mission_id,
                            "level": level_dir.upper(),
                            "is_personal": False,
                            **config
                        }
                        
                        # Если миссия пройдена, добавляем информацию о статусе
                        if mission_id in user_missions:
                            mission_info = user_missions[mission_id]
                            mission_data["completed"] = True
                            mission_data["score"] = mission_info.get("score", 0)
                            mission_data["completed_at"] = mission_info.get("completed_at")
                            mission_data["attempts"] = mission_info.get("attempts", 1)
                        else:
                            mission_data["completed"] = False
                            mission_data["score"] = None
                        
                        missions.append(mission_data)
                except Exception as e:
                    logger.error(f"Ошибка загрузки миссии {mission_dir.name} из уровня {level_dir}: {e}", exc_info=True)
                    continue
    
    # Загружаем персональные миссии пользователя
    personal_missions_dir = settings.MISSIONS_DIR / "personal" / username
    if personal_missions_dir.exists():
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
                        
                        mission_id = mission_dir.name
                        mission_level = config.get("level", "A").lower()
                        
                        # Фильтруем по уровню, если указан
                        if level and mission_level != level.lower():
                            continue
                        
                        mission_data = {
                            "id": mission_id,
                            "level": mission_level.upper(),
                            "is_personal": True,
                            "owner": username,
                            **config
                        }
                        
                        # Если миссия пройдена, добавляем информацию о статусе
                        if mission_id in user_missions:
                            mission_info = user_missions[mission_id]
                            mission_data["completed"] = True
                            mission_data["score"] = mission_info.get("score", 0)
                            mission_data["completed_at"] = mission_info.get("completed_at")
                            mission_data["attempts"] = mission_info.get("attempts", 1)
                        else:
                            mission_data["completed"] = False
                            mission_data["score"] = None
                        
                        missions.append(mission_data)
                except Exception as e:
                    logger.error(f"Ошибка загрузки персональной миссии {mission_dir.name}: {e}", exc_info=True)
                    continue
    
    return missions


@router.get("/missions/{mission_id}")
async def get_mission(
    mission_id: str,
    username: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Получить информацию о конкретной миссии"""
    # Ищем миссию в уровнях A и B
    for level in ["a", "b"]:
        mission_path = settings.MISSIONS_DIR / f"level_{level}" / mission_id
        config_file = mission_path / "mission.yaml"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    return {
                        "id": mission_id,
                        "level": level.upper(),
                        "is_personal": False,
                        **config
                    }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Ошибка чтения конфигурации: {e}")
    
    # Ищем в персональных миссиях пользователя
    if mission_id.startswith(f"personal_{username}_"):
        personal_mission_path = settings.MISSIONS_DIR / "personal" / username / mission_id
        config_file = personal_mission_path / "mission.yaml"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    return {
                        "id": mission_id,
                        "level": config.get("level", "A"),
                        "is_personal": True,
                        "owner": username,
                        **config
                    }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Ошибка чтения конфигурации: {e}")
    
    raise HTTPException(status_code=404, detail=f"Миссия {mission_id} не найдена")

