import easyocr
import cv2
import numpy as np


class TextRecognizer:
    def __init__(self):
        """
        Инициализирует модуль распознавания текста.
        Безопасно переключается на CPU, если нет поддержки CUDA.
        """
        try:
            self.reader = easyocr.Reader(['ru', 'en'], gpu=True)
        except Exception as e:
            print(f"[TextRecognizer Warning] Ошибка инициализации GPU, откат на CPU: {e}")
            self.reader = easyocr.Reader(['ru', 'en'], gpu=False)

    def recognize(self, img_bgr) -> tuple:
        """
        Распознает печатный текст на BGR-изображении OpenCV.
        Возвращает максимум найденных элементов без жесткой фильтрации.
        """
        objects_raw = []
        full_text_list = []
        has_text = False

        # Защита от пустого кадра
        if img_bgr is None:
            return [], "Ошибка: Изображение отсутствует", False

        try:
            # Запускаем EasyOCR в стандартном режиме без объединения строк,
            # чтобы он находил отдельные слова и надписи на мемах / обложках
            ocr_results = self.reader.readtext(img_bgr)

            for (bbox, text, prob) in ocr_results:
                cleaned_text = text.strip()
                if not cleaned_text:
                    continue

                full_text_list.append(cleaned_text)
                has_text = True

                # Оригинальный рабочий конвертер координат из прошлых наработок
                x_coords = [int(p[0]) for p in bbox]
                y_coords = [int(p[1]) for p in bbox]
                text_box = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]

                # Передаем чистый текст, чтобы в UI не было дублирования "Текст: Текст: "
                preview_text = cleaned_text[:20] + "..." if len(cleaned_text) > 20 else cleaned_text

                objects_raw.append({
                    "label": preview_text,
                    "conf": float(prob),
                    "box": text_box,
                    "type": "ocr"
                })

            # Собираем итоговую строку для вывода в интерфейс
            detected_text = " ".join(full_text_list) if full_text_list else "Текст не обнаружен"
            return objects_raw, detected_text, has_text

        except Exception as e:
            print(f"[TextRecognizer Error] Ошибка OCR модуля: {e}")
            import traceback
            traceback.print_exc()
            return [], f"Ошибка распознавания: {str(e)}", False
