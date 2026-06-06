import os
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QSizePolicy, QScrollArea
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
        layout.setContentsMargins(25, 40, 25, 40)
        layout.setSpacing(35)

        # QSS Стили для карточек и скроллбара
        # QSS Стили для карточек и скроллбара (фикс текстуры и фона)
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
            QLabel#CardStatus {
                color: #BB9AF7;
                font-weight: bold;
            }

            /* Исправленный вертикальный скроллбар */
            QScrollBar:vertical {
                border: none;
                background-color: #1E1F22; /* Чистый темный фон вместо текстуры Windows */
                width: 10px;
                margin: 15px 0px 15px 0px; /* Отступы сверху и снизу, чтобы не вылезать за скругления карточки */
                border-radius: 5px;
            }

            /* Сам ползунок */
            QScrollBar::handle:vertical {
                background-color: #3F424A;
                min-height: 30px;
                border-radius: 5px;
            }

            /* Ползунок при наведении */
            QScrollBar::handle:vertical:hover {
                background-color: #BB9AF7; /* Лавандовый акцент */
            }

            /* Убираем стрелочки сверху и снизу */
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }

            /* Фикс: принудительно убираем системную шахматную текстуру фона выше и ниже ползунка */
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
                background-color: transparent;
            }

            /* Адаптация скроллбара под СВЕТЛУЮ тему */
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QFrame#InfoCard {
                background-color: #F0F2F5;
                border: 2px solid #E4E6EB;
            }
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QLabel {
                color: #1F1F1F;
            }
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QLabel#CardStatus {
                color: #7C3AED;
            }
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QScrollBar:vertical {
                background-color: #E4E6EB;
            }
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QScrollBar::handle:vertical {
                background-color: #C4C6CC;
            }
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QScrollBar::handle:vertical:hover {
                background-color: #7C3AED;
            }
        """

        self.setStyleSheet(card_style)

        # ==========================================================
        # 1. СВЕДЕНИЯ О СИСТЕМЕ И МОДЕЛЯХ (ЛЕВО, выравнивание по центру)
        # ==========================================================
        left_card = QFrame()
        left_card.setObjectName("InfoCard")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(40, 40, 40, 40)
        left_layout.setSpacing(18)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_path = ICONS.get("vision", "")
        if icon_path and os.path.exists(icon_path):
            icon_label = QLabel()
            pixmap = QPixmap(icon_path)
            scaled_pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(scaled_pixmap)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            left_layout.addWidget(icon_label)

        left_title = QLabel("Сведения о системе")
        left_title.setFont(QFont(self.main_font_name, 20, QFont.Weight.Bold))
        left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(left_title)

        info_text = (
            "Vision Pro AI — профессиональное модульное решение для комплексной автоматической "
            "идентификации объектов и сквозного OCR-распознавания текста.\n"
            "Версия сборки: 3.0.0 PyQt6 Modular\n"
            "Архитектура детекции: YOLOv11\n"
            "Движок распознавания текста: EasyOCR Engine"
        )
        left_content = QLabel(info_text)
        left_content.setFont(QFont(self.main_font_name, 13))
        left_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_content.setWordWrap(True)
        left_layout.addWidget(left_content)

        status_label = QLabel("Статус: Система готова к работе")
        status_label.setObjectName("CardStatus")
        status_label.setFont(QFont(self.main_font_name, 14))
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(status_label)

        # ==========================================================
        # 2. ИНСТРУКЦИЯ ПОЛЬЗОВАТЕЛЯ (ПРАВО, со скроллбаром)
        # ==========================================================
        right_card = QFrame()
        right_card.setObjectName("InfoCard")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(40, 40, 25, 40)  # Уменьшили отступ справа для скроллбара
        right_layout.setSpacing(15)

        # Заголовок инструкции (всегда остается на месте, не прокручивается)
        right_title = QLabel("Инструкция по эксплуатации")
        right_title.setFont(QFont(self.main_font_name, 20, QFont.Weight.Bold))
        right_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        right_layout.addWidget(right_title)

        # Создаем область прокрутки
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        # Прячем стандартную рамку QScrollArea, чтобы она была невидимой
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Виджет-контейнер для содержимого внутри скролла
        scroll_content_widget = QWidget()
        scroll_content_widget.setStyleSheet("background: transparent;")
        scroll_content_layout = QVBoxLayout(scroll_content_widget)
        scroll_content_layout.setContentsMargins(0, 0, 10, 0)  # Отступ от правого края

        # Текст инструкции руководства
        instruction_text = (
            "\tДобро пожаловать в систему!\n\n"
            "\tВ верхней панели расположены основные разделы: идентификатор, история и аналитика.\n\n"
            "\tВ разделе идентификатора происходит испытания имеющихся нейросетей.\n"
            "\tПри желании вы можете скачать собственную модель через встроенный менеджер моделей,указав ссылку на "
            "скачивание, после вы можете задать порог уверенности или выбрать поиск только текста.\n"
            "\tДля того чтобы испытать модель, необходимо загрузить изображение в левый блок, достаточно просто "
            "кликнуть по иконке загрузки\n "
            "В нижней панели имеет окно для заметок, после обработки изображения вы можете составить протокол "
            "исследования."
            "В диалоговом окне разметки отметьте галочками нужные объекты и текст для сохранения."
            "Протокол запишется в базу данных и будет доступен в разделе «История».\n\n"
            "\t В разделе История вы можете ознакомится со всеми проколами и сгенерировать PDF файл.\n\n"
            "\t В разделе Аналитика вы можете просмотреть сводку по найденными объектам за день, неделю и всё время."
            "Так же можете увидеть график частоты проведения испытаний"
        )
        right_content = QLabel(instruction_text)
        right_content.setFont(QFont(self.main_font_name, 12))
        right_content.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        right_content.setWordWrap(True)

        # Собираем область прокрутки
        scroll_content_layout.addWidget(right_content)
        scroll_content_layout.addStretch()
        scroll_area.setWidget(scroll_content_widget)

        # Добавляем скролл в основной слой правой карточки
        right_layout.addWidget(scroll_area)

        # Добавляем карточки в главный слой экрана
        layout.addWidget(left_card)
        layout.addWidget(right_card)
