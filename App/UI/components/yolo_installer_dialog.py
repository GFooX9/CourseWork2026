import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLineEdit, QLabel, QProgressBar, QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt
from App.Engine.model_installer import ModelDownloadWorker


class YoloInstallerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.btn_rows = {}  # Словарь для хранения ссылок на кнопки строк [(filename): (btn_install, btn_delete)]
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Менеджер ИИ моделей YOLO")
        self.setFixedSize(550, 400)  # Слегка увеличили ширину под новую кнопку

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # --- БЛОК 1. БЫСТРАЯ УСТАНОВКА И УДАЛЕНИЕ СТАНДАРТНЫХ МОДЕЛЕЙ ---
        preset_group = QGroupBox("Предустановленные модели YOLO11")
        preset_layout = QVBoxLayout(preset_group)
        preset_layout.setSpacing(8)

        self.presets = [
            ("yolo11n.pt", "Скачать Nano (Сверхбыстрая, 11 МБ)", "https://github.com"),
            ("yolo11s.pt", "Скачать Small (Сбалансированная, 22 МБ)", "https://github.com"),
            ("yolo11m.pt", "Скачать Medium (Универсальная, 40 МБ)", "https://github.com"),
            ("yolo11x.pt", "Скачать Extra Large (Максимальная точность, 114 МБ)", "https://github.com")
        ]

        for filename, desc, url in self.presets:
            btn_layout = QHBoxLayout()
            lbl = QLabel(desc)

            # Кнопка установки
            btn_install = QPushButton("Установить" if not self._is_installed(filename) else "Установлено")
            btn_install.setFixedWidth(110)
            btn_install.setEnabled(not self._is_installed(filename))
            btn_install.clicked.connect(lambda checked, u=url, f=filename, b=btn_install: self.start_download(u, f, b))

            # Кнопка удаления (Новая фича!)
            btn_delete = QPushButton("Удалить")
            btn_delete.setFixedWidth(80)
            btn_delete.setObjectName("DeleteBtn")
            btn_delete.setEnabled(self._is_installed(filename))
            btn_delete.clicked.connect(lambda checked, f=filename: self.delete_model(f))

            # Сохраняем ссылки на кнопки, чтобы менять их статус на лету
            self.btn_rows[filename] = (btn_install, btn_delete)

            btn_layout.addWidget(lbl)
            btn_layout.addWidget(btn_install)
            btn_layout.addWidget(btn_delete)
            preset_layout.addLayout(btn_layout)

        layout.addWidget(preset_group)

        # --- БЛОК 2. ЗАГРУЗКА ПО КАСТОМНОЙ ССЫЛКЕ ---
        custom_group = QGroupBox("Установка кастомной модели по URL-ссылке")
        custom_layout = QVBoxLayout(custom_group)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Вставьте прямую ссылку на .pt или .onnx файл...")
        custom_layout.addWidget(self.url_input)

        self.btn_custom_download = QPushButton("Скачать кастомную модель")
        self.btn_custom_download.clicked.connect(self.start_custom_download)
        custom_layout.addWidget(self.btn_custom_download)

        layout.addWidget(custom_group)

        # --- БЛОК 3. ДИНАМИЧЕСКИЙ ПРОГРЕСС СКАЧИВАНИЯ ---
        self.status_label = QLabel("Статус: Ожидание действий пользователя")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # СТИЛИ И ПАЛИТРА С КОНТРАСТНЫМ ТЕКСТОМ
        dialog_qss = """
            QDialog { background-color: #F0F2F5; }
            QGroupBox {
                color: #000000; font-family: 'Noto Sans Mono'; font-weight: bold;
                border: 1px solid #D8DADF; margin-top: 12px; padding-top: 15px;
            }
            QLabel { color: #000000; font-family: 'Noto Sans Mono'; font-size: 12px; font-weight: 500; }
            QLineEdit { background-color: white; color: #000000; border: 1px solid #D8DADF; border-radius: 6px; padding: 6px; }
            QPushButton {
                background-color: #E4E6EB; color: #000000; border-radius: 6px;
                font-family: 'Noto Sans Mono'; font-weight: bold; border: 1px solid #D8DADF; padding: 5px;
            }
            QPushButton:hover { background-color: #D8DADF; border-color: #BB9AF7; }
            QPushButton:disabled { background-color: #E4E6EB; color: #8A8D93; }

            /* Стили для красной кнопки удаления */
            QPushButton#DeleteBtn { background-color: #FADBD8; color: #C0392B; border: 1px solid #E6B0AA; }
            QPushButton#DeleteBtn:hover { background-color: #F5B7B1; border-color: #E74C3C; }
            QPushButton#DeleteBtn:disabled { background-color: #E4E6EB; color: #8A8D93; border-color: #D8DADF; }
        """
        self.setStyleSheet(dialog_qss)

    def _is_installed(self, filename: str) -> bool:
        """Проверяет физическое наличие файла модели в нужной папке"""
        return os.path.exists(os.path.join("Source", "Models", filename))

    def start_download(self, url: str, filename: str, target_button: QPushButton = None):
        """Запуск фонового потока скачивания"""
        self.setEnabled(False)
        self.progress_bar.setValue(0)

        self.worker = ModelDownloadWorker(url, filename)
        self.worker.progress_changed.connect(self.progress_bar.setValue)
        self.worker.status_changed.connect(self.status_label.setText)
        self.worker.finished.connect(
            lambda success, msg, b=target_button, f=filename: self.on_download_finished(success, msg, b, f))
        self.worker.start()

    def start_custom_download(self):
        url = self.url_input.text().strip()
        if not url.startswith(("http://", "https://")):
            QMessageBox.warning(self, "Внимание",
                                "Пожалуйста, введите корректную ссылку, начинающуюся с http:// или https://")
            return
        self.start_download(url, None, None)

    def on_download_finished(self, success: bool, message: str, target_button: QPushButton = None,
                             filename: str = None):
        """Вызывается автоматически, когда поток завершил скачивание"""
        self.setEnabled(True)

        if success:
            QMessageBox.information(self, "Успех", message)
            if filename in self.btn_rows:
                btn_inst, btn_del = self.btn_rows[filename]
                btn_inst.setText("Установлено")
                btn_inst.setEnabled(False)
                btn_del.setEnabled(True)  # Разрешаем удаление
            self.url_input.clear()
            self.status_label.setText("Статус: Готово")
        else:
            QMessageBox.critical(self, "Ошибка загрузки", message)
            self.status_label.setText("Статус: Ошибка")

        self.progress_bar.setValue(0)

    def delete_model(self, filename: str):
        """Метод безопасного удаления файла модели с диска с подтверждением"""
        # Предупреждаем пользователя перед удалением тяжелых файлов
        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Вы действительно хотите навсегда удалить файл {filename} с диска?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            file_path = os.path.join("Source", "Models", filename)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)

                QMessageBox.information(self, "Успех", f"Файл {filename} успешно удален.")

                # Переключаем кнопки в интерфейсе обратно в режим «Установить»
                if filename in self.btn_rows:
                    btn_inst, btn_del = self.btn_rows[filename]
                    btn_inst.setText("Установить")
                    btn_inst.setEnabled(True)
                    btn_del.setEnabled(False)  # Блокируем кнопку удаления

                self.status_label.setText(f"Файл {filename} удален")

            except Exception as e:
                QMessageBox.critical(self, "Ошибка удаления",
                                     f"Не удалось удалить файл: {str(e)}\nВозможно, он сейчас используется бэкендом.")
