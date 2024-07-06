import abc
import logging
import re
from typing import Any, Dict, List, Optional

from models import Proxy


logger = logging.getLogger(__name__)


class BaseCollector(abc.ABC):
    HEADERS = {
        # "Accept": "application/json",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7",
        "Content-Type": "application/json; charset=UTF-8",
        # 'Cookie': 'SESSION_COOKIE_NAME_PREFIX=redatman_',
        # "Host": "httpbin.org",
        # "Sec-Ch-Ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
        # "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "macOS",
        # "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        # "Sec-Fetch-Site": "none",
        # "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        # "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # "User-Agent": "Magic Browser",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/",
    }
    url: str
    urls: List[str]
    re_ip_encode_pattern: re.Pattern
    re_port_pattern: re.Pattern
    cur_proxy: Optional[dict]
    proxies: List[Proxy]
    result: List[Dict[str, Any]]

    def __init__(self) -> None:
        self.cur_proxy = None
        self.proxies = []
        self.result = []

    # @abc.abstractmethod
    # def start(self) -> None:
    #     raise NotImplementedError

    @abc.abstractmethod
    def extract_proxy(self, url: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def start(self):
        for url in self.urls:
            try:
                page_result = self.extract_proxy(url)
            except:
                continue

            if not page_result:
                continue

            self.result.extend(page_result)

    @staticmethod
    def decode(content: bytes) -> str:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            logger.debug("try gb2312")
            try:
                text = content.decode("gb2312")
            except UnicodeDecodeError:
                logger.debug("try ISO-8859-1")
                text = content.decode("ISO-8859-1")  # 尝试其他常见编码
        return text

        import chardet

        encoding = chardet.detect(content)["encoding"]
        logger.debug(encoding)
        # response.encoding = encoding

        # Decode using the detected encoding
        # decoded_content = response.text
        assert isinstance(encoding, str), "encoding must be str, not {}".format(type(encoding))
        encoding = "utf-8"
        text = content.decode(encoding)
        logger.debug(text)
        return text
        # logger.debug(content)
        # logger.debug(content)
        text = content.decode("utf-8")
        return text
