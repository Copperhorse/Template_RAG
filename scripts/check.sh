#!/usr/bin/env bash
# The checks that need no model and no network: unit tests, then the adversarial answer-gate table compared with the committed one.
# A change to the gates, the chunker or the table check that moves a number fails here; update evals/results/gates.md on purpose, not by accident.
set -euo pipefail
cd "$(dirname "$0")/.."
export RAG_NO_DOTENV=1
PY="${PYTHON:-}"
if [ -z "$PY" ]; then if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=python; fi; fi  # the project venv unless PYTHON says otherwise
"$PY" -m pytest tests -q -m "not models"
out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT
"$PY" -m rag_template.evals gates --out "$out/gates" > /dev/null
diff -u evals/results/gates.md "$out/gates.md" && echo "gates table: identical to evals/results/gates.md"
