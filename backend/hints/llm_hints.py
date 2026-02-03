"""LLM-based система подсказок с поддержкой локальных и облачных моделей"""
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from backend.config import settings

logger = logging.getLogger(__name__)

# Настройки для разных провайдеров
LM_STUDIO_TIMEOUT = 30  # Увеличиваем таймаут для LM Studio
OLLAMA_TIMEOUT = 15
OPENAI_TIMEOUT = 15


class LLMHintProvider:
    """Провайдер подсказок на основе LLM"""
    
    def __init__(self):
        self.provider_type = getattr(settings, 'LLM_PROVIDER', 'lm_studio')  # lm_studio, ollama, openai, heuristic
        self.api_url = getattr(settings, 'LLM_API_URL', 'http://localhost:1234/v1')  # LM Studio по умолчанию
        self.model_name = getattr(settings, 'LLM_MODEL', 'local-model')
        self.enabled = getattr(settings, 'LLM_HINTS_ENABLED', False)  # По умолчанию выключено
    
    def _get_user_level_context(self, level: str, os_type: Optional[str] = None) -> str:
        """Получить контекст об уровне пользователя и ОС"""
        level = level.upper() if level else "A"
        
        # Контекст об ОС
        os_context = self._get_os_context(os_type)
        
        if level == "A":
            return f"""ВАЖНО: Пользователь - НОВИЧОК в Linux. Он:
- Знает очень мало или НИЧЕГО о Linux
- Работает ТОЛЬКО через графический интерфейс (GUI)
- НЕ ИСПОЛЬЗУЕТ терминал и команды
- Полагается только на мышь, меню и визуальные элементы
- Подсказки должны объяснять действия в GUI терминах (клик, меню, кнопка)
- НИКОГДА не предлагайте использовать терминал или команды

{os_context}"""
        elif level == "B":
            return f"""Пользователь - ПРОДВИНУТЫЙ. Он:
- Знает основы Linux
- Может использовать терминал и команды
- Понимает файловую систему
- Подсказки могут включать команды терминала

{os_context}"""
        else:
            return f"""Пользователь - АДМИНИСТРАТОР. Он:
- Опытный пользователь Linux
- Понимает системное администрирование
- Может использовать сложные команды и скрипты

{os_context}"""
    
    def _get_os_context(self, os_type: Optional[str] = None) -> str:
        """Получить контекст об операционной системе"""
        if not os_type:
            return ""
        
        os_contexts = {
            "astra_linux": """ОПЕРАЦИОННАЯ СИСТЕМА: Astra Linux Special Edition
ВАЖНО учитывать особенности Astra Linux:
- Это российская операционная система на базе Debian
- Использует собственную систему прав доступа (ПДП - подсистема дискреционного разграничения доступа)
- Файловый менеджер: Fly (аналог Nautilus/Nautilus)
- Меню приложений: Fly Menu
- Рабочий стол: Fly Desktop (на базе Xfce)
- Для уровня A: объясняй через Fly (файловый менеджер), Fly Menu (меню приложений)
- Названия могут отличаться от стандартных Linux дистрибутивов
- Используй термины: "Fly", "Fly Menu", "Fly Desktop" вместо общих терминов""",
            "ubuntu": """ОПЕРАЦИОННАЯ СИСТЕМА: Ubuntu Linux
- Файловый менеджер: Nautilus (Файлы)
- Меню приложений: Activities Overview или меню приложений
- Рабочий стол: GNOME (по умолчанию) или Unity
- Для уровня A: объясняй через Nautilus, Activities, меню приложений""",
            "debian": """ОПЕРАЦИОННАЯ СИСТЕМА: Debian Linux
- Файловый менеджер: Nautilus или Thunar (в зависимости от окружения)
- Меню приложений: зависит от окружения рабочего стола
- Рабочий стол: может быть GNOME, Xfce, KDE
- Для уровня A: объясняй через стандартный файловый менеджер и меню приложений""",
            "linux": """ОПЕРАЦИОННАЯ СИСТЕМА: Linux (общий)
- Используй общие термины для Linux дистрибутивов
- Файловый менеджер, меню приложений, рабочий стол"""
        }
        
        return os_contexts.get(os_type, os_contexts["linux"])
    
    async def get_hint(
        self,
        mission_id: str,
        mission_config: Dict[str, Any],
        failed_checks: List[Dict[str, Any]],
        check_result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Получить подсказку от LLM"""
        
        # Определяем уровень пользователя и ОС
        level = context.get("level", "A") if context else "A"
        os_type = context.get("os_type") if context else None
        """Получить подсказку от LLM"""
        
        if not self.enabled:
            return None
        
        if self.provider_type == 'heuristic':
            return self._heuristic_hint(failed_checks, mission_config)
        
        try:
            if self.provider_type == 'lm_studio':
                return await self._lm_studio_hint(mission_id, mission_config, failed_checks, check_result, context)
            elif self.provider_type == 'ollama':
                return await self._ollama_hint(mission_id, mission_config, failed_checks, check_result, context)
            elif self.provider_type == 'openai':
                return await self._openai_hint(mission_id, mission_config, failed_checks, check_result, context)
            else:
                logger.warning(f"Неизвестный провайдер LLM: {self.provider_type}")
                return self._heuristic_hint(failed_checks, mission_config)
        except Exception as e:
            logger.error(f"Ошибка получения подсказки от LLM: {e}", exc_info=True)
            # Fallback на эвристику
            return self._heuristic_hint(failed_checks, mission_config)
    
    def _heuristic_hint(self, failed_checks: List[Dict[str, Any]], mission_config: Dict[str, Any]) -> Optional[str]:
        """Эвристическая подсказка (fallback)"""
        if not failed_checks:
            return None
        
        # Простая эвристика на основе типа проверки
        first_failed = failed_checks[0]
        check_type = first_failed.get("type", "")
        check_message = first_failed.get("message", "")
        level = mission_config.get("level", "A").upper()
        is_level_a = level == "A"
        
        if is_level_a:
            # GUI подсказки для уровня A
            hints_map = {
                "file_exists": "Откройте файловый менеджер, перейдите в нужную папку и проверьте наличие файла. Если файла нет, создайте его (правый клик → Создать → Документ).",
                "file_content": "Откройте файл в текстовом редакторе (двойной клик) и проверьте его содержимое. Убедитесь, что текст соответствует требованиям.",
                "command_output": "Проверьте выполнение задачи через графический интерфейс и убедитесь, что результат соответствует требованиям.",
            }
        else:
            # Терминальные подсказки для уровня B+
            hints_map = {
                "file_exists": "Проверьте, что файл существует по указанному пути. Используйте команду 'ls' для просмотра содержимого директории.",
                "file_content": "Проверьте содержимое файла командой 'cat <файл>' и убедитесь, что оно соответствует требованиям.",
                "command_output": "Проверьте вывод команды и убедитесь, что он соответствует ожидаемому результату.",
            }
        
        return hints_map.get(check_type, "Проверьте выполнение задачи и повторите попытку.")
    
    async def _lm_studio_hint(
        self,
        mission_id: str,
        mission_config: Dict[str, Any],
        failed_checks: List[Dict[str, Any]],
        check_result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Получить подсказку от LM Studio (локальный LLM)"""
        
        if not AIOHTTP_AVAILABLE:
            logger.warning("aiohttp не установлен. Установите: pip install aiohttp")
            return None
        
        # Формируем упрощенный промпт
        prompt = self._build_prompt(mission_id, mission_config, failed_checks, check_result, context)
        level = mission_config.get('level', 'A').upper()
        os_type = context.get('os_type') if context else None
        
        # Сначала проверяем доступность модели
        if not await self._check_lm_studio_model():
            logger.warning("LM Studio модель недоступна или не загружена")
            return None
        
        # Упрощенный формат для Mistral моделей - объединяем системное сообщение и промпт
        user_message = f"""Ты помощник для учебного тренажера Linux.

{self._get_user_level_context(level, os_type)}

Задача: {prompt}

ВАЖНО:
- Дай КРАТКУЮ подсказку (1-2 предложения, максимум 150 символов)
- Будь лаконичным и конкретным
- Для уровня A: объясняй ТОЛЬКО через GUI (клик, меню, кнопки, файловый менеджер)
- НИКОГДА не предлагай терминал или команды для уровня A
- Укажи конкретное действие: где кликнуть или что найти
- Учитывай особенности операционной системы, указанной выше
- НЕ пиши длинные инструкции, только краткую подсказку

Подсказка (кратко, 1-2 предложения):"""
        
        # Пробуем несколько вариантов запроса
        variants = [
            # Вариант 1: С системным сообщением
            {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": "Ты помощник учебного тренажера Linux. Дай краткую подсказку (1-2 предложения)."},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7,
                "max_tokens": 100,  # Ограничиваем длину подсказок
                "stream": False,
                "stop": ["\n\n", "###", "---", ".", "!"]  # Стоп-символы для коротких ответов
            },
            # Вариант 2: Без системного сообщения
            {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7,
                "max_tokens": 100,  # Ограничиваем длину подсказок
                "stream": False,
                "stop": ["\n\n", "###", "---", ".", "!"]  # Стоп-символы для коротких ответов
            },
            # Вариант 3: Минималистичный
            {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": f"Подсказка для новичка Linux: {prompt.split('Проваленные проверки:')[0] if 'Проваленные проверки:' in prompt else prompt[:200]}"}
                ],
                "temperature": 0.5,
                "max_tokens": 80,  # Ограничиваем длину подсказок
                "stream": False,
                "stop": ["\n\n", "###", ".", "!"]
            }
        ]
        
        async with aiohttp.ClientSession() as session:
            for i, payload in enumerate(variants, 1):
                try:
                    headers = {
                        "Content-Type": "application/json"
                    }
                    
                    logger.debug(f"Попытка {i}: Отправка запроса к LM Studio с моделью {self.model_name}")
                    
                    async with session.post(
                        f"{self.api_url}/chat/completions",
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        response_text = await response.text()
                        
                        if response.status == 200:
                            try:
                                data = json.loads(response_text) if isinstance(response_text, str) else response_text
                                choices = data.get("choices", [])
                                if choices:
                                    hint = choices[0].get("message", {}).get("content", "").strip()
                                    if hint:
                                        # Очищаем и ограничиваем длину подсказки
                                        hint = hint.strip()
                                        # Убираем лишние переносы строк
                                        hint = ' '.join(hint.split())
                                        # Берем только первое предложение или ограничиваем длину
                                        if len(hint) > 150:
                                            # Обрезаем до первого предложения или до 150 символов
                                            sentences = hint.split('.')
                                            if len(sentences) > 1:
                                                hint = sentences[0] + '.'
                                            else:
                                                hint = hint[:147] + '...'
                                        # Ограничиваем максимум 150 символов
                                        if len(hint) > 150:
                                            hint = hint[:147] + '...'
                                        logger.info(f"LM Studio успешно вернул подсказку (вариант {i}, длина: {len(hint)})")
                                        return hint
                            except (json.JSONDecodeError, KeyError) as e:
                                logger.warning(f"Вариант {i}: Ошибка парсинга ответа: {e}")
                                if i == len(variants):
                                    logger.error(f"Все варианты запросов не сработали. Ответ: {response_text[:300]}")
                        else:
                            logger.warning(f"Вариант {i}: LM Studio вернул код {response.status}: {response_text[:200]}")
                            
                except (aiohttp.ServerTimeoutError, asyncio.TimeoutError):
                    logger.warning(f"Вариант {i}: Таймаут при обращении к LM Studio")
                except aiohttp.ClientError as e:
                    logger.warning(f"Вариант {i}: Ошибка подключения: {e}")
                except Exception as e:
                    logger.warning(f"Вариант {i}: Неожиданная ошибка: {e}")
                    
                # Если это не последняя попытка, пробуем следующий вариант
                if i < len(variants):
                    continue
        
        logger.error("Все попытки запроса к LM Studio не удались")
        return None
    
    async def _check_lm_studio_model(self) -> bool:
        """Проверить, доступна ли модель в LM Studio"""
        if not AIOHTTP_AVAILABLE:
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/models",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get("data", [])
                        model_ids = [m.get("id", "") for m in models]
                        
                        # Проверяем, есть ли наша модель в списке
                        if self.model_name in model_ids:
                            return True
                        
                        # Проверяем частичное совпадение
                        for model_id in model_ids:
                            if self.model_name in model_id or model_id in self.model_name:
                                logger.info(f"Найдена модель: {model_id}, используем её вместо {self.model_name}")
                                self.model_name = model_id
                                return True
                        
                        # Если модель не найдена, используем первую доступную
                        if models:
                            self.model_name = model_ids[0]
                            logger.warning(f"Модель {self.model_name} не найдена, используем {model_ids[0]}")
                            return True
                        
                        return False
                    return False
        except Exception as e:
            logger.warning(f"Ошибка проверки доступности модели: {e}")
            return True  # Продолжаем попытку, даже если проверка не удалась
    
    async def _ollama_hint(
        self,
        mission_id: str,
        mission_config: Dict[str, Any],
        failed_checks: List[Dict[str, Any]],
        check_result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Получить подсказку от Ollama"""
        
        if not AIOHTTP_AVAILABLE:
            logger.warning("aiohttp не установлен. Установите: pip install aiohttp")
            return None
        
        prompt = self._build_prompt(mission_id, mission_config, failed_checks, check_result, context)
        level = mission_config.get('level', 'A').upper()
        os_type = context.get('os_type') if context else None
        
        # Ollama API формат
        payload = {
            "model": self.model_name,
            "prompt": f"""Ты — помощник для учебного тренажера Linux.

{self._get_user_level_context(level, os_type)}

Задача: {prompt}

Дай КРАТКУЮ подсказку (1 предложение, максимум 100 символов) для исправления ошибки.
- Не раскрывай полное решение
- Учитывай особенности операционной системы, указанной выше
- Для уровня A: объясняй только через GUI, НИКОГДА не предлагай терминал
- Будь лаконичным и конкретным

Подсказка (кратко):""",
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 100
            }
        }
        
        ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{ollama_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        hint = data.get("response", "").strip()
                        if hint:
                            # Ограничиваем длину подсказки
                            hint = ' '.join(hint.split())  # Убираем лишние пробелы
                            if len(hint) > 150:
                                sentences = hint.split('.')
                                if len(sentences) > 1:
                                    hint = sentences[0] + '.'
                                else:
                                    hint = hint[:147] + '...'
                            return hint
                    else:
                        logger.warning(f"Ollama API вернул код {response.status}")
            except aiohttp.ClientError as e:
                logger.error(f"Ошибка подключения к Ollama: {e}")
        
        return None
    
    async def _openai_hint(
        self,
        mission_id: str,
        mission_config: Dict[str, Any],
        failed_checks: List[Dict[str, Any]],
        check_result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Получить подсказку от OpenAI API"""
        
        if not AIOHTTP_AVAILABLE:
            logger.warning("aiohttp не установлен. Установите: pip install aiohttp")
            return None
        
        prompt = self._build_prompt(mission_id, mission_config, failed_checks, check_result, context)
        os_type = context.get('os_type') if context else None
        
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key:
            logger.warning("OpenAI API ключ не настроен")
            return None
        
        payload = {
            "model": self.model_name or "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": f"""Ты — помощник для учебного тренажера Linux.

{self._get_user_level_context(mission_config.get('level', 'A'), os_type)}

Дай КРАТКУЮ подсказку (1 предложение, максимум 100 символов), которая:
- Помогает понять ошибку
- НЕ раскрывает полностью решение
- Учитывает уровень знаний пользователя
- Для уровня A: объясняет только GUI, НИКОГДА не предлагай терминал
- Учитывает особенности операционной системы, указанной выше
- Будь лаконичным"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 100  # Ограничиваем длину подсказок
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        hint = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                        if hint:
                            # Ограничиваем длину подсказки
                            hint = ' '.join(hint.split())  # Убираем лишние пробелы
                            if len(hint) > 150:
                                sentences = hint.split('.')
                                if len(sentences) > 1:
                                    hint = sentences[0] + '.'
                                else:
                                    hint = hint[:147] + '...'
                            return hint
                    else:
                        error_text = await response.text()
                        logger.warning(f"OpenAI API вернул код {response.status}: {error_text}")
            except aiohttp.ClientError as e:
                logger.error(f"Ошибка подключения к OpenAI: {e}")
        
        return None
    
    def _build_prompt(
        self,
        mission_id: str,
        mission_config: Dict[str, Any],
        failed_checks: List[Dict[str, Any]],
        check_result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Построить промпт для LLM"""
        
        mission_description = mission_config.get("description", "")
        mission_objectives = mission_config.get("objectives", [])
        
        failed_info = []
        for check in failed_checks[:3]:  # Берем первые 3 для краткости
            failed_info.append(f"- {check.get('name', 'Неизвестно')}: {check.get('message', '')}")
        
        level = mission_config.get("level", "A").upper()
        os_type = context.get('os_type') if context else None
        user_context = self._get_user_level_context(level, os_type)
        
        prompt = f"""Задача миссии (уровень {level}):
{mission_description}

Цели:
{chr(10).join(f"- {obj}" for obj in mission_objectives[:3])}

Проваленные проверки:
{chr(10).join(failed_info)}

{user_context}

Дай КРАТКУЮ подсказку (1 предложение, максимум 100 символов), что нужно исправить.
- Не раскрывай полное решение
- Только направь пользователя к правильному действию
- Для уровня A: объясняй только через GUI (клик, меню, кнопки), НИКОГДА не предлагай терминал или команды
- Учитывай особенности операционной системы, указанной выше
- Будь лаконичным, без длинных инструкций"""
        
        return prompt
    
    async def _chat_with_bot(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        mission_config: Dict[str, Any],
        level: str,
        os_type: Optional[str] = None
    ) -> str:
        """Генерация ответа чат-бота в стиле диалога"""
        
        if not self.enabled:
            return "Извините, чат-бот временно недоступен."
        
        if self.provider_type == 'lm_studio':
            return await self._lm_studio_chat(system_prompt, messages)
        elif self.provider_type == 'ollama':
            return await self._ollama_chat(system_prompt, messages)
        elif self.provider_type == 'openai':
            return await self._openai_chat(system_prompt, messages)
        else:
            # Fallback на эвристику
            return "Я готов помочь! Задайте вопрос о задании."
    
    async def _lm_studio_chat(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]]
    ) -> str:
        """Чат через LM Studio"""
        if not AIOHTTP_AVAILABLE:
            return "Извините, чат-бот временно недоступен."
        
        # Проверяем доступность модели
        if not await self._check_lm_studio_model():
            return "Извините, модель временно недоступна."
        
        # Формируем сообщения для LM Studio
        chat_messages = []
        
        # Добавляем системное сообщение
        chat_messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Добавляем историю диалога
        chat_messages.extend(messages)
        
        payload = {
            "model": self.model_name,
            "messages": chat_messages,
            "temperature": 0.7,
            "max_tokens": 200,  # Ограничиваем длину ответа
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.api_url}/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        choices = data.get("choices", [])
                        if choices:
                            content = choices[0].get("message", {}).get("content", "").strip()
                            if content:
                                # Очищаем ответ
                                content = ' '.join(content.split())  # Убираем лишние пробелы
                                if len(content) > 300:
                                    # Обрезаем до 300 символов
                                    sentences = content.split('.')
                                    if len(sentences) > 1:
                                        content = '. '.join(sentences[:2]) + '.'
                                    else:
                                        content = content[:297] + '...'
                                return content
                    else:
                        logger.warning(f"LM Studio вернул код {response.status}")
            except Exception as e:
                logger.error(f"Ошибка чата через LM Studio: {e}", exc_info=True)
        
        return "Извините, произошла ошибка. Попробуйте еще раз."
    
    async def _ollama_chat(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]]
    ) -> str:
        """Чат через Ollama"""
        if not AIOHTTP_AVAILABLE:
            return "Извините, чат-бот временно недоступен."
        
        # Формируем промпт для Ollama
        conversation = "\n".join([
            f"{'Пользователь' if msg['role'] == 'user' else 'Ассистент'}: {msg['content']}"
            for msg in messages
        ])
        
        prompt = f"""{system_prompt}

{conversation}

Ассистент:"""
        
        ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 200
            }
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{ollama_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data.get("response", "").strip()
                        if content:
                            content = ' '.join(content.split())
                            if len(content) > 300:
                                sentences = content.split('.')
                                if len(sentences) > 1:
                                    content = '. '.join(sentences[:2]) + '.'
                                else:
                                    content = content[:297] + '...'
                            return content
            except Exception as e:
                logger.error(f"Ошибка чата через Ollama: {e}", exc_info=True)
        
        return "Извините, произошла ошибка. Попробуйте еще раз."
    
    async def _openai_chat(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]]
    ) -> str:
        """Чат через OpenAI"""
        if not AIOHTTP_AVAILABLE:
            return "Извините, чат-бот временно недоступен."
        
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key:
            return "Извините, API ключ не настроен."
        
        chat_messages = [
            {"role": "system", "content": system_prompt}
        ]
        chat_messages.extend(messages)
        
        payload = {
            "model": self.model_name or "gpt-3.5-turbo",
            "messages": chat_messages,
            "temperature": 0.7,
            "max_tokens": 200
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                        if content:
                            content = ' '.join(content.split())
                            if len(content) > 300:
                                sentences = content.split('.')
                                if len(sentences) > 1:
                                    content = '. '.join(sentences[:2]) + '.'
                                else:
                                    content = content[:297] + '...'
                            return content
            except Exception as e:
                logger.error(f"Ошибка чата через OpenAI: {e}", exc_info=True)
        
        return "Извините, произошла ошибка. Попробуйте еще раз."
    
    async def test_connection(self) -> Dict[str, Any]:
        """Проверить подключение к LLM сервису"""
        result = {
            "provider": self.provider_type,
            "enabled": self.enabled,
            "connected": False,
            "message": ""
        }
        
        if not self.enabled:
            result["message"] = "LLM подсказки отключены"
            return result
        
        if self.provider_type == 'heuristic':
            result["connected"] = True
            result["message"] = "Используется эвристический метод"
            return result
        
        if not AIOHTTP_AVAILABLE:
            result["message"] = "aiohttp не установлен. Установите: pip install aiohttp"
            return result
        
        try:
            async with aiohttp.ClientSession() as session:
                if self.provider_type == 'lm_studio':
                    async with session.get(
                        f"{self.api_url}/models",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            result["connected"] = True
                            result["message"] = "LM Studio доступен"
                        else:
                            result["message"] = f"LM Studio недоступен (код {response.status})"
                
                elif self.provider_type == 'ollama':
                    ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
                    async with session.get(
                        f"{ollama_url}/api/tags",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            result["connected"] = True
                            result["message"] = "Ollama доступен"
                        else:
                            result["message"] = f"Ollama недоступен (код {response.status})"
                
                elif self.provider_type == 'openai':
                    # Для OpenAI просто проверяем наличие ключа
                    api_key = getattr(settings, 'OPENAI_API_KEY', '')
                    if api_key:
                        result["connected"] = True
                        result["message"] = "OpenAI API ключ настроен"
                    else:
                        result["message"] = "OpenAI API ключ не найден"
        
        except Exception as e:
            result["message"] = f"Ошибка подключения: {str(e)}"
        
        return result


def get_llm_hint_provider() -> LLMHintProvider:
    """Получить экземпляр LLM провайдера"""
    return LLMHintProvider()

