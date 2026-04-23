"""Unit tests for :class:`bot.api_client.BackendClient` via pytest-httpx."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pytest
from bot.api_client import BackendClient
from bot.api_client.errors import (
    BadRequestError,
    NotFoundError,
    ServerError,
    UnauthorizedError,
)
from pytest_httpx import HTTPXMock
from shared.contracts import http as routes
from shared.enums import Currency, PaymentProvider, PaymentStatus, SubscriptionStatus
from shared.schemas import PaymentCreate, SubscriptionRenew, UserUpsert

BASE = "http://backend.test"
BOT_TOKEN = "bot-token"  # noqa: S105 — test fixture
ADMIN_TOKEN = "admin-token"  # noqa: S105 — test fixture
API = f"{BASE}{routes.API_PREFIX}"


@pytest.fixture
async def client() -> BackendClient:
    return BackendClient(base_url=BASE, bot_token=BOT_TOKEN, admin_token=ADMIN_TOKEN)


async def test_upsert_user_sends_bot_header(
    httpx_mock: HTTPXMock, client: BackendClient
) -> None:
    payload = {
        "id": 1,
        "telegram_id": 42,
        "username": "neo",
        "first_name": "Thomas",
        "last_name": "Anderson",
        "locale": "ru",
        "balance": "0",
        "is_admin": False,
        "is_banned": False,
        "created_at": datetime.now(tz=UTC).isoformat(),
    }
    httpx_mock.add_response(method="POST", url=f"{API}{routes.USERS_UPSERT}", json=payload)

    out = await client.upsert_user(UserUpsert(telegram_id=42, username="neo"))

    assert out.telegram_id == 42
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers[routes.HEADER_BOT_TOKEN] == BOT_TOKEN
    assert routes.HEADER_ADMIN_TOKEN not in request.headers
    await client.aclose()


async def test_list_plans(httpx_mock: HTTPXMock, client: BackendClient) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}{routes.PLANS_LIST}",
        json=[
            {
                "id": 1,
                "name": "1 month",
                "description": None,
                "duration_days": 30,
                "traffic_gb": 0,
                "price": "299",
                "currency": Currency.RUB.value,
                "is_active": True,
                "sort_order": 0,
            }
        ],
    )
    plans = await client.list_plans()
    assert len(plans) == 1
    assert plans[0].price == Decimal("299")
    await client.aclose()


async def test_user_subscriptions(httpx_mock: HTTPXMock, client: BackendClient) -> None:
    now = datetime.now(tz=UTC).isoformat()
    httpx_mock.add_response(
        method="GET",
        url=f"{API}{routes.USER_SUBSCRIPTIONS.format(telegram_id=99)}",
        json=[
            {
                "id": 7,
                "user_id": 1,
                "plan_id": 2,
                "xui_client_uuid": "uuid",
                "xui_inbound_id": 1,
                "xui_email": "u@example.com",
                "vless_link": "vless://",
                "traffic_limit_bytes": 0,
                "traffic_used_bytes": 0,
                "starts_at": now,
                "expires_at": now,
                "status": SubscriptionStatus.ACTIVE.value,
                "created_at": now,
            }
        ],
    )
    subs = await client.user_subscriptions(99)
    assert subs[0].id == 7
    await client.aclose()


async def test_create_payment_posts_body(
    httpx_mock: HTTPXMock, client: BackendClient
) -> None:
    now = datetime.now(tz=UTC).isoformat()
    httpx_mock.add_response(
        method="POST",
        url=f"{API}{routes.PAYMENTS_CREATE}",
        json={
            "id": 10,
            "user_id": 1,
            "plan_id": 2,
            "subscription_id": None,
            "amount": "299",
            "currency": Currency.RUB.value,
            "provider": PaymentProvider.YOOKASSA.value,
            "provider_payment_id": "prv-1",
            "payment_url": "https://pay",
            "status": PaymentStatus.PENDING.value,
            "created_at": now,
        },
    )
    dto = PaymentCreate(telegram_id=1, plan_id=2, provider=PaymentProvider.YOOKASSA)
    out = await client.create_payment(dto)
    assert out.payment_url == "https://pay"
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers[routes.HEADER_BOT_TOKEN] == BOT_TOKEN
    await client.aclose()


async def test_get_subscription_not_found_raises(
    httpx_mock: HTTPXMock, client: BackendClient
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}{routes.SUBSCRIPTION_GET.format(subscription_id=123)}",
        status_code=404,
        json={"detail": "no"},
    )
    with pytest.raises(NotFoundError):
        await client.get_subscription(123)
    await client.aclose()


async def test_renew_subscription(
    httpx_mock: HTTPXMock, client: BackendClient
) -> None:
    now = datetime.now(tz=UTC).isoformat()
    httpx_mock.add_response(
        method="POST",
        url=f"{API}{routes.SUBSCRIPTION_RENEW.format(subscription_id=5)}",
        json={
            "id": 11,
            "user_id": 1,
            "plan_id": 2,
            "subscription_id": 5,
            "amount": "299",
            "currency": Currency.RUB.value,
            "provider": PaymentProvider.YOOKASSA.value,
            "provider_payment_id": None,
            "payment_url": None,
            "status": PaymentStatus.PENDING.value,
            "created_at": now,
        },
    )
    out = await client.renew_subscription(5, SubscriptionRenew(plan_id=2))
    assert out.subscription_id == 5
    await client.aclose()


async def test_subscription_qr_returns_bytes(
    httpx_mock: HTTPXMock, client: BackendClient
) -> None:
    png = b"\x89PNG\r\n\x1a\n"
    httpx_mock.add_response(
        method="GET",
        url=f"{API}{routes.SUBSCRIPTION_QR.format(subscription_id=3)}",
        content=png,
        headers={"content-type": "image/png"},
    )
    body = await client.subscription_qr(3)
    assert body == png
    await client.aclose()


async def test_admin_stats_sends_admin_header(
    httpx_mock: HTTPXMock, client: BackendClient
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}{routes.ADMIN_STATS}",
        json={"users": 3, "subscriptions": 5},
    )
    stats = await client.admin_stats()
    assert stats["users"] == 3
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers[routes.HEADER_ADMIN_TOKEN] == ADMIN_TOKEN
    await client.aclose()


async def test_admin_without_token_raises() -> None:
    c = BackendClient(base_url=BASE, bot_token=BOT_TOKEN, admin_token=None)
    with pytest.raises(UnauthorizedError):
        await c.admin_stats()
    await c.aclose()


async def test_admin_broadcast_posts_body(
    httpx_mock: HTTPXMock, client: BackendClient
) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}{routes.ADMIN_BROADCAST}",
        json={"count": 7},
    )
    out = await client.admin_broadcast("hi")
    assert out["count"] == 7
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers[routes.HEADER_ADMIN_TOKEN] == ADMIN_TOKEN
    await client.aclose()


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (400, BadRequestError),
        (401, UnauthorizedError),
        (403, UnauthorizedError),
        (500, ServerError),
    ],
)
async def test_status_code_mapping(
    httpx_mock: HTTPXMock, client: BackendClient, status: int, expected: type[Exception]
) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}{routes.PLANS_LIST}",
        status_code=status,
        json={"detail": "x"},
    )
    with pytest.raises(expected):
        await client.list_plans()
    await client.aclose()


async def test_async_context_manager_closes_session() -> None:
    transport = httpx.MockTransport(lambda req: httpx.Response(200, json=[]))
    http_client = httpx.AsyncClient(
        base_url=f"{BASE}{routes.API_PREFIX}",
        headers={routes.HEADER_BOT_TOKEN: BOT_TOKEN},
        transport=transport,
    )
    async with BackendClient(
        base_url=BASE, bot_token=BOT_TOKEN, client=http_client
    ) as c:
        plans = await c.list_plans()
    assert plans == []
    assert http_client.is_closed
