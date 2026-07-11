from rich import print
from oneshot.llm_request import process_config, curl_log_message
from oneshot.llm_response import RESPONSEFUN
from oneshot.config import Config
from oneshot.utils import measure_time, bestfile
import requests
import polars as pl
from pathlib import Path
from typing import Annotated
import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
from oneshot import __version__
from loguru import logger

# import sys

# configure once at module import time
logger.remove()

# # Do not log to the console for the time being.
# logger.add(
#     sys.stderr,
#     level="INFO",
#     colorize=True,
#     format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
#            "<level>{level: <8}</level> | "
#            "{extra[qid]} | {message}",
# )

logger.add(
    "oneshot.log",
    level="DEBUG",
    rotation="1 week",
    retention="8 weeks",
    compression="zip",
    enqueue=True,
    backtrace=True,
    diagnose=False,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[qid]} | {name}:{function}:{line} | {message}",
)


def get_logger(qid: str | None = None):
    return logger.bind(qid=qid or "-")

app = typer.Typer()

help_text = (
    f"oneshot version {__version__}, visit https://github.com/joheli/oneshot for help"
)


@app.callback(invoke_without_command=True, help=help_text)
def main(
    config_file: Annotated[
        Path, typer.Option("-c", "--config", exists=True, readable=True, dir_okay=False)
    ] = Path("oneshot.toml"),
):
    log = get_logger()
    log.info("Starting oneshot with config file '{}'", config_file)

    try:
        cfg = Config.from_toml(config_file)
        log.info("Configuration loaded successfully")
        log.debug("Output mode='{}', target='{}'", cfg.out.mode, cfg.query.target)
    except Exception:
        log.exception("Failed to load configuration from '{}'", config_file)
        raise

    records = []
    writeout = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        for qid, rq in process_config(cfg):
            qlog = get_logger(str(qid))
            qlog.info("Processing query started")
            qlog.debug("Request prepared for url='{}'", rq.url)

            task = progress.add_task(
                description=f"processing query identifier '{qid}'", total=None
            )

            try:
                # record the whole request so it can be passed on:
                #qlog.debug("Data passed to API:\nurl: {}\nheaders: {}\njson body:\n{}\n\n\n", rq.url, rq.headers, rq.json)
                qlog.debug("Curl call to reproduce API call\n{}", curl_log_message(rq))
                raw_response, elapsed = measure_time(
                    requests.post, url=rq.url, headers=rq.headers, json=rq.json # add timeout
                )
                qlog.info(
                    "HTTP POST completed with status_code={} in {:.3f}s",
                    raw_response.status_code,
                    elapsed,
                )
                raw_response.raise_for_status()
            except requests.RequestException:
                qlog.exception("HTTP POST failed")
                progress.remove_task(task_id=task)
                continue

            try:
                responsefun = RESPONSEFUN[cfg.query.target]
                response = responsefun(raw_response.json())
                qlog.debug(
                    "Response parsed: provider='{}', model='{}'",
                    response.provider,
                    response.model_name,
                )
            except Exception:
                qlog.exception("Failed to decode or transform API response")
                progress.remove_task(task_id=task)
                continue

            response_text_llm = response.response_text
            qlog.debug("LLM response length={}", len(response_text_llm))
            qlog.debug("The actual text returned from the LLM:\n\n{}\n\n", response_text_llm)

            if len(response_text_llm) > cfg.out.response_to_file_length_threshold:
                response_to_file_filename = cfg.out.response_to_file_filename.replace(
                    "~qid~", str(qid)
                )
                writeout.append(
                    {
                        "file": response_to_file_filename,
                        "content": response.response_text,
                    }
                )
                qlog.info(
                    "Response exceeds threshold {}; queued for separate file '{}'",
                    cfg.out.response_to_file_length_threshold,
                    response_to_file_filename,
                )
                response_text_llm = f"see {response_to_file_filename}"

            record = {
                "Query ID": qid,
                "Provider": response.provider,
                "Timepoint (UTC)": response.timepoint,
                "Model name": response.model_name,
                "Response": response_text_llm,
                "Elapsed (seconds)": format(elapsed, ".3f"),
                "Usage": str(response.usage_flat),
            }
            records.append(record)
            qlog.info("Record appended; total records={}", len(records))

            if cfg.out.mode == "standard":
                qlog.debug("Writing response to standard output")
                print(f"Model {response.model_name} on {response.provider}:")
                print(f"Query id: {qid}")
                print(f"Response: {response.response_text}")
                print(f"Timepoint (UTC): {response.timepoint}")
                print(f"Elapsed: {elapsed:.3f} seconds\n")

            progress.remove_task(task_id=task)
            qlog.info("Processing query finished")

        if cfg.out.mode == "file":
            try:
                log.info("Writing {} records to csv '{}'", len(records), cfg.out.csv_file)
                df = pl.DataFrame(records)
                df.write_csv(cfg.out.csv_file, separator=cfg.out.csv_file_separator)
                log.info("CSV written successfully to {}", cfg.out.csv_file)
            except Exception:
                log.exception("Failed to write csv output")
                raise

            if len(writeout) > 0:
                log.info("Writing {} long responses to separate files", len(writeout))
                for w in writeout:
                    try:
                        writeout_file = cfg.out.csv_file.parent / w.get("file")
                        writeout_file_best = bestfile(writeout_file)
                        writeout_file_best.write_text(w.get("content"), encoding="utf-8")
                        log.info("Wrote long response file '{}'", writeout_file_best)
                    except Exception:
                        log.exception("Failed to write long response file '{}'", w.get("file"))
                        raise

    log.info("Run completed successfully: {} records, {} long-response files", len(records), len(writeout))


def cli():
    app()
