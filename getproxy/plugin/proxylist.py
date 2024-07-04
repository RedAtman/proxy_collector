#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import base64
import logging
import re
import time

import requests
import retrying

from .base import BaseCollector


logger = logging.getLogger(__name__)


class Proxy(BaseCollector):
    def __init__(self):
        super().__init__()
        self.url = "http://proxy-list.org/english/index.php?p={page}"  # 从1-10
        self.re_ip_port_encode_pattern = re.compile(r"Proxy\(\'([\w\d=+]+)\'\)", re.I)

    @retrying.retry(stop_max_attempt_number=3)
    def extract_proxy(self, page_num: int):
        try:
            rp = requests.get(self.url.format(page=page_num), proxies=self.cur_proxy, timeout=10)
            re_ip_port_encode_result = self.re_ip_port_encode_pattern.findall(rp.text)

            if not re_ip_port_encode_result:
                raise Exception("empty")

        except Exception as e:
            logger.error("[-] Request page {page} error: {error}".format(page=page_num, error=str(e)))
            while self.proxies:
                new_proxy = self.proxies.pop(0)
                self.cur_proxy = {new_proxy["type"]: "%s:%s" % (new_proxy["host"], new_proxy["port"])}
                raise e
            else:
                return []

        re_ip_port_result = []
        for each_result in re_ip_port_encode_result:
            decode_ip_port = base64.b64decode(each_result).decode("utf-8")
            host, port = decode_ip_port.split(":")
            re_ip_port_result.append({"host": host, "port": int(port), "from": "proxylist"})

        return re_ip_port_result

    def start(self):
        for page in range(1, 10):
            page_result = self.extract_proxy(page)
            time.sleep(3)

            if not page_result:
                return

            self.result.extend(page_result)


if __name__ == "__main__":
    p = Proxy()
    p.start()

    for i in p.result:
        print(i)
