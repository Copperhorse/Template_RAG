"""
device.py — one place that decides where torch models run.

Put this file next to DBManager.py (qp_core/device.py) and import with:

    from qp_core.device import get_device

Order of preference: CUDA -> Apple MPS -> CPU.
Override with the environment variable QP_DEVICE (e.g. QP_DEVICE=cpu to force
CPU, QP_DEVICE=cuda:1 to pick a second GPU).
"""

import logging
import os
from functools import lru_cache

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_device() -> str:
    override = os.environ.get("QP_DEVICE", "").strip().lower()
    if override:
        logger.info(f"Device forced by QP_DEVICE: {override}")
        return override

    try:
        import torch
    except ImportError:
        logger.info("torch not importable — using cpu")
        return "cpu"

    if torch.cuda.is_available():
        logger.info(f"Using GPU: {torch.cuda.get_device_name(0)} (cuda)")
        return "cuda"

    mps = getattr(torch.backends, "mps", None)
    if mps is not None and mps.is_available():
        logger.info("Using Apple GPU (mps)")
        return "mps"

    logger.info("No GPU available — using cpu")
    return "cpu"
