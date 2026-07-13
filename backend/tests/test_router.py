from downtube.providers.router import classify, provider_for_url


def test_provider_routing() -> None:
    assert provider_for_url("https://youtube.com/watch?v=abc") == "ytdlp"
    assert provider_for_url("https://music.youtube.com/watch?v=abc") == "ytdlp"
    assert provider_for_url("https://open.spotify.com/track/abc") == "spotify"


def test_classify() -> None:
    assert classify("https://open.spotify.com/track/abc") == "track"
    assert classify("https://open.spotify.com/playlist/abc") == "playlist"
    assert classify("https://youtube.com/watch?v=abc") == "track"
    assert classify("https://youtube.com/playlist?list=abc") == "playlist"
