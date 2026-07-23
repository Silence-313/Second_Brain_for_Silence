"""Search framework — protocol, manager, and providers."""

from agent.search.manager import SearchManager
from agent.search.protocol import SearchProvider

__all__ = ["SearchProvider", "SearchManager"]
