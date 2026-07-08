import base64
from pathlib import Path
import mimetypes
from time import perf_counter
from typing import Callable, TypeVar
import re

PREFIX_FILE_PATTERN = re.compile(
    r"^\[>\]"
)  # strings beginning with prefix [>] possibly carry a pathlib.Path!


def b64enc(fl: Path) -> str:
    try:
        with fl.open(mode="rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return b64
    except OSError as e:
        # Any OS-related file error ends up here
        print(f"Could not open/read file {fl}: {e}")


def guess_image_mime(path: Path) -> str:
    """
    Return MIME type for common image formats based on file extension.
    Falls back to 'application/octet-stream' if unknown.
    """
    mime, _ = mimetypes.guess_type(path)
    if mime is None:
        # sensible generic default
        return "application/octet-stream"
    return mime


T = TypeVar("T")


def measure_time(func: Callable[..., T], *args, **kwargs) -> tuple[T, float]:
    start = perf_counter()
    result = func(*args, **kwargs)
    end = perf_counter()
    return result, end - start


def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    items: dict[str, object] = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items


def bestfile(p: Path) -> Path:
    # if p does not exist, return
    if not p.exists():
        return p
    else:
        # is the last character a digit?
        if p.stem[-1].isdigit():
            d = int(p.stem[-1])
            new_file = p.parent.absolute() / f"{p.stem[:-1]}{d + 1}{p.suffix}"
        else:
            # append digit to stem
            new_file = p.parent.absolute() / f"{p.stem}0{p.suffix}"
        # return
        return bestfile(new_file)


def path_in_string(
    s: str,
    *,
    path_pattern: re.Pattern = PREFIX_FILE_PATTERN,
    only_existing=True,
    no_dir=True,
) -> Path | None:
    """
    `path_in_string` checks whether a path is hidden in a string.
    Strings potentially carrying paths start with `PREFIX_FILE_PATTERN` [>].
    The function returns the found path or None, if no path was verified.
    """
    # if the prefix is present then a split returns exactly 2 parts
    parts = path_pattern.split(s)
    if len(parts) == 2:
        # ok
        possible_path = parts[1]  # the second part possibly contains a path
        try:
            extracted_path = Path(possible_path)
            if only_existing:
                assert extracted_path.exists()
            if no_dir:
                assert not extracted_path.is_dir()
            return extracted_path
        except:
            # any error suggests there is no path hidden in the string
            return
    else:
        # if length is not exactly 2 it's not worth looking
        return


def textfile_content(t: Path, *, enc: str = "utf-8") -> str:
    try:
        with t.open(mode="r", encoding=enc) as tf:
            content = tf.read()
        return content
    except:
        return ""


def pth(s: str, *, path_pattern=PREFIX_FILE_PATTERN) -> str:
    """
    `pth` takes a string and checks whether it carries a path to a text file.
    If yes, it returns the contents of the file as a string.
    If no, it returns `s` unchanged.
    """
    res = s
    p = path_in_string(s, path_pattern=path_pattern)
    if p:
        res = textfile_content(p)
    return res


if __name__ == "__main__":
    # b = b64enc(Path("demo/resized.jpg"))
    # b = guess_image_mime(Path("README.md"))
    # print(b)
    path1 = "[>]README.md"
    path2 = "Kerstin"
    path3 = "[>]demo/input/comparison_dunno.png"
    path4 = "[>]demo/fujo.txt"
    path5 = "[>]demo/input"
    path6 = ""
    print(f"""p1: {pth(path1)[:50]}, p2: {pth(path2)[:50]}, p3: {pth(path3)[:50]}, 
          p4: {pth(path4)[:50]}, p5: {pth(path5)[:50]}, p6: {pth(path6)[:50]}""")
