#!/usr/bin/env bash
# IPv6 first, residential IPv4 as the fallback — and log which path was used.
#
# This is how you get the IPv6 bandwidth saving without an outage every time a
# target turns out to be v4-only.
#
#   QD_PROXY_USER=... QD_PROXY_PASS=... bash dual_stack.sh urls.txt
set -uo pipefail
: "${QD_PROXY_USER:?set QD_PROXY_USER}"
: "${QD_PROXY_PASS:?set QD_PROXY_PASS}"

FILE="${1:-urls.txt}"
COUNTRY="${QD_COUNTRY:-us}"
V6=v6.quanticdata.io:7777
V4=pr.quanticdata.io:7777

printf "%-46s %-8s %-7s %s\n" "url" "path" "status" "seconds"

while IFS= read -r url; do
  [ -z "$url" ] && continue
  case "$url" in \#*) continue;; esac

  read -r code seconds < <(
    curl -s -o /dev/null -m 30 \
      -x "$V6" -U "$QD_PROXY_USER-country-$COUNTRY:$QD_PROXY_PASS" \
      -w '%{http_code} %{time_total}\n' "$url" 2>/dev/null || echo "000 0"
  )

  path=ipv6
  if [ "$code" = "000" ] || [ "$code" -ge 500 ] 2>/dev/null; then
    path=ipv4
    read -r code seconds < <(
      curl -s -o /dev/null -m 45 \
        -x "$V4" -U "$QD_PROXY_USER-country-$COUNTRY:$QD_PROXY_PASS" \
        -w '%{http_code} %{time_total}\n' "$url" 2>/dev/null || echo "000 0"
    )
  fi

  printf "%-46s %-8s %-7s %s\n" "${url:0:45}" "$path" "$code" "$seconds"
done < "$FILE"

echo
echo "Rows on the ipv4 path are the ones costing you residential bandwidth."
echo "Run aaaa_check.py on those hosts to confirm they are genuinely v4-only."
