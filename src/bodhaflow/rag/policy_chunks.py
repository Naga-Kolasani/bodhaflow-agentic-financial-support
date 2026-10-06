"""Load the five fictional policies into source-traceable section chunks.

Validate the fixed document structure and preserve each section's text.
This module does not generate embeddings or create an index.
"""

from pathlib import Path

from pydantic import BaseModel, field_validator

_PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]
_POLICY_DIR: Path = _PROJECT_ROOT / "data" / "policies"

_POLICY_FILES: tuple[tuple[str, str], ...] = (
    ("declined_card_payment.md", "Declined card payment"),
    ("duplicate_charge.md", "Duplicate charge"),
    ("pending_card_payment.md", "Pending card payment"),
    ("transfer_pending_or_not_received.md", "Transfer pending or not received"),
    ("unrecognized_transaction.md", "Unrecognized transaction"),
)

_SECTION_ID_MAP: dict[str, str] = {
    "Purpose": "purpose",
    "When it applies": "when_it_applies",
    "Required information": "required_information",
    "Safe guidance": "safe_guidance",
    "Approved future mock lookup": "approved_future_mock_lookup",
    "Mandatory escalation conditions": "mandatory_escalation_conditions",
}

_REQUIRED_SECTION_HEADINGS: tuple[str, ...] = tuple(_SECTION_ID_MAP.keys())

_H1_PREFIX = "# "
_H2_PREFIX = "## "

_EXPECTED_H2_LINES: tuple[str, ...] = tuple(
    f"{_H2_PREFIX}{heading}" for heading in _REQUIRED_SECTION_HEADINGS
)


class PolicyChunk(BaseModel):
    chunk_id: str
    source_path: str
    document_title: str
    section_heading: str
    text: str

    @field_validator(
        "chunk_id",
        "source_path",
        "document_title",
        "section_heading",
        "text",
    )
    @classmethod
    def _reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("PolicyChunk fields must not be empty or whitespace-only")
        return value


def load_policy_chunks() -> list[PolicyChunk]:
    """Return policy sections in alphabetical file order and document order.

    Raise FileNotFoundError for missing files and ValueError for invalid
    document structure. Do not return partial results.
    """
    chunks: list[PolicyChunk] = []
    for filename, expected_title in _POLICY_FILES:
        path = _POLICY_DIR / filename
        chunks.extend(_load_single_policy(path, filename, expected_title))
    return chunks


def _load_single_policy(
    path: Path,
    filename: str,
    expected_title: str,
) -> list[PolicyChunk]:
    if not path.is_file():
        raise FileNotFoundError(f"Policy file not found: {path}")

    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError(f"{filename}: file is empty")

    expected_h1 = f"{_H1_PREFIX}{expected_title}"
    if lines[0] != expected_h1:
        raise ValueError(
            f"{filename}: expected first line {expected_h1!r}, got {lines[0]!r}"
        )

    extra_h1_indices = [
        index
        for index, line in enumerate(lines)
        if index > 0 and line.startswith(_H1_PREFIX)
    ]
    if extra_h1_indices:
        first_extra = extra_h1_indices[0]
        raise ValueError(
            f"{filename}: unexpected additional top-level heading at line "
            f"{first_extra + 1}: {lines[first_extra]!r}"
        )

    h2_indices = [
        index for index, line in enumerate(lines) if line.startswith(_H2_PREFIX)
    ]
    if not h2_indices:
        raise ValueError(f"{filename}: no section headings found")

    preamble = lines[1 : h2_indices[0]]
    if any(line.strip() for line in preamble):
        raise ValueError(
            f"{filename}: unexpected text between the title and the first section heading"
        )

    found_h2_lines = [lines[index] for index in h2_indices]
    if found_h2_lines != list(_EXPECTED_H2_LINES):
        raise ValueError(
            f"{filename}: expected section headings {list(_EXPECTED_H2_LINES)!r} "
            f"in order with no duplicates or extras, found {found_h2_lines!r}"
        )

    stem = filename.removesuffix(".md")
    source_path = f"data/policies/{filename}"

    chunks: list[PolicyChunk] = []
    for position, heading_index in enumerate(h2_indices):
        heading = _REQUIRED_SECTION_HEADINGS[position]
        body_start = heading_index + 1
        body_end = (
            h2_indices[position + 1]
            if position + 1 < len(h2_indices)
            else len(lines)
        )
        body_text = "\n".join(lines[body_start:body_end]).strip()
        if not body_text:
            raise ValueError(f"{filename}: section {heading!r} has an empty body")

        section_id = _SECTION_ID_MAP[heading]
        chunks.append(
            PolicyChunk(
                chunk_id=f"{stem}:{section_id}",
                source_path=source_path,
                document_title=expected_title,
                section_heading=heading,
                text=body_text,
            )
        )

    return chunks
