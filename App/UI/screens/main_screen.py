import os
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt
from App.CFG.config import ICONS

class MainScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_font_name = "Noto Sans Mono"
        self.setup_ui()

    def setup_ui(self):
        # Главный слой экрана — горизонтальный, чтобы расположить две карточки рядом
        layout = QHBoxLayout(self)
        layout.setContentsMargins(25, 100, 25, 100)
        layout.setSpacing(35)

        # Данные для карточек (интегрировано из вашего старого кода)
        info_blocks = [
            {
                "title": "Сведения о приложении",
                "content": "Vision Pro AI — профессиональное решение\nдля автоматической идентификации объектов.\n\nВерсия системы: 3.0.0 PyQt6 Modular",
                "icon_key": "vision"
            },
            {
                "title": "Сведения о моделях ИИ",
                "content": "Архитектура детекции: YOLOv11 (Ultra)\nПоддержка текста: EasyOCR Engine\n\nСтатус: Готов к работе",
                "icon_key": "push"
            }
        ]

        # QSS Стили для карточек, которые идеально подстраиваются под тему главного окна
        card_style = """
            QFrame#InfoCard {
                background-color: #2B2D31;
                border: 2px solid #3F424A;
                border-radius: 40px;
            }
            QLabel {
                color: #DFE1E5;
                background-color: transparent;
                border: none;
            }
            /* Динамическое изменение стилей для светлой темы */
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QFrame#InfoCard {
                background-color: #F0F2F5;
                border: 2px solid #E4E6EB;
            }
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QLabel {
                color: #1F1F1F;
            }
        """
        self.setStyleSheet(card_style)

        for info in info_blocks:
            # Создаем контейнер карточки
            card = QFrame()
            card.setObjectName("InfoCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(40, 40, 40, 40)
            card_layout.setSpacing(20)
            card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Добавляем иконку в карточку, если она существует в конфиге
            icon_path = ICONS.get(info["icon_key"], "")
            if icon_path and os.path.exists(icon_path):
                icon_label = QLabel()
                pixmap = QPixmap(icon_path)
                # Масштабируем иконку до исходных размеров 80x80
                scaled_pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                icon_label.setPixmap(scaled_pixmap)
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                card_layout.addWidget(icon_label)

            # Заголовок карточки
            title_label = QLabel(info["title"])
            title_font = QFont(self.main_font_name, 20, QFont.Weight.Bold)
            title_label.setFont(title_font)
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(title_label)

            # Текст описания карточки
            content_label = QLabel(info["content"])
            content_font = QFont(self.main_font_name, 13)
            content_label.setFont(content_font)
            content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_label.setWordWrap(True)  # Перенос строк при сужении окна
            card_layout.addWidget(content_label)

            # Добавляем готовую карточку на экран
            layout.addWidget(card)
