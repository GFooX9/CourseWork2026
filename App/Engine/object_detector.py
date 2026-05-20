import cv2
from ultralytics import YOLO


class ObjectDetector:
    def __init__(self, model_name="yolo11n.pt"):
        self.model = YOLO(model_name)

    def set_model(self, model_name: str):
        """Динамически переключает веса модели YOLO."""
        if getattr(self.model, 'ckpt_path', None) != model_name:
            self.model = YOLO(model_name)

    def detect(self, image_path: str, conf_threshold: float) -> tuple:
        """
        Обнаруживает объекты на изображении с помощью YOLO.
        Возвращает кортеж: (список сырых данных объектов, массив разметки BGR, список названий классов)
        """
        objects_raw = []
        detected_labels = []

        original_img_bgr = cv2.imread(image_path)
        if original_img_bgr is None:
            return [], None, []

        try:
            results = self.model.predict(image_path, conf=conf_threshold)
            result = results[0]

            for box in result.boxes:
                label = result.names[int(box.cls[0])]
                conf = float(box.conf[0])
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
