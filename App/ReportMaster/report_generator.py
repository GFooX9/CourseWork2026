import os
import sys
import time
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.pdfgen import canvas
from reportlab.pdfbase import ttfonts, pdfmetrics
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Frame

from App.CFG.config import FONT_PATH, ICONS


class ReportGenerator:
    def __init__(self):
        # Регистрируем шрифт из централизованного конфига для поддержки кириллицы
        if os.path.exists(FONT_PATH):
            pdfmetrics.registerFont(ttfonts.TTFont('NotoSans', FONT_PATH))
        else:
            print(f"[ReportGenerator Warning] Шрифт не найден по пути: {FONT_PATH}")

    def export_pdf(self, file_path: str, data: dict) -> bool:
        """
        Генерирует финальный PDF-протокол исследования.
        file_path: путь, куда сохранить PDF (выбирается пользователем в UI)
        data: словарь с данными из конкретной записи БД
        """
        try:
            c = canvas.Canvas(file_path, pagesize=A4)
            width, height = A4

            # 1. ЗАГОЛОВОК ДОКУМЕНТА
            c.setFont("NotoSans", 22)
            c.drawCentredString(width / 2, 800, f"Протокол исследования № {data.get('protocol_num', '---')}")

            c.setFont("NotoSans", 12)
            c.drawCentredString(width / 2, 780, f"Дата: {data.get('date_str', '---')}")
            c.line(50, 765, 545, 765)

            # 2. ОТОБРАЖЕНИЕ КЭШИРОВАННОГО ИЗОБРАЖЕНИЯ
            img_path = data.get('result_file_path', '')
            if img_path and os.path.exists(img_path):
                # Отрисовываем картинку из папки ResultsImages
                c.drawImage(img_path, 57.5, 400, width=480, height=340)
                c.setFont("NotoSans", 14)
                c.drawString(60, 375, f"Исходный файл: {data.get('original_name', '---')}")
            else:
                c.setFont("NotoSans", 12)
                c.drawString(60, 550, "[ Изображение исследования не найдено ]")

            # 3. ПОДГОТОВКА И ВЕРСТКА ТЕКСТА
            styles = getSampleStyleSheet()
            custom_style = ParagraphStyle(
                'CustomStyle',
                fontName='NotoSans',
                fontSize=10,
                leading=14,
                alignment=0
            )

            def safe_text(text):
                """Безопасное экранирование спецсимволов для XML-парсера ReportLab."""
                if not text:
                    return "-"
                return escape(str(text)).replace('\n', '<br/>')

            obj_txt = safe_text(data.get('detected_objects', '-'))
            ocr_txt = safe_text(data.get('ocr_text', '-'))
            user_notes = safe_text(data.get('user_notes', '-'))

            # Формируем структуру документа с HTML-подобными тегами
            text_content = (
                f"<b>Обнаруженные объекты:</b> {obj_txt}<br/><br/>"
                f"<b>Распознанный текст (OCR):</b> {ocr_txt}<br/><br/>"
                f"<b>Заметки эксперта:</b> {user_notes}"
            )

            p = Paragraph(text_content, custom_style)
            f = Frame(60, 80, 480, 280, showBoundary=0)
            f.addFromList([p], c)

            # 4. НАЛОЖЕНИЕ ЦИФРОВОЙ ПЕЧАТИ / ВОДЯНОГО ЗНАКА
            try:
                # Берём путь к логотипу напрямую из конфига ICONS
                logo_path = ICONS.get("vision")
                if logo_path and os.path.exists(logo_path):
                    c.saveState()
                    c.setFillAlpha(0.15)  # Делаем водяной знак более прозрачным и аккуратным
                    c.drawImage(logo_path, 420, 40, width=100, height=100, mask='auto')
                    c.restoreState()

                    c.setFont("NotoSans", 8)
                    c.setFillGray(0.5)
                    c.drawRightString(530, 35, "Электронный протокол Vision Pro AI")
                else:
                    print(f"[ReportGenerator Warning] Файл логотипа не найден по пути: {logo_path}")
            except Exception as logo_err:
                print(f"[ReportGenerator Error] Ошибка добавления логотипа/печати: {logo_err}")

            c.save()
            return True

        except Exception as e:
            import traceback
            print(f"[ReportGenerator Critical Error] Ошибка генерации PDF:\n{traceback.format_exc()}")
            return False
