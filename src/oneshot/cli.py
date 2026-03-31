from rich import print
from oneshot.llm_request import process_config
from oneshot.llm_response import RESPONSEFUN, LLMResponse
from oneshot.config import Config
from oneshot.utils import b64enc, measure_time
import requests
from pathlib import Path
import tomllib

def cli():
    
    # cfg_path = Path("oneshot_prv.toml")
    # with cfg_path.open("rb") as cfg:
    #     config = tomllib.load(cfg)
        
    # print(config)
    
    cfg = Config.from_toml("oneshot_prv.toml")
    
    #print(cfg)
    
    for qid, rq in process_config(cfg):
        raw_response, elapsed = measure_time(requests.post,
                                     url = rq.url, headers = rq.headers, 
                                     json = rq.json)
        #print(resp.json())
        responsefun = RESPONSEFUN[cfg.query.target]
        response = responsefun(raw_response.json())
        print(f"Model {response.model_name} on {response.provider}:")
        print(f"Query id: {qid}")
        print(f"Response: {response.response_text}")
        print(f"Timepoint (UTC): {response.timepoint}")
        print(f"Elapsed: {elapsed:.3f} seconds\n")
    
if __name__ == "__main__":
    cli()