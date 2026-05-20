import cv2
from PIL import Image
from App.Engine.object_detector import ObjectDetector
from App.Engine.text_recognizer import TextRecognizer
from App.CFG.config import DEFAULT_MODEL_PAT


class VisionEngine:
    def __init__(self, model_name=DEFAULT_MODEL_PATH):
        # Подключаем наши новые специализированные модули
        self.detector = ObjectDetector(model_name)
        self.recognizer = TextRecognizer()

    def set_model(self, model_name: str):
        self.detector.set_model(model_name)

    def analyze(self, image_path: str, conf_threshold: float, only_text: bool = False) -> dict:
        """Оркестрирует процесс комплексного анализа изображений."""
        objects_raw = []
        detected_labels = []

        # Читаем картинку для первичной проверки
        original_img_bgr = cv2.imread(image_path)
        if original_img_bgr is None:
            print(f"[VisionEngine Error] Файл не найден: {image_path}")
            return None

        # 1. Запускаем детекцию объектов
        if not only_text:
            yolo_objs, res_img_bgr, yolo_labels = self.detector.detect(image_path, conf_threshold)
            objects_raw.extend(yolo_objs)
            detected_labels.extend(yolo_labels)
        else:
            res_img_bgr = original_img_bgr.copy()

        # 2. Запускаем распознавание текста
        ocr_objs, detected_text, has_text = self.recognizer.recognize(original_img_bgr)
        objects_raw.extend(ocr_objs)
        if has_text:
            detected_labels.append("Текст (OCR)")

        # 3. Подготавливаем финальное изображение PIL для PyQt6
        res_img_rgb = cv2.cvtColor(res_img_bgr, cv2.COLOR_BGR2RGB)
        result_pil = Image.fromarray(res_img_rgb)

        return {
            "result_img": result_pil,
            "objects": ", ".join(list(set(detected_labels))) if detected_labels else "Не определены",
            "objects_raw": objects_raw,
            "text_data": detected_text
        }
