"""
asr_model.py: decide where the speech-recognition model (Qwen3-ASR-0.6B) is loaded from.

The model used to be loaded by the bare name "Qwen3-ASR-0.6B", which transformers reads as a folder relative to the
server's current working directory and, when there is none, as a Hugging Face repo id without an organisation, hence
"Qwen3-ASR-0.6B is not a local folder and is not a valid model identifier". `resolve_asr_model` picks, in order:

  1. QP_ASR_MODEL: a folder, or a Hugging Face repo id such as "Qwen/Qwen3-ASR-0.6B";
  2. a folder named Qwen3-ASR-0.6B in the current directory, then at the repository root;
  3. the public repo id Qwen/Qwen3-ASR-0.6B (downloaded once into the Hugging Face cache).

Nothing here imports torch or transformers, so it is cheap to test.
"""

import os
from pathlib import Path
from typing import List, Mapping, Optional, Tuple

ASR_REPO_ID = "Qwen/Qwen3-ASR-0.6B"
ASR_FOLDER_NAME = "Qwen3-ASR-0.6B"


def _repository_root() -> Optional[Path]:
    for folder in Path(__file__).resolve().parents:
        if (folder / "pyproject.toml").is_file() and (folder / "packages").is_dir():
            return folder
    return None


def resolve_asr_model(
    env: Optional[Mapping[str, str]] = None, cwd: Optional[Path] = None, root: Optional[Path] = None
) -> Tuple[str, List[str]]:
    """(folder or repo id to pass to from_pretrained, the local folders that were checked)."""
    env = os.environ if env is None else env
    explicit = env.get("QP_ASR_MODEL", "").strip()
    if explicit:
        path = Path(explicit).expanduser()
        if path.is_dir():
            return str(path), [str(path)]
        if "/" in explicit and not path.is_absolute() and not explicit.startswith((".", "~")):
            return explicit, []  # a Hugging Face repo id such as org/name
        raise FileNotFoundError(
            f"QP_ASR_MODEL={explicit!r} is neither an existing folder nor a Hugging Face repo id ('organisation/name')."
        )
    tried: List[str] = []
    for base in (cwd or Path.cwd(), root or _repository_root()):
        if base is None:
            continue
        folder = Path(base) / ASR_FOLDER_NAME
        tried.append(str(folder))
        if (folder / "config.json").is_file():
            return str(folder), tried
    return ASR_REPO_ID, tried


def load_error_message(model_id: str, tried: List[str], cause: Exception) -> str:
    where = "; ".join(tried) if tried else "no local folder"
    return (
        f"Could not load the speech model '{model_id}' ({type(cause).__name__}: {cause}). "
        f"Local folders checked: {where}. Put the weights in a folder named {ASR_FOLDER_NAME} in the working directory "
        f"or the repository root, or set QP_ASR_MODEL to a folder or a Hugging Face id (default {ASR_REPO_ID}, "
        f"downloaded on first use, which needs network access)."
    )
