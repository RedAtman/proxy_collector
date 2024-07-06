from __future__ import absolute_import, division, print_function, unicode_literals

from functools import lru_cache
import logging

import requests
import retrying

from .base import BaseCollector


logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
    "accept": "application/json",
    # "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7",
    # "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
    # "proxy-connection": "keep-alive",
    # "x-csrf-token": "491bae64ff7f62a163569c72558c69f8fe9cc4ba",
    # "x-requested-with": "XMLHttpRequest",
    # "Referer": "http://proxydb.net/?protocol=http&anonlvl=4",
    # "Referrer-Policy": "strict-origin-when-cross-origin",
}


class Collector(BaseCollector):
    def __init__(self):
        super().__init__()
        self.api_url = "http://proxydb.net/list"
        self.urls = [
            "http://proxydb.net/?protocol=http&anonlvl=4",
        ]
        # self.re_ip_port_pattern = re.compile(r'<td class="col_proxy"><a href="[^"]+">([\d.]+):(\d+)</a></td>', re.I)

    @retrying.retry(stop_max_attempt_number=3)
    def extract_proxy(self, params: dict):
        try:
            response = requests.post(
                self.api_url,
                # params={"protocol": "http", "anonlvl": "4", "offset": "0"},
                params=params,
                headers=HEADERS,
                timeout=10,
            )
            assert response.status_code == 200
            list__ip_port = response.json()
            # logger.info((len(list__ip_port), list__ip_port))

            if not list__ip_port:
                raise Exception("empty")

        except Exception as err:
            logger.exception(err)
            # logger.error("[-] Request page {page} error: {error}".format(page=page_num, error=str(err)))
            while self.proxies:
                new_proxy = self.proxies.pop(0)
                self.cur_proxy = {new_proxy.type: "%s:%s" % (new_proxy.host, new_proxy.port)}
                raise err
            else:
                return []

        return [
            {"type": item["type"], "host": item["ip"], "port": int(item["port"]), "source": "proxydb"}
            for item in list__ip_port
            if isinstance(item, dict)
        ]

    @lru_cache(maxsize=1024)
    def countries(self):
        """
        Returns:
            List[str]: list of country code
            e.g. [{"ccode":"AF","cname":"Afghanistan","count":3},...]
        """
        response = requests.get("https://proxydb.net/get_countries")
        assert response.status_code == 200
        countries = response.json()
        # logger.debug((len(countries), countries))
        return countries

    def start(self):
        params = {
            # "protocol": "http",
            # "anonlvl": "4",
            "offset": "0",
        }
        for country in self.countries():
            params["offset"] = "0"
            ccode = country.get("ccode")
            if not ccode:
                continue
            params["country"] = ccode
            page_offset = 1
            while page_offset < 5:
                result = self.extract_proxy(params)
                logger.info((country, f"page {page_offset} got {len(result)}"))
                self.result.extend(result)
                if not len(result):
                    break
                params["offset"] = str(page_offset * 15)
                page_offset += 1


if __name__ == "__main__":
    p = Collector()
    p.start()

    for i in p.result:
        print(i)

    print(len(p.result))
