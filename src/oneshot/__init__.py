from importlib.metadata import PackageNotFoundError, version as pkg_version  # stdlib on 3.13
from pathlib import Path
import tomllib  # stdlib on 3.13

__all__ = ["__version__"]

def _read_version_from_pyproject() -> str:
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    if not pyproject.is_file():
        return "0.0.0+local"

    with pyproject.open("rb") as f:
        data = tomllib.load(f)  # parses TOML 1.0 pyproject.toml [web:18][web:24]

    # PEP 621 style:
    try:
        return data["project"]["version"]
    except KeyError:
        # Poetry style:
        return data["tool"]["poetry"]["version"] + "+local"

try:
    __version__: str = pkg_version("yourpkg")  # name from [project].name [web:9]
except PackageNotFoundError:
    __version__ = _read_version_from_pyproject()