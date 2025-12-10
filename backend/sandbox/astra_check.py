"""Проверка совместимости с Astra Linux"""
import subprocess
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


def check_podman_available() -> Tuple[bool, Optional[str]]:
    """Проверить доступность Podman"""
    try:
        result = subprocess.run(
            ["podman", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, None
    except FileNotFoundError:
        return False, "Podman не установлен"
    except Exception as e:
        return False, f"Ошибка проверки: {e}"


def check_rootless_support() -> Tuple[bool, Optional[str]]:
    """Проверить поддержку rootless режима"""
    try:
        # Проверяем, можем ли запустить podman info без sudo
        result = subprocess.run(
            ["podman", "info", "--format", "{{.Host.UserNS}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, "Rootless режим поддерживается"
        return False, "Rootless режим не поддерживается"
    except Exception as e:
        return False, f"Ошибка проверки: {e}"


def check_astra_rootless_helper() -> Tuple[bool, Optional[str]]:
    """Проверить наличие rootless-helper-astra (Astra Linux)"""
    try:
        result = subprocess.run(
            ["which", "rootlessenv"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, "rootless-helper-astra установлен"
        return False, "rootless-helper-astra не установлен (опционально)"
    except Exception as e:
        return False, f"Ошибка проверки: {e}"


def check_user_namespaces() -> Tuple[bool, Optional[str]]:
    """Проверить поддержку user_namespaces (необходимо для rootless)"""
    from pathlib import Path
    import os
    
    # Альтернативная проверка через /proc/sys
    try:
        with open("/proc/sys/user/max_user_namespaces", "r") as f:
            max_ns = int(f.read().strip())
            if max_ns > 0:
                return True, f"user_namespaces поддерживается (max: {max_ns})"
            return False, "user_namespaces отключены"
    except:
        # Проверяем наличие CONFIG_USER_NS в ядре (если доступно)
        try:
            kernel_version = os.uname().release
            config_path = Path(f"/boot/config-{kernel_version}")
            if config_path.exists():
                with open(config_path, "r") as f:
                    content = f.read()
                    if "CONFIG_USER_NS=y" in content:
                        return True, "user_namespaces поддерживается"
                    return False, "user_namespaces не поддерживается (hardened ядро?)"
        except:
            pass
        return False, "Не удалось проверить user_namespaces"


def run_compatibility_check() -> dict:
    """Запустить полную проверку совместимости с Astra Linux"""
    results = {
        "podman_available": check_podman_available(),
        "rootless_support": check_rootless_support(),
        "rootless_helper": check_astra_rootless_helper(),
        "user_namespaces": check_user_namespaces(),
    }
    
    all_ok = all(result[0] for result in results.values())
    
    return {
        "compatible": all_ok,
        "checks": results,
        "recommendations": _get_recommendations(results)
    }


def _get_recommendations(results: dict) -> list:
    """Получить рекомендации на основе результатов проверки"""
    recommendations = []
    
    if not results["podman_available"][0]:
        recommendations.append("Установите Podman: sudo apt install podman")
    
    if not results["user_namespaces"][0]:
        recommendations.append(
            "user_namespaces не поддерживается. Возможно, используется hardened ядро. "
            "Rootless режим недоступен. Используйте привилегированный режим."
        )
    
    if not results["rootless_support"][0] and results["user_namespaces"][0]:
        recommendations.append(
            "Настройте rootless режим: podman system migrate"
        )
    
    if results["rootless_helper"][0]:
        recommendations.append(
            "Обнаружен rootless-helper-astra. Можно использовать: "
            "PODMAN_BINARY='rootlessenv podman' в конфигурации"
        )
    
    return recommendations

