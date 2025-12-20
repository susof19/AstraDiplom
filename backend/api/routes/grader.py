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
    level: str = None,
    username: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Проверить выполнение миссии"""
    from fastapi import Query
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Получаем level из query параметров или из песочницы
    sandbox = await sandbox_manager.get_sandbox(mission_id)
    
    if not sandbox:
        raise HTTPException(status_code=404, detail="Песочница не найдена")
    
    # Используем level из параметра или из песочницы
    if not level:
        level = sandbox.level
    
    logger.info(f"Проверка миссии {mission_id} уровня {level}")
    
    result = await Grader.grade_mission(mission_id, level, sandbox)
    
    # Автоматически останавливаем песочницу после проверки
    try:
        logger.info(f"Остановка песочницы после проверки миссии {mission_id}")
        await sandbox_manager.remove_sandbox(mission_id)
        logger.info(f"Песочница {mission_id} остановлена")
    except Exception as e:
        logger.warning(f"Не удалось остановить песочницу после проверки: {e}")
    
    # Сохраняем прогресс, если миссия выполнена (score >= 70%)
    score = result.get("score", 0)
    result_status = result.get("result", "failed")
    
    # Миссия считается пройденной если score >= 70% или все проверки пройдены
    is_passed = result_status == "passed" or (result_status == "partial" and score >= 70)
    
    if is_passed:
        progress = get_user_progress(username)
        old_achievements = set(progress.achievements)
        old_total_score = progress.total_score
        
        # Рассчитываем XP: score * difficulty (если есть в конфиге) или просто score
        # Загружаем конфиг миссии для получения difficulty
        try:
            import yaml
            from backend.config import settings
            mission_dir = settings.MISSIONS_DIR / f"level_{level.lower()}" / mission_id
            config_file = mission_dir / "mission.yaml"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    mission_config = yaml.safe_load(f)
                    difficulty = mission_config.get("difficulty", 1)
                    # XP = score * difficulty (максимум 100 * 5 = 500 XP за миссию)
                    base_xp = int(score * difficulty)
            else:
                base_xp = score
        except Exception as e:
            logger.warning(f"Не удалось загрузить конфиг миссии для расчёта XP: {e}")
            base_xp = score
        
        # Отмечаем миссию как выполненную (передаём score для сохранения, но XP рассчитываем отдельно)
        # complete_mission теперь возвращает информацию о том, было ли это первое прохождение или улучшение
        completion_info = progress.complete_mission(mission_id, level, score)
        
        # Рассчитываем фактически заработанный XP на основе base_xp
        # XP начисляется только при первом прохождении или при улучшении результата
        if completion_info["is_new"]:
            # Первое прохождение - начисляем полный XP и добавляем в total_score
            xp_earned = base_xp
            progress.total_score += xp_earned
            progress.save()  # Сохраняем обновлённый total_score
            xp_message = f"Получено {xp_earned} XP"
        elif completion_info["is_improved"]:
            # Улучшен результат - начисляем только разницу в XP
            old_xp = int(completion_info["old_score"] * difficulty) if completion_info["old_score"] else 0
            xp_earned = base_xp - old_xp
            progress.total_score += xp_earned
            progress.save()  # Сохраняем обновлённый total_score
            xp_message = f"Результат улучшен! Получено {xp_earned} XP (было {completion_info['old_score']}%, стало {score}%)"
        else:
            # Повторное прохождение без улучшения - XP не начисляется
            xp_earned = 0
            xp_message = f"Миссия уже пройдена с результатом {completion_info['old_score']}%. XP не начислено."
        
        new_achievements = set(progress.achievements) - old_achievements
        new_total_score = progress.total_score
        
        result["mission_passed"] = True
        result["xp_earned"] = xp_earned
        result["total_xp"] = new_total_score
        result["new_achievements"] = list(new_achievements)
        result["is_new_mission"] = completion_info["is_new"]
        result["is_improved"] = completion_info["is_improved"]
        result["message"] = f"Миссия пройдена! {xp_message}. {result.get('message', '')}"
    else:
        result["mission_passed"] = False
        result["xp_earned"] = 0
        result["message"] = f"Миссия не пройдена. Необходимо набрать минимум 70% для прохождения. {result.get('message', '')}"
    
    return result

