import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta
from App.CFG.config import DB_PATH

class DatabaseManager:
    def __init__(self):
        # Используем централизованный путь к БД из конфигурационного файла
        self.db_path = DB_PATH
        self._init_db()

    def _init_db(self):
        """Создает таблицу истории исследований, если она отсутствует."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    protocol_num TEXT,
                    date_str TEXT,
                    original_name TEXT,
                    result_file_path TEXT,
                    detected_objects TEXT,
                    ocr_text TEXT,
                    user_notes TEXT
                )
            ''')
            conn.commit()

    def load_history(self):
        """Возвращает все записи из базы данных в виде списка словарей для вывода в таблицу PyQt6."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM history ORDER BY id DESC")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"[DatabaseManager Error] Ошибка загрузки истории: {e}")
            return []

    def get_filtered_history(self, search_query: str = None, date_filter: str = "Все время") -> list:
        """
        Осуществляет поиск по номеру протокола и фильтрацию по датам.
        Интегрировано из старого модуля SearchEngine.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM history WHERE 1=1"
                params = []

                # Поиск по частичному совпадению номера протокола
                if search_query:
                    query += " AND protocol_num LIKE ?"
                    params.append(f"%{search_query}%")

                # Если фильтр по дате не дефолтный, фильтруем выборку с помощью Pandas
                if date_filter != "Все время":
                    today = datetime.now().date()
                    if date_filter == "Сегодня":
                        start_date = today
                    elif date_filter == "За неделю":
                        start_date = today - timedelta(days=7)
                    else:
                        start_date = None

                    if start_date:
                        df = pd.read_sql_query(query, conn, params=params)
                        # Парсим текстовую дату в объект даты для сравнения
                        df['dt_obj'] = pd.to_datetime(df['date_str'], dayfirst=True).dt.date
                        # Фильтруем, дропаем временную колонку и возвращаем список словарей
                        filtered_df = df[df['dt_obj'] >= start_date].drop(columns=['dt_obj'])
                        return filtered_df.to_dict('records')

                # Если фильтрация по дате «Все время», выполняем обычный быстрый SQL-запрос
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            print(f"[DatabaseManager Error] Ошибка фильтрации истории: {e}")
            return []

    def save_to_history(self, protocol_num, original_path, cached_img_path, objects_info, text_info, user_notes=""):
        """Записывает результаты нового исследования в базу данных."""
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        original_name = os.path.basename(original_path)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO history (
                        protocol_num, date_str, original_name, 
                        result_file_path, detected_objects, ocr_text, user_notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    protocol_num, now_str, original_name,
                    cached_img_path, objects_info, text_info, user_notes
                ))
                conn.commit()

            return {
                "protocol_num": protocol_num,
                "date_str": now_str,
                "original_name": original_name,
                "result_file_path": cached_img_path,
                "detected_objects": objects_info,
                "ocr_text": text_info,
                "user_notes": user_notes
            }
        except Exception as e:
            print(f"[DatabaseManager Error] Ошибка сохранения записи: {e}")
            return None

    def delete_record(self, record_id):
        """Удаляет одну запись из истории по её ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM history WHERE id = ?", (record_id,))
                conn.commit()
            return True
        except Exception as e:
            print(f"[DatabaseManager Error] Ошибка удаления записи {record_id}: {e}")
            return False

    def delete_all_history(self):
        """Полностью очищает таблицу истории исследований."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM history")
                conn.commit()
            return True
        except Exception as e:
            print(f"[DatabaseManager Error] Ошибка полной очистки БД: {e}")
            return False
