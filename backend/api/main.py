"""Главный файл FastAPI приложения"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from backend.config import settings
from backend.api.routes import missions, sandbox, grader, progress
from backend.sandbox.manager import sandbox_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Astra Linux Training Simulator API",
    description="API для тренажёра Astra Linux",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(missions.router, prefix=settings.API_PREFIX, tags=["missions"])
app.include_router(sandbox.router, prefix=settings.API_PREFIX, tags=["sandbox"])
app.include_router(grader.router, prefix=settings.API_PREFIX, tags=["grader"])
app.include_router(progress.router, prefix=settings.API_PREFIX, tags=["progress"])


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    logger.info("Запуск Astra Linux Training Simulator API")
    
    # Проверка совместимости с Astra Linux
    try:
        from backend.sandbox.astra_check import run_compatibility_check
        compat = run_compatibility_check()
        if compat["compatible"]:
            logger.info("✅ Система совместима с Astra Linux")
        else:
            logger.warning("⚠️  Обнаружены проблемы совместимости:")
            for check, (status, msg) in compat["checks"].items():
                if not status:
                    logger.warning(f"  - {check}: {msg}")
            if compat["recommendations"]:
                logger.info("Рекомендации:")
                for rec in compat["recommendations"]:
                    logger.info(f"  - {rec}")
    except Exception as e:
        logger.warning(f"Не удалось проверить совместимость: {e}")
    
    sandbox_manager.start_cleanup_task()


@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при остановке"""
    logger.info("Остановка API")
    # Останавливаем все песочницы
    for mission_id in list(sandbox_manager.sandboxes.keys()):
        await sandbox_manager.remove_sandbox(mission_id)


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "name": "Astra Linux Training Simulator API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Проверка здоровья сервиса"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)

