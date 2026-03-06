"""
pages/base_page.py — базовый Page Object.

Все Page Object-классы наследуются от BasePage.
Здесь собраны общие методы: навигация, ожидания, скриншоты.
"""

from playwright.sync_api import Page, Locator, expect
from utils.helpers import get_base_url


class BasePage:
    """Базовый класс для всех Page Object."""

    BASE_URL = get_base_url()

    def __init__(self, page: Page) -> None:
        self.page = page

    # ── Навигация ──────────────────────────────────────────────────────────────

    def navigate(self, path: str = "") -> None:
        """Переход по URL относительно BASE_URL."""
        url = f"{self.BASE_URL}{path}"
        self.page.goto(url, wait_until="domcontentloaded", timeout=30_000)

    def get_title(self) -> str:
        return self.page.title()

    def get_url(self) -> str:
        return self.page.url

    # ── Ожидания и состояния ──────────────────────────────────────────────────

    def wait_for_selector(self, selector: str, timeout: int = 10_000) -> Locator:
        return self.page.wait_for_selector(selector, timeout=timeout)

    def is_visible(self, selector: str) -> bool:
        return self.page.locator(selector).is_visible()

    # ── HTTP-статус ───────────────────────────────────────────────────────────

    def get_response_status(self, path: str = "") -> int:
        """Проверяет HTTP-статус страницы через requests (без браузера)."""
        import requests
        url = f"{self.BASE_URL}{path}"
        r = requests.get(url, timeout=15, allow_redirects=True)
        return r.status_code

    # ── Утилиты ───────────────────────────────────────────────────────────────

    def take_screenshot(self, name: str) -> bytes:
        return self.page.screenshot(path=f"reports/screenshots/{name}.png", full_page=True)

    def get_meta_content(self, name: str) -> str:
        """Возвращает содержимое мета-тега по атрибуту name."""
        locator = self.page.locator(f'meta[name="{name}"]')
        return locator.get_attribute("content") or ""

    def get_og_content(self, prop: str) -> str:
        """Возвращает содержимое Open Graph мета-тега."""
        locator = self.page.locator(f'meta[property="og:{prop}"]')
        return locator.get_attribute("content") or ""

    def has_https(self) -> bool:
        return self.page.url.startswith("https://")

    def count_elements(self, selector: str) -> int:
        return self.page.locator(selector).count()

    def get_text(self, selector: str) -> str:
        return self.page.locator(selector).inner_text()
