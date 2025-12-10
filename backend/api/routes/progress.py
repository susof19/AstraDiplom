"""Роуты для работы с прогрессом"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from backend.models.progress import get_user_progress

router = APIRouter()


@router.get("/progress")
async def get_progress(user_id: str = "default") -> Dict[str, Any]:
    """Получить прогресс пользователя"""
    progress = get_user_progress(user_id)
    return progress.get_stats()


@router.post("/progress/{mission_id}/complete")
async def complete_mission(
    mission_id: str,
    level: str,
    score: int,
    user_id: str = "default"
) -> Dict[str, Any]:
    """Отметить миссию как выполненную"""
    if score < 0 or score > 100:
        raise HTTPException(status_code=400, detail="Оценка должна быть от 0 до 100")
    
    progress = get_user_progress(user_id)
    progress.complete_mission(mission_id, level, score)
    
    return {
        "status": "success",
        "mission_id": mission_id,
        "score": score,
        "total_score": progress.total_score,
        "new_achievements": [
            a for a in progress.achievements 
            if a not in get_user_progress(user_id).achievements
        ]
    }


@router.get("/progress/achievements")
async def get_achievements(user_id: str = "default") -> Dict[str, Any]:
    """Получить список достижений"""
    progress = get_user_progress(user_id)
    
    achievement_names = {
        "first_mission": "Первая миссия",
        "perfect_score": "Идеальный результат",
        "level_a_master": "Мастер уровня A",
        "level_b_master": "Мастер уровня B",
        "level_c_master": "Мастер уровня C",
        "all_levels": "Универсал",
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

