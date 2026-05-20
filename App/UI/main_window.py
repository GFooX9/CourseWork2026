import sys
import os
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QApplication
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt


from App.UI.screens.main_screen import MainScreen
from App.UI.screens.identifier_screen import IdentifierScreen
from App.UI.screens.analytics_screen import AnalyticsScreen
from App.UI.screens.history_screen import HistoryScreen
from App.CFG.config import ICONS
from App.Data.database_manager import DatabaseManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.is_dark_theme = True  # По умолчанию включаем темную тему нашего чата

        # Настройка главного окна
        self.setWindowTitle("Object Identifier Pro v3.0 (PyQt6)")
        self.setGeometry(100, 100, 1200, 850)

        if os.path.exists(ICONS["main_icon"]):
            self.setWindowIcon(QIcon(ICONS["main_icon"]))

        # Главный контейнер
        self.main_widget = QWidget()
        self.main_widget.setObjectName("MainWidget")
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(20)

        # 1. Создаем верхнюю навигационную панель
        self.setup_navigation()

        # 2. Создаем контейнер для экранов
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("StackedContainer")
        self.main_layout.addWidget(self.stacked_widget)

        self.setCentralWidget(self.main_widget)

        # Применяем тему оформления при старте
        self.apply_theme()

        # Инициализация пустых экранов-заглушек (их мы заменим в следующих шагах)
        self.setup_screens()

    def setup_navigation(self):
        """Создает верхнюю панель навигации приложения в стиле чата."""
        self.nav_frame = QWidget()
        self.nav_frame.setObjectName("NavFrame")
        nav_layout = QHBoxLayout(self.nav_frame)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(12)

        # Кнопки страниц
        self.btn_main = QPushButton("Главное меню")
        self.btn_id = QPushButton("Идентификатор")
        self.btn_history = QPushButton("История")
        self.btn_analytics = QPushButton("Аналитика")

        for btn in [self.btn_main, self.btn_id, self.btn_history, self.btn_analytics]:
            btn.setProperty("class", "nav-btn")
            nav_layout.addWidget(btn)

        nav_layout.addStretch()

        # Кнопка переключения тем (Светлая / Темная)
        self.btn_theme = QPushButton("🌙 Темная")
        self.btn_theme.setObjectName("ThemeBtn")
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.clicked.connect(self.toggle_theme)
        nav_layout.addWidget(self.btn_theme)

        # Кнопка Выход
        btn_exit = QPushButton("ВЫЙТИ")
        btn_exit.setObjectName("ExitBtn")
        btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exit.clicked.connect(QApplication.instance().quit)
        nav_layout.addWidget(btn_exit)

        self.main_layout.addWidget(self.nav_frame)

        # Логика переключения индексов stacked_widget
        self.btn_main.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.btn_id.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.btn_history.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        self.btn_analytics.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))

    def toggle_theme(self):
        """Переключает флаг темы и обновляет интерфейс."""
        self.is_dark_theme = not self.is_dark_theme
        if self.is_dark_theme:
            self.btn_theme.setText("🌙 Темная")
        else:
            self.btn_theme.setText("☀️ Светлая")
        self.apply_theme()

    def apply_theme(self):
        """Определяет стили QSS для темной и светлой тем с сиреневыми акцентами."""
        if self.is_dark_theme:
            # ТЕМНАЯ ТЕМА (Графитовый фон нашего чата + Светло-сиреневые акценты)
            qss = """
                QMainWindow, QWidget#MainWidget { background-color: #1E1F22; }
                QWidget#NavFrame { background-color: transparent; }

                /* Кнопки навигации */
                QPushButton.nav-btn {
                    background-color: #2B2D31;
                    color: #DFE1E5;
                    border-radius: 12px;
                    font-family: 'Noto Sans Mono';
                    font-size: 15px;
                    font-weight: bold;
                    min-height: 50px;
                    min-width: 170px;
                    border: 1px solid #3F424A;
                }
                QPushButton.nav-btn:hover { background-color: #35373C; border-color: #A970FF; }
                QPushButton.nav-btn:pressed { background-color: #1E1F22; }

                /* Кнопка смены темы (Светло-сиреневый акцент) */
                QPushButton#ThemeBtn {
                    background-color: #2B2D31;
                    color: #BB9AF7;
                    border-radius: 12px;
                    font-family: 'Noto Sans Mono';
                    font-size: 14px;
                    font-weight: bold;
                    min-height: 50px;
                    min-width: 120px;
                    border: 1px solid #3F424A;
                }
                QPushButton#ThemeBtn:hover { background-color: #35373C; border-color: #BB9AF7; }

                /* Кнопка Выход */
                QPushButton#ExitBtn {
                    background-color: #442326;
                    color: #F85149;
                    border-radius: 12px;
                    font-family: 'Noto Sans Mono';
                    font-size: 15px;
                    font-weight: bold;
                    min-height: 50px;
                    min-width: 140px;
                    border: 1px solid #6E2E31;
                }
                QPushButton#ExitBtn:hover { background-color: #DA3637; color: white; }
            """
        else:
            # СВЕТЛАЯ ТЕМА (Чистый светлый фон чата + Насыщенный лавандовый акцент)
            qss = """
                QMainWindow, QWidget#MainWidget { background-color: #FFFFFF; }
                QWidget#NavFrame { background-color: transparent; }

                /* Кнопки навигации */
                QPushButton.nav-btn {
                    background-color: #F0F2F5;
                    color: #1F1F1F;
                    border-radius: 12px;
                    font-family: 'Noto Sans Mono';
                    font-size: 15px;
                    font-weight: bold;
                    min-height: 50px;
                    min-width: 170px;
                    border: 1px solid #E4E6EB;
                }
                QPushButton.nav-btn:hover { background-color: #E4E6EB; border-color: #7C3AED; }
                QPushButton.nav-btn:pressed { background-color: #D8DADF; }

                /* Кнопка смены темы (Лавандовый акцент) */
                QPushButton#ThemeBtn {
                    background-color: #F0F2F5;
                    color: #7C3AED;
                    border-radius: 12px;
                    font-family: 'Noto Sans Mono';
                    font-size: 14px;
                    font-weight: bold;
                    min-height: 50px;
                    min-width: 120px;
                    border: 1px solid #E4E6EB;
                }
                QPushButton#ThemeBtn:hover { background-color: #E4E6EB; border-color: #7C3AED; }

                /* Кнопка Выход */
                QPushButton#ExitBtn {
                    background-color: #FFEBEB;
                    color: #FF4C4C;
                    border-radius: 12px;
                    font-family: 'Noto Sans Mono';
                    font-size: 15px;
                    font-weight: bold;
                    min-height: 50px;
                    min-width: 140px;
                    border: 1px solid #FFCCCC;
                }
                QPushButton#ExitBtn:hover { background-color: #FF4C4C; color: white; }
            """
        self.setStyleSheet(qss)

    def setup_screens(self):
        """Инициализирует и добавляет готовые экраны в менеджер компоновки QStackedWidget."""
        # Индекс 0 — Главный экран
        self.main_screen = MainScreen(self)
        self.stacked_widget.addWidget(self.main_screen)

        # Индекс 1 — Идентификатор
        self.id_screen = IdentifierScreen(self, self)
        self.stacked_widget.addWidget(self.id_screen)

        # Индекс 2 — История
        self.history_screen = HistoryScreen(self, self)
        self.stacked_widget.addWidget(self.history_screen)

        # Индекс 3 — Аналитика
        self.analytics_screen = AnalyticsScreen(self, self)
        self.stacked_widget.addWidget(self.analytics_screen)

        # НАСТРОЙКА АВТООБНОВЛЕНИЯ ДАННЫХ ПРИ ПЕРЕХОДЕ ПО ВКЛАДКАМ
        self.btn_history.clicked.connect(self.history_screen.refresh_ui)
        self.btn_analytics.clicked.connect(self.analytics_screen.update_analytics)




