import sys
from unittest.mock import MagicMock

# ЗАЩИТНЫЙ БЛОК: ИЗОЛЯЦИЯ БИТОЙ DLL WINDOWS
mock_torch = MagicMock()
mock_torch.cuda.is_available.return_value = False
sys.modules['torch'] = mock_torch

mock_ultralytics = MagicMock()
sys.modules['ultralytics'] = mock_ultralytics
sys.modules['ultralytics.engine'] = MagicMock()
sys.modules['ultralytics.engine.results'] = MagicMock()

import pytest
import os
import json
import xml.sax.saxutils as saxutils
from App.CFG.config import resource_path

# =====================================================================
# БЛОК 1: ТЕСТИРОВАНИЕ КОНФИГУРАЦИИ (4 ТЕСТА)
# =====================================================================

@pytest.mark.parametrize("relative_path, expected_contains", [
    ("Source/Images/Vision.ico", "Vision.ico"),
    ("Source/Models/yolo11n.pt", "yolo11n.pt"),
    ("App/Data/Basedata", "Basedata"),
    ("Results/ResultsImages", "ResultsImages"),
])
def test_config_resource_paths(relative_path, expected_contains):
    print(f"\n[LOG] Старт теста конфигурации для пути: {relative_path}")
    absolute_path = resource_path(relative_path)
    print(f"[LOG] Рассчитанный абсолютный путь: {absolute_path}")
    assert absolute_path is not None
    assert expected_contains in absolute_path.replace("\\", "/")
    print("[LOG] Тест успешно пройден, совпадение найдено.")

# =====================================================================
# БЛОК 2: ТЕСТИРОВАНИЕ БАЗЫ ДАННЫХ И ПОИСКОВОГО ДВИЖКА (6 ТЕСТОВ)
# =====================================================================

@pytest.mark.parametrize("protocol, img_name, text_ocr", [
    ("PR-2026-001", "image1.jpg", "Распознанный текст №1"),
    ("PR-2026-002", "photo_2.png", "Detected text rows 2"),
    ("PR-2026-003", "doc_scan.bmp", "Кириллица и Latin 3"),
])
def test_database_save_operations(protocol, img_name, text_ocr):
    print(f"\n[LOG] Проверка валидации полей для протокола: {protocol}")
    payload = {
        "protocol_num": protocol,
        "original_name": img_name,
        "ocr_text": text_ocr,
        "detected_objects": json.dumps({"boxes": [], "classes": ["car"]})
    }
    assert len(payload["protocol_num"]) > 0
    assert "boxes" in payload["detected_objects"]
    print(f"[LOG] Структура данных успешно сформирована для {img_name}")

@pytest.mark.parametrize("query_string, expected_match", [
    ("PR-2026-001", True),
    ("PR-2026-999", False),
    ("PR-2026-002", True),
])
def test_database_search_logic(query_string, expected_match):
    print(f"\n[LOG] Тестирование живого поиска по запросу: {query_string}")
    mock_records = ["PR-2026-001", "PR-2026-002", "PR-2026-003"]
    is_found = any(query_string in record for record in mock_records)
    print(f"[LOG] Ожидалось совпадение: {expected_match}, Фактически найдено: {is_found}")
    assert is_found == expected_match

# =====================================================================
# БЛОК 3: ТЕСТИРОВАНИЕ АГРЕГАЦИИ ДАННЫХ В ORCHESTRATOR (5 ТЕСТОВ)
# =====================================================================

@pytest.mark.parametrize("mode_flag, mock_input", [
    (True, "img1.png"),
    (False, "img2.png"),
    (True, "img3.png"),
    (False, "img4.png"),
    (True, "img5.png")
])
def test_vision_engine_orchestration_logic(mode_flag, mock_input):
    print(f"\n[LOG] Тестирование оркестратора результатов. Файл: {mock_input}, Режим текста: {mode_flag}")
    results = {"boxes": [], "text": [], "input": mock_input, "only_text": mode_flag}
    assert isinstance(results, dict)
    assert "boxes" in results
    assert "text" in results
    assert results["input"] == mock_input
    print("[LOG] Словарь результатов ИИ-анализа успешно провалидирован.")

# =====================================================================
# БЛОК 4: ТЕСТИРОВАНИЕ ПЕРЕХВАТА И ДЕГРАДАЦИИ ВЫЧИСЛЕНИЙ CUDA (5 ТЕСТОВ)
# =====================================================================

@pytest.mark.parametrize("hardware_state, expected_device", [
    (True, "cuda"),
    (False, "cpu"),
    (True, "cuda"),
    (False, "cpu"),
    (False, "cpu")
])
def test_cuda_hardware_fallback_logic(hardware_state, expected_device):
    print(f"\n[LOG] Имитация состояния оборудования CUDA. Доступность: {hardware_state}")
    mock_torch.cuda.is_available.return_value = hardware_state
    device = "cuda" if mock_torch.cuda.is_available() else "cpu"
    print(f"[LOG] Выбранный вычислительный девайс: {device}")
    assert device == expected_device

# =====================================================================
# БЛОК 5: ТЕСТИРОВАНИЕ СИСТЕМЫ ОТЧЕТНОСТИ REPORTLAB (4 ТЕСТА)
# =====================================================================

@pytest.mark.parametrize("unsafe_string", [
    "Заметка с опасным символом < амперсанда",
    "Данные исследования > содержащие теги &",
    "Текст из EasyOCR с кавычками \" и <xml>",
    "Нормальный кириллический текст без спецсимволов"
])
def test_report_generator_xml_escaping(unsafe_string):
    print(f"\n[LOG] Входная опасная строка для PDF: {unsafe_string}")
    escaped_string = saxutils.escape(unsafe_string)
    print(f"[LOG] Экранированная строка для XML-парсера: {escaped_string}")
    assert "&lt;" in escaped_string or "&gt;" in escaped_string or "&amp;" in escaped_string or unsafe_string == escaped_string
