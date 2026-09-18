import json
from pathlib import Path
from typing import Any

from bodhaflow.domain.models import CardTransaction, Customer

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIRECTORY = REPO_ROOT / "data" / "synthetic"
CUSTOMERS_PATH = DATA_DIRECTORY / "customers.json"
CARD_TRANSACTIONS_PATH = DATA_DIRECTORY / "card_transactions.json"


def _load_json_array(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON array")
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError(f"{path} must contain only JSON objects")
    return payload


class SyntheticDataRepository:
    def __init__(self) -> None:
        raw_customers = _load_json_array(CUSTOMERS_PATH)
        raw_transactions = _load_json_array(CARD_TRANSACTIONS_PATH)

        customers = [Customer.model_validate(item) for item in raw_customers]
        transactions = [CardTransaction.model_validate(item) for item in raw_transactions]

        customers_by_id: dict[str, Customer] = {}
        for customer in customers:
            if customer.customer_id in customers_by_id:
                raise ValueError(f"duplicate customer_id: {customer.customer_id}")
            customers_by_id[customer.customer_id] = customer

        transactions_by_id: dict[str, CardTransaction] = {}
        for transaction in transactions:
            if transaction.transaction_id in transactions_by_id:
                raise ValueError(f"duplicate transaction_id: {transaction.transaction_id}")
            transactions_by_id[transaction.transaction_id] = transaction
            if transaction.customer_id not in customers_by_id:
                raise ValueError(
                    f"transaction {transaction.transaction_id} references "
                    f"unknown customer_id: {transaction.customer_id}"
                )

        customer_ids_with_transactions = {
            transaction.customer_id for transaction in transactions
        }
        for customer_id in customers_by_id:
            if customer_id not in customer_ids_with_transactions:
                raise ValueError(f"customer {customer_id} has no transactions")

        self._customers_by_id = customers_by_id
        self._transactions_by_id = transactions_by_id
        self._transactions_in_order: tuple[CardTransaction, ...] = tuple(transactions)

    def get_customer(self, customer_id: str) -> Customer | None:
        return self._customers_by_id.get(customer_id)

    def get_card_transaction(self, transaction_id: str) -> CardTransaction | None:
        return self._transactions_by_id.get(transaction_id)

    def list_card_transactions_for_customer(self, customer_id: str) -> list[CardTransaction]:
        return [
            transaction
            for transaction in self._transactions_in_order
            if transaction.customer_id == customer_id
        ]
