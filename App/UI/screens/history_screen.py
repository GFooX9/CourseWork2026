from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame,
                             QLabel, QLineEdit, QComboBox, QListWidget,
                             QListWidgetItem, QPushButton, QMessageBox)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from App.UI.components.protocol_dialog import ProtocolDialog


class HistoryScreen(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window  # Ссылка на главное окно для работы с базой данных
        self.setup_ui()
        self.setup_styles()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # 1. ПАНЕЛЬ ПОИСКА И ФИЛЬТРАЦИИ
        search_panel = QFrame()
        search_panel.setObjectName("SearchPanel")
        search_layout = QHBoxLayout(search_panel)
        search_layout.setContentsMargins(15, 10, 15, 10)
        search_layout.setSpacing(15)

        # Поле текстового поиска по номеру
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText(" Поиск по номеру протокола...")
        self.search_entry.setFont(QFont("Noto Sans Mono", 11))
        self.search_entry.textChanged.connect(self.apply_filters)  # Мгновенный поиск при вводе
        search_layout.addWidget(self.search_entry, 2)

        # Комбобокс выбора временного периода
        self.date_menu = QComboBox()
        self.date_menu.addItems(["Все время", "Сегодня", "За неделю"])
        self.date_menu.setFont(QFont("Noto Sans Mono", 11))
        self.date_menu.currentIndexChanged.connect(self.apply_filters)  # Поиск при смене даты
        search_layout.addWidget(self.date_menu, 1)

        main_layout.addWidget(search_panel)

        # 2. СПИСОК ПРОТОКОЛОВ (С кастомным скроллбаром и ховерами)
        self.history_list = QListWidget()
        self.history_list.setObjectName("HistoryList")
        self.history_list.setFont(QFont("Noto Sans Mono", 12))
        self.history_list.setSpacing(8)
        self.history_list.itemClicked.connect(self.open_protocol_details)
        main_layout.addWidget(self.history_list, 1)

        # 3. НИЖНЯЯ ПАНЕЛЬ КНОПОК УПРАВЛЕНИЯ
        bottom_panel = QHBoxLayout()
        bottom_panel.setSpacing(15)

        # Правка 2: Кнопка полной очистки (Оформлена в стиле кнопки ВЫЙТИ из хедера)
        self.btn_clear_all = QPushButton("ОЧИСТИТЬ ВСЮ ИСТОРИЮ")
        self.btn_clear_all.setObjectName("ClearAllBtn")
        self.btn_clear_all.setFont(QFont("Noto Sans Mono", 11, QFont.Weight.Bold))
        self.btn_clear_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear_all.clicked.connect(self.confirm_full_delete)
        self.btn_clear_all.setFixedHeight(45)

        # Правка 3: Новая кнопка принудительного обновления (Мягкий сиреневый цвет)
        self.btn_refresh = QPushButton("ОБНОВИТЬ ДАННЫЕ")
        self.btn_refresh.setObjectName("RefreshDataBtn")
        self.btn_refresh.setFont(QFont("Noto Sans Mono", 11, QFont.Weight.Bold))
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(lambda: self.refresh_ui())
        self.btn_refresh.setFixedHeight(45)

        bottom_panel.addWidget(self.btn_clear_all, 1)
        bottom_panel.addWidget(self.btn_refresh, 1)
        main_layout.addLayout(bottom_panel)

    def setup_styles(self):
        """Задает лавандово-графитовое оформление экрана истории."""
        style_qss = """
        QFrame#SearchPanel {
            background-color: #2B2D31;
            border: 1px solid #3F424A;
            border-radius: 12px;
        }
        QLineEdit {
            background-color: #3F424A;
            color: white;
            border: 1px solid #4E515B;
            border-radius: 8px;
            padding: 5px 10px;
            min-height: 25px;
        }
        QLineEdit:focus { border-color: #BB9AF7; }

        QComboBox {
            background-color: #3F424A;
            color: white;
            border: 1px solid #4E515B;
            border-radius: 8px;
            padding: 5px 10px;
        }
        QComboBox:hover { border-color: #BB9AF7; }

        QListWidget#HistoryList {
            background-color: #131416;
            border: none;
            padding: 5px;
        }
        QListWidget#HistoryList::item {
            background-color: #1C1D20;
            color: #DFE1E5;
            border: 1px solid #2A2B30;
            border-radius: 12px;
            margin-bottom: 8px;
            padding: 15px;
        }
        QListWidget#HistoryList::item:hover {
            background-color: #222327;
            border: 1px dashed #BB9AF7;
            color: #FFFFFF;
        }
        QListWidget#HistoryList::item:selected {
            background-color: #1C1D20;
            color: #BB9AF7;
            border: 1px solid #7C3AED;
        }

        /* Скроллбар (Мягкий сиреневый с серым фоном) */
        QListWidget#HistoryList QScrollBar:vertical {
            border: none;
            background-color: #2B2D31;
            width: 12px;
            margin: 0px;
            border-radius: 6px;
        }
        QListWidget#HistoryList QScrollBar::handle:vertical {
            background-color: #BB9AF7;
            min-height: 30px;
            border-radius: 6px;
        }
        QListWidget#HistoryList QScrollBar::handle:vertical:hover {
            background-color: #9D62FF;
        }
        QListWidget#HistoryList QScrollBar::sub-line:vertical, 
        QListWidget#HistoryList QScrollBar::add-line:vertical {
            border: none; background: none; height: 0px;
        }
        QListWidget#HistoryList QScrollBar::add-page:vertical, 
        QListWidget#HistoryList QScrollBar::sub-page:vertical {
            background: none;
        }

        /* Кнопка "ОЧИСТИТЬ ВСЮ ИСТОРИЮ" (Стиль хедера ВЫЙТИ) */
        QPushButton#ClearAllBtn {
            background-color: rgba(198, 40, 40, 0.15);
            color: #FF8A80;
            border-radius: 12px;
            border: 1px solid rgba(239, 83, 80, 0.3);
        }
        QPushButton#ClearAllBtn:hover { 
            background-color: rgba(198, 40, 40, 0.35); 
            border-color: #FF5252; 
            color: white; 
        }

        /* Кнопка "ОБНОВИТЬ ДАННЫЕ" (Твой кастомный сиреневый стиль #808aff) */
        QPushButton#RefreshDataBtn {
            background-color: rgba(128, 138, 255, 0.12);
            color: #808aff;
            border: 1px solid rgba(128, 138, 255, 0.35);
            border-radius: 12px;
        }
        QPushButton#RefreshDataBtn:hover {
            background-color: rgba(128, 138, 255, 0.25);
            border-color: #808aff;
            color: #FFFFFF;
        }
        QPushButton#RefreshDataBtn:pressed {
            background-color: rgba(128, 138, 255, 0.45);
            border-color: #808aff;
            color: #FFFFFF;
        }

        /* === ДИНАМИЧЕСКИЙ СБРОС НА СВЕТЛУЮ ТЕМУ === */
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QFrame#SearchPanel {
            background-color: #F0F2F5; border-color: #E4E6EB;
        }
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QLineEdit {
            background-color: white; color: #1F1F1F; border-color: #E4E6EB;
        }
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QLineEdit:focus { border-color: #7C3AED; }
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QComboBox {
            background-color: white; color: #1F1F1F; border-color: #E4E6EB;
        }
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QListWidget#HistoryList {
            background-color: #F8F9FA; border: none;
        }
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QListWidget#HistoryList::item {
            background-color: white; color: #1F1F1F; border-color: #E4E6EB;
        }
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QListWidget#HistoryList::item:hover {
            background-color: #F0F2F5; border-color: #7C3AED; border-style: dashed; color: #1F1F1F;
        }
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QListWidget#HistoryList::item:selected {
            background-color: white; color: #7C3AED; border: 1px solid #7C3AED;
        }
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QListWidget#HistoryList QScrollBar:vertical {
            background-color: #E4E6EB;
        }
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QListWidget#HistoryList QScrollBar::handle:vertical {
            background-color: #7C3AED;
        }
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QPushButton#ClearAllBtn {
            background-color: #FFEBEB; color: #FF4C4C; border-color: #FFCCCC;
        }
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QPushButton#ClearAllBtn:hover {
            background-color: #FF4C4C; color: white;
        }

        /* Исправление для светлой темы кнопки Обновить данные — убираем белый фон */
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QPushButton#RefreshDataBtn {
            background-color: rgba(128, 138, 255, 0.1);
            color: #808aff;
            border: 1px solid rgba(128, 138, 255, 0.4);
        }
        QMainWindow[styleSheet*="background-color: #FFFFFF"] QPushButton#RefreshDataBtn:hover {
            background-color: #808aff;
            color: white;
        }
        """
        self.setStyleSheet(style_qss)

    def refresh_ui(self, records_data=None):
        """Очищает список на экране и заново наполняет его актуальными карточками."""
        self.history_list.clear()
        display_data = records_data if records_data is not None else self.main_window.db.load_history()

        if not display_data:
            item = QListWidgetItem("Ничего не найдено")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_list.addItem(item)
            return

        for item_data in display_data:
            text_line = (f" 📋  Протокол № {item_data.get('protocol_num', '?')}   │  "
                         f" 🕒  {item_data.get('date_str', '')}   │  "
                         f" 📄  Файл: {item_data.get('original_name', '')}")

            list_item = QListWidgetItem(text_line)
            list_item.setData(Qt.ItemDataRole.UserRole, item_data)
            self.history_list.addItem(list_item)

    def apply_filters(self):
        """Собирает значения фильтров поиска и дат, запрашивает данные из БД и обновляет UI."""
        query = self.search_entry.text().strip()
        date_filter = self.date_menu.currentText()
        filtered_data = self.main_window.db.get_filtered_history(search_query=query, date_filter=date_filter)
        self.refresh_ui(records_data=filtered_data)

    def open_protocol_details(self, item):
        """Срабатывает при клике на элемент списка истории."""
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        dialog = ProtocolDialog(data, self.main_window, self)
        dialog.exec()

    def confirm_full_delete(self):
        """Окно подтверждения полной очистки базы данных."""
        reply = QMessageBox.question(
            self, "ВНИМАНИЕ",
            "Вы уверены, что хотите полностью очистить историю?\nЭто действие нельзя отменить!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.main_window.db.delete_all_history():
                self.refresh_ui()
                QMessageBox.information(self, "Успех", "Вся история успешно удалена.")
