"""API endpoints для системы подсказок"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, List, Any, Optional

from backend.hints.hint_system import get_hint_system
from backend.hints.action_tracker import get_action_tracker
from backend.sandbox.manager import sandbox_manager
from backend.auth.dependencies import get_current_user
from backend.models.progress import get_user_progress

router = APIRouter()


@router.get("/hints/check/{mission_id}")
async def get_hints_for_mission(
    mission_id: str,
    use_ml: bool = Query(True, description="Использовать ML подсказки"),
    username: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Получить подсказки для миссии на основе текущего состояния"""
    hint_system = get_hint_system()
    
    # Получаем песочницу для миссии
    sandbox = await sandbox_manager.get_sandbox(mission_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Песочница не найдена. Запустите песочницу для получения подсказок.")
    
    # Получаем прогресс пользователя для определения уровня
    progress = get_user_progress(username)
    
    # Определяем уровень миссии (можно улучшить, загрузив конфиг миссии)
    level = sandbox.level or "A"
    
    # Получаем подсказки
    hints = hint_system.get_hints(
        username=username,
        mission_id=mission_id,
        level=level,
        use_ml=use_ml
    )
    
    return {
        "mission_id": mission_id,
        "hints": hints,
        "hints_enabled": True,
        "ml_enabled": use_ml
    }


@router.post("/hints/check-result/{mission_id}")
async def get_hints_for_check_result(
    mission_id: str,
    check_result: Dict[str, Any],
    command: Optional[str] = Query(None, description="Последняя выполненная команда"),
    use_ml: bool = Query(True, description="Использовать ML подсказки"),
    username: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Получить подсказки на основе результата проверки миссии"""
    hint_system = get_hint_system()
    
    # Определяем уровень
    level = check_result.get("level") or "A"
    
    # Извлекаем информацию об ошибках
    failed_checks = [
        c for c in check_result.get("checks", [])
        if not c.get("passed", False)
    ]
    
    error_messages = [c.get("message", "") for c in failed_checks]
    combined_error = " ".join(error_messages)
    
    # Получаем подсказки
    hints = hint_system.get_hints(
        username=username,
        mission_id=mission_id,
        level=level,
        error_message=combined_error if combined_error else None,
        command=command,
        check_result={
            "checks": failed_checks,
            "result": check_result.get("result", "failed"),
            "level": level
        },
        use_ml=use_ml
    )
    
    # Отслеживаем результат для обучения
    is_success = check_result.get("result") == "passed" or check_result.get("score", 0) >= 70
    hint_system.track_and_learn(
        username=username,
        mission_id=mission_id,
        level=level,
        command=command,
        check_result=check_result,
        success=is_success
    )
    
    return {
        "mission_id": mission_id,
        "hints": hints,
        "failed_checks_count": len(failed_checks),
        "ml_enabled": use_ml
    }


@router.post("/hints/track-command")
async def track_command(
    mission_id: str,
    command: str,
    exit_code: int,
    level: Optional[str] = Query("A", description="Уровень миссии"),
    username: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Отследить выполнение команды пользователем"""
    tracker = get_action_tracker(username)
    
    tracker.track_command(
        mission_id=mission_id,
        level=level,
        command=command,
        exit_code=exit_code,
        output=""  # Можно добавить вывод команды, если нужно
    )
    
    # Получаем подсказки, если команда завершилась с ошибкой
    hints = []
    if exit_code != 0:
        hint_system = get_hint_system()
        hints = hint_system.get_hints(
            username=username,
            mission_id=mission_id,
            level=level,
            error_message=f"Команда завершилась с кодом {exit_code}",
            command=command,
            use_ml=True
        )
    
    return {
        "tracked": True,
        "hints": hints if exit_code != 0 else []
    }


@router.get("/hints/settings")
async def get_hint_settings(
    username: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Получить настройки подсказок пользователя"""
    progress = get_user_progress(username)
    
    # Получаем настройки из прогресса (можно добавить отдельную таблицу настроек)
    hints_enabled = progress.user_data.get("hints_enabled", True)
    ml_enabled = progress.user_data.get("ml_hints_enabled", True)
    
    return {
        "hints_enabled": hints_enabled,
        "ml_enabled": ml_enabled
    }


@router.post("/hints/settings")
async def update_hint_settings(
    hints_enabled: bool = Query(True, description="Включить/выключить подсказки"),
    ml_enabled: bool = Query(True, description="Включить/выключить ML подсказки"),
    username: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Обновить настройки подсказок пользователя"""
    progress = get_user_progress(username)
    
    # Сохраняем настройки в user_data
    if "user_data" not in progress.__dict__:
        progress.user_data = {}
    
    progress.user_data["hints_enabled"] = hints_enabled
    progress.user_data["ml_hints_enabled"] = ml_enabled
    
    progress.save()
    
    return {
        "hints_enabled": hints_enabled,
        "ml_enabled": ml_enabled,
        "updated": True
    }


@router.get("/hints/stats")
async def get_hint_statistics(
    username: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Получить статистику по подсказкам и действиям пользователя"""
    tracker = get_action_tracker(username)
    ml_system = get_hint_system().ml_system
    
    # Статистика модели
    ml_stats = ml_system.get_statistics()
    
    # Статистика пользователя
    user_patterns = tracker.get_user_patterns()
    
    return {
        "ml_model": ml_stats,
        "user_actions": {
            "total": user_patterns.get("total_actions", 0),
            "successful_patterns": len(user_patterns.get("successful_patterns", [])),
            "failed_patterns": len(user_patterns.get("failed_patterns", []))
        }
    }

