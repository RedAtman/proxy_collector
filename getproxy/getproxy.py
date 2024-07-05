#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import gevent.monkey


gevent.monkey.patch_all()

import copy
import json
import logging
import os
import pickle
import signal
import time
from typing import Dict, List

import geoip2.database
import gevent.pool
from models import Proxy
from plugin.base import BaseCollector
import requests
from utils import load_object, signal_name


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

CACHE_FILE = "cache.pickle"


class GetProxy(object):
    base_dir = os.path.dirname(os.path.realpath(__file__))

    def __init__(self, input_proxies_file=CACHE_FILE, output_proxies_file=CACHE_FILE):
        self.pool = gevent.pool.Pool(500)
        self.plugins: list[BaseCollector] = []
        # self.web_proxies: List[Proxy] = []
        self.web_proxies: Dict[str, Proxy] = {}
        self.valid_proxies: List[Proxy] = []
        self.input_proxies: List[Proxy] = []
        assert isinstance(input_proxies_file, str), "Input proxies file must be a string"
        self.input_proxies_file: str = input_proxies_file
        assert isinstance(output_proxies_file, str), "Output proxies file must be a string"
        self.output_proxies_file: str = output_proxies_file
        # TODO: maybe remove self.proxies_hash
        self.proxies_hash: Dict[str, bool] = {}
        self.origin_ip = None
        self.geoip_reader = geoip2.database.Reader(os.path.join(self.base_dir, "data/GeoLite2-Country.mmdb"))

    def _collect_result(self):
        for plugin in self.plugins:
            try:
                if not plugin.result:
                    continue

                for proxy in plugin.result:
                    obj = Proxy(**proxy)
                    self.web_proxies[obj.hash] = obj
            except Exception as err:
                logger.info(("plugin", plugin))
                logger.exception(err)

    def _validate_proxy(self, proxy: Proxy, scheme="http"):
        if proxy.hash in self.proxies_hash:
            return

        self.proxies_hash[proxy.hash] = True
        request_proxies = {scheme: "%s:%s" % (proxy.host, proxy.port)}

        request_begin = time.time()
        try:
            response_json = requests.get(
                "%s://httpbin.org/get?show_env=1&cur=%s" % (scheme, request_begin), proxies=request_proxies, timeout=5
            ).json()
        except Exception as err:
            logger.error(err)
            return

        request_end = time.time()

        if str(request_begin) != response_json.get("args", {}).get("cur", ""):
            return

        proxy.anonymity = self._check_proxy_anonymity(response_json)
        proxy.export_address = self._check_export_address(response_json)

        try:
            _country = self.geoip_reader.country(proxy.host).country
            country = _country.iso_code
            country_zh = _country.names.get("zh-CN", "")
            if country:
                proxy.country = country
            if country_zh:
                proxy.country_zh = country_zh
        except Exception:
            country = "unknown"
        proxy.response_time = round(request_end - request_begin, 2)
        proxy.type = scheme
        return proxy

    def _validate_proxy_list(self, proxies: List[Proxy], timeout=300):
        valid_proxies = []

        def save_result(p):
            if p:
                valid_proxies.append(p)

        for proxy in proxies:
            self.pool.apply_async(self._validate_proxy, args=(proxy, "http"), callback=save_result)
            self.pool.apply_async(self._validate_proxy, args=(proxy, "https"), callback=save_result)

        self.pool.join(timeout=timeout)
        self.pool.kill()

        return valid_proxies

    def _check_proxy_anonymity(self, response):
        via = response.get("headers", {}).get("Via", "")

        if self.origin_ip in json.dumps(response):
            return "transparent"
        elif via and via != "1.1 vegur":
            return "anonymous"
        else:
            return "high_anonymous"

    def _check_export_address(self, response):
        origin = response.get("origin", "").split(", ")
        if self.origin_ip in origin:
            origin.remove(self.origin_ip)
        return origin

    def _request_force_stop(self, signum, _):
        logger.warning("[-] Cold shut down")
        self.save_proxies()

        raise SystemExit()

    def _request_stop(self, signum, _):
        logger.debug("Got signal %s" % signal_name(signum))

        signal.signal(signal.SIGINT, self._request_force_stop)
        signal.signal(signal.SIGTERM, self._request_force_stop)

        logger.warning("[-] Press Ctrl+C again for a cold shutdown.")

    def init(self):
        logger.info("[*] Init")
        signal.signal(signal.SIGINT, self._request_stop)
        signal.signal(signal.SIGTERM, self._request_stop)

        rp = requests.get("http://httpbin.org/get")
        self.origin_ip = rp.json().get("origin", "")
        logger.info("[*] Current Ip Address: %s" % self.origin_ip)

    def validate_input_proxies(self):
        logger.info("[*] Validate input proxies")
        self.valid_proxies = self._validate_proxy_list(self.input_proxies)
        logger.info(
            "[*] Check %s input proxies, Got %s valid input proxies" % (len(self.proxies_hash), len(self.valid_proxies))
        )

    def load_plugins(self):
        logger.info(f"[*] Load plugins{os.path.join(self.base_dir, 'plugin')}")
        for plugin_name in os.listdir(os.path.join(self.base_dir, "plugin")):
            logger.info(f"[*] Load plugin {plugin_name}")
            if os.path.splitext(plugin_name)[1] != ".py" or plugin_name == "__init__.py":
                continue

            try:
                cls = load_object("plugin.%s.Collector" % os.path.splitext(plugin_name)[0])
            except NameError as err:
                logger.warning(err)
                continue
            except Exception as err:
                logger.exception(err)
                logger.info("[-] Load Plugin %s error: %s" % (plugin_name, str(err)))
                continue

            inst = cls()
            inst.proxies = copy.deepcopy(self.valid_proxies)
            self.plugins.append(inst)

    def grab_web_proxies(self):
        logger.info("[*] Grab proxies")

        for plugin in self.plugins:
            try:
                self.pool.spawn(plugin.start)
            except Exception as err:
                logger.error(plugin)
                logger.exception(err)

        self.pool.join(timeout=8 * 60)
        self.pool.kill()

        self._collect_result()

    def validate_web_proxies(self):
        logger.info("[*] Validate web proxies")
        input_proxies_len = len(self.proxies_hash)

        valid_proxies = self._validate_proxy_list(list(self.web_proxies.values()))
        self.valid_proxies.extend(valid_proxies)

        output_proxies_len = len(self.proxies_hash) - input_proxies_len

        logger.info(
            "[*] Check %s output proxies, Got %s valid output proxies" % (output_proxies_len, len(valid_proxies))
        )
        logger.info("[*] Check %s proxies, Got %s valid proxies" % (len(self.proxies_hash), len(self.valid_proxies)))

    def load_input_proxies(self):
        logger.info("[*] Load input proxies")
        logger.info(self.input_proxies_file)
        if self.input_proxies_file and os.path.exists(self.input_proxies_file):
            with open(self.input_proxies_file, "rb") as fd:
                self.input_proxies = pickle.load(fd)

    def save_proxies(self):
        with open(CACHE_FILE, "wb") as fd:
            pickle.dump(self.valid_proxies, fd)
        with open("proxies.json", "w") as fd:
            data = [proxy.__dict__ for proxy in self.valid_proxies]
            json.dump(data, fd)

    def save_to_csv(self):
        import csv

        with open("proxies.csv", "w") as fd:
            writer = csv.writer(fd)
            header = [
                "国家",
                "国家代码",
                "IP地址",
                "端口",
                "响应时间/秒",
                "匿名度",
                "有效性",
                "来源",
            ]
            writer.writerow(header)
            for proxy in self.valid_proxies:
                row = [
                    proxy.country_zh,
                    proxy.country,
                    proxy.host,
                    proxy.port,
                    proxy.response_time,
                    proxy.anonymity,
                    proxy.validate,
                    proxy.source,
                ]
                writer.writerow(row)

    def start(self):
        self.init()
        # self.load_input_proxies()
        self.validate_input_proxies()
        self.load_plugins()
        self.grab_web_proxies()
        self.validate_web_proxies()
        # self.save_proxies()
        self.save_to_csv()


if __name__ == "__main__":
    g = GetProxy()
    g.start()
