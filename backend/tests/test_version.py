from sys import version

from ..config.version_config import __version__


def test_python_version() -> None:
    assert version.startswith("3.10.5")
