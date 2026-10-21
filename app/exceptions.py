"""Custom exceptions for scraper validation and network handling."""

from __future__ import annotations


class WebScraperError(Exception):
    """Base exception for WebScraper Pro."""


class ConfigurationError(WebScraperError):
    """Raised when extraction configuration is invalid or incomplete."""


class NetworkRequestError(WebScraperError):
    """Raised when an HTTP request fails or is rejected."""


class UnexpectedContentTypeError(NetworkRequestError):
    """Raised when the server responds with an unsupported content type."""


class InvalidSelectorError(ConfigurationError):
    """Raised when a CSS selector is malformed or unusable."""


class MissingFieldError(ConfigurationError):
    """Raised when a required field cannot be found in the HTML."""


class UnsupportedExtractionTypeError(ConfigurationError):
    """Raised when a field extraction type is not supported."""
