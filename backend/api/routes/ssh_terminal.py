"""Роуты для SSH терминала через WebSocket"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import logging
import threading
import select
import socket

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False

from backend.sandbox.manager import sandbox_manager
from backend.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class SSHConnection:
    """Управление SSH подключением через paramiko"""
    
    def __init__(self, host: str, port: int, user: str, password: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.client = None
        self.channel = None
        self._closed = False
        
    async def connect(self):
        """Подключиться к SSH через paramiko"""
        if not PARAMIKO_AVAILABLE:
            logger.error("paramiko не установлен. Установите: pip install paramiko")
            return False
        
        try:
            # Создаем SSH клиент
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Подключаемся в отдельном потоке (paramiko не async)
            def _connect():
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.user,
                    password=self.password,
                    timeout=10,
                    allow_agent=False,
                    look_for_keys=False
                )
            
            # Запускаем в thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _connect)
            
            # Создаем интерактивный канал
            def _get_channel():
                self.channel = self.client.invoke_shell(term='xterm-256color')
                self.channel.settimeout(0.1)
            
            await loop.run_in_executor(None, _get_channel)
            
            logger.info(f"SSH подключение установлено: {self.user}@{self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка подключения SSH: {e}", exc_info=True)
            return False
    
    async def read(self, size: int = 4096) -> bytes:
        """Читать данные из SSH"""
        if not self.channel or self._closed:
            return b""
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, self.channel.recv, size)
            return data if data else b""
        except socket.timeout:
            return b""
        except Exception as e:
            if not self._closed:
                logger.error(f"Ошибка чтения из SSH: {e}")
            return b""
    
    async def write(self, data: bytes):
        """Записать данные в SSH"""
        if not self.channel or self._closed:
            return
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.channel.send, data)
        except Exception as e:
            if not self._closed:
                logger.error(f"Ошибка записи в SSH: {e}")
    
    async def close(self):
        """Закрыть SSH подключение"""
        self._closed = True
        if self.channel:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.channel.close)
            except Exception:
                pass
            self.channel = None
        if self.client:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.client.close)
            except Exception:
                pass
            self.client = None


@router.websocket("/sandbox/{mission_id}/ssh")
async def ssh_terminal(websocket: WebSocket, mission_id: str):
    """WebSocket endpoint для SSH терминала"""
    logger.info(f"Попытка WebSocket подключения для SSH терминала миссии {mission_id}")
    
    try:
        await websocket.accept()
        logger.info(f"WebSocket подключение принято для миссии {mission_id}")
    except Exception as e:
        logger.error(f"Ошибка принятия WebSocket подключения: {e}", exc_info=True)
        return
    
    ssh_conn = None
    read_task = None
    
    try:
        # Получаем информацию о песочнице
        sandbox = await sandbox_manager.get_sandbox(mission_id)
        if not sandbox:
            error_msg = "ERROR: Песочница не найдена\n"
            logger.error(f"Песочница {mission_id} не найдена")
            await websocket.send_text(error_msg)
            await websocket.close()
            return
        
        if not hasattr(sandbox, 'ssh_port') or not sandbox.ssh_port:
            error_msg = "ERROR: SSH порт не настроен\n"
            logger.error(f"SSH порт не настроен для песочницы {mission_id}")
            await websocket.send_text(error_msg)
            await websocket.close()
            return
        
        # Получаем информацию о подключении
        host = "localhost"
        port = sandbox.ssh_port
        user = sandbox.container_user or "root"
        password = settings.SSH_PASSWORD
        
        # Создаем SSH подключение
        ssh_conn = SSHConnection(host, port, user, password)
        if not await ssh_conn.connect():
            await websocket.send_text("ERROR: Не удалось подключиться к SSH серверу\n")
            await websocket.close()
            return
        
        # Отправляем приветственное сообщение
        await websocket.send_text("\r\n*** Подключено к SSH терминалу ***\r\n")
        
        # Задача для чтения из SSH и отправки в WebSocket
        async def read_from_ssh():
            while True:
                try:
                    data = await ssh_conn.read(4096)
                    if not data:
                        await asyncio.sleep(0.1)
                        continue
                    await websocket.send_bytes(data)
                except Exception as e:
                    logger.error(f"Ошибка чтения из SSH: {e}")
                    break
        
        read_task = asyncio.create_task(read_from_ssh())
        
        # Основной цикл: читаем из WebSocket и отправляем в SSH
        while True:
            try:
                message = await websocket.receive()
                
                if message["type"] == "websocket.receive":
                    if "text" in message:
                        # Текстовые данные (команды)
                        text = message["text"]
                        await ssh_conn.write(text.encode('utf-8'))
                    elif "bytes" in message:
                        # Бинарные данные
                        await ssh_conn.write(message["bytes"])
                
            except WebSocketDisconnect:
                logger.info("WebSocket отключен")
                break
            except Exception as e:
                logger.error(f"Ошибка обработки WebSocket сообщения: {e}")
                break
        
    except Exception as e:
        logger.error(f"Ошибка в SSH терминале: {e}", exc_info=True)
        try:
            await websocket.send_text(f"ERROR: {str(e)}\n")
        except:
            pass
    finally:
        if read_task:
            read_task.cancel()
        if ssh_conn:
            await ssh_conn.close()
        try:
            await websocket.close()
        except:
            pass

