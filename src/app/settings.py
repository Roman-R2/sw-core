import logging
from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')

# -------------- Настройки логирования
# Уровень логирования
APP_LOGGING_LEVEL = logging.DEBUG
# Папка логов
APP_LOG_FOLDER = BASE_DIR.parent / 'logs'
# Файл логов
APP_LOG_FILE = APP_LOG_FOLDER / 'sw_core.r2_log'
# Имя логера для создания бэкапов
APP_LOGGER_NAME = 'sw_core_logger'

# -------------- Настройки сканирования ресурсов на доступность
# Периодичность запуска сбора доступности (в секундах)
FREQUENCY_OF_LAUNCHING_AVAILABILITY_COLLECTION = 5
# Периодичность запуска обработки результатов сбора
FREQUENCY_OF_LAUNCHING_AVAILABILITY_COMPILE = 20
# Колличество проверок ресурса на доступность
COUNT_OF_AVAILABLE_ATTEMPT = 2
#
