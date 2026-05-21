import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics, ttfonts
from xml.sax.saxutils import escape
from App.CFG.config import FONT_PATH, ICONS


class ReportGenerator:
    def __init__(self):
        """Инициализирует генератор PDF отчетов и регистрирует русский шрифт."""
        self.font_name = "NotoSans"

        if os.path.exists(FONT_PATH):
            try:
                pdfmetrics.registerFont(ttfonts.TTFont(self.font_name, FONT_PATH))
            except Exception as e:
                print(f"[ReportGenerator Warning] Не удалось зарегистрировать шрифт: {e}")
                self.font_name = "Helvetica"
        else:
            print(f"[ReportGenerator Warning] Шрифт не найден по пути: {FONT_PATH}")
            self.font_name = "Helvetica"

    def _draw_footer_only(self, canvas, doc):
        """Фоновый метод: рисует двухстрочный подвал с аккуратной разделительной линией."""
        canvas.saveState()

        # Настройка серого цвета для линий и текста
        canvas.setStrokeColorRGB(0.8, 0.8, 0.8)  # Очень мягкий серый цвет для линии
        canvas.setFillColorRGB(0.5, 0.5, 0.5)  # Цвет текста подвала

        # 1. Рисуем тонкую горизонтальную линию над текстом подвала
        # Координаты: от левого поля (X=50) до правого поля (X=545) на высоте Y=55
        canvas.setLineWidth(0.5)
        canvas.line(50, 55, 545, 55)

        # 2. Выводим служебный текст в подвале строго в 2 строки
        canvas.setFont(self.font_name, 8)
        canvas.drawRightString(545, 40, "Электронный протокол системы ИИ")
        canvas.drawRightString(545, 28, "Программный комплекс Vision Pro AI")

        canvas.restoreState()

    def export_pdf(self, file_path: str, data: dict) -> bool:
        """
        Генерирует динамический многостраничный PDF-протокол исследования.
        Печать вынесена в поток и размещена в правом верхнем углу шапки без наложений.
        """
        if not file_path:
            return False

        try:
            # ЖЕСТКИЙ ФИКС ОТСТУПОВ: Увеличиваем bottomMargin до 70,
            # чтобы текст гарантированно переносился на новую страницу и не налезал на подвал!
            doc = SimpleDocTemplate(
                file_path,
                pagesize=A4,
                rightMargin=50, leftMargin=50,
                topMargin=40, bottomMargin=70
            )

            story = []
            styles = getSampleStyleSheet()

            # --- НАСТРОЙКА КИРИЛЛИЧЕСКИХ СТИЛЕЙ С ПОДДЕРЖКОЙ NOTOSANS ---
            title_style = ParagraphStyle(
                'PDFTitle',
                parent=styles['Heading1'],
                fontName=self.font_name,
                fontSize=20,
                leading=24,
                alignment=0,  # Выравнивание по ЛЕВОМУ краю, чтобы справа встала печать
                spaceAfter=6
            )

            meta_style = ParagraphStyle(
                'PDFMeta',
                parent=styles['Normal'],
                fontName=self.font_name,
                fontSize=11,
                leading=14,
                alignment=0,  # По левому краю
                textColor='gray'
            )

            h2_style = ParagraphStyle(
                'PDFH2',
                parent=styles['Heading2'],
                fontName=self.font_name,
                fontSize=13,
                leading=16,
                spaceBefore=14,
                spaceAfter=6,
                textColor='#7C3AED'
            )

            body_style = ParagraphStyle(
                'PDFBody',
                parent=styles['BodyText'],
                fontName=self.font_name,
                fontSize=10,
                leading=15,
                textColor='#2B2D31',
                spaceAfter=8
            )

            def safe_html_text(text):
                if not text:
                    return "-"
                return escape(str(text)).replace('\n', '<br/>')

            # --- 1. СТРОИМ СТИЛЬНУЮ ШАПКУ (Таблица: Слева Текст, Справа Печать) ---
            p_num = data.get('protocol_num', '---')
            date_str = data.get('date_str', '---')

            header_elements = [
                Paragraph(f"Протокол исследования № {p_num}", title_style),
                Paragraph(f"Дата формирования: {date_str}", meta_style)
            ]

            # Подготавливаем печать (УВЕЛИЧИЛИ РАЗМЕР с 50 до 65 пикселей)
            logo_path = ICONS.get("vision")
            if logo_path and os.path.exists(logo_path):
                header_img = Image(logo_path, width=65, height=65)
                header_img.hAlign = 'RIGHT'
            else:
                header_img = Paragraph("", body_style)

            # ПРАВКА СДВИГА: Расширили колонки [430, 65], чтобы печать встала крупнее и правее
            # В сумме 495 пунктов — это идеальная максимальная ширина печатной зоны листа A4
            header_table = Table([[header_elements, header_img]], colWidths=[430, 65])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))

            story.append(header_table)
            story.append(Spacer(1, 15))  # Отступ после шапки

            # --- 2. ИЗОБРАЖЕНИЕ ИССЛЕДОВАНИЯ ---
            img_path = data.get('result_file_path', '')
            if img_path and os.path.exists(img_path):
                try:
                    report_img = Image(img_path, width=450, height=320)
                    report_img.hAlign = 'CENTER'
                    story.append(report_img)
                    story.append(Spacer(1, 8))

                    orig_name = data.get('original_name', '---')
                    # Делаем подпись по центру под картинкой
                    center_meta = ParagraphStyle('PDFCenterMeta', parent=meta_style, alignment=1, spaceAfter=15)
                    story.append(Paragraph(f"Исходный файл: {orig_name}", center_meta))
                except Exception as img_err:
                    print(f"[ReportGenerator Error] Ошибка вставки картинки: {img_err}")
                    story.append(Paragraph("[ Ошибка отрисовки изображения исследования ]", body_style))
            else:
                story.append(Paragraph("[ Изображение исследования не найдено в ResultsImages ]", body_style))
                story.append(Spacer(1, 15))

            # --- 3. ДИНАМИЧЕСКИЕ ТЕКСТОВЫЕ БЛОКИ (ТЕПЕРЬ СВОБОДНО ПЕРЕНОСЯТСЯ) ---

            # Секция: Заметки эксперта
            story.append(Paragraph("Заметки эксперта:", h2_style))
            user_notes = safe_html_text(data.get('user_notes', '-'))
            story.append(Paragraph(user_notes, body_style))

            # Секция: Обнаруженные объекты
            story.append(Paragraph("Обнаруженные объекты:", h2_style))
            obj_txt = safe_html_text(data.get('detected_objects', '-'))
            story.append(Paragraph(obj_txt, body_style))

            # Секция: Распознанный текст (OCR)
            story.append(Paragraph("Распознанный текст (OCR):", h2_style))
            ocr_txt = safe_html_text(data.get('ocr_text', '-'))
            story.append(Paragraph(ocr_txt, body_style))

            # --- СБОРКА ДОКУМЕНТА С НАЛОЖЕНИЕМ ТОЛЬКО ПОДВАЛА ---
            doc.build(
                story,
                onFirstPage=self._draw_footer_only,
                onLaterPages=self._draw_footer_only
            )

            print(f"[ReportGenerator] PDF протокол успешно сгенерирован: {file_path}")
            return True

        except Exception as e:
            import traceback
            print(f"[ReportGenerator Critical Error] Ошибка генерации PDF:\n{traceback.format_exc()}")
            return False
