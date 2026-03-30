import pydantic as pd
from typing_extensions import Self
from typing import Literal, Annotated, Any
from pathlib import Path
import tomllib
from oneshot.tables import csv_has_columns

class Ollama(pd.BaseModel):
    host: pd.AnyHttpUrl | None = None
    # helper variable to be set by model_validator
    url: str | None =  None
    
    @pd.model_validator(mode = "after")
    def add_url(self) -> Self:
        if self.host:
            self.url = f"{self.host}api/generate"
        return self

class Openai(pd.BaseModel):
    api_key: str | None = None

class Vendor(pd.BaseModel):
    ollama: Ollama | None = None
    openai: Openai | None = None
    
    # check if at least one defined
    @pd.model_validator(mode = "after")
    def at_least_one(self) -> Self:
        # only allow variables with meaningful entries, otherwise set None
        if self.ollama:
            if not self.ollama.host:
                self.ollama = None
        if self.openai:
            if not self.openai.api_key:
                self.openai = None
        # at least one should remain, otherwise raise error
        if not (self.ollama or self.openai):
            raise ValueError("At least one vendor has to be specified.")
        return self
    
class Singleton(pd.BaseModel):
    instructions: str
    question: str
    
class SingletonText(Singleton):
    context: str

class SingletonImage(Singleton):
    image: pd.FilePath
    
class BatchText(pd.BaseModel):
    csv_file: pd.FilePath
    colname_instructions: str = "instructions"
    colname_questions: str = "questions"
    colname_contexts: str| None = None
    
    @pd.model_validator(mode="after")
    def check_csv_file(self) -> Self:
        # check if table file has suffix .csv
        if not self.csv_file.suffix.lower() == ".csv":
            raise ValueError(f"{self.csv_file.name} has to be a csv file!")
        # check if csv file has the required column names
        column_names = [self.colname_instructions, self.colname_contexts, self.colname_questions]
        required_columns = [c for c in column_names if c is not None]
        if not csv_has_columns(self.csv_file, required_columns):
            raise ValueError(f"{self.csv_file.name} does not have required column names {required_columns}.")
        return self
    
class BatchImage(Singleton):
    img_dir: pd.DirectoryPath

class Query(pd.BaseModel):
    type: Literal["singleton-text", "singleton-image", "batch-text", "batch-image"]
    target: Literal["ollama", "openai"]
    model_name: Annotated[str, pd.Field(max_length = 40)]
    temperature: Annotated[float, pd.Field(ge = 0.0, le = 1.0)]
    details: SingletonText | SingletonImage | BatchText | BatchImage
    
    # check the data passed in "details"
    # - does it correspond to SingletonText | SingletonImage | BatchText | BatchImage ?
    @pd.model_validator(mode="before")
    @classmethod
    def fill_details(cls, data: Any) -> Any:
        # only allow dict to be processed
        if not isinstance(data, dict):
            return data
        
        # q_type - see variable "type" which has not been validated yet 
        q_type = data.get("type")
        raw_details = data.get("details")

        # if details is missing, let normal validation handle it
        if raw_details is None:
            return data

        # already a model instance? then do nothing here
        if isinstance(raw_details, (SingletonText, SingletonImage, BatchText, BatchImage)):
            return data

        # choose the appropriate details model based on type
        if q_type == "singleton-text":
            model = SingletonText
        elif q_type == "singleton-image":
            model = SingletonImage
        elif q_type == "batch-text":
            model = BatchText
        elif q_type == "batch-image":
            model = BatchImage
        else:
            # unknown type, let the main validation raise
            return data

        # validate and replace
        data["details"] = model.model_validate(raw_details)
        return data
    
class Config(pd.BaseModel):
    vendor: Vendor
    query: Query
    
    @pd.model_validator(mode = "after")
    def target_defined(self) -> Self:
        # does vendor provide information corresponding to target?
        if not getattr(self.vendor, self.query.target):
            # if no raise error
            raise ValueError(f"Target {self.query.target} is not defined!")
        return self
    
    @classmethod
    def from_toml(cls, path: str | Path) -> "Config":
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(str(p))
        data = tomllib.loads(p.read_text(encoding="utf-8"))
        return cls.model_validate(data)