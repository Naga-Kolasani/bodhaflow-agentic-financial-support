"""Check policy chunk metadata, ordering, validation, and text preservation.

Read the committed corpus for source checks. Use temporary files for
malformed documents without changing the original policies.
"""

from pathlib import Path

import pytest

from bodhaflow.rag import policy_chunks
from bodhaflow.rag.policy_chunks import PolicyChunk, load_policy_chunks

EXPECTED_FILE_ORDER: tuple[str, ...] = (
    "declined_card_payment.md",
    "duplicate_charge.md",
    "pending_card_payment.md",
    "transfer_pending_or_not_received.md",
    "unrecognized_transaction.md",
)

EXPECTED_TITLES: dict[str, str] = {
    "declined_card_payment.md": "Declined card payment",
    "duplicate_charge.md": "Duplicate charge",
    "pending_card_payment.md": "Pending card payment",
    "transfer_pending_or_not_received.md": "Transfer pending or not received",
    "unrecognized_transaction.md": "Unrecognized transaction",
}

EXPECTED_SECTION_HEADINGS: tuple[str, ...] = (
    "Purpose",
    "When it applies",
    "Required information",
    "Safe guidance",
    "Approved future mock lookup",
    "Mandatory escalation conditions",
)

EXPECTED_SECTION_IDS: tuple[str, ...] = (
    "purpose",
    "when_it_applies",
    "required_information",
    "safe_guidance",
    "approved_future_mock_lookup",
    "mandatory_escalation_conditions",
)

_SECTION_BODY_TEMPLATE = (
    "This is original fictional synthetic text for the {heading} section."
)


def _section_block(heading: str) -> str:
    return f"## {heading}\n\n{_SECTION_BODY_TEMPLATE.format(heading=heading)}\n\n"


def _build_valid_policy_text(title: str) -> str:
    lines: list[str] = [f"# {title}", ""]
    for heading in EXPECTED_SECTION_HEADINGS:
        lines.append(f"## {heading}")
        lines.append("")
        lines.append(_SECTION_BODY_TEMPLATE.format(heading=heading))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _write_valid_corpus(directory: Path) -> None:
    for filename, title in EXPECTED_TITLES.items():
        (directory / filename).write_text(
            _build_valid_policy_text(title),
            encoding="utf-8",
        )


# Check the committed policy corpus.


def test_load_policy_chunks_returns_thirty_chunks() -> None:
    chunks = load_policy_chunks()

    assert len(chunks) == 30
    assert all(isinstance(chunk, PolicyChunk) for chunk in chunks)


def test_all_chunk_ids_are_unique() -> None:
    chunks = load_policy_chunks()
    ids = [chunk.chunk_id for chunk in chunks]

    assert len(ids) == len(set(ids))


def test_chunks_follow_alphabetical_document_and_section_order() -> None:
    chunks = load_policy_chunks()

    expected_ids: list[str] = []
    for filename in EXPECTED_FILE_ORDER:
        stem = filename.removesuffix(".md")
        for section_id in EXPECTED_SECTION_IDS:
            expected_ids.append(f"{stem}:{section_id}")

    actual_ids = [chunk.chunk_id for chunk in chunks]
    assert actual_ids == expected_ids


def test_representative_chunk_matches_source_file() -> None:
    chunks = load_policy_chunks()
    target = next(
        chunk
        for chunk in chunks
        if chunk.chunk_id == "pending_card_payment:safe_guidance"
    )

    repo_root = Path(__file__).resolve().parents[2]
    source_file = repo_root / "data" / "policies" / "pending_card_payment.md"
    lines = source_file.read_text(encoding="utf-8").splitlines()

    heading_index = lines.index("## Safe guidance")
    next_heading_index = lines.index("## Approved future mock lookup")
    expected_body = "\n".join(
        lines[heading_index + 1 : next_heading_index]
    ).strip()

    assert target.source_path == "data/policies/pending_card_payment.md"
    assert target.document_title == "Pending card payment"
    assert target.section_heading == "Safe guidance"
    assert target.text == expected_body


def test_loading_is_repeatable() -> None:
    first = load_policy_chunks()
    second = load_policy_chunks()

    first_dump = [chunk.model_dump() for chunk in first]
    second_dump = [chunk.model_dump() for chunk in second]
    assert first_dump == second_dump


# Check malformed policies using temporary files.


def test_missing_file_raises_file_not_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_valid_corpus(tmp_path)
    (tmp_path / "declined_card_payment.md").unlink()
    monkeypatch.setattr(policy_chunks, "_POLICY_DIR", tmp_path)

    with pytest.raises(FileNotFoundError):
        load_policy_chunks()


def test_duplicate_section_heading_raises_value_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_valid_corpus(tmp_path)
    text = _build_valid_policy_text("Duplicate charge")
    corrupted = text.replace(
        "## Mandatory escalation conditions",
        "## Purpose\n\n"
        "Duplicate purpose text for testing.\n\n"
        "## Mandatory escalation conditions",
        1,
    )
    (tmp_path / "duplicate_charge.md").write_text(corrupted, encoding="utf-8")
    monkeypatch.setattr(policy_chunks, "_POLICY_DIR", tmp_path)

    with pytest.raises(ValueError, match="expected section headings"):
        load_policy_chunks()


def test_missing_section_raises_value_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_valid_corpus(tmp_path)
    text = _build_valid_policy_text("Pending card payment")
    corrupted = text.replace(_section_block("Safe guidance"), "", 1)
    (tmp_path / "pending_card_payment.md").write_text(corrupted, encoding="utf-8")
    monkeypatch.setattr(policy_chunks, "_POLICY_DIR", tmp_path)

    with pytest.raises(ValueError, match="expected section headings"):
        load_policy_chunks()


def test_incorrect_heading_order_raises_value_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_valid_corpus(tmp_path)
    text = _build_valid_policy_text("Unrecognized transaction")
    purpose_block = _section_block("Purpose")
    when_block = _section_block("When it applies")
    corrupted = text.replace(
        purpose_block + when_block,
        when_block + purpose_block,
        1,
    )
    (tmp_path / "unrecognized_transaction.md").write_text(
        corrupted,
        encoding="utf-8",
    )
    monkeypatch.setattr(policy_chunks, "_POLICY_DIR", tmp_path)

    with pytest.raises(ValueError, match="expected section headings"):
        load_policy_chunks()


def test_unexpected_heading_raises_value_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_valid_corpus(tmp_path)
    text = _build_valid_policy_text("Transfer pending or not received")
    corrupted = text.replace(
        "## Mandatory escalation conditions",
        "## Extra unsupported section\n\n"
        "Unexpected synthetic text for testing.\n\n"
        "## Mandatory escalation conditions",
        1,
    )
    (tmp_path / "transfer_pending_or_not_received.md").write_text(
        corrupted,
        encoding="utf-8",
    )
    monkeypatch.setattr(policy_chunks, "_POLICY_DIR", tmp_path)

    with pytest.raises(ValueError, match="expected section headings"):
        load_policy_chunks()


def test_incorrect_h1_title_raises_value_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_valid_corpus(tmp_path)
    text = _build_valid_policy_text("Declined card payment")
    corrupted = text.replace(
        "# Declined card payment",
        "# Declined payment (wrong title)",
        1,
    )
    (tmp_path / "declined_card_payment.md").write_text(corrupted, encoding="utf-8")
    monkeypatch.setattr(policy_chunks, "_POLICY_DIR", tmp_path)

    with pytest.raises(ValueError, match="expected first line"):
        load_policy_chunks()


def test_empty_section_body_raises_value_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_valid_corpus(tmp_path)
    text = _build_valid_policy_text("Duplicate charge")
    corrupted = text.replace(
        _section_block("Safe guidance"),
        "## Safe guidance\n\n",
        1,
    )
    (tmp_path / "duplicate_charge.md").write_text(corrupted, encoding="utf-8")
    monkeypatch.setattr(policy_chunks, "_POLICY_DIR", tmp_path)

    with pytest.raises(ValueError, match="empty body"):
        load_policy_chunks()


# Check heading validation and section text preservation.


def test_additional_h1_heading_raises_value_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_valid_corpus(tmp_path)
    text = _build_valid_policy_text("Pending card payment")
    corrupted = text.replace(
        "## When it applies",
        "# Unexpected extra heading\n\n## When it applies",
        1,
    )
    (tmp_path / "pending_card_payment.md").write_text(corrupted, encoding="utf-8")
    monkeypatch.setattr(policy_chunks, "_POLICY_DIR", tmp_path)

    with pytest.raises(ValueError, match="unexpected additional top-level heading"):
        load_policy_chunks()


def test_text_between_title_and_first_section_raises_value_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_valid_corpus(tmp_path)
    text = _build_valid_policy_text("Duplicate charge")
    corrupted = text.replace(
        "# Duplicate charge\n\n## Purpose",
        "# Duplicate charge\n\nUnexpected synthetic preamble text.\n\n## Purpose",
        1,
    )
    (tmp_path / "duplicate_charge.md").write_text(corrupted, encoding="utf-8")
    monkeypatch.setattr(policy_chunks, "_POLICY_DIR", tmp_path)

    with pytest.raises(ValueError, match="unexpected text between the title"):
        load_policy_chunks()


def test_altered_heading_spacing_raises_value_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_valid_corpus(tmp_path)
    text = _build_valid_policy_text("Transfer pending or not received")
    corrupted = text.replace("## Purpose", "##  Purpose", 1)
    (tmp_path / "transfer_pending_or_not_received.md").write_text(
        corrupted,
        encoding="utf-8",
    )
    monkeypatch.setattr(policy_chunks, "_POLICY_DIR", tmp_path)

    with pytest.raises(ValueError, match="expected section headings"):
        load_policy_chunks()


def test_valid_temporary_section_preserves_internal_formatting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_valid_corpus(tmp_path)

    custom_text = (
        "# Pending card payment\n"
        "\n"
        "## Purpose\n"
        "\n"
        "Fictional synthetic purpose text.\n"
        "\n"
        "## When it applies\n"
        "\n"
        "Fictional synthetic applicability text.\n"
        "\n"
        "## Required information\n"
        "\n"
        "Fictional synthetic required information text.\n"
        "\n"
        "## Safe guidance\n"
        "\n"
        "Line one of guidance.\n"
        "\n"
        "    Indented line two of guidance.\n"
        "\n"
        "Line three of guidance.\n"
        "\n"
        "## Approved future mock lookup\n"
        "\n"
        "Fictional synthetic lookup text.\n"
        "\n"
        "## Mandatory escalation conditions\n"
        "\n"
        "Fictional synthetic escalation text.\n"
    )
    (tmp_path / "pending_card_payment.md").write_text(
        custom_text,
        encoding="utf-8",
    )
    monkeypatch.setattr(policy_chunks, "_POLICY_DIR", tmp_path)

    chunks = load_policy_chunks()
    target = next(
        chunk
        for chunk in chunks
        if chunk.chunk_id == "pending_card_payment:safe_guidance"
    )

    expected_body = (
        "Line one of guidance.\n"
        "\n"
        "    Indented line two of guidance.\n"
        "\n"
        "Line three of guidance."
    )
    assert target.text == expected_body
