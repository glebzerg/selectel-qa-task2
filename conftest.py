"""
conftest.py — глобальные фикстуры для всех тестов.

Здесь определяются:
- настройки браузера (Playwright)
- Page Object фикстуры
- общие тестовые данные
"""

import pytest
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from pages.main_page import MainPage
from pages.navigation_page import NavigationPage
from utils.helpers import get_base_url


# ─── Playwright fixtures ──────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def browser_instance():
    """Запускает браузер один раз на всю тестовую сессию."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser_instance: Browser):
    """Создаёт новый изолированный контекст браузера для каждого теста."""
    ctx = browser_instance.new_context(
        viewport={"width": 1440, "height": 900},
        locale="ru-RU",
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    )
    yield ctx
    ctx.close()


@pytest.fixture(scope="function")
def mobile_context(browser_instance: Browser):
    """Контекст с эмуляцией мобильного устройства (iPhone 14)."""
    ctx = browser_instance.new_context(
        viewport={"width": 390, "height": 844},
        device_scale_factor=3,
        is_mobile=True,
        has_touch=True,
        locale="ru-RU",
        user_agent=(
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
            "Mobile/15E148 Safari/604.1"
        ),
    )
    yield ctx
    ctx.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Page:
    """Открывает новую вкладку в десктопном контексте."""
    p = context.new_page()
    yield p
    p.close()


@pytest.fixture(scope="function")
def mobile_page(mobile_context: BrowserContext) -> Page:
    """Открывает новую вкладку в мобильном контексте."""
    p = mobile_context.new_page()
    yield p
    p.close()


# ─── Page Object фикстуры ─────────────────────────────────────────────────────

@pytest.fixture
def main_page(page: Page) -> MainPage:
    """Page Object главной страницы selectel.ru."""
    return MainPage(page)


@pytest.fixture
def navigation_page(page: Page) -> NavigationPage:
    """Page Object навигации сайта."""
    return NavigationPage(page)


@pytest.fixture
def mobile_main_page(mobile_page: Page) -> MainPage:
    """Page Object главной страницы в мобильном контексте."""
    return MainPage(mobile_page)


# ─── Общие данные ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def base_url() -> str:
    return get_base_url()
