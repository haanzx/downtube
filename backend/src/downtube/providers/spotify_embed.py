"""Spotify embed page scraper for metadata.

Resolves track, album and playlist links by scraping the public
open.spotify.com/embed pages. No Spotify credentials required.

Based on Downtify's approach:
- Metadata: open.spotify.com/embed scraping
- Audio match: ytmusicapi with duration comparison
- Download: yt-dlp + mutagen
"""

from __future__ import annotations

import json
import re
from typing import Any, Optional

import httpx

# Spotify embed URL pattern
EMBED_URL = "https://open.spotify.com/embed/{kind}/{id}"

# User agent (minimal to get embed data)
_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Spotify URL regex
SPOTIFY_URL_RE = re.compile(
    r"(?:https?://)?(?:open\.)?spotify\.com/"
    r"(?:intl-[a-z]{2}/)?"
    r"(?P<type>track|album|playlist|artist|episode|show)/"
    r"(?P<id>[A-Za-z0-9]+)"
)

# GraphQL hash for fetchPlaylist (from Downtify)
_GRAPHQL_HASH = (
    "a65e12194ed5fc443a1cdebed5fabe33ca5b07b987185d63c72483867ad13cb4"
)

_PARTNER_API = "https://api-partner.spotify.com/pathfinder/v1/query"


def parse_spotify_url(url: str) -> Optional[tuple[str, str]]:
    """Return (type, id) for a Spotify URL or None."""
    if not url:
        return None
    if url.startswith("spotify:"):
        try:
            _, kind, sid = url.split(":", 2)
        except ValueError:
            return None
        return kind, sid
    match = SPOTIFY_URL_RE.search(url)
    if not match:
        return None
    return match.group("type"), match.group("id")


def is_spotify(url: str) -> bool:
    """Check if URL is a Spotify link."""
    return bool(parse_spotify_url(url))


async def _fetch_embed_json(kind: str, spotify_id: str) -> dict[str, Any]:
    """Fetch Spotify embed page and extract __NEXT_DATA__ JSON."""
    url = EMBED_URL.format(kind=kind, id=spotify_id)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            url,
            headers={
                "User-Agent": _USER_AGENT,
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=15,
        )
        resp.raise_for_status()

    # Extract __NEXT_DATA__ JSON from HTML
    match = re.search(
        r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        resp.text,
        re.DOTALL,
    )
    if not match:
        raise ValueError("Spotify embed payload not found")

    return json.loads(match.group(1))


def _entity_from(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract entity from embed payload."""
    page_props = payload.get("props", {}).get("pageProps", {}) or {}

    # Try multiple paths (Spotify changes structure)
    candidates = [
        page_props.get("state", {}).get("data", {}).get("entity")
        if isinstance(page_props.get("state"), dict)
        else None,
        page_props.get("entity"),
        page_props.get("data", {}).get("entity")
        if isinstance(page_props.get("data"), dict)
        else None,
    ]

    for candidate in candidates:
        if isinstance(candidate, dict):
            return candidate

    raise ValueError("Spotify entity not found in embed payload")


def _largest_image(sources: list[dict[str, Any]]) -> str:
    """Get largest image URL from sources list."""
    if not sources:
        return ""
    sized = [s for s in sources if isinstance(s, dict) and s.get("url")]
    if not sized:
        return ""
    sized.sort(key=lambda s: int(s.get("width") or 0), reverse=True)
    return sized[0]["url"]


def _cover_url(entity: dict[str, Any]) -> str:
    """Extract cover art URL from entity."""
    candidates: list[dict[str, Any]] = []

    # Try coverArt.sources
    cover_art = entity.get("coverArt") or {}
    if isinstance(cover_art, dict):
        candidates += cover_art.get("sources") or []

    # Try visualIdentity.image
    visual = entity.get("visualIdentity") or {}
    if isinstance(visual, dict):
        candidates += visual.get("image") or []

    # Try nested album.coverArt
    album = entity.get("album") or {}
    if isinstance(album, dict):
        nested = album.get("coverArt") or {}
        if isinstance(nested, dict):
            candidates += nested.get("sources") or []
        images = album.get("images")
        if isinstance(images, list):
            candidates += images

    return _largest_image(candidates)


def _artist_names(entity: dict[str, Any]) -> list[str]:
    """Extract artist names from entity."""
    raw = entity.get("artists") or []
    names: list[str] = []

    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str):
                if item.strip():
                    names.append(item.strip())
            elif isinstance(item, dict):
                name = item.get("name")
                if name:
                    names.append(name)

    if names:
        return names

    # Fallback to subtitle parsing
    return [
        d["name"]
        for d in _artists_from_subtitle(entity.get("subtitle"))
        if d.get("name")
    ]


def _artists_from_subtitle(subtitle: Any) -> list[dict[str, str]]:
    """Parse artists from subtitle string."""
    if not isinstance(subtitle, str) or not subtitle:
        return []
    normalized = subtitle.replace("\xa0", " ")
    return [
        {"name": name.strip()}
        for name in re.split(r"\s*(?:,|，)\s*", normalized)
        if name.strip()
    ]


def _normalize_release_date(raw: Any) -> str:
    """Normalize release date to YYYY-MM-DD or year."""
    if not isinstance(raw, str):
        return ""
    text = raw.strip()
    if not text:
        return ""
    if "T" in text:
        text = text.split("T", 1)[0].strip()
    # YYYY-MM-DD
    if (
        len(text) >= 10
        and text[4:5] == "-"
        and text[7:8] == "-"
        and text[:4].isdigit()
        and text[5:7].isdigit()
        and text[8:10].isdigit()
    ):
        return text[:10]
    # YYYY-MM
    if (
        len(text) >= 7
        and text[4:5] == "-"
        and text[:4].isdigit()
        and text[5:7].isdigit()
    ):
        return f"{text[:4]}-{text[5:7]}-01"
    # YYYY
    if len(text) >= 4 and text[:4].isdigit():
        return text[:4]
    return text


def _release_date_str(entity: dict[str, Any]) -> str:
    """Extract release date from entity."""
    rd = entity.get("releaseDate")
    if isinstance(rd, dict):
        iso = rd.get("isoString")
        if isinstance(iso, str) and iso.strip():
            return _normalize_release_date(iso.strip())
        # Try year/month/day
        year = rd.get("year")
        month = rd.get("month")
        day = rd.get("day")
        if year and month:
            return f"{year}-{month:02d}-{day:02d}" if day else f"{year}-{month:02d}-01"
        if year:
            return str(year)
    elif isinstance(rd, str):
        return _normalize_release_date(rd)

    # Fallback to album
    album = entity.get("album") or {}
    if isinstance(album, dict):
        for key in ("releaseDate", "date"):
            alt = album.get(key)
            if alt:
                result = _release_date_str(alt) if isinstance(alt, dict) else _normalize_release_date(alt)
                if result:
                    return result

    return ""


def _year_from_release_date(rd: str) -> str:
    """Extract year from release date."""
    if len(rd) >= 4 and rd[:4].isdigit():
        return rd[:4]
    return ""


def _embed_row_track(item: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Extract track dict from playlist/album embed row."""
    inner = item.get("track")
    if isinstance(inner, dict):
        sub = item.get("subtitle")
        if isinstance(sub, str) and sub.strip() and not inner.get("subtitle"):
            return {**inner, "subtitle": sub}
        return inner
    return item if isinstance(item, dict) else None


def _id_from_uri(uri: str) -> str:
    """Extract ID from Spotify URI."""
    if not uri:
        return ""
    parts = uri.split(":")
    return parts[-1] if parts else ""


def _track_dict(
    entity: dict[str, Any],
    *,
    track_id: str,
    fallback_album: str = "",
    fallback_cover: str = "",
    fallback_release_date: str = "",
) -> dict[str, Any]:
    """Build track metadata dict from entity."""
    duration_ms = entity.get("duration") or entity.get("duration_ms") or 0
    album = entity.get("album") or {}
    album_name = album.get("name", "") if isinstance(album, dict) else ""
    cover = _cover_url(entity) or fallback_cover
    names = _artist_names(entity)
    release_date = _release_date_str(entity)
    if not release_date:
        release_date = (fallback_release_date or "").strip()
    year = _year_from_release_date(release_date)

    return {
        "song_id": track_id,
        "name": entity.get("name") or entity.get("title") or "",
        "artists": names,
        "artist": ", ".join(names),
        "album_name": album_name or fallback_album,
        "cover_url": cover,
        "duration": int(int(duration_ms) / 1000) if duration_ms else 0,
        "url": f"https://open.spotify.com/track/{track_id}" if track_id else "",
        "explicit": bool(entity.get("isExplicit") or entity.get("explicit")),
        "release_date": release_date,
        "year": year,
        "source": "spotify",
    }


# Public API


async def scrape_track(url: str) -> dict[str, Any]:
    """Scrape a single Spotify track URL for metadata."""
    parsed = parse_spotify_url(url)
    if not parsed:
        raise ValueError(f"Not a Spotify URL: {url}")
    kind, spotify_id = parsed

    if kind != "track":
        raise ValueError(f"Expected track URL, got {kind}")

    payload = await _fetch_embed_json("track", spotify_id)
    entity = _entity_from(payload)
    return _track_dict(entity, track_id=spotify_id)


async def scrape_album(url: str) -> list[dict[str, Any]]:
    """Scrape a Spotify album URL for all track metadata."""
    parsed = parse_spotify_url(url)
    if not parsed:
        raise ValueError(f"Not a Spotify URL: {url}")
    kind, album_id = parsed

    if kind != "album":
        raise ValueError(f"Expected album URL, got {kind}")

    payload = await _fetch_embed_json("album", album_id)
    entity = _entity_from(payload)
    album_name = entity.get("name") or ""
    cover = _cover_url(entity)
    release_date = _release_date_str(entity)

    track_items = (
        entity.get("trackList")
        or (entity.get("tracks") or {}).get("items")
        or []
    )

    songs: list[dict[str, Any]] = []
    for idx, item in enumerate(track_items, start=1):
        if not isinstance(item, dict):
            continue
        track = _embed_row_track(item)
        if not isinstance(track, dict):
            continue
        track_id = track.get("id") or _id_from_uri(track.get("uri", ""))
        if not track_id:
            continue

        row = _track_dict(
            dict(track),
            track_id=track_id,
            fallback_album=album_name,
            fallback_cover=cover,
            fallback_release_date=release_date,
        )
        row["track_number"] = idx
        songs.append(row)

    return songs


async def scrape_playlist(url: str) -> tuple[str, list[dict[str, Any]]]:
    """Scrape a Spotify playlist URL.

    Returns (playlist_name, tracks).
    Uses GraphQL for full pagination if access token available.
    """
    parsed = parse_spotify_url(url)
    if not parsed:
        raise ValueError(f"Not a Spotify URL: {url}")
    kind, playlist_id = parsed

    if kind != "playlist":
        raise ValueError(f"Expected playlist URL, got {kind}")

    payload = await _fetch_embed_json("playlist", playlist_id)
    entity = _entity_from(payload)
    embed_name = entity.get("name") or entity.get("title") or playlist_id

    # Try GraphQL for full pagination
    token = _token_from_payload(payload)
    if token:
        try:
            name, tracks = await _graphql_fetch_playlist(playlist_id, token)
            return name or embed_name, tracks
        except Exception:
            pass  # Fallback to embed data

    return embed_name, _parse_embed_tracks(entity)


def _token_from_payload(payload: dict[str, Any]) -> Optional[str]:
    """Extract access token from embed payload."""
    try:
        return payload["props"]["pageProps"]["state"]["settings"]["session"]["accessToken"]
    except (KeyError, TypeError):
        return None


def _parse_embed_tracks(entity: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse tracks from embed data (limited to first page)."""
    fallback_cover = _cover_url(entity)
    track_items = entity.get("trackList") or []
    songs: list[dict[str, Any]] = []

    for item in track_items:
        if not isinstance(item, dict):
            continue
        track = _embed_row_track(item)
        if not isinstance(track, dict):
            continue
        track_id = track.get("id") or _id_from_uri(track.get("uri", ""))
        if not track_id:
            continue
        songs.append(
            _track_dict(dict(track), track_id=track_id, fallback_cover=fallback_cover)
        )

    return songs


async def _graphql_fetch_playlist(
    playlist_id: str, token: str
) -> tuple[Optional[str], list[dict[str, Any]]]:
    """Fetch all tracks via Spotify GraphQL API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": _USER_AGENT,
        "app-platform": "WebPlayer",
    }

    tracks: list[dict[str, Any]] = []
    playlist_name: Optional[str] = None
    offset = 0
    limit = 100

    async with httpx.AsyncClient() as client:
        while True:
            params = {
                "operationName": "fetchPlaylist",
                "variables": json.dumps({
                    "uri": f"spotify:playlist:{playlist_id}",
                    "offset": offset,
                    "limit": limit,
                    "enableWatchFeedEntrypoint": False,
                    "includeEpisodeContentRatingsV2": False,
                }),
                "extensions": json.dumps({
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": _GRAPHQL_HASH,
                    }
                }),
            }

            resp = await client.get(
                _PARTNER_API,
                params=params,
                headers=headers,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            if "errors" in data:
                raise ValueError(f"GraphQL errors: {data['errors']}")

            pv2 = data["data"]["playlistV2"]
            if playlist_name is None:
                playlist_name = pv2.get("name")

            content = pv2.get("content") or {}
            items = content.get("items") or []

            for item in items:
                td = _track_dict_from_graphql_item(item)
                if td:
                    tracks.append(td)

            total = content.get("totalCount") or 0
            offset += len(items)

            if not items or offset >= total:
                break

    return playlist_name, tracks


def _track_dict_from_graphql_item(item: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Parse track from GraphQL item."""
    iv2 = item.get("itemV2") or {}
    if iv2.get("__typename") != "TrackResponseWrapper":
        return None

    track = iv2.get("data") or {}
    if not isinstance(track, dict):
        return None

    track_id = _id_from_uri(track.get("uri") or "")
    if not track_id:
        return None

    artists = [
        a["profile"]["name"]
        for a in (track.get("artists") or {}).get("items", [])
        if isinstance(a, dict)
        and isinstance(a.get("profile"), dict)
        and a["profile"].get("name")
    ]

    album = track.get("albumOfTrack") or {}
    album_name = album.get("name", "") if isinstance(album, dict) else ""
    cover_sources = (album.get("coverArt") or {}).get("sources") or []
    cover_url = _largest_image(cover_sources)
    duration_ms = (track.get("trackDuration") or {}).get("totalMilliseconds") or 0

    gql_release = ""
    if isinstance(album, dict):
        for key in ("date", "releaseDate"):
            gql_release = _release_date_str(album.get(key) or {})
            if gql_release:
                break

    return {
        "song_id": track_id,
        "name": track.get("name") or "",
        "artists": artists,
        "artist": ", ".join(artists),
        "album_name": album_name,
        "cover_url": cover_url,
        "duration": int(duration_ms / 1000) if duration_ms else 0,
        "url": f"https://open.spotify.com/track/{track_id}",
        "explicit": False,
        "release_date": gql_release,
        "year": _year_from_release_date(gql_release),
        "source": "spotify",
    }


async def resolve(url: str) -> dict[str, Any] | list[dict[str, Any]]:
    """Resolve any Spotify URL to track(s) metadata.

    Returns dict for track, list for album/playlist.
    """
    parsed = parse_spotify_url(url)
    if parsed is None:
        raise ValueError("Not a Spotify URL")

    kind, sid = parsed
    if kind == "track":
        return await scrape_track(url)
    elif kind == "album":
        return await scrape_album(url)
    elif kind == "playlist":
        name, tracks = await scrape_playlist(url)
        return {"name": name, "tracks": tracks}
    else:
        raise ValueError(f"Unsupported Spotify entity type: {kind}")
