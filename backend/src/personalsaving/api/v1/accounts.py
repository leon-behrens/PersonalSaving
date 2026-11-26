from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated, Literal
from uuid import UUID

import pycountry
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from stdnum import iban
from stdnum.exceptions import ValidationError as NumberValidationError

from personalsaving.database import get_db
from personalsaving.models import Account


class AccountCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    account_type: Literal["checking", "savings", "cash", "credit_card"] = "checking"
    currency: str = "CHF"
    iban: str | None = None
    opening_balance: str = "0"
    opening_date: str

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:  # Checks if name is empty
            raise ValueError("Name must not be blank")
        if len(value) > 64:
            raise ValueError("Name must not exceed 64 characters")
        return value

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if pycountry.currencies.get(alpha_3=value) is None:
            raise ValueError("Currency must be a recognized ISO 4217 code")
        return value

    @field_validator("iban")
    @classmethod
    def normalize_iban(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.replace(" ", "").upper()
        try:
            return iban.validate(value, check_country=True)
        except NumberValidationError as exc:
            raise ValueError("IBAN must have a valid country format and checksum") from exc

    @field_validator("opening_date")
    @classmethod
    def normalize_opening_date(cls, value: str) -> str:
        parsed_date = date.fromisoformat(value)
        if parsed_date.isoformat() != value:
            raise ValueError("Opening date must use YYYY-MM-DD")
        return value

    @field_validator("opening_balance")
    @classmethod
    def normalize_opening_balance(cls, value: str) -> str:
        try:
            parsed_balance = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError("Opening balance must be a valid decimal number") from exc
        if not parsed_balance.is_finite():
            raise ValueError("Opening balance must not be infinite or NaN")
        if parsed_balance < Decimal(-1000000) or parsed_balance > Decimal(1000000):
            raise ValueError("Opening balance must be between -1000000 and 1000000")
        if int(parsed_balance.as_tuple().exponent) < -2:
            raise ValueError("Opening balance must have at most two fractional digits")

        return value


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    account_type: Literal["checking", "savings", "cash", "credit_card"]
    currency: str
    iban: str | None
    opening_balance: Decimal
    opening_date: date
    balance: Decimal
    archived: bool
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


router = APIRouter()


@router.post(
    "/accounts",
    status_code=201,
)
async def create_account(
    db: Annotated[AsyncSession, Depends(get_db)], account: AccountCreate, response: Response
) -> AccountResponse:

    new_account = Account(
        name=account.name,
        account_type=account.account_type,
        currency=account.currency,
        iban=account.iban,
        opening_balance=Decimal(account.opening_balance),
        opening_date=date.fromisoformat(account.opening_date),
        balance=Decimal(account.opening_balance),
    )

    try:
        db.add(new_account)
        await db.flush()
        result = AccountResponse.model_validate(new_account)
        await db.commit()
    except OperationalError as exc:
        await db.rollback()
        raise HTTPException(status_code=503, detail="Database operation failed") from exc
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database operation failed") from exc
    except ValidationError as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Validating the Datamodel failed") from exc
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Some unidentified error occured") from exc

    response.headers["location"] = f"/api/v1/accounts/{new_account.id}"

    return result
