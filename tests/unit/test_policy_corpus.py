from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
POLICIES_DIR = REPO_ROOT / "data" / "policies"

EXPECTED_TITLES: dict[str, str] = {
    "pending_card_payment.md": "# Pending card payment",
    "declined_card_payment.md": "# Declined card payment",
    "duplicate_charge.md": "# Duplicate charge",
    "unrecognized_transaction.md": "# Unrecognized transaction",
    "transfer_pending_or_not_received.md": "# Transfer pending or not received",
}

EXPECTED_FILENAMES: frozenset[str] = frozenset(EXPECTED_TITLES)

REQUIRED_HEADINGS: list[str] = [
    "## Purpose",
    "## When it applies",
    "## Required information",
    "## Safe guidance",
    "## Approved future mock lookup",
    "## Mandatory escalation conditions",
]

DISCLAIMER = (
    "This is an original fictional BodhaFlow policy for synthetic-data "
    "demonstrations. It does not describe real financial services or "
    "authorize real financial actions."
)

EM_DASH = "\u2014"

UNRECOGNIZED_ESCALATION_SENTENCE = (
    "Escalate every unrecognized-transaction request immediately."
)

TRANSFER_UNSUPPORTED_SENTENCE = (
    "The current approved mock lookup does not support transfers."
)


def read_policy(filename: str) -> str:
    return (POLICIES_DIR / filename).read_text(encoding="utf-8")


def test_policies_directory_exists() -> None:
    assert POLICIES_DIR.is_dir()


def test_policy_filenames_match_expected_set() -> None:
    actual_filenames = {path.name for path in POLICIES_DIR.glob("*.md")}

    assert actual_filenames == EXPECTED_FILENAMES


def test_policy_files_are_non_empty() -> None:
    for filename in EXPECTED_FILENAMES:
        assert read_policy(filename).strip()


def test_policy_titles_match_expected() -> None:
    for filename, expected_title in EXPECTED_TITLES.items():
        assert read_policy(filename).splitlines()[0] == expected_title


def test_required_headings_appear_once_and_in_order() -> None:
    for filename in EXPECTED_FILENAMES:
        lines = read_policy(filename).splitlines()

        for heading in REQUIRED_HEADINGS:
            assert lines.count(heading) == 1

        positions = [lines.index(heading) for heading in REQUIRED_HEADINGS]

        assert positions == sorted(positions)


def test_disclaimer_appears_exactly_once_per_policy() -> None:
    for filename in EXPECTED_FILENAMES:
        assert read_policy(filename).count(DISCLAIMER) == 1


def test_no_em_dash_in_policy_corpus() -> None:
    for filename in EXPECTED_FILENAMES:
        assert EM_DASH not in read_policy(filename)


def test_unrecognized_transaction_has_immediate_escalation_sentence() -> None:
    assert UNRECOGNIZED_ESCALATION_SENTENCE in read_policy(
        "unrecognized_transaction.md"
    )


def test_transfer_policy_has_unsupported_lookup_sentence() -> None:
    assert TRANSFER_UNSUPPORTED_SENTENCE in read_policy(
        "transfer_pending_or_not_received.md"
    )
