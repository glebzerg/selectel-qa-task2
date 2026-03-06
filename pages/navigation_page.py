"""
pages/navigation_page.py — Page Object для проверки навигации и внутренних страниц.
"""

import requests
from pages.base_page import BasePage
from playwright.sync_api import Page


# Ключевые страницы сайта selectel.ru, которые должны быть доступны
IMPORTANT_PAGES = [
    ("/",                    "Главная страница"),
    ("/services/",           "Сервисы / продукты"),
    ("/about/",              "О компании"),
    ("/blog/",               "Блог"),
]

# Страницы, которые точно должны вернуть 404 (тест на корректную обработку)
NOT_FOUND_PAGES = [
    "/this-page-definitely-does-not-exist-12345",
    "/api/nonexistent-endpoint-xyz",
]


class NavigationPage(BasePage):
    """Page Object для проверки навигации, роутинга и доступности страниц."""

    # Локаторы
    MOBILE_MENU_BUTTON = "[class*='burger'], [class*='hamburger'], [aria-label*='меню'], button[class*='menu']"
    MOBILE_MENU_OPEN = "[class*='mobile-nav'], [class*='drawer'], [class*='menu-open']"
    BREADCRUMBS = "[class*='breadcrumb'], nav[aria-label*='breadcrumb']"
    BACK_TO_TOP = "[class*='back-to-top'], [class*='scroll-top']"

    def open_home(self) -> "NavigationPage":
        self.navigate("/")
        self.page.wait_for_load_state("domcontentloaded")
        return self

    def check_page_status(self, path: str) -> int:
        """
        Проверяет HTTP-статус страницы без браузера.
        Быстро и эффективно — браузер не нужен для проверки статуса.
        """
        url = f"{self.BASE_URL}{path}"
        try:
            r = requests.get(url, timeout=15, allow_redirects=True)
            return r.status_code
        except requests.RequestException:
            return 0

    def check_redirect(self, from_path: str) -> str:
        """Проверяет итоговый URL после редиректа."""
        url = f"{self.BASE_URL}{from_path}"
        r = requests.get(url, timeout=15, allow_redirects=True)
        return r.url

    def get_all_important_page_statuses(self) -> dict[str, int]:
        """Возвращает словарь {путь: HTTP-статус} для всех важных страниц."""
        return {
            path: self.check_page_status(path)
            for path, _ in IMPORTANT_PAGES
        }

    def navigate_to(self, path: str) -> None:
        """Навигация через браузер (для UI-проверок)."""
        self.navigate(path)
        self.page.wait_for_load_state("domcontentloaded")

    def is_404_page(self) -> bool:
        """Проверяет, показывает ли страница 404-контент."""
        title = self.page.title().lower()
        body = self.page.locator("body").inner_text().lower()
        return "404" in title or "не найден" in body or "not found" in body

    def open_mobile_menu(self) -> bool:
        """Открывает мобильное меню, если кнопка присутствует."""
        btn = self.page.locator(self.MOBILE_MENU_BUTTON)
        if btn.count() > 0 and btn.first.is_visible():
            btn.first.click()
            self.page.wait_for_timeout(500)
            return True
        return False

    def get_all_external_links(self) -> list[str]:
        """Все ссылки на внешние домены (не selectel.ru)."""
        links = self.page.locator("a[href^='http']").all()
        external = []
        for link in links:
            href = link.get_attribute("href") or ""
            if "selectel.ru" not in href:
                external.append(href)
        return external

    def external_links_open_in_new_tab(self) -> list[str]:
        """Внешние ссылки без target='_blank' (потенциальная UX-проблема)."""
        links = self.page.locator("a[href^='http']:not([href*='selectel.ru'])").all()
        bad_links = []
        for link in links:
            target = link.get_attribute("target") or ""
            if target != "_blank":
                href = link.get_attribute("href") or ""
                bad_links.append(href)
        return bad_links
