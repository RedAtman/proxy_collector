import abc
import re
from typing import Any, Dict, List, Optional


class BaseCollector(abc.ABC):
    url: str
    re_ip_encode_pattern: re.Pattern
    re_port_pattern: re.Pattern
    cur_proxy: Optional[dict]
    proxies: List[Dict[str, Any]]
    result: List[Dict[str, Any]]

    def __init__(self) -> None:
        self.cur_proxy = None
        self.proxies = []
        self.result = []

    @abc.abstractmethod
    def start(self) -> None:
        raise NotImplementedError
