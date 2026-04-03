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
from rich.progress import Progress, SpinnerColumn, TextColumn
from oneshot import __version__

app = typer.Typer()

help_text = f"oneshot version {__version__}, visit https://github.com/joheli/oneshot for help"

@app.callback(invoke_without_command = True, help = help_text)
def main(config_file: Annotated[Path, typer.Option("-c", "--config", exists=True, readable=True, dir_okay=False)] = Path("oneshot.toml")):

    cfg = Config.from_toml(config_file)
    
    records = []
    
    # be friendly
    #print(f"Welcome friend! This is outshot version {__version__}. Have fun.\n")
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        for qid, rq in process_config(cfg):
            task = progress.add_task(description=f"processing query identifier '{qid}'", total=None)
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
            
            # print to standard out if so specified
            if cfg.out.mode == "standard":
                print(f"Model {response.model_name} on {response.provider}:")
                print(f"Query id: {qid}")
                print(f"Response: {response.response_text}")
                print(f"Timepoint (UTC): {response.timepoint}")
                print(f"Elapsed: {elapsed:.3f} seconds\n")
                
            # remove the line from the progress
            progress.remove_task(task_id=task)
        
        
        if cfg.out.mode == "file":
            #task = progress.add_task(description="writing to file", total = None)
            df = pl.DataFrame(records)
            df.write_csv(cfg.out.csv_file, separator = cfg.out.csv_file_separator)
            #progress.remove_task(task_id=task)        
    
def cli():
    app()