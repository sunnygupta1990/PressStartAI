
import http.client
from unittest.mock import patch

from src.services.highlight_reasoner import HighlightReasoner


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return b'{"response":"{\\"highlight_score\\":0.5}"}'


def test_commentary_retries_remote_disconnect_then_succeeds():
    reasoner = HighlightReasoner()
    calls = [
        http.client.RemoteDisconnected("closed"),
        FakeResponse(),
    ]

    def fake_urlopen(*args, **kwargs):
        value = calls.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    with patch("urllib.request.urlopen", side_effect=fake_urlopen), patch("time.sleep"):
        result = reasoner._generate("test")
    assert "highlight_score" in result


def test_commentary_retry_policy_has_multiple_attempts():
    assert HighlightReasoner.MAXIMUM_ATTEMPTS >= 5
