import pytest
from pydantic import ValidationError

from bodhaflow.domain.models import CardTransaction
from bodhaflow.repositories.synthetic_data import SyntheticDataRepository
from bodhaflow.tools.card_transaction_lookup import (
    CardTransactionLookupInput,
    CustomerNotFound,
    TransactionFound,
    TransactionNotFound,
    UnauthorizedTransactionAccess,
    get_card_transaction_for_customer,
)


def test_owned_lookup_returns_transaction_found() -> None:
    repository = SyntheticDataRepository()
    request = CardTransactionLookupInput(
        customer_id="cust_001",
        transaction_id="txn_001",
    )

    result = get_card_transaction_for_customer(request, repository)

    assert isinstance(result, TransactionFound)
    assert result.outcome == "found"
    assert isinstance(result.transaction, CardTransaction)
    assert result.transaction.transaction_id == "txn_001"


def test_unknown_customer_returns_customer_not_found() -> None:
    repository = SyntheticDataRepository()
    request = CardTransactionLookupInput(
        customer_id="cust_missing",
        transaction_id="txn_001",
    )

    result = get_card_transaction_for_customer(request, repository)

    assert isinstance(result, CustomerNotFound)
    assert result.outcome == "customer_not_found"
    assert not hasattr(result, "transaction")


def test_unknown_transaction_returns_transaction_not_found() -> None:
    repository = SyntheticDataRepository()
    request = CardTransactionLookupInput(
        customer_id="cust_001",
        transaction_id="txn_missing",
    )

    result = get_card_transaction_for_customer(request, repository)

    assert isinstance(result, TransactionNotFound)
    assert result.outcome == "transaction_not_found"
    assert not hasattr(result, "transaction")


def test_cross_customer_lookup_returns_unauthorized() -> None:
    repository = SyntheticDataRepository()
    request = CardTransactionLookupInput(
        customer_id="cust_001",
        transaction_id="txn_003",
    )

    result = get_card_transaction_for_customer(request, repository)

    assert isinstance(result, UnauthorizedTransactionAccess)
    assert result.outcome == "unauthorized"
    assert not hasattr(result, "transaction")


def test_input_is_stripped_and_owned_lookup_still_succeeds() -> None:
    repository = SyntheticDataRepository()
    request = CardTransactionLookupInput(
        customer_id="  cust_001  ",
        transaction_id="  txn_001  ",
    )

    result = get_card_transaction_for_customer(request, repository)

    assert request.customer_id == "cust_001"
    assert request.transaction_id == "txn_001"
    assert isinstance(result, TransactionFound)


@pytest.mark.parametrize("customer_id", ["", "   "])
def test_input_rejects_invalid_customer_id(customer_id: str) -> None:
    with pytest.raises(ValidationError):
        CardTransactionLookupInput(
            customer_id=customer_id,
            transaction_id="txn_001",
        )


@pytest.mark.parametrize("transaction_id", ["", "   "])
def test_input_rejects_invalid_transaction_id(transaction_id: str) -> None:
    with pytest.raises(ValidationError):
        CardTransactionLookupInput(
            customer_id="cust_001",
            transaction_id=transaction_id,
        )
