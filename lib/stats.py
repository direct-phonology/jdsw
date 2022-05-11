from typing import Callable, Hashable, Dict
from collections import Counter
from functools import wraps


class StatisticsTracker:
    _instance = None

    def __new__(cls: type["StatisticsTracker"]) -> "StatisticsTracker":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.counters = {}
            # setup here
        return cls._instance

    @classmethod
    def track_stat(cls: type["StatisticsTracker"], name: str) -> None:
        cls._instance

    @classmethod
    def update_stat(cls: type["StatisticsTracker"], name: str, val: Hashable) -> None:
        pass



def track(fn: Callable) -> Callable:
    @wraps(fn)
    def wrapper(*args, **kwargs):

        fn(*args, **kwargs)

    # set up tracking

    return wrapper
