"""Генератор персональных миссий через LLM"""
import json
import logging
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
import re

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from backend.config import settings
from backend.hints.llm_hints import LLMHintProvider

logger = logging.getLogger(__name__)


class MissionGenerator:
    """Генератор персональных миссий через LLM"""
    
    def __init__(self):
        self.llm_provider = LLMHintProvider()
        self.provider_type = getattr(settings, 'LLM_PROVIDER', 'lm_studio')
        self.api_url = getattr(settings, 'LLM_API_URL', 'http://localhost:1234/v1')
        self.model_name = getattr(settings, 'LLM_MODEL', 'local-model')
        self.enabled = getattr(settings, 'LLM_HINTS_ENABLED', False)
    
    async def generate_mission(
        self,
        user_request: str,
        username: str,
        level: str = "A",
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Сгенерировать миссию на основе запроса пользователя
        
        Args:
            user_request: Запрос пользователя (что он хочет изучить)
            username: Имя пользователя
            level: Уровень миссии (A или B)
            conversation_history: История диалога для контекста
        
        Returns:
            dict с ключами:
            - mission_id: str - ID миссии
            - mission_config: dict - Конфигурация миссии в формате YAML
            - message: str - Сообщение от LLM
            - success: bool - Успешность генерации
        """
        if not self.enabled:
            return {
                "success": False,
                "message": "LLM генерация миссий отключена. Включите LLM_HINTS_ENABLED в настройках."
            }
        
        # Формируем промпт для генерации миссии
        prompt = self._build_generation_prompt(user_request, level, conversation_history)
        
        try:
            if self.provider_type == 'lm_studio':
                response = await self._generate_with_lm_studio(prompt, conversation_history)
            elif self.provider_type == 'ollama':
                response = await self._generate_with_ollama(prompt, conversation_history)
            elif self.provider_type == 'openai':
                response = await self._generate_with_openai(prompt, conversation_history)
            else:
                return {
                    "success": False,
                    "message": f"Неподдерживаемый провайдер LLM: {self.provider_type}"
                }
            
            if not response:
                return {
                    "success": False,
                    "message": "Не удалось получить ответ от LLM. Проверьте подключение к LLM сервису."
                }
            
            # Парсим ответ LLM и извлекаем конфигурацию миссии
            mission_config = self._parse_llm_response(response, user_request, level)
            
            if not mission_config:
                return {
                    "success": False,
                    "message": "Не удалось распарсить ответ LLM. Попробуйте переформулировать запрос."
                }
            
            # Генерируем уникальный ID миссии
            mission_id = self._generate_mission_id(username, user_request)
            
            return {
                "success": True,
                "mission_id": mission_id,
                "mission_config": mission_config,
                "message": "Миссия успешно сгенерирована!"
            }
            
        except Exception as e:
            logger.error(f"Ошибка генерации миссии: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Ошибка генерации миссии: {str(e)}"
            }
    
    def _build_generation_prompt(
        self,
        user_request: str,
        level: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Построить промпт для генерации миссии"""
        
        level_context = {
            "A": """Уровень A (GUI):
- Пользователь - НОВИЧОК в Linux
- Работает ТОЛЬКО через графический интерфейс (GUI)
- НЕ использует терминал
- Все действия через мышь, меню, кнопки
- Миссия должна быть простой и понятной
- Используй термины: файловый менеджер, меню, клик, кнопка""",
            "B": """Уровень B (CLI):
- Пользователь знает основы Linux
- Может использовать терминал и команды
- Понимает файловую систему
- Миссия может включать команды терминала"""
        }
        
        history_context = ""
        if conversation_history:
            history_context = "\n\nИстория диалога:\n"
            for msg in conversation_history[-3:]:  # Последние 3 сообщения
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_context += f"{role}: {content}\n"
        
        # Примеры из реальных миссий для лучшего понимания формата
        example_a = """name: "Создать текстовый файл через графический редактор"
description: "Откройте текстовый редактор (Kate) через меню, создайте файл hello_gui.txt на рабочем столе и запишите в него строку «Привет, Astra!», затем сохраните"
level: "A"
difficulty: 2
estimated_time: 5

objectives:
  - "Открыть текстовый редактор Kate через меню"
  - "Создать новый файл"
  - "Записать текст «Привет, Astra!»"
  - "Сохранить файл как hello_gui.txt на рабочем столе"

hints:
  - "Текстовый редактор можно найти в Меню → Офис → Kate (или другой редактор)"
  - "Рабочий стол находится в ~/Desktop"
  - "Для сохранения используйте Ctrl+S или Файл → Сохранить"

setup:
  directories:
    - "/root/Desktop"

checks:
  - name: "Файл hello_gui.txt создан на рабочем столе"
    type: "file_exists"
    path: "/root/Desktop/hello_gui.txt"
    file_type: "file"
    points: 40
  - name: "Файл содержит правильный текст"
    type: "file_content"
    path: "/root/Desktop/hello_gui.txt"
    operator: "contains"
    expected: "Привет, Astra!"
    points: 60"""

        example_b = """name: "Создать Bash-скрипт для подсчёта строк"
description: "В домашней директории создайте bash-скрипт count_lines.sh, который принимает имя файла в качестве аргумента и выводит количество строк в этом файле."
level: "B"
difficulty: 3
estimated_time: 7

objectives:
  - "Открыть терминал"
  - "Создать bash-скрипт count_lines.sh в домашней директории"
  - "Сделать скрипт исполняемым (chmod +x)"

setup:
  directories:
    - "/root/Documents"
  files:
    - path: "/root/Documents/data.txt"
      content: |
        Строка 1
        Строка 2
      mode: "644"

checks:
  - name: "Скрипт count_lines.sh существует"
    type: "file_exists"
    path: "/root/count_lines.sh"
    file_type: "file"
    points: 30
  - name: "Скрипт имеет бит исполнения"
    type: "command_output"
    command: "test -x /root/count_lines.sh && echo 'executable' || echo 'not_executable'"
    operator: "contains"
    expected: "executable"
    points: 30"""

        example_level = example_a if level.upper() == "A" else example_b

        prompt = f"""Ты помощник для создания учебных миссий Linux.

{level_context.get(level.upper(), level_context["A"])}

Запрос пользователя: {user_request}
{history_context}

Создай миссию в формате YAML, используя следующий РЕАЛЬНЫЙ пример миссии как образец:

{example_level}

КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:
1. Checks - это СПИСОК объектов (массив), НЕ словарь! Каждый элемент начинается с "-"
2. Все пути должны быть /root/... (НЕ /home/your_username или /home/user)
3. estimated_time - это ЧИСЛО (5, 10, 15), НЕ строка типа "10-15 минут"
4. file_content.expected - это СТРОКА, НЕ объект или массив
5. Для папок используй type: "file_exists" с file_type: "directory" (НЕ "dir_exists")
6. Для файлов используй type: "file_exists" с file_type: "file"

ПРАВИЛЬНАЯ СТРУКТУРА checks:
```yaml
checks:
  - name: "Описание проверки"
    type: "file_exists"
    path: "/root/Documents/file.txt"
    file_type: "file"  # или "directory" для папок
    points: 50
  - name: "Проверка содержимого"
    type: "file_content"
    path: "/root/Documents/file.txt"
    operator: "contains"
    expected: "текст для поиска"  # СТРОКА, не объект!
    points: 50
```

НЕПРАВИЛЬНО (НЕ используй!):
- checks: {{file_exists: true}}  ❌
- path: "/home/user/file.txt"  ❌ (должно быть /root/)
- estimated_time: "10 минут"  ❌ (должно быть число 10)
- expected: {{lines: [...]}}  ❌ (должно быть строка)
- type: "dir_exists"  ❌ (используй file_exists с file_type: "directory")

Создай ПОЛНУЮ миссию для запроса: "{user_request}"

КРИТИЧЕСКИ ВАЖНО:
- Верни ВСЮ миссию целиком: name, description, level, difficulty, estimated_time, objectives, hints, setup, checks
- НЕ возвращай только checks или только часть миссии!
- Миссия должна быть полной и готовой к использованию

Верни ТОЛЬКО YAML код полной миссии, без дополнительных объяснений:"""
        
        return prompt
    
    async def _generate_chat_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        level: str = "A"
    ) -> Optional[str]:
        """Генерация текстового ответа для чата (без YAML)"""
        if not AIOHTTP_AVAILABLE:
            return None
        
        messages = []
        
        # Системное сообщение для чата - только объяснения, без YAML
        system_message = """Ты помощник для создания учебных миссий Linux.
Твоя задача - помочь пользователю сформулировать запрос для создания миссии.

ВАЖНО:
- Отвечай ТОЛЬКО текстом, без YAML кода
- Объясняй, что нужно сделать для выполнения задачи
- Задавай уточняющие вопросы, если нужно
- НЕ генерируй YAML код - это будет сделано позже при нажатии кнопки "Создать миссию"
- Будь дружелюбным и понятным"""
        
        messages.append({"role": "system", "content": system_message})
        
        # Добавляем историю диалога
        if conversation_history:
            for msg in conversation_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                # Пропускаем системные сообщения из истории
                if role in ["user", "assistant"]:
                    messages.append({"role": role, "content": content})
        
        # Добавляем текущий запрос
        messages.append({"role": "user", "content": user_message})
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/chat/completions",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        choices = data.get("choices", [])
                        if choices:
                            content = choices[0].get("message", {}).get("content", "").strip()
                            # Убираем YAML блоки, если модель их сгенерировала
                            content = re.sub(r'```yaml\s*.*?```', '', content, flags=re.DOTALL)
                            content = re.sub(r'```\s*.*?```', '', content, flags=re.DOTALL)
                            return content.strip()
        except Exception as e:
            logger.error(f"Ошибка генерации чата через LM Studio: {e}")
        
        return None
    
    async def _generate_with_lm_studio(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Optional[str]:
        """Генерация через LM Studio"""
        if not AIOHTTP_AVAILABLE:
            return None
        
        messages = []
        
        # Добавляем системное сообщение для лучшей генерации
        system_message = f"""Ты эксперт по созданию учебных миссий для Linux тренажера.
Твоя задача - генерировать ТОЛЬКО валидный YAML код миссии, без дополнительных объяснений.

КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:
1. Checks - это СПИСОК объектов (массив словарей), НЕ словарь!
   Каждый элемент начинается с "-"

2. Все пути должны быть /root/... (НЕ /home/user или /home/your_username)

3. estimated_time - это ЧИСЛО (5, 10, 15), НЕ строка типа "10 минут"

4. file_content.expected - это СТРОКА, НЕ объект {{lines: [...]}}

5. Для папок используй type: "file_exists" с file_type: "directory" (НЕ "dir_exists")

6. Для файлов используй type: "file_exists" с file_type: "file"

ПРАВИЛЬНЫЙ формат checks:
```yaml
checks:
  - name: "Файл создан"
    type: "file_exists"
    path: "/root/Documents/file.txt"
    file_type: "file"
    points: 50
  - name: "Папка создана"
    type: "file_exists"
    path: "/root/Documents/MyFolder"
    file_type: "directory"
    points: 50
  - name: "Файл содержит текст"
    type: "file_content"
    path: "/root/Documents/file.txt"
    operator: "contains"
    expected: "текст для поиска"
    points: 50
```

НЕПРАВИЛЬНО (НЕ используй!):
- checks: {{file_exists: true}}  ❌
- path: "/home/user/file.txt"  ❌
- estimated_time: "10 минут"  ❌
- expected: {{lines: [...]}}  ❌
- type: "dir_exists"  ❌"""
        messages.append({"role": "system", "content": system_message})
        
        # Добавляем историю диалога
        if conversation_history:
            for msg in conversation_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ["user", "assistant", "system"]:
                    messages.append({"role": role, "content": content})
        
        # Добавляем текущий запрос
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/chat/completions",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        choices = data.get("choices", [])
                        if choices:
                            return choices[0].get("message", {}).get("content", "").strip()
        except Exception as e:
            logger.error(f"Ошибка генерации через LM Studio: {e}")
        
        return None
    
    async def _generate_with_ollama(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Optional[str]:
        """Генерация через Ollama"""
        if not AIOHTTP_AVAILABLE:
            return None
        
        ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 2000
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{ollama_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("response", "").strip()
        except Exception as e:
            logger.error(f"Ошибка генерации через Ollama: {e}")
        
        return None
    
    async def _generate_with_openai(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Optional[str]:
        """Генерация через OpenAI"""
        if not AIOHTTP_AVAILABLE:
            return None
        
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key:
            return None
        
        messages = []
        
        # Добавляем историю диалога
        if conversation_history:
            for msg in conversation_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ["user", "assistant", "system"]:
                    messages.append({"role": role, "content": content})
        
        # Добавляем текущий запрос
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model_name or "gpt-3.5-turbo",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        except Exception as e:
            logger.error(f"Ошибка генерации через OpenAI: {e}")
        
        return None
    
    def _parse_llm_response(
        self,
        response: str,
        user_request: str,
        level: str
    ) -> Optional[Dict[str, Any]]:
        """Парсинг ответа LLM и извлечение конфигурации миссии"""
        try:
            yaml_content = None
            
            # Метод 1: Ищем YAML в markdown блоке ```yaml ... ```
            yaml_match = re.search(r'```yaml\s*(.*?)\s*```', response, re.DOTALL)
            if yaml_match:
                yaml_content = yaml_match.group(1).strip()
                logger.debug("YAML найден в markdown блоке ```yaml```")
            else:
                # Метод 2: Ищем YAML в общем markdown блоке ``` ... ```
                yaml_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
                if yaml_match:
                    yaml_content = yaml_match.group(1).strip()
                    # Убираем возможную метку yaml в начале
                    if yaml_content.startswith('yaml'):
                        yaml_content = yaml_content[4:].strip()
                    logger.debug("YAML найден в markdown блоке ```")
                else:
                    # Метод 3: Ищем блок, начинающийся с "name:" и заканчивающийся пустой строкой или концом
                    yaml_match = re.search(r'(name:\s*["\'].*?)(?=\n\n|\n```|$)', response, re.DOTALL)
                    if yaml_match:
                        yaml_content = yaml_match.group(1).strip()
                        logger.debug("YAML найден по паттерну name:")
                    else:
                        # Метод 4: Пробуем весь ответ как YAML
                        yaml_content = response.strip()
                        logger.debug("Используем весь ответ как YAML")
            
            # Парсим YAML
            try:
                mission_config = yaml.safe_load(yaml_content)
            except yaml.YAMLError as yaml_err:
                logger.error(f"Ошибка парсинга YAML: {yaml_err}")
                logger.debug(f"Содержимое для парсинга: {yaml_content[:500]}")
                # Пробуем исправить распространенные ошибки
                # Убираем лишние символы и пробуем снова
                cleaned = re.sub(r'```', '', yaml_content)
                cleaned = re.sub(r'^yaml\s*$', '', cleaned, flags=re.MULTILINE)
                try:
                    mission_config = yaml.safe_load(cleaned)
                except yaml.YAMLError:
                    logger.error("Не удалось исправить YAML, возвращаем None")
                    return None
            
            if not mission_config:
                logger.warning("Пустая конфигурация миссии")
                return None
            
            if not isinstance(mission_config, dict):
                logger.error(f"Конфигурация миссии не является словарем: {type(mission_config)}")
                return None
            
            # Если модель вернула только checks или другую часть, создаем базовую структуру
            if "name" not in mission_config and ("checks" in mission_config or len(mission_config) <= 2):
                logger.warning("Модель вернула неполную миссию, создаем базовую структуру")
                # Сохраняем то, что есть
                saved_checks = mission_config.get("checks", [])
                saved_setup = mission_config.get("setup", {})
                saved_objectives = mission_config.get("objectives", [])
                saved_hints = mission_config.get("hints", [])
                
                # Генерируем более детальное описание на основе запроса
                if "скачать" in user_request.lower() or "download" in user_request.lower():
                    mission_name = f"Скачать файл"
                    mission_desc = f"Скачайте файл согласно заданию: {user_request}"
                    objectives = [
                        "Открыть браузер или файловый менеджер",
                        "Найти и скачать требуемый файл",
                        "Проверить, что файл скачан"
                    ]
                    hints = [
                        "Используйте браузер для скачивания файлов",
                        "Скачанные файлы обычно сохраняются в папке Downloads",
                        "Проверьте папку ~/Downloads после скачивания"
                    ]
                elif "создать" in user_request.lower() or "create" in user_request.lower():
                    mission_name = f"Создать файл или папку"
                    mission_desc = f"Создайте файл или папку согласно заданию: {user_request}"
                    objectives = [
                        "Открыть файловый менеджер",
                        "Создать требуемый файл или папку",
                        "Проверить создание"
                    ]
                    hints = [
                        "Используйте файловый менеджер для создания файлов",
                        "Правый клик → Создать для создания новых элементов",
                        "Проверьте папку Documents для созданных файлов"
                    ]
                else:
                    mission_name = f"Миссия: {user_request}"
                    mission_desc = f"Выполните задание: {user_request}"
                    objectives = [f"Выполнить: {user_request}"]
                    hints = [f"Следуйте инструкциям для выполнения: {user_request}"]
                
                # Создаем полную структуру
                mission_config = {
                    "name": mission_name,
                    "description": mission_desc,
                    "level": level.upper(),
                    "difficulty": 2,
                    "estimated_time": 10,
                    "objectives": saved_objectives if saved_objectives else objectives,
                    "hints": saved_hints if saved_hints else hints,
                    "setup": saved_setup if saved_setup else {
                        "directories": ["/root/Downloads", "/root/Documents"]
                    },
                    "checks": saved_checks if saved_checks else []
                }
            
            # Валидация обязательных полей
            required_fields = ["name", "description", "level", "objectives", "checks"]
            for field in required_fields:
                if field not in mission_config:
                    logger.warning(f"Отсутствует обязательное поле: {field}")
                    # Добавляем значения по умолчанию
                    if field == "level":
                        mission_config[field] = level.upper()
                    elif field == "objectives":
                        mission_config[field] = [f"Выполнить: {user_request}"]
                    elif field == "checks":
                        mission_config[field] = []
                    elif field == "name":
                        mission_config[field] = f"Миссия: {user_request}"
                    elif field == "description":
                        mission_config[field] = f"Выполните задание: {user_request}"
            
            # Устанавливаем уровень
            mission_config["level"] = level.upper()
            
            # Нормализация estimated_time - должно быть число
            if "estimated_time" in mission_config:
                et = mission_config["estimated_time"]
                if isinstance(et, str):
                    # Извлекаем число из строки типа "10-15 минут" или "10 минут"
                    numbers = re.findall(r'\d+', et)
                    if numbers:
                        mission_config["estimated_time"] = int(numbers[0])
                    else:
                        mission_config["estimated_time"] = 10
                elif not isinstance(et, (int, float)):
                    mission_config["estimated_time"] = 10
            
            # Нормализация путей - заменяем /home/user на /root
            self._normalize_paths(mission_config)
            
            # Нормализация checks - преобразуем неправильный формат в правильный
            if "checks" in mission_config:
                mission_config["checks"] = self._normalize_checks(mission_config["checks"], user_request)
            
            # Валидация checks - убеждаемся, что это список
            if "checks" in mission_config and not isinstance(mission_config["checks"], list):
                logger.warning("Checks не является списком, преобразуем")
                mission_config["checks"] = []
            
            # Если checks пустой или невалидный, создаем базовую проверку
            if not mission_config.get("checks") or len(mission_config["checks"]) == 0:
                logger.warning("Checks пустой, создаем базовую проверку")
                mission_config["checks"] = [{
                    "name": "Базовая проверка выполнения",
                    "type": "file_exists",
                    "path": "/root/Documents/temp_check.txt",
                    "file_type": "file",
                    "points": 100
                }]
            
            # Добавляем значения по умолчанию
            if "difficulty" not in mission_config:
                mission_config["difficulty"] = 2
            if "estimated_time" not in mission_config:
                mission_config["estimated_time"] = 10
            
            # Валидация checks - проверяем структуру каждого элемента
            valid_checks = []
            for check in mission_config["checks"]:
                if isinstance(check, dict) and "type" in check:
                    # Исправление типа dir_exists -> file_exists с file_type: "directory"
                    if check.get("type") == "dir_exists":
                        check["type"] = "file_exists"
                        if "file_type" not in check:
                            check["file_type"] = "directory"
                    
                    # Добавляем обязательные поля, если их нет
                    if "name" not in check:
                        check["name"] = f"Проверка {check.get('type', 'unknown')}"
                    if "points" not in check:
                        check["points"] = 50
                    
                    # Нормализация file_type для file_exists
                    if check.get("type") == "file_exists" and "file_type" not in check:
                        # Если путь заканчивается без расширения и нет file_type, предполагаем директорию
                        path = check.get("path", "")
                        if path and not any(path.endswith(ext) for ext in [".txt", ".jpg", ".pdf", ".docx", ".sh"]):
                            check["file_type"] = "directory"
                        else:
                            check["file_type"] = "file"
                    
                    # Нормализация file_content - expected должен быть строкой
                    if check.get("type") == "file_content":
                        # Исправление неправильных операторов
                        operator = check.get("operator", "contains")
                        if operator not in ["contains", "equals", "regex", "starts_with", "ends_with"]:
                            logger.warning(f"Неправильный operator '{operator}' для file_content, заменяем на 'contains'")
                            check["operator"] = "contains"
                        
                        if "expected" in check:
                            expected = check["expected"]
                            # Если expected - это boolean или число, преобразуем в строку
                            if isinstance(expected, bool):
                                check["expected"] = "true" if expected else "false"
                            elif isinstance(expected, (int, float)):
                                check["expected"] = str(expected)
                            elif isinstance(expected, dict):
                                # Если это объект с lines, объединяем в строку
                                if "lines" in expected and isinstance(expected["lines"], list):
                                    check["expected"] = "\n".join(str(line) for line in expected["lines"])
                                else:
                                    check["expected"] = str(expected)
                            elif isinstance(expected, list):
                                check["expected"] = "\n".join(str(item) for item in expected)
                            elif not isinstance(expected, str):
                                check["expected"] = str(expected)
                        else:
                            check["expected"] = ""
                    
                    # Нормализация command_output
                    if check.get("type") == "command_output":
                        if "operator" not in check:
                            check["operator"] = "contains"
                        if "expected" not in check:
                            check["expected"] = ""
                    
                    # Генерируем путь, если его нет
                    if "path" not in check and check.get("type") in ["file_exists", "file_content"]:
                        check["path"] = f"/root/Documents/{self._generate_file_name_from_request(user_request)}.txt"
                    
                    # Нормализация путей в check
                    if "path" in check and isinstance(check["path"], str):
                        check["path"] = check["path"].replace("/home/user", "/root").replace("/home/your_username", "/root")
                    if "command" in check and isinstance(check["command"], str):
                        check["command"] = check["command"].replace("/home/user", "/root").replace("/home/your_username", "/root")
                    
                    valid_checks.append(check)
                else:
                    logger.warning(f"Пропускаем невалидный check: {check}")
            mission_config["checks"] = valid_checks
            
            return mission_config
            
        except yaml.YAMLError as e:
            logger.error(f"Ошибка парсинга YAML: {e}")
            return None
        except Exception as e:
            logger.error(f"Ошибка парсинга ответа LLM: {e}")
            return None
    
    def _normalize_paths(self, mission_config: Dict[str, Any]) -> None:
        """Нормализация путей в конфигурации миссии - замена /home/user на /root"""
        # Нормализация путей в setup
        if "setup" in mission_config and isinstance(mission_config["setup"], dict):
            setup = mission_config["setup"]
            
            # Нормализация директорий
            if "directories" in setup and isinstance(setup["directories"], list):
                setup["directories"] = [
                    path.replace("/home/user", "/root").replace("/home/your_username", "/root")
                    if isinstance(path, str) else path
                    for path in setup["directories"]
                ]
            
            # Нормализация файлов
            if "files" in setup and isinstance(setup["files"], list):
                for file_entry in setup["files"]:
                    if isinstance(file_entry, dict) and "path" in file_entry:
                        file_entry["path"] = file_entry["path"].replace("/home/user", "/root").replace("/home/your_username", "/root")
        
        # Нормализация путей в checks (предварительная, более детальная будет в валидации checks)
        if "checks" in mission_config and isinstance(mission_config["checks"], list):
            for check in mission_config["checks"]:
                if isinstance(check, dict):
                    if "path" in check and isinstance(check["path"], str):
                        check["path"] = check["path"].replace("/home/user", "/root").replace("/home/your_username", "/root")
                    if "command" in check and isinstance(check["command"], str):
                        check["command"] = check["command"].replace("/home/user", "/root").replace("/home/your_username", "/root")
    
    def _normalize_checks(self, checks: Any, user_request: str) -> List[Dict[str, Any]]:
        """Нормализация checks - преобразование неправильного формата в правильный"""
        if not checks:
            return []
        
        # Если checks - это список, проверяем каждый элемент
        if isinstance(checks, list):
            normalized = []
            for check in checks:
                if isinstance(check, dict):
                    # Проверяем структуру
                    if "type" in check:
                        normalized.append(check)
                    else:
                        logger.warning(f"Check без типа, пропускаем: {check}")
                elif isinstance(check, str):
                    # Если это строка, пытаемся создать простой check
                    logger.warning(f"Check как строка, преобразуем: {check}")
                    normalized.append({
                        "name": f"Проверка: {check}",
                        "type": "file_exists",
                        "path": f"/root/Documents/{self._generate_file_name_from_request(user_request)}.txt",
                        "file_type": "file",
                        "points": 50
                    })
            return normalized
        
        # Если checks - это словарь (неправильный формат), преобразуем
        if isinstance(checks, dict):
            logger.warning("Checks в неправильном формате (словарь вместо списка), преобразуем")
            normalized = []
            
            # Обрабатываем случаи типа file_exists: true, file_exists: "path" и т.д.
            check_types = {
                "file_exists": "file_exists",
                "file_content": "file_content",
                "command_output": "command_output"
            }
            
            for key, check_type in check_types.items():
                if key in checks:
                    value = checks[key]
                    check_obj = {
                        "name": f"Проверка {key}",
                        "type": check_type,
                        "points": 50
                    }
                    
                    if check_type == "file_exists":
                        # Если value - это путь (строка) или True, создаем check
                        if isinstance(value, str) and value:
                            check_obj["path"] = value
                        elif value is True or value == "true":
                            # Если просто True, генерируем путь
                            check_obj["path"] = f"/root/Documents/{self._generate_file_name_from_request(user_request)}.txt"
                        else:
                            # Если значение неопределенное, генерируем путь
                            check_obj["path"] = f"/root/Documents/{self._generate_file_name_from_request(user_request)}.txt"
                        check_obj["file_type"] = "file"
                        normalized.append(check_obj)
                    
                    elif check_type == "file_content":
                        check_obj["path"] = f"/root/Documents/{self._generate_file_name_from_request(user_request)}.txt"
                        check_obj["operator"] = "contains"
                        if isinstance(value, str):
                            check_obj["expected"] = value
                        else:
                            check_obj["expected"] = ""
                        normalized.append(check_obj)
                    
                    elif check_type == "command_output":
                        if isinstance(value, str):
                            check_obj["command"] = value
                        else:
                            check_obj["command"] = "echo 'test'"
                        check_obj["expected"] = ""
                        normalized.append(check_obj)
            
            # Если ничего не нашлось, создаем базовую проверку
            if not normalized:
                normalized.append({
                    "name": "Базовая проверка",
                    "type": "file_exists",
                    "path": f"/root/Documents/{self._generate_file_name_from_request(user_request)}.txt",
                    "file_type": "file",
                    "points": 100
                })
            
            return normalized
        
        logger.warning(f"Неизвестный тип checks: {type(checks)}, возвращаем пустой список")
        return []
    
    def _generate_file_name_from_request(self, user_request: str) -> str:
        """Генерирует имя файла на основе запроса пользователя"""
        # Берем ключевые слова из запроса
        words = user_request.lower().split()
        # Убираем стоп-слова
        stop_words = {"хочу", "научиться", "научить", "создать", "создавать", "на", "в", "с", "из", "по"}
        words = [w for w in words if w not in stop_words]
        # Берем первые 2-3 слова
        if words:
            filename = "_".join(words[:2])
            # Убираем все небуквенные символы
            filename = re.sub(r'[^a-zа-я0-9_]', '', filename)
            if len(filename) < 3:
                filename = "document"
            return filename
        return "document"
    
    def _generate_mission_id(self, username: str, user_request: str) -> str:
        """Генерирует уникальный ID миссии на основе username и запроса"""
        import hashlib
        from datetime import datetime
        
        # Создаем хеш из username и запроса
        hash_input = f"{username}_{user_request}_{datetime.now().isoformat()}"
        hash_obj = hashlib.md5(hash_input.encode())
        hash_hex = hash_obj.hexdigest()[:8]
        
        # Создаем читаемый ID
        # Берем первые слова из запроса и добавляем хеш
        words = user_request.lower().split()[:3]
        readable_part = "_".join(words[:2]) if len(words) >= 2 else "custom"
        readable_part = re.sub(r'[^a-z0-9_]', '', readable_part)
        
        return f"personal_{username}_{readable_part}_{hash_hex}"


def get_mission_generator() -> MissionGenerator:
    """Получить экземпляр генератора миссий"""
    return MissionGenerator()
