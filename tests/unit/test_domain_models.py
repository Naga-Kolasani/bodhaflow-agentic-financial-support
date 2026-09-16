from datetime import datetime, timezone
from typing import Any

import pytest
from pydantic import ValidationError

from bodhaflow.domain.models import CardTransaction, CardTransactionStatus, Customer


def test_customer_accepts_valid_values_and_strips_whitespace() -> None:
    customer = Customer(customer_id="  cust-001  ", display_name="  Jane Doe  ")

    assert customer.customer_id == "cust-001"
    assert customer.display_name == "Jane Doe"


@pytest.mark.parametrize("customer_id", ["", "   "])
def test_customer_rejects_invalid_customer_id(customer_id: str) -> None:
    with pytest.raises(ValidationError):
        Customer(customer_id=customer_id, display_name="Jane Doe")


@pytest.mark.parametrize("display_name", ["", "   "])
def test_customer_rejects_invalid_display_name(display_name: str) -> None:
    with pytest.raises(ValidationError):
        Customer(customer_id="cust-001", display_name=display_name)


def valid_transaction_kwargs(**overrides: Any) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "transaction_id": "  txn-001  ",
        "customer_id": "  cust-001  ",
        "merchant_name": "  Fictional Coffee Co  ",
        "amount_minor": 1299,
        "currency": "USD",
        "status": "pending",
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }
    kwargs.update(overrides)
    return kwargs


def test_card_transaction_accepts_valid_timezone_aware_transaction() -> None:
    transaction = CardTransaction(**valid_transaction_kwargs())

    assert transaction.status == CardTransactionStatus.PENDING


def test_card_transaction_strips_text_fields() -> None:
    transaction = CardTransaction(**valid_transaction_kwargs())

    assert transaction.transaction_id == "txn-001"
    assert transaction.customer_id == "cust-001"
    assert transaction.merchant_name == "Fictional Coffee Co"


@pytest.mark.parametrize("amount_minor", [0, -100, 12.99, "1299", True])
def test_card_transaction_rejects_invalid_amount_minor(amount_minor: Any) -> None:
    with pytest.raises(ValidationError):
        CardTransaction(**valid_transaction_kwargs(amount_minor=amount_minor))


def test_card_transaction_rejects_non_usd_currency() -> None:
    with pytest.raises(ValidationError):
        CardTransaction(**valid_transaction_kwargs(currency="EUR"))


def test_card_transaction_rejects_unsupported_status() -> None:
    with pytest.raises(ValidationError):
        CardTransaction(**valid_transaction_kwargs(status="refunded"))


def test_card_transaction_rejects_naive_datetime() -> None:
    with pytest.raises(ValidationError):
        CardTransaction(**valid_transaction_kwargs(created_at=datetime(2026, 1, 1)))
