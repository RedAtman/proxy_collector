# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, division, print_function
import gevent.monkey


gevent.monkey.patch_all()
import click
import os
import sys

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[0]  # ROOT directory
print("ROOT", ROOT)
sys.path.insert(0, str(ROOT))
# sys.path.insert(0, "./getproxy")


import re
import time
import codecs
import base64
import logging
import retrying
import requests

# BASE_DIR = os.getcwd()
# print("BASE_DIR", BASE_DIR)
# sys.path.insert(0, BASE_DIR)
# sys.path.insert(0, os.path.join(BASE_DIR, "getproxy", "models"))

from getproxy import GetProxy

# pyinstaller --onefile cli.py --add-data ./data:./getproxy/data --add-data ./plugin:./getproxy/plugin


@click.command()
@click.option("--in-proxy", help="Input proxy file", default="cache.pickle")
@click.option("--out-proxy", help="Output proxy file", default="cache.pickle")
def main(in_proxy, out_proxy):
    g = GetProxy(in_proxy, out_proxy)
    g.start()


if __name__ == "__main__":
    main()
