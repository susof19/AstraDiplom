"""Роуты для работы с миссиями"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import yaml
from pathlib import Path

from backend.config import settings

router = APIRouter()


@router.get("/missions")
async def list_missions(level: str = None) -> List[Dict[str, Any]]:
    """Получить список всех миссий"""
    missions = []
    
    levels = ["a"] if not level else [level.lower()]
    
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
                        missions.append({
                            "id": mission_dir.name,
                            "level": level_dir.upper(),
                            **config
                        })
                except Exception as e:
                    continue
    
    return missions


@router.get("/missions/{mission_id}")
async def get_mission(mission_id: str) -> Dict[str, Any]:
    """Получить информацию о конкретной миссии"""
    # Ищем миссию в уровне A
    for level in ["a"]:
        mission_path = settings.MISSIONS_DIR / f"level_{level}" / mission_id
        config_file = mission_path / "mission.yaml"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    return {
                        "id": mission_id,
                        "level": level.upper(),
                        **config
                    }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Ошибка чтения конфигурации: {e}")
    
    raise HTTPException(status_code=404, detail=f"Миссия {mission_id} не найдена")

