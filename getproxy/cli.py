# -*- coding: utf-8 -*-

import click
from getproxy import GetProxy


@click.command()
@click.option("--in-proxy", help="Input proxy file", default="proxies.json")
@click.option("--out-proxy", help="Output proxy file", default="proxies.json")
def main(in_proxy, out_proxy):
    g = GetProxy(in_proxy, out_proxy)
    g.start()


if __name__ == "__main__":
    main()
