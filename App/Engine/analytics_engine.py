import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from collections import Counter
from App.CFG.config import DB_PATH


class AnalyticsEngine:
    def __init__(self):
        # Используем централизованный путь к БД из конфигурационного файла
        self.db_path = DB_PATH

    def get_data(self) -> pd.DataFrame:
        """Загружает необходимые данные из БД в Pandas DataFrame."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT date_str, detected_objects FROM history"
                return pd.read_sql_query(query, conn)
        except Exception as e:
            print(f"[AnalyticsEngine Error] Ошибка чтения данных для анализа: {e}")
            return pd.DataFrame(columns=['date_str', 'detected_objects'])

    def create_top_objects_plot(self, data: pd.DataFrame = None) -> Figure:
        """
        Формирует столбчатую диаграмму Топ-5 объектов.
        Возвращает чистый объект Figure, готовый для отрисовки в PyQt6.
        """
        df = data if data is not None else self.get_data()
        if df.empty:
            return None

        all_objects = []
        # Парсим строку объектов (разбиваем по запятой, убираем пробелы)
        for row in df['detected_objects']:
            if row and row != "Не определены":
                objs = [obj.strip() for obj in row.split(',')]
                all_objects.extend(objs)

        counts = Counter(all_objects).most_common(5)
        if not counts:
            return None

        names, values = zip(*counts)

        # Создаем чистую фигуру matplotlib без привязки к UI-библиотекам
        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)

        ax.bar(names, values, color='#4CAF50')
        ax.set_title("Топ-5 объектов", fontsize=12, pad=10)
        ax.set_ylabel("Количество")

        # Разворачиваем подписи для читаемости
        for tick in ax.get_xticklabels():
            tick.set_rotation(15)

        fig.tight_layout()
        return fig

    def get_kpi_metrics(self, data: pd.DataFrame = None) -> dict:
        """Возвращает общее число исследований и среднее количество объектов."""
        df = data if data is not None else self.get_data()
        if df.empty:
            return {"total": 0, "avg_objs": 0}

        total_prots = len(df)

        # Считаем количество объектов в каждой строке
        df['obj_count'] = df['detected_objects'].apply(
            lambda x: len(x.split(',')) if x and x != "Не определены" else 0
        )

        avg_objs = round(df['obj_count'].mean(), 1)
        return {"total": total_prots, "avg_objs": avg_objs}

    def create_activity_plot(self, data: pd.DataFrame = None) -> Figure:
        """
        Формирует линейный график динамики исследований.
        Возвращает чистый объект Figure для отображения в PyQt6.
        """
        df = data if data is not None else self.get_data()
        if df.empty:
            return None

        try:
            # Конвертируем даты (берем только день)
            df['date'] = pd.to_datetime(df['date_str'], dayfirst=True).dt.date
            activity = df.groupby('date').size()

            # Создаем чистую фигуру
            fig = Figure(figsize=(4, 3), dpi=100)
            ax = fig.add_subplot(111)

            activity.plot(kind='line', marker='o', color='#2196F3', linewidth=2, ax=ax)

            ax.set_title("Динамика исследований", fontsize=10, fontweight='bold')
            ax.grid(True, linestyle='--', alpha=0.6)

            for tick in ax.get_xticklabels():
                tick.set_rotation(45)

            fig.tight_layout()
            return fig
        except Exception as e:
            print(f"[AnalyticsEngine Error] Ошибка построения графика динамики: {e}")
            return None

    def export_full_excel(self, file_path: str) -> bool:
        """Экспортирует все записи из базы данных в Excel-файл."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("SELECT * FROM history", conn)
                df.to_excel(file_path, index=False)
                return True
        except Exception as e:
            print(f"[AnalyticsEngine Error] Ошибка экспорта в Excel: {e}")
            return False
