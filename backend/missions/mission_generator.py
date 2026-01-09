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
        
        prompt = f"""Ты помощник для создания учебных миссий Linux.

{level_context.get(level.upper(), level_context["A"])}

Запрос пользователя: {user_request}
{history_context}

Создай миссию в формате YAML. Миссия должна быть:
1. Понятной и выполнимой для указанного уровня
2. Иметь четкие цели (objectives)
3. Включать проверки (checks) для автоматической проверки выполнения
4. Иметь setup секцию для подготовки окружения (если нужно)
5. Включать подсказки (hints) для помощи пользователю

Формат ответа (строго YAML, без дополнительного текста):
```yaml
name: "Название миссии"
description: "Подробное описание задания"
level: "{level.upper()}"
difficulty: 1-5
estimated_time: 5-30 (минуты)

objectives:
  - "Цель 1"
  - "Цель 2"

hints:
  - "Подсказка 1"
  - "Подсказка 2"

setup:
  directories:
    - "/path/to/dir"
  files:
    - path: "/path/to/file"
      content: "содержимое"
      mode: "644"
  commands:
    - "команда для выполнения"

checks:
  - name: "Название проверки"
    type: "file_exists"  # или file_content, command_output
    path: "/path/to/file"
    points: 50
```

ВАЖНО:
- Верни ТОЛЬКО YAML код, без дополнительных объяснений
- Для уровня A: используй только GUI действия, никаких команд терминала
- Для уровня B: можно использовать команды терминала
- Убедись, что все пути корректны
- Checks должны проверять выполнение целей (objectives)

YAML миссии:"""
        
        return prompt
    
    async def _generate_with_lm_studio(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Optional[str]:
        """Генерация через LM Studio"""
        if not AIOHTTP_AVAILABLE:
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
            # Извлекаем YAML из ответа (может быть в markdown блоке)
            yaml_match = re.search(r'```yaml\s*(.*?)\s*```', response, re.DOTALL)
            if yaml_match:
                yaml_content = yaml_match.group(1)
            else:
                # Пробуем найти YAML без markdown
                yaml_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
                if yaml_match:
                    yaml_content = yaml_match.group(1)
                else:
                    # Пробуем весь ответ как YAML
                    yaml_content = response
            
            # Парсим YAML
            mission_config = yaml.safe_load(yaml_content)
            
            if not mission_config:
                logger.warning("Пустая конфигурация миссии")
                return None
            
            # Валидация обязательных полей
            required_fields = ["name", "description", "level", "objectives", "checks"]
            for field in required_fields:
                if field not in mission_config:
                    logger.warning(f"Отсутствует обязательное поле: {field}")
                    # Добавляем значения по умолчанию
                    if field == "level":
                        mission_config[field] = level.upper()
                    elif field == "objectives":
                        mission_config[field] = ["Выполнить задание"]
                    elif field == "checks":
                        mission_config[field] = []
            
            # Устанавливаем уровень
            mission_config["level"] = level.upper()
            
            # Добавляем значения по умолчанию
            if "difficulty" not in mission_config:
                mission_config["difficulty"] = 2
            if "estimated_time" not in mission_config:
                mission_config["estimated_time"] = 10
            
            return mission_config
            
        except yaml.YAMLError as e:
            logger.error(f"Ошибка парсинга YAML: {e}")
            return None
        except Exception as e:
            logger.error(f"Ошибка парсинга ответа LLM: {e}")
            return None
    
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
