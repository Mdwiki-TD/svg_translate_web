from collections.abc import Generator

from _typeshed import Incomplete

from .sleep import Sleepers as Sleepers
from .util import handle_limit as handle_limit
from .util import parse_timestamp as parse_timestamp
from .util import read_in_chunks as read_in_chunks

__version__: str
log: Incomplete
USER_AGENT: Incomplete

class Site:
    api_limit: int
    host: Incomplete
    path: Incomplete
    ext: Incomplete
    credentials: Incomplete
    compress: Incomplete
    max_lag: Incomplete
    force_login: Incomplete
    requests: Incomplete
    scheme: Incomplete
    sleepers: Incomplete
    blocked: bool
    hasmsg: bool
    groups: Incomplete
    rights: Incomplete
    tokens: Incomplete
    version: Incomplete
    namespaces: Incomplete
    connection: Incomplete
    pages: Incomplete
    categories: Incomplete
    images: Incomplete
    Pages: Incomplete
    Categories: Incomplete
    Images: Incomplete
    initialized: bool
    chunk_size: int
    def __init__(
        self,
        host,
        path: str = "/w/",
        ext: str = ".php",
        pool=None,
        retry_timeout: int = 30,
        max_retries: int = 25,
        wait_callback=...,
        clients_useragent=None,
        max_lag: int = 3,
        compress: bool = True,
        force_login: bool = True,
        do_init: bool = True,
        httpauth=None,
        connection_options=None,
        consumer_token=None,
        consumer_secret=None,
        access_token=None,
        access_secret=None,
        client_certificate=None,
        custom_headers=None,
        scheme: str = "https",
        reqs=None,
    ) -> None: ...
    username: Incomplete
    site: Incomplete
    def site_init(self) -> None: ...
    @staticmethod
    def version_tuple_from_generator(string, prefix: str = "MediaWiki "): ...
    default_namespaces: Incomplete
    def get(self, action, *args, **kwargs): ...
    def post(self, action, *args, **kwargs): ...
    def api(self, action, http_method: str = "POST", *args, **kwargs): ...
    logged_in: Incomplete
    def handle_api_result(self, info, kwargs=None, sleeper=None): ...
    def raw_call(self, script, data, files=None, retry_on_error: bool = True, http_method: str = "POST"): ...
    def raw_api(self, action, http_method: str = "POST", retry_on_error: bool = True, *args, **kwargs): ...
    def raw_index(self, action, http_method: str = "POST", *args, **kwargs): ...
    def require(self, major, minor, revision=None, raise_error: bool = True): ...
    def email(self, user, text, subject, cc: bool = False): ...
    def login(self, username=None, password=None, cookies=None, domain=None) -> None: ...
    def clientlogin(self, cookies=None, **kwargs): ...
    def get_token(self, type, force: bool = False, title=None): ...
    def upload(
        self,
        file=None,
        filename=None,
        description: str = "",
        ignore: bool = False,
        file_size=None,
        url=None,
        filekey=None,
        comment=None,
    ): ...
    def chunk_upload(self, file, filename, ignorewarnings, comment, text): ...
    def parse(
        self, text=None, title=None, page=None, prop=None, redirects: bool = False, mobileformat: bool = False
    ): ...
    def patrol(self, rcid=None, revid=None, tags=None): ...
    def allpages(
        self,
        start=None,
        prefix=None,
        namespace: str = "0",
        filterredir: str = "all",
        minsize=None,
        maxsize=None,
        prtype=None,
        prlevel=None,
        limit=None,
        dir: str = "ascending",
        filterlanglinks: str = "all",
        generator: bool = True,
        end=None,
        max_items=None,
        api_chunk_size=None,
    ): ...
    def allimages(
        self,
        start=None,
        prefix=None,
        minsize=None,
        maxsize=None,
        limit=None,
        dir: str = "ascending",
        sha1=None,
        sha1base36=None,
        generator: bool = True,
        end=None,
        max_items=None,
        api_chunk_size=None,
    ): ...
    def alllinks(
        self,
        start=None,
        prefix=None,
        unique: bool = False,
        prop: str = "title",
        namespace: str = "0",
        limit=None,
        generator: bool = True,
        end=None,
        max_items=None,
        api_chunk_size=None,
    ): ...
    def allcategories(
        self,
        start=None,
        prefix=None,
        dir: str = "ascending",
        limit=None,
        generator: bool = True,
        end=None,
        max_items=None,
        api_chunk_size=None,
    ): ...
    def allusers(
        self,
        start=None,
        prefix=None,
        group=None,
        prop=None,
        limit=None,
        witheditsonly: bool = False,
        activeusers: bool = False,
        rights=None,
        end=None,
        max_items=None,
        api_chunk_size=None,
    ): ...
    def blocks(
        self,
        start=None,
        end=None,
        dir: str = "older",
        ids=None,
        users=None,
        limit=None,
        prop: str = "id|user|by|timestamp|expiry|reason|flags",
        max_items=None,
        api_chunk_size=None,
    ): ...
    def deletedrevisions(
        self,
        start=None,
        end=None,
        dir: str = "older",
        namespace=None,
        limit=None,
        prop: str = "user|comment",
        max_items=None,
        api_chunk_size=None,
    ): ...
    def exturlusage(
        self, query, prop=None, protocol: str = "http", namespace=None, limit=None, max_items=None, api_chunk_size=None
    ): ...
    def logevents(
        self,
        type=None,
        prop=None,
        start=None,
        end=None,
        dir: str = "older",
        user=None,
        title=None,
        limit=None,
        action=None,
        max_items=None,
        api_chunk_size=None,
    ): ...
    def checkuserlog(
        self,
        user=None,
        target=None,
        limit=None,
        dir: str = "older",
        start=None,
        end=None,
        max_items=None,
        api_chunk_size: int = 10,
    ): ...
    def random(self, namespace, limit=None, max_items=None, api_chunk_size: int = 20): ...
    def recentchanges(
        self,
        start=None,
        end=None,
        dir: str = "older",
        namespace=None,
        prop=None,
        show=None,
        limit=None,
        type=None,
        toponly=None,
        max_items=None,
        api_chunk_size=None,
    ): ...
    def revisions(self, revids, prop: str = "ids|timestamp|flags|comment|user"): ...
    def search(
        self,
        search,
        namespace: str = "0",
        what=None,
        redirects: bool = False,
        limit=None,
        max_items=None,
        api_chunk_size=None,
    ): ...
    def usercontributions(
        self,
        user,
        start=None,
        end=None,
        dir: str = "older",
        namespace=None,
        prop=None,
        show=None,
        limit=None,
        uselang=None,
        max_items=None,
        api_chunk_size=None,
    ): ...
    def users(self, users, prop: str = "blockinfo|groups|editcount"): ...
    def watchlist(
        self,
        allrev: bool = False,
        start=None,
        end=None,
        namespace=None,
        dir: str = "older",
        prop=None,
        show=None,
        limit=None,
        max_items=None,
        api_chunk_size=None,
    ): ...
    def expandtemplates(self, text, title=None, generatexml: bool = False): ...
    def ask(self, query, title=None) -> Generator[Incomplete]: ...
