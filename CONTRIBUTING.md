# Руководство по внесению вклада

## Как добавить новую миссию

1. Создайте директорию для миссии:
   ```bash
   mkdir -p missions/level_{a|b|c}/{mission_id}
   ```

2. Создайте файл `mission.yaml` (см. `docs/MISSIONS.md`)

3. Протестируйте миссию локально

4. Создайте Pull Request

## Структура кода

- `backend/` - Python FastAPI приложение
- `frontend/web/` - React приложение
- `missions/` - Определения миссий
- `images/` - Dockerfile для образов

## Стиль кода

- **Python**: PEP 8, type hints
- **JavaScript**: ESLint, Prettier
- **YAML**: 2 пробела для отступов

## Тестирование

Перед отправкой PR убедитесь, что:
- Backend запускается без ошибок
- Frontend компилируется
- Миссия проходит проверку grader'ом
- Нет ошибок линтера

## Вопросы?

Создайте Issue с вопросом или предложением.

