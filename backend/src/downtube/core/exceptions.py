"""Custom exceptions for DownTube."""


class DownTubeError(Exception):
    """Base exception for all DownTube errors."""

    pass


class DownloadError(DownTubeError):
    """Raised when a download fails."""

    pass


class ProviderError(DownTubeError):
    """Raised when a provider (Spotify, YTMusic, etc.) fails."""

    pass


class MetadataError(DownTubeError):
    """Raised when metadata resolution fails."""

    pass


class TaggingError(DownTubeError):
    """Raised when audio tagging fails."""

    pass
