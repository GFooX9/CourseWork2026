import os
import sys
import ctypes


def resource_path(relative_path):
    # Если приложение запущено из .exe, PyInstaller распаковывает ресурсы во временную папку _MEIPASS
    base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    return os.path.normpath(os.path.join(base_path, relative_path))


# --- ПУТИ К КОРНЕВЫМ ДИРЕКТОРИЯМ ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MODELS_DIR = resource_path("Source/Models")
DEFAULT_MODEL_PATH = os.path.join(MODELS_DIR, "yolo11n.pt")

# --- ПУТИ К РЕСУРСАМ (ИЗ ПАПКИ SOURCE) ---
FONT_PATH = resource_path("Source/Noto_Sans_Mono/static/NotoSansMono-Regular.ttf")

ICONS = {
    "push": resource_path("Source/Images/Push.png"),
    "vision": resource_path("Source/Images/Vision.png"),
    "main_icon": resource_path("Source/Images/Vision.ico")
}

# --- ФАЙЛЫ ДАННЫХ И РЕЗУЛЬТАТОВ ---
DB_DIR = os.path.join(BASE_DIR, "App/Data/Basedata")
DB_PATH = os.path.join(DB_DIR, "vision_pro.db")
HISTORY_FILE = os.path.join(BASE_DIR, "App/Data/history.json")  # Перенесли историю в предназначенную папку Data
RESULTS_DIR = os.path.join(BASE_DIR, "Results")  # Отчеты теперь летят строго в папку Results
RESULTS_IMAGES_DIR = os.path.join(RESULTS_DIR, "ResultsImages")

# --- СИСТЕМНЫЕ НАСТРОЙКИ (ДЛЯ WINDOWS) ---
try:
    # Явное указание ID приложения, чтобы Windows правильно группировала иконку в панели задач
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
