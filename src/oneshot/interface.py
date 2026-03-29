from dataclasses import dataclass
from oneshot.config import Config
from oneshot.utils import b64enc, guess_image_mime
from collections.abc import Iterator

@dataclass
class LLMRequest:
    url: str
    headers: dict[str]
    json: dict[str]
    
def request_openai(model_name: str,
                   question: str,
                   instructions: str|None = None,
                   context: str|None =  None,
                   img_mime_type: str|None = None,
                   img_b64: str|None =  None,
                   api_key: str|None = None,
                   url: str|None = "https://api.openai.com/v1/responses") -> LLMRequest:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    context_x = None
    if context:
        context_x = f"<context>\n{context}\n</context>"
    json={
        "model": f"{model_name}",
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

def request_ollama(model_name: str,
                   question: str,
                   instructions: str|None = None,
                   context: str|None =  None,
                   img_b64: str|None =  None,
                   url: str|None = None) -> LLMRequest:
    if not url:
        raise ValueError("Argument 'url' must be supplied!")
    headers = {} # empty by default
    context_x = None
    if context:
        context_x = f"<context>\n{context}\n</context>"
    prompt = f"{instructions or ''}\n{context_x or ''}\n{question}"
    json = {"model": model_name,
            "prompt": prompt,
            "stream": False}
    if img_b64:
        json["images"] = [img_b64]
    return LLMRequest(url = url, headers = headers, json = json) 

# use a Config object to get a LLMRequest object
def process_config(cfg: Config) -> Iterator[LLMRequest]:
    # lets sart with singletons
    if (cfg.query.type == "singleton-image"):
        if (cfg.query.target == "ollama"):
            args = {"url": cfg.vendor.ollama.url, 
                    "img_b64": b64enc(cfg.query.details.image),
                    "question": cfg.query.details.question,
                    "instructions": cfg.query.details.instructions,
                    "model_name": cfg.query.model_name}
            yield request_ollama(**args)
        elif (cfg.query.target == "openai"):
            args = {"img_b64": b64enc(cfg.query.details.image),
                    "img_mime_type": guess_image_mime(cfg.query.details.image),
                    "question": cfg.query.details.question,
                    "instructions": cfg.query.details.instructions,
                    "model_name": cfg.query.model_name,
                    "api_key": cfg.vendor.openai.api_key}
            yield request_openai(**args)
        else:
            return ValueError(f"The target specified in the config file is not implemented.")
    elif (cfg.query.type == "singleton-text"):
        if (cfg.query.target == "ollama"):
            args = {"url": cfg.vendor.ollama.url, 
                    "question": cfg.query.details.question,
                    "context": cfg.query.details.context,
                    "instructions": cfg.query.details.instructions,
                    "model_name": cfg.query.model_name}
            yield request_ollama(**args)
        elif (cfg.query.target == "openai"):
            args = {"question": cfg.query.details.question,
                    "instructions": cfg.query.details.instructions,
                    "context": cfg.query.details.context,
                    "model_name": cfg.query.model_name,
                    "api_key": cfg.vendor.openai.api_key}
            yield request_openai(**args)
        else:
            return ValueError(f"The target specified in the config file is not implemented.")
    elif (cfg.query.type == "batch-image"):
        for img_file in cfg.query.details.img_dir.iterdir():
            if (cfg.query.target == "ollama"):
                args = {"url": cfg.vendor.ollama.url, 
                        "img_b64": b64enc(img_file),
                        "question": cfg.query.details.question,
                        "instructions": cfg.query.details.instructions,
                        "model_name": cfg.query.model_name}
                yield request_ollama(**args)
            elif (cfg.query.target == "openai"):
                args = {"img_b64": b64enc(img_file),
                        "img_mime_type": guess_image_mime(img_file),
                        "question": cfg.query.details.question,
                        "instructions": cfg.query.details.instructions,
                        "model_name": cfg.query.model_name,
                        "api_key": cfg.vendor.openai.api_key}
                yield request_openai(**args)
            else:
                return ValueError(f"The target specified in the config file is not implemented.")
    elif (cfg.query.type == "batch-text"):
        pass

REQUESTFUN = {"openai": request_openai, "ollama": request_ollama}

if __name__ == "__main__":
    lr_data = {"model_name": "Fut",
          "question": "Watt?",
          "instructions": "You just so sis!",
          "api_key": "XXXSECRETXXX",
          "img_b64": "IMGSDAADSSADSDASDA",
          "img_mime_type": "ASDDSADSA",
          "url": "http://172.22.100.39:11434/api/generate"}
    
    lr = request_ollama(**lr_data)
    
    print(lr)