"""
tests/test_navigation.py
========================
Тесты навигации, роутинга и доступности страниц selectel.ru.

Покрываемые области:
  - HTTP-статусы ключевых страниц
  - Обработка 404
  - Редиректы
  - Внешние ссылки
  - Мобильное меню
"""

import pytest
import requests
from pages.navigation_page import NavigationPage, IMPORTANT_PAGES, NOT_FOUND_PAGES
from utils.helpers import get_base_url

BASE_URL = get_base_url()


# ═══════════════════════════════════════════════════════════════════════════════
# Доступность ключевых страниц
# ═══════════════════════════════════════════════════════════════════════════════

class TestKeyPagesAvailability:
    """Проверяем, что все важные страницы сайта доступны."""

    @pytest.mark.smoke
    @pytest.mark.api
    @pytest.mark.parametrize("path,description", IMPORTANT_PAGES)
    def test_important_page_is_accessible(self, path: str, description: str):
        """
        Каждая ключевая страница должна отвечать с кодом 200 или допустимым редиректом.

        Бизнес-смысл: недоступность любой из этих страниц — прямые потери
        клиентов, так как они не могут узнать о продуктах или оформить заказ.
        """
        url = f"{BASE_URL}{path}"
        response = requests.get(url, timeout=15, allow_redirects=True)

        assert response.status_code in (200, 301, 302), (
            f"Страница '{description}' ({url}) вернула код {response.status_code}. "
            f"Итоговый URL: {response.url}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Обработка 404
# ═══════════════════════════════════════════════════════════════════════════════

class TestNotFoundHandling:
    """Проверяем корректную обработку несуществующих страниц."""

    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.parametrize("path", NOT_FOUND_PAGES)
    def test_nonexistent_page_returns_404(self, path: str):
        """
        Несуществующие URL должны возвращать HTTP 404.

        Бизнес-смысл: возврат 200 для несуществующих страниц (soft 404)
        сбивает с толку поисковых роботов и вредит SEO.
        Возврат 500 говорит о проблемах на сервере.
        """
        url = f"{BASE_URL}{path}"
        response = requests.get(url, timeout=15, allow_redirects=True)

        assert response.status_code == 404, (
            f"Страница {url} вернула {response.status_code} вместо ожидаемого 404."
        )

    @pytest.mark.regression
    @pytest.mark.ui
    def test_404_page_has_helpful_content(self, navigation_page):
        """
        Страница 404 должна содержать понятный пользователю контент,
        а не техническую ошибку.

        Бизнес-смысл: хорошая 404-страница удерживает пользователя на сайте —
        предлагает поиск или навигацию вместо тупика.
        """
        navigation_page.navigate_to("/this-page-definitely-does-not-exist-xyz")

        body_text = navigation_page.page.locator("body").inner_text().lower()

        # На странице должно быть что-то понятное о ненайденном контенте
        has_404_content = any(
            keyword in body_text
            for keyword in ["404", "не найден", "not found", "страница не существует",
                            "вернуться", "на главную"]
        )
        assert has_404_content, (
            "Страница 404 не содержит полезного контента для пользователя. "
            "Добавьте понятное сообщение и ссылку на главную страницу."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Редиректы
# ═══════════════════════════════════════════════════════════════════════════════

class TestRedirects:
    """Проверяем корректность редиректов."""

    @pytest.mark.regression
    @pytest.mark.api
    def test_www_redirects_to_non_www(self):
        """
        www.selectel.ru должен редиректить на selectel.ru (или наоборот — главное, консистентность).

        Бизнес-смысл: оба варианта URL не должны индексироваться отдельно —
        это дублирование контента и размывание ссылочного веса.
        """
        www_url = "https://www.selectel.ru"
        response = requests.get(www_url, timeout=15, allow_redirects=True)

        # Финальный URL не должен содержать www
        assert "www.selectel.ru" not in response.url or response.url == www_url, (
            f"www-версия не редиректит корректно. Итоговый URL: {response.url}"
        )
        assert response.status_code == 200, (
            f"После редиректа с www получен код {response.status_code}"
        )

    @pytest.mark.regression
    @pytest.mark.api
    def test_trailing_slash_consistency(self):
        """
        URL со слешом и без должны приводить к одному результату.

        Бизнес-смысл: /about и /about/ — разные URL для поисковиков,
        если оба отдают 200 без canonical.
        """
        url_with_slash = f"{BASE_URL}/about/"
        url_without_slash = f"{BASE_URL}/about"

        r1 = requests.get(url_with_slash, timeout=15, allow_redirects=True)
        r2 = requests.get(url_without_slash, timeout=15, allow_redirects=True)

        # Оба должны быть доступны (200) или один редиректит на другой
        assert r1.status_code in (200, 301, 302), (
            f"URL {url_with_slash} вернул {r1.status_code}"
        )
        assert r2.status_code in (200, 301, 302), (
            f"URL {url_without_slash} вернул {r2.status_code}"
        )

        # Итоговые URL должны совпадать (оба ведут к одному canonical)
        assert r1.url == r2.url, (
            f"URL со слешом ({r1.url}) и без ({r2.url}) ведут к разным страницам. "
            f"Это создаёт дублирование контента."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Внешние ссылки и безопасность
# ═══════════════════════════════════════════════════════════════════════════════

class TestExternalLinks:
    """Проверяем корректность работы со внешними ссылками."""

    @pytest.mark.regression
    @pytest.mark.ui
    def test_external_links_have_target_blank(self, navigation_page):
        """
        Внешние ссылки должны открываться в новой вкладке (target='_blank').

        Бизнес-смысл: без target='_blank' пользователь уходит с сайта,
        теряя контекст. Увеличивает bounce rate.
        """
        navigation_page.open_home()
        bad_links = navigation_page.external_links_open_in_new_tab()

        # Допускаем небольшое количество исключений (например, для документов)
        assert len(bad_links) <= 3, (
            f"Найдено {len(bad_links)} внешних ссылок без target='_blank': "
            f"{bad_links[:5]}"
        )

    @pytest.mark.regression
    @pytest.mark.api
    def test_robots_txt_accessible(self):
        """
        Файл robots.txt должен быть доступен.

        Бизнес-смысл: robots.txt управляет индексацией сайта.
        Недоступный robots.txt — поисковики могут проиндексировать
        служебные страницы или, наоборот, не проиндексировать нужные.
        """
        url = f"{BASE_URL}/robots.txt"
        response = requests.get(url, timeout=15)
        assert response.status_code == 200, (
            f"robots.txt недоступен: {response.status_code}"
        )
        assert len(response.text) > 0, "robots.txt пустой."

    @pytest.mark.regression
    @pytest.mark.api
    def test_sitemap_accessible(self):
        """
        Sitemap.xml должен быть доступен.

        Бизнес-смысл: sitemap помогает поисковикам обнаружить все страницы сайта.
        """
        # Пробуем стандартные расположения sitemap
        possible_urls = [
            f"{BASE_URL}/sitemap.xml",
            f"{BASE_URL}/sitemap_index.xml",
        ]

        found = False
        for url in possible_urls:
            r = requests.get(url, timeout=15)
            if r.status_code == 200 and len(r.text) > 100:
                found = True
                break

        assert found, (
            f"Sitemap не найден ни по одному из ожидаемых URL: {possible_urls}"
        )
