from typing import Annotated, Literal

from pydantic import BaseModel, Field

from bodhaflow.domain.models import CardTransaction, NonEmptyText
from bodhaflow.repositories.synthetic_data import SyntheticDataRepository


class CardTransactionLookupInput(BaseModel):
    customer_id: NonEmptyText
    transaction_id: NonEmptyText


class TransactionFound(BaseModel):
    outcome: Literal["found"]
    transaction: CardTransaction


class CustomerNotFound(BaseModel):
    outcome: Literal["customer_not_found"]


class TransactionNotFound(BaseModel):
    outcome: Literal["transaction_not_found"]


class UnauthorizedTransactionAccess(BaseModel):
    outcome: Literal["unauthorized"]


CardTransactionLookupResult = Annotated[
    TransactionFound
    | CustomerNotFound
    | TransactionNotFound
    | UnauthorizedTransactionAccess,
    Field(discriminator="outcome"),
]


def get_card_transaction_for_customer(
    request: CardTransactionLookupInput,
    repository: SyntheticDataRepository,
) -> CardTransactionLookupResult:
    customer = repository.get_customer(request.customer_id)
    if customer is None:
        return CustomerNotFound(outcome="customer_not_found")

    transaction = repository.get_card_transaction(request.transaction_id)
    if transaction is None:
        return TransactionNotFound(outcome="transaction_not_found")

    if transaction.customer_id != request.customer_id:
        return UnauthorizedTransactionAccess(outcome="unauthorized")

    return TransactionFound(outcome="found", transaction=transaction)
