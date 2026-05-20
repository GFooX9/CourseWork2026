import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
                             QSlider, QComboBox, QCheckBox, QPushButton,
                             QTextEdit, QProgressBar, QFileDialog, QMessageBox)
from PyQt6.QtGui import QFont, QPixmap, QImage
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot

from App.CFG.config import ICONS, MODELS_DIR
from App.Engine.vision_engine import VisionEngine
from App.UI.components.object_editor import ObjectEditorDialog


# === РАБОЧИЙ ПОТОК ДЛЯ ИИ-АНАЛИЗА ===
class AnalysisWorker(QThread):
    # Сигналы для передачи результатов обратно в главный поток UI
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, engine, image_path, conf, only_text):
        super().__init__()
        self.engine = engine
        self.image_path = image_path
        self.conf = conf
        self.only_text = only_text

    def run(self):
        try:
            results = self.engine.analyze(self.image_path, self.conf, self.only_text)
            if results:
                self.finished.emit(results)
            else:
                self.error.emit("Движок вернул пустой результат.")
        except Exception as e:
            self.error.emit(str(e))


# === ГЛАВНЫЙ КЛАСС ЭКРАНА ИДЕНТИФИКАЦИИ ===
class IdentifierScreen(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window  # Ссылка на главное окно для доступа к БД
        self.engine = VisionEngine()

        self.current_path = None
        self.last_results = None
        self.is_processing = False

        self.setup_ui()
        self.setup_styles()
        self.load_models_to_selector()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # 1. ВЕРХНЯЯ ПАНЕЛЬ НАСТРОЕК
        settings_panel = QFrame()
        settings_panel.setObjectName("SettingsPanel")
        settings_layout = QHBoxLayout(settings_panel)
        settings_layout.setContentsMargins(15, 10, 15, 10)
        settings_layout.setSpacing(15)

        # Селектор моделей
        lbl_model = QLabel("Модель:")
        lbl_model.setFont(QFont("Noto Sans Mono", 11, QFont.Weight.Bold))
        self.model_selector = QComboBox()
        self.model_selector.currentIndexChanged.connect(self.change_model)

        settings_layout.addWidget(lbl_model)
        settings_layout.addWidget(self.model_selector)

        # Чекбокс режима OCR (Заменили старый свитч на чекбокс PyQt)
        self.mode_checkbox = QCheckBox("Только Текст")
        self.mode_checkbox.setFont(QFont("Noto Sans Mono", 11, QFont.Weight.Bold))
        settings_layout.addWidget(self.mode_checkbox)

        # Ползунок Confidence (Точность)
        lbl_conf = QLabel("Точность (Conf):")
        lbl_conf.setFont(QFont("Noto Sans Mono", 11, QFont.Weight.Bold))

        self.conf_slider = QSlider(Qt.Orientation.Horizontal)
        self.conf_slider.setMinimum(10)
        self.conf_slider.setMaximum(100)
        self.conf_slider.setValue(25)
        self.conf_slider.setTickInterval(10)
        self.conf_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.conf_slider.valueChanged.connect(self.update_conf_label)

        self.conf_val_label = QLabel("0.25")
        self.conf_val_label.setFont(QFont("Noto Sans Mono", 11))

        settings_layout.addWidget(lbl_conf)
        settings_layout.addWidget(self.conf_slider)
        settings_layout.addWidget(self.conf_val_label)

        main_layout.addWidget(settings_panel)

        # 2. ЦЕНТРАЛЬНЫЙ БЛОК (ЛЕВАЯ И ПРАВАЯ ЗОНЫ)
        content_box = QWidget()
        content_layout = QHBoxLayout(content_box)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

        # Левая интерактивная кнопка-окно для выбора изображения
        self.btn_left_image = QPushButton()
        self.btn_left_image.setObjectName("ImageZoneLeft")
        self.btn_left_image.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_left_image.clicked.connect(self.process_image)
        self.set_placeholder_icon(self.btn_left_image, "push")
        content_layout.addWidget(self.btn_left_image, 1)

        # Правая зона для вывода результатов обработки ИИ
        self.panel_right_res = QFrame()
        self.panel_right_res.setObjectName("ImageZoneRight")
        right_layout = QVBoxLayout(self.panel_right_res)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_right_image = QLabel()
        self.lbl_right_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_placeholder_icon(self.lbl_right_image, "vision")
        right_layout.addWidget(self.lbl_right_image)

        content_layout.addWidget(self.panel_right_res, 1)
        main_layout.addWidget(content_box, 1)

        # 3. ПРОГРЕСС-БАР
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Бегущий индикатор (Indeterminate)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # 4. ПОЛЕ ДЛЯ ЗАМЕТОК ЭКСПЕРТА
        lbl_notes = QLabel("Заметки эксперта (по желанию):")
        lbl_notes.setFont(QFont("Noto Sans Mono", 11, QFont.Weight.Bold))
        main_layout.addWidget(lbl_notes)

        self.notes_box = QTextEdit()
        self.notes_box.setMaximumHeight(80)
        self.notes_box.setFont(QFont("Noto Sans Mono", 11))
        main_layout.addWidget(self.notes_box)

        # 5. НИЖНЯЯ ПАНЕЛЬ КНОПОК УПРАВЛЕНИЯ
        bottom_panel = QWidget()
        bottom_layout = QHBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(0, 10, 0, 10)

        self.btn_clear = QPushButton("ОЧИСТИТЬ")
        self.btn_clear.setObjectName("ClearBtn")
        self.btn_clear.clicked.connect(self.clear_all)

        self.btn_save = QPushButton("РЕДАКТИРОВАТЬ И СОХРАНИТЬ")
        self.btn_save.setObjectName("SaveBtn")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.open_object_editor)

        bottom_layout.addWidget(self.btn_clear)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_save)
        main_layout.addWidget(bottom_panel)

    def setup_styles(self):
        """Интегрирует сиреневые (лавандовые) стили под текущие темы нашего чата."""
        style_qss = """
            QFrame#SettingsPanel {
                background-color: #2B2D31;
                border: 1px solid #3F424A;
                border-radius: 12px;
            }
            QLabel { color: #DFE1E5; }
            QCheckBox { color: #DFE1E5; }

            /* Стили окон-контейнеров для фото */
            QPushButton#ImageZoneLeft, QFrame#ImageZoneRight {
                background-color: #2B2D31;
                border: 2px dashed #3F424A;
                border-radius: 20px;
            }
            QPushButton#ImageZoneLeft:hover { border-color: #BB9AF7; }

            /* Поле ввода заметок */
            QTextEdit {
                background-color: #2B2D31;
                color: white;
                border: 1px solid #3F424A;
                border-radius: 10px;
                padding: 5px;
            }

            /* Кнопка Очистить */
            QPushButton#ClearBtn {
                background-color: #3F424A;
                color: #DFE1E5;
                border-radius: 12px;
                font-family: 'Noto Sans Mono';
                font-weight: bold;
                min-height: 45px;
                min-width: 180px;
                border: none;
            }
            QPushButton#ClearBtn:hover { background-color: #4E515B; }

            /* Кнопка Сохранить (Сиреневый акцент) */
            QPushButton#SaveBtn {
                background-color: #7C3AED;
                color: white;
                border-radius: 12px;
                font-family: 'Noto Sans Mono';
                font-weight: bold;
                min-height: 45px;
                min-width: 260px;
                border: none;
            }
            QPushButton#SaveBtn:hover { background-color: #BB9AF7; }
            QPushButton#SaveBtn:disabled { background-color: #3F424A; color: #7F7F7F; }

            /* Выпадающий список моделей */
            QComboBox {
                background-color: #3F424A;
                color: white;
                border: 1px solid #4E515B;
                border-radius: 6px;
                padding: 3px 10px;
                min-width: 140px;
            }

            /* ДИНАМИЧЕСКИЙ СБРОС НА СВЕТЛУЮ ТЕМУ */
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QFrame#SettingsPanel {
                background-color: #F0F2F5; border-color: #E4E6EB;
            }
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QLabel, 
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QCheckBox { color: #1F1F1F; }

            QMainWindow[styleSheet*="background-color: #FFFFFF"] QPushButton#ImageZoneLeft, 
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QFrame#ImageZoneRight {
                background-color: #F0F2F5; border-color: #E4E6EB;
            }
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QPushButton#ImageZoneLeft:hover { border-color: #7C3AED; }

            QMainWindow[styleSheet*="background-color: #FFFFFF"] QTextEdit {
                background-color: white; color: #1F1F1F; border-color: #E4E6EB;
            }
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QPushButton#ClearBtn {
                background-color: #E4E6EB; color: #1F1F1F;
            }
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QPushButton#ClearBtn:hover { background-color: #D8DADF; }
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QComboBox {
                background-color: white; color: #1F1F1F; border-color: #E4E6EB;
            }
        """
        self.setStyleSheet(style_qss)

    def set_placeholder_icon(self, target_widget, icon_key):
        """Вспомогательный метод установки дефолтных иконок 80x80."""
        path = ICONS.get(icon_key, "")
        if os.path.exists(path):
            pix = QPixmap(path).scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
            if isinstance(target_widget, QPushButton):
                target_widget.setIcon(QIcon(pix))
                target_widget.setIconSize(pix.size())
            elif isinstance(target_widget, QLabel):
                target_widget.setPixmap(pix)

    def load_models_to_selector(self):
        """Динамически сканирует папку Models и выводит файлы .pt в комбобокс."""
        if os.path.exists(MODELS_DIR):
            files = [f for f in os.listdir(MODELS_DIR) if f.endswith('.pt')]
            if files:
                self.model_selector.addItems(files)
                return
        self.model_selector.addItems(["yolo11n.pt", "yolo11m.pt", "yolo11x.pt"])

    def change_model(self):
        model_name = self.model_selector.currentText()
        full_path = os.path.join(MODELS_DIR, model_name) if os.path.exists(MODELS_DIR) else model_name
        self.engine.set_model(full_path)

    def update_conf_label(self, value):
        float_val = value / 100.0
        self.conf_val_label.setText(f"{float_val:.2f}")

    # === ЛОГИКА ЗАПУСКА ИИ В ПОТОКЕ ===
    def process_image(self):
        if self.is_processing:
            return

        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть изображение", "", "Images (*.jpg *.jpeg *.png *.webp)"
        )
        if not path:
            return

        self.current_path = path
        self.is_processing = True

        # Обновляем UI перед стартом
        self.progress_bar.show()
        self.btn_save.setText("ОБРАБОТКА...")
        self.btn_save.setEnabled(False)
        self.btn_left_image.setEnabled(False)

        # Вычисляем параметры
        conf = self.conf_slider.value() / 100.0
        only_text = self.mode_checkbox.isChecked()

        # Создаем и запускаем рабочий поток QThread
        self.worker = AnalysisWorker(self.engine, path, conf, only_text)
        self.worker.finished.connect(self.on_analysis_done)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.start()

    @pyqtSlot(dict)
    def on_analysis_done(self, results):
        self.last_results = results

        # Отрисовка исходного фото слева
        pix_left = QPixmap(self.current_path).scaled(450, 350, Qt.AspectRatioMode.KeepAspectRatio,
                                                     Qt.TransformationMode.SmoothTransformation)
        self.btn_left_image.setIcon(QIcon())  # Убираем иконку-заглушку

        # В PyQt кнопке нельзя напрямую поставить Pixmap как фон, поэтому используем трюк со стилем
        self.btn_left_image.setEnabled(True)
        # Отображаем картинку в левой кнопке через QLabel, добавленный поверх, либо меняем иконку на саму картинку:
        self.btn_left_image.setIcon(QIcon(pix_left))
        self.btn_left_image.setIconSize(pix_left.size())

        # Конвертация PIL изображения результатов YOLO в QImage/QPixmap для вывода справа
        pil_img = results["result_img"]
        img_data = pil_img.tobytes("raw", "RGB")
        qimg = QImage(img_data, pil_img.size[0], pil_img.size[1], QImage.Format.Format_RGB888)
        pix_right = QPixmap.fromImage(qimg).scaled(450, 350, Qt.AspectRatioMode.KeepAspectRatio,
                                                   Qt.TransformationMode.SmoothTransformation)
        self.lbl_right_image.setPixmap(pix_right)

        # Сброс прогресс-бара
        self.progress_bar.hide()
        self.btn_save.setText("СОХРАНИТЬ РЕЗУЛЬТАТ")
        self.btn_save.setEnabled(True)
        self.is_processing = False

    @pyqtSlot(str)
    def on_analysis_error(self, err_msg):
        self.progress_bar.hide()
        self.btn_save.setText("ОШИБКА АНАЛИЗА")
        self.btn_left_image.setEnabled(True)
        self.is_processing = False
        QMessageBox.critical(self, "Ошибка", f"Сбой работы модулей ИИ: {err_msg}")

    def clear_all(self):
        self.current_path = None
        self.last_results = None
        self.btn_left_image.setIcon(QIcon())
        self.set_placeholder_icon(self.btn_left_image, "push")
        self.lbl_right_image.clear()
        self.set_placeholder_icon(self.lbl_right_image, "vision")
        self.notes_box.clear()
        self.btn_save.setText("РЕДАКТИРОВАТЬ И СОХРАНИТЬ")
        self.btn_save.setEnabled(False)

    def open_object_editor(self):
        if not self.last_results:
            return
        # Вызываем всплывающее диалоговое окно редактора чекбоксов
        dialog = ObjectEditorDialog(self.current_path, self.last_results, self.notes_box.toPlainText().strip(),
                                    self.main_window, self)
        if dialog.exec():
            # Если сохранение прошло успешно, отключаем кнопку
            self.btn_save.setText("СОХРАНЕНО В БД")
            self.btn_save.setEnabled(False)
