from time import perf_counter
from typing import Callable, TypeVar, Tuple

T = TypeVar("T")

def measure_time(func: Callable[..., T], *args, **kwargs) -> Tuple[T, float]:
    start = perf_counter()
    result = func(*args, **kwargs)
    end = perf_counter()
    return result, end - start