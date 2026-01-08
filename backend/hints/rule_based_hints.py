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
                "hint": "Файл или директория не найдены. Проверьте путь через файловый менеджер.",
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
                "hint": "Файл не найден. Откройте файловый менеджер, перейдите в нужную папку и создайте файл (правый клик → Создать → Документ).",
                "category": "mission_check",
                "priority": 1
            },
            {
                "check_type": "file_content",
                "hint": "Содержимое файла не соответствует ожидаемому. Откройте файл в текстовом редакторе и проверьте содержимое.",
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
        mission_id: Optional[str] = None,
        level: Optional[str] = None
    ) -> Optional[str]:
        """Получить подсказку для ошибки"""
        hints = []
        
        # Определяем уровень пользователя
        level_upper = (level or "A").upper() if level else "A"
        is_level_a = level_upper == "A"
        
        # Поиск по паттернам в сообщении об ошибке
        if error_message:
            for rule in self.rules:
                if "pattern" in rule:
                    if re.search(rule["pattern"], error_message, re.IGNORECASE):
                        hint_text = rule["hint"]
                        # Для уровня A заменяем терминальные команды на GUI подсказки
                        if is_level_a:
                            hint_text = self._convert_to_gui_hint(hint_text, rule.get("pattern", ""), error_message, level)
                        hints.append({
                            "hint": hint_text,
                            "priority": rule.get("priority", 1),
                            "category": rule.get("category", "general")
                        })
        
        # Поиск по типу проверки
        if check_result:
            check_type = check_result.get("type")
            for rule in self.rules:
                if rule.get("check_type") == check_type:
                    hint_text = rule["hint"]
                    # Для уровня A заменяем терминальные команды на GUI подсказки
                    if is_level_a:
                        hint_text = self._convert_to_gui_hint(hint_text, check_type, error_message or "", level)
                    
                    # Проверяем дополнительные условия
                    if "expected" in rule:
                        if check_result.get("expected") == rule["expected"]:
                            hints.append({
                                "hint": hint_text,
                                "priority": rule.get("priority", 1),
                                "category": rule.get("category", "mission_check")
                            })
                    else:
                        hints.append({
                            "hint": hint_text,
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
    
    def get_hints_for_failed_checks(self, check_results: List[Dict[str, Any]], level: Optional[str] = None) -> List[str]:
        """Получить подсказки для всех проваленных проверок"""
        hints = []
        
        for check in check_results:
            if not check.get("passed", False):
                hint = self.get_hint_for_error(
                    error_message=check.get("message", ""),
                    check_result=check,
                    level=level
                )
                if hint:
                    hints.append(hint)
        
        return hints
    
    def _convert_to_gui_hint(self, hint_text: str, pattern: str, error_message: str, level: Optional[str] = None) -> str:
        """Преобразовать подсказку с командами терминала в GUI подсказку для уровня A"""
        level_upper = (level or "A").upper() if level else "A"
        is_level_a = level_upper == "A"
        
        # Замены для уровня A
        gui_replacements = {
            r"командой 'ls'": "через файловый менеджер (откройте нужную папку)",
            r"командой 'pwd'": "посмотрев путь в адресной строке файлового менеджера",
            r"командой 'cat'": "открыв файл в текстовом редакторе",
            r"командой 'which'": "найдя программу в меню приложений",
            r"командой 'ls -l'": "через свойства файла (правый клик → Свойства)",
            r"'ls'": "в файловом менеджере",
            r"'pwd'": "в адресной строке",
            r"'cat'": "в текстовом редакторе",
            r"'sudo'": "использовав кнопку 'Запуск от имени администратора' (правый клик)",
            r"'cp'": "через копирование (Ctrl+C) и вставку (Ctrl+V) или перетаскивание",
            r"'mv'": "перетащив файл в нужную папку",
            r"'rm'": "через удаление (правый клик → Удалить или клавиша Delete)",
            r"'mkdir'": "правым кликом → Создать папку",
            r"'rmdir'": "удалив пустую папку",
            r"'chmod'": "через Свойства файла → Права доступа",
            r"'find'": "используя поиск в файловом менеджере (Ctrl+F)",
            r"'grep'": "используя поиск в текстовом редакторе (Ctrl+F)",
            r"'tar'": "используя архивный менеджер или распаковку архива"
        }
        
        if is_level_a:
            converted_hint = hint_text
            for pattern, replacement in gui_replacements.items():
                converted_hint = re.sub(pattern, replacement, converted_hint, flags=re.IGNORECASE)
            
            # Общие улучшения для GUI
            if "Файл или директория не найдены" in converted_hint:
                return "Файл или папка не найдены. Проверьте путь в файловом менеджере или поищите файл через поиск (Ctrl+F)."
            if "Файл не найден" in converted_hint and "команда" not in converted_hint.lower():
                return "Файл не найден. Откройте файловый менеджер и проверьте правильность пути или создайте файл."
            if "Недостаточно прав доступа" in converted_hint:
                return "Недостаточно прав доступа. Попробуйте использовать опцию 'Запуск от имени администратора' (правый клик на файле)."
            
            return converted_hint
        
        return hint_text

