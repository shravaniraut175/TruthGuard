# TruthGuard Search Module
"""Web search functionality for external grounding."""

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

from .config import settings


@dataclass
class SearchResult:
    """Represents a single search result."""
    title: str
    url: str
    snippet: str
    source: str = ""


class BaseSearchProvider(ABC):
    """Abstract base class for search providers."""

    @abstractmethod
    def search(self, query: str, num_results: int = 5) -> list[SearchResult]:
        """
        Perform a web search.

        Args:
            query: Search query string
            num_results: Number of results to return

        Returns:
            List of SearchResult objects
        """
        pass


class DuckDuckGoProvider(BaseSearchProvider):
    """DuckDuckGo search provider using duckduckgo-search library."""

    def search(self, query: str, num_results: int = 5) -> list[SearchResult]:
        """
        Perform a DuckDuckGo search.

        Args:
            query: Search query string
            num_results: Number of results to return

        Returns:
            List of SearchResult objects
        """
        try:
            from ddgs import DDGS

            results = []
            with DDGS() as ddgs:
                # Use text search
                search_results = list(ddgs.text(query, max_results=num_results))

                for result in search_results:
                    if isinstance(result, dict):
                        results.append(SearchResult(
                            title=result.get("title", "Untitled"),
                            url=result.get("href", ""),
                            snippet=result.get("body", ""),
                            source="DuckDuckGo"
                        ))
                    elif hasattr(result, 'title'):
                        # Handle named tuple or object results
                        results.append(SearchResult(
                            title=getattr(result, 'title', 'Untitled'),
                            url=getattr(result, 'href', getattr(result, 'url', '')),
                            snippet=getattr(result, 'body', getattr(result, 'snippet', '')),
                            source="DuckDuckGo"
                        ))

            return results[:num_results]

        except ImportError:
            raise RuntimeError("duckduckgo-search library not installed")
        except Exception as e:
            # Return empty results on search failure
            print(f"Search failed: {str(e)}")
            return []


class SearchProvider:
    """Factory class for creating search providers."""

    _providers = {
        "duckduckgo": DuckDuckGoProvider,
    }

    @classmethod
    def create(cls, provider: str) -> BaseSearchProvider:
        """
        Create a search provider instance.

        Args:
            provider: Provider name (duckduckgo)

        Returns:
            Search provider instance

        Raises:
            ValueError: If provider is not supported
        """
        provider_lower = provider.lower()
        if provider_lower not in cls._providers:
            raise ValueError(
                f"Unsupported search provider: {provider}. "
                f"Supported providers: {list(cls._providers.keys())}"
            )
        return cls._providers[provider_lower]()


def get_search_provider(provider: str = "duckduckgo") -> BaseSearchProvider:
    """
    Get a search provider instance.

    Args:
        provider: Provider name

    Returns:
        Search provider instance
    """
    return SearchProvider.create(provider)
