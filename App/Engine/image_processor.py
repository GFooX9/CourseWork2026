import os
import time
from PIL import Image
from App.CFG.config import RESULTS_IMAGES_DIR


class ImageProcessor:
    def __init__(self):
        # Базовая директория для кэша картинок теперь берется централизованно из конфига
        self.results_base_dir = RESULTS_IMAGES_DIR

    def _get_clean_protocol_dir(self, protocol_num: str) -> str:
        """Вспомогательный метод для создания безопасного пути папки протокола."""
        clean_protocol_name = "".join(x for x in str(protocol_num) if x.isalnum() or x in "._-")
        session_folder = os.path.join(self.results_base_dir, clean_protocol_name)
        os.makedirs(session_folder, exist_ok=True)
        return session_folder

    def cache_original_image(self, original_image_path: str, protocol_num: str) -> str:
        """
        Копирует исходное изображение исследования в локальный кэш ResultsImages.
        Возвращает новый надежный путь к файлу для сохранения в БД.
        """
        try:
            session_folder = self._get_clean_protocol_dir(protocol_num)
            ext = os.path.splitext(original_image_path)[1] or ".jpg"

            # Формируем имя файла: оригинальное имя + таймстамп для уникальности
            base_name = os.path.splitext(os.path.basename(original_image_path))[0]
            cached_filename = f"source_{base_name}_{int(time.time())}{ext}"
            cached_path = os.path.join(session_folder, cached_filename)

            with Image.open(original_image_path) as img:
                img.save(cached_path, quality=95)

            return os.path.normpath(cached_path)
        except Exception as e:
            print(f"[ImageProcessor Error] Не удалось закэшировать оригинал: {e}")
            return original_image_path  # В случае сбоя возвращаем старый путь, чтобы не ломать поток

    def crop_and_save_objects(self, original_image_path: str, selected_objects: list, protocol_num: str) -> str:
        """
        Нарезает обнаруженные объекты по координатам боксов и раскладывает
        их в подпапки классов внутри папки протокола.
        """
        try:
            session_folder = self._get_clean_protocol_dir(protocol_num)

            with Image.open(original_image_path) as img:
                for i, obj in enumerate(selected_objects):
                    # ЧИСТКА ИМЕНИ КЛАССА
                    label = obj.get('label', 'unknown').replace("Текст: ", "text_")
                    label = "".join(x for x in label if x.isalnum() or x == "_").strip()
                    if len(label) > 30:
                        label = label[:30]

                    # СОЗДАНИЕ ПОДПАПКИ КЛАССА
                    class_dir = os.path.join(session_folder, label)
                    os.makedirs(class_dir, exist_ok=True)

                    # ОБРАБОТКА КООРДИНАТ БОКСА
                    coords = obj['box']
                    if isinstance(coords, list) and len(coords) > 0 and isinstance(coords[0], list):
                        coords = coords[0]

                    x1, y1, x2, y2 = map(int, coords)

                    # ПРОВЕРКА И КОРРЕКЦИЯ ГРАНИЦ ДЛЯ CROP
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(img.width, x2), min(img.height, y2)

                    # Защита от некорректных или перевернутых координат
                    if x2 <= x1 or y2 <= y1:
                        continue

                    crop = img.crop((x1, y1, x2, y2))
                    file_name = f"{label}_{i + 1}_{int(time.time())}.jpg"
                    save_path = os.path.join(class_dir, file_name)

                    crop.save(save_path, quality=95)

            return os.path.normpath(session_folder)
        except Exception as e:
            print(f"[ImageProcessor Error] Ошибка при нарезке объектов: {e}")
            return None
