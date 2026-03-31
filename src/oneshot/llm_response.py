from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime, timezone
from oneshot.utils import flatten_dict

@dataclass
class LLMResponse:
    provider: str                 # "ollama" or "openai"
    timepoint: datetime           # always UTC, tz-aware
    model_name: str
    temperature: Optional[float]
    response_text: str
    usage: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)
    usage_flat: dict[str, Any] = field(init = False)    # flattened version of usage
    raw_flat: dict[str, Any] = field(init = False)      # flattened version of raw
    
    def __post_init__(self):
        self.usage_flat = flatten_dict(self.usage)
        self.raw_flat = flatten_dict(self.raw)


def _parse_ollama_time(created_at: str) -> datetime:
    """
    Ollama: ISO 8601 with 'Z', e.g. '2026-03-30T10:52:03.832362628Z'
    Normalize to UTC datetime (truncate extra ns if needed).
    """
    if created_at is None:
        return datetime.now(timezone.utc)

    # Drop trailing 'Z', keep up to 6 microseconds for Python's datetime
    ts = created_at.rstrip("Z")
    if "." in ts:
        date_part, frac = ts.split(".", 1)
        # keep up to 6 digits (microseconds)
        frac = frac[:6]
        ts = f"{date_part}.{frac}"
    # Add explicit UTC offset
    return datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)


def _parse_openai_time(created_at: int) -> datetime:
    """
    OpenAI: Unix timestamp (seconds since epoch, UTC).
    """
    if created_at is None:
        return datetime.now(timezone.utc)
    return datetime.fromtimestamp(created_at, tz=timezone.utc)


def from_ollama_responses(resp: dict[str, Any]) -> LLMResponse:
    usage = {
        "prompt_tokens": resp.get("prompt_eval_count"),
        "completion_tokens": resp.get("eval_count"),
        "total_tokens": (
            (resp.get("prompt_eval_count") or 0)
            + (resp.get("eval_count") or 0)
        ),
        "timings_ns": {
            "total_duration": resp.get("total_duration"),
            "load_duration": resp.get("load_duration"),
            "prompt_eval_duration": resp.get("prompt_eval_duration"),
            "eval_duration": resp.get("eval_duration"),
        },
        "context_length": len(resp.get("context") or []),
    }

    return LLMResponse(
        provider="ollama",
        timepoint=_parse_ollama_time(resp.get("created_at")),
        model_name=resp.get("model", ""),
        temperature=None,  # only known from request/options, not echoed
        response_text=resp.get("response", ""),
        usage=usage,
        raw=resp,
    )


def from_openai_responses(resp: dict[str, Any]) -> LLMResponse:
    response_text = ""
    output = resp.get("output") or []
    if output:
        msg = output[0]
        contents = msg.get("content") or []
        for item in contents:
            if item.get("type") == "output_text":
                response_text = item.get("text", "")
                break

    usage = resp.get("usage") or {}

    return LLMResponse(
        provider="openai",
        timepoint=_parse_openai_time(resp.get("created_at")),
        model_name=resp.get("model", ""),
        temperature=resp.get("temperature"),
        response_text=response_text,
        usage=usage,
        raw=resp,
    )
    
RESPONSEFUN = {"openai": from_openai_responses, "ollama": from_ollama_responses}