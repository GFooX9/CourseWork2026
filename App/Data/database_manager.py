import sqlite3
import os
from datetime import datetime
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
                # Позволяет читать строки как словари: row['protocol_num'] вместо row[1]
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM history ORDER BY id DESC")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"[DatabaseManager Error] Ошибка загрузки истории: {e}")
            return []

    def save_to_history(self, protocol_num, original_path, cached_img_path, objects_info, text_info, user_notes=""):
        """
        Записывает результаты нового исследования в базу данных.
        Принимает 'cached_img_path' — путь к уже скопированной в ResultsImages картинке.
        """
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

            # Возвращаем словарь данных, чтобы интерфейс мгновенно обновил таблицу без тяжелого перезапроса БД
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
