"""Provider-independent garment generation use cases."""

from .tee import TeeInputError, generate_tee

__all__ = ["TeeInputError", "generate_tee"]