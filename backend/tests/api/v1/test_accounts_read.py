from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from personalsaving.models import Account


@pytest.fixture
async def stored_accounts(db_session: AsyncSession) -> list[Account]:
    # Insert out of display order, with an archived account that sorts first.
    specifications = [
        (4, "Zulu", "checking", False),
        (3, "Daily", "savings", False),
        (2, "Daily", "checking", False),
        (1, "Daily", "checking", False),
        (5, "Archived", "checking", True),
    ]
    accounts = [
        Account(
            id=UUID(int=identifier),
            name=name,
            account_type=account_type,
            currency="CHF",
            iban=None,
            opening_balance=Decimal("1250.50"),
            balance=Decimal("1250.50"),
            opening_date=date(2026, 10, 10),
            archived=archived,
            archived_at=datetime(2026, 11, 1, tzinfo=UTC) if archived else None,
        )
        for identifier, name, account_type, archived in specifications
    ]
    db_session.add_all(accounts)
    await db_session.commit()
    return sorted(accounts, key=lambda account: (account.name, account.account_type, account.id))


def assert_account_response(body: dict[str, Any], account: Account) -> None:
    assert body["id"] == str(account.id)
    assert body["name"] == account.name
    assert body["account_type"] == account.account_type
    assert body["currency"] == account.currency
    assert body["iban"] is None
    assert body["opening_balance"] == "1250.50"
    assert body["balance"] == "1250.50"
    assert body["opening_date"] == account.opening_date.isoformat()
    assert body["archived"] is account.archived
    for field in ("created_at", "updated_at"):
        assert isinstance(body[field], str)
        timestamp = datetime.fromisoformat(body[field])
        assert timestamp.utcoffset() == timedelta(0)
        assert timestamp == getattr(account, field)
    if account.archived_at is None:
        assert body["archived_at"] is None
    else:
        timestamp = datetime.fromisoformat(body["archived_at"])
        assert timestamp.utcoffset() == timedelta(0)
        assert timestamp == account.archived_at


@pytest.mark.parametrize("archived", [False, True])
async def test_get_account_returns_active_and_archived_accounts(
    client: AsyncClient, stored_accounts: list[Account], archived: bool
) -> None:
    account = next(account for account in stored_accounts if account.archived is archived)

    response = await client.get(f"/api/v1/accounts/{account.id}")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert_account_response(response.json(), account)


async def test_get_account_returns_not_found_for_unknown_uuid(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/accounts/{UUID(int=999)}")

    assert response.status_code == 404


@pytest.mark.parametrize(
    "error_type, expected_status",
    [(OperationalError, 503), (SQLAlchemyError, 500)],
)
async def test_get_account_database_failure_returns_safe_error(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    error_type: type[SQLAlchemyError],
    expected_status: int,
) -> None:
    account_id = UUID(int=999)
    sensitive_details = "host=private-db port=5432 user=secret-user password=secret-password"
    error: SQLAlchemyError
    if error_type is OperationalError:
        error = OperationalError("SELECT * FROM accounts", {}, OSError(sensitive_details))
    else:
        error = SQLAlchemyError(sensitive_details)
    failed_lookup = AsyncMock(side_effect=error)
    monkeypatch.setattr(db_session, "get", failed_lookup)

    response = await client.get(f"/api/v1/accounts/{account_id}")

    assert response.status_code == expected_status
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"detail": "Database operation failed"}
    for secret in ("private-db", "5432", "secret-user", "secret-password", "SELECT", "Traceback"):
        assert secret not in response.text
    failed_lookup.assert_awaited_once_with(Account, account_id)


@pytest.mark.parametrize("account_id", ["invalid-uuid", "123", "null"])
async def test_get_account_rejects_invalid_uuid(client: AsyncClient, account_id: str) -> None:
    response = await client.get(f"/api/v1/accounts/{account_id}")

    assert response.status_code == 422
    assert any(error["loc"] == ["path", "account_id"] for error in response.json()["detail"])


async def test_list_accounts_defaults_filter_and_sort(client: AsyncClient, stored_accounts: list[Account]) -> None:
    response = await client.get("/api/v1/accounts")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    body = response.json()
    expected = [account for account in stored_accounts if not account.archived]
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert body["has_more"] is False
    assert [item["id"] for item in body["items"]] == [str(account.id) for account in expected]
    for item, account in zip(body["items"], expected, strict=True):
        assert_account_response(item, account)


@pytest.mark.parametrize("archived", [False, True])
async def test_list_accounts_explicit_archive_filter(
    client: AsyncClient, stored_accounts: list[Account], archived: bool
) -> None:
    response = await client.get("/api/v1/accounts", params={"archived": str(archived).lower()})

    assert response.status_code == 200
    body = response.json()
    expected = [account for account in stored_accounts if account.archived is archived]
    assert len(body["items"]) == len(expected)
    for item, account in zip(body["items"], expected, strict=True):
        assert_account_response(item, account)
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert body["has_more"] is False


@pytest.mark.parametrize(
    "limit, offset, has_more",
    [(1, 0, True), (2, 1, True), (2, 2, False), (1, 3, False), (2, 4, False), (2, 20, False), (200, 0, False)],
)
async def test_list_accounts_paginates_after_filtering_and_sorting(
    client: AsyncClient, stored_accounts: list[Account], limit: int, offset: int, has_more: bool
) -> None:
    response = await client.get("/api/v1/accounts", params={"limit": limit, "offset": offset})

    assert response.status_code == 200
    body = response.json()
    expected = [account for account in stored_accounts if not account.archived][offset : offset + limit]
    assert body["limit"] == limit
    assert body["offset"] == offset
    assert body["has_more"] is has_more
    assert [item["id"] for item in body["items"]] == [str(account.id) for account in expected]
    for item, account in zip(body["items"], expected, strict=True):
        assert_account_response(item, account)


@pytest.mark.parametrize("params", [{}, {"limit": 1, "offset": 0}, {"archived": "true"}])
async def test_list_accounts_empty_results(client: AsyncClient, params: dict[str, Any]) -> None:
    response = await client.get("/api/v1/accounts", params=params)

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "limit": params.get("limit", 50),
        "offset": params.get("offset", 0),
        "has_more": False,
    }


@pytest.mark.parametrize(
    "field, value",
    [
        ("limit", "0"),
        ("limit", "-1"),
        ("limit", "201"),
        ("limit", "1.5"),
        ("limit", "abc"),
        ("offset", "-1"),
        ("offset", "1.5"),
        ("offset", "abc"),
        ("archived", "maybe"),
    ],
)
async def test_list_accounts_rejects_invalid_query_parameters(client: AsyncClient, field: str, value: str) -> None:
    response = await client.get("/api/v1/accounts", params={field: value})

    assert response.status_code == 422
    assert any(error["loc"] == ["query", field] for error in response.json()["detail"])


@pytest.mark.parametrize("error_type, expected_status", [(OperationalError, 503), (SQLAlchemyError, 500)])
async def test_list_accounts_database_failure_returns_safe_error(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    error_type: type[SQLAlchemyError],
    expected_status: int,
) -> None:
    sensitive_details = "host=private-db port=5432 user=secret-user password=secret-password"
    error: SQLAlchemyError
    if error_type is OperationalError:
        error = OperationalError("SELECT * FROM accounts", {}, OSError(sensitive_details))
    else:
        error = SQLAlchemyError(sensitive_details)
    failed_query = AsyncMock(side_effect=error)
    rollback = AsyncMock(wraps=db_session.rollback)
    with monkeypatch.context() as patch:
        patch.setattr(db_session, "execute", failed_query)
        patch.setattr(db_session, "rollback", rollback)
        response = await client.get("/api/v1/accounts")
        assert response.status_code == expected_status
        assert response.headers["content-type"] == "application/json"
        assert response.json() == {"detail": "Database operation failed"}
        failed_query.assert_awaited_once()
        rollback.assert_awaited_once()

    for secret in ("private-db", "5432", "secret-user", "secret-password", "SELECT", "Traceback"):
        assert secret not in response.text
    retry = await client.get("/api/v1/accounts")
    assert retry.status_code == 200
    assert retry.json()["items"] == []


@pytest.mark.parametrize("operation", ["get", "list"])
async def test_read_accounts_response_validation_failure_returns_safe_error(
    client: AsyncClient,
    db_session: AsyncSession,
    stored_accounts: list[Account],
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    account = next(account for account in stored_accounts if not account.archived)
    account_id = account.id
    private_value = "private-invalid-account-type"
    account.account_type = private_value
    await db_session.commit()
    url = f"/api/v1/accounts/{account_id}" if operation == "get" else "/api/v1/accounts"
    rollback = AsyncMock(wraps=db_session.rollback)
    with monkeypatch.context() as patch:
        patch.setattr(db_session, "rollback", rollback)
        response = await client.get(url)
        assert response.status_code == 500
        assert response.headers["content-type"] == "application/json"
        assert response.json() == {"detail": "Validating the Datamodel failed"}
        rollback.assert_awaited_once()

    assert private_value not in response.text
    assert "Traceback" not in response.text
    # Reads must preserve the stored facts even when response validation fails.
    preserved = await db_session.get(Account, account_id)
    assert preserved is not None
    assert preserved.account_type == private_value
