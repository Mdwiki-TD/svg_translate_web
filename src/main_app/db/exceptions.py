from __future__ import annotations


class MaxUserConnectionsError(Exception):
    pass


class InsufficientDatabaseConfigError(RuntimeError):
    def __init__(self):
        msg = "DB requires database configuration; no fallback store is available."
        super().__init__(msg)
