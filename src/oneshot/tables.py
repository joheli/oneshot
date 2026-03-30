import polars as pl
from pathlib import Path
from typing import Iterable, Iterator, Any
from rich import print

def csv_has_columns(
    path: str | Path,
    required_columns: Iterable[str],
    *,
    separator: str = ",",
) -> bool:
    """
    Return True if all required_columns are present in the CSV header.
    """
    lf = pl.scan_csv(path, has_header=True, separator=separator)  
    existing = set(lf.collect_schema().names())  
    req = set(required_columns)
    return req.issubset(existing)

def csv_row_iterator(
    path: str | Path,
    *,
    separator: str = ",",
    named: bool = True,
) -> Iterator[dict[str, Any] | tuple[Any, ...]]:
    """
    Return an iterator over rows of the CSV.
    If named=True, yields dict-like rows; otherwise tuples.
    """
    df = pl.read_csv(path, has_header=True, separator=separator)  # [web:8][web:12]
    return df.iter_rows(named=named)  # [web:14]

if __name__ == "__main__":
    d = pl.read_csv(Path("temp/queries.csv"))
    print(d)
    colnames = ["fut","contexts"]
    csv_file = Path("temp/queries.csv")
    has_cols = csv_has_columns(csv_file, colnames)
    print(f"{csv_file.name} has {colnames}: {has_cols}")
    for row in csv_row_iterator(csv_file):
        print(f"row: {row}")
    