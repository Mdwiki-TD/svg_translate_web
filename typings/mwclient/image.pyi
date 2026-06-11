from _typeshed import Incomplete

from . import page
from .util import handle_limit as handle_limit

class Image(page.Page):
    imagerepository: Incomplete
    imageinfo: Incomplete
    def __init__(self, site, name, info=None) -> None: ...
    def imagehistory(self): ...
    def imageusage(
        self,
        namespace=None,
        filterredir: str = "all",
        redirect: bool = False,
        limit=None,
        generator: bool = True,
        max_items=None,
        api_chunk_size=None,
    ): ...
    def duplicatefiles(self, limit=None, max_items=None, api_chunk_size=None): ...
    def download(self, destination=None): ...
