"""tokens.py: token counting with a cheap fallback."""

from functools import lru_cache


@lru_cache(maxsize=1)
def _encoder():
    """cl100k_base if tiktoken is installed *and* its vocabulary is available (it is downloaded on
    first use). The result, including a failure, is cached so a missing network costs one attempt."""
    try:
        import tiktoken

        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        return None


def count_tokens(text: str) -> int:
    if not text:
        return 0
    enc = _encoder()
    if enc is not None:
        try:
            return len(enc.encode(text, disallowed_special=()))
        except Exception:
            pass
    return max(1, len(text) // 4)
