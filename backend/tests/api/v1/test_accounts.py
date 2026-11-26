from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, Mock

import pycountry
import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from personalsaving.api.v1.accounts import AccountCreate, AccountResponse
from personalsaving.models import Account


@pytest.mark.parametrize(
    "json_parameter, json_value",
    [
        ("id", "123e4567-e89b-12d3-a456-426614174000"),
        ("created_at", "2026-10-10T12:00:00Z"),
        ("updated_at", "2026-10-10T12:00:00Z"),
        ("archived", True),
        ("archived_at", "2026-10-10T12:00:00Z"),
        ("balance", "1000.00"),
        ("unexpected_field", "unexpected value"),
    ],
)
async def test_create_account_rejects_server_managed_fields(
    client: AsyncClient, db_session: AsyncSession, json_parameter: str, json_value: str | bool
) -> None:
    test_account_json = {
        "name": "Daily spending",
        "account_type": "savings",
        "currency": "CHF",
        "iban": None,
        "opening_balance": "1250.50",
        "opening_date": "2026-10-10",
        json_parameter: json_value,
    }

    response = await client.post(url="/api/v1/accounts", json=test_account_json)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", json_parameter]
    assert await db_session.scalar(select(func.count()).select_from(Account)) == 0


async def test_create_account_with_valid_body(client: AsyncClient, db_session: AsyncSession) -> None:
    test_account_json = {
        "name": "Daily spending",
        "account_type": "savings",
        "currency": "CHF",
        "iban": None,
        "opening_balance": "1250.50",
        "opening_date": "2026-10-10",
    }

    response = await client.post(url="/api/v1/accounts", json=test_account_json)
    assert response.status_code == 201
    assert response.headers["content-type"] == "application/json"
    body = response.json()

    result = await db_session.execute(select(Account).where(Account.name == "Daily spending"))
    saved_account = result.scalar_one()

    assert body["id"] == str(saved_account.id)
    assert response.headers["location"] == f"/api/v1/accounts/{saved_account.id}"
    assert body["name"] == "Daily spending"
    assert body["account_type"] == "savings"
    assert body["currency"] == "CHF"
    assert body["iban"] is None
    assert body["opening_balance"] == "1250.50"
    assert body["opening_date"] == "2026-10-10"
    assert body["balance"] == "1250.50"
    assert isinstance(body["created_at"], str)
    assert isinstance(body["updated_at"], str)
    created_at = datetime.fromisoformat(body["created_at"])
    updated_at = datetime.fromisoformat(body["updated_at"])
    assert created_at.utcoffset() == timedelta(0)
    assert updated_at.utcoffset() == timedelta(0)
    assert created_at == saved_account.created_at
    assert updated_at == saved_account.updated_at
    assert body["archived"] is False
    assert body["archived_at"] is None

    assert saved_account.name == "Daily spending"
    assert saved_account.account_type == "savings"
    assert saved_account.currency == "CHF"
    assert saved_account.archived is False
    assert saved_account.iban is None
    assert saved_account.opening_balance == Decimal("1250.50")
    assert saved_account.balance == Decimal("1250.50")
    assert saved_account.opening_date == date(2026, 10, 10)
    assert saved_account.archived_at is None


async def test_create_account_without_optional_fields(client: AsyncClient, db_session: AsyncSession) -> None:
    test_account_json = {
        "name": "Daily spending",
        "opening_date": "2026-10-10",
    }

    response = await client.post(url="/api/v1/accounts", json=test_account_json)
    assert response.status_code == 201

    result = await db_session.execute(select(Account).where(Account.name == "Daily spending"))
    saved_account = result.scalar_one()

    assert response.json()["id"] == str(saved_account.id)
    assert saved_account.name == "Daily spending"
    assert saved_account.account_type == "checking"
    assert saved_account.currency == "CHF"
    assert saved_account.archived is False
    assert saved_account.iban is None
    assert saved_account.opening_balance == Decimal(0)
    assert saved_account.balance == Decimal(0)
    body = response.json()
    assert body["account_type"] == "checking"
    assert body["currency"] == "CHF"
    assert body["iban"] is None
    assert isinstance(body["opening_balance"], str)
    assert isinstance(body["balance"], str)
    assert Decimal(body["opening_balance"]) == Decimal(0)
    assert Decimal(body["balance"]) == Decimal(0)
    assert saved_account.opening_date == date(2026, 10, 10)


@pytest.mark.parametrize("missing_field", ["name", "opening_date"])
async def test_create_account_rejects_missing_required_fields(
    client: AsyncClient, db_session: AsyncSession, missing_field: str
) -> None:
    test_account_json = {
        "name": "Daily spending",
        "opening_date": "2026-10-10",
    }
    del test_account_json[missing_field]

    response = await client.post("/api/v1/accounts", json=test_account_json)

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(error["loc"] == ["body", missing_field] and error["type"] == "missing" for error in errors)
    assert await db_session.scalar(select(func.count()).select_from(Account)) == 0


@pytest.mark.parametrize(
    "wrong_json_parameter, wrong_json_value, right_json_parameter, right_json_value",
    [
        ("name", 123, "opening_date", "2026-10-10"),
        ("opening_date", 123, "name", "Main Account"),
        ("name", None, "opening_date", "2026-10-10"),
        ("opening_date", None, "name", "Main Account"),
    ],
)
async def test_create_account_with_invalid_mandatory_fields(
    client: AsyncClient,
    db_session: AsyncSession,
    wrong_json_parameter: str,
    wrong_json_value: Any,
    right_json_parameter: str,
    right_json_value: Any,
) -> None:
    test_account_json = {
        wrong_json_parameter: wrong_json_value,
        right_json_parameter: right_json_value,
    }

    response = await client.post(url="/api/v1/accounts", json=test_account_json)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", wrong_json_parameter]
    assert await db_session.scalar(select(func.count()).select_from(Account)) == 0


async def test_create_account_rejects_empty_body(client: AsyncClient, db_session: AsyncSession) -> None:
    response = await client.post("/api/v1/accounts", json={})

    assert response.status_code == 422

    errors = response.json()["detail"]
    missing_fields = {tuple(error["loc"]) for error in errors if error["type"] == "missing"}
    assert missing_fields == {
        ("body", "name"),
        ("body", "opening_date"),
    }
    assert await db_session.scalar(select(func.count()).select_from(Account)) == 0


@pytest.mark.parametrize(
    "field, value",
    [
        pytest.param("name", "", id="empty-name"),
        pytest.param("name", "   ", id="spaces-only-name"),
        pytest.param("name", "\t\n", id="whitespace-only-name"),
        pytest.param("name", True, id="boolean-name"),
        pytest.param("name", [], id="array-name"),
        pytest.param("account_type", "house", id="unknown-account-type"),
        pytest.param("account_type", 123, id="numeric-account-type"),
        pytest.param("account_type", None, id="null-account-type"),
        pytest.param("currency", "", id="empty-currency"),
        pytest.param("currency", "CH", id="short-currency"),
        pytest.param("currency", "ZZZ", id="non-iso-currency"),
        pytest.param("currency", "CHFF", id="long-currency"),
        pytest.param("currency", "123", id="numeric-currency-code"),
        pytest.param("currency", 123, id="numeric-currency-value"),
        pytest.param("currency", None, id="null-currency"),
        pytest.param("iban", "not-an-iban", id="malformed-iban"),
        pytest.param("iban", "CH9300762011623852958", id="invalid-iban-checksum"),
        pytest.param("iban", "CH930076201162385295", id="invalid-iban-country-length"),
        pytest.param("iban", 123, id="numeric-iban"),
        pytest.param("opening_balance", None, id="null-balance"),
        pytest.param("opening_balance", 0, id="integer-balance"),
        pytest.param("opening_balance", 12.5, id="float-balance"),
        pytest.param("opening_balance", True, id="boolean-balance"),
        pytest.param("opening_balance", "", id="empty-balance"),
        pytest.param("opening_balance", "invalid", id="malformed-balance"),
        pytest.param("opening_balance", "NaN", id="nan-balance"),
        pytest.param("opening_balance", "Infinity", id="infinite-balance"),
        pytest.param("opening_balance", "-Infinity", id="negative-infinite-balance"),
        pytest.param("opening_date", "2026-02-30", id="impossible-date"),
        pytest.param("opening_date", "2025-02-29", id="non-leap-day"),
        pytest.param("opening_date", "2026-13-01", id="invalid-month"),
        pytest.param("opening_date", "10/10/2026", id="wrong-date-format"),
        pytest.param("opening_date", "20261010", id="compact-date"),
        pytest.param("opening_date", "2026-10-10T12:00:00Z", id="timestamp-as-date"),
        pytest.param("opening_date", "", id="empty-date"),
    ],
)
async def test_create_account_rejects_invalid_values_without_inserting(
    client: AsyncClient, db_session: AsyncSession, field: str, value: Any
) -> None:
    payload = {"name": "Rejected account", "opening_date": "2026-10-10", field: value}

    response = await client.post("/api/v1/accounts", json=payload)

    assert response.status_code == 422
    assert any(error["loc"] == ["body", field] for error in response.json()["detail"])
    assert await db_session.scalar(select(func.count()).select_from(Account)) == 0


@pytest.mark.parametrize(
    "field, supplied, normalized",
    [
        ("name", "  Daily spending  ", "Daily spending"),
        ("currency", " chf ", "CHF"),
        ("currency", " eur ", "EUR"),
        ("currency", " usd ", "USD"),
        ("iban", "ch93 0076 2011 6238 5295 7", "CH9300762011623852957"),
        ("iban", "de89 3704 0044 0532 0130 00", "DE89370400440532013000"),
        ("iban", "gb82 west 1234 5698 7654 32", "GB82WEST12345698765432"),
    ],
)
async def test_create_account_normalizes_input(
    client: AsyncClient, db_session: AsyncSession, field: str, supplied: str, normalized: str
) -> None:
    payload = {"name": "Daily spending", "opening_date": "2026-10-10", field: supplied}

    response = await client.post("/api/v1/accounts", json=payload)

    assert response.status_code == 201
    assert response.json()[field] == normalized
    saved_account = (await db_session.execute(select(Account))).scalar_one()
    assert getattr(saved_account, field) == normalized


@pytest.mark.parametrize("account_type", ["checking", "savings", "cash", "credit_card"])
async def test_create_account_accepts_supported_account_types(
    client: AsyncClient, db_session: AsyncSession, account_type: str
) -> None:
    response = await client.post(
        "/api/v1/accounts",
        json={"name": "Account", "opening_date": "2026-10-10", "account_type": account_type},
    )

    assert response.status_code == 201
    assert response.json()["account_type"] == account_type
    saved_account = (await db_session.execute(select(Account))).scalar_one()
    assert saved_account.account_type == account_type


@pytest.mark.parametrize("amount", ["0", "-1250.50", "+1250.50"])
async def test_create_account_accepts_zero_and_signed_balances(
    client: AsyncClient, db_session: AsyncSession, amount: str
) -> None:
    response = await client.post(
        "/api/v1/accounts",
        json={"name": "Account", "opening_date": "2026-10-10", "opening_balance": amount},
    )

    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["opening_balance"], str)
    assert isinstance(body["balance"], str)
    assert Decimal(body["opening_balance"]) == Decimal(amount)
    assert Decimal(body["balance"]) == Decimal(amount)
    saved_account = (await db_session.execute(select(Account))).scalar_one()
    assert saved_account.opening_balance == Decimal(amount)
    assert saved_account.balance == Decimal(amount)


async def test_create_account_accepts_leap_day(client: AsyncClient, db_session: AsyncSession) -> None:
    response = await client.post("/api/v1/accounts", json={"name": "Leap day", "opening_date": "2024-02-29"})

    assert response.status_code == 201
    assert response.json()["opening_date"] == "2024-02-29"
    saved_account = (await db_session.execute(select(Account))).scalar_one()
    assert saved_account.opening_date == date(2024, 2, 29)


async def test_create_account_assigns_distinct_ids(client: AsyncClient, db_session: AsyncSession) -> None:
    payload = {"name": "Account", "opening_date": "2026-10-10"}
    first = await client.post("/api/v1/accounts", json=payload)
    second = await client.post("/api/v1/accounts", json=payload)

    assert first.status_code == second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
    assert await db_session.scalar(select(func.count()).select_from(Account)) == 2


@pytest.mark.parametrize("name", ["A", "A" * 64, "é" * 64, "  " + "A" * 64 + "  "])
async def test_create_account_accepts_name_length_boundaries(
    client: AsyncClient, db_session: AsyncSession, name: str
) -> None:
    response = await client.post("/api/v1/accounts", json={"name": name, "opening_date": "2026-10-10"})

    assert response.status_code == 201
    assert response.json()["name"] == name.strip()
    saved_account = (await db_session.execute(select(Account))).scalar_one()
    assert saved_account.name == name.strip()


@pytest.mark.parametrize("name", ["A" * 65, "é" * 65, "  " + "A" * 65 + "  "])
async def test_create_account_rejects_names_over_64_characters(
    client: AsyncClient, db_session: AsyncSession, name: str
) -> None:
    response = await client.post("/api/v1/accounts", json={"name": name, "opening_date": "2026-10-10"})

    assert response.status_code == 422
    assert any(error["loc"] == ["body", "name"] for error in response.json()["detail"])
    assert await db_session.scalar(select(func.count()).select_from(Account)) == 0


@pytest.mark.parametrize(
    "amount",
    [
        "-1000000",
        "-1000000.00",
        "1000000",
        "1000000.00",
        "-999999.99",
        "999999.99",
        "0",
        "0.0",
        "0.00",
        "0.01",
        "-0.01",
        "1.2",
    ],
)
async def test_create_account_accepts_monetary_boundaries(
    client: AsyncClient, db_session: AsyncSession, amount: str
) -> None:
    response = await client.post(
        "/api/v1/accounts",
        json={"name": "Boundary", "opening_date": "2026-10-10", "opening_balance": amount},
    )

    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["opening_balance"], str)
    assert isinstance(body["balance"], str)
    assert Decimal(body["opening_balance"]) == Decimal(amount)
    assert Decimal(body["balance"]) == Decimal(amount)
    saved_account = (await db_session.execute(select(Account))).scalar_one()
    assert saved_account.opening_balance == Decimal(amount)
    assert saved_account.balance == Decimal(amount)


@pytest.mark.parametrize(
    "amount", ["-1000000.01", "1000000.01", "-1000001", "1000001", "0.001", "-0.001", "1250.501", "1.230"]
)
async def test_create_account_rejects_out_of_range_or_overprecise_money(
    client: AsyncClient, db_session: AsyncSession, amount: str
) -> None:
    response = await client.post(
        "/api/v1/accounts",
        json={"name": "Rejected", "opening_date": "2026-10-10", "opening_balance": amount},
    )

    assert response.status_code == 422
    assert any(error["loc"] == ["body", "opening_balance"] for error in response.json()["detail"])
    assert await db_session.scalar(select(func.count()).select_from(Account)) == 0


@pytest.mark.parametrize("body", [None, [], "account", 123])
async def test_create_account_rejects_non_object_bodies(
    client: AsyncClient, db_session: AsyncSession, body: Any
) -> None:
    response = await client.post("/api/v1/accounts", json=body)

    assert response.status_code == 422
    assert await db_session.scalar(select(func.count()).select_from(Account)) == 0


async def test_create_account_rejects_malformed_json(client: AsyncClient, db_session: AsyncSession) -> None:
    response = await client.post("/api/v1/accounts", content='{"name":', headers={"Content-Type": "application/json"})

    assert response.status_code == 422
    assert await db_session.scalar(select(func.count()).select_from(Account)) == 0


async def test_create_account_has_named_typed_response_schema(app: FastAPI) -> None:
    document = app.openapi()
    response_schema = document["paths"]["/api/v1/accounts"]["post"]["responses"]["201"]["content"]["application/json"][
        "schema"
    ]
    reference = response_schema["$ref"]
    schema = document["components"]["schemas"][reference.rsplit("/", 1)[1]]
    properties = schema["properties"]

    assert schema["title"] == "AccountResponse"
    assert set(properties) == {
        "id",
        "name",
        "account_type",
        "currency",
        "iban",
        "opening_balance",
        "balance",
        "opening_date",
        "created_at",
        "updated_at",
        "archived",
        "archived_at",
    }
    assert set(schema["required"]) == set(properties)
    assert properties["id"]["type"] == "string"
    assert properties["id"]["format"] == "uuid"
    for field in ("name", "account_type", "currency", "opening_balance", "balance"):
        assert properties[field]["type"] == "string"
    assert properties["opening_date"]["format"] == "date"
    for field in ("created_at", "updated_at"):
        assert properties[field]["type"] == "string"
        assert properties[field]["format"] == "date-time"
    assert properties["archived"]["type"] == "boolean"
    assert {option["type"] for option in properties["iban"]["anyOf"]} == {"string", "null"}
    assert {option["type"] for option in properties["archived_at"]["anyOf"]} == {"string", "null"}
    assert any(option.get("format") == "date-time" for option in properties["archived_at"]["anyOf"])


@pytest.mark.parametrize("currency", sorted(currency.alpha_3 for currency in pycountry.currencies))
def test_create_account_accepts_every_pycountry_currency(currency: str) -> None:
    request = AccountCreate(name="Account", opening_date="2026-10-10", currency=currency)

    assert request.currency == currency


@pytest.mark.parametrize("failure_point", ["before_flush", "after_flush"])
@pytest.mark.parametrize("database_unavailable, expected_status", [(True, 503), (False, 500)])
async def test_create_account_rolls_back_database_failures_without_leaking_details(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    failure_point: str,
    database_unavailable: bool,
    expected_status: int,
) -> None:
    existing = Account(
        name="Existing account",
        opening_date=date(2026, 10, 10),
        opening_balance=Decimal(25),
        balance=Decimal(25),
    )
    db_session.add(existing)
    await db_session.commit()
    existing_id = existing.id
    sensitive_details = "host=private-db port=5432 user=secret-user password=secret-password"

    async def fail_write() -> None:
        if database_unavailable:
            raise OperationalError("INSERT INTO accounts", {}, OSError(sensitive_details))
        raise SQLAlchemyError(sensitive_details)

    rollback = AsyncMock(wraps=db_session.rollback)
    with monkeypatch.context() as patch:
        # Fail either before insertion or after the handler has flushed its row.
        failing_method = "flush" if failure_point == "before_flush" else "commit"
        patch.setattr(db_session, failing_method, fail_write)
        patch.setattr(db_session, "rollback", rollback)
        response = await client.post(
            "/api/v1/accounts",
            json={"name": "Failed account", "opening_date": "2026-10-10"},
        )
        assert response.status_code == expected_status
        rollback.assert_awaited_once()

    assert "location" not in response.headers
    for secret in ("private-db", "5432", "secret-user", "secret-password", "INSERT INTO", "Traceback"):
        assert secret not in response.text
    accounts = (await db_session.execute(select(Account))).scalars().all()
    assert [account.id for account in accounts] == [existing_id]

    # Prove rollback restored a usable session and a retry creates one row.
    retry = await client.post("/api/v1/accounts", json={"name": "Failed account", "opening_date": "2026-10-10"})
    assert retry.status_code == 201
    assert (
        await db_session.scalar(select(func.count()).select_from(Account).where(Account.name == "Failed account")) == 1
    )


async def test_create_account_response_validation_failure_rolls_back_insert(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    existing = Account(
        name="Existing account",
        opening_date=date(2026, 10, 10),
        opening_balance=Decimal(25),
        balance=Decimal(25),
    )
    db_session.add(existing)
    await db_session.commit()
    existing_id = existing.id
    private_name = "private-financial-name"
    with pytest.raises(ValidationError) as validation:
        AccountResponse.model_validate({"name": private_name})

    failed_response = Mock(side_effect=validation.value)
    flush = AsyncMock(wraps=db_session.flush)
    commit = AsyncMock(wraps=db_session.commit)
    rollback = AsyncMock(wraps=db_session.rollback)
    with monkeypatch.context() as patch:
        patch.setattr(AccountResponse, "model_validate", failed_response)
        patch.setattr(db_session, "flush", flush)
        patch.setattr(db_session, "commit", commit)
        patch.setattr(db_session, "rollback", rollback)
        response = await client.post("/api/v1/accounts", json={"name": "Failed account", "opening_date": "2026-10-10"})
        assert response.status_code == 500
        assert response.json() == {"detail": "Validating the Datamodel failed"}
        flush.assert_awaited_once()
        failed_response.assert_called_once()
        commit.assert_not_awaited()
        rollback.assert_awaited_once()

    assert "location" not in response.headers
    assert private_name not in response.text
    assert "Traceback" not in response.text
    accounts = (await db_session.execute(select(Account))).scalars().all()
    assert [account.id for account in accounts] == [existing_id]
    retry = await client.post("/api/v1/accounts", json={"name": "Failed account", "opening_date": "2026-10-10"})
    assert retry.status_code == 201
    assert await db_session.scalar(select(func.count()).select_from(Account)) == 2
