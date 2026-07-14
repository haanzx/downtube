"""Provider registry with auto-discovery.

Automatically discovers and registers all providers in the providers/ folder.
Providers must implement the MusicProvider protocol.
"""

import importlib
import pkgutil
from pathlib import Path

from downtube.providers.base import MusicProvider

_registry: dict[str, MusicProvider] = {}
_discovered = False


def _discover() -> None:
    """Auto-import all modules in providers/ folder and register providers."""
    global _discovered
    if _discovered:
        return

    package_dir = Path(__file__).parent
    for _, name, _ in pkgutil.iter_modules([str(package_dir)]):
        if name.startswith("_") or name in ("base", "tagger", "registry"):
            continue
        try:
            mod = importlib.import_module(f"downtube.providers.{name}")
            _register_from_module(mod)
        except Exception:
            pass

    _discovered = True


def _register_from_module(mod: object) -> None:
    """Register provider instances from a module."""
    for attr_name in dir(mod):
        attr = getattr(mod, attr_name)
        if isinstance(attr, type) and hasattr(attr, "name"):
            try:
                instance = attr()
                if hasattr(instance, "can_handle") and hasattr(instance, "search"):
                    register(instance)
            except Exception:
                pass


def register(provider: MusicProvider) -> None:
    """Register a provider instance."""
    _registry[provider.name] = provider


def get_provider(name: str) -> MusicProvider:
    """Get a provider by name."""
    if not _discovered:
        _discover()
    if name not in _registry:
        raise KeyError(f"Provider not found: {name}")
    return _registry[name]


def find_provider_for_url(url: str) -> MusicProvider:
    """Find the appropriate provider for a given URL."""
    if not _discovered:
        _discover()
    for p in _registry.values():
        if p.can_handle(url):
            return p
    raise ValueError(f"No provider for URL: {url}")


def all_providers() -> list[MusicProvider]:
    """Return all registered providers."""
    if not _discovered:
        _discover()
    return list(_registry.values())


def provider_names() -> list[str]:
    """Return all registered provider names."""
    if not _discovered:
        _discover()
    return list(_registry.keys())
