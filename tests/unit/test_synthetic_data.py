import json
from collections import Counter
from pathlib import Path
from typing import Any

from bodhaflow.domain.models import CardTransaction, Customer

REPO_ROOT = Path(__file__).resolve().parents[2]
CUSTOMERS_PATH = REPO_ROOT / "data" / "synthetic" / "customers.json"
TRANSACTIONS_PATH = REPO_ROOT / "data" / "synthetic" / "card_transactions.json"


def load_json_objects(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        data: Any = json.load(handle)

    assert isinstance(data, list)
    assert all(isinstance(item, dict) for item in data)

    return data


def load_customers() -> list[Customer]:
    return [Customer.model_validate(record) for record in load_json_objects(CUSTOMERS_PATH)]


def load_transactions() -> list[CardTransaction]:
    return [
        CardTransaction.model_validate(record)
        for record in load_json_objects(TRANSACTIONS_PATH)
    ]


def test_synthetic_data_counts() -> None:
    assert len(load_customers()) == 3
    assert len(load_transactions()) == 6


def test_customer_ids_are_unique() -> None:
    customer_ids = [customer.customer_id for customer in load_customers()]

    assert len(customer_ids) == len(set(customer_ids))


def test_transaction_ids_are_unique() -> None:
    transaction_ids = [transaction.transaction_id for transaction in load_transactions()]

    assert len(transaction_ids) == len(set(transaction_ids))


def test_every_transaction_references_a_known_customer() -> None:
    customer_ids = {customer.customer_id for customer in load_customers()}
    transaction_customer_ids = {
        transaction.customer_id for transaction in load_transactions()
    }

    assert transaction_customer_ids.issubset(customer_ids)


def test_every_customer_has_at_least_one_transaction() -> None:
    customer_ids = {customer.customer_id for customer in load_customers()}
    transaction_customer_ids = {
        transaction.customer_id for transaction in load_transactions()
    }

    assert customer_ids.issubset(transaction_customer_ids)


def test_transaction_status_counts_match_expected_distribution() -> None:
    status_counts = Counter(transaction.status.value for transaction in load_transactions())

    assert status_counts == {
        "pending": 2,
        "completed": 2,
        "declined": 1,
        "reversed": 1,
    }
