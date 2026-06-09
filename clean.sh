#!/bin/bash

echo "Очистка: удаление всех каталогов __pycache__ и venv в $(pds)..."

find . -type d -name "__pycache__" -exec rm -rf {} \;

find . -type d -name "venv" -exec rm -rf {} \;

echo "Готово."