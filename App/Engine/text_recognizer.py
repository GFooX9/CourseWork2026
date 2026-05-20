import easyocr


class TextRecognizer:
    def __init__(self):
        try:
            self.reader = easyocr.Reader(['ru', 'en'], gpu=True)
        except Exception as e:
            print(f"[TextRecognizer Warning] Ошибка инициализации GPU, откат на CPU: {e}")
            self.reader = easyocr.Reader(['ru', 'en'], gpu=False)

    def recognize(self, img_bgr) -> tuple:
        """
        Распознает печатный текст на BGR-изображении OpenCV.
        Возвращает кортеж: (список сырых текстовых объектов для кропа, итоговая строка текста, флаг успешности)
        """
        objects_raw = []
        full_text_list = []
        has_text = False

        if img_bgr is None:
            return [], "Ошибка: Изображение отсутствует", False

        try:
            ocr_results = self.reader.readtext(img_bgr)
            for (bbox, text, prob) in ocr_results:
                full_text_list.append(text)
                has_text = True

                # Конвертируем 4 точки EasyOCR в плоский формат [x1, y1, x2, y2]
                x_coords = [p[0] for p in bbox]
                y_coords = [p[1] for p in bbox]
                text_box = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]

                objects_raw.append({
                    "label": f"Текст: {text[:20]}...",
                    "conf": prob,
                    "box": text_box,
                    "type": "ocr"
                })

            detected_text = " ".join(full_text_list) if full_text_list else "Текст не обнаружен"
            return objects_raw, detected_text, has_text

        except Exception as e:
            print(f"[TextRecognizer Error] Ошибка OCR модуля: {e}")
            return [], f"Ошибка распознавания: {str(e)}", False
