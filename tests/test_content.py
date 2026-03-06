"""
tests/test_content.py
=====================
Тесты контента, UX-элементов и критичных пользовательских сценариев.

Покрываемые области:
  - Кнопки CTA (call to action)
  - Ссылки на продукты и цены
  - Форма обратной связи / чат
  - Переход к регистрации/авторизации
  - Контактная информация
  - Отображение цен
"""

import pytest
import requests
from utils.helpers import get_base_url

BASE_URL = get_base_url()


class TestCriticalUserJourneys:
    """
    Тесты критичных пользовательских путей.
    Каждый тест — это шаг, который пользователь должен пройти без помех.
    """

    @pytest.mark.smoke
    @pytest.mark.ui
    def test_registration_link_exists_and_works(self, page):
        """
        На главной странице должна быть ссылка, ведущая к регистрации.

        Бизнес-смысл: если пользователь не может найти CTA-кнопку регистрации,
        он не станет клиентом. Это прямые потери выручки.
        """
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30_000)

        # Ищем любую ссылку на регистрацию
        reg_selectors = [
            "a[href*='registration']",
            "a[href*='register']",
            "a[href*='signup']",
            "a[href*='sign-up']",
            "[class*='register']",
        ]

        found = False
        for selector in reg_selectors:
            if page.locator(selector).count() > 0:
                found = True
                link = page.locator(selector).first
                href = link.get_attribute("href") or ""
                assert href, f"Ссылка регистрации найдена по '{selector}', но href пустой."
                break

        assert found, (
            "Ссылка на регистрацию не найдена на главной странице. "
            "Проверьте наличие CTA-кнопок с href, содержащим 'registration'/'register'."
        )

    @pytest.mark.smoke
    @pytest.mark.ui
    def test_login_link_exists(self, page):
        """
        Ссылка для входа в личный кабинет должна быть на главной странице.

        Бизнес-смысл: существующие клиенты должны легко попасть в кабинет.
        Ненайденная кнопка входа — обращение в поддержку и потеря лояльности.
        """
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30_000)

        login_selectors = [
            "a[href*='my.selectel']",
            "a[href*='login']",
            "a[href*='signin']",
            "[class*='login']",
            "[class*='signin']",
            "a[href*='auth']",
        ]

        found = False
        for selector in login_selectors:
            if page.locator(selector).count() > 0:
                found = True
                break

        assert found, (
            "Ссылка для входа в личный кабинет не найдена на главной странице. "
            "Существующие клиенты не могут быстро авторизоваться."
        )

    @pytest.mark.regression
    @pytest.mark.api
    def test_registration_page_is_accessible(self):
        """
        Страница регистрации должна быть доступна.

        Бизнес-смысл: недоступная страница регистрации = 100% потеря
        всех потенциальных клиентов, которые хотят зарегистрироваться.
        """
        reg_url = "https://my.selectel.ru/registration"
        response = requests.get(reg_url, timeout=15, allow_redirects=True)

        assert response.status_code == 200, (
            f"Страница регистрации {reg_url} вернула {response.status_code}. "
            f"Итоговый URL: {response.url}"
        )

    @pytest.mark.regression
    @pytest.mark.ui
    def test_pricing_page_accessible(self, page):
        """
        Страница с ценами должна быть доступна и содержать информацию о ценах.

        Бизнес-смысл: клиент принимает решение о покупке на основе цен.
        Сломанная страница цен = потеря конверсии.
        """
        page.goto(f"{BASE_URL}/price/", wait_until="domcontentloaded", timeout=30_000)

        # Страница должна содержать признаки цен (числа с валютой)
        body = page.locator("body").inner_text()

        has_price_content = any(
            symbol in body
            for symbol in ["₽", "руб", "RUB", "от", "тариф", "месяц"]
        )
        assert has_price_content, (
            "Страница цен не содержит информации о ценах или тарифах. "
            "Проверьте, что контент загружается корректно."
        )

    @pytest.mark.regression
    @pytest.mark.ui
    def test_blog_page_has_articles(self, page):
        """Блог должен содержать статьи."""
        response = requests.get(f"{BASE_URL}/blog/", timeout=15, allow_redirects=True)
        if response.status_code != 200:
            pytest.skip(f"Блог недоступен ({response.status_code}), пропускаем тест.")

        page.goto(f"{BASE_URL}/blog/", wait_until="domcontentloaded", timeout=30_000)

        # Ищем элементы статей
        article_selectors = ["article", "[class*='post']", "[class*='article']", "[class*='card']"]
        found_count = 0
        for selector in article_selectors:
            count = page.locator(selector).count()
            if count > 0:
                found_count = count
                break

        assert found_count >= 1, (
            f"На странице блога не найдены статьи. "
            f"Проверяемые селекторы: {article_selectors}"
        )


class TestPageContent:
    """Проверяем качество и полноту контента на страницах."""

    @pytest.mark.regression
    @pytest.mark.ui
    def test_no_placeholder_text(self, main_page):
        """
        На странице не должно быть Lorem ipsum или placeholder-текста.

        Бизнес-смысл: заглушки на продакшене подрывают доверие клиентов
        и говорят о низком качестве разработки.
        """
        main_page.open()
        body_text = main_page.page.locator("body").inner_text().lower()

        placeholders = ["lorem ipsum", "placeholder", "coming soon", "скоро", "test text"]
        found_placeholders = [p for p in placeholders if p in body_text]

        assert not found_placeholders, (
            f"Найден placeholder-текст на главной странице: {found_placeholders}"
        )

    @pytest.mark.regression
    @pytest.mark.ui
    def test_no_broken_images(self, main_page):
        """
        Все изображения на странице должны загружаться успешно.

        Бизнес-смысл: битые картинки выглядят как сломанный сайт,
        снижают доверие и конверсию.
        """
        main_page.open()

        # Проверяем через JavaScript — naturalWidth === 0 означает битую картинку
        broken_count = main_page.page.evaluate("""() => {
            const imgs = Array.from(document.querySelectorAll('img'));
            return imgs.filter(img => img.complete && img.naturalWidth === 0).length;
        }""")

        assert broken_count == 0, (
            f"Найдено {broken_count} битых изображений на главной странице. "
            "Проверьте пути к файлам изображений."
        )

    @pytest.mark.regression
    @pytest.mark.api
    def test_contact_page_has_phone_or_email(self):
        """
        Страница контактов должна содержать телефон или email поддержки.

        Бизнес-смысл: клиент должен знать, как связаться с компанией.
        Отсутствие контактов — потеря доверия.
        """
        response = requests.get(f"{BASE_URL}/contacts/", timeout=15, allow_redirects=True)
        if response.status_code != 200:
            pytest.skip(f"Страница контактов недоступна ({response.status_code})")

        content = response.text.lower()
        has_contact = (
            "@selectel" in content          # email
            or "8-800" in content           # бесплатный телефон
            or "+7" in content              # телефон
            or "поддержк" in content        # упоминание поддержки
        )

        assert has_contact, (
            "Страница контактов не содержит контактной информации (телефон/email). "
            "Клиенты не знают, как связаться с компанией."
        )


class TestJavaScriptErrors:
    """Проверяем отсутствие критичных JavaScript-ошибок."""

    @pytest.mark.smoke
    @pytest.mark.ui
    def test_no_critical_js_errors_on_main_page(self, page):
        """
        На главной странице не должно быть критичных JavaScript-ошибок.

        Бизнес-смысл: JS-ошибки могут сломать интерактивные элементы
        (меню, формы, чат) без видимых признаков для тестировщика.
        """
        js_errors = []

        def capture_error(error):
            js_errors.append(str(error))

        page.on("pageerror", capture_error)
        page.goto(BASE_URL, wait_until="networkidle", timeout=30_000)
        page.wait_for_timeout(2000)

        # Фильтруем ошибки от selectel.ru (не третьесторонних скриптов)
        own_errors = [
            e for e in js_errors
            if not any(third_party in e.lower()
                      for third_party in ["google", "facebook", "yandex", "analytics",
                                          "metrika", "jivosite", "intercom"])
        ]

        assert len(own_errors) == 0, (
            f"Обнаружены JS-ошибки на главной странице: {own_errors}"
        )
