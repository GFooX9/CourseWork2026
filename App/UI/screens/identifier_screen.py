import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
                             QSlider, QComboBox, QCheckBox, QPushButton,
                             QTextEdit, QProgressBar, QFileDialog, QMessageBox,
                             QSizePolicy)
from PyQt6.QtGui import QFont, QPixmap, QImage, QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from App.CFG.config import ICONS, MODELS_DIR
from App.Engine.vision_engine import VisionEngine
from App.UI.components.object_editor import ObjectEditorDialog
from App.UI.components.yolo_installer_dialog import YoloInstallerDialog


# === РАБОЧИЙ ПОТОК ДЛЯ ИИ-АНАЛИЗА ===
class AnalysisWorker(QThread):
    analysis_completed = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, engine: VisionEngine, image_path: str, conf: float, only_text: bool):
        super().__init__()
        self.engine = engine
        self.image_path = image_path
        self.conf = conf
        self.only_text = only_text

    def run(self):
        try:
            results = self.engine.analyze(self.image_path, self.conf, self.only_text)
            if results:
                self.analysis_completed.emit(results)
            else:
                self.error.emit("Движок вернул пустой результат.")
        except Exception as e:
            self.error.emit(str(e))


# === ГЛАВНЫЙ КЛАСС ЭКРАНА ИДЕНТИФИКАЦИИ ===
class IdentifierScreen(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.engine = VisionEngine()
        self.current_path = None
        self.last_results = None
        self.is_processing = False
        self.worker = None

        # Объявление всех атрибутов в __init__
        self.model_selector = None
        self.btn_install_models = None
        self.mode_checkbox = None
        self.conf_slider = None
        self.conf_val_label = None
        self.btn_left_image = None
        self.panel_right_res = None
        self.lbl_right_image = None
        self.progress_bar = None
        self.notes_box = None
        self.btn_clear = None
        self.btn_save = None

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

        # Выделенный шрифт пользователя для элементов управления панели
        user_font = QFont("Noto Sans Mono", 11, QFont.Weight.Bold)

        lbl_model = QLabel("Модель:")
        lbl_model.setFont(user_font)

        # Правка 1: Шрифт выбора модели приведен к вашему стандарту
        self.model_selector = QComboBox()
        self.model_selector.setFont(user_font)
        self.model_selector.currentIndexChanged.connect(self.change_model)

        # Правка 2: Надпись "Менеджер моделей" переведена на ваш шрифт
        self.btn_install_models = QPushButton("Менеджер моделей")
        self.btn_install_models.setObjectName("InstallModelsBtn")
        self.btn_install_models.setFont(user_font)
        self.btn_install_models.clicked.connect(self.open_model_installer)
        self.btn_install_models.setCursor(Qt.CursorShape.PointingHandCursor)

        settings_layout.addWidget(lbl_model)
        settings_layout.addWidget(self.model_selector)
        settings_layout.addWidget(self.btn_install_models)

        # Инициализация чекбокса с вашим шрифтом
        self.mode_checkbox = QCheckBox("Только Текст")
        self.mode_checkbox.setFont(user_font)
        settings_layout.addWidget(self.mode_checkbox)

        lbl_conf = QLabel("Точность (Conf):")
        lbl_conf.setFont(user_font)

        self.conf_slider = QSlider(Qt.Orientation.Horizontal)
        self.conf_slider.setMinimum(10)
        self.conf_slider.setMaximum(100)
        self.conf_slider.setValue(25)
        self.conf_slider.setTickInterval(10)
        self.conf_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.conf_slider.valueChanged.connect(self.update_conf_label)

        self.conf_val_label = QLabel("0.25")
        self.conf_val_label.setFont(user_font)

        settings_layout.addWidget(lbl_conf)
        settings_layout.addWidget(self.conf_slider)
        settings_layout.addWidget(self.conf_val_label)
        main_layout.addWidget(settings_panel)

        # 2. ЦЕНТРАЛЬНЫЙ БЛОК (ЛЕВАЯ И ПРАВАЯ ЗОНЫ)
        content_box = QWidget()
        content_layout = QHBoxLayout(content_box)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

        self.btn_left_image = QPushButton()
        self.btn_left_image.setObjectName("ImageZoneLeft")
        self.btn_left_image.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_left_image.setMinimumSize(450, 350)
        self.btn_left_image.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.btn_left_image.clicked.connect(self.process_image)
        self.set_placeholder_icon(self.btn_left_image, "push")
        content_layout.addWidget(self.btn_left_image, 1)

        self.panel_right_res = QFrame()
        self.panel_right_res.setObjectName("ImageZoneRight")
        self.panel_right_res.setMinimumSize(450, 350)
        self.panel_right_res.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

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
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # 4. ПОЛЕ ДЛЯ ЗАМЕТОК ЭКСПЕРТА
        lbl_notes = QLabel("Заметки эксперта (по желанию):")
        lbl_notes.setFont(user_font)
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
        style_qss = """
        QFrame#SettingsPanel { background-color: #2B2D31; border: 1px solid #3F424A; border-radius: 12px; }
        QLabel { color: #DFE1E5; }

        /* Правка 3: Блок-галочка (Только текст) увеличена и скруглена */
        QCheckBox { 
            color: #DFE1E5; 
            spacing: 8px;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 5px;
            border: 2px solid #3F424A;
            background-color: #1E1F22;
        }
        QCheckBox::indicator:hover {
            border-color: #BB9AF7;
        }
        QCheckBox::indicator:checked {
            background-color: #7C3AED;
            border-color: #BB9AF7;
        }

        /* ПРАВКА 4: Палка ползунка на шкале уверенности (Slider handle) переведена в сиреневый цвет */
        QSlider::groove:horizontal {
            border: 1px solid #3F424A;
            height: 6px;
            background: #1E1F22;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #BB9AF7, stop:1 #7C3AED);
            border: 1px solid #A970FF;
            width: 14px;
            height: 20px;
            margin: -7px 0;
            border-radius: 4px;
        }
        QSlider::handle:horizontal:hover {
            background: #BB9AF7;
            border-color: #FFFFFF;
        }

        QPushButton#ImageZoneLeft, QFrame#ImageZoneRight { 
            background-color: #2B2D31; border: 2px dashed #3F424A; border-radius: 20px; 
        }
        QPushButton#ImageZoneLeft:hover { border-color: #BB9AF7; }
        QTextEdit { background-color: #2B2D31; color: white; border: 1px solid #3F424A; border-radius: 10px; padding: 5px; }

        QProgressBar {
            border: 2px solid #BB9AF7;
            border-radius: 10px;
            background-color: #1E1F22;
            text-align: center;
            height: 20px;
        }
        QProgressBar::chunk {
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7C3AED, stop:1 #BB9AF7);
            border-radius: 8px;
        }
        QPushButton#ClearBtn { 
            background-color: #3F424A; color: #DFE1E5; border-radius: 12px; 
            font-family: 'Noto Sans Mono'; font-weight: bold; min-height: 45px; min-width: 180px; border: none; 
        }
        QPushButton#ClearBtn:hover { background-color: #4E515B; }

        QPushButton#SaveBtn { 
            background-color: #7C3AED; color: white; border-radius: 12px; 
            font-family: 'Noto Sans Mono'; font-weight: bold; min-height: 45px; min-width: 260px; border: none; 
        }
        QPushButton#SaveBtn:hover { background-color: #BB9AF7; }
        QPushButton#SaveBtn:disabled { background-color: #3F424A; color: #7F7F7F; }

        QPushButton#InstallModelsBtn {
            background-color: #3F424A; color: white; border: 1px solid #4E515B; border-radius: 6px; padding: 4px 12px;
        }
        QPushButton#InstallModelsBtn:hover { background-color: #4E515B; border-color: #BB9AF7; }

        QComboBox { background-color: #3F424A; color: white; border: 1px solid #4E515B; border-radius: 6px; padding: 4px 10px; min-width: 140px; }
        QComboBox:hover { border-color: #BB9AF7; }

        QMainWindow[styleSheet*="background-color: #FFFFFF"] QFrame#SettingsPanel { background-color: #F0F2F5; border-color: #E4E6EB; }
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QLabel, 
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QCheckBox { color: #1F1F1F; }
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QPushButton#ImageZoneLeft, 
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QFrame#ImageZoneRight { background-color: #F0F2F5; border-color: #E4E6EB; }
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QPushButton#ImageZoneLeft:hover { border-color: #7C3AED; }
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QTextEdit { background-color: white; color: #1F1F1F; border-color: #E4E6EB; }
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QPushButton#ClearBtn { background-color: #E4E6EB; color: #1F1F1F; }
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QPushButton#ClearBtn:hover { background-color: #D8DADF; }
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QComboBox { background-color: white; color: #1F1F1F; border-color: #E4E6EB; }
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QPushButton#InstallModelsBtn { background-color: #E4E6EB; color: #1F1F1F; border-color: #D8DADF; }
        """
        self.setStyleSheet(style_qss)

    def set_placeholder_icon(self, target_widget, icon_key):
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
        """Сканирует локальную папку Source/Models и динамически наполняет выпадающий список выбора ИИ-моделей."""
        from App.CFG.config import MODELS_DIR
        target_dir = MODELS_DIR
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        files = [f for f in os.listdir(target_dir) if f.endswith(('.pt', '.onnx'))]

        self.model_selector.blockSignals(True)
        self.model_selector.clear()
        if files:
            files.sort()
            self.model_selector.addItems(files)
            print(f"[UI Selector] Успешно подгружено моделей с диска: {len(files)}")
        else:
            self.model_selector.addItems(["yolo11n.pt", "yolo11s.pt", "yolo11m.pt", "yolo11x.pt"])
            print("[UI Selector Warning] Папка моделей пуста. Выведены дефолтные пресеты.")
        self.model_selector.blockSignals(False)
        self.change_model()

    def change_model(self):
        """Передает чистый текст имени файла в бэкенд оркестратора."""
        model_name = self.model_selector.currentText()
        if model_name:
            self.engine.set_model(model_name)

    def open_model_installer(self):
        """Открывает диалоговое окно установщика моделей и обновляет селектор при закрытии."""
        dialog = YoloInstallerDialog(self)
        dialog.exec()
        self.load_models_to_selector()

    def update_conf_label(self, value):
        float_val = value / 100.0
        self.conf_val_label.setText(f"{float_val:.2f}")

    def process_image(self):
        if self.is_processing:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Открыть изображение", "", "Images (*.jpg *.jpeg *.png *.webp)")
        if not path:
            return
        self.current_path = path
        self.is_processing = True
        self.progress_bar.show()
        self.btn_save.setText("ОБРАБОТКА...")
        self.btn_save.setEnabled(False)
        self.btn_left_image.setEnabled(False)

        conf = self.conf_slider.value() / 100.0
        only_text = self.mode_checkbox.isChecked()
        self.worker = AnalysisWorker(self.engine, path, conf, only_text)
        self.worker.analysis_completed.connect(self.on_analysis_done)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.start()

    @pyqtSlot(dict)
    def on_analysis_done(self, results):
        self.last_results = results
        w = self.btn_left_image.width()
        h = self.btn_left_image.height()
        pix_left = QPixmap(self.current_path).scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio,
                                                     Qt.TransformationMode.SmoothTransformation)
        self.btn_left_image.setIcon(QIcon())
        self.btn_left_image.setEnabled(True)
        self.btn_left_image.setIcon(QIcon(pix_left))
        self.btn_left_image.setIconSize(pix_left.size())

        pil_img = results["result_img"]
        img_data = pil_img.tobytes("raw", "RGB")
        bytes_per_line = pil_img.width * 3
        qimg = QImage(img_data, pil_img.width, pil_img.height, bytes_per_line, QImage.Format.Format_RGB888)
        w_r = self.panel_right_res.width()
        h_r = self.panel_right_res.height()
        pix_right = QPixmap.fromImage(qimg).scaled(w_r, h_r, Qt.AspectRatioMode.KeepAspectRatio,
                                                   Qt.TransformationMode.SmoothTransformation)
        self.lbl_right_image.setPixmap(pix_right)
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
        dialog = ObjectEditorDialog(self.current_path, self.last_results,
                                    self.notes_box.toPlainText().strip(),
                                    self.main_window, self)

        # НАШ ФИКС: Передаем команду обновления интерфейса в экран истории
        if hasattr(self.main_window, 'history_screen'):
            dialog.database_updated.connect(self.main_window.history_screen.refresh_ui)

        if dialog.exec():
            self.btn_save.setText("СОХРАНЕНО В БД")

