"""Fetch through the IPv6 gateway, with the failure modes named.

The three errors you will actually hit, and what each one means:

  proxy 407              credentials wrong, or the plan does not include IPv6
  connection refused/    the TARGET has no AAAA record — nothing to connect to
    "network unreachable"
  timeout                the target has AAAA but drops v6 traffic; rare, real

    export QD_PROXY_USER=... QD_PROXY_PASS=...
    python3 fetch.py https://ipv6.google.com/ --country us
"""
from __future__ import annotations

import argparse
import os
import socket

import requests

GATEWAY = "v6.quanticdata.io:7777"

USER = os.environ.get("QD_PROXY_USER") or ""
PASS = os.environ.get("QD_PROXY_PASS") or ""
if not (USER and PASS):
    raise SystemExit("set QD_PROXY_USER and QD_PROXY_PASS")


def has_aaaa(host: str) -> bool:
    try:
        socket.getaddrinfo(host, 443, socket.AF_INET6)
        return True
    except (socket.gaierror, UnicodeError):
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--country", default="us")
    ap.add_argument("--session", default=None)
    args = ap.parse_args()

    from urllib.parse import urlparse
    host = urlparse(args.url).hostname or args.url
    if not has_aaaa(host):
        print(f"⚠ {host} publishes no AAAA record. An IPv6 exit cannot reach it.")
        print("  Use https://quanticdata.io/residential-proxies/ or "
              "https://quanticdata.io/datacenter-proxies/ instead.")

    suffix = f"-country-{args.country}" + (f"-session-{args.session}" if args.session else "")
    proxy = f"http://{USER}{suffix}:{PASS}@{GATEWAY}"

    try:
        r = requests.get(args.url, proxies={"http": proxy, "https": proxy}, timeout=45)
    except requests.exceptions.ProxyError as exc:
        text = str(exc)
        if "407" in text:
            print("proxy 407 — credentials rejected, or IPv6 is not on this plan")
        else:
            print(f"proxy error — {text[:160]}")
        return
    except requests.exceptions.ConnectTimeout:
        print("timeout — the target may advertise AAAA but drop IPv6 traffic")
        return
    except requests.RequestException as exc:
        print(f"{type(exc).__name__}: {str(exc)[:160]}")
        return

    print(f"HTTP {r.status_code}   {len(r.content):,} bytes   {r.elapsed.total_seconds():.1f}s")
    print(f"server: {r.headers.get('server', '-')}   "
          f"content-type: {r.headers.get('content-type', '-')}")
    print("\nfirst 300 characters:\n" + r.text[:300])


if __name__ == "__main__":
    main()
