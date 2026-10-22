"""
tables.py: small helpers on Markdown table rows shared by the chunker (chunking/markdown.py) and the answer gate (tablecheck.py).
"""

import re
from typing import List

LABEL_JOINER = " / "  # between an inherited parent label and the row's own: "Qwen3-30B-Thinking / + SSD"
_CONTINUATION = re.compile(r"^(?:[+\-−–]\s*[A-Za-z]|w/o?(?![A-Za-z])|with(?:out)?\s|\([^)]*\)\s*$|\.\.\.|…)", re.IGNORECASE)  # "+ SSD", "w/ ACT", "(ours)"; not "-0.5" or "(a) Setup"
_ROW_LABEL = re.compile(r"^(\|\s*)(.*?)(\s*\|)")


def inherit_row_labels(rows: List[str]) -> List[str]:
    """Rows whose first cell only continues the previous row's label ("+ SSD", "w/ ACT", "(ours)") get that label in front, so a row
    says what it is a row of even when it is read apart from its neighbours. Ordinary labels are never rewritten."""
    out, parent = [], ""
    for row in rows:
        m = _ROW_LABEL.match(row)
        label = m.group(2).strip() if m else ""
        if m and label and _CONTINUATION.match(label) and parent:
            row = f"{m.group(1)}{parent}{LABEL_JOINER}{label}{m.group(3)}" + row[m.end():]
        elif label:
            parent = label
        out.append(row)
    return out
