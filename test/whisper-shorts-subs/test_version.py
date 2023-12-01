def test_version_pep440():
    from pkg_resources import parse_version
    from pkg_resources.extern.packaging.version import Version
    from whisper_shorts_subs import __version__

    assert isinstance(parse_version(__version__), Version)
