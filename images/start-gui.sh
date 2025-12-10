#!/bin/bash
# Скрипт запуска GUI в контейнере

# Запуск Xvfb (виртуальный дисплей)
Xvfb :0 -screen 0 1024x768x24 &
export DISPLAY=:0

# Запуск XFCE
startxfce4 &

# Запуск VNC сервера
x11vnc -forever -usepw -display :0 -rfbport 5900 -shared &

# Ожидание
wait

