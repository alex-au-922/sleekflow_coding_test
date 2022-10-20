from sys import version

from .. import __version__


def test_python_version() -> None:
    assert version.startswith("3.10.5")
