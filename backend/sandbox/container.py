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
        
        if image is None:
            image = settings.DISTRO_GUI_IMAGES.get(distro, settings.DISTRO_GUI_IMAGES["debian"])
            logger.info(f"[LEVEL A] Выбран GUI образ для distro={distro}: {image}")
        
        self.image = image
        logger.info(f"[FINAL] Финальный образ для {level}: {self.image}")
        if use_vnc and level == "A" and "gui-vnc" not in self.image:
            # Пытаемся найти GUI образ для текущего дистрибутива
            gui_image = settings.DISTRO_GUI_IMAGES.get(distro)
            if gui_image:
                self.image = gui_image
                logger.info(f"Автоматически выбран GUI образ для дистрибутива {distro}: {self.image}")
        
        self.container_name = f"astra-trainer-{mission_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.container_id: Optional[str] = None
        self.vnc_port: Optional[int] = None
        self.novnc_port: Optional[int] = None
        self.status: str = "created"
        self.container_user: Optional[str] = None
        
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
                "--rm",
                "--memory", settings.SANDBOX_MEMORY_LIMIT,
                "--cpus", settings.SANDBOX_CPU_LIMIT,
            ]
            
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
            
            level_dir = settings.MISSIONS_DIR / f"level_{self.level.lower()}"
            if level_dir.exists():
                cmd.extend([
                    "-v", f"{level_dir}:/mission:ro",
                ])
            
            cmd.append(self.image)
            logger.info(f"[CREATE] Запуск команды создания контейнера для миссии {self.mission_id}")
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                logger.error(f"Ошибка создания контейнера: {stderr.decode()}")
                return False
            
            self.container_id = stdout.decode().strip()
            self.status = "running"
            logger.info(f"[CREATE] Контейнер создан: {self.container_name} ({self.container_id})")
            
            if "astra-vnc" in self.image.lower():
                self.container_user = "root"
                logger.info(f"[CREATE] Используется пользователь root для образа astra-vnc")
            else:
                logger.info(f"[CREATE] Определение пользователя контейнера для миссии {self.mission_id}...")
                try:
                    await self._detect_container_user()
                    logger.info(f"[CREATE] Определён пользователь: {self.container_user}")
                except Exception as e:
                    logger.error(f"[CREATE] Ошибка определения пользователя: {e}", exc_info=True)
                    self.container_user = "root"
            
            logger.info(f"[SETUP] === НАЧАЛО ВЫПОЛНЕНИЯ SETUP ДЛЯ МИССИИ {self.mission_id} ===")
            try:
                await self._run_setup_after_create()
                logger.info(f"[SETUP] === SETUP ДЛЯ МИССИИ {self.mission_id} ВЫПОЛНЕН УСПЕШНО ===")
            except Exception as e:
                logger.error(f"[SETUP] === ОШИБКА ВЫПОЛНЕНИЯ SETUP ДЛЯ МИССИИ {self.mission_id}: {e} ===", exc_info=True)
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
        
        if user is None:
            user = self.container_user or "sandboxuser"
        
        try:
            cmd = self.container_cmd.split() + ["exec", "-u", user, self.container_name, "sh", "-c", command]
            logger.debug(f"Выполнение команды в контейнере {self.container_name} (user={user}): {command}")
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            output = stdout.decode() + stderr.decode()
            logger.debug(f"Команда выполнена, код возврата: {result.returncode}, вывод: {output[:200]}")
            return output, result.returncode
        except Exception as e:
            logger.error(f"Ошибка выполнения команды '{command}' в контейнере: {e}")
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
        try:
            output, code = await self.exec_command("ps aux | grep -E '(vnc|xfce|fly|websockify)' | grep -v grep | head -1 | awk '{print $1}'", user="root")
            if output.strip() and output.strip() != "root":
                self.container_user = output.strip()
                logger.info(f"Определён пользователь контейнера из процессов VNC/GUI: {self.container_user}")
                return
        except Exception:
            pass
        
        for username in ["sandboxuser", "user", "astrauser"]:
            try:
                output, code = await self.exec_command(f"test -d /home/{username} && echo 'exists' || echo 'not_found'", user="root")
                if "exists" in output:
                    self.container_user = username
                    logger.info(f"Определён пользователь контейнера по домашней директории: {username}")
                    return
            except Exception:
                continue
        
        try:
            output, code = await self.exec_command("ps aux | grep -E '(vnc|xfce|fly|websockify)' | grep -v grep | head -1", user="root")
            if "root" in output:
                self.container_user = "root"
                logger.info(f"Определён пользователь контейнера как root (VNC/GUI запущены от root)")
                return
        except Exception:
            pass
        
        try:
            output, code = await self.exec_command("test -d /root && echo 'exists' || echo 'not_found'", user="root")
            if "exists" in output:
                self.container_user = "root"
                logger.info(f"Используется root (найдена директория /root)")
                return
        except Exception:
            pass
        
        self.container_user = "sandboxuser"
        logger.warning(f"Не удалось определить пользователя контейнера, используется по умолчанию: {self.container_user}")
    
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

