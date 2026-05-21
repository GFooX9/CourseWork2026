import os
from PyQt6.QtCore import QThread, pyqtSignal
from huggingface_hub import hf_hub_download


class ModelDownloadWorker(QThread):
    """
    Фоновый рабочий поток для скачивания оригинальных моделей YOLO
    напрямую из официального ОТКРЫТОГО репозитория Ultralytics без токенов.
    """
    progress_changed = pyqtSignal(int)  # Сигнал для ProgressBar (0-100)
    status_changed = pyqtSignal(str)  # Сигнал для текста статуса
    finished = pyqtSignal(bool, str)  # Сигнал завершения: (успех, сообщение)

    def __init__(self, url_or_name: str, filename: str = None):
        super().__init__()
        self.filename = filename if filename else url_or_name.split("/")[-1]

    def run(self):
        target_dir = os.path.join("Source", "Models")
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, self.filename)

        self.status_changed.emit("Подключение к официальному репозиторию Ultralytics...")

        try:
            self.status_changed.emit(f"Скачивание {self.filename}...")

            # ИСПРАВЛЕНО: Меняем repo_id на официальный 'Ultralytics/YOLO11'
            # Он полностью публичный, ошибки 401/Unauthorized больше не будет!
            downloaded_path = hf_hub_download(
                repo_id="Ultralytics/YOLO11",
                filename=self.filename,
                local_dir=target_dir
            )

            # Проверяем физический размер файла на диске
            real_size_mb = os.path.getsize(target_path) // (1024 * 1024)

            if real_size_mb < 2:
                if os.path.exists(target_path):
                    os.remove(target_path)
                self.finished.emit(False, "Внимание: Скачался поврежденный файл. Попробуйте снова.")
                return

            self.progress_changed.emit(100)
            self.finished.emit(True, f"Модель успешно сохранена!\nРазмер: {real_size_mb} МБ.")

        except Exception as e:
            if os.path.exists(target_path):
                os.remove(target_path)
            print(f"[ModelDownloadWorker Error]: {e}")
            self.finished.emit(False, f"Ошибка при загрузке: {str(e)}")
