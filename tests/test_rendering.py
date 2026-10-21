from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.exceptions import NetworkRequestError
from app.network import fetch_html


class FakePage:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.url = "https://example.com/rendered"
        self._content = "<html><body><h1>Rendered</h1></body></html>"

    def goto(self, url: str, wait_until: str, timeout: int) -> None:
        self.calls.append(f"goto:{url}:{wait_until}:{timeout}")

    def wait_for_selector(self, selector: str, timeout: int) -> None:
        self.calls.append(f"wait:{selector}:{timeout}")

    def content(self) -> str:
        return self._content


class FakeBrowser:
    def __init__(self) -> None:
        self.closed = False
        self.context = SimpleNamespace(new_page=lambda: self.page)
        self.page = FakePage()

    def new_context(self, **kwargs):
        return FakeContext(self)

    def close(self) -> None:
        self.closed = True


class FakeContext:
    def __init__(self, browser: FakeBrowser) -> None:
        self.browser = browser
        self.page = browser.page

    def new_page(self):
        return self.page

    def close(self) -> None:
        self.browser.closed = True


class FakePlaywright:
    def __init__(self) -> None:
        self.browser = FakeBrowser()
        self.called = False

    @property
    def chromium(self):
        return self

    def launch(self, headless: bool):
        self.called = True
        return self.browser


def test_fetch_html_static_uses_requests_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    class FakeResponse:
        status_code = 200
        headers = {"Content-Type": "text/html; charset=utf-8"}
        url = "https://example.com"
        text = "<html><body>ok</body></html>"
        content = text.encode("utf-8")

    def fake_get(*args, **kwargs):
        calls.append("static")
        return FakeResponse()

    monkeypatch.setattr("app.network.requests.get", fake_get)
    assert fetch_html("https://example.com") == "<html><body>ok</body></html>"
    assert calls == ["static"]


def test_fetch_html_rendered_uses_browser_and_waits_for_content(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_playwright = FakePlaywright()
    fake_browser = fake_playwright.browser

    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "playwright.sync_api":
            return SimpleNamespace(sync_playwright=lambda: FakePlaywrightContext(fake_playwright))
        return real_import(name, *args, **kwargs)

    class FakePlaywrightContext:
        def __init__(self, playwright):
            self.playwright = playwright
        @property
        def chromium(self):
            return self.playwright
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            fake_browser.close()

    monkeypatch.setattr("builtins.__import__", fake_import, raising=False)

    result = fetch_html(
        "https://example.com/page",
        engine="playwright",
        render_config={"wait_for": "h1", "wait_timeout": 3000, "page_load_timeout": 30000},
    )

    assert result == "<html><body><h1>Rendered</h1></body></html>"
    assert fake_browser.closed is True


def test_fetch_html_rendered_handles_launch_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "playwright.sync_api":
            raise ImportError("Playwright not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import, raising=False)

    with pytest.raises(NetworkRequestError, match="Playwright"):
        fetch_html("https://example.com/page", engine="playwright")
