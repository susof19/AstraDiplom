#!/bin/bash
# Скрипт для отключения CD-репозитория в Astra Linux
# Используйте если основной скрипт просит вставить диск

echo "🔧 Отключение CD-репозитория в apt..."

# Создаём конфигурацию для игнорирования CD
sudo mkdir -p /etc/apt/apt.conf.d/
echo 'Acquire::cdrom::AutoDetect "false";' | sudo tee /etc/apt/apt.conf.d/99no-cdrom
echo 'Acquire::cdrom::mount "/dev/null";' | sudo tee -a /etc/apt/apt.conf.d/99no-cdrom

# Комментируем CD-репозиторий в sources.list
if [ -f /etc/apt/sources.list ]; then
    sudo sed -i 's/^deb cdrom:/#deb cdrom:/' /etc/apt/sources.list
fi

# Комментируем CD-репозитории в sources.list.d
if [ -d /etc/apt/sources.list.d ]; then
    sudo find /etc/apt/sources.list.d -name "*.list" -exec sed -i 's/^deb cdrom:/#deb cdrom:/' {} \;
fi

echo "✅ CD-репозиторий отключен"
echo "Теперь можно запустить: ./quickstart-astra.sh"

