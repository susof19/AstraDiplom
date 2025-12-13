# Быстрый старт для WSL

## Установка (один раз)

```bash
# В WSL терминале
cd /path/to/AstraDiplom
chmod +x scripts/quickstart-wsl.sh
./scripts/quickstart-wsl.sh
```

## Запуск

```bash
./start-demo-wsl.sh
```

Откройте в браузере Windows: **http://localhost:3000**

## Остановка

```bash
./stop-demo.sh
```

## Важно для WSL

1. **Docker Desktop** должен быть запущен в Windows
2. **PostgreSQL** запускается автоматически при старте
3. Frontend доступен на `localhost:3000` в браузере Windows

## Проблемы?

См. подробную инструкцию: [WSL-SETUP.md](WSL-SETUP.md)

