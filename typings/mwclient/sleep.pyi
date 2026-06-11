from _typeshed import Incomplete

from .errors import MaximumRetriesExceeded as MaximumRetriesExceeded

log: Incomplete

class Sleepers:
    max_retries: Incomplete
    retry_timeout: Incomplete
    callback: Incomplete
    def __init__(self, max_retries, retry_timeout, callback=...) -> None: ...
    def make(self, args=None): ...

class Sleeper:
    args: Incomplete
    retries: int
    max_retries: Incomplete
    retry_timeout: Incomplete
    callback: Incomplete
    def __init__(self, args, max_retries, retry_timeout, callback) -> None: ...
    def sleep(self, min_time: int = 0) -> None: ...
