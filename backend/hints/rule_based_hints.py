"""Rule-based система подсказок на основе ошибок"""
import re
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from backend.config import settings

logger = logging.getLogger(__name__)


class RuleBasedHintSystem:
    """Система подсказок на основе правил"""
    
    def __init__(self):
        self.rules = self._load_rules()
    
    def _load_rules(self) -> List[Dict[str, Any]]:
        """Загрузить правила для подсказок"""
        # Базовые правила для типичных ошибок
        return [
            # Ошибки файловой системы
            {
                "pattern": r"No such file or directory",
                "hint": "Файл или директория не найдены. Проверьте путь командой 'ls' или 'pwd'.",
                "category": "file_system",
                "priority": 1
            },
            {
                "pattern": r"Permission denied",
                "hint": "Недостаточно прав доступа. Попробуйте использовать 'sudo' или проверьте права командой 'ls -l'.",
                "category": "permissions",
                "priority": 1
            },
            {
                "pattern": r"command not found",
                "hint": "Команда не найдена. Проверьте правильность написания командой 'which <команда>' или установите пакет.",
                "category": "command",
                "priority": 1
            },
            {
                "pattern": r"cannot create.*File exists",
                "hint": "Файл уже существует. Используйте другую команду или удалите существующий файл.",
                "category": "file_system",
                "priority": 2
            },
            {
                "pattern": r"cannot remove.*Is a directory",
                "hint": "Это директория, а не файл. Используйте 'rmdir' для пустых директорий или 'rm -r' для удаления с содержимым.",
                "category": "file_system",
                "priority": 1
            },
            # Ошибки команд
            {
                "pattern": r"cp.*missing destination",
                "hint": "Не указан путь назначения для копирования. Формат: 'cp <источник> <назначение>'.",
                "category": "command",
                "priority": 1
            },
            {
                "pattern": r"mv.*missing destination",
                "hint": "Не указан путь назначения для перемещения. Формат: 'mv <источник> <назначение>'.",
                "category": "command",
                "priority": 1
            },
            {
                "pattern": r"mkdir.*File exists",
                "hint": "Директория уже существует. Используйте 'mkdir -p' для создания без ошибок или проверьте существование.",
                "category": "command",
                "priority": 2
            },
            {
                "pattern": r"tar.*Cannot open",
                "hint": "Не удалось открыть архив. Проверьте путь к файлу и его существование.",
                "category": "archive",
                "priority": 1
            },
            {
                "pattern": r"grep.*No such file",
                "hint": "Файл для поиска не найден. Проверьте путь командой 'ls'.",
                "category": "command",
                "priority": 1
            },
            # Ошибки проверки миссий
            {
                "check_type": "file_exists",
                "expected": True,
                "hint": "Файл не найден. Создайте файл или проверьте правильность пути.",
                "category": "mission_check",
                "priority": 1
            },
            {
                "check_type": "file_content",
                "hint": "Содержимое файла не соответствует ожидаемому. Проверьте содержимое командой 'cat <файл>'.",
                "category": "mission_check",
                "priority": 1
            },
            {
                "check_type": "command_output",
                "hint": "Вывод команды не соответствует ожидаемому. Проверьте команду и её вывод.",
                "category": "mission_check",
                "priority": 1
            },
        ]
    
    def get_hint_for_error(
        self,
        error_message: str,
        command: Optional[str] = None,
        check_result: Optional[Dict[str, Any]] = None,
        mission_id: Optional[str] = None
    ) -> Optional[str]:
        """Получить подсказку для ошибки"""
        hints = []
        
        # Поиск по паттернам в сообщении об ошибке
        if error_message:
            for rule in self.rules:
                if "pattern" in rule:
                    if re.search(rule["pattern"], error_message, re.IGNORECASE):
                        hints.append({
                            "hint": rule["hint"],
                            "priority": rule.get("priority", 1),
                            "category": rule.get("category", "general")
                        })
        
        # Поиск по типу проверки
        if check_result:
            check_type = check_result.get("type")
            for rule in self.rules:
                if rule.get("check_type") == check_type:
                    # Проверяем дополнительные условия
                    if "expected" in rule:
                        if check_result.get("expected") == rule["expected"]:
                            hints.append({
                                "hint": rule["hint"],
                                "priority": rule.get("priority", 1),
                                "category": rule.get("category", "mission_check")
                            })
                    else:
                        hints.append({
                            "hint": rule["hint"],
                            "priority": rule.get("priority", 1),
                            "category": rule.get("category", "mission_check")
                        })
        
        # Специфичные подсказки для команд
        if command:
            command_base = command.split()[0] if command else ""
            command_hints = self._get_command_specific_hints(command_base, error_message)
            hints.extend(command_hints)
        
        # Специфичные подсказки для миссий
        if mission_id:
            mission_hints = self._get_mission_specific_hints(mission_id, check_result)
            hints.extend(mission_hints)
        
        if not hints:
            return None
        
        # Сортируем по приоритету (меньше = важнее)
        hints.sort(key=lambda x: x["priority"])
        
        # Возвращаем подсказку с наивысшим приоритетом
        return hints[0]["hint"]
    
    def _get_command_specific_hints(self, command_base: str, error_message: str) -> List[Dict[str, Any]]:
        """Получить специфичные подсказки для команды"""
        hints = []
        
        command_hints = {
            "cp": {
                "patterns": [r"cannot stat", r"omitting directory"],
                "hint": "Для копирования директорий используйте 'cp -r <источник> <назначение>'."
            },
            "rm": {
                "patterns": [r"cannot remove.*Is a directory"],
                "hint": "Для удаления директории используйте 'rm -r <директория>' или 'rmdir <пустая_директория>'."
            },
            "chmod": {
                "patterns": [r"cannot access"],
                "hint": "Проверьте существование файла и права доступа. Формат: 'chmod <права> <файл>' (например, chmod 755 file.sh)."
            },
            "find": {
                "patterns": [r"paths must precede expression"],
                "hint": "В команде find путь должен идти перед опциями. Формат: 'find <путь> -name <шаблон>'."
            },
            "grep": {
                "patterns": [r"No such file"],
                "hint": "Проверьте путь к файлу. Формат: 'grep <паттерн> <файл>'."
            },
            "tar": {
                "patterns": [r"Cannot open", r"Unexpected EOF"],
                "hint": "Проверьте целостность архива и путь. Для создания: 'tar -czf <архив.tar.gz> <файлы>', для распаковки: 'tar -xzf <архив.tar.gz>'."
            }
        }
        
        if command_base in command_hints:
            cmd_info = command_hints[command_base]
            for pattern in cmd_info["patterns"]:
                if re.search(pattern, error_message, re.IGNORECASE):
                    hints.append({
                        "hint": cmd_info["hint"],
                        "priority": 1,
                        "category": "command_specific"
                    })
                    break
        
        return hints
    
    def _get_mission_specific_hints(
        self,
        mission_id: str,
        check_result: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Получить специфичные подсказки для миссии"""
        hints = []
        
        # Загружаем подсказки из конфигурации миссии
        try:
            mission_path = settings.MISSIONS_DIR / f"level_{check_result.get('level', 'a').lower()}" / mission_id
            config_file = mission_path / "mission.yaml"
            
            if config_file.exists():
                import yaml
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    mission_hints = config.get("hints", [])
                    
                    if check_result:
                        failed_checks = [
                            c for c in check_result.get("checks", [])
                            if not c.get("passed", False)
                        ]
                        
                        for failed_check in failed_checks:
                            check_name = failed_check.get("name", "")
                            for hint_config in mission_hints:
                                if hint_config.get("check") == check_name:
                                    hints.append({
                                        "hint": hint_config.get("text", ""),
                                        "priority": hint_config.get("priority", 2),
                                        "category": "mission_specific"
                                    })
        except Exception as e:
            logger.debug(f"Не удалось загрузить подсказки для миссии {mission_id}: {e}")
        
        return hints
    
    def get_hints_for_failed_checks(self, check_results: List[Dict[str, Any]]) -> List[str]:
        """Получить подсказки для всех проваленных проверок"""
        hints = []
        
        for check in check_results:
            if not check.get("passed", False):
                hint = self.get_hint_for_error(
                    error_message=check.get("message", ""),
                    check_result=check
                )
                if hint:
                    hints.append(hint)
        
        return hints

