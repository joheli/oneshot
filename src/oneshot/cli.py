from rich import print
from oneshot.interface import process_config
from oneshot.config import Config
from oneshot.utils import b64enc
import requests

def cli():
    # cfg_path = Path("oneshot_prv.toml")
    # with cfg_path.open("rb") as cfg:
    #     config = tomllib.load(cfg)
        
    # print(config)
    
    cfg = Config.from_toml("oneshot_prv.toml")
    
    print(cfg)
    
    pc = process_config(cfg)
    
    for rq in pc:
        resp = requests.post(url = rq.url, headers = rq.headers, 
                             json = rq.json)
        print(resp.json())
    
if __name__ == "__main__":
    cli()