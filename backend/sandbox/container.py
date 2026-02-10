"""Контейнерная песочница на базе Podman/Docker (поддерживает Debian-based дистрибутивы и Astra Linux)"""
import asyncio
import json
import subprocess
import os
import shutil
import socket
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


def _get_host_ip() -> str:
    """Получить IP адрес хоста для доступа из локальной сети"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


def _detect_container_command() -> str:
    """Автоматически определить доступную команду (docker или podman)"""
    if settings.PODMAN_BINARY and settings.PODMAN_BINARY != "podman":
        cmd = settings.PODMAN_BINARY.split()[0]
        if shutil.which(cmd):
            return settings.PODMAN_BINARY
    
    if shutil.which("docker"):
        return "docker"
    
    if shutil.which("podman"):
        return "podman"
    
    return settings.PODMAN_BINARY


class ContainerSandbox:
    """Управление изолированным контейнером для миссии"""
    
    def __init__(self, mission_id: str, level: str, image: str = None, use_vnc: bool = True, distro: str = None):
        self.mission_id = mission_id
        self.level = level
        self.use_vnc = use_vnc
        
        self.container_cmd = _detect_container_command()
        if distro is None:
            distro = settings.DEFAULT_DISTRO
        
        # Для уровня B не используем VNC, нужен базовый образ без GUI
        if image is None:
            if self.level.upper() == "B":
                # Для уровня B используем базовые образы без GUI
                image = settings.DISTRO_BASE_IMAGES.get(distro, settings.DISTRO_BASE_IMAGES["debian"])
                logger.info(f"[LEVEL B] Выбран базовый образ для distro={distro}: {image}")
                self.use_vnc = False  # Отключаем VNC для уровня B
            else:
                # Для уровня A используем GUI образы
                image = settings.DISTRO_GUI_IMAGES.get(distro, settings.DISTRO_GUI_IMAGES["debian"])
                logger.info(f"[LEVEL A] Выбран GUI образ для distro={distro}: {image}")
        
        self.image = image
        self._original_image = image  # Сохраняем оригинальный образ для fallback
        logger.info(f"[FINAL] Финальный образ для {level}: {self.image}, use_vnc={self.use_vnc}")
        if use_vnc and level == "A" and "gui-vnc" not in self.image and "astra-vnc" not in self.image:
            # Пытаемся найти GUI образ для текущего дистрибутива
            gui_image = settings.DISTRO_GUI_IMAGES.get(distro)
            if gui_image:
                self.image = gui_image
                logger.info(f"Автоматически выбран GUI образ для дистрибутива {distro}: {self.image}")
        
        self.container_name = f"astra-trainer-{mission_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.container_id: Optional[str] = None
        self.vnc_port: Optional[int] = None
        self.novnc_port: Optional[int] = None
        self.ssh_port: Optional[int] = None
        self.status: str = "created"
        self.container_user: Optional[str] = None
        self._last_error: Optional[str] = None
        
    async def _image_exists(self, image_name: str) -> bool:
        """Проверить существование образа"""
        try:
            container_cmd = _detect_container_command()
            cmd_name = container_cmd.split()[0]
            
            result = await asyncio.create_subprocess_exec(
                cmd_name, "images", "--format", "{{.Repository}}:{{.Tag}}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                images = stdout.decode().strip().split('\n')
                # Проверяем точное совпадение или без localhost/ префикса
                for img in images:
                    if img == image_name or img.replace('localhost/', '') == image_name.replace('localhost/', ''):
                        return True
            return False
        except Exception as e:
            logger.warning(f"Ошибка проверки образа {image_name}: {e}")
            return False
    
    async def create(self) -> bool:
        """Создать контейнер (rootless режим для Podman или Docker)"""
        logger.info(f"[CREATE] === НАЧАЛО СОЗДАНИЯ КОНТЕЙНЕРА ДЛЯ МИССИИ {self.mission_id} ===")
        try:
            container_cmd = _detect_container_command()
            base_cmd = container_cmd.split()
            cmd_name = base_cmd[0]
            if not shutil.which(cmd_name):
                logger.error(f"Команда {cmd_name} не найдена в PATH")
                logger.error("💡 Установите Docker или Podman:")
                logger.error("   - Для WSL: убедитесь, что Docker Desktop запущен в Windows")
                logger.error("   - Для Linux: sudo apt-get install docker.io или podman")
                return False
            
            try:
                result = await asyncio.create_subprocess_exec(
                    cmd_name, "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await result.wait()
                if result.returncode != 0:
                    logger.error(f"Команда {cmd_name} не работает (код возврата: {result.returncode})")
                    logger.error("💡 Убедитесь, что Docker Desktop запущен в Windows (для WSL)")
                    return False
                logger.info(f"Используется контейнерная команда: {cmd_name}")
            except FileNotFoundError:
                logger.error(f"Команда {cmd_name} не найдена")
                logger.error("💡 Установите Docker или Podman:")
                logger.error("   - Для WSL: убедитесь, что Docker Desktop запущен в Windows")
                logger.error("   - Для Linux: sudo apt-get install docker.io или podman")
                return False
            except Exception as e:
                logger.error(f"Ошибка проверки команды {cmd_name}: {e}")
                return False
            
            cmd = base_cmd + [
                "run",
                "-d",
                "--name", self.container_name,
                "--memory", settings.SANDBOX_MEMORY_LIMIT,
                "--cpus", settings.SANDBOX_CPU_LIMIT,
            ]
            
            # Для уровня B не используем --rm, чтобы контейнер не удалялся автоматически
            # Для уровня A используем --rm для автоматической очистки после остановки VNC
            if self.level.upper() != "B":
                cmd.insert(-2, "--rm")
            
            is_podman = "podman" in cmd_name.lower()
            is_docker = "docker" in cmd_name.lower()
            
            if is_podman and settings.PODMAN_ROOTLESS:
                cmd.extend([
                    "--userns=keep-id",
                ])
            elif is_docker:
                pass
            else:
                cmd.extend([
                    "--security-opt", "label=disable",
                ])
            
            if self.use_vnc:
                self.vnc_port = await self._find_free_port(settings.VNC_PORT_START)
                self.novnc_port = await self._find_free_port(settings.NOVNC_PORT_START)
                
                is_astra_vnc = "astra-vnc" in self.image.lower()
                novnc_container_port = 80 if is_astra_vnc else 6080
                vnc_container_port = 5900
                
                cmd.extend([
                    "-p", f"0.0.0.0:{self.vnc_port}:{vnc_container_port}",
                    "-p", f"0.0.0.0:{self.novnc_port}:{novnc_container_port}",
                    "-e", "DISPLAY=:0",
                    "-e", f"VNC_PORT={vnc_container_port}",
                    "-e", f"NOVNC_PORT={novnc_container_port}",
                    "-e", f"VNC_RESOLUTION={settings.VNC_RESOLUTION}",
                ])
                
                logger.info(f"VNC порты: VNC={self.vnc_port}->{vnc_container_port}, noVNC={self.novnc_port}->{novnc_container_port} (проброшены на 0.0.0.0)")
            elif self.level.upper() == "B":
                # Для уровня B настраиваем SSH
                self.ssh_port = await self._find_free_port(settings.SSH_PORT_START)
                ssh_container_port = 22
                
                cmd.extend([
                    "-p", f"0.0.0.0:{self.ssh_port}:{ssh_container_port}",
                ])
                
                logger.info(f"SSH порт: {self.ssh_port}->{ssh_container_port} (проброшен на 0.0.0.0)")
            
            level_dir = settings.MISSIONS_DIR / f"level_{self.level.lower()}"
            if level_dir.exists():
                cmd.extend([
                    "-v", f"{level_dir}:/mission:ro",
                ])
            
            # Проверяем существование образа перед созданием контейнера
            logger.info(f"[CREATE] Проверка существования образа: {self.image}")
            image_exists = await self._image_exists(self.image)
            
            # Если образ не найден, пытаемся использовать fallback образы
            if not image_exists:
                logger.warning(f"[CREATE] ⚠️ Образ {self.image} не найден, пытаемся найти альтернативный...")
                
                # Для уровня B пробуем стандартные образы Debian/Ubuntu
                if self.level.upper() == "B":
                    fallback_images = [
                        "debian:12",
                        "debian:11",
                        "ubuntu:22.04",
                        "ubuntu:20.04"
                    ]
                    for fallback_image in fallback_images:
                        logger.info(f"[CREATE] Проверка fallback образа: {fallback_image}")
                        if await self._image_exists(fallback_image):
                            logger.info(f"[CREATE] ✅ Найден fallback образ: {fallback_image}")
                            self.image = fallback_image
                            image_exists = True
                            break
                        # Если образа нет локально, пробуем его скачать
                        logger.info(f"[CREATE] Попытка скачать образ {fallback_image}...")
                        try:
                            pull_cmd = base_cmd + ["pull", fallback_image]
                            pull_result = await asyncio.create_subprocess_exec(
                                *pull_cmd,
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE
                            )
                            stdout_pull, stderr_pull = await pull_result.communicate()
                            if pull_result.returncode == 0:
                                logger.info(f"[CREATE] ✅ Образ {fallback_image} успешно скачан")
                                self.image = fallback_image
                                image_exists = True
                                break
                            else:
                                stderr_text = stderr_pull.decode() if stderr_pull else ""
                                logger.warning(f"[CREATE] Не удалось скачать {fallback_image}: {stderr_text[:200]}")
                        except Exception as e:
                            logger.warning(f"[CREATE] Ошибка при скачивании {fallback_image}: {e}")
                
                # Если все fallback образы не подошли
                if not image_exists:
                    error_msg = f"Образ {self._original_image} не найден и не удалось найти/скачать альтернативный образ."
                    logger.error(f"[CREATE] {error_msg}")
                    logger.error(f"[CREATE] 💡 Для использования образа Astra Linux выполните:")
                    logger.error(f"[CREATE]    docker build -t localhost/astra-linux:latest <путь_к_dockerfile>")
                    logger.error(f"[CREATE] 💡 Или используйте стандартный образ Debian/Ubuntu")
                    self._last_error = error_msg
                    return False
            else:
                logger.info(f"[CREATE] ✅ Образ {self.image} найден")
            
            # Для уровня B нужна долгоживущая команда, чтобы контейнер не остановился
            if self.level.upper() == "B":
                # Запускаем контейнер с командой, которая будет работать постоянно
                # Используем простой while true loop - работает везде
                # Используем sleep 200 внутри цикла, чтобы не нагружать CPU
                cmd.append(self.image)
                cmd.extend([
                    "sh", "-c", "while true; do sleep 200; done"  # Простой бесконечный цикл для уровня B
                ])
                logger.info(f"[CREATE] Используется команда для уровня B: sh -c 'while true; do sleep 200; done'")
            else:
                cmd.append(self.image)
            
            logger.info(f"[CREATE] Запуск команды создания контейнера для миссии {self.mission_id}")
            logger.info(f"[CREATE] Полная команда docker run: {' '.join(cmd)}")
            try:
                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                logger.info(f"[CREATE] Команда запущена, ожидаем результат...")
                stdout, stderr = await result.communicate()
                logger.info(f"[CREATE] Команда завершена, returncode={result.returncode}")
            except Exception as e:
                logger.error(f"[CREATE] Исключение при выполнении docker run: {e}", exc_info=True)
                self._last_error = f"Ошибка выполнения команды docker run: {str(e)}"
                return False
            
            # Логируем результат сразу после выполнения
            if stderr:
                stderr_text = stderr.decode()
                if stderr_text.strip():
                    logger.warning(f"[CREATE] stderr от docker run: {stderr_text[:500]}")
                else:
                    logger.info(f"[CREATE] stderr пустой")
            else:
                logger.info(f"[CREATE] stderr отсутствует")
            if stdout:
                stdout_text = stdout.decode()
                logger.info(f"[CREATE] stdout от docker run: {stdout_text[:200]}")
            else:
                logger.warning(f"[CREATE] stdout отсутствует!")
            
            logger.info(f"[CREATE] Проверка returncode: {result.returncode}")
            if result.returncode != 0:
                error_output = stderr.decode() if stderr else stdout.decode()
                if not error_output or not error_output.strip():
                    error_output = stdout.decode() if stdout else "Неизвестная ошибка при создании контейнера"
                logger.error(f"[CREATE] Ошибка создания контейнера: {error_output}")
                logger.error(f"[CREATE] Команда была: {' '.join(cmd)}")
                # Сохраняем ошибку для последующего использования
                self._last_error = error_output.strip() if error_output else "Не удалось создать контейнер"
                return False
            
            self.container_id = stdout.decode().strip() if stdout else ""
            logger.info(f"[CREATE] Получен container_id: '{self.container_id}' (длина: {len(self.container_id)})")
            if not self.container_id:
                stdout_str = stdout.decode() if stdout else "НЕТ"
                stderr_str = stderr.decode() if stderr else "НЕТ"
                logger.error(f"[CREATE] ❌ Пустой container_id после создания! stdout: '{stdout_str}', stderr: '{stderr_str}'")
                self._last_error = f"Пустой container_id. stdout: {stdout_str[:200]}, stderr: {stderr_str[:200]}"
                return False
            
            self.status = "running"
            logger.info(f"[CREATE] Контейнер создан: {self.container_name} (ID: {self.container_id[:12]})")
            logger.info(f"[CREATE] ОТЛАДКА: Дошли до проверки статуса, container_id={self.container_id[:12]}")
            
            # КРИТИЧЕСКИ ВАЖНО: НЕМЕДЛЕННО проверяем статус контейнера БЕЗ ЗАДЕРЖКИ
            # Контейнер может исчезнуть/остановиться мгновенно, поэтому проверяем СРАЗУ
            logger.info(f"[CREATE] КРИТИЧЕСКАЯ ПРОВЕРКА: Немедленная проверка статуса контейнера (БЕЗ задержки)...")
            logger.info(f"[CREATE] ОТЛАДКА: Начинаем проверку статуса через docker ps")
            
            # Проверяем статус контейнера через docker ps напрямую (используем container_id для надежности)
            container_exists_and_running = False
            try:
                # Используем container_id для более надежной проверки
                cmd_ps = self.container_cmd.split() + ["ps", "-a", "--filter", f"id={self.container_id[:12]}", "--format", "{{.Names}}\t{{.Status}}\t{{.ID}}"]
                logger.info(f"[CREATE] Выполняю команду проверки статуса: {' '.join(cmd_ps)}")
                result_ps = await asyncio.create_subprocess_exec(
                    *cmd_ps,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout_ps, stderr_ps = await result_ps.communicate()
                logger.info(f"[CREATE] Результат docker ps: код={result_ps.returncode}, stdout={stdout_ps.decode()[:200]}, stderr={stderr_ps.decode()[:200]}")
                if result_ps.returncode == 0:
                    ps_output = stdout_ps.decode().strip()
                    logger.info(f"[CREATE] 📊 Статус контейнера через docker ps: {ps_output if ps_output else 'НЕ НАЙДЕН'}")
                    if ps_output:
                        if "Up" in ps_output or "running" in ps_output.lower():
                            logger.info(f"[CREATE] ✅ Контейнер запущен и работает")
                            container_exists_and_running = True
                        elif "Exited" in ps_output or "Stopped" in ps_output or "Exit" in ps_output or "Dead" in ps_output:
                            logger.error(f"[CREATE] ❌ КОНТЕЙНЕР ОСТАНОВИЛСЯ СРАЗУ ПОСЛЕ СОЗДАНИЯ!")
                            # Получаем детальную информацию (используем container_id для надежности)
                            cmd_inspect = self.container_cmd.split() + ["inspect", self.container_id[:12], "--format", "{{.State.Status}}|{{.State.ExitCode}}|{{.State.Error}}"]
                            result_inspect = await asyncio.create_subprocess_exec(
                                *cmd_inspect,
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE
                            )
                            stdout_inspect, stderr_inspect = await result_inspect.communicate()
                            if result_inspect.returncode == 0:
                                inspect_output = stdout_inspect.decode().strip()
                                parts = inspect_output.split('|')
                                if len(parts) >= 2:
                                    status = parts[0]
                                    exit_code = parts[1]
                                    error = parts[2] if len(parts) > 2 else ""
                                    logger.error(f"[CREATE] State: {status}, ExitCode: {exit_code}, Error: {error}")
                            # Получаем логи контейнера
                            logs_cmd = self.container_cmd.split() + ["logs", "--tail", "100", self.container_name]
                            logs_result = await asyncio.create_subprocess_exec(
                                *logs_cmd,
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE
                            )
                            logs_stdout, logs_stderr = await logs_result.communicate()
                            if logs_stdout:
                                logger.error(f"[CREATE] Логи контейнера:\n{logs_stdout.decode()}")
                            if logs_stderr:
                                logger.error(f"[CREATE] Ошибки в логах:\n{logs_stderr.decode()}")
                            # КРИТИЧНО: контейнер остановился, не продолжаем создание
                            return False
                    else:
                        logger.error(f"[CREATE] ❌ Контейнер не найден в docker ps сразу после создания!")
                        return False
                else:
                    logger.warning(f"[CREATE] Не удалось проверить статус через docker ps: {stderr_ps.decode()}")
                    # Если не удалось проверить - предполагаем, что контейнер не работает
                    container_exists_and_running = False
            except Exception as e:
                logger.error(f"[CREATE] Ошибка проверки статуса: {e}", exc_info=True)
                container_exists_and_running = False
            
            # Если контейнер не найден или остановился - прерываем создание
            if not container_exists_and_running:
                logger.error(f"[CREATE] ❌ КРИТИЧЕСКАЯ ОШИБКА: Контейнер не запущен или не существует!")
                return False
            
            # Дополнительная проверка через _check_container_status
            status_immediate = await self._check_container_status()
            logger.info(f"[CREATE] Статус через _check_container_status: {'RUNNING' if status_immediate else 'NOT RUNNING'}")
            if not status_immediate:
                logger.error(f"[CREATE] ⚠️ Контейнер {self.container_name} не запущен сразу после создания!")
                # Получаем статус контейнера немедленно
                try:
                    cmd_ps = self.container_cmd.split() + ["ps", "-a", "--filter", f"name={self.container_name}", "--format", "{{.Names}}\t{{.Status}}"]
                    result_ps = await asyncio.create_subprocess_exec(
                        *cmd_ps,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout_ps, stderr_ps = await result_ps.communicate()
                    if result_ps.returncode == 0:
                        ps_output = stdout_ps.decode().strip()
                        logger.error(f"[CREATE] Статус контейнера (немедленно): {ps_output}")
                        if "Exited" in ps_output or "Stopped" in ps_output or "Exit" in ps_output:
                            # Контейнер остановился, получаем логи
                            logger.error(f"[CREATE] ⚠️ КОНТЕЙНЕР ОСТАНОВИЛСЯ! Получаем логи...")
                            logs_cmd = self.container_cmd.split() + ["logs", "--tail", "100", self.container_name]
                            logs_result = await asyncio.create_subprocess_exec(
                                *logs_cmd,
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE
                            )
                            logs_stdout, logs_stderr = await logs_result.communicate()
                            if logs_stdout:
                                logger.error(f"[CREATE] Логи остановленного контейнера (немедленно):\n{logs_stdout.decode()}")
                            if logs_stderr:
                                logger.error(f"[CREATE] Ошибки в логах (немедленно):\n{logs_stderr.decode()}")
                            
                            # Получаем ExitCode и полную информацию о состоянии
                            cmd_inspect = self.container_cmd.split() + ["inspect", self.container_name]
                            result_inspect = await asyncio.create_subprocess_exec(
                                *cmd_inspect,
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE
                            )
                            stdout_inspect, stderr_inspect = await result_inspect.communicate()
                            if result_inspect.returncode == 0:
                                import json
                                inspect_data = json.loads(stdout_inspect.decode())
                                if inspect_data and len(inspect_data) > 0:
                                    state = inspect_data[0].get("State", {})
                                    exit_code = state.get('ExitCode', -1)
                                    error_msg = state.get('Error', '')
                                    logger.error(f"[CREATE] ExitCode контейнера: {exit_code}")
                                    if error_msg:
                                        logger.error(f"[CREATE] Причина остановки: {error_msg}")
                                    # Проверяем запущенную команду
                                    config = inspect_data[0].get("Config", {})
                                    cmd = config.get("Cmd", [])
                                    logger.error(f"[CREATE] Команда контейнера: {cmd}")
                except Exception as e:
                    logger.error(f"[CREATE] Ошибка проверки статуса (немедленно): {e}", exc_info=True)
                return False
            
            logger.info(f"[CREATE] ✓ Контейнер {self.container_name} запущен и работает")
            
            # Ждем немного, чтобы контейнер точно запустился
            await asyncio.sleep(1)
            
            # Проверяем логи контейнера, чтобы убедиться, что он работает
            try:
                logs_cmd = self.container_cmd.split() + ["logs", self.container_name]
                logs_result = await asyncio.create_subprocess_exec(
                    *logs_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                logs_stdout, logs_stderr = await logs_result.communicate()
                if logs_stdout:
                    logger.debug(f"[CREATE] Логи контейнера: {logs_stdout.decode()[:500]}")
                if logs_stderr and result.returncode != 0:
                    logger.warning(f"[CREATE] Ошибки в логах контейнера: {logs_stderr.decode()[:500]}")
            except Exception as e:
                logger.warning(f"[CREATE] Не удалось получить логи контейнера: {e}")
            
            await asyncio.sleep(1)
            
            # Проверяем, что контейнер запущен несколько раз с задержкой
            max_retries = 5
            for i in range(max_retries):
                status_check = await self._check_container_status()
                if status_check:
                    logger.info(f"[CREATE] Контейнер {self.container_name} запущен и работает")
                    break
                else:
                    logger.warning(f"[CREATE] Попытка {i+1}/{max_retries}: Контейнер еще не запущен, ждем...")
                    await asyncio.sleep(1)
            else:
                logger.error(f"[CREATE] Контейнер {self.container_name} не запустился после {max_retries} попыток")
                # Пробуем получить информацию о контейнере и его статус
                try:
                    # Проверяем статус контейнера
                    cmd_ps = self.container_cmd.split() + ["ps", "-a", "--filter", f"name={self.container_name}", "--format", "{{.Names}}\t{{.Status}}"]
                    result_ps = await asyncio.create_subprocess_exec(
                        *cmd_ps,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout_ps, stderr_ps = await result_ps.communicate()
                    if result_ps.returncode == 0:
                        ps_output = stdout_ps.decode().strip()
                        logger.info(f"[CREATE] Статус контейнера: {ps_output}")
                        if "Exited" in ps_output or "Stopped" in ps_output or "Exit" in ps_output:
                            # Контейнер остановился, получаем логи для диагностики
                            logger.error(f"[CREATE] ⚠️ Контейнер остановился! Получаем логи...")
                            logs_cmd = self.container_cmd.split() + ["logs", "--tail", "100", self.container_name]
                            logs_result = await asyncio.create_subprocess_exec(
                                *logs_cmd,
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE
                            )
                            logs_stdout, logs_stderr = await logs_result.communicate()
                            if logs_stdout:
                                logger.error(f"[CREATE] Логи остановленного контейнера:\n{logs_stdout.decode()}")
                            if logs_stderr:
                                logger.error(f"[CREATE] Ошибки в логах:\n{logs_stderr.decode()}")
                    
                    # Получаем детальную информацию о контейнере
                    cmd_inspect = self.container_cmd.split() + ["inspect", self.container_name]
                    result_inspect = await asyncio.create_subprocess_exec(
                        *cmd_inspect,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout_inspect, stderr_inspect = await result_inspect.communicate()
                    if result_inspect.returncode == 0:
                        import json
                        inspect_data = json.loads(stdout_inspect.decode())
                        if inspect_data and len(inspect_data) > 0:
                            state = inspect_data[0].get("State", {})
                            status = state.get('Status', 'unknown')
                            exit_code = state.get('ExitCode', -1)
                            error_msg = state.get('Error', '')
                            logger.error(f"[CREATE] ⚠️ Состояние контейнера: Status={status}, ExitCode={exit_code}")
                            if error_msg:
                                logger.error(f"[CREATE] ⚠️ Причина остановки: {error_msg}")
                            if exit_code != 0:
                                logger.error(f"[CREATE] ⚠️ Контейнер завершился с кодом {exit_code}")
                    else:
                        logger.error(f"[CREATE] Ошибка получения информации: {stderr_inspect.decode()}")
                except Exception as e:
                    logger.error(f"[CREATE] Ошибка проверки контейнера: {e}", exc_info=True)
                return False
            
            # СНАЧАЛА проверяем, что контейнер все еще существует и запущен
            container_still_running = await self._check_container_status()
            if not container_still_running:
                logger.error(f"[CREATE] ❌ КРИТИЧЕСКАЯ ОШИБКА: Контейнер {self.container_name} исчез или остановился после проверки статуса!")
                # Проверяем статус контейнера еще раз
                try:
                    cmd_ps = self.container_cmd.split() + ["ps", "-a", "--filter", f"id={self.container_id[:12]}", "--format", "{{.Names}}\t{{.Status}}"]
                    result_ps = await asyncio.create_subprocess_exec(
                        *cmd_ps,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout_ps, stderr_ps = await result_ps.communicate()
                    if result_ps.returncode == 0:
                        ps_output = stdout_ps.decode().strip()
                        if ps_output:
                            logger.error(f"[CREATE] Контейнер найден, статус: {ps_output}")
                        else:
                            logger.error(f"[CREATE] ❌ Контейнер полностью удален из Docker!")
                except Exception as e:
                    logger.error(f"[CREATE] Ошибка проверки статуса: {e}")
                return False
            
            # Для уровня B временно root; ниже _ensure_sandbox_user_for_b создаст sandboxuser и переключит на него
            if self.level.upper() == "B":
                self.container_user = "root"
                logger.info(f"[CREATE] Для уровня B: будет создан пользователь sandboxuser (до setup)")
            elif "astra-vnc" in self.image.lower():
                self.container_user = "root"
                logger.info(f"[CREATE] Используется пользователь root для образа astra-vnc")
            else:
                logger.info(f"[CREATE] Определение пользователя контейнера для миссии {self.mission_id}...")
                try:
                    # Сначала проверяем, что контейнер все еще существует
                    if not await self._check_container_status():
                        logger.warning(f"[CREATE] Контейнер не найден при определении пользователя, используем root")
                        self.container_user = "root"
                    else:
                        await self._detect_container_user()
                        # Проверяем, что container_user не является сообщением об ошибке
                        if self.container_user and ("Error response from daemon" in str(self.container_user) or "No such container" in str(self.container_user)):
                            logger.warning(f"[CREATE] Обнаружена ошибка в container_user, используем root")
                            self.container_user = "root"
                        logger.info(f"[CREATE] Определён пользователь: {self.container_user}")
                except Exception as e:
                    logger.error(f"[CREATE] Ошибка определения пользователя: {e}", exc_info=True)
                    # Для уровня B используем root по умолчанию
                    self.container_user = "root" if self.level.upper() == "B" else "sandboxuser"
            
            # Для уровня B создаём пользователя до setup, чтобы файлы создавались в его домашней директории
            if self.level.upper() == "B":
                await self._ensure_sandbox_user_for_b()

            logger.info(f"[SETUP] === НАЧАЛО ВЫПОЛНЕНИЯ SETUP ДЛЯ МИССИИ {self.mission_id} ===")
            try:
                await self._run_setup_after_create()
                logger.info(f"[SETUP] === SETUP ДЛЯ МИССИИ {self.mission_id} ВЫПОЛНЕН УСПЕШНО ===")
            except Exception as e:
                logger.error(f"[SETUP] === ОШИБКА ВЫПОЛНЕНИЯ SETUP ДЛЯ МИССИИ {self.mission_id}: {e} ===", exc_info=True)
            
            # Для уровня B настраиваем SSH сервер
            if self.level.upper() == "B":
                logger.info(f"[SSH] Настройка SSH сервера для миссии {self.mission_id}")
                try:
                    await self._setup_ssh_server()
                    logger.info(f"[SSH] SSH сервер настроен успешно")
                except Exception as e:
                    logger.error(f"[SSH] Ошибка настройки SSH сервера: {e}", exc_info=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Исключение при создании контейнера: {e}")
            return False
    
    async def start(self) -> bool:
        """Запустить контейнер"""
        if not self.container_id:
            return await self.create()
        
        try:
            cmd = self.container_cmd.split() + ["start", self.container_name]
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            
            if result.returncode == 0:
                self.status = "running"
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка запуска контейнера: {e}")
            return False
    
    async def stop(self) -> bool:
        """Остановить контейнер"""
        if not self.container_id:
            return True
        
        try:
            cmd = self.container_cmd.split() + ["stop", self.container_name]
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            
            self.status = "stopped"
            return True
        except Exception as e:
            logger.error(f"Ошибка остановки контейнера: {e}")
            return False
    
    async def remove(self) -> bool:
        """Удалить контейнер"""
        if not self.container_id:
            return True
        
        try:
            cmd = self.container_cmd.split() + ["rm", "-f"]
            result = await asyncio.create_subprocess_exec(
                *cmd,
                self.container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            
            self.status = "removed"
            self.container_id = None
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления контейнера: {e}")
            return False
    
    async def exec_command(self, command: str, user: str = None) -> tuple[str, int]:
        """Выполнить команду в контейнере"""
        if not self.container_id:
            logger.error(f"Контейнер {self.container_name} не существует, невозможно выполнить команду")
            return "", 1
        
        # Проверяем, что контейнер запущен
        if not await self._check_container_status():
            logger.error(f"Контейнер {self.container_name} не запущен, невозможно выполнить команду")
            return f"Error: container {self.container_name} is not running", 1
        
        if user is None:
            user = self.container_user or "sandboxuser"
        
        try:
            # Используем container_id вместо container_name для большей надежности
            container_ref = self.container_id[:12] if self.container_id else self.container_name
            cmd = self.container_cmd.split() + ["exec", "-u", user, container_ref, "sh", "-c", command]
            logger.debug(f"Выполнение команды в контейнере {container_ref} (user={user}): {command}")
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            output = stdout.decode() + stderr.decode()
            
            # Проверяем на ошибки Docker/Podman
            if "Error response from daemon" in output or "No such container" in output:
                logger.error(f"Ошибка Docker/Podman при выполнении команды: {output}")
                return output, 1
            
            logger.debug(f"Команда выполнена, код возврата: {result.returncode}, вывод: {output[:200]}")
            return output, result.returncode
        except Exception as e:
            logger.error(f"Ошибка выполнения команды '{command}' в контейнере: {e}", exc_info=True)
            return str(e), 1
    
    async def get_info(self) -> Dict[str, Any]:
        """Получить информацию о контейнере"""
        if not self.container_id:
            return {}
        
        try:
            cmd = self.container_cmd.split() + ["inspect", self.container_name]
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            data = json.loads(stdout.decode())
            container_info = data[0] if data else {}
            
            if self.vnc_port or self.novnc_port:
                container_info["vnc_info"] = {
                    "vnc_port": self.vnc_port,
                    "novnc_port": self.novnc_port,
                    "novnc_url": f"http://localhost:{self.novnc_port}/vnc.html" if self.novnc_port else None,
                    "enabled": True
                }
            
            if self.ssh_port:
                container_info["ssh_info"] = {
                    "ssh_port": self.ssh_port,
                    "ssh_user": self.container_user or "root",
                    "ssh_password": settings.SSH_PASSWORD,
                    "enabled": True
                }
            
            return container_info
        except Exception as e:
            logger.error(f"Ошибка получения информации: {e}")
            return {}
    
    async def get_vnc_url(self) -> Optional[str]:
        """Получить URL для подключения к noVNC с автоматическим вводом пароля"""
        if not self.novnc_port:
            return None
        
        is_astra_vnc = "astra-vnc" in self.image.lower()
        novnc_path = "/vnc.html"
        host = "localhost"
        password = settings.VNC_PASSWORD
        return f"http://{host}:{self.novnc_port}{novnc_path}?password={password}&autoconnect=true&resize=scale"
    
    async def wait_for_vnc(self, timeout: int = 60) -> bool:
        """Ожидание готовности VNC сервера"""
        if not self.novnc_port:
            return False
        
        import socket
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', self.novnc_port))
                sock.close()
                
                if result == 0:
                    logger.info(f"VNC сервер готов на порту {self.novnc_port}")
                    return True
            except Exception:
                pass
            
            await asyncio.sleep(2)
        
        logger.warning(f"VNC сервер не запустился за {timeout} секунд")
        return False
    
    async def _detect_container_user(self):
        """Определить пользователя контейнера (root, sandboxuser, user или astrauser)"""
        # Для уровня B используем root по умолчанию
        if self.level.upper() == "B":
            self.container_user = "root"
            logger.info(f"Для уровня B используется пользователь root")
            return
        
        try:
            output, code = await self.exec_command("ps aux | grep -E '(vnc|xfce|fly|websockify)' | grep -v grep | head -1 | awk '{print $1}'", user="root")
            if code == 0 and output.strip() and output.strip() != "root" and "Error response from daemon" not in output:
                self.container_user = output.strip()
                logger.info(f"Определён пользователь контейнера из процессов VNC/GUI: {self.container_user}")
                return
        except Exception:
            pass
        
        for username in ["sandboxuser", "user", "astrauser"]:
            try:
                output, code = await self.exec_command(f"test -d /home/{username} && echo 'exists' || echo 'not_found'", user="root")
                if code == 0 and "exists" in output and "Error response from daemon" not in output:
                    self.container_user = username
                    logger.info(f"Определён пользователь контейнера по домашней директории: {username}")
                    return
            except Exception:
                continue
        
        try:
            output, code = await self.exec_command("test -d /root && echo 'exists' || echo 'not_found'", user="root")
            if code == 0 and "exists" in output and "Error response from daemon" not in output:
                self.container_user = "root"
                logger.info(f"Используется root (найдена директория /root)")
                return
        except Exception:
            pass
        
        self.container_user = "root"
        logger.warning(f"Не удалось определить пользователя контейнера, используется по умолчанию: {self.container_user}")
    
    async def _check_container_status(self) -> bool:
        """Проверить, что контейнер запущен"""
        try:
            # Сначала пробуем по имени
            cmd = self.container_cmd.split() + ["ps", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"]
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            output = stdout.decode().strip()
            
            if result.returncode == 0 and self.container_name in output:
                logger.debug(f"Контейнер {self.container_name} найден через ps")
                return True
            
            # Если не нашли по имени, пробуем по ID
            if self.container_id:
                cmd_id = self.container_cmd.split() + ["ps", "--filter", f"id={self.container_id}", "--format", "{{.ID}}"]
                result_id = await asyncio.create_subprocess_exec(
                    *cmd_id,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout_id, _ = await result_id.communicate()
                if result_id.returncode == 0 and self.container_id[:12] in stdout_id.decode():
                    logger.debug(f"Контейнер {self.container_id[:12]} найден через ps по ID")
                    return True
            
            logger.debug(f"Контейнер {self.container_name} не найден в списке запущенных. Output: {output}, stderr: {stderr.decode()}")
            return False
        except Exception as e:
            logger.error(f"Ошибка проверки статуса контейнера: {e}")
            return False
    
    async def _find_free_port(self, start_port: int) -> int:
        """Найти свободный порт"""
        import socket
        port = start_port
        while port < start_port + 100:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result != 0:
                return port
            port += 1
        raise RuntimeError("Не удалось найти свободный порт")
    
    async def _run_setup_after_create(self):
        """Выполнить setup секцию миссии после создания контейнера"""
        logger.info(f"[SETUP] _run_setup_after_create вызван для миссии {self.mission_id}")
        try:
            import yaml
            
            # Определяем путь к миссии (стандартная или персональная)
            if self.mission_id.startswith("personal_"):
                # Персональная миссия: извлекаем username из mission_id
                # Формат: personal_{username}_{readable_part}_{hash}
                parts = self.mission_id.split("_", 2)
                if len(parts) >= 2:
                    username = parts[1]
                    mission_dir = settings.MISSIONS_DIR / "personal" / username / self.mission_id
                else:
                    logger.warning(f"[SETUP] Не удалось извлечь username из mission_id: {self.mission_id}")
                    mission_dir = settings.MISSIONS_DIR / f"level_{self.level.lower()}" / self.mission_id
            else:
                # Стандартная миссия
                mission_dir = settings.MISSIONS_DIR / f"level_{self.level.lower()}" / self.mission_id
            
            config_file = mission_dir / "mission.yaml"
            
            logger.info(f"[SETUP] Поиск конфигурации миссии: {config_file}")
            logger.info(f"[SETUP] Путь существует? {config_file.exists()}")
            if not config_file.exists():
                logger.warning(f"[SETUP] Конфигурация миссии не найдена: {config_file}")
                return
            
            logger.info(f"[SETUP] Загрузка конфигурации из {config_file}")
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            setup = config.get("setup", {})
            logger.info(f"[SETUP] Setup секция загружена: {setup}")
            if not setup:
                logger.info("[SETUP] Setup секция пуста, пропускаем")
                return
            
            logger.info(f"[SETUP] Выполнение setup для миссии {self.mission_id} после создания контейнера")
            
            container_user = self.container_user or "sandboxuser"
            if container_user == "root":
                user_home = "/root"
            else:
                home_output, home_code = await self.exec_command(f"echo ~{container_user}", user=container_user)
                user_home = home_output.strip() if home_code == 0 else f"/home/{container_user}"
            logger.info(f"Домашняя директория пользователя {container_user}: {user_home}")
            
            def replace_user_path(path: str) -> str:
                """Заменяет /home/sandboxuser, /home/user на реальный путь пользователя"""
                if container_user == "root":
                    return path.replace("/home/sandboxuser", user_home).replace("/home/user", user_home)
                else:
                    return path.replace("/home/sandboxuser", user_home).replace("/home/user", user_home).replace("/root", user_home)
            
            directories = setup.get("directories", [])
            for directory in directories:
                original_dir = directory
                directory = replace_user_path(directory)
                logger.info(f"[SETUP] Создание директории: {original_dir} -> {directory}")
                try:
                    output, code = await self.exec_command(f"mkdir -p '{directory}'", user=container_user)
                    if code == 0:
                        logger.info(f"[SETUP] ✓ Директория создана: {directory}")
                        await self.exec_command(f"chmod 755 '{directory}'", user=container_user)
                    else:
                        logger.warning(f"[SETUP] ✗ Не удалось создать директорию {directory}: код {code}, output: {output}")
                except Exception as e:
                    logger.error(f"[SETUP] Ошибка создания директории {directory}: {e}")
            
            files = setup.get("files", [])
            for file_spec in files:
                file_path = file_spec.get("path")
                file_path = replace_user_path(file_path)
                file_spec["path"] = file_path
                
                file_source = file_spec.get("source", None)
                file_content = file_spec.get("content", None)
                file_mode = file_spec.get("mode", "644")
                
                if not file_path:
                    logger.warning("Путь к файлу не указан в setup.files")
                    continue
                
                try:
                    parent_dir = file_path.rsplit('/', 1)[0] if '/' in file_path else '.'
                    await self.exec_command(f"mkdir -p '{parent_dir}'", user=container_user)
                    
                    if file_source:
                        if file_source.startswith("../"):
                            source_path = f"/mission/{file_source.replace('../', '')}"
                        elif file_source.startswith("./"):
                            source_path = f"/mission/{self.mission_id}/{file_source.replace('./', '')}"
                        elif "/" in file_source:
                            source_path = f"/mission/{file_source}"
                        else:
                            source_path = f"/mission/{self.mission_id}/{file_source}"
                        logger.info(f"[SETUP] Копирование файла из {source_path} в {file_path}")
                        output, code = await self.exec_command(
                            f"cp '{source_path}' '{file_path}' 2>&1", user=container_user
                        )
                        if code == 0:
                            logger.info(f"[SETUP] ✓ Файл скопирован из {source_path} в {file_path}")
                        else:
                            logger.error(f"[SETUP] ✗ Не удалось скопировать файл из {source_path} в {file_path}: код {code}, output: {output}")
                    elif file_content is not None:
                        content_str = str(file_content)
                        escaped_content = content_str.replace("\\", "\\\\").replace("'", "'\"'\"'").replace("$", "\\$").replace("`", "\\`")
                        output, code = await self.exec_command(
                            f"printf '%s\\n' '{escaped_content}' > '{file_path}'", user=container_user
                        )
                        if code == 0:
                            logger.debug(f"Файл создан с содержимым: {file_path}")
                        else:
                            logger.warning(f"Не удалось создать файл {file_path}: код {code}, output: {output}")
                    else:
                        output, code = await self.exec_command(f"touch '{file_path}'", user=container_user)
                        if code == 0:
                            logger.debug(f"Пустой файл создан: {file_path}")
                    
                    await self.exec_command(f"chmod {file_mode} '{file_path}'", user=container_user)
                    await self.exec_command(f"chown {container_user}:{container_user} '{file_path}'", user="root")
                    
                except Exception as e:
                    logger.error(f"Ошибка обработки файла {file_path}: {e}", exc_info=True)
            
            commands = setup.get("commands", [])
            for cmd in commands:
                try:
                    output, code = await self.exec_command(cmd, user=container_user)
                    if code == 0:
                        logger.debug(f"Команда setup выполнена: {cmd}")
                    else:
                        logger.warning(f"Команда setup завершилась с кодом {code}: {cmd}, output: {output}")
                except Exception as e:
                    logger.error(f"Ошибка выполнения команды setup {cmd}: {e}")
            
            logger.info(f"Setup для миссии {self.mission_id} завершён")
        except Exception as e:
            logger.error(f"Ошибка выполнения setup для миссии {self.mission_id}: {e}", exc_info=True)
    
    async def _ensure_sandbox_user_for_b(self):
        """Создать пользователя sandboxuser для уровня B до выполнения setup (файлы создаются в его домашней директории)."""
        logger.info(f"[CREATE] Проверка пользователя sandboxuser для уровня B")
        output, code = await self.exec_command("id -u sandboxuser 2>/dev/null", user="root")
        if code != 0:
            logger.info(f"[CREATE] Создание пользователя sandboxuser")
            await self.exec_command("useradd -m -s /bin/bash sandboxuser", user="root")
            password = settings.SSH_PASSWORD
            await self.exec_command(f"echo 'sandboxuser:{password}' | chpasswd", user="root")
            await self.exec_command("mkdir -p /home/sandboxuser/.ssh", user="root")
            await self.exec_command("chown -R sandboxuser:sandboxuser /home/sandboxuser", user="root")
        else:
            await self.exec_command(f"echo 'sandboxuser:{settings.SSH_PASSWORD}' | chpasswd", user="root")
        self.container_user = "sandboxuser"
        logger.info(f"[CREATE] Для уровня B используется пользователь: sandboxuser (домашняя директория: /home/sandboxuser)")

    async def _setup_ssh_server(self):
        """Настроить SSH сервер для уровня B"""
        logger.info(f"[SSH] Начало настройки SSH сервера")
        
        # Проверяем, установлен ли SSH сервер
        output, code = await self.exec_command("which sshd", user="root")
        if code != 0:
            logger.info(f"[SSH] Установка openssh-server")
            # Устанавливаем openssh-server
            if "debian" in self.image.lower() or "ubuntu" in self.image.lower():
                await self.exec_command("apt-get update -qq", user="root")
                output, code = await self.exec_command(
                    "DEBIAN_FRONTEND=noninteractive apt-get install -y -qq openssh-server", 
                    user="root"
                )
                if code != 0:
                    logger.error(f"[SSH] Ошибка установки openssh-server: {output}")
                    raise RuntimeError(f"Не удалось установить openssh-server: {output}")
            else:
                logger.warning(f"[SSH] Неизвестный дистрибутив, попытка установки через apt")
                await self.exec_command("apt-get update -qq", user="root")
                await self.exec_command(
                    "DEBIAN_FRONTEND=noninteractive apt-get install -y -qq openssh-server", 
                    user="root"
                )
        
        # Создаем директорию для SSH
        await self.exec_command("mkdir -p /var/run/sshd", user="root")
        
        # Настраиваем SSH для пароля root
        await self.exec_command("sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config", user="root")
        await self.exec_command("sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config", user="root")
        await self.exec_command("sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config", user="root")
        
        # Устанавливаем пароль для root
        password = settings.SSH_PASSWORD
        await self.exec_command(f"echo 'root:{password}' | chpasswd", user="root")
        
        # Создаем пользователя sandboxuser, если его нет
        output, code = await self.exec_command("id -u sandboxuser 2>/dev/null", user="root")
        if code != 0:
            logger.info(f"[SSH] Создание пользователя sandboxuser")
            await self.exec_command("useradd -m -s /bin/bash sandboxuser", user="root")
            await self.exec_command(f"echo 'sandboxuser:{password}' | chpasswd", user="root")
            await self.exec_command("mkdir -p /home/sandboxuser/.ssh", user="root")
            await self.exec_command("chown -R sandboxuser:sandboxuser /home/sandboxuser", user="root")
            self.container_user = "sandboxuser"
        else:
            # Устанавливаем пароль для существующего пользователя
            await self.exec_command(f"echo 'sandboxuser:{password}' | chpasswd", user="root")
            self.container_user = "sandboxuser"
        
        # Запускаем SSH сервер в фоновом режиме
        logger.info(f"[SSH] Запуск SSH сервера")
        # Используем nohup для запуска в фоне
        output, code = await self.exec_command(
            "nohup /usr/sbin/sshd -D > /dev/null 2>&1 &", 
            user="root"
        )
        
        # Альтернативный способ: используем supervisord или systemd, но для простоты используем nohup
        # Если nohup не работает, пробуем запустить напрямую
        if code != 0:
            logger.warning(f"[SSH] Не удалось запустить через nohup, пробуем напрямую")
            output, code = await self.exec_command("/usr/sbin/sshd", user="root")
        
        # Ждем немного для запуска
        await asyncio.sleep(3)
        
        # Проверяем, что SSH сервер запущен
        output, code = await self.exec_command("ps aux | grep '[s]shd' | head -1", user="root")
        if code != 0 or "sshd" not in output:
            logger.error(f"[SSH] SSH сервер не запустился, код: {code}, output: {output}")
            # Пробуем запустить еще раз в фоне другим способом
            logger.info(f"[SSH] Пробуем альтернативный способ запуска SSH")
            await self.exec_command("(/usr/sbin/sshd -D > /var/log/sshd.log 2>&1 &) && sleep 2", user="root")
            await asyncio.sleep(2)
            
            # Проверяем еще раз
            output, code = await self.exec_command("ps aux | grep '[s]shd' | head -1", user="root")
            if "sshd" not in output:
                logger.error(f"[SSH] ⚠️ SSH сервер все еще не запущен после повторной попытки!")
                logger.error(f"[SSH] Проверка логов SSH: {await self.exec_command('cat /var/log/sshd.log 2>&1 || echo no log', user='root')}")
            else:
                logger.info(f"[SSH] SSH сервер запущен успешно после повторной попытки")
        else:
            logger.info(f"[SSH] SSH сервер запущен успешно: {output.strip()}")
        
        # Проверяем, что порт слушается
        output, code = await self.exec_command("netstat -tuln | grep :22 || ss -tuln | grep :22 || echo 'port check failed'", user="root")
        if ":22" in output:
            logger.info(f"[SSH] ✓ SSH порт 22 слушается: {output.strip()}")
        else:
            logger.warning(f"[SSH] ⚠️ SSH порт 22 не найден в списке слушающих портов: {output}")
        
        logger.info(f"[SSH] SSH сервер настроен, порт на хосте: {self.ssh_port}->22, пользователь: {self.container_user}")

