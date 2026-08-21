"""Can this target be reached over IPv6 at all?

Answers the only question that matters before buying IPv6 bandwidth: does the
destination publish an AAAA record?

Why a hand-rolled DNS query instead of getaddrinfo: on a machine with no IPv6
connectivity of its own, the system resolver quietly returns IPv4-mapped
addresses (::ffff:1.2.3.4) for AF_INET6 lookups, or nothing at all. Either way
you get the wrong answer about the *target*. A direct AAAA query asks the
question that was actually meant, from any machine.

Nothing here touches the proxy — this test is free.

    python3 aaaa_check.py targets.txt
    python3 aaaa_check.py google.com github.com
"""
from __future__ import annotations

import ipaddress
import pathlib
import random
import socket
import struct
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

TYPE_A, TYPE_AAAA, CLASS_IN = 1, 28, 1


def nameserver() -> str:
    """First nameserver in /etc/resolv.conf, or a public resolver."""
    try:
        for line in pathlib.Path("/etc/resolv.conf").read_text(encoding="utf-8").splitlines():
            if line.startswith("nameserver"):
                parts = line.split()
                if len(parts) > 1 and ":" not in parts[1]:
                    return parts[1]
    except OSError:
        pass
    return "1.1.1.1"


def _encode_name(host: str) -> bytes:
    out = b""
    for label in host.rstrip(".").split("."):
        encoded = label.encode("idna") if any(ord(c) > 127 for c in label) else label.encode()
        out += bytes([len(encoded)]) + encoded
    return out + b"\x00"


def _skip_name(data: bytes, offset: int) -> int:
    while True:
        length = data[offset]
        if length == 0:
            return offset + 1
        if length & 0xC0 == 0xC0:      # compression pointer, always two bytes
            return offset + 2
        offset += 1 + length


def query(host: str, rtype: int, server: str | None = None, timeout: float = 3.0) -> list[str]:
    """One DNS question, one UDP packet. Returns the addresses in the answer section."""
    server = server or nameserver()
    ident = random.randint(0, 0xFFFF)
    packet = struct.pack(">HHHHHH", ident, 0x0100, 1, 0, 0, 0)
    packet += _encode_name(host) + struct.pack(">HH", rtype, CLASS_IN)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.sendto(packet, (server, 53))
            data, _ = sock.recvfrom(4096)
        except (socket.timeout, OSError):
            return []

    if len(data) < 12 or struct.unpack(">H", data[:2])[0] != ident:
        return []
    _, _, questions, answers, _, _ = struct.unpack(">HHHHHH", data[:12])

    offset = 12
    for _ in range(questions):
        offset = _skip_name(data, offset) + 4

    out: list[str] = []
    for _ in range(answers):
        offset = _skip_name(data, offset)
        atype, _, _, length = struct.unpack(">HHIH", data[offset:offset + 10])
        offset += 10
        rdata = data[offset:offset + length]
        offset += length
        if atype == rtype and rtype in (TYPE_A, TYPE_AAAA):
            try:
                out.append(str(ipaddress.ip_address(rdata)))
            except ValueError:
                continue
    return out


def hostname(value: str) -> str:
    value = value.strip()
    if "://" in value:
        return urlparse(value).hostname or value
    return value.split("/")[0]


def check(host: str) -> tuple[str, list[str], list[str]]:
    return host, query(host, TYPE_AAAA), query(host, TYPE_A)


def main() -> None:
    args = sys.argv[1:]
    if not args:
        raise SystemExit("usage: python3 aaaa_check.py <targets.txt | host [host…]>")

    if len(args) == 1 and pathlib.Path(args[0]).is_file():
        raw = pathlib.Path(args[0]).read_text(encoding="utf-8").splitlines()
    else:
        raw = args

    hosts = [hostname(line) for line in raw if line.strip() and not line.startswith("#")]

    print(f"resolver {nameserver()}\n")
    print(f"{'host':<34}{'AAAA':<7}{'A':<6}verdict")
    ready = 0
    with ThreadPoolExecutor(max_workers=16) as pool:
        for host, v6, v4 in pool.map(check, hosts):
            if v6:
                ready += 1
                verdict = f"IPv6 ready — {v6[0]}"
            elif v4:
                verdict = "IPv4 only — use residential/datacenter"
            else:
                verdict = "no answer (typo, or DNS blocked)"
            print(f"{host[:33]:<34}{'yes' if v6 else 'no':<7}{'yes' if v4 else 'no':<6}{verdict}")

    print(f"\n{ready}/{len(hosts)} targets reachable over IPv6.")
    if ready < len(hosts):
        print("For the rest an IPv6 proxy cannot help — the destination has no v6 address.")


if __name__ == "__main__":
    main()
