# Настройка LLM подсказок

Руководство по настройке умных подсказок с использованием локальных или облачных LLM моделей.

## 🎯 Поддерживаемые провайдеры

1. **LM Studio** (рекомендуется для локального использования)
2. **Ollama** (альтернатива для локальных моделей)
3. **OpenAI API** (облачный вариант)
4. **Heuristic** (простая эвристика, без LLM)

## 📦 Вариант 1: LM Studio (Рекомендуется)

### Установка LM Studio

1. Скачайте LM Studio с официального сайта: https://lmstudio.ai/
2. Установите приложение
3. Загрузите легкую модель (рекомендуется):
   - **Qwen2.5-1.5B-Instruct** (~1.5GB) - очень легкая
   - **Phi-3-mini** (~2.3GB) - быстрая и эффективная
   - **Llama-3.2-3B-Instruct** (~2GB) - хорошее качество

### Настройка LM Studio

1. Запустите LM Studio
2. Перейдите в раздел "Local Server"
3. Выберите загруженную модель
4. Запустите локальный сервер (по умолчанию порт 1234)
5. Убедитесь, что сервер работает (должен быть зеленый индикатор)

### Настройка в проекте

Добавьте в `backend/.env`:

```env
# LLM настройки
LLM_HINTS_ENABLED=true
LLM_PROVIDER=lm_studio
LLM_API_URL=http://localhost:1234/v1
LLM_MODEL=local-model
```

**Примечание:** `LLM_MODEL` должно совпадать с названием модели в LM Studio.

## 📦 Вариант 2: Ollama

### Установка Ollama

1. Установите Ollama: https://ollama.ai/
2. Загрузите модель:
   ```bash
   ollama pull qwen2.5:1.5b
   # или
   ollama pull phi3:mini
   ```

### Настройка в проекте

Добавьте в `backend/.env`:

```env
# LLM настройки
LLM_HINTS_ENABLED=true
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:1.5b
OLLAMA_URL=http://localhost:11434
```

## 📦 Вариант 3: OpenAI API

### Настройка

1. Получите API ключ на https://platform.openai.com/
2. Добавьте в `backend/.env`:

```env
# LLM настройки
LLM_HINTS_ENABLED=true
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
OPENAI_API_KEY=sk-your-api-key-here
```

## 🔧 Вариант 4: Эвристика (без LLM)

Если не хотите использовать LLM, система будет использовать простую эвристику:

```env
# LLM настройки
LLM_HINTS_ENABLED=false
LLM_PROVIDER=heuristic
```

## ✅ Проверка подключения

После настройки проверьте подключение:

```bash
# В браузере или curl
curl http://localhost:8000/api/v1/llm/test \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Или используйте API документацию:
- http://localhost:8000/docs → `/api/v1/llm/test`

## 🎯 Рекомендации

### Для разработки/тестирования:
- **LM Studio** с **Qwen2.5-1.5B** - быстро, локально, бесплатно
- **Ollama** с **phi3:mini** - альтернатива LM Studio

### Для продакшена:
- **OpenAI GPT-3.5-turbo** - быстро и качественно, но платно
- **Heuristic** - бесплатно, но менее умные подсказки

## 🔍 Устранение неполадок

### LM Studio не отвечает

1. Проверьте, что сервер запущен в LM Studio
2. Проверьте порт: `curl http://localhost:1234/v1/models`
3. Убедитесь, что модель загружена

### Ollama не отвечает

1. Проверьте, что Ollama запущен: `ollama list`
2. Проверьте порт: `curl http://localhost:11434/api/tags`

### Медленные ответы

- Используйте более легкую модель (Qwen2.5-1.5B или Phi-3-mini)
- Уменьшите `max_tokens` в коде (сейчас 150)
- Используйте эвристику для быстрых подсказок

## 📝 Примеры конфигурации

### Минимальная конфигурация (без LLM)

```env
LLM_HINTS_ENABLED=false
```

### LM Studio с Qwen2.5

```env
LLM_HINTS_ENABLED=true
LLM_PROVIDER=lm_studio
LLM_API_URL=http://localhost:1234/v1
LLM_MODEL=Qwen2.5-1.5B-Instruct-q4_K_M
```

### Ollama с Phi-3

```env
LLM_HINTS_ENABLED=true
LLM_PROVIDER=ollama
LLM_MODEL=phi3:mini
OLLAMA_URL=http://localhost:11434
```

## 🚀 Использование

После настройки LLM подсказки будут автоматически использоваться при проверке миссий, если:
1. `LLM_HINTS_ENABLED=true`
2. ML подсказки включены в настройках пользователя
3. Есть проваленные проверки

Система автоматически выберет лучший источник подсказок:
1. LLM подсказки (если доступны)
2. Статистические подсказки (на основе паттернов)
3. Rule-based подсказки (fallback)

