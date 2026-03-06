"""
tests/test_main_page.py
=======================
Тесты главной страницы selectel.ru.

Покрываемые области:
  - Загрузка и HTTP-статус
  - Структура страницы (H1, header, footer)
  - SEO: мета-теги, canonical, favicon
  - Безопасность: HTTPS
  - Производительность: время загрузки
  - Доступность: lang, alt у картинок
  - Мобильная версия
"""

import pytest
import requests
from utils.helpers import get_base_url, MAX_LOAD_TIME_MS


BASE_URL = get_base_url()


# ═══════════════════════════════════════════════════════════════════════════════
# HTTP / Доступность сервера
# ═══════════════════════════════════════════════════════════════════════════════

class TestHttpAvailability:
    """Проверяем, что сайт доступен и возвращает корректные HTTP-коды."""

    @pytest.mark.smoke
    @pytest.mark.api
    def test_main_page_returns_200(self):
        """
        Главная страница должна возвращать HTTP 200.

        Бизнес-смысл: если сайт недоступен — клиенты не могут узнать
        о продуктах и оформить заказ. Критичность: максимальная.
        """
        response = requests.get(BASE_URL, timeout=15, allow_redirects=True)
        assert response.status_code == 200, (
            f"Главная страница вернула {response.status_code} вместо 200. "
            f"Итоговый URL после редиректов: {response.url}"
        )

    @pytest.mark.smoke
    @pytest.mark.api
    def test_main_page_redirects_to_https(self):
        """
        HTTP-версия сайта должна редиректить на HTTPS.

        Бизнес-смысл: HTTPS обязателен для доверия клиентов и SEO.
        Отсутствие редиректа — угроза безопасности и позиций в поиске.
        """
        http_url = BASE_URL.replace("https://", "http://")
        response = requests.get(http_url, timeout=15, allow_redirects=True)
        assert response.url.startswith("https://"), (
            f"Ожидался редирект на HTTPS, итоговый URL: {response.url}"
        )

    @pytest.mark.api
    def test_response_time_is_acceptable(self):
        """
        Сервер должен отвечать не дольше 5 секунд.

        Бизнес-смысл: задержка > 3с увеличивает bounce rate на 32%.
        Данный порог — технический минимум (не UX-оптимум).
        """
        import time
        start = time.time()
        requests.get(BASE_URL, timeout=15, allow_redirects=True)
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < MAX_LOAD_TIME_MS, (
            f"Сервер ответил за {elapsed_ms:.0f}ms — превышен порог {MAX_LOAD_TIME_MS}ms."
        )

    @pytest.mark.api
    def test_security_headers_present(self):
        """
        Ответ должен содержать базовые заголовки безопасности.

        Бизнес-смысл: отсутствие X-Frame-Options открывает возможность
        clickjacking-атак; без X-Content-Type-Options — MIME-sniffing.
        """
        response = requests.get(BASE_URL, timeout=15, allow_redirects=True)
        headers = {k.lower(): v for k, v in response.headers.items()}

        # Хотя бы один из заголовков защиты должен присутствовать
        security_headers = [
            "x-frame-options",
            "content-security-policy",
            "x-content-type-options",
            "strict-transport-security",
        ]
        found = [h for h in security_headers if h in headers]
        assert len(found) > 0, (
            f"Не найдено ни одного заголовка безопасности. "
            f"Проверяемые: {security_headers}. "
            f"Заголовки ответа: {list(headers.keys())}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Структура страницы (UI)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPageStructure:
    """Проверяем ключевые структурные элементы главной страницы."""

    @pytest.mark.smoke
    @pytest.mark.ui
    def test_page_has_title(self, main_page):
        """
        У страницы должен быть непустой title.

        Бизнес-смысл: title — первое, что видят в поисковой выдаче.
        Пустой title ведёт к потере органического трафика.
        """
        main_page.open()
        title = main_page.get_title()
        assert title, "Title страницы пустой."
        assert len(title) > 5, f"Title слишком короткий: '{title}'"
        assert "selectel" in title.lower() or "селектел" in title.lower(), (
            f"Title не содержит упоминания бренда: '{title}'"
        )

    @pytest.mark.smoke
    @pytest.mark.ui
    def test_page_has_h1(self, main_page):
        """
        На главной странице должен быть ровно один H1.

        Бизнес-смысл: несколько H1 — SEO-ошибка. Отсутствие H1 —
        плохо для доступности и поисковых роботов.
        """
        main_page.open()
        h1_count = main_page.count_elements("h1")
        assert h1_count >= 1, "H1 не найден на главной странице."
        assert h1_count == 1, f"На странице {h1_count} тега H1 — должен быть ровно 1."

    @pytest.mark.smoke
    @pytest.mark.ui
    def test_header_is_visible(self, main_page):
        """Шапка сайта должна быть видна после загрузки страницы."""
        main_page.open()
        assert main_page.is_header_visible(), "Шапка (header) не видна на странице."

    @pytest.mark.smoke
    @pytest.mark.ui
    def test_footer_is_visible(self, main_page):
        """Футер сайта должен присутствовать и быть виден."""
        main_page.open()
        main_page.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        main_page.page.wait_for_timeout(500)
        assert main_page.is_footer_visible(), "Футер (footer) не найден на странице."

    @pytest.mark.ui
    def test_footer_has_links(self, main_page):
        """Футер должен содержать ссылки на разделы сайта."""
        main_page.open()
        count = main_page.get_footer_link_count()
        assert count >= 5, (
            f"В футере найдено только {count} ссылок — ожидается не менее 5."
        )

    @pytest.mark.ui
    def test_no_horizontal_scroll_on_desktop(self, main_page):
        """
        На десктопном разрешении (1440px) не должно быть горизонтального скролла.

        Бизнес-смысл: горизонтальный скролл — признак вёрсточной поломки,
        значительно ухудшает пользовательский опыт.
        """
        main_page.open()
        assert main_page.has_no_horizontal_scroll(), (
            "Обнаружен горизонтальный скролл на десктопном разрешении 1440px. "
            "Проверьте ширину контейнеров и overflow."
        )

    @pytest.mark.ui
    def test_page_uses_https(self, main_page):
        """Страница должна быть загружена по HTTPS."""
        main_page.open()
        assert main_page.is_page_secure(), (
            f"Страница загружена не по HTTPS: {main_page.get_url()}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SEO и мета-теги
# ═══════════════════════════════════════════════════════════════════════════════

class TestSeoMetaTags:
    """Проверяем наличие и качество SEO-атрибутов."""

    @pytest.mark.regression
    @pytest.mark.ui
    def test_meta_description_present(self, main_page):
        """
        Мета-тег description должен присутствовать и быть непустым.

        Бизнес-смысл: description отображается в сниппете в поисковой выдаче.
        Его отсутствие снижает CTR из поиска.
        """
        main_page.open()
        description = main_page.get_meta_content("description")
        assert description, "Мета-тег <meta name='description'> отсутствует или пустой."
        assert len(description) >= 50, (
            f"Мета-description слишком короткий ({len(description)} симв.): '{description}'"
        )
        assert len(description) <= 320, (
            f"Мета-description слишком длинный ({len(description)} симв.) — "
            f"обрезается в поиске после 160 симв.: '{description[:50]}...'"
        )

    @pytest.mark.regression
    @pytest.mark.ui
    def test_og_title_present(self, main_page):
        """Open Graph title должен быть задан для корректного шаринга в соцсетях."""
        main_page.open()
        og_title = main_page.get_og_content("title")
        assert og_title, (
            "Мета-тег <meta property='og:title'> отсутствует. "
            "При шаринге ссылки в соцсетях будет показан некорректный заголовок."
        )

    @pytest.mark.regression
    @pytest.mark.ui
    def test_og_image_present(self, main_page):
        """Open Graph image должен быть задан для превью при шаринге."""
        main_page.open()
        og_image = main_page.get_og_content("image")
        assert og_image, (
            "Мета-тег <meta property='og:image'> отсутствует. "
            "При шаринге ссылки в Telegram/VK/соцсетях не будет картинки."
        )

    @pytest.mark.regression
    @pytest.mark.ui
    def test_canonical_url_present(self, main_page):
        """Canonical URL должен быть задан для избежания дублирования контента."""
        main_page.open()
        canonical = main_page.get_canonical_url()
        assert canonical, (
            "Тег <link rel='canonical'> отсутствует. "
            "Это может привести к дублированию контента в поисковых системах."
        )

    @pytest.mark.regression
    @pytest.mark.ui
    def test_favicon_present(self, main_page):
        """Favicon должен быть задан — базовый элемент идентичности бренда."""
        main_page.open()
        assert main_page.has_favicon(), (
            "Favicon не найден. Вкладка браузера будет без иконки — "
            "негативно влияет на восприятие бренда."
        )

    @pytest.mark.regression
    @pytest.mark.ui
    def test_html_lang_attribute(self, main_page):
        """
        Тег <html> должен иметь атрибут lang.

        Бизнес-смысл: lang нужен для скринридеров (доступность),
        правильного произношения голосовыми помощниками, и учитывается поисковиками.
        """
        main_page.open()
        lang = main_page.get_lang()
        assert lang, "Атрибут lang отсутствует на теге <html>."
        assert lang.startswith("ru"), (
            f"Ожидается lang='ru', найдено lang='{lang}'. "
            f"Для русскоязычного сайта должен быть указан русский язык."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Доступность (Accessibility)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAccessibility:
    """Базовые проверки доступности по стандарту WCAG 2.1."""

    @pytest.mark.accessibility
    @pytest.mark.ui
    def test_images_have_alt_attributes(self, main_page):
        """
        Все изображения должны иметь атрибут alt.

        Бизнес-смысл: без alt скринридеры не могут описать картинку.
        Нарушение WCAG 2.1 (1.1.1) — риск претензий по доступности.
        """
        main_page.open()
        # Прокручиваем страницу для загрузки lazy-load картинок
        main_page.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        main_page.page.wait_for_timeout(1000)

        missing_alt = main_page.get_images_without_alt()
        total_imgs = main_page.count_elements("img")

        assert missing_alt == 0, (
            f"Найдено {missing_alt} из {total_imgs} изображений без атрибута alt. "
            f"Все <img> должны иметь alt='' (декоративные) или осмысленный alt."
        )

    @pytest.mark.accessibility
    @pytest.mark.ui
    def test_page_has_main_landmark(self, main_page):
        """
        Страница должна содержать тег <main> или role='main'.

        Бизнес-смысл: landmark-регионы позволяют пользователям скринридеров
        быстро переходить к основному контенту, минуя навигацию.
        """
        main_page.open()
        main_count = main_page.count_elements("main, [role='main']")
        assert main_count >= 1, (
            "Не найден элемент <main> или role='main'. "
            "Добавьте семантический тег <main> для основного контента."
        )

    @pytest.mark.accessibility
    @pytest.mark.ui
    def test_navigation_has_nav_tag(self, main_page):
        """Навигация должна быть обёрнута в семантический тег <nav>."""
        main_page.open()
        nav_count = main_page.count_elements("nav")
        assert nav_count >= 1, (
            "Не найден тег <nav>. Навигация должна быть семантически размечена."
        )
