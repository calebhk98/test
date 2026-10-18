"""Load GLiNER2 checkpoints once and share them between taggers and fact extractors.

GLiNER2 (fastino) is a ~200M encoder trained for entity extraction, text
classification and structured extraction. It runs well on CPU.
`pip install "gliner2[local]"`.
"""
from __future__ import annotations

import logging

from .. import hardware
from .base import PartUnavailable

log = logging.getLogger(__name__)

DEFAULT_GLINER_MODEL = "fastino/gliner2.5-base-v1"
_loaded_models: dict[tuple[str, str], object] = {}


def gliner_installed() -> bool:
    try:
        import gliner2  # noqa: F401
        return True
    except ImportError:
        return False


def load_gliner(model_name: str = DEFAULT_GLINER_MODEL, device: str = "auto"):
    device = hardware.detect().device if device == "auto" else device
    cache_key = (model_name, device)
    if cache_key not in _loaded_models:
        try:
            from gliner2 import AutoExtractor
        except ImportError as error:
            raise PartUnavailable('GLiNER2 is not installed: pip install "gliner2[local]"') from error
        try:
            log.info("loading %s on %s", model_name, device)
            _loaded_models[cache_key] = AutoExtractor.from_pretrained(model_name, map_location=device)
        except (OSError, ValueError) as error:
            raise PartUnavailable(f"could not load {model_name}: {error}") from error
    return _loaded_models[cache_key]
