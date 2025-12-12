"""Модель пользователя"""
# Импортируем модель из user_db для работы с PostgreSQL
from backend.models.user_db import User

# Экспортируем для обратной совместимости
__all__ = ["User"]


class User:
    """Модель пользователя"""
    
    def __init__(self, username: str):
        self.username = username
        self.users_dir = settings.SANDBOX_DATA_DIR / "users"
        self.users_dir.mkdir(parents=True, exist_ok=True)
        self.user_file = self.users_dir / f"{username}.json"
        self.password_hash: Optional[str] = None
        self.secret_code_hash: Optional[str] = None
        self.created_at: Optional[datetime] = None
        self.last_login: Optional[datetime] = None
        
    def load(self) -> bool:
        """Загрузить данные пользователя из файла"""
        if not self.user_file.exists():
            return False
        
        try:
            with open(self.user_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.password_hash = data.get("password_hash")
                self.secret_code_hash = data.get("secret_code_hash")
                if data.get("created_at"):
                    self.created_at = datetime.fromisoformat(data["created_at"])
                if data.get("last_login"):
                    self.last_login = datetime.fromisoformat(data["last_login"])
                return True
        except Exception as e:
            print(f"Ошибка загрузки пользователя {self.username}: {e}")
            return False
    
    def save(self):
        """Сохранить данные пользователя в файл"""
        data = {
            "username": self.username,
            "password_hash": self.password_hash,
            "secret_code_hash": self.secret_code_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        
        try:
            with open(self.user_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения пользователя {self.username}: {e}")
            raise
    
    def set_password(self, password: str):
        """Установить хеш пароля"""
        self.password_hash = pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Проверить пароль"""
        if not self.password_hash:
            return False
        return pwd_context.verify(password, self.password_hash)
    
    def set_secret_code(self, secret_code: str):
        """Установить хеш секретного кода"""
        self.secret_code_hash = pwd_context.hash(secret_code)
    
    def verify_secret_code(self, secret_code: str) -> bool:
        """Проверить секретный код"""
        if not self.secret_code_hash:
            return False
        return pwd_context.verify(secret_code, self.secret_code_hash)
    
    def update_last_login(self):
        """Обновить время последнего входа"""
        self.last_login = datetime.now()
        self.save()
    
    def to_dict(self) -> Dict:
        """Преобразовать в словарь (без паролей)"""
        return {
            "username": self.username,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
    
    @staticmethod
    def exists(username: str) -> bool:
        """Проверить, существует ли пользователь"""
        users_dir = settings.SANDBOX_DATA_DIR / "users"
        user_file = users_dir / f"{username}.json"
        return user_file.exists()
    
    @staticmethod
    def create(username: str, password: str, secret_code: str) -> 'User':
        """Создать нового пользователя"""
        if User.exists(username):
            raise ValueError(f"Пользователь {username} уже существует")
        
        user = User(username)
        user.set_password(password)
        user.set_secret_code(secret_code)
        user.created_at = datetime.now()
        user.save()
        return user

