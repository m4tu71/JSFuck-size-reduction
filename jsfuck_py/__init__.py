"""Experimental Python JSFuck size-reduction encoder."""

from ._version import __version__
from .encoder import encode

__all__ = ["encode", "__version__"]
