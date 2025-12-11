# 🔐 Система аутентификации

Проект включает полноценную систему аутентификации с регистрацией, входом и восстановлением пароля.

## Возможности

- ✅ Регистрация новых пользователей
- ✅ Вход в систему (JWT токены)
- ✅ Восстановление пароля по секретному коду
- ✅ Изменение пароля (для авторизованных пользователей)
- ✅ Защита API endpoints (требуется аутентификация)
- ✅ Хранение паролей в зашифрованном виде (bcrypt)

## API Endpoints

### Регистрация

```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "user123",
  "password": "securepass123",
  "secret_code": "mysecretcode"
}
```

**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "username": "user123"
}
```

### Вход

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user123",
  "password": "securepass123"
}
```

**Ответ:** Аналогичен регистрации (возвращает JWT токен)

### Восстановление пароля

```bash
POST /api/v1/auth/recover-password
Content-Type: application/json

{
  "username": "user123",
  "secret_code": "mysecretcode",
  "new_password": "newsecurepass123"
}
```

**Ответ:**
```json
{
  "message": "Пароль успешно изменён"
}
```

### Получение информации о пользователе

```bash
GET /api/v1/auth/me
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "username": "user123",
  "created_at": "2024-01-01T12:00:00",
  "last_login": "2024-01-02T10:30:00"
}
```

### Изменение пароля (требует аутентификации)

```bash
POST /api/v1/auth/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "old_password": "oldpass123",
  "new_password": "newpass123"
}
```

## Использование токенов

Все защищённые API endpoints требуют JWT токен в заголовке:

```bash
Authorization: Bearer <your_jwt_token>
```

Токен автоматически добавляется в запросы после успешного входа или регистрации.

## Хранение данных

- Пользователи хранятся в `sandbox_data/users/<username>.json`
- Пароли хешируются с помощью bcrypt
- Секретные коды также хешируются
- JWT токены действительны 7 дней

## Frontend

Frontend автоматически:
- Сохраняет токен в localStorage
- Добавляет токен в заголовки всех запросов
- Перенаправляет на страницу входа при истечении токена
- Защищает приватные маршруты

## Безопасность

- ✅ Пароли никогда не хранятся в открытом виде
- ✅ Используется bcrypt для хеширования
- ✅ JWT токены с истечением срока действия
- ✅ HTTPS рекомендуется для продакшена
- ✅ Валидация входных данных
- ✅ Защита от SQL injection (используется JSON файлы, не SQL)

## Настройка

В `backend/config.py` можно настроить:

```python
JWT_SECRET_KEY: str = "your-secret-key"  # В продакшене через .env
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_DAYS: int = 7
```

**Важно**: В продакшене обязательно измените `JWT_SECRET_KEY` на случайную строку!

## Примеры использования

### Регистрация через curl

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123",
    "secret_code": "mycode123"
  }'
```

### Вход и использование токена

```bash
# Вход
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}' \
  | jq -r '.access_token')

# Использование токена
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

## Защищённые endpoints

Следующие endpoints требуют аутентификации:

- `GET /api/v1/progress` - Получение прогресса
- `POST /api/v1/progress/{mission_id}/complete` - Завершение миссии
- `GET /api/v1/progress/achievements` - Получение достижений
- `POST /api/v1/grader/check/{mission_id}` - Проверка миссии
- `POST /api/v1/sandbox/create` - Создание песочницы
- `GET /api/v1/sandbox/{mission_id}` - Получение информации о песочнице
- `POST /api/v1/auth/change-password` - Изменение пароля

Публичные endpoints (не требуют аутентификации):

- `GET /api/v1/missions` - Список миссий
- `GET /api/v1/missions/{mission_id}` - Информация о миссии
- `POST /api/v1/auth/register` - Регистрация
- `POST /api/v1/auth/login` - Вход
- `POST /api/v1/auth/recover-password` - Восстановление пароля

