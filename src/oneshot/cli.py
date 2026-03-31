from rich import print
from oneshot.llm_request import process_config
from oneshot.llm_response import RESPONSEFUN, LLMResponse
from oneshot.config import Config
from oneshot.utils import measure_time
import requests
import polars as pl
from pathlib import Path
from typing import Annotated
import typer
from oneshot import __version__

"""
FUT
"""
def main(config_file: Annotated[Path, typer.Option("-c", "--config", exists=True, readable=True, dir_okay=False)] = Path("oneshot.toml")):
    f"""
    oneshot version {__version__}
    """
    cfg = Config.from_toml(config_file)
    
    records = []
    
    for qid, rq in process_config(cfg):
        raw_response, elapsed = measure_time(requests.post,
                                     url = rq.url, headers = rq.headers, 
                                     json = rq.json)
        #print(resp.json())
        responsefun = RESPONSEFUN[cfg.query.target]
        response = responsefun(raw_response.json())
        record = {"Query ID": qid,
                  "Provider": response.provider,
                  "Timepoint (UTC)": response.timepoint,
                  "Model name": response.model_name,
                  "Response": response.response_text,
                  "Elapsed (seconds)": format(elapsed, ".3f"),
                  "Usage": str(response.usage_flat)}
        records.append(record)
        print(f"Model {response.model_name} on {response.provider}:")
        print(f"Query id: {qid}")
        print(f"Response: {response.response_text}")
        print(f"Timepoint (UTC): {response.timepoint}")
        print(f"Elapsed: {elapsed:.3f} seconds\n")
    
    if cfg.out.mode == "file":
        df = pl.DataFrame(records)
        df.write_csv(cfg.out.csv_file, separator = cfg.out.csv_file_separator)
        
    
def cli():
    typer.run(main)