"""Regression tests for localized metadata and playlist selection."""

import json
from unittest.mock import patch

import httpx
import pytest
from click.testing import CliRunner

from onepace_assistant.cli import cli
from onepace_assistant.models import Arc
from onepace_assistant.scraper import ScraperError, merge_arcs, parse_arcs_from_html


def localized_arc(language="fr", cut=None):
    return Arc.model_validate(
        {
            "slug": "wano",
            "title": "Wano",
            "playGroups": [
                {
                    "sub": language,
                    "dub": "ja",
                    "cut": cut,
                    "items": [{"id": language + (cut or ""), "resolution": 1080}],
                }
            ],
        }
    )


def test_french_payload_with_quotes_unicode_and_brackets():
    data = {
        "slug": "wano",
        "title": 'Été [ "test"',
        "description": "C:\\media",
        "playlistGroups": [],
    }
    payload = json.dumps({"timeline": {"segments": [data]}})
    html = "self.__next_f.push([1," + json.dumps(payload) + "])"
    arc = parse_arcs_from_html(html)[0]
    assert arc.title == data["title"]
    assert arc.description == data["description"]


def test_merge_preserves_languages_and_cuts_without_duplicates():
    fr, en, extended = localized_arc(), localized_arc("en"), localized_arc(cut="extended")
    arc = merge_arcs([[fr], [en], [extended], [fr]])[0]
    assert len(arc.play_groups) == 3
    assert arc.get_playlist(sub="fr", variant="extended").id == "frextended"
    assert len(fr.play_groups) == 1


def test_info_multiple_languages():
    with patch(
        "onepace_assistant.cli.fetch_metadata_sync",
        side_effect=lambda language: [localized_arc(language)],
    ) as fetch:
        result = CliRunner().invoke(cli, ["info", "wano", "-l", "fr", "-l", "en", "-l", "fr"])
    assert result.exit_code == 0, result.output
    assert "Sub: fr" in result.output and "Sub: en" in result.output
    assert [call.args for call in fetch.call_args_list] == [("fr",), ("en",)]


def test_info_all_languages_reports_partial_failure():
    with (
        patch("onepace_assistant.cli.discover_languages_sync", return_value=["en", "fr"]),
        patch(
            "onepace_assistant.cli.fetch_metadata_sync",
            side_effect=[ScraperError("English unavailable"), [localized_arc()]],
        ),
    ):
        result = CliRunner().invoke(cli, ["info", "wano", "--all-languages"])
    assert result.exit_code == 0, result.output
    assert "English unavailable" in result.output
    assert "Sub: fr" in result.output


def test_info_all_failures_exit_nonzero():
    with patch("onepace_assistant.cli.fetch_metadata_sync", side_effect=ScraperError("offline")):
        result = CliRunner().invoke(cli, ["info", "wano", "-l", "fr"])
    assert result.exit_code == 1


def test_info_conflicting_flags():
    result = CliRunner().invoke(cli, ["info", "wano", "-l", "fr", "--all-languages"])
    assert result.exit_code == 2


def test_french_extended_download_selects_localized_playlist(tmp_path):
    with (
        patch(
            "onepace_assistant.cli.fetch_metadata_sync",
            return_value=[localized_arc(cut="extended")],
        ) as fetch,
        patch("onepace_assistant.cli.download_playlist_sync", return_value=[]) as download,
    ):
        result = CliRunner().invoke(
            cli,
            [
                "download",
                "wano",
                "--sub",
                "fr",
                "--variant",
                "extended",
                "--no-nfo",
                "--output",
                str(tmp_path),
            ],
            env={"PIXELDRAIN_API_KEY": ""},
        )
    assert result.exit_code == 0, result.output
    fetch.assert_called_once_with("fr")
    assert download.call_args.args[0].id == "frextended"


def test_discover_languages_from_site_metadata():
    from onepace_assistant.scraper import discover_languages_sync

    payload = json.dumps(
        [
            {"property": "og:locale", "content": "en"},
            {"property": "og:locale:alternate", "content": "fr"},
            {"property": "og:locale:alternate", "content": "pt-BR"},
        ],
    )
    html = "self.__next_f.push([1," + json.dumps(payload) + "])"
    with patch("onepace_assistant.scraper.httpx.Client") as client:
        client.return_value.__enter__.return_value.get.return_value.text = html
        assert discover_languages_sync() == ["en", "fr", "pt-BR"]


def test_missing_french_playlist_does_not_download(tmp_path):
    with (
        patch("onepace_assistant.cli.fetch_metadata_sync", return_value=[localized_arc("en")]),
        patch("onepace_assistant.cli.download_playlist_sync") as download,
    ):
        result = CliRunner().invoke(
            cli,
            ["download", "wano", "--sub", "fr", "--output", str(tmp_path)],
            env={"PIXELDRAIN_API_KEY": ""},
        )
    assert result.exit_code == 1
    assert "No playlist found" in result.output
    download.assert_not_called()


@pytest.mark.parametrize("sub", [None, "fr"])
def test_french_dub_auto_subtitles(tmp_path, sub):
    arc = Arc.model_validate(
        {
            "slug": "wano",
            "title": "Wano",
            "playGroups": [
                {"sub": sub, "dub": "fr", "items": [{"id": "french-dub", "resolution": 1080}]}
            ],
        }
    )
    with (
        patch("onepace_assistant.cli.fetch_metadata_sync", return_value=[arc]) as fetch,
        patch("onepace_assistant.cli.download_playlist_sync", return_value=[]) as download,
    ):
        result = CliRunner().invoke(
            cli,
            ["download", "wano", "--dub", "fr", "--no-nfo", "-o", str(tmp_path)],
            env={"PIXELDRAIN_API_KEY": ""},
        )
    assert result.exit_code == 0, result.output
    fetch.assert_called_once_with("fr")
    assert download.call_args.args[0].id == "french-dub"


@pytest.mark.parametrize("asynchronous", [False, True])
def test_fetch_metadata_uses_regional_locale(asynchronous):
    import asyncio

    from onepace_assistant.scraper import fetch_metadata, fetch_metadata_sync

    payload = json.dumps({"timeline": {"segments": [{"slug": "wano", "title": "Wano"}]}})
    html = "self.__next_f.push([1," + json.dumps(payload) + "])"
    urls = []

    def respond(request):
        urls.append(str(request.url))
        return httpx.Response(200, text=html)

    transport = httpx.MockTransport(respond)
    if asynchronous:
        client = httpx.AsyncClient(transport=transport)
        with patch("onepace_assistant.scraper.httpx.AsyncClient", return_value=client):
            arcs = asyncio.run(fetch_metadata("pt-BR"))
    else:
        client = httpx.Client(transport=transport)
        with patch("onepace_assistant.scraper.httpx.Client", return_value=client):
            arcs = fetch_metadata_sync("pt-BR")
    assert urls == ["https://onepace.net/pt-BR/watch"]
    assert arcs[0].slug == "wano"


@pytest.mark.parametrize("status", [404, 500])
def test_fetch_metadata_wraps_http_failures(status):
    from onepace_assistant.scraper import fetch_metadata_sync

    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(status)))
    with patch("onepace_assistant.scraper.httpx.Client", return_value=client):
        with pytest.raises(ScraperError, match="Could not fetch fr metadata"):
            fetch_metadata_sync("fr")


def test_invalid_locale_does_not_make_request():
    from onepace_assistant.scraper import fetch_metadata_sync

    with patch("onepace_assistant.scraper.httpx.Client") as client:
        with pytest.raises(ScraperError, match="Invalid language code"):
            fetch_metadata_sync("../fr")
        client.return_value.__enter__.return_value.get.assert_not_called()
