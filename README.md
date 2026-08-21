# IPv6 proxy examples — the cheapest bandwidth you can buy, and its one catch

[IPv6 proxies](https://quanticdata.io/ipv6-proxies/) are the cheapest tier per gigabyte by a
wide margin, for a simple reason: IPv6 address space is enormous, so addresses are not scarce.

The catch is equally simple. **The target must speak IPv6.** If it publishes no `AAAA` record,
no IPv6 proxy in the world can reach it — and a large share of the web still does not.

Gateway: `v6.quanticdata.io:7777`

```bash
export QD_PROXY_USER=your_user QD_PROXY_PASS=your_pass

python3 aaaa_check.py targets.txt          # check IPv6 reachability BEFORE you buy
python3 fetch.py https://ipv6.google.com/  # fetch through the v6 gateway
bash dual_stack.sh                          # v6 with a v4 fallback
```

## Files

| File | What it does |
|---|---|
| [`aaaa_check.py`](aaaa_check.py) | resolve `AAAA` for a list of hosts — the go/no-go test |
| [`fetch.py`](fetch.py) | fetch through the IPv6 gateway, with the errors decoded |
| [`dual_stack.sh`](dual_stack.sh) | try IPv6, fall back to residential IPv4 on failure |

## Check first, always

```bash
python3 aaaa_check.py targets.txt
```

```
host                          AAAA   A     verdict
google.com                    yes    yes   IPv6 ready
github.com                    no     yes   IPv4 only — use residential/datacenter
example-shop.test             no     yes   IPv4 only — use residential/datacenter
```

Two minutes here saves a week of "the proxy does not work". It is not the proxy; the destination
has no IPv6 address to connect to.

## Using it

```bash
curl -x v6.quanticdata.io:7777 -U "USER-country-us:PASS" https://ipv6.google.com/
```

Same [username modifiers](https://github.com/quantumproxies/quanticdata-proxy-quickstart) as the
other networks: `-country-`, `-session-`, `-sessTime-`.

## Where IPv6 genuinely wins

- **High-volume fetching of IPv6-ready targets** — Google properties, most large CDNs, plenty of
  modern APIs. The bandwidth saving is real and large.
- **Address diversity.** A /64 holds more addresses than the entire IPv4 internet, so per-IP
  rate limits behave very differently.

## Where it does not

- **Any IPv4-only target.** No workaround exists at the proxy layer.
- **Targets that treat IPv6 as suspicious.** Some anti-bot vendors score IPv6 ranges more harshly
  precisely because addresses are cheap. Test on your target, do not assume.

`dual_stack.sh` is the practical answer to both: attempt IPv6, fall back to
[residential](https://quanticdata.io/residential-proxies/) when it fails, and log which path
each request took so you can see what you are actually paying for.

## Related

- [IPv6 proxies](https://quanticdata.io/ipv6-proxies/) · [Datacenter proxies](https://quanticdata.io/datacenter-proxies/) · [Residential proxies](https://quanticdata.io/residential-proxies/)
- [Proxy quickstart](https://github.com/quantumproxies/quanticdata-proxy-quickstart) · [Documentation](https://quanticdata.io/docs/)
- [How to use a proxy with Python requests](https://quanticdata.io/blog/how-to-use-a-proxy-with-python-requests/)

MIT licensed.
