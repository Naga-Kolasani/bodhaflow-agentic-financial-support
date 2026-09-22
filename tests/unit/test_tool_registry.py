from typing import Any

import pytest

from bodhaflow.tools import AllowedToolName
from bodhaflow.tools import get_allowed_tool as package_get_allowed_tool
from bodhaflow.tools.card_transaction_lookup import get_card_transaction_for_customer
from bodhaflow.tools.registry import get_allowed_tool


def test_registry_resolves_approved_tool_name() -> None:
    resolved = get_allowed_tool("get_card_transaction_for_customer")

    assert resolved is get_card_transaction_for_customer


def test_package_export_is_same_object_as_registry_function() -> None:
    assert package_get_allowed_tool is get_allowed_tool


def test_allowed_tool_name_literal_resolves_to_approved_tool() -> None:
    allowed_name: AllowedToolName = "get_card_transaction_for_customer"
    resolved = get_allowed_tool(allowed_name)

    assert resolved is get_card_transaction_for_customer


@pytest.mark.parametrize(
    "name",
    [
        "unknown_tool",
        "",
        "   ",
        "bodhaflow.tools.card_transaction_lookup.get_card_transaction_for_customer",
        "__import__('os').system('echo unsafe')",
    ],
)
def test_registry_returns_none_for_unknown_string_names(name: str) -> None:
    assert get_allowed_tool(name) is None


@pytest.mark.parametrize("name", [None, 0, [], {}, object()])
def test_registry_returns_none_for_non_string_values(name: Any) -> None:
    assert get_allowed_tool(name) is None
