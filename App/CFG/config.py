import os
import sys
import ctypes

def resource_path(relative_path):
    """
    Определяет абсолютный путь к ресурсам.
    Так как папка Source лежит внутри App, мы поднимаемся на один уровень вверх от App/CFG/
    """
    base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    return os.path.normpath(os.path.join(base_path, relative_path))

# --- ПУТИ К КОРНЕВЫМ ДИРЕКТОРИЯМ ---
# Базовая директория самого приложения App
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Корень всего репозитория (для папок Results, которые лежат в самом корне Coursework)
REPO_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))

# Централизованный путь к моделям внутри App/Source/Models
MODELS_DIR = resource_path("Source/Models")
DEFAULT_MODEL_PATH = os.path.join(MODELS_DIR, "yolo11n.pt")

# --- ПУТИ К РЕСУРСАМ (ИЗ ВНУТРЕННЕЙ ПАПКИ APP/SOURCE) ---
FONT_PATH = resource_path("Source/Noto_Sans_Mono/static/NotoSansMono-Regular.ttf")

ICONS = {
    "push": resource_path("Source/Images/push.png"),
    "vision": resource_path("Source/Images/vision.png"),
    "main_icon": resource_path("Source/Images/vision.ico")
}

# --- ФАЙЛЫ ДАННЫХ И РЕЗУЛЬТАТОВ ---
DB_DIR = os.path.join(BASE_DIR, "Data", "Basedata")
DB_PATH = os.path.join(DB_DIR, "vision_pro.db")
HISTORY_FILE = os.path.join(BASE_DIR, "Data", "history.json")

# Отчеты и результаты складываем в корень проекта Coursework
RESULTS_DIR = os.path.join(REPO_DIR, "Results")
RESULTS_IMAGES_DIR = os.path.join(RESULTS_DIR, "ResultsImages")

# --- СИСТЕМНЫЕ НАСТРОЙКИ (ДЛЯ WINDOWS) ---
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('vision.pro.final.master.v3')
except Exception:
    pass

# --- ИНИЦИАЛИЗАЦИЯ ПАПОК ---
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)
if not os.path.exists(RESULTS_IMAGES_DIR):
    os.makedirs(RESULTS_IMAGES_DIR)
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)
