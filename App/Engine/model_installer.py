import os
import urllib.request
from PyQt6.QtCore import QThread, pyqtSignal
from huggingface_hub import hf_hub_download

# Импортируем централизованную директорию моделей прямо из вашего config.py
from App.CFG.config import MODELS_DIR


class ModelDownloadWorker(QThread):
    """
    Фоновый рабочий поток для скачивания оригинальных и кастомных моделей YOLO.
    Связана напрямую с константой MODELS_DIR из центрального конфигуратора путей.
    """
    progress_changed = pyqtSignal(int)  # Сигнал для ProgressBar (0-100)
    status_changed = pyqtSignal(str)  # Сигнал для текста статуса
    finished = pyqtSignal(bool, str)  # Сигнал завершения: (успех, сообщение)

    def __init__(self, url_or_name: str, filename: str = None):
        super().__init__()
        self.url_or_name = url_or_name.strip()
        # Извлекаем чистое имя файла из конца переданной строки (например, fire.pt)
        self.filename = filename if filename else self.url_or_name.split("/")[-1]

    def _download_report(self, block_num, block_size, total_size):
        """Внутренний колбэк для динамического расчета прогресс-бара при HTTP-закачке"""
        if total_size > 0:
            downloaded = block_num * block_size
            progress = int((downloaded / total_size) * 100)
            if progress > 100:
                progress = 100
            self.progress_changed.emit(progress)

    def run(self):
        # Наш 100% точный целевой путь берется напрямую из конфига
        target_dir = MODELS_DIR
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, self.filename)

        try:
            # ПРОВЕРКА: Это прямая веб-ссылка (например, с GitHub) или просто имя весов?
            if self.url_or_name.startswith(("http://", "https://")):
                self.status_changed.emit("Установка соединения с сервером источника...")

                # Маскируемся под браузер с помощью User-Agent, чтобы GitHub не сбрасывал соединение
                req = urllib.request.Request(
                    self.url_or_name,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )

                self.status_changed.emit(f"Потоковое скачивание файла: {self.filename}...")

                # Потоковая загрузка по ссылке пользователя
                urllib.request.urlretrieve(
                    self.url_or_name,
                    target_path,
                    reporthook=self._download_report
                )
            else:
                # Если введено просто имя весов, выполняем ваш проверенный откат на Hugging Face
                self.status_changed.emit("Подключение к репозиторию Ultralytics на Hugging Face...")
                self.status_changed.emit(f"Скачивание {self.filename}...")

                hf_hub_download(
                    repo_id="Ultralytics/YOLO11",
                    filename=self.filename,
                    local_dir=target_dir
                )

            # Защитная валидация физического размера файла на жестком диске
            real_size_mb = os.path.getsize(target_path) // (1024 * 1024)
            if real_size_mb < 2:
                if os.path.exists(target_path):
                    os.remove(target_path)
                self.finished.emit(False,
                                   "Внимание: Скачался поврежденный файл или пустая веб-страница. Проверьте адрес.")
                return

            self.progress_changed.emit(100)
            self.finished.emit(True, f"Модель успешно добавлена в каталог!\nРазмер: {real_size_mb} МБ.")

        except Exception as e:
            if os.path.exists(target_path):
                os.remove(target_path)
            print(f"[ModelDownloadWorker Error]: {e}")
            self.finished.emit(False, f"Ошибка при загрузке: {str(e)}")
