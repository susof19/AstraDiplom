# Руководство по развертыванию

## Рекомендуемые платформы для демо

### 🥇 1. Railway (Рекомендуется)

**Плюсы:**
- ✅ Бесплатный план: $5 кредитов/месяц (достаточно для демо)
- ✅ Отличная поддержка Docker контейнеров
- ✅ Встроенная поддержка PostgreSQL
- ✅ Простое развертывание через GitHub
- ✅ Автоматические деплои при push
- ✅ Поддержка нескольких сервисов (backend + frontend + DB)
- ✅ Переменные окружения через UI

**Минусы:**
- Ограниченные ресурсы на бесплатном плане
- Может быть медленнее, чем платные альтернативы

**Стоимость:** Бесплатно (с ограничениями)

**Ссылка:** https://railway.app

---

### 🥈 2. Fly.io

**Плюсы:**
- ✅ Бесплатный план: 3 shared-cpu-1x VMs
- ✅ Отличная поддержка Docker
- ✅ Глобальная сеть (низкая задержка)
- ✅ Поддержка портов (важно для VNC)
- ✅ Простое развертывание

**Минусы:**
- Нужна отдельная база данных (можно использовать Supabase)
- Немного сложнее настройка

**Стоимость:** Бесплатно (с ограничениями)

**Ссылка:** https://fly.io

---

### 🥉 3. Render

**Плюсы:**
- ✅ Бесплатный план для статических сайтов (frontend)
- ✅ Web Services с ограничениями (backend)
- ✅ Встроенная поддержка PostgreSQL
- ✅ Автоматические деплои из GitHub

**Минусы:**
- Бесплатные сервисы "засыпают" после 15 минут бездействия
- Ограниченные ресурсы
- Может быть медленнее

**Стоимость:** Бесплатно (с ограничениями)

**Ссылка:** https://render.com

---

## Гибридный подход (Рекомендуется для демо)

### Frontend: Vercel или Netlify
- ✅ Бесплатно и быстро
- ✅ Отличная поддержка React
- ✅ CDN по всему миру
- ✅ Автоматические деплои

### Backend: Railway или Fly.io
- ✅ Поддержка Docker
- ✅ Переменные окружения
- ✅ Поддержка портов

### Database: Supabase или Railway PostgreSQL
- ✅ Бесплатный PostgreSQL
- ✅ Автоматические бэкапы
- ✅ Веб-интерфейс для управления

---

## Пошаговая инструкция для Railway (Рекомендуется)

### 1. Подготовка проекта

Создайте файлы для деплоя:

#### `railway.json` (в корне проекта)
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile.backend"
  },
  "deploy": {
    "startCommand": "uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### `Dockerfile.backend` (в корне проекта)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV API_HOST=0.0.0.0
ENV API_PORT=${PORT:-8000}

# Открытие порта
EXPOSE ${PORT:-8000}

# Запуск приложения
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
```

#### `.railwayignore` (в корне проекта)
```
node_modules/
frontend/web/node_modules/
frontend/web/build/
__pycache__/
*.pyc
.env
.git/
```

### 2. Развертывание на Railway

1. **Создайте аккаунт на Railway:**
   - Перейдите на https://railway.app
   - Войдите через GitHub

2. **Создайте новый проект:**
   - Нажмите "New Project"
   - Выберите "Deploy from GitHub repo"
   - Выберите ваш репозиторий

3. **Добавьте PostgreSQL:**
   - В проекте нажмите "+ New"
   - Выберите "Database" → "PostgreSQL"
   - Railway автоматически создаст базу и переменные окружения

4. **Настройте переменные окружения:**
   - В настройках сервиса → Variables
   - Добавьте необходимые переменные из `.env`

5. **Настройте порты:**
   - Railway автоматически назначает порт через переменную `PORT`
   - Обновите `API_PORT` в коде для использования `PORT`

### 3. Развертывание Frontend на Vercel

1. **Создайте аккаунт на Vercel:**
   - Перейдите на https://vercel.com
   - Войдите через GitHub

2. **Импортируйте проект:**
   - Нажмите "Add New Project"
   - Выберите ваш репозиторий
   - Root Directory: `frontend/web`
   - Build Command: `npm run build`
   - Output Directory: `build`

3. **Настройте переменные окружения:**
   - Добавьте `REACT_APP_API_URL` с URL вашего Railway backend
   - Например: `https://your-app.railway.app`

---

## Альтернатива: Fly.io

### 1. Установка Fly CLI
```bash
curl -L https://fly.io/install.sh | sh
```

### 2. Логин
```bash
fly auth login
```

### 3. Создание приложения
```bash
cd backend
fly launch
```

### 4. Настройка `fly.toml`
```toml
app = "your-app-name"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile.backend"

[env]
  PORT = "8080"

[[services]]
  internal_port = 8080
  protocol = "tcp"

  [[services.ports]]
    port = 80
    handlers = ["http"]
    force_https = true

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
```

---

## Важные замечания для демо

### Ограничения бесплатных планов:

1. **Ресурсы:**
   - Ограниченная RAM/CPU
   - Может быть медленнее при нагрузке

2. **Docker контейнеры:**
   - Railway и Fly.io поддерживают Docker
   - Render имеет ограничения

3. **Порты VNC:**
   - Railway: автоматическое пробрасывание портов
   - Fly.io: нужно настроить в `fly.toml`
   - Render: ограниченная поддержка

4. **База данных:**
   - Railway: встроенная PostgreSQL
   - Fly.io: нужна внешняя (Supabase)
   - Render: встроенная PostgreSQL

### Рекомендации для демо:

1. **Используйте Railway для всего стека:**
   - Backend + Frontend + Database в одном проекте
   - Проще настроить
   - Один сервис для управления

2. **Или гибридный подход:**
   - Frontend на Vercel (быстрее)
   - Backend на Railway (Docker поддержка)
   - Database на Supabase (бесплатно)

3. **Оптимизация:**
   - Минимизируйте размер Docker образов
   - Используйте `.dockerignore`
   - Кешируйте зависимости

---

## Переменные окружения для продакшена

Создайте файл `.env.production`:

```env
# API
API_HOST=0.0.0.0
API_PORT=${PORT}
API_PREFIX=/api/v1

# Database
DATABASE_URL=${DATABASE_URL}  # Автоматически от Railway/Supabase

# CORS
ALLOWED_ORIGINS=https://your-frontend.vercel.app,https://your-frontend.netlify.app

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# Sandbox
MOCK_SANDBOX=false
PODMAN_BINARY=docker

# VNC
VNC_PASSWORD=sandbox123
```

---

## Полезные ссылки

- **Railway:** https://railway.app/docs
- **Fly.io:** https://fly.io/docs
- **Render:** https://render.com/docs
- **Vercel:** https://vercel.com/docs
- **Supabase:** https://supabase.com/docs

---

## Troubleshooting

### Проблема: Docker контейнеры не запускаются
**Решение:** Убедитесь, что Docker доступен в контейнере (может потребоваться Docker-in-Docker или использование внешнего Docker API)

### Проблема: VNC порты не работают
**Решение:** Настройте пробрасывание портов в конфигурации платформы

### Проблема: База данных не подключается
**Решение:** Проверьте переменную `DATABASE_URL` и убедитесь, что она правильно настроена

---

## Следующие шаги

1. Выберите платформу (рекомендуется Railway)
2. Создайте аккаунт
3. Подготовьте Dockerfile
4. Настройте переменные окружения
5. Разверните backend
6. Разверните frontend
7. Протестируйте демо

