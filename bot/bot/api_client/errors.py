"""Exceptions raised by :class:`bot.api_client.BackendClient`."""

from __future__ import annotations


class BackendError(Exception):
    """Base class for all errors coming from the backend HTTP API."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class NotFoundError(BackendError):
    """Backend returned HTTP 404."""


class UnauthorizedError(BackendError):
    """Backend returned HTTP 401/403 — bad or missing bot/admin token."""


class BadRequestError(BackendError):
    """Backend returned HTTP 4xx for a request the client sent."""


class ServerError(BackendError):
    """Backend returned HTTP 5xx."""
