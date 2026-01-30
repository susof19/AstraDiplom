"""Проверка выполнения миссий"""
import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from enum import Enum

import yaml

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
    
    def __init__(self, mission_id: str, level: str, username: str = None):
        self.mission_id = mission_id
        self.level = level
        self.username = username
        
        # Определяем путь к миссии
        # Если это персональная миссия (начинается с personal_{username}_)
        if mission_id.startswith("personal_") and username:
            # Извлекаем username из mission_id, если он не передан явно
            # Формат: personal_{username}_{readable_part}_{hash}
            parts = mission_id.split("_", 2)
            if len(parts) >= 2:
                extracted_username = parts[1]
                self.mission_path = settings.MISSIONS_DIR / "personal" / extracted_username / mission_id
            else:
                # Если не удалось извлечь, используем переданный username
                self.mission_path = settings.MISSIONS_DIR / "personal" / username / mission_id
        else:
            # Стандартная миссия
            self.mission_path = settings.MISSIONS_DIR / f"level_{level.lower()}" / mission_id
        
    async def load_mission_config(self) -> Optional[Dict[str, Any]]:
        """Загрузить конфигурацию миссии"""
        config_file = self.mission_path / "mission.yaml"
        if not config_file.exists():
            logger.error(f"Конфигурация миссии не найдена: {config_file}")
            return None
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if config:
                    logger.info(f"Конфигурация миссии {self.mission_id} успешно загружена из {config_file}")
                return config
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            return None
    
    async def check(self, sandbox: ContainerSandbox) -> Dict[str, Any]:
        """Проверить выполнение миссии"""
        config = await self.load_mission_config()
        if not config:
            logger.error(f"Конфигурация миссии {self.mission_id} не загружена")
            return {
                "result": CheckResult.FAILED.value,
                "score": 0,
                "message": "Ошибка загрузки конфигурации миссии",
                "checks": []
            }
        
        container_user = sandbox.container_user or "sandboxuser"
        try:
            if container_user == "root":
                user_home = "/root"
            else:
                home_output, home_code = await sandbox.exec_command(f"echo ~{container_user}", user=container_user)
                user_home = home_output.strip() if home_code == 0 else f"/home/{container_user}"
        except Exception:
            user_home = "/root" if container_user == "root" else f"/home/{container_user}"
        
        def replace_user_path(path: str) -> str:
            """Заменяет /home/sandboxuser, /home/user на реальный путь пользователя, но НЕ заменяет /root если пользователь root"""
            if container_user == "root":
                # Для root не заменяем /root, только /home/ пути
                if path.startswith("/home/user/"):
                    return path.replace("/home/user", user_home, 1)
                elif path.startswith("/home/sandboxuser/"):
                    return path.replace("/home/sandboxuser", user_home, 1)
                return path
            else:
                # Для других пользователей заменяем все пути
                if path.startswith("/root/"):
                    return path.replace("/root", user_home, 1)
                elif path.startswith("/home/user/"):
                    return path.replace("/home/user", user_home, 1)
                elif path.startswith("/home/sandboxuser/"):
                    return path.replace("/home/sandboxuser", user_home, 1)
                return path
        
        checks = config.get("checks", [])
        for check in checks:
            if "path" in check:
                check["path"] = replace_user_path(check["path"])
        if not checks:
            logger.warning(f"Миссия {self.mission_id} не содержит проверок")
            return {
                "result": CheckResult.FAILED.value,
                "score": 0,
                "message": "Миссия не содержит проверок",
                "checks": []
            }
        
        logger.info(f"Начало проверки миссии {self.mission_id}, проверок: {len(checks)}")
        results = []
        passed = 0
        total_points = 0
        earned_points = 0
        
        for check in checks:
            check_name = check.get("name", "unknown")
            check_points = check.get("points", 0)
            total_points += check_points
            logger.info(f"Выполнение проверки '{check_name}': {check.get('type', 'unknown')}")
            
            check_result = await self._run_check(check, sandbox)
            check_result["points"] = check_points
            if check_result.get("passed", False):
                passed += 1
                earned_points += check_points
                check_result["earned_points"] = check_points
                logger.info(f"✓ Проверка пройдена: {check_name} (+{check_points} баллов)")
            else:
                check_result["earned_points"] = 0
                logger.info(f"✗ Проверка не пройдена: {check_name} - {check_result.get('message', '')} (0/{check_points} баллов)")
            
            results.append(check_result)
        
        score = int((earned_points / total_points) * 100) if total_points > 0 else 0
        result = CheckResult.PASSED if passed == len(checks) else (CheckResult.PARTIAL if passed > 0 else CheckResult.FAILED)
        
        logger.info(f"Проверка миссии {self.mission_id} завершена: {passed}/{len(checks)} проверок пройдено, {earned_points}/{total_points} баллов, оценка: {score}%")
        
        # Если rule-based проверка не пройдена, используем ML evaluator для оценки по смыслу
        ml_evaluation = None
        if result != CheckResult.PASSED:
            try:
                from backend.grader.ml_evaluator import get_ml_evaluator
                ml_evaluator = get_ml_evaluator()
                
                # Загружаем конфигурацию миссии для ML evaluator
                mission_config = await self.load_mission_config()
                if mission_config:
                    ml_evaluation = await ml_evaluator.evaluate(
                        mission_id=self.mission_id,
                        mission_config=mission_config,
                        check_results=results,
                        sandbox_context=None  # Можно добавить контекст из sandbox
                    )
                    
                    # Если ML считает, что миссия выполнена по смыслу, переопределяем результат
                    if ml_evaluation.get("should_override", False):
                        ml_score = int(ml_evaluation["score"] * 100)
                        if ml_score >= 70:
                            result = CheckResult.PARTIAL
                            score = ml_score
                            logger.info(f"ML evaluator переопределил результат: score={ml_score}%, reason={ml_evaluation.get('reason', '')}")
            except Exception as e:
                logger.warning(f"Ошибка ML evaluation: {e}", exc_info=True)
        
        return {
            "result": result.value,
            "score": score,
            "points": {
                "earned": earned_points,
                "total": total_points
            },
            "message": f"Выполнено {passed} из {len(checks)} проверок ({earned_points}/{total_points} баллов)",
            "checks": results,
            "ml_evaluation": ml_evaluation  # Добавляем ML оценку в результат
        }
    
    async def _run_check(self, check: Dict[str, Any], sandbox: ContainerSandbox) -> Dict[str, Any]:
        """Выполнить одну проверку"""
        check_type = check.get("type")
        
        try:
            if check_type == "file_exists":
                return await self._check_file_exists(check, sandbox)
            elif check_type == "file_content":
                return await self._check_file_content(check, sandbox)
            elif check_type == "command_output":
                return await self._check_command_output(check, sandbox)
            elif check_type == "gui_state":
                return await self._check_gui_state(check, sandbox)
            else:
                logger.warning(f"Неизвестный тип проверки: {check_type}")
                return {
                    "name": check.get("name", "unknown"),
                    "type": check_type or "unknown",
                    "passed": False,
                    "message": f"Неизвестный тип проверки: {check_type}"
                }
        except Exception as e:
            logger.error(f"Ошибка выполнения проверки {check.get('name', 'unknown')}: {e}", exc_info=True)
            return {
                "name": check.get("name", "unknown"),
                "type": check_type or "unknown",
                "passed": False,
                "message": f"Ошибка выполнения проверки: {e}"
            }
    
    async def _check_file_exists(self, check: Dict[str, Any], sandbox: ContainerSandbox) -> Dict[str, Any]:
        """Проверить существование файла или директории"""
        path = check.get("path")
        check_type = check.get("file_type", "file")
        expected = check.get("expected", True)
        
        if not path:
            return {"name": check.get("name"), "passed": False, "message": "Путь не указан"}
        
        try:
            if check_type == "directory":
                output, code = await sandbox.exec_command(f"test -d '{path}' && echo 'exists' || echo 'not_found'")
                exists = "exists" in output
                item_type = "Директория"
            elif check_type == "file":
                output, code = await sandbox.exec_command(f"test -f '{path}' && echo 'exists' || echo 'not_found'")
                exists = "exists" in output
                item_type = "Файл"
            else:
                output, code = await sandbox.exec_command(f"test -e '{path}' && echo 'exists' || echo 'not_found'")
                exists = "exists" in output
                item_type = "Файл или директория"
            
            logger.debug(f"Проверка {item_type} {path}: exists={exists}, expected={expected}, output='{output.strip()}', code={code}")
        except Exception as e:
            logger.error(f"Ошибка проверки файла/директории {path}: {e}")
            exists = False
            item_type = "Файл или директория"
        
        passed = (exists == expected)
        
        if expected is False:
            message = f"{item_type} {'не найден' if passed else 'найден (должен быть удален)'}: {path}"
        else:
            message = f"{item_type} {'найден' if passed else 'не найден'}: {path}"
        
        return {
            "name": check.get("name", f"{item_type} exists: {path}"),
            "type": "file_exists",
            "passed": passed,
            "message": message
        }
    
    async def _check_file_content(self, check: Dict[str, Any], sandbox: ContainerSandbox) -> Dict[str, Any]:
        """Проверить содержимое файла"""
        path = check.get("path")
        expected = check.get("expected")
        operator = check.get("operator", "contains")
        
        if not path:
            return {"name": check.get("name"), "passed": False, "message": "Путь не указан"}
        
        if expected is None:
            return {"name": check.get("name"), "passed": False, "message": "Ожидаемое содержимое не указано"}
        
        try:
            output, code = await sandbox.exec_command(f"cat '{path}' 2>/dev/null || echo ''")
            content = output.strip()
            
            if operator == "contains":
                matches = str(expected) in content
            elif operator == "equals":
                matches = content == str(expected)
            elif operator == "regex":
                matches = bool(re.search(str(expected), content))
            else:
                matches = str(expected) in content
            
            logger.debug(f"Проверка содержимого файла {path}: operator={operator}, expected={expected}, matches={matches}")
            
            return {
                "name": check.get("name", f"File content: {path}"),
                "type": "file_content",
                "passed": matches,
                "message": f"Содержимое файла {'соответствует' if matches else 'не соответствует'} ожиданию (оператор: {operator})"
            }
        except Exception as e:
            logger.error(f"Ошибка проверки содержимого файла {path}: {e}")
            return {
                "name": check.get("name", f"File content: {path}"),
                "type": "file_content",
                "passed": False,
                "message": f"Ошибка чтения файла: {e}"
            }
    
    async def _check_command_output(self, check: Dict[str, Any], sandbox: ContainerSandbox) -> Dict[str, Any]:
        """Проверить вывод команды с различными операторами сравнения"""
        command = check.get("command")
        expected = check.get("expected")
        operator = check.get("operator", "contains")
        exit_code_required = check.get("exit_code", None)
        
        if not command:
            return {"name": check.get("name"), "passed": False, "message": "Команда не указана"}
        
        try:
            output, code = await sandbox.exec_command(command)
            output = output.strip()
            
            if exit_code_required is not None:
                if code != exit_code_required:
                    return {
                        "name": check.get("name", f"Command: {command}"),
                        "type": "command_output",
                        "passed": False,
                        "message": f"Код возврата не совпадает: получено {code}, ожидалось {exit_code_required}"
                    }
            
            if expected is None:
                matches = (code == 0) if exit_code_required is None else (code == exit_code_required)
                return {
                    "name": check.get("name", f"Command: {command}"),
                    "type": "command_output",
                    "passed": matches,
                    "message": f"Команда {'выполнена успешно' if matches else f'завершилась с кодом {code}'}"
                }
            
            if operator == "contains":
                matches = str(expected) in output
            elif operator == "equals":
                matches = output == str(expected)
            elif operator == "greater_than":
                try:
                    output_num = float(output)
                    expected_num = float(expected)
                    matches = output_num > expected_num
                except ValueError:
                    matches = False
            elif operator == "less_than":
                try:
                    output_num = float(output)
                    expected_num = float(expected)
                    matches = output_num < expected_num
                except ValueError:
                    matches = False
            elif operator == "regex":
                matches = bool(re.search(str(expected), output))
            else:
                matches = str(expected) in output
            
            logger.debug(f"Проверка команды: {command}, оператор={operator}, expected={expected}, output='{output}', matches={matches}")
            
            return {
                "name": check.get("name", f"Command: {command}"),
                "type": "command_output",
                "passed": matches,
                "message": f"Вывод команды {'соответствует' if matches else 'не соответствует'} ожиданию (оператор: {operator})"
            }
        except Exception as e:
            logger.error(f"Ошибка выполнения команды {command}: {e}")
            return {
                "name": check.get("name", f"Command: {command}"),
                "type": "command_output",
                "passed": False,
                "message": f"Ошибка выполнения команды: {e}"
            }
    
    async def _check_gui_state(self, check: Dict[str, Any], sandbox: ContainerSandbox) -> Dict[str, Any]:
        """Проверить состояние GUI (для уровня A)"""
        if not sandbox.use_vnc or not sandbox.novnc_port:
            return {
                "name": check.get("name", "GUI state"),
                "type": "gui_state",
                "passed": False,
                "message": "VNC не доступен для проверки GUI"
            }
        
        window_name = check.get("window", None)
        if window_name:
            try:
                output, code = await sandbox.exec_command(f"pgrep -f '{window_name}' || echo 'not_found'")
                window_exists = "not_found" not in output
                return {
                    "name": check.get("name", f"GUI window: {window_name}"),
                    "type": "gui_state",
                    "passed": window_exists,
                    "message": f"Окно {window_name} {'найдено' if window_exists else 'не найдено'}"
                }
            except Exception as e:
                logger.error(f"Ошибка проверки GUI состояния: {e}")
        
        return {
            "name": check.get("name", "GUI state"),
            "type": "gui_state",
            "passed": False,
            "message": "Проверка GUI через скриншоты ещё не реализована (можно проверить процессы)"
        }


class Grader:
    """Главный класс для проверки миссий"""
    
    @staticmethod
    async def grade_mission(mission_id: str, level: str, sandbox: ContainerSandbox, username: str = None) -> Dict[str, Any]:
        """Проверить выполнение миссии"""
        checker = MissionChecker(mission_id, level, username)
        return await checker.check(sandbox)
