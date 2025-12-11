"""Роуты для проверки миссий"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from backend.grader.checker import Grader
from backend.sandbox.manager import sandbox_manager
from backend.models.progress import get_user_progress
from backend.auth.dependencies import get_current_user

router = APIRouter()


@router.post("/grader/check/{mission_id}")
async def check_mission(
    mission_id: str, 
    level: str, 
    username: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Проверить выполнение миссии"""
    sandbox = await sandbox_manager.get_sandbox(mission_id)
    
    if not sandbox:
        raise HTTPException(status_code=404, detail="Песочница не найдена")
    
    result = await Grader.grade_mission(mission_id, level, sandbox)
    
    # Сохраняем прогресс, если миссия выполнена
    if result.get("result") in ["passed", "partial"]:
        score = result.get("score", 0)
        progress = get_user_progress(username)
        old_achievements = set(progress.achievements)
        progress.complete_mission(mission_id, level, score)
        new_achievements = set(progress.achievements) - old_achievements
        result["new_achievements"] = list(new_achievements)
    
    return result

