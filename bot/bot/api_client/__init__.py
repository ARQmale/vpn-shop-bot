"""HTTP client for the backend service.

The bot MUST NOT talk to the database or 3x-ui directly; all state changes
go through the backend per :mod:`shared.contracts.http`.
"""

from __future__ import annotations

from types import TracebackType
from typing import Any, Self

import httpx
from shared.contracts import http as routes
from shared.schemas import (
    PaymentCreate,
    PaymentOut,
    PlanOut,
    SubscriptionOut,
    SubscriptionRenew,
    UserOut,
    UserUpsert,
)

from bot.api_client.errors import (
    BackendError,
    BadRequestError,
    NotFoundError,
    ServerError,
    UnauthorizedError,
)


def _raise_for_status(response: httpx.Response) -> None:
    """Convert non-2xx responses into the module's exception hierarchy."""
    if response.is_success:
        return
    status = response.status_code
    try:
        payload = response.json()
    except ValueError:
        payload = response.text
    message = f"Backend {response.request.method} {response.request.url} -> {status}: {payload!r}"
    if status == 404:
        raise NotFoundError(message, status_code=status)
    if status in (401, 403):
        raise UnauthorizedError(message, status_code=status)
    if 400 <= status < 500:
        raise BadRequestError(message, status_code=status)
    if status >= 500:
        raise ServerError(message, status_code=status)
    raise BackendError(message, status_code=status)


class BackendClient:
    """Thin ``httpx.AsyncClient`` wrapper over the backend HTTP API.

    Every request carries ``X-Bot-Token``; admin calls additionally carry
    ``X-Admin-Token`` when ``admin_token`` is configured.
    """

    def __init__(
        self,
        base_url: str,
        bot_token: str,
        admin_token: str | None = None,
        *,
        timeout: float = 10.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._bot_token = bot_token
        self._admin_token = admin_token
        headers = {routes.HEADER_BOT_TOKEN: bot_token}
        self._client = client or httpx.AsyncClient(
            base_url=f"{self._base_url}{routes.API_PREFIX}",
            headers=headers,
            timeout=timeout,
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    def _admin_headers(self) -> dict[str, str]:
        if not self._admin_token:
            raise UnauthorizedError("admin_token is not configured on BackendClient")
        return {routes.HEADER_ADMIN_TOKEN: self._admin_token}

    # --- users ------------------------------------------------------------
    async def upsert_user(self, dto: UserUpsert) -> UserOut:
        response = await self._client.post(routes.USERS_UPSERT, json=dto.model_dump(mode="json"))
        _raise_for_status(response)
        return UserOut.model_validate(response.json())

    async def get_user(self, telegram_id: int) -> UserOut:
        response = await self._client.get(routes.USER_GET.format(telegram_id=telegram_id))
        _raise_for_status(response)
        return UserOut.model_validate(response.json())

    async def user_subscriptions(self, telegram_id: int) -> list[SubscriptionOut]:
        response = await self._client.get(
            routes.USER_SUBSCRIPTIONS.format(telegram_id=telegram_id)
        )
        _raise_for_status(response)
        return [SubscriptionOut.model_validate(item) for item in response.json()]

    # --- plans ------------------------------------------------------------
    async def list_plans(self) -> list[PlanOut]:
        response = await self._client.get(routes.PLANS_LIST)
        _raise_for_status(response)
        return [PlanOut.model_validate(item) for item in response.json()]

    async def get_plan(self, plan_id: int) -> PlanOut:
        response = await self._client.get(routes.PLAN_GET.format(plan_id=plan_id))
        _raise_for_status(response)
        return PlanOut.model_validate(response.json())

    # --- payments ---------------------------------------------------------
    async def create_payment(self, dto: PaymentCreate) -> PaymentOut:
        response = await self._client.post(
            routes.PAYMENTS_CREATE, json=dto.model_dump(mode="json")
        )
        _raise_for_status(response)
        return PaymentOut.model_validate(response.json())

    async def get_payment(self, payment_id: int) -> PaymentOut:
        response = await self._client.get(routes.PAYMENT_GET.format(payment_id=payment_id))
        _raise_for_status(response)
        return PaymentOut.model_validate(response.json())

    # --- subscriptions ----------------------------------------------------
    async def get_subscription(self, subscription_id: int) -> SubscriptionOut:
        response = await self._client.get(
            routes.SUBSCRIPTION_GET.format(subscription_id=subscription_id)
        )
        _raise_for_status(response)
        return SubscriptionOut.model_validate(response.json())

    async def renew_subscription(
        self, subscription_id: int, dto: SubscriptionRenew
    ) -> PaymentOut:
        response = await self._client.post(
            routes.SUBSCRIPTION_RENEW.format(subscription_id=subscription_id),
            json=dto.model_dump(mode="json"),
        )
        _raise_for_status(response)
        return PaymentOut.model_validate(response.json())

    async def subscription_qr(self, subscription_id: int) -> bytes:
        response = await self._client.get(
            routes.SUBSCRIPTION_QR.format(subscription_id=subscription_id)
        )
        _raise_for_status(response)
        return response.content

    # --- admin ------------------------------------------------------------
    async def admin_stats(self) -> dict[str, Any]:
        response = await self._client.get(routes.ADMIN_STATS, headers=self._admin_headers())
        _raise_for_status(response)
        data = response.json()
        if not isinstance(data, dict):
            raise BackendError(f"admin_stats expected dict, got {type(data).__name__}")
        return data

    async def admin_broadcast(self, message: str) -> dict[str, Any]:
        response = await self._client.post(
            routes.ADMIN_BROADCAST,
            json={"message": message},
            headers=self._admin_headers(),
        )
        _raise_for_status(response)
        data = response.json()
        if not isinstance(data, dict):
            raise BackendError(f"admin_broadcast expected dict, got {type(data).__name__}")
        return data


__all__ = [
    "BackendClient",
    "BackendError",
    "BadRequestError",
    "NotFoundError",
    "ServerError",
    "UnauthorizedError",
]
