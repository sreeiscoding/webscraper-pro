from app.config import PaginationConfig, validate_url


def test_validate_url_accepts_http_and_https() -> None:
    assert validate_url("https://example.com") is True
    assert validate_url("http://example.com") is True


def test_validate_url_rejects_invalid_values() -> None:
    assert validate_url("") is False
    assert validate_url("example.com") is False
    assert validate_url("ftp://example.com") is False


def test_validate_url_rejects_local_and_private_networks() -> None:
    assert validate_url("http://localhost:8000") is False
    assert validate_url("http://127.0.0.1") is False
    assert validate_url("http://10.0.0.1") is False


def test_pagination_config_serialises_expected_values() -> None:
    settings = PaginationConfig(
        max_pages=4,
        max_records=50,
        next_page_selector="a.next",
        request_delay=0.25,
        max_retries=2,
        retry_backoff=1.5,
    )

    payload = settings.to_dict()
    assert payload["max_pages"] == 4
    assert payload["max_records"] == 50
    assert payload["next_page_selector"] == "a.next"
    assert payload["request_delay"] == 0.25
