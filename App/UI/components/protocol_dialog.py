import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QScrollArea,
                             QWidget, QLabel, QPushButton, QFileDialog, QMessageBox)
from PyQt6.QtGui import QFont, QPixmap, QImage
from PyQt6.QtCore import Qt

from App.ReportMaster.report_generator import ReportGenerator


class ProtocolDialog(QDialog):
    def __init__(self, data, main_window, history_screen, parent=None):
        super().__init__(parent)
        self.data = data
        self.main_window = main_window  # Доступ к менеджеру БД
        self.history_screen = history_screen  # Доступ к экрану истории для обновления списка
        self.reporter = ReportGenerator()

        self.setup_ui()
        self.setup_styles()

    def setup_ui(self):
        # Настройка всплывающего окна
        self.setWindowTitle(f"Протокол № {self.data.get('protocol_num', '---')}")
        self.setGeometry(150, 150, 1100, 820)

        # Основной вертикальный слой диалога
        dialog_layout = QVBoxLayout(self)
        dialog_layout.setContentsMargins(30, 30, 30, 30)
        dialog_layout.setSpacing(20)

        # 1. ОБЛАСТЬ ПРОКРУТКИ ДЛЯ ИНФОРМАЦИИ (Аналог CTkScrollableFrame)
        scroll_area = QScrollArea()
        scroll_area.setObjectName("ProtocolScroll")
        scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()
        scroll_content.setObjectName("ScrollContent")
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(40, 20, 40, 20)
        content_layout.setSpacing(20)

        # Заголовок протокола
        title_lbl = QLabel(f"Протокол исследования № {self.data.get('protocol_num', '---')}")
        title_lbl.setFont(QFont("Noto Sans Mono", 22, QFont.Weight.Bold))
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title_lbl)

        # Дата создания
        date_lbl = QLabel(f"Дата: {self.data.get('date_str', '---')}")
        date_lbl.setFont(QFont("Noto Sans Mono", 12))
        date_lbl.setStyleSheet("color: gray;")
        date_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(date_lbl)

        # Отображение закэшированной ИИ-картинки из ResultsImages
        img_path = self.data.get('result_file_path', '')
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if img_path and os.path.exists(img_path):
            pix = QPixmap(img_path).scaled(480, 360, Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)
            self.img_label.setPixmap(pix)
        else:
            self.img_label.setText("Файл изображения не найден в локальном хранилище ResultsImages")
            self.img_label.setStyleSheet("color: #FF4C4C; font-weight: bold;")

        content_layout.addWidget(self.img_label)

        # Блок "Заметки эксперта"
        lbl_n_title = QLabel("Заметки эксперта:")
        lbl_n_title.setFont(QFont("Noto Sans Mono", 13, QFont.Weight.Bold))
        content_layout.addWidget(lbl_n_title)

        notes_txt = self.data.get('user_notes', '-') or "-"
        self.lbl_notes = QLabel(notes_txt)
        self.lbl_notes.setFont(QFont("Noto Sans Mono", 12))
        self.lbl_notes.setWordWrap(True)
        content_layout.addWidget(self.lbl_notes)

        # Блок "Обнаруженные объекты"
        lbl_obj_title = QLabel("Обнаруженные объекты:")
        lbl_obj_title.setFont(QFont("Noto Sans Mono", 13, QFont.Weight.Bold))
        content_layout.addWidget(lbl_obj_title)

        objs_txt = self.data.get('detected_objects', 'Не определены')
        self.lbl_objs = QLabel(objs_txt)
        self.lbl_objs.setFont(QFont("Noto Sans Mono", 12))
        self.lbl_objs.setWordWrap(True)
        content_layout.addWidget(self.lbl_objs)

        # Блок "Распознанный текст (OCR)"
        lbl_ocr_title = QLabel("Распознанный текст (OCR):")
        lbl_ocr_title.setFont(QFont("Noto Sans Mono", 13, QFont.Weight.Bold))
        content_layout.addWidget(lbl_ocr_title)

        ocr_txt = self.data.get('ocr_text', 'Текст не обнаружен')
        self.lbl_ocr = QLabel(ocr_txt)
        self.lbl_ocr.setFont(QFont("Noto Sans Mono", 12))
        self.lbl_ocr.setWordWrap(True)
        content_layout.addWidget(self.lbl_ocr)

        scroll_area.setWidget(scroll_content)
        dialog_layout.addWidget(scroll_area, 1)

        # 2. ПАНЕЛЬ УПРАВЛЕНИЯ (КНОПКИ) ВНИЗУ ОКНА
        bottom_box = QWidget()
        bottom_layout = QHBoxLayout(bottom_box)
        bottom_layout.setContentsMargins(0, 10, 0, 0)

        self.btn_delete = QPushButton("УДАЛИТЬ ПРОТОКОЛ")
        self.btn_delete.setObjectName("DeleteBtn")
        self.btn_delete.clicked.connect(self.delete_protocol)
        bottom_layout.addWidget(self.btn_delete)

        bottom_layout.addStretch()

        self.btn_export = QPushButton("ЭКСПОРТ В PDF")
        self.btn_export.setObjectName("ExportBtn")
        self.btn_export.clicked.connect(self.export_pdf)
        bottom_layout.addWidget(self.btn_export)

        dialog_layout.addWidget(bottom_box)

    def setup_styles(self):
        """Подключает лавандовую стилизацию, зависимую от выбранной темы в MainWindow."""
        style_qss = """
            QDialog { background-color: #1E1F22; }
            QLabel { color: #DFE1E5; }

            /* Стили скролл-бара и контента */
            QScrollArea#ProtocolScroll {
                background-color: #2B2D31;
                border: 2px solid #3F424A;
                border-radius: 20px;
            }
            QWidget#ScrollContent { background-color: transparent; }

            /* Кнопка Экспорта (Лавандовый акцент) */
            QPushButton#ExportBtn {
                background-color: #7C3AED;
                color: white;
                border-radius: 12px;
                font-family: 'Noto Sans Mono';
                font-weight: bold;
                min-height: 45px;
                min-width: 220px;
                border: none;
            }
            QPushButton#ExportBtn:hover { background-color: #BB9AF7; }

            /* Кнопка Удалить (Красный акцент) */
            QPushButton#DeleteBtn {
                background-color: #442326;
                color: #F85149;
                border-radius: 12px;
                font-family: 'Noto Sans Mono';
                font-weight: bold;
                min-height: 45px;
                min-width: 220px;
                border: 1px solid #6E2E31;
            }
            QPushButton#DeleteBtn:hover { background-color: #DA3637; color: white; }

            /* ДИНАМИЧЕСКИЙ ПЕРЕКЛЮЧАТЕЛЬ СТИЛЕЙ НА СВЕТЛУЮ ТЕМУ ЧАТА */
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QDialog { background-color: #FFFFFF; }
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QLabel { color: #1F1F1F; }
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QScrollArea#ProtocolScroll {
                background-color: #F0F2F5; border-color: #E4E6EB;
            }
        """
        # Принудительно проверяем состояние темы главного окна, чтобы диалог открылся в нужном цвете
        if not self.main_window.is_dark_theme:
            style_qss = style_qss.replace("#1E1F22", "#FFFFFF").replace("#DFE1E5", "#1F1F1F").replace("#2B2D31",
                                                                                                      "#F0F2F5").replace(
                "#3F424A", "#E4E6EB")
        self.setStyleSheet(style_qss)

    def export_pdf(self):
        """Метод вызова генерации PDF отчета через модуль ReportGenerator."""
        p_num = self.data.get('protocol_num', '000')
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить PDF отчет",
            f"Protocol_{p_num}.pdf",
            "PDF Files (*.pdf)"
        )
        if file_path:
            success = self.reporter.export_pdf(file_path, self.data)
            if success:
                QMessageBox.information(self, "Успех", "PDF отчет успешно создан!")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось создать PDF файл.")

    def delete_protocol(self):
        """Метод безопасного удаления текущей записи из базы данных."""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Вы уверены, что хотите удалить этот протокол?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            record_id = self.data.get('id')
            if self.main_window.db.delete_record(record_id):
                # Закрываем это окно, обновляем интерфейс таблицы истории и выдаем лог
                self.accept()
                self.history_screen.apply_filters()  # Вызываем рефреш списка
                QMessageBox.information(self, "Успех", "Запись успешно удалена из базы данных.")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось удалить запись из базы данных.")
