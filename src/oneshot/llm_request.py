from dataclasses import dataclass
from oneshot.config import Config
from oneshot.utils import b64enc, guess_image_mime
from oneshot.tables import csv_row_iterator
from collections.abc import Iterator

# A convenience class to hold requests to the LLM
@dataclass
class LLMRequest:
    url: str
    headers: dict[str]
    json: dict[str]

# Methods to generate LLMRequest objects

#   openai
def request_openai(model_name: str,
                   question: str,
                   instructions: str|None = None,
                   context: str|None =  None,
                   img_mime_type: str|None = None,
                   img_b64: str|None =  None,
                   api_key: str|None = None,
                   url: str|None = "https://api.openai.com/v1/responses",
                   temperature: float = 0.0) -> LLMRequest:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    context_x = None
    if context:
        context_x = f"<context>\n{context}\n</context>"
    json={
        "model": f"{model_name}",
        "temperature": temperature,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": f"{instructions or ''}\n{context_x or ''}\n{question}"},
                ],
            }
        ],
    }
    if img_b64 and img_mime_type:
        json.get("input")[0].get("content").append({"type": "input_image", "image_url": f"data:{img_mime_type};base64,{img_b64}"})
        
    return LLMRequest(url=url, headers=headers, json=json)

# ollama
def request_ollama(model_name: str,
                   question: str,
                   instructions: str|None = None,
                   context: str|None =  None,
                   img_b64: str|None =  None,
                   url: str|None = None,
                   temperature: float = 0.0) -> LLMRequest:
    if not url:
        raise ValueError("Argument 'url' must be supplied!")
    headers = {} # empty by default
    context_x = None
    if context:
        context_x = f"<context>\n{context}\n</context>"
    prompt = f"{instructions or ''}\n{context_x or ''}\n{question}"
    json = {"model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }}
    if img_b64:
        json["images"] = [img_b64]
    return LLMRequest(url = url, headers = headers, json = json) 

# Request function dictionary containing functions that return LLMRequest objects
REQUESTFUN = {"openai": request_openai, "ollama": request_ollama}

# `process_config` is a function that takes a config object and returns an iterator yielding LLMRequest objects
def process_config(cfg: Config) -> Iterator[LLMRequest]:
    # function for generating LLMRequest objects
    reqfun = REQUESTFUN[cfg.query.target]
    
    # singleton-image
    if (cfg.query.type == "singleton-image"):
        if (cfg.query.target == "ollama"):
            # create ollama-specific arguments for reqfun
            args = {"url": cfg.vendor.ollama.url, 
                    "img_b64": b64enc(cfg.query.details.image),
                    "question": cfg.query.details.question,
                    "instructions": cfg.query.details.instructions,
                    "model_name": cfg.query.model_name,
                    "temperature": cfg.query.temperature}
        elif (cfg.query.target == "openai"):
            # create openai-specific arguments for reqfun
            args = {"img_b64": b64enc(cfg.query.details.image),
                    "img_mime_type": guess_image_mime(cfg.query.details.image),
                    "question": cfg.query.details.question,
                    "instructions": cfg.query.details.instructions,
                    "model_name": cfg.query.model_name,
                    "api_key": cfg.vendor.openai.api_key,
                    "temperature": cfg.query.temperature}
        else:
            # this should never happen, but let's be safe:
            return ValueError(f"Target {cfg.query.target} is currently not implemented.")
        # pass the arguments to reqfun
        yield reqfun(**args)
    
    # singleton-text
    elif (cfg.query.type == "singleton-text"):
        if (cfg.query.target == "ollama"):
            # create ollama-specific arguments for reqfun
            args = {"url": cfg.vendor.ollama.url, 
                    "question": cfg.query.details.question,
                    "context": cfg.query.details.context,
                    "instructions": cfg.query.details.instructions,
                    "model_name": cfg.query.model_name,
                    "temperature": cfg.query.temperature}
        elif (cfg.query.target == "openai"):
            # create openai-specific arguments for reqfun
            args = {"question": cfg.query.details.question,
                    "instructions": cfg.query.details.instructions,
                    "context": cfg.query.details.context,
                    "model_name": cfg.query.model_name,
                    "api_key": cfg.vendor.openai.api_key,
                    "temperature": cfg.query.temperature}
        else:
            # this should never happen, but let's be safe:
            return ValueError(f"Target {cfg.query.target} is currently not implemented.")
        # pass the arguments to reqfun
        yield reqfun(**args)
        
    # batch-image
    elif (cfg.query.type == "batch-image"):
        # here images are taken from a directory and looped over
        for img_file in cfg.query.details.img_dir.iterdir():
            # loop over images
            if (cfg.query.target == "ollama"):
                # create ollama-specific arguments for reqfun
                args = {"url": cfg.vendor.ollama.url, 
                        "img_b64": b64enc(img_file),
                        "question": cfg.query.details.question,
                        "instructions": cfg.query.details.instructions,
                        "model_name": cfg.query.model_name,
                        "temperature": cfg.query.temperature}
            elif (cfg.query.target == "openai"):
                # create openai-specific arguments for reqfun
                args = {"img_b64": b64enc(img_file),
                        "img_mime_type": guess_image_mime(img_file),
                        "question": cfg.query.details.question,
                        "instructions": cfg.query.details.instructions,
                        "model_name": cfg.query.model_name,
                        "api_key": cfg.vendor.openai.api_key,
                        "temperature": cfg.query.temperature}
            else:
                # this should never happen, but let's be safe:
                return ValueError(f"Target {cfg.query.target} is currently not implemented.")
            # pass the arguments to reqfun
            yield reqfun(**args)
            
    # batch-text
    elif (cfg.query.type == "batch-text"):
        # here rows are taken from a csv file and looped over
        for row in csv_row_iterator(cfg.query.details.csv_file):
            # loop over rows
            if (cfg.query.target == "ollama"):
                # create ollama-specific arguments for reqfun
                args = {"url": cfg.vendor.ollama.url, 
                        "question": row.get(cfg.query.details.colname_questions, ''),
                        "context": row.get(cfg.query.details.colname_contexts, ''),
                        "instructions": row.get(cfg.query.details.colname_instructions, ''),
                        "model_name": cfg.query.model_name}
            elif (cfg.query.target == "openai"):
                # create openai-specific arguments for reqfun
                args = {"question": row.get(cfg.query.details.colname_questions, ''),
                        "context": row.get(cfg.query.details.colname_contexts, ''),
                        "instructions": row.get(cfg.query.details.colname_instructions, ''),
                        "model_name": cfg.query.model_name,
                        "api_key": cfg.vendor.openai.api_key}
            else:
                # this should never happen, but let's be safe:
                return ValueError(f"Target {cfg.query.target} is currently not implemented.")
            # pass the arguments to reqfun
            yield reqfun(**args)
            
    else:
        # this should never happen, but let's be safe:
        return ValueError(f"Query type {cfg.query.type} is currently not implemented.")


if __name__ == "__main__":
    pass