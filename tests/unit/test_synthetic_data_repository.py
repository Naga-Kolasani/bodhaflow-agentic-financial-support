import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from bodhaflow.domain.models import CardTransaction, CardTransactionStatus
from bodhaflow.repositories import synthetic_data
from bodhaflow.repositories.synthetic_data import SyntheticDataRepository


def test_get_customer_returns_known_customer() -> None:
    repository = SyntheticDataRepository()

    customer = repository.get_customer("cust_001")

    assert customer is not None
    assert customer.display_name == "Avery Stone"


def test_get_customer_returns_none_for_unknown_id() -> None:
    repository = SyntheticDataRepository()

    assert repository.get_customer("cust_missing") is None


def test_get_card_transaction_returns_known_transaction() -> None:
    repository = SyntheticDataRepository()

    transaction = repository.get_card_transaction("txn_001")

    assert transaction is not None
    assert transaction.customer_id == "cust_001"
    assert transaction.status == CardTransactionStatus.PENDING


def test_get_card_transaction_returns_none_for_unknown_id() -> None:
    repository = SyntheticDataRepository()

    assert repository.get_card_transaction("txn_missing") is None


def test_list_card_transactions_for_customer_preserves_source_order() -> None:
    repository = SyntheticDataRepository()

    transactions = repository.list_card_transactions_for_customer("cust_001")

    assert [transaction.transaction_id for transaction in transactions] == [
        "txn_001",
        "txn_002",
    ]
    assert all(isinstance(transaction, CardTransaction) for transaction in transactions)


def test_list_card_transactions_for_customer_returns_empty_for_unknown_id() -> None:
    repository = SyntheticDataRepository()

    assert repository.list_card_transactions_for_customer("cust_missing") == []


def _write_json(path: Path, payload: object) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle)


def test_missing_customers_file_raises_file_not_found_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(synthetic_data, "CUSTOMERS_PATH", tmp_path / "customers.json")
    monkeypatch.setattr(
        synthetic_data, "CARD_TRANSACTIONS_PATH", tmp_path / "card_transactions.json"
    )

    with pytest.raises(FileNotFoundError):
        SyntheticDataRepository()


def test_non_list_customers_payload_raises_value_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    customers_path = tmp_path / "customers.json"
    transactions_path = tmp_path / "card_transactions.json"
    _write_json(customers_path, {"not": "a list"})
    _write_json(transactions_path, [])

    monkeypatch.setattr(synthetic_data, "CUSTOMERS_PATH", customers_path)
    monkeypatch.setattr(synthetic_data, "CARD_TRANSACTIONS_PATH", transactions_path)

    with pytest.raises(ValueError):
        SyntheticDataRepository()


def test_duplicate_customer_ids_raise_value_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    customers_path = tmp_path / "customers.json"
    transactions_path = tmp_path / "card_transactions.json"
    _write_json(
        customers_path,
        [
            {"customer_id": "cust_fx1", "display_name": "Fixture One"},
            {"customer_id": "cust_fx1", "display_name": "Fixture Two"},
        ],
    )
    _write_json(
        transactions_path,
        [
            {
                "transaction_id": "txn_fx1",
                "customer_id": "cust_fx1",
                "merchant_name": "Fixture Merchant",
                "amount_minor": 500,
                "currency": "USD",
                "status": "pending",
                "created_at": "2026-01-01T00:00:00Z",
            }
        ],
    )

    monkeypatch.setattr(synthetic_data, "CUSTOMERS_PATH", customers_path)
    monkeypatch.setattr(synthetic_data, "CARD_TRANSACTIONS_PATH", transactions_path)

    with pytest.raises(ValueError):
        SyntheticDataRepository()


def test_duplicate_transaction_ids_raise_value_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    customers_path = tmp_path / "customers.json"
    transactions_path = tmp_path / "card_transactions.json"
    _write_json(
        customers_path,
        [{"customer_id": "cust_fx1", "display_name": "Fixture One"}],
    )
    _write_json(
        transactions_path,
        [
            {
                "transaction_id": "txn_fx1",
                "customer_id": "cust_fx1",
                "merchant_name": "Fixture Merchant",
                "amount_minor": 500,
                "currency": "USD",
                "status": "pending",
                "created_at": "2026-01-01T00:00:00Z",
            },
            {
                "transaction_id": "txn_fx1",
                "customer_id": "cust_fx1",
                "merchant_name": "Fixture Merchant Two",
                "amount_minor": 700,
                "currency": "USD",
                "status": "completed",
                "created_at": "2026-01-02T00:00:00Z",
            },
        ],
    )

    monkeypatch.setattr(synthetic_data, "CUSTOMERS_PATH", customers_path)
    monkeypatch.setattr(synthetic_data, "CARD_TRANSACTIONS_PATH", transactions_path)

    with pytest.raises(ValueError):
        SyntheticDataRepository()


def test_transaction_with_unknown_customer_raises_value_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    customers_path = tmp_path / "customers.json"
    transactions_path = tmp_path / "card_transactions.json"
    _write_json(
        customers_path,
        [{"customer_id": "cust_fx1", "display_name": "Fixture One"}],
    )
    _write_json(
        transactions_path,
        [
            {
                "transaction_id": "txn_fx1",
                "customer_id": "cust_unknown",
                "merchant_name": "Fixture Merchant",
                "amount_minor": 500,
                "currency": "USD",
                "status": "pending",
                "created_at": "2026-01-01T00:00:00Z",
            }
        ],
    )

    monkeypatch.setattr(synthetic_data, "CUSTOMERS_PATH", customers_path)
    monkeypatch.setattr(synthetic_data, "CARD_TRANSACTIONS_PATH", transactions_path)

    with pytest.raises(ValueError):
        SyntheticDataRepository()


def test_customer_with_no_transactions_raises_value_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    customers_path = tmp_path / "customers.json"
    transactions_path = tmp_path / "card_transactions.json"
    _write_json(
        customers_path,
        [{"customer_id": "cust_fx1", "display_name": "Fixture One"}],
    )
    _write_json(transactions_path, [])

    monkeypatch.setattr(synthetic_data, "CUSTOMERS_PATH", customers_path)
    monkeypatch.setattr(synthetic_data, "CARD_TRANSACTIONS_PATH", transactions_path)

    with pytest.raises(ValueError):
        SyntheticDataRepository()


def test_schema_invalid_transaction_raises_validation_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    customers_path = tmp_path / "customers.json"
    transactions_path = tmp_path / "card_transactions.json"
    _write_json(
        customers_path,
        [{"customer_id": "cust_fx1", "display_name": "Fixture One"}],
    )
    _write_json(
        transactions_path,
        [
            {
                "transaction_id": "txn_fx1",
                "customer_id": "cust_fx1",
                "merchant_name": "Fixture Merchant",
                "amount_minor": 0,
                "currency": "USD",
                "status": "pending",
                "created_at": "2026-01-01T00:00:00Z",
            }
        ],
    )

    monkeypatch.setattr(synthetic_data, "CUSTOMERS_PATH", customers_path)
    monkeypatch.setattr(synthetic_data, "CARD_TRANSACTIONS_PATH", transactions_path)

    with pytest.raises(ValidationError):
        SyntheticDataRepository()


def test_malformed_customers_json_raises_json_decode_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    customers_path = tmp_path / "customers.json"
    transactions_path = tmp_path / "card_transactions.json"
    customers_path.write_text("{not valid json", encoding="utf-8")
    _write_json(transactions_path, [])

    monkeypatch.setattr(synthetic_data, "CUSTOMERS_PATH", customers_path)
    monkeypatch.setattr(
        synthetic_data,
        "CARD_TRANSACTIONS_PATH",
        transactions_path,
    )

    with pytest.raises(json.JSONDecodeError):
        SyntheticDataRepository()
