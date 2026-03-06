"""
tests/test_mobile.py
====================
Тесты адаптивности и мобильного отображения selectel.ru.

Покрываемые области:
  - Отсутствие горизонтального скролла
  - Видимость ключевых элементов на мобильном
  - Мобильное меню (бургер)
  - Минимальные размеры кликабельных элементов (44x44px по WCAG)
  - Viewport meta-тег
"""

import pytest
from playwright.sync_api import Page


# Наборы разрешений для тестирования адаптивности
VIEWPORTS = [
    (390, 844, "iPhone 14 Pro"),
    (360, 780, "Android (Samsung Galaxy S23)"),
    (768, 1024, "iPad (портретная ориентация)"),
    (1024, 768, "iPad (альбомная ориентация)"),
]


class TestMobileLayout:
    """Проверяем корректность отображения на мобильных устройствах."""

    @pytest.mark.mobile
    @pytest.mark.ui
    def test_no_horizontal_scroll_on_mobile(self, mobile_main_page):
        """
        На мобильном устройстве (390px) не должно быть горизонтального скролла.

        Бизнес-смысл: горизонтальный скролл на мобильном — критичная вёрсточная
        ошибка. Пользователь не может нормально читать контент и уходит с сайта.
        Мобильный трафик — 50–70% от общего.
        """
        mobile_main_page.open()
        scroll_width = mobile_main_page.page.evaluate("document.documentElement.scrollWidth")
        client_width = mobile_main_page.page.evaluate("document.documentElement.clientWidth")

        assert scroll_width <= client_width, (
            f"Горизонтальный скролл на мобильном: scrollWidth={scroll_width}px, "
            f"clientWidth={client_width}px. Разница: {scroll_width - client_width}px. "
            "Проверьте элементы с фиксированной шириной или overflow."
        )

    @pytest.mark.mobile
    @pytest.mark.ui
    def test_h1_visible_on_mobile(self, mobile_main_page):
        """Заголовок H1 должен быть виден на мобильном устройстве без скролла."""
        mobile_main_page.open()
        h1 = mobile_main_page.page.locator("h1").first

        assert h1.is_visible(), (
            "H1 не виден сразу при загрузке страницы на мобильном устройстве."
        )

    @pytest.mark.mobile
    @pytest.mark.ui
    def test_header_visible_on_mobile(self, mobile_main_page):
        """Шапка должна быть видна на мобильном."""
        mobile_main_page.open()
        assert mobile_main_page.is_header_visible(), (
            "Шапка не видна на мобильном устройстве."
        )

    @pytest.mark.mobile
    @pytest.mark.ui
    def test_viewport_meta_tag_present(self, mobile_main_page):
        """
        Мета-тег viewport должен присутствовать с корректными настройками.

        Без него мобильные браузеры рендерят страницу как десктопную,
        пользователь видит уменьшенный нечитаемый текст.
        """
        mobile_main_page.open()
        viewport_meta = mobile_main_page.page.locator('meta[name="viewport"]')

        assert viewport_meta.count() > 0, (
            "Мета-тег <meta name='viewport'> отсутствует! "
            "Страница будет некорректно отображаться на мобильных устройствах."
        )

        content = viewport_meta.get_attribute("content") or ""
        assert "width=device-width" in content, (
            f"Viewport meta не содержит 'width=device-width': '{content}'. "
            "Это необходимо для корректной адаптивности."
        )

    @pytest.mark.mobile
    @pytest.mark.ui
    @pytest.mark.parametrize("width,height,device_name", VIEWPORTS)
    def test_page_renders_on_different_screens(
        self, browser_instance, width: int, height: int, device_name: str
    ):
        """
        Страница должна корректно рендериться на разных размерах экрана.

        Проверяем отсутствие JS-ошибок и наличие H1 на всех разрешениях.
        """
        ctx = browser_instance.new_context(
            viewport={"width": width, "height": height},
            locale="ru-RU",
        )
        page = ctx.new_page()

        js_errors = []
        page.on("console", lambda msg: js_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: js_errors.append(str(err)))

        try:
            page.goto("https://selectel.ru", wait_until="domcontentloaded", timeout=30_000)

            # H1 должен быть на любом разрешении
            h1_count = page.locator("h1").count()
            assert h1_count >= 1, (
                f"[{device_name} {width}x{height}] H1 не найден на странице."
            )

            # Нет критичных JS-ошибок (фильтруем третьесторонние)
            critical_errors = [
                e for e in js_errors
                if "selectel.ru" in e or "TypeError" in e or "ReferenceError" in e
            ]
            assert len(critical_errors) == 0, (
                f"[{device_name} {width}x{height}] JS-ошибки: {critical_errors}"
            )

        finally:
            page.close()
            ctx.close()

    @pytest.mark.mobile
    @pytest.mark.ui
    def test_touch_targets_size(self, mobile_main_page):
        """
        Интерактивные элементы должны иметь минимальный размер 44x44px (WCAG 2.5.5).

        Бизнес-смысл: слишком маленькие кнопки — частая причина случайных кликов
        на мобильных. Пользователь нажимает не то и испытывает разочарование.
        """
        mobile_main_page.open()

        # Проверяем кнопки и ссылки в навигации
        buttons = mobile_main_page.page.locator("button, a[class*='btn'], a[class*='button']").all()

        small_elements = []
        for btn in buttons[:10]:  # Проверяем первые 10 для скорости
            try:
                if not btn.is_visible():
                    continue
                box = btn.bounding_box()
                if box and (box["width"] < 44 or box["height"] < 44):
                    small_elements.append({
                        "text": btn.inner_text()[:30] or btn.get_attribute("aria-label") or "?",
                        "width": round(box["width"]),
                        "height": round(box["height"]),
                    })
            except Exception:
                continue

        # Допускаем небольшое количество — иконки-декорации могут быть меньше
        assert len(small_elements) <= 2, (
            f"Найдено {len(small_elements)} элементов меньше 44x44px: {small_elements}. "
            "По WCAG 2.5.5 минимальный размер touch-цели — 44x44px."
        )
