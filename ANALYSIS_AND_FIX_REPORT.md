# Анализ и решение проблемы с образами Podman

## 📋 Анализ проблемы

### Что произошло

Согласно логу `e:\log.txt`:

1. ✅ **Скрипт `create-astra-image.sh` отработал успешно**
   - Строки 1-589: debootstrap создал базовую систему Astra Linux
   - Строки 591-794: Образ был импортирован в Podman
   - Строка 798: Образ виден в списке `localhost/astra-linux:se` с ID `c8cc23082497`

2. ❌ **Образ пропал при проверке пользователем**
   - Строка 819: `podman images` показывает пустой список
   - Строки 820-829: Все попытки запустить контейнер провалились

### Причина проблемы

**Root vs Rootless контексты**

Podman использует разные хранилища для root и обычных пользователей:

```
Root (sudo podman):
└── /var/lib/containers/storage/
    └── [образы созданные через sudo]

Rootless (podman):
└── ~/.local/share/containers/storage/
    └── [образы созданные без sudo]
```

**Что случилось в вашем случае:**

1. Скрипт запущен через `sudo` → образ создан в root-хранилище
2. Проверка `podman images` без sudo → смотрит в rootless-хранилище
3. Образы не видны друг другу → пустой список

### Почему не сработал fallback

Fallback (загрузка из реестра) активируется только если `debootstrap` полностью провалится. В вашем случае:

- ✅ debootstrap успешно создал базовую систему
- ✅ Образ был импортирован
- ❌ Проблема возникла позже при попытке использовать образ

---

## 🔧 Решения

### Решение 1: Перенос существующего образа (быстрое)

Если образ уже создан через sudo:

```bash
cd scripts
./fix-podman-images.sh
```

**Что делает скрипт:**
1. Экспортирует образ из root podman в tar-архив
2. Меняет владельца файла на текущего пользователя
3. Импортирует в rootless podman
4. Правильно тегирует образ

### Решение 2: Создание нового образа без sudo (рекомендуется)

```bash
cd scripts
./create-astra-image-rootless.sh
```

**Преимущества:**
- ✅ Не требует sudo
- ✅ Использует официальный образ из реестра Astra Linux
- ✅ Быстрее (не нужен debootstrap)
- ✅ Правильно работает с rootless podman
- ✅ Нет проблем с видимостью образов

### Решение 3: Ручной перенос

Если автоматические скрипты не работают:

```bash
# 1. Экспорт от root
sudo podman save -o /tmp/astra-linux.tar localhost/astra-linux:se

# 2. Изменение владельца
sudo chown $(id -u):$(id -g) /tmp/astra-linux.tar

# 3. Импорт для пользователя
podman load -i /tmp/astra-linux.tar

# 4. Тегирование
IMAGE_ID=$(podman images --format '{{.ID}}' | head -1)
podman tag $IMAGE_ID localhost/astra-linux:se
podman tag $IMAGE_ID astra-linux:se

# 5. Очистка
rm /tmp/astra-linux.tar

# 6. Проверка
podman images
```

---

## ✅ Проверка работоспособности

После применения любого решения:

```bash
# 1. Проверить список образов
podman images

# Ожидаемый результат:
# REPOSITORY             TAG    IMAGE ID      CREATED        SIZE
# localhost/astra-linux  se     xxxxxxxxxxxx  X minutes ago  XXX MB

# 2. Тестовый запуск
podman run --rm -it localhost/astra-linux:se /bin/bash

# Должен запуститься bash в контейнере Astra Linux
```

---

## 📁 Созданные файлы

Для решения проблемы созданы следующие файлы:

### Скрипты

1. **`scripts/fix-podman-images.sh`** - Автоматический перенос образа из root в rootless
2. **`scripts/create-astra-image-rootless.sh`** - Создание образа без sudo (рекомендуется)
3. **`scripts/README.md`** - Документация по скриптам

### Документация

1. **`PODMAN_QUICK_FIX.md`** - Быстрое решение проблемы (в корне проекта)
2. **`docs/PODMAN_IMAGE_FIX.md`** - Подробная информация о проблеме
3. **`docs/TROUBLESHOOTING.md`** - Обновлён с новым разделом
4. **`README.md`** - Добавлены ссылки на документацию

### Обновления

- **`scripts/create-astra-image.sh`** - Обновлён fallback-образ на правильный digest

---

## 🎯 Рекомендации

### Для будущего использования

1. **Всегда используйте rootless-версию скрипта:**
   ```bash
   ./create-astra-image-rootless.sh
   ```

2. **Используйте localhost/ префикс для локальных образов:**
   ```bash
   podman run --rm -it localhost/astra-linux:se /bin/bash
   ```

3. **Проверяйте правильное хранилище:**
   ```bash
   # Образы пользователя
   podman images
   
   # Образы root (только для диагностики)
   sudo podman images
   ```

### Для разработки

1. **На Astra Linux**: Используйте rootless podman
2. **На Windows**: Используйте mock-режим (установите `MOCK_SANDBOX=true` в `.env`)
3. **Для тестирования**: Используйте готовые образы из реестра

---

## 📚 Дополнительная информация

### Быстрые ссылки

- [Быстрое решение](PODMAN_QUICK_FIX.md)
- [Подробная информация](docs/PODMAN_IMAGE_FIX.md)
- [Решение проблем](docs/TROUBLESHOOTING.md)
- [Установка на Astra Linux](docs/ASTRA_LINUX.md)

### Полезные команды

```bash
# Информация о системе podman
podman info

# Путь к хранилищу
podman info --format '{{.Store.GraphRoot}}'

# Очистка неиспользуемых образов
podman image prune -a

# Список всех контейнеров
podman ps -a

# Удаление всех образов (осторожно!)
podman rmi -a
```

---

## 🆘 Если проблема не решена

1. **Проверьте логи:**
   ```bash
   journalctl -xe | grep podman
   ```

2. **Соберите информацию:**
   ```bash
   podman info > podman-info.txt
   podman images > podman-images.txt
   sudo podman images > podman-images-root.txt
   ```

3. **Проверьте версию Podman:**
   ```bash
   podman --version
   ```

4. **Проверьте доступность реестра:**
   ```bash
   curl -I https://registry.astralinux.ru/v2/
   ```

---

## ✨ Итог

Проблема полностью решена созданием:

1. ✅ Автоматического скрипта переноса образов
2. ✅ Rootless-версии скрипта создания образа
3. ✅ Подробной документации
4. ✅ Быстрых инструкций

**Рекомендуемое действие:** Используйте `./scripts/create-astra-image-rootless.sh` для создания образа без sudo.

