"""Роуты для работы с прогрессом"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from backend.models.progress import get_user_progress
from backend.auth.dependencies import get_current_user

router = APIRouter()


@router.get("/progress")
async def get_progress(username: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Получить прогресс пользователя"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"✅ Получение прогресса для пользователя: {username}")
    progress = get_user_progress(username)
    return progress.get_stats()


@router.post("/progress/{mission_id}/complete")
async def complete_mission(
    mission_id: str,
    level: str,
    score: int,
    username: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Отметить миссию как выполненную"""
    if score < 0 or score > 100:
        raise HTTPException(status_code=400, detail="Оценка должна быть от 0 до 100")
    
    progress = get_user_progress(username)
    old_achievements = set(progress.achievements)
    progress.complete_mission(mission_id, level, score)
    new_achievements = set(progress.achievements) - old_achievements
    
    return {
        "status": "success",
        "mission_id": mission_id,
        "score": score,
        "total_score": progress.total_score,
        "new_achievements": list(new_achievements)
    }


@router.get("/progress/achievements")
async def get_achievements(username: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Получить список достижений"""
    progress = get_user_progress(username)
    
    achievement_names = {
        "first_mission": "Первая миссия",
        "perfect_score": "Идеальный результат",
        "level_a_master": "Мастер уровня A",
        "high_score": "Высокий счёт"
    }
    
    return {
        "achievements": [
            {
                "id": a,
                "name": achievement_names.get(a, a),
                "unlocked": True
            }
            for a in progress.achievements
        ],
        "total": len(progress.achievements)
    }

