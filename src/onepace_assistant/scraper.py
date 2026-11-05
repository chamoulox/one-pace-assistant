"""Scraper for One Pace metadata from onepace.net."""

import json
import re
from typing import Any

import httpx

from .models import Arc

ONEPACE_WATCH_URL = "https://onepace.net/en/watch"

# Regex to extract RSC payload data from Next.js script tags
RSC_PAYLOAD_PATTERN = re.compile(r'self\.__next_f\.push\(\[1,"(.+?)"\]\)', re.DOTALL)


class ScraperError(Exception):
    """Error during metadata scraping."""


def _unescape_rsc_string(s: str) -> str:
    """Unescape the RSC payload string."""
    try:
        return json.loads('"' + s + '"')
    except json.JSONDecodeError as e:
        raise ScraperError(f"Invalid RSC string: {e}") from e


def _extract_arcs_array(payload: str) -> list[dict]:
    """Extract the arcs data array from the RSC payload (supports modern and legacy formats)."""
    # 1. Handle timeline-based segments (current site version)
    # 2. Fallback for legacy data property structure
    patterns = [r'"timeline":\s*\{.*?"segments":\s*(\[)', r'"data":\s*(\[{"slug":")']

    for pattern in patterns:
        match = re.search(pattern, payload, re.DOTALL)
        if not match:
            continue

        try:
            value, _ = json.JSONDecoder().raw_decode(payload[match.start(1) :])
            return value
        except json.JSONDecodeError:
            continue

    raise ScraperError("Could not extract arcs data from RSC payload")


def _normalize_arc_data(data: Any) -> Any:
    """
    Recursively normalizes payload data:
    - Replaces '$undefined' with None.
    - Maps 'playlistGroups' to 'playGroups' for compatibility with newer site versions.
    """
    if isinstance(data, list):
        return [_normalize_arc_data(item) for item in data]

    if isinstance(data, dict):
        normalized = {}
        for k, v in data.items():
            key = "playGroups" if k == "playlistGroups" else k
            normalized[key] = _normalize_arc_data(v)
        return normalized

    return None if data == "$undefined" else data


def extract_rsc_payload(html: str) -> str:
    """Extract and combine RSC payload strings from HTML."""
    matches = RSC_PAYLOAD_PATTERN.findall(html)
    if not matches:
        raise ScraperError("No RSC payload found in HTML")

    # Combine all payload chunks
    combined = ""
    for match in matches:
        combined += _unescape_rsc_string(match)

    return combined


def parse_arcs_from_html(html: str) -> list[Arc]:
    """Parse arc metadata from HTML content."""
    payload = extract_rsc_payload(html)
    arcs_data = _extract_arcs_array(payload)

    arcs = []
    for arc_data in arcs_data:
        try:
            # Normalize data: $undefined -> None, playlistGroups -> playGroups
            normalized_data = _normalize_arc_data(arc_data)
            arc = Arc.model_validate(normalized_data)
            arcs.append(arc)
        except Exception as e:
            # Log but don't fail on individual arc parsing errors
            print(f"Warning: Failed to parse arc '{arc_data.get('slug', 'unknown')}': {e}")

    return arcs


async def fetch_metadata(language: str = "en") -> list[Arc]:
    """Fetch and parse all arc metadata from onepace.net."""
    async with httpx.AsyncClient(
        headers={
            "User-Agent": "OnePaceAssistant/0.1.0 (https://github.com/one-pace-assistant)",
        },
        timeout=30.0,
    ) as client:
        try:
            response = await client.get(_watch_url(language))
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise ScraperError(f"Could not fetch {language} metadata: {e}") from e

    return parse_arcs_from_html(response.text)


def fetch_metadata_sync(language: str = "en") -> list[Arc]:
    """Synchronous version of fetch_metadata for CLI use."""
    with httpx.Client(
        headers={
            "User-Agent": "OnePaceAssistant/0.1.0 (https://github.com/one-pace-assistant)",
        },
        timeout=30.0,
    ) as client:
        try:
            response = client.get(_watch_url(language))
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise ScraperError(f"Could not fetch {language} metadata: {e}") from e

    return parse_arcs_from_html(response.text)


def _watch_url(language: str) -> str:
    """Build a locale URL without accepting arbitrary paths."""
    if not re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z0-9]+)*", language):
        raise ScraperError(f"Invalid language code: {language}")
    return f"https://onepace.net/{language}/watch"


def discover_languages_sync() -> list[str]:
    """Discover advertised site locales from the English watch page."""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(ONEPACE_WATCH_URL)
            response.raise_for_status()
    except httpx.HTTPError as e:
        raise ScraperError(f"Could not discover languages: {e}") from e
    payload = extract_rsc_payload(response.text)
    languages = re.findall(r'"og:locale(?::alternate)?"\s*,\s*"content"\s*:\s*"([^"]+)"', payload)
    if not languages:
        raise ScraperError("No language locales found on the watch page")
    return list(dict.fromkeys(languages))


def merge_arcs(collections: list[list[Arc]]) -> list[Arc]:
    """Merge localized playlists by slug, keeping the first locale's text."""
    merged: dict[str, Arc] = {}
    for arcs in collections:
        for arc in arcs:
            if arc.slug not in merged:
                merged[arc.slug] = arc.model_copy(deep=True)
                continue
            target = merged[arc.slug]
            for group in arc.play_groups:
                match = next(
                    (
                        g
                        for g in target.play_groups
                        if (g.sub, g.dub, g.variant) == (group.sub, group.dub, group.variant)
                    ),
                    None,
                )
                if match is None:
                    target.play_groups.append(group.model_copy(deep=True))
                else:
                    for playlist in group.playlists:
                        if playlist not in match.playlists:
                            match.playlists.append(playlist.model_copy(deep=True))
    return list(merged.values())
