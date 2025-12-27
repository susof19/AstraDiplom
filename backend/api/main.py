"""Главный файл FastAPI приложения"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from backend.config import settings
from backend.api.routes import missions, sandbox, grader, progress, auth, admin
from backend.sandbox.manager import sandbox_manager
from backend.models.user_db import User  # noqa: F401

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Linux Training Simulator API",
    description="API для тренажёра Linux (поддерживает Debian-based дистрибутивы и Astra Linux)",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("📋 Регистрация API роутов...")
app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["auth"])
logger.info(f"   ✅ Auth роуты зарегистрированы: {settings.API_PREFIX}/auth")
app.include_router(missions.router, prefix=settings.API_PREFIX, tags=["missions"])
logger.info(f"   ✅ Missions роуты зарегистрированы: {settings.API_PREFIX}/missions")
app.include_router(sandbox.router, prefix=settings.API_PREFIX, tags=["sandbox"])
logger.info(f"   ✅ Sandbox роуты зарегистрированы: {settings.API_PREFIX}/sandbox")
app.include_router(grader.router, prefix=settings.API_PREFIX, tags=["grader"])
logger.info(f"   ✅ Grader роуты зарегистрированы: {settings.API_PREFIX}/grader")
app.include_router(progress.router, prefix=settings.API_PREFIX, tags=["progress"])
logger.info(f"   ✅ Progress роуты зарегистрированы: {settings.API_PREFIX}/progress")
app.include_router(admin.router, prefix=f"{settings.API_PREFIX}/admin", tags=["admin"])
logger.info(f"   ✅ Admin роуты зарегистрированы: {settings.API_PREFIX}/admin")
logger.info("✅ Все роуты зарегистрированы")


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    logger.info("=" * 60)
    logger.info("🚀 Запуск Linux Training Simulator API")
    logger.info(f"📡 API будет доступен на: http://{settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"📋 API префикс: {settings.API_PREFIX}")
    logger.info("=" * 60)
    
    try:
        from backend.database import engine, Base
        from backend.models.user_db import User
        logger.info("🔍 Проверка соединения с базой данных...")
        
        with engine.connect() as conn:
            logger.info("✅ Соединение с базой данных установлено")
        
        logger.info("📦 Проверка таблиц базы данных...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Таблицы базы данных готовы")
        
    except Exception as e:
        logger.error(f"❌ Ошибка работы с базой данных: {e}")
        logger.error("💡 Убедитесь, что:")
        logger.error("   1. PostgreSQL установлен и запущен")
        logger.error("   2. База данных создана: trainer_db")
        logger.error("   3. Пользователь создан: trainer_user")
        logger.error("   4. DATABASE_URL в config.py правильный")
        logger.error("💡 Выполните: python backend/init_db.py")
        logger.warning("⚠️  Приложение продолжит работу, но функции аутентификации могут не работать")
    
    try:
        from backend.sandbox.astra_check import run_compatibility_check
        compat = run_compatibility_check()
        if compat["compatible"]:
            logger.info("✅ Система совместима (Podman/Docker доступен)")
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
    for mission_id in list(sandbox_manager.sandboxes.keys()):
        await sandbox_manager.remove_sandbox(mission_id)


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "name": "Linux Training Simulator API",
        "version": "0.1.0",
        "status": "running",
        "description": "Универсальный тренажёр для Debian-based дистрибутивов"
    }


@app.get("/health")
async def health():
    """Проверка здоровья сервиса"""
    return {"status": "healthy"}


@app.get("/api/v1/routes")
async def list_routes():
    """Список всех доступных роутов (для отладки)"""
    routes = []
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else ["GET"]
            })
    return {
        "routes": routes,
        "total": len(routes),
        "api_prefix": settings.API_PREFIX
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)

