from dataclasses import dataclass
from oneshot.config import Config
from oneshot.utils import b64enc, guess_image_mime
from oneshot.tables import csv_row_iterator
from collections.abc import Iterator
import re

# A convenience class to hold requests to the LLM
@dataclass
class LLMRequest:
    url: str
    headers: dict[str]
    json: dict[str]
    
@dataclass
class ImageInput:
    mimetype: str
    b64: str

# Methods to generate LLMRequest objects

#   openai
def request_openai(model_name: str,
                   question: str,
                   instructions: str|None = None,
                   context: str|None =  None,
                   images: list[ImageInput] | None = None,
                   api_key: str|None = None,
                   url: str|None = "https://api.openai.com/v1/responses",
                   temperature: float = 0.0) -> LLMRequest:
    # header contains the api key
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # if context is provided, place between <context></context> tags
    context_x = f"<context>\n{context}\n</context>" if context else None
    
    # place instructions, context, and question into input_text
    content = [
        {
            "type": "input_text",
            "text": f"{instructions or ''}\n{context_x or ''}\n{question}"
        }
    ]
    
    # if images are provided, place into content as "input_image"; append each image separately
    if images:
        for img in images:
            content.append({
                "type": "input_image",
                "image_url": f"data:{img.mimetype};base64,{img.b64}"
            })
    
    # put everything into json payload
    json={
        "model": f"{model_name}",
        "temperature": temperature,
        "input": [
            {
                "role": "user",
                "content": content,
            }
        ],
    }
    
    # return url, headers, and json payload
    return LLMRequest(url=url, headers=headers, json=json)

# ollama
def request_ollama(model_name: str,
                   question: str,
                   instructions: str|None = None,
                   context: str|None =  None,
                   images: list[ImageInput] | None = None,
                   url: str|None = None,
                   temperature: float = 0.0) -> LLMRequest:
    if not url:
        raise ValueError("Argument 'url' must be supplied!")
    headers = {} # empty by default, actually not needed
    # if context is provided, place between <context></context> tags
    context_x = f"<context>\n{context}\n</context>" if context else None
    # place instructions, context, and question into prompt
    prompt = f"{instructions or ''}\n{context_x or ''}\n{question}"
    json = {"model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }}
    # if images present, place into json under heading "images"
    if images:
        json["images"] = [img.b64 for img in images]
    
    # return url, headers (empty), and json payload
    return LLMRequest(url = url, headers = headers, json = json) 

# Request function dictionary containing functions that return LLMRequest objects
REQUESTFUN = {"openai": request_openai, "ollama": request_ollama}

# `process_config` is a function that takes a config object and returns an iterator yielding LLMRequest objects
def process_config(cfg: Config) -> Iterator[tuple[str, LLMRequest]]:
    # function for generating LLMRequest objects
    reqfun = REQUESTFUN[cfg.query.target]
    
    # singleton-image
    if (cfg.query.type == "singleton-image"):
        # package images, which are in "image" and "ref_imgs"
        images = []
        # if ref_imgs present, place those first into images
        if cfg.query.details.ref_imgs:
            for ri in cfg.query.details.ref_imgs:
                images.append(ImageInput(mimetype=guess_image_mime(ri), b64=b64enc(ri)))
        # finally place "image" into "images"
        images.append(ImageInput(guess_image_mime(cfg.query.details.image), b64=b64enc(cfg.query.details.image)))
        
        if (cfg.query.target == "ollama"):
            # create ollama-specific arguments for reqfun
            args = {"url": cfg.vendor.ollama.url, 
                    "images": images,
                    "question": cfg.query.details.question,
                    "instructions": cfg.query.details.instructions,
                    "model_name": cfg.query.model_name,
                    "temperature": cfg.query.temperature}
        elif (cfg.query.target == "openai"):
            # create openai-specific arguments for reqfun
            args = {"images": images,
                    "question": cfg.query.details.question,
                    "instructions": cfg.query.details.instructions,
                    "model_name": cfg.query.model_name,
                    "api_key": cfg.vendor.openai.api_key,
                    "temperature": cfg.query.temperature}
        else:
            # this should never happen, but let's be safe:
            return ValueError(f"Target {cfg.query.target} is currently not implemented.")
        # pass the arguments to reqfun
        yield "singleton", reqfun(**args)
    
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
        yield "singleton", reqfun(**args)
        
    # batch-image
    elif (cfg.query.type == "batch-image"):
        # determine the file iterator:
        #   default:            all the files in the directory
        #   if glob supplied:   only the files corresponding to glob pattern    
        img_files_it = cfg.query.details.img_dir.iterdir()
        if cfg.query.details.img_dir_glob:
            img_files_it = cfg.query.details.img_dir.glob(cfg.query.details.img_dir_glob)
            
        for img_file in img_files_it:
            # loop over images
            # package images into list of ImageInput
            images = []
            # if ref_imgs present, place those first into images
            if cfg.query.details.ref_imgs:
                for ri in cfg.query.details.ref_imgs:
                    images.append(ImageInput(mimetype=guess_image_mime(ri), b64=b64enc(ri)))
            # finally place current "img_file" into "images"
            images.append(ImageInput(mimetype=guess_image_mime(img_file), b64=b64enc(img_file)))
            
            # pass on to ollama or openai
            if (cfg.query.target == "ollama"):
                # create ollama-specific arguments for reqfun
                args = {"url": cfg.vendor.ollama.url, 
                        "images": images,
                        "question": cfg.query.details.question,
                        "instructions": cfg.query.details.instructions,
                        "model_name": cfg.query.model_name,
                        "temperature": cfg.query.temperature}
            elif (cfg.query.target == "openai"):
                # create openai-specific arguments for reqfun
                args = {"images": images,
                        "question": cfg.query.details.question,
                        "instructions": cfg.query.details.instructions,
                        "model_name": cfg.query.model_name,
                        "api_key": cfg.vendor.openai.api_key,
                        "temperature": cfg.query.temperature}
            else:
                # this should never happen, but let's be safe:
                return ValueError(f"Target {cfg.query.target} is currently not implemented.")
            # determine image qid
            image_qid = img_file.name
            if cfg.query.details.img_qid == "filename-regex":
                p = re.compile(cfg.query.details.img_qid_regex)
                matches = p.findall(img_file.name)
                if len(matches) > 0:
                    image_qid = matches[0]
            
            # pass the arguments to reqfun
            yield image_qid, reqfun(**args)
            
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
            yield row.get(cfg.query.details.colname_query_id, 'no query id'), reqfun(**args)
            
    else:
        # this should never happen, but let's be safe:
        return ValueError(f"Query type {cfg.query.type} is currently not implemented.")


if __name__ == "__main__":
    pass