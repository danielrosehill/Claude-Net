"""Minimal TOON-style encoder for tabular list responses.

Format: header row of field names, then one row per record, pipe-delimited.
Token-cheap alternative to JSON for repeated-shape lists.
"""
from typing import Iterable, Sequence


def encode_table(fields: Sequence[str], rows: Iterable[Sequence]) -> str:
    out = ["|".join(fields)]
    for r in rows:
        out.append("|".join(_cell(v) for v in r))
    return "\n".join(out)


def _cell(v) -> str:
    if v is None:
        return ""
    s = str(v).replace("|", "\\|").replace("\n", "\\n")
    return s
