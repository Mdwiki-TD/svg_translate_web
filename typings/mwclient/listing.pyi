from collections.abc import Generator

import mwclient.page
from _typeshed import Incomplete

from .util import handle_limit as handle_limit
from .util import parse_timestamp as parse_timestamp

class List:
    site: Incomplete
    list_name: Incomplete
    generator: str
    prefix: Incomplete
    args: Incomplete
    count: int
    max_items: Incomplete
    last: bool
    result_member: Incomplete
    return_values: Incomplete
    def __init__(
        self,
        site,
        list_name,
        prefix,
        limit=None,
        return_values=None,
        max_items=None,
        api_chunk_size=None,
        *args,
        **kwargs,
    ) -> None: ...
    def __iter__(self): ...
    def __next__(self): ...
    def load_chunk(self) -> None: ...
    def set_iter(self, data) -> None: ...
    @staticmethod
    def generate_kwargs(_prefix, *args, **kwargs) -> Generator[Incomplete]: ...
    @staticmethod
    def get_prefix(prefix, generator: bool = False): ...
    @staticmethod
    def get_list(generator: bool = False): ...

class NestedList(List):
    nested_param: Incomplete
    def __init__(self, nested_param, *args, **kwargs) -> None: ...
    def set_iter(self, data) -> None: ...

class GeneratorList(List):
    generator: str
    result_member: str
    page_class: Incomplete
    def __init__(self, site, list_name, prefix, *args, **kwargs) -> None: ...
    def __next__(self): ...
    def load_chunk(self): ...

class Category(mwclient.page.Page, GeneratorList):
    def __init__(self, site, name, info=None, namespace=None) -> None: ...
    def members(
        self,
        prop: str = "ids|title",
        namespace=None,
        sort: str = "sortkey",
        dir: str = "asc",
        start=None,
        end=None,
        generator: bool = True,
    ): ...

class PageList(GeneratorList):
    namespace: Incomplete
    def __init__(self, site, prefix=None, start=None, namespace: int = 0, redirects: str = "all", end=None) -> None: ...
    def __getitem__(self, name): ...
    def get(self, name, info=()): ...
    def guess_namespace(self, name): ...

class PageProperty(List):
    page: Incomplete
    generator: str
    def __init__(self, page, prop, prefix, *args, **kwargs) -> None: ...
    def set_iter(self, data) -> None: ...

class PagePropertyGenerator(GeneratorList):
    page: Incomplete
    def __init__(self, page, prop, prefix, *args, **kwargs) -> None: ...

class RevisionsIterator(PageProperty):
    def load_chunk(self): ...
