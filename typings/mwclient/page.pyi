from _typeshed import Incomplete

from .util import handle_limit as handle_limit
from .util import parse_timestamp as parse_timestamp

class Page:
    site: Incomplete
    name: Incomplete
    namespace: Incomplete
    page_title: Incomplete
    base_title: Incomplete
    base_name: Incomplete
    touched: Incomplete
    revision: Incomplete
    exists: Incomplete
    length: Incomplete
    protection: Incomplete
    redirect: Incomplete
    pageid: Incomplete
    contentmodel: Incomplete
    pagelanguage: Incomplete
    restrictiontypes: Incomplete
    last_rev_time: Incomplete
    edit_time: Incomplete
    def __init__(self, site, name, info=None, extra_properties=None) -> None: ...
    def redirects_to(self): ...
    def resolve_redirect(self): ...
    @staticmethod
    def strip_namespace(title): ...
    @staticmethod
    def normalize_title(title): ...
    def can(self, action): ...
    def get_token(self, type, force: bool = False): ...
    def text(self, section=None, expandtemplates: bool = False, cache: bool = True, slot: str = "main"): ...
    def save(self, *args, **kwargs): ...
    def edit(self, text, summary: str = "", minor: bool = False, bot: bool = True, section=None, **kwargs): ...
    def append(self, text, summary: str = "", minor: bool = False, bot: bool = True, section=None, **kwargs): ...
    def prepend(self, text, summary: str = "", minor: bool = False, bot: bool = True, section=None, **kwargs): ...
    def handle_edit_error(self, e, summary) -> None: ...
    def touch(self) -> None: ...
    def move(
        self,
        new_title,
        reason: str = "",
        move_talk: bool = True,
        no_redirect: bool = False,
        move_subpages: bool = False,
        ignore_warnings: bool = False,
    ): ...
    def delete(self, reason: str = "", watch: bool = False, unwatch: bool = False, oldimage: bool = False): ...
    def purge(self) -> None: ...
    def backlinks(
        self,
        namespace=None,
        filterredir: str = "all",
        redirect: bool = False,
        limit=None,
        generator: bool = True,
        max_items=None,
        api_chunk_size=None,
    ): ...
    def categories(self, generator: bool = True, show=None): ...
    def embeddedin(
        self,
        namespace=None,
        filterredir: str = "all",
        limit=None,
        generator: bool = True,
        max_items=None,
        api_chunk_size=None,
    ): ...
    def extlinks(self): ...
    def images(self, generator: bool = True): ...
    def iwlinks(self): ...
    def langlinks(self, **kwargs): ...
    def links(self, namespace=None, generator: bool = True, redirects: bool = False): ...
    def revisions(
        self,
        startid=None,
        endid=None,
        start=None,
        end=None,
        dir: str = "older",
        user=None,
        excludeuser=None,
        limit=None,
        prop: str = "ids|timestamp|flags|comment|user",
        expandtemplates: bool = False,
        section=None,
        diffto=None,
        slots=None,
        uselang=None,
        max_items=None,
        api_chunk_size: int = 50,
    ): ...
    def templates(self, namespace=None, generator: bool = True): ...
