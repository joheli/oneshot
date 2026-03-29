import polars as pl
from pathlib import Path
from rich import print

if __name__ == "__main__":
    d = pl.read_csv(Path("temp/queries.csv"))
    print(d)