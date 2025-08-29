#!/bin/bash

echo "🚀 Установка инструментов разработки..."

# Устанавливаем зависимости для разработки
uv sync --group dev

echo "✅ Готово!"
echo ""
echo "Команды:"
echo "  make format  - форматировать код"
echo "  make lint    - проверить код"
echo "  make check   - форматировать и проверить"
echo "  make clean   - очистить кэш"
