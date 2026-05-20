import cv2
import os
from PIL import Image
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QScrollArea,
                             QWidget, QLabel, QCheckBox, QPushButton,
                             QInputDialog, QMessageBox)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from App.Engine.image_processor import ImageProcessor


class ObjectEditorDialog(QDialog):
    def __init__(self, current_path, last_results, user_notes, main_window, identifier_screen, parent=None):
        super().__init__(parent)
        self.current_path = current_path
        self.last_results = last_results
        self.user_notes = user_notes
        self.main_window = main_window
        self.id_screen = identifier_screen

        self.processor = ImageProcessor()
        self.checkboxes_vars = []  # Хранит кортежи (данные_объекта, экземпляр_QCheckBox)

        self.setup_ui()
        self.setup_styles()

    def setup_ui(self):
        self.setWindowTitle("Редактор объектов")
        self.setGeometry(200, 200, 700, 750)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(15)

        title_lbl = QLabel("Выберите элементы для отображения:")
        title_lbl.setFont(QFont("Noto Sans Mono", 14, QFont.Weight.Bold))
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_lbl)

        # 1. ПАНЕЛЬ ВЫДЕЛЕНИЯ (ВЫДЕЛИТЬ / СНЯТЬ ВСЁ)
        select_p = QWidget()
        select_layout = QHBoxLayout(select_p)
        select_layout.setContentsMargins(0, 0, 0, 0)
        select_layout.setSpacing(15)

        btn_select_all = QPushButton("ВЫДЕЛИТЬ ВСЁ")
        btn_select_all.setObjectName("SelectAllBtn")
        btn_select_all.clicked.connect(lambda: self.set_all_checkboxes(True))

        btn_deselect_all = QPushButton("СНЯТЬ ВСЁ")
        btn_deselect_all.setObjectName("DeselectAllBtn")
        btn_deselect_all.clicked.connect(lambda: self.set_all_checkboxes(False))

        select_layout.addWidget(btn_select_all)
        select_layout.addWidget(btn_deselect_all)
        main_layout.addWidget(select_p)

        # 2. СКРОЛЛ-ЗОНА СО СПИСКОМ ЧЕКБОКСОВ ОБЪЕКТОВ
        scroll_area = QScrollArea()
        scroll_area.setObjectName("EditorScroll")
        scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()
        scroll_content.setObjectName("ScrollContent")
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(15, 15, 15, 15)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Динамически наполняем список чекбоксами на основе сырых результатов ИИ
        for obj in self.last_results.get("objects_raw", []):
            is_yolo = obj.get('type') == 'yolo'
            prefix = "📦 Объект" if is_yolo else "📝 Текст"
            color_style = "color: #DFE1E5;" if is_yolo else "color: #BB9AF7;"

            cb = QCheckBox(f"{prefix}: {obj['label']} ({obj['conf']:.2f})")
            cb.setFont(QFont("Noto Sans Mono", 11))
            cb.setStyleSheet(color_style)
            cb.setChecked(True)  # По умолчанию всё выбрано

            self.scroll_layout.addWidget(cb)
            self.checkboxes_vars.append((obj, cb))

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)

        # 3. КНОПКА ПРИМЕНЕНИЯ ВНИЗУ
        self.btn_confirm = QPushButton("ПРИМЕНИТЬ И СОХРАНИТЬ")
        self.btn_confirm.setObjectName("ConfirmBtn")
        self.btn_confirm.setFont(QFont("Noto Sans Mono", 12, QFont.Weight.Bold))
        self.btn_confirm.clicked.connect(self.confirm_edit)
        main_layout.addWidget(self.btn_confirm)

    def setup_styles(self):
        style_qss = """
            QDialog { background-color: #1E1F22; }
            QLabel { color: #DFE1E5; }

            QScrollArea#EditorScroll {
                background-color: #2B2D31;
                border: 1px solid #3F424A;
                border-radius: 15px;
            }
            QWidget#ScrollContent { background-color: transparent; }

            QPushButton#SelectAllBtn { background-color: #2E6930; color: white; border-radius: 8px; min-height: 30px; border: none; }
            QPushButton#SelectAllBtn:hover { background-color: #388E3C; }

            QPushButton#DeselectAllBtn { background-color: #6E2E31; color: white; border-radius: 8px; min-height: 30px; border: none; }
            QPushButton#DeselectAllBtn:hover { background-color: #DA3637; }

            QPushButton#ConfirmBtn {
                background-color: #7C3AED;
                color: white;
                border-radius: 12px;
                min-height: 45px;
                border: none;
            }
            QPushButton#ConfirmBtn:hover { background-color: #BB9AF7; }
        """
        if not self.main_window.is_dark_theme:
            style_qss = style_qss.replace("#1E1F22", "#FFFFFF").replace("#DFE1E5", "#1F1F1F").replace("#2B2D31",
                                                                                                      "#F0F2F5").replace(
                "#3F424A", "#E4E6EB")
            style_qss = style_qss.replace("#BB9AF7", "#7C3AED")  # Подсветка текста OCR на светлой теме
            style_qss = style_qss.replace("color: #DFE1E5;", "color: #1F1F1F;")
        self.setStyleSheet(style_qss)

    def set_all_checkboxes(self, state: bool):
        for _, cb in self.checkboxes_vars:
            cb.setChecked(state)

    def confirm_edit(self):
        # Собираем данные только тех объектов, где стоит галочка
        selected_data = [obj for obj, cb in self.checkboxes_vars if cb.isChecked()]

        protocol_num, ok = QInputDialog.getText(self, "Сохранение", "Введите номер протокола:")
        if not ok or not protocol_num.strip():
            return

        protocol_num = protocol_num.strip()

        # 1. Запускаем нарезку кропов в новую папку ResultsImages через наш ImageProcessor
        # Метод возвращает нам путь к созданной папке протокола
        protocol_folder = self.processor.crop_and_save_objects(self.current_path, selected_data, protocol_num)

        # Кэшируем оригинальную картинку исследования в созданную папку
        cached_img_path = self.processor.cache_original_image(self.current_path, protocol_num)

        # 2. Рендерим bounding-boxes заново на чистом cv2-изображении на основе выбранных элементов
        clean_img = cv2.imread(self.current_path)
        if clean_img is None:
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить исходное изображение.")
            return

        final_labels = []
        final_text_parts = []

        for obj in selected_data:
            coords = obj['box']
            # Координаты могут приходить списком списков, берем первый элемент если нужно
            if isinstance(coords, list) and len(coords) > 0 and isinstance(coords[0], list):
                coords = coords[0]

            x1, y1, x2, y2 = map(int, coords)
            color = (0, 255, 0) if obj.get('type') == 'yolo' else (255, 0, 0)  # BGR
            cv2.rectangle(clean_img, (x1, y1), (x2, y2), color, 2)

            if obj.get('type') == 'yolo':
                final_labels.append(obj['label'])
            else:
                clean_text = obj['label'].replace("Текст: ", "").replace("...", "")
                final_text_parts.append(clean_text)
                if "Текст (OCR)" not in final_labels:
                    final_labels.append("Текст (OCR)")

        # 3. Переписываем временный словарь результатов, чтобы UI обновился
        new_img_rgb = cv2.cvtColor(clean_img, cv2.COLOR_BGR2RGB)
        pil_img_rects = Image.fromarray(new_img_rgb)

        # Пересохраняем изображение с боксами поверх закэшированного оригинала для красивого вывода в PDF
        pil_img_rects.save(cached_img_path, quality=95)

        self.last_results["result_img"] = pil_img_rects
        self.last_results["objects"] = ", ".join(final_labels) if final_labels else "Ничего не выбрано"
        self.last_results["text_data"] = " ".join(
            final_text_parts) if final_text_parts else "Текст не выбран или удален"

        # 4. Отправляем финальную запись в базу данных через DatabaseManager
        entry = self.main_window.db.save_to_history(
            protocol_num=protocol_num,
            original_path=self.current_path,
            cached_img_path=cached_img_path,  # Передаем стабильный локальный путь
            objects_info=self.last_results["objects"],
            text_info=self.last_results["text_data"],
            user_notes=self.user_notes
        )

        if entry:
            self.accept()  # Закрываем диалог с успешным статусом
            QMessageBox.information(self, "Успех",
                                    f"Протокол №{protocol_num} успешно сохранен, объекты нарезаны в датасет!")
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось зафиксировать запись в базе данных.")
