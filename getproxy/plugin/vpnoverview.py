from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import re

import requests
import retrying

from .base import BaseCollector


logger = logging.getLogger(__name__)


class Collector(BaseCollector):
    def __init__(self):
        super().__init__()
        self.urls = [
            "https://vpnoverview.com/privacy/anonymous-browsing/free-proxy-servers/",
        ]
        self.re_ip_port_pattern = re.compile(
            r"<tr><td><strong>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</strong></td><td>(\d{1,5})</td>", re.I
        )

    @retrying.retry(stop_max_attempt_number=3)
    def extract_proxy(self, url: str):
        try:
            response = requests.get(
                url,
                # headers=self.HEADERS,
                proxies=self.cur_proxy,
                timeout=10,
                # verify=False,
            )
            text = self.decode(response.content)
            # logger.debug(text)
            list__ip_port = self.re_ip_port_pattern.findall(text)
            logger.debug((len(list__ip_port), list__ip_port))

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

        return [{"host": host, "port": int(port), "source": "vpnoverview"} for host, port in list__ip_port]


if __name__ == "__main__":
    p = Collector()
    p.start()

    for i in p.result:
        print(i)

    print(len(p.result))
