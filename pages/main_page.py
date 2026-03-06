"""
pages/main_page.py — Page Object главной страницы selectel.ru.

Инкапсулирует все локаторы и действия, специфичные для главной страницы.
Тесты работают ТОЛЬКО через этот класс, не через сырые селекторы.
"""

from playwright.sync_api import Page
from pages.base_page import BasePage


class MainPage(BasePage):
    """Page Object для https://selectel.ru/"""

    # ── Локаторы (селекторы) ──────────────────────────────────────────────────
    # Хранятся здесь — при изменении вёрстки правится только этот файл.

    # Шапка (header)
    HEADER = "header"
    LOGO = "header a[href='/'], header a[href='https://selectel.ru/']"
    NAV_LINKS = "header nav a, header [class*='nav'] a"
    SIGNIN_BUTTON = "a[href*='my.selectel.ru'], a[href*='login'], [class*='sign'], [class*='login']"

    # Главный экран (hero)
    HERO_SECTION = "main section:first-of-type, [class*='hero'], [class*='banner']"
    HERO_HEADING = "h1"

    # Продуктовый каталог / разделы
    PRODUCTS_SECTION = "[class*='product'], [class*='service'], [class*='catalog']"

    # Футер
    FOOTER = "footer"
    FOOTER_LINKS = "footer a"
    FOOTER_LOGO = "footer img[alt*='Selectel'], footer a[href='/']"

    # Мета / SEO
    META_DESCRIPTION = 'meta[name="description"]'
    OG_TITLE = 'meta[property="og:title"]'
    OG_IMAGE = 'meta[property="og:image"]'
    CANONICAL = 'link[rel="canonical"]'

    # Доступность
    LANG_ATTR = "html"

    # Чат / поддержка
    CHAT_WIDGET = "[class*='chat'], [id*='chat'], [class*='support']"

    # ── Действия ──────────────────────────────────────────────────────────────

    def open(self) -> "MainPage":
        """Открывает главную страницу и дожидается загрузки."""
        self.navigate("/")
        self.page.wait_for_load_state("domcontentloaded")
        return self

    def get_heading(self) -> str:
        """Возвращает текст главного заголовка H1."""
        h1 = self.page.locator(self.HERO_HEADING).first
        return h1.inner_text() if h1.is_visible() else ""

    def click_logo(self) -> None:
        """Клик по логотипу в шапке."""
        self.page.locator(self.LOGO).first.click()
        self.page.wait_for_load_state("domcontentloaded")

    def get_nav_link_count(self) -> int:
        """Количество ссылок в навигации шапки."""
        return self.page.locator(self.NAV_LINKS).count()

    def get_footer_link_count(self) -> int:
        """Количество ссылок в футере."""
        return self.page.locator(self.FOOTER_LINKS).count()

    def is_header_visible(self) -> bool:
        return self.page.locator(self.HEADER).is_visible()

    def is_footer_visible(self) -> bool:
        return self.page.locator(self.FOOTER).is_visible()

    def is_h1_visible(self) -> bool:
        return self.page.locator(self.HERO_HEADING).first.is_visible()

    def get_lang(self) -> str:
        """Возвращает значение атрибута lang тега <html>."""
        return self.page.locator(self.LANG_ATTR).get_attribute("lang") or ""

    def get_canonical_url(self) -> str:
        el = self.page.locator(self.CANONICAL)
        return el.get_attribute("href") or "" if el.count() > 0 else ""

    def has_favicon(self) -> bool:
        """Проверяет наличие favicon."""
        favicon = self.page.locator('link[rel*="icon"]')
        return favicon.count() > 0

    def get_all_images(self):
        """Возвращает все img-теги на странице."""
        return self.page.locator("img").all()

    def get_images_without_alt(self) -> int:
        """Считает картинки без атрибута alt (нарушение доступности)."""
        all_imgs = self.page.locator("img").count()
        imgs_with_alt = self.page.locator("img[alt]").count()
        return all_imgs - imgs_with_alt

    def get_broken_links_count(self) -> list[str]:
        """
        Собирает href всех ссылок на странице.
        Фактическая проверка доступности — в тестах через requests.
        """
        links = self.page.locator("a[href]").all()
        hrefs = []
        for link in links:
            href = link.get_attribute("href") or ""
            if href.startswith("http"):
                hrefs.append(href)
        return hrefs

    def has_no_horizontal_scroll(self) -> bool:
        """Проверяет отсутствие горизонтального скролла."""
        scroll_width = self.page.evaluate("document.documentElement.scrollWidth")
        client_width = self.page.evaluate("document.documentElement.clientWidth")
        return scroll_width <= client_width

    def get_console_errors(self) -> list[str]:
        """Возвращает список JS-ошибок из консоли браузера."""
        errors = []
        self.page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        return errors

    def is_page_secure(self) -> bool:
        """Проверяет, что страница загружена по HTTPS."""
        return self.page.url.startswith("https://")

    def get_response_code(self) -> int:
        """Получает HTTP-код ответа главной страницы."""
        import requests
        r = requests.get(self.BASE_URL, timeout=15, allow_redirects=True)
        return r.status_code

    def get_page_load_time_ms(self) -> float:
        """Возвращает время загрузки страницы в миллисекундах (Navigation Timing API)."""
        timing = self.page.evaluate("""() => {
            const t = window.performance.timing;
            return t.loadEventEnd - t.navigationStart;
        }""")
        return float(timing)
