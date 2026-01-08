"""API endpoints для системы подсказок"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, List, Any, Optional
import logging

from backend.hints.hint_system import get_hint_system
from backend.hints.action_tracker import get_action_tracker
from backend.sandbox.manager import sandbox_manager
from backend.auth.dependencies import get_current_user
from backend.models.progress import get_user_progress
from backend.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def _detect_os_from_image(image: Optional[str]) -> str:
    """Определить тип ОС из образа контейнера"""
    if not image:
        return "linux"  # По умолчанию
    
    image_lower = image.lower()
    
    # Определяем по названию образа
    if "astra" in image_lower:
        return "astra_linux"
    elif "ubuntu" in image_lower:
        return "ubuntu"
    elif "debian" in image_lower:
        return "debian"
    elif "fedora" in image_lower:
        return "fedora"
    elif "centos" in image_lower or "rhel" in image_lower:
        return "rhel"
    else:
        return "linux"  # Общий Linux


@router.get("/hints/check/{mission_id}")
async def get_hints_for_mission(
    mission_id: str,
    use_ml: bool = Query(True, description="Использовать ML подсказки"),
    username: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Получить подсказки для миссии на основе текущего состояния (во время прохождения)"""
    hint_system = get_hint_system()
    
    # Получаем песочницу для миссии
    sandbox = await sandbox_manager.get_sandbox(mission_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Песочница не найдена. Запустите песочницу для получения подсказок.")
    
    # Получаем прогресс пользователя для определения уровня
    progress = get_user_progress(username)
    
    # Определяем уровень миссии
    level = sandbox.level or "A"
    
    # Определяем ОС из образа песочницы
    os_type = _detect_os_from_image(sandbox.image if hasattr(sandbox, 'image') else None)
    
    # Загружаем конфигурацию миссии для контекста
    import yaml
    from backend.config import settings
    mission_path = settings.MISSIONS_DIR / f"level_{level.lower()}" / mission_id
    config_file = mission_path / "mission.yaml"
    mission_config = {}
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            mission_config = yaml.safe_load(f) or {}
    
    # Получаем последние действия пользователя для контекста
    tracker = get_action_tracker(username)
    recent_actions = [a for a in tracker.actions if a.get("mission_id") == mission_id][-5:]  # Последние 5 действий
    
    # Всегда генерируем подсказки на основе целей миссии
    context_hints = []
    
    # Сначала проверяем, есть ли неудачные действия
    if recent_actions:
        failed_actions = [a for a in recent_actions if not a.get("result", {}).get("success", True)]
        if failed_actions:
            last_failed = failed_actions[-1]
            error_msg = last_failed.get("error") or f"Действие не выполнено: {last_failed.get('action_type', 'unknown')}"
            
            # Получаем подсказки на основе последних ошибок
            try:
                hints = await hint_system.get_hints(
                    username=username,
                    mission_id=mission_id,
                    level=level,
                    error_message=error_msg,
                    command=last_failed.get("command"),
                    check_result=None,
                    use_ml=use_ml,
                    os_type=os_type
                )
                if hints:
                    context_hints = hints
            except Exception as e:
                logger.warning(f"Ошибка получения подсказок на основе ошибок: {e}")
    
    # Если нет контекстных подсказок или use_ml=True, получаем общие ML подсказки для миссии
    if use_ml:
        try:
            # Получаем подсказки на основе целей миссии
            # Используем описание миссии как контекст
            mission_description = mission_config.get("description", "")
            objectives = mission_config.get("objectives", [])
            
            # Формируем контекст для генерации подсказок
            context_message = None
            if mission_description:
                context_message = f"Задача: {mission_description}"
            if objectives:
                context_message = (context_message or "") + f" Цели: {', '.join(objectives[:3])}"
            
            hints = await hint_system.get_hints(
                username=username,
                mission_id=mission_id,
                level=level,
                error_message=context_message,
                command=None,
                check_result={
                    "checks": [],
                    "result": "in_progress",
                    "level": level
                },
                use_ml=True,  # Всегда используем ML для realtime подсказок
                os_type=os_type
            )
            
            # Добавляем ML подсказки к существующим (если есть)
            if hints:
                # Фильтруем дубликаты
                existing_texts = set(context_hints)
                unique_hints = [h for h in hints if h not in existing_texts]
                context_hints.extend(unique_hints)
                
        except Exception as e:
            logger.error(f"Ошибка получения ML подсказок: {e}", exc_info=True)
    
    # Логируем для отладки
    logger.debug(f"Сгенерировано {len(context_hints)} подсказок для миссии {mission_id}, use_ml={use_ml}")
    
    return {
        "mission_id": mission_id,
        "hints": context_hints,
        "hints_enabled": True,
        "ml_enabled": use_ml,
        "realtime": True,
        "recent_actions_count": len(recent_actions)
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
    
    # Проверяем, пройдена ли миссия
    result_status = check_result.get("result", "failed")
    score = check_result.get("score", 0)
    is_passed = result_status == "passed" or (result_status == "partial" and score >= 70)
    
    # Если миссия пройдена, не возвращаем подсказки
    if is_passed:
        return {
            "mission_id": mission_id,
            "hints": [],
            "failed_checks_count": 0,
            "ml_enabled": use_ml,
            "mission_passed": True
        }
    
    # Определяем уровень
    level = check_result.get("level") or "A"
    
    # Извлекаем информацию об ошибках
    failed_checks = [
        c for c in check_result.get("checks", [])
        if not c.get("passed", False)
    ]
    
    error_messages = [c.get("message", "") for c in failed_checks]
    combined_error = " ".join(error_messages)
    
    # Определяем ОС из песочницы
    sandbox = await sandbox_manager.get_sandbox(mission_id)
    os_type = _detect_os_from_image(sandbox.image if sandbox and hasattr(sandbox, 'image') else None)
    
    # Получаем подсказки
    hints = await hint_system.get_hints(
        username=username,
        mission_id=mission_id,
        level=level,
        error_message=combined_error if combined_error else None,
        command=command,
        check_result={
            "checks": failed_checks,
            "result": check_result.get("result", "failed"),
            "score": score,
            "level": level
        },
        use_ml=use_ml,
        os_type=os_type
    )
    
    # Отслеживаем результат для обучения
    hint_system.track_and_learn(
        username=username,
        mission_id=mission_id,
        level=level,
        command=command,
        check_result=check_result,
        success=False  # Миссия не пройдена, раз мы здесь
    )
    
    return {
        "mission_id": mission_id,
        "hints": hints,
        "failed_checks_count": len(failed_checks),
        "ml_enabled": use_ml,
        "mission_passed": False
    }


@router.post("/hints/track-command")
async def track_command(
    mission_id: str,
    command: str,
    exit_code: int,
    level: Optional[str] = Query("A", description="Уровень миссии"),
    username: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Отследить выполнение команды пользователем и получить подсказки в реальном времени"""
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
        hints = await hint_system.get_hints(
            username=username,
            mission_id=mission_id,
            level=level,
            error_message=f"Команда завершилась с кодом {exit_code}",
            command=command,
            use_ml=True
        )
    
    return {
        "tracked": True,
        "hints": hints if exit_code != 0 else [],
        "realtime": True
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
