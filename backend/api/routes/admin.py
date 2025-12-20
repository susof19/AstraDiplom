"""Роуты для администратора - управление миссиями"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Dict, Any, Optional, List
import yaml
import logging
import shutil
from pathlib import Path

from backend.config import settings
from backend.auth.dependencies import get_admin_user, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/missions")
async def create_mission(
    mission_id: str = Form(...),
    level: str = Form(...),
    name: str = Form(...),
    description: str = Form(...),
    difficulty: int = Form(1),
    estimated_time: int = Form(5),
    objectives: str = Form(...),  # JSON строка
    hints: Optional[str] = Form(None),  # JSON строка (опционально)
    setup: Optional[str] = Form(None),  # YAML строка (опционально)
    checks: str = Form(...),  # JSON строка
    username: str = Depends(get_admin_user)
) -> Dict[str, Any]:
    """Создать новую миссию"""
    import json
    
    # Валидация уровня
    if level.upper() not in ["A", "B", "C"]:
        raise HTTPException(status_code=400, detail="Уровень должен быть A, B или C")
    
    level_dir = level.lower()
    mission_path = settings.MISSIONS_DIR / f"level_{level_dir}" / mission_id
    
    # Проверка, что миссия с таким ID не существует
    if mission_path.exists():
        raise HTTPException(status_code=400, detail=f"Миссия с ID {mission_id} уже существует")
    
    try:
        # Создаем директорию для миссии
        mission_path.mkdir(parents=True, exist_ok=True)
        
        # Парсим JSON строки
        objectives_list = json.loads(objectives)
        checks_list = json.loads(checks)
        hints_list = json.loads(hints) if hints else []
        
        # Формируем конфигурацию миссии
        mission_config = {
            "name": name,
            "description": description,
            "level": level.upper(),
            "difficulty": difficulty,
            "estimated_time": estimated_time,
            "objectives": objectives_list,
            "hints": hints_list,
        }
        
        # Добавляем setup если есть (может быть как JSON так и YAML)
        if setup:
            try:
                # Сначала пробуем как JSON
                setup_config = json.loads(setup)
            except json.JSONDecodeError:
                # Если не JSON, пробуем как YAML
                setup_config = yaml.safe_load(setup)
            if setup_config:
                mission_config["setup"] = setup_config
        
        # Добавляем checks
        mission_config["checks"] = checks_list
        
        # Сохраняем конфигурацию
        config_file = mission_path / "mission.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(mission_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Миссия {mission_id} создана администратором {username}")
        
        return {
            "status": "success",
            "message": f"Миссия {mission_id} успешно создана",
            "mission_id": mission_id,
            "level": level.upper()
        }
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Ошибка парсинга JSON: {e}")
    except Exception as e:
        logger.error(f"Ошибка создания миссии {mission_id}: {e}", exc_info=True)
        # Удаляем директорию в случае ошибки
        if mission_path.exists():
            shutil.rmtree(mission_path)
        raise HTTPException(status_code=500, detail=f"Ошибка создания миссии: {e}")


@router.put("/missions/{mission_id}")
async def update_mission(
    mission_id: str,
    level: str = Form(...),
    name: str = Form(...),
    description: str = Form(...),
    difficulty: int = Form(1),
    estimated_time: int = Form(5),
    objectives: str = Form(...),
    hints: Optional[str] = Form(None),
    setup: Optional[str] = Form(None),
    checks: str = Form(...),
    username: str = Depends(get_admin_user)
) -> Dict[str, Any]:
    """Обновить существующую миссию"""
    import json
    
    level_dir = level.lower()
    mission_path = settings.MISSIONS_DIR / f"level_{level_dir}" / mission_id
    config_file = mission_path / "mission.yaml"
    
    if not config_file.exists():
        raise HTTPException(status_code=404, detail=f"Миссия {mission_id} не найдена")
    
    try:
        # Парсим JSON строки
        objectives_list = json.loads(objectives)
        checks_list = json.loads(checks)
        hints_list = json.loads(hints) if hints else []
        
        # Формируем конфигурацию миссии
        mission_config = {
            "name": name,
            "description": description,
            "level": level.upper(),
            "difficulty": difficulty,
            "estimated_time": estimated_time,
            "objectives": objectives_list,
            "hints": hints_list,
        }
        
        # Добавляем setup если есть (может быть как JSON так и YAML)
        if setup:
            try:
                # Сначала пробуем как JSON
                setup_config = json.loads(setup)
            except json.JSONDecodeError:
                # Если не JSON, пробуем как YAML
                setup_config = yaml.safe_load(setup)
            if setup_config:
                mission_config["setup"] = setup_config
        
        # Добавляем checks
        mission_config["checks"] = checks_list
        
        # Сохраняем конфигурацию (создаем backup)
        backup_file = config_file.with_suffix('.yaml.backup')
        if config_file.exists():
            shutil.copy2(config_file, backup_file)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(mission_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Миссия {mission_id} обновлена администратором {username}")
        
        return {
            "status": "success",
            "message": f"Миссия {mission_id} успешно обновлена",
            "mission_id": mission_id,
            "level": level.upper()
        }
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Ошибка парсинга JSON: {e}")
    except Exception as e:
        logger.error(f"Ошибка обновления миссии {mission_id}: {e}", exc_info=True)
        # Восстанавливаем backup в случае ошибки
        if backup_file.exists() and config_file.exists():
            shutil.copy2(backup_file, config_file)
        raise HTTPException(status_code=500, detail=f"Ошибка обновления миссии: {e}")


@router.delete("/missions/{mission_id}")
async def delete_mission(
    mission_id: str,
    level: str,
    username: str = Depends(get_admin_user)
) -> Dict[str, Any]:
    """Удалить миссию"""
    level_dir = level.lower()
    mission_path = settings.MISSIONS_DIR / f"level_{level_dir}" / mission_id
    
    if not mission_path.exists():
        raise HTTPException(status_code=404, detail=f"Миссия {mission_id} не найдена")
    
    try:
        # Удаляем директорию миссии
        shutil.rmtree(mission_path)
        
        logger.info(f"Миссия {mission_id} удалена администратором {username}")
        
        return {
            "status": "success",
            "message": f"Миссия {mission_id} успешно удалена"
        }
    except Exception as e:
        logger.error(f"Ошибка удаления миссии {mission_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка удаления миссии: {e}")


@router.post("/missions/{mission_id}/files")
async def upload_mission_file(
    mission_id: str,
    level: str = Form(...),
    file: UploadFile = File(...),
    username: str = Depends(get_admin_user)
) -> Dict[str, Any]:
    """Загрузить файл для миссии (например, изображения, документы и т.д.)"""
    level_dir = level.lower()
    mission_path = settings.MISSIONS_DIR / f"level_{level_dir}" / mission_id
    
    if not mission_path.exists():
        raise HTTPException(status_code=404, detail=f"Миссия {mission_id} не найдена")
    
    try:
        # Сохраняем файл
        file_path = mission_path / file.filename
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(file.file, f)
        
        logger.info(f"Файл {file.filename} загружен для миссии {mission_id} администратором {username}")
        
        return {
            "status": "success",
            "message": f"Файл {file.filename} успешно загружен",
            "filename": file.filename,
            "path": str(file_path.relative_to(settings.MISSIONS_DIR))
        }
    except Exception as e:
        logger.error(f"Ошибка загрузки файла для миссии {mission_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки файла: {e}")


@router.delete("/missions/{mission_id}/files/{filename}")
async def delete_mission_file(
    mission_id: str,
    level: str,
    filename: str,
    username: str = Depends(get_admin_user)
) -> Dict[str, Any]:
    """Удалить файл миссии"""
    level_dir = level.lower()
    mission_path = settings.MISSIONS_DIR / f"level_{level_dir}" / mission_id
    file_path = mission_path / filename
    
    # Безопасность: проверяем, что файл находится в директории миссии
    try:
        file_path.resolve().relative_to(mission_path.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Недопустимый путь к файлу")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Файл {filename} не найден")
    
    # Не разрешаем удалять mission.yaml
    if filename == "mission.yaml":
        raise HTTPException(status_code=400, detail="Нельзя удалить файл конфигурации миссии")
    
    try:
        file_path.unlink()
        
        logger.info(f"Файл {filename} удален из миссии {mission_id} администратором {username}")
        
        return {
            "status": "success",
            "message": f"Файл {filename} успешно удален"
        }
    except Exception as e:
        logger.error(f"Ошибка удаления файла {filename} из миссии {mission_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка удаления файла: {e}")


@router.get("/user-info")
async def get_user_info(
    username: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Получить информацию о текущем пользователе, включая права администратора"""
    from backend.database import SessionLocal
    from backend.models.user_db import User
    
    db = SessionLocal()
    try:
        user = User(username, db=db)
        if not user.load(db=db):
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        return {
            "username": user.username,
            "is_admin": bool(getattr(user, 'is_admin', 0)),  # Поддержка старых записей
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
    finally:
        db.close()


@router.get("/users-list", tags=["admin"])
async def list_users(
    username: str = Depends(get_admin_user)
) -> List[Dict[str, Any]]:
    """Получить список всех пользователей (только для администраторов)"""
    from backend.database import SessionLocal
    from backend.database import UserModel
    
    db = SessionLocal()
    try:
        users = db.query(UserModel).all()
        result = [
            {
                "username": user.username,
                "is_admin": bool(getattr(user, 'is_admin', 0)),
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
            for user in users
        ]
        logger.info(f"Администратор {username} запросил список пользователей. Найдено: {len(result)}")
        return result
    except Exception as e:
        logger.error(f"Ошибка получения списка пользователей: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка пользователей: {e}")
    finally:
        db.close()


@router.get("/users/{target_username}/progress")
async def get_user_progress_admin(
    target_username: str,
    username: str = Depends(get_admin_user)
) -> Dict[str, Any]:
    """Получить прогресс конкретного пользователя (только для администраторов)"""
    from backend.models.progress import get_user_progress
    
    try:
        progress = get_user_progress(target_username)
        progress.load()
        
        return {
            "username": target_username,
            "missions_completed": progress.missions_completed,
            "total_score": progress.total_score,
            "level_progress": progress.level_progress,
            "achievements": progress.achievements,
            "last_updated": progress.last_updated.isoformat() if progress.last_updated else None,
            "stats": progress.get_stats()
        }
    except Exception as e:
        logger.error(f"Ошибка получения прогресса пользователя {target_username}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка получения прогресса: {e}")
