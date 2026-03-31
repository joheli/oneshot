from importlib.metadata import PackageNotFoundError, version as pkg_version  # stdlib
from pathlib import Path
import tomllib  # stdlib on 3.13

PACKAGE_NAME = "oneshot"  # must match [project].name or poetry name


def _read_version_from_pyproject() -> str | None:
    # Look for pyproject.toml next to the package (src-layout friendly)
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "pyproject.toml",  # src/oneshot -> project root
        here / "pyproject.toml",         # flat layout as fallback
    ]
    for pyproject in candidates:
        if pyproject.is_file():
            with pyproject.open("rb") as f:
                data = tomllib.load(f)

            # PEP 621 style
            if "project" in data and "version" in data["project"]:
                return data["project"]["version"]

            # Poetry style
            if "tool" in data and "poetry" in data["tool"]:
                return data["tool"]["poetry"].get("version")

    return None


def _get_version() -> str:
    # 1) Installed package metadata (works from wheel)
    try:
        return pkg_version(PACKAGE_NAME)
    except PackageNotFoundError:
        pass

    # 2) Fallback to local pyproject.toml (dev/editable installs)
    version = _read_version_from_pyproject()
    if version is not None:
        return version

    # 3) Last-resort default
    return "0.0.0+unknown"


__version__ = _get_version()