#!/usr/bin/env bash
# Serve a GGUF model with llama.cpp's OpenAI-compatible server (what LLM_BASE_URL points at).
#   scripts/serve_llm.sh                         # Gemma 4 E2B, port 8080
#   MODEL=~/models/other.gguf PORT=8081 scripts/serve_llm.sh
# Which server runs, in order: LLAMA_SERVER (a path you give), `llama serve` when the `llama` command is on PATH (it uses the GPU),
# then a llama-server binary in one of the folders below. Use a GPU build: on the RTX A2000 a CPU-only build read a 1.8k-token prompt
# at 82 tokens/s (22 s per RAG answer); a CUDA build takes about 1 s for the same prompt and generates 4x faster.
set -euo pipefail
if [ -n "${LLAMA_SERVER:-}" ]; then
  CMD=("$LLAMA_SERVER")
  export LD_LIBRARY_PATH="$(dirname "$LLAMA_SERVER")${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
elif command -v llama >/dev/null 2>&1; then
  CMD=(llama serve)
else
  for candidate in "$HOME/Git/llama.cpp-spark/build/bin/llama-server" "$HOME/Git/notmine/llama.cpp-spark/build/bin/llama-server" \
                   "$HOME/Git/VLS/runtime/llama-server" "$HOME/Git/notmine/VLS/runtime/llama-server"; do
    if [ -x "$candidate" ]; then
      CMD=("$candidate")
      export LD_LIBRARY_PATH="$(dirname "$candidate")${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
      break
    fi
  done
fi
if [ -z "${CMD+x}" ]; then
  echo "no llama server found: install the \`llama\` command, or set LLAMA_SERVER=/path/to/llama-server" >&2
  exit 1
fi
echo "serving with ${CMD[*]}" >&2
MODEL="${MODEL:-$HOME/models/Sharp-MiniCPM5-2B-Q8_K_M.gguf}"
PORT="${PORT:-8080}"
CTX="${CTX:-8192}"
# --reasoning off: Gemma 4 otherwise writes its chain of thought into `content`, which breaks JSON replies
exec "${CMD[@]}" -m "$MODEL" --port "$PORT" -c "$CTX" -ngl 99 -np 1 --jinja --reasoning off "$@"
