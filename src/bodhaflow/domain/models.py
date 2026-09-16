from datetime import datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
PositiveMinorAmount = Annotated[int, Field(strict=True, gt=0)]


class Customer(BaseModel):
    customer_id: NonEmptyText
    display_name: NonEmptyText


class CardTransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    DECLINED = "declined"
    REVERSED = "reversed"


class CardTransaction(BaseModel):
    transaction_id: NonEmptyText
    customer_id: NonEmptyText
    merchant_name: NonEmptyText
    amount_minor: PositiveMinorAmount
    currency: Literal["USD"]
    status: CardTransactionStatus
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def reject_naive_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        return value
