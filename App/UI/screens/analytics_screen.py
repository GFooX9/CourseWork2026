import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame,
                             QLabel, QComboBox, QPushButton, QFileDialog, QMessageBox)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from App.Engine.analytics_engine import AnalyticsEngine


class AnalyticsScreen(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window  # Доступ к бэкенду/БД через главное окно
        self.analytics = AnalyticsEngine()
        self.setup_ui()
        self.setup_styles()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # Заголовок экрана
        title_label = QLabel("📊 АНАЛИТИКА И СТАТИСТИКА")
        title_label.setFont(QFont("Noto Sans Mono", 20, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # 1. ПАНЕЛЬ ФИЛЬТРА ДАТ
        filter_panel = QFrame()
        filter_panel.setObjectName("FilterPanel")
        filter_layout = QHBoxLayout(filter_panel)
        filter_layout.setContentsMargins(15, 10, 15, 10)

        lbl_period = QLabel("Период анализа:")
        lbl_period.setFont(QFont("Noto Sans Mono", 11, QFont.Weight.Bold))

        self.period_menu = QComboBox()
        self.period_menu.addItems(["Все время", "Сегодня", "За неделю"])
        self.period_menu.currentIndexChanged.connect(self.update_analytics)

        filter_layout.addWidget(lbl_period)
        filter_layout.addWidget(self.period_menu)
        filter_layout.addStretch()
        main_layout.addWidget(filter_panel)

        # 2. БЛОК KPI КАРТОЧЕК
        kpi_box = QWidget()
        kpi_layout = QHBoxLayout(kpi_box)
        kpi_layout.setContentsMargins(0, 0, 0, 0)
        kpi_layout.setSpacing(20)

        # Карточка "Всего протоколов"
        self.card_total = QFrame()
        self.card_total.setObjectName("KpiCard")
        total_layout = QVBoxLayout(self.card_total)
        lbl_t1 = QLabel("ВСЕГО ПРОТОКОЛОВ")
        lbl_t1.setFont(QFont("Noto Sans Mono", 10))
        lbl_t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.val_total = QLabel("0")
        self.val_total.setFont(QFont("Noto Sans Mono", 22, QFont.Weight.Bold))
        self.val_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        total_layout.addWidget(lbl_t1)
        total_layout.addWidget(self.val_total)

        # Карточка "Среднее количество объектов"
        self.card_avg = QFrame()
        self.card_avg.setObjectName("KpiCard")
        avg_layout = QVBoxLayout(self.card_avg)
        lbl_t2 = QLabel("СРЕДНЕЕ ОБЪЕКТОВ")
        lbl_t2.setFont(QFont("Noto Sans Mono", 10))
        lbl_t2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.val_avg = QLabel("0.0")
        self.val_avg.setFont(QFont("Noto Sans Mono", 22, QFont.Weight.Bold))
        self.val_avg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avg_layout.addWidget(lbl_t2)
        avg_layout.addWidget(self.val_avg)

        kpi_layout.addWidget(self.card_total, 1)
        kpi_layout.addWidget(self.card_avg, 1)
        main_layout.addWidget(kpi_box)

        # 3. КОНТЕЙНЕР ДЛЯ МАТПЛОТЛИБ ГРАФИКОВ
        self.charts_area = QFrame()
        self.charts_area.setObjectName("ChartsArea")
        self.charts_layout = QHBoxLayout(self.charts_area)
        self.charts_layout.setContentsMargins(15, 15, 15, 15)
        self.charts_layout.setSpacing(15)

        # Заглушка, если данных нет
        self.no_data_label = QLabel("Нет данных за выбранный период")
        self.no_data_label.setFont(QFont("Noto Sans Mono", 14))
        self.no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.charts_layout.addWidget(self.no_data_label)

        main_layout.addWidget(self.charts_area, 1)

        # 4. НИЖНЯЯ ПАНЕЛЬ С КНОПКАМИ
        controls_box = QWidget()
        controls_layout = QHBoxLayout(controls_box)
        controls_layout.setContentsMargins(0, 5, 0, 5)

        self.btn_refresh = QPushButton("ОБНОВИТЬ ДАННЫЕ")
        self.btn_refresh.setObjectName("RefreshBtn")
        self.btn_refresh.clicked.connect(self.update_analytics)

        self.btn_excel = QPushButton("СВОДНЫЙ EXCEL ОТЧЕТ")
        self.btn_excel.setObjectName("ExcelBtn")
        self.btn_excel.clicked.connect(self.export_excel)

        controls_layout.addWidget(self.btn_refresh, 1)
        controls_layout.addWidget(self.btn_excel, 1)
        main_layout.addWidget(controls_box)

    def setup_styles(self):
        """Интегрирует сиреневые (лавандовые) стили под текущую тему нашего чата."""
        style_qss = """
            QLabel { color: #DFE1E5; }

            QFrame#FilterPanel, QFrame#KpiCard {
                background-color: #2B2D31;
                border: 1px solid #3F424A;
                border-radius: 12px;
            }
            QFrame#ChartsArea {
                background-color: #2B2D31;
                border: 2px dashed #3F424A;
                border-radius: 20px;
            }

            QComboBox {
                background-color: #3F424A;
                color: white;
                border: 1px solid #4E515B;
                border-radius: 6px;
                padding: 3px 10px;
                min-width: 150px;
            }

            /* Кнопка Обновить */
            QPushButton#RefreshBtn {
                background-color: #3F424A;
                color: #DFE1E5;
                border-radius: 12px;
                font-family: 'Noto Sans Mono';
                font-weight: bold;
                min-height: 45px;
                border: none;
            }
            QPushButton#RefreshBtn:hover { background-color: #4E515B; border-color: #BB9AF7; }

            /* Кнопка Excel (Лавандовый акцент) */
            QPushButton#ExcelBtn {
                background-color: #7C3AED;
                color: white;
                border-radius: 12px;
                font-family: 'Noto Sans Mono';
                font-weight: bold;
                min-height: 45px;
                border: none;
            }
            QPushButton#ExcelBtn:hover { background-color: #BB9AF7; }

            /* ДИНАМИЧЕСКИЙ СБРОС НА СВЕТЛУЮ ТЕМУ */
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QLabel { color: #1F1F1F; }
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QFrame#FilterPanel,
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QFrame#KpiCard {
                background-color: #F0F2F5; border-color: #E4E6EB;
            }
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QFrame#ChartsArea {
                background-color: #F0F2F5; border-color: #E4E6EB;
            }
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QComboBox {
                background-color: white; color: #1F1F1F; border-color: #E4E6EB;
            }
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QPushButton#RefreshBtn {
                background-color: #E4E6EB; color: #1F1F1F;
            }
            QMainWindow[styleSheet*="background-color: #FFFFFF"] QPushButton#RefreshBtn:hover { background-color: #D8DADF; }
        """
        self.setStyleSheet(style_qss)

    def update_analytics(self):
        """Запрашивает отфильтрованные данные и перерисовывает KPI и графики."""
        # 1. Очищаем старые виджеты графиков из области
        while self.charts_layout.count():
            child = self.charts_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 2. Вытягиваем период и запрашиваем отфильтрованные данные через наш DatabaseManager
        period = self.period_menu.currentText()
        filtered_data = self.main_window.db.get_filtered_history(search_query=None, date_filter=period)

        # 3. Обновляем KPI
        metrics = self.analytics.get_kpi_metrics(data=filtered_data)
        self.val_total.setText(str(metrics["total"]))
        self.val_avg.setText(str(metrics["avg_objs"]))

        # 4. Если данных нет — выводим текстовую заглушку
        if not filtered_data:
            self.no_data_label = QLabel(f"За период '{period}' данных не найдено")
            self.no_data_label.setFont(QFont("Noto Sans Mono", 14))
            self.no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.charts_layout.addWidget(self.no_data_label)
            return

        # 5. Отрисовываем новые графики matplotlib через FigureCanvas в PyQt6
        import pandas as pd
        df = pd.DataFrame(filtered_data)

        # График Топ-5 объектов
        fig_top = self.analytics.create_top_objects_plot(data=df)
        if fig_top:
            # Настройка темы графика под стиль интерфейса
            if self.main_window.is_dark_theme:
                fig_top.patch.set_facecolor('#2B2D31')
                fig_top.gca().set_facecolor('#2B2D31')
                fig_top.gca().title.set_color('white')
                fig_top.gca().xaxis.label.set_color('white')
                fig_top.gca().yaxis.label.set_color('white')
                fig_top.gca().tick_params(colors='white')
            else:
                fig_top.patch.set_facecolor('#F0F2F5')
                fig_top.gca().set_facecolor('#F0F2F5')

            canvas_top = FigureCanvas(fig_top)
            self.charts_layout.addWidget(canvas_top, 1)

        # График Динамики исследований
        fig_act = self.analytics.create_activity_plot(data=df)
        if fig_act:
            if self.main_window.is_dark_theme:
                fig_act.patch.set_facecolor('#2B2D31')
                fig_act.gca().set_facecolor('#2B2D31')
                fig_act.gca().title.set_color('white')
                fig_act.gca().tick_params(colors='white')
            else:
                fig_act.patch.set_facecolor('#F0F2F5')
                fig_act.gca().set_facecolor('#F0F2F5')

            canvas_act = FigureCanvas(fig_act)
            self.charts_layout.addWidget(canvas_act, 1)

    def export_excel(self):
        """Вызывает диалог сохранения Excel отчета."""
        from datetime import datetime
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить сводный отчет",
            f"VisionPro_Report_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
            "Excel Files (*.xlsx)"
        )
        if file_path:
            if self.analytics.export_full_excel(file_path):
                QMessageBox.information(self, "Успех", f"Отчет успешно сохранен в:\n{file_path}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось выполнить экспорт в Excel.")
