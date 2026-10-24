"""Tests for the models module."""

import pytest

from onepace_assistant.models import Arc, PlayGroup, Playlist


class TestArc:
    """Tests for the Arc model."""

    @pytest.fixture
    def sample_arc(self):
        return Arc(
            slug="romance-dawn",
            title="Romance Dawn",
            description="Luffy sets out on an adventure",
            special=False,
            chapters="1-7",
            episodes="1-3",
            playGroups=[
                PlayGroup(
                    sub="en",
                    dub="ja",
                    variant=None,
                    playlists=[
                        Playlist(id="abc123", resolution=480),
                        Playlist(id="def456", resolution=720),
                        Playlist(id="ghi789", resolution=1080),
                    ],
                ),
                PlayGroup(
                    sub=None,
                    dub="en",
                    variant=None,
                    playlists=[
                        Playlist(id="jkl012", resolution=720),
                    ],
                ),
            ],
        )

    def test_get_playlist_default(self, sample_arc):
        playlist = sample_arc.get_playlist(resolution=1080, sub="en", dub="ja")
        assert playlist is not None
        assert playlist.id == "ghi789"
        assert playlist.resolution == 1080

    def test_get_playlist_lower_resolution(self, sample_arc):
        playlist = sample_arc.get_playlist(resolution=720, sub="en", dub="ja")
        assert playlist is not None
        assert playlist.id == "def456"
        assert playlist.resolution == 720

    def test_get_playlist_english_dub(self, sample_arc):
        playlist = sample_arc.get_playlist(resolution=720, sub=None, dub="en")
        assert playlist is not None
        assert playlist.id == "jkl012"

    def test_get_playlist_not_found(self, sample_arc):
        playlist = sample_arc.get_playlist(resolution=1080, sub="de", dub="ja")
        assert playlist is None

    def test_available_resolutions(self, sample_arc):
        resolutions = sample_arc.available_resolutions()
        assert resolutions == {480, 720, 1080}

    def test_available_languages(self, sample_arc):
        languages = sample_arc.available_languages()
        assert len(languages) == 2
        assert {"sub": "en", "dub": "ja", "variant": None} in languages
        assert {"sub": None, "dub": "en", "variant": None} in languages

    def test_get_playlist_with_items_key(self):
        """onepace.net renamed a play group's 'playlists' key to 'items'."""
        arc = Arc.model_validate(
            {
                "slug": "romance-dawn",
                "title": "Romance Dawn",
                "playGroups": [
                    {"sub": "en", "dub": "ja", "items": [{"id": "abc", "resolution": 1080}]}
                ],
            }
        )
        assert arc.get_playlist(resolution=1080, sub="en", dub="ja").id == "abc"

    def test_renders_structured_chapters_and_episodes(self):
        """onepace.net sometimes sends {"terms": [...], "coverStories": bool}
        instead of a plain string for chapters/episodes (seen on e.g. Wano)."""
        arc = Arc.model_validate(
            {
                "slug": "wano",
                "title": "Wano",
                "chapters": {"terms": [{"from": 909, "to": 1057}], "coverStories": False},
                "episodes": {
                    "terms": [
                        {"from": 890, "to": 894},
                        {"from": 897, "to": 906},
                        {"from": 908, "to": 1028},
                        {"from": 1031, "to": 1083},
                        {"from": 1085, "to": 1085},
                    ],
                    "coverStories": False,
                },
            }
        )
        assert arc.chapters == "909-1057"
        assert arc.episodes == "890-894, 897-906, 908-1028, 1031-1083, 1085"
q
    def test_renders_text_term(self):
        """Non-numeric specials (e.g. 'One Piece Fan Letter') use a 'text' term."""
        arc = Arc.model_validate(
            {
                "slug": "one-piece-fan-letter",
                "title": "One Piece Fan Letter",
                "chapters": {"terms": [{"text": "One Piece Fan Letter"}], "coverStories": False},
            }
        )
        assert arc.chapters == "One Piece Fan Letter"
