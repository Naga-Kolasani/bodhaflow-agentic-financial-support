from typing import Callable, Literal

from bodhaflow.repositories.synthetic_data import SyntheticDataRepository
from bodhaflow.tools.card_transaction_lookup import (
    CardTransactionLookupInput,
    CardTransactionLookupResult,
    get_card_transaction_for_customer,
)

AllowedToolName = Literal["get_card_transaction_for_customer"]

ToolCallable = Callable[
    [CardTransactionLookupInput, SyntheticDataRepository],
    CardTransactionLookupResult,
]

_ALLOWED_TOOLS: dict[AllowedToolName, ToolCallable] = {
    "get_card_transaction_for_customer": get_card_transaction_for_customer,
}


def get_allowed_tool(name: object) -> ToolCallable | None:
    if not isinstance(name, str):
        return None
    return _ALLOWED_TOOLS.get(name)
