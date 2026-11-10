"""Re-export each resource router under an explicit name.

Explicit names beat `from .widgets import *`: the wildcard makes it impossible to
tell where a router came from, and it happily re-exports every helper and import
in the module into the package namespace.
"""

from .widgets import router as widgets_router

__all__ = ["widgets_router"]
