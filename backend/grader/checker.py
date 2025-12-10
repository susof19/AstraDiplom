"""Проверка выполнения миссий"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from enum import Enum

from backend.sandbox.container import ContainerSandbox
from backend.config import settings

logger = logging.getLogger(__name__)


class CheckResult(Enum):
    """Результат проверки"""
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"


class MissionChecker:
    """Проверка выполнения конкретной миссии"""
    
    def __init__(self, mission_id: str, level: str):
        self.mission_id = mission_id
        self.level = level
        self.mission_path = settings.MISSIONS_DIR / f"level_{level.lower()}" / mission_id
        
    async def load_mission_config(self) -> Optional[Dict[str, Any]]:
        """Загрузить конфигурацию миссии"""
        config_file = self.mission_path / "mission.yaml"
        if not config_file.exists():
            logger.error(f"Конфигурация миссии не найдена: {config_file}")
            return None
        
        try:
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            return None
    
    async def check(self, sandbox: ContainerSandbox) -> Dict[str, Any]:
        """Проверить выполнение миссии"""
        config = await self.load_mission_config()
        if not config:
            return {
                "result": CheckResult.FAILED.value,
                "score": 0,
                "message": "Ошибка загрузки конфигурации миссии",
                "checks": []
            }
        
        checks = config.get("checks", [])
        results = []
        passed = 0
        total = len(checks)
        
        for check in checks:
            check_result = await self._run_check(check, sandbox)
            results.append(check_result)
            if check_result["passed"]:
                passed += 1
        
        score = int((passed / total) * 100) if total > 0 else 0
        result = CheckResult.PASSED if passed == total else (CheckResult.PARTIAL if passed > 0 else CheckResult.FAILED)
        
        return {
            "result": result.value,
            "score": score,
            "message": f"Выполнено {passed} из {total} проверок",
            "checks": results
        }
    
    async def _run_check(self, check: Dict[str, Any], sandbox: ContainerSandbox) -> Dict[str, Any]:
        """Выполнить одну проверку"""
        check_type = check.get("type")
        
        if check_type == "file_exists":
            return await self._check_file_exists(check, sandbox)
        elif check_type == "file_content":
            return await self._check_file_content(check, sandbox)
        elif check_type == "command_output":
            return await self._check_command_output(check, sandbox)
        elif check_type == "gui_state":
            return await self._check_gui_state(check, sandbox)
        else:
            return {
                "name": check.get("name", "unknown"),
                "passed": False,
                "message": f"Неизвестный тип проверки: {check_type}"
            }
    
    async def _check_file_exists(self, check: Dict[str, Any], sandbox: ContainerSandbox) -> Dict[str, Any]:
        """Проверить существование файла"""
        path = check.get("path")
        if not path:
            return {"name": check.get("name"), "passed": False, "message": "Путь не указан"}
        
        output, code = await sandbox.exec_command(f"test -f '{path}' && echo 'exists' || echo 'not_found'")
        exists = "exists" in output
        
        return {
            "name": check.get("name", f"File exists: {path}"),
            "passed": exists,
            "message": f"Файл {'найден' if exists else 'не найден'}: {path}"
        }
    
    async def _check_file_content(self, check: Dict[str, Any], sandbox: ContainerSandbox) -> Dict[str, Any]:
        """Проверить содержимое файла"""
        path = check.get("path")
        expected = check.get("expected")
        if not path or expected is None:
            return {"name": check.get("name"), "passed": False, "message": "Параметры не указаны"}
        
        output, code = await sandbox.exec_command(f"cat '{path}' 2>/dev/null || echo ''")
        content = output.strip()
        matches = expected in content if isinstance(expected, str) else expected == content
        
        return {
            "name": check.get("name", f"File content: {path}"),
            "passed": matches,
            "message": f"Содержимое {'совпадает' if matches else 'не совпадает'}"
        }
    
    async def _check_command_output(self, check: Dict[str, Any], sandbox: ContainerSandbox) -> Dict[str, Any]:
        """Проверить вывод команды"""
        command = check.get("command")
        expected = check.get("expected")
        if not command or expected is None:
            return {"name": check.get("name"), "passed": False, "message": "Параметры не указаны"}
        
        output, code = await sandbox.exec_command(command)
        output = output.strip()
        matches = expected in output if isinstance(expected, str) else str(expected) in output
        
        return {
            "name": check.get("name", f"Command: {command}"),
            "passed": matches,
            "message": f"Вывод команды {'совпадает' if matches else 'не совпадает'}"
        }
    
    async def _check_gui_state(self, check: Dict[str, Any], sandbox: ContainerSandbox) -> Dict[str, Any]:
        """Проверить состояние GUI (для уровня A)"""
        # TODO: Реализовать проверку через скриншоты или состояние окон
        # Пока возвращаем заглушку
        return {
            "name": check.get("name", "GUI state"),
            "passed": False,
            "message": "Проверка GUI ещё не реализована"
        }


class Grader:
    """Главный класс для проверки миссий"""
    
    @staticmethod
    async def grade_mission(mission_id: str, level: str, sandbox: ContainerSandbox) -> Dict[str, Any]:
        """Проверить выполнение миссии"""
        checker = MissionChecker(mission_id, level)
        return await checker.check(sandbox)

