"""
utils/helpers.py — вспомогательные функции и константы.
"""

import os
import time
import requests
from pathlib import Path


BASE_URL = os.getenv("SELECTEL_BASE_URL", "https://selectel.ru")

# Допустимое время загрузки страницы (мс)
MAX_LOAD_TIME_MS = 5000

# Допустимые HTTP-коды для «живых» страниц
ACCEPTABLE_STATUS_CODES = {200, 301, 302}


def get_base_url() -> str:
    """Возвращает базовый URL из переменной окружения или дефолтное значение."""
    return BASE_URL.rstrip("/")


def check_url_status(url: str, timeout: int = 15) -> int:
    """
    Выполняет GET-запрос и возвращает HTTP-статус.
    Возвращает 0 при сетевой ошибке.
    """
    try:
        r = requests.get(url, timeout=timeout, allow_redirects=True)
        return r.status_code
    except requests.RequestException:
        return 0


def check_response_time(url: str, timeout: int = 15) -> float:
    """Возвращает время ответа сервера в миллисекундах."""
    try:
        start = time.time()
        requests.get(url, timeout=timeout, allow_redirects=True)
        return (time.time() - start) * 1000
    except requests.RequestException:
        return float("inf")


def get_response_headers(url: str) -> dict:
    """Возвращает заголовки HTTP-ответа."""
    try:
        r = requests.get(url, timeout=15, allow_redirects=True)
        return dict(r.headers)
    except requests.RequestException:
        return {}


def ensure_reports_dir() -> None:
    """Создаёт папку reports/screenshots если её нет."""
    Path("reports/screenshots").mkdir(parents=True, exist_ok=True)


def format_ms(ms: float) -> str:
    """Форматирует миллисекунды в читаемую строку."""
    if ms < 1000:
        return f"{ms:.0f}ms"
    return f"{ms/1000:.2f}s"
