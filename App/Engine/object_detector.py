import os
import gc
import cv2
import torch
from ultralytics import YOLO


class ObjectDetector:
    def __init__(self, model_name="yolo11n.pt"):
        """
        Инициализирует выделенный подмодуль детекции объектов YOLO.
        Гарантирует запуск приложения при любых повреждениях файлов.
        """
        self.model_name = model_name
        self.model = None
        self._load_yolo_weights(model_name)

    def _load_yolo_weights(self, model_name: str):
        """Внутренний защищенный метод инициализации весов."""
        model_path = os.path.join("Source", "Models", model_name)

        try:
            # 1. Проверяем, существует ли файл локально
            if os.path.exists(model_path):
                # Пробуем загрузить локальный файл
                self.model = YOLO(model_path)
                print(f"[ObjectDetector] Успешно загружена локальная модель: {model_path}")
            else:
                # 2. Если файла нет, берем из официального встроенного кэша Ultralytics
                print(f"[ObjectDetector] Локальный файл {model_name} не найден. Загрузка из кэша...")
                self.model = YOLO(model_name)

            self.model_name = model_name

        except Exception as e:
            print(f"[ObjectDetector Error] Локальный файл {model_name} поврежден ({e}). Зачистка и откат...")
            # Если файл оказался битым (HTML-заглушкой), удаляем его, чтобы не ломал систему
            if os.path.exists(model_path):
                try:
                    os.remove(model_path)
                except:
                    pass

            # Принудительный откат на чистую скачанную модель из кэша системы
            self.model = YOLO("yolo11n.pt")
            self.model_name = "yolo11n.pt"

    def set_model(self, new_model_name: str):
        """Динамически переключает веса модели YOLO с очисткой RAM/VRAM."""
        if self.model_name == new_model_name and self.model is not None:
            return

        print(f"[ObjectDetector] Смена архитектуры YOLO: {self.model_name} -> {new_model_name}")

        try:
            if self.model is not None:
                del self.model
                self.model = None

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()

            self._load_yolo_weights(new_model_name)

        except Exception as e:
            print(f"[ObjectDetector Error] Сбой горячей смены, аварийный откат: {e}")
            self._load_yolo_weights("yolo11n.pt")

    def detect(self, image_path: str, conf_threshold: float) -> tuple:
        """Обнаруживает объекты на изображении с помощью YOLO."""
        objects_raw = []
        detected_labels = []

        original_img_bgr = cv2.imread(image_path)
        if original_img_bgr is None:
            return [], None, []

        if self.model is None:
            return [], original_img_bgr.copy(), []

        try:
            results = self.model.predict(image_path, conf=conf_threshold, verbose=False)
            result = results[0]

            for box in result.boxes:
                cls_idx = int(box.cls.item())
                label = result.names[cls_idx]
                conf = float(box.conf.item())
                coords = box.xyxy[0].tolist()

                objects_raw.append({
                    "label": label,
                    "conf": conf,
                    "box": coords,
                    "type": "yolo"
                })
                detected_labels.append(label)

            res_img_bgr = result.plot()
            return objects_raw, res_img_bgr, detected_labels

        except Exception as e:
            print(f"[ObjectDetector Error] Ошибка детекции YOLO: {e}")
            return [], original_img_bgr.copy(), []
