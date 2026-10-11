#!/usr/bin/env python3
"""Fetch current South Korean laws from the National Law Information Center
(국가법령정보센터, https://www.law.go.kr) Open API (DRF).

  1. lawSearch.do?target=law  -> list of all current (현행) laws, paginated
  2. lawService.do?target=law&MST=<법령일련번호> -> full XML text of each law

Raw XML is cached under _raw/kr/ so re-runs do not re-download.

The Open API requires an `OC` parameter (the user id of a registered account at
https://open.law.go.kr). The value `test` is the sample OC used throughout the
official API guide and currently works; set LAW_OC to your own registered id
to use it instead.

Usage: python fetch.py [--raw DIR] [--workers N]
"""
import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from lxml import etree

UA = "LawCodex/1.0 (+https://github.com/LawCodex)"
BASE = "https://www.law.go.kr/DRF"
OC = os.environ.get("LAW_OC", "test")
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RAW = os.path.normpath(os.path.join(HERE, "..", "..", "_raw", "kr"))

session = requests.Session()
session.headers["User-Agent"] = UA


def get(url, params, tries=6):
    delay = 2
    for i in range(tries):
        try:
            r = session.get(url, params=params, timeout=120)
            if r.status_code == 200 and r.content.lstrip().startswith(b"<?xml"):
                return r.content
            err = f"HTTP {r.status_code} {r.content[:200]!r}"
        except requests.RequestException as e:
            err = str(e)
        print(f"  retry {i+1} {params}: {err}", file=sys.stderr)
        time.sleep(delay)
        delay = min(delay * 2, 120)
    raise RuntimeError(f"failed: {url} {params}")


def fetch_list(raw):
    d = os.path.join(raw, "list")
    os.makedirs(d, exist_ok=True)
    page, total, out = 1, None, []
    while True:
        p = os.path.join(d, f"page-{page:03d}.xml")
        if not os.path.exists(p):
            data = get(f"{BASE}/lawSearch.do", {"OC": OC, "target": "law", "type": "XML",
                                                "display": 100, "page": page})
            with open(p, "wb") as f:
                f.write(data)
            time.sleep(0.5)
        root = etree.parse(p).getroot()
        total = int(root.findtext("totalCnt"))
        laws = root.findall("law")
        out.extend(laws)
        if not laws or page * 100 >= total:
            break
        page += 1
    print(f"list: {len(out)} entries (totalCnt {total})")
    return out


def fetch_law(raw, mst):
    d = os.path.join(raw, "law", mst[-2:])
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"{mst}.xml")
    if os.path.exists(p) and os.path.getsize(p) > 0:
        return False
    data = get(f"{BASE}/lawService.do", {"OC": OC, "target": "law", "type": "XML", "MST": mst})
    tmp = p + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, p)
    time.sleep(0.3)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=DEFAULT_RAW)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    laws = fetch_list(a.raw)
    msts = sorted({l.findtext("법령일련번호") for l in laws})
    n = 0
    with ThreadPoolExecutor(max_workers=min(a.workers, 4)) as ex:
        futs = {ex.submit(fetch_law, a.raw, m): m for m in msts}
        for f in as_completed(futs):
            n += 1
            try:
                f.result()
            except Exception as e:
                print(f"ERROR {futs[f]}: {e}", file=sys.stderr)
            if n % 200 == 0:
                print(f"  {n}/{len(msts)}", flush=True)
    print("done")


if __name__ == "__main__":
    main()
