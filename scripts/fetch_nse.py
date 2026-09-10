#!/usr/bin/env python3
"""
Fetch live NSE index & stock quotes from Yahoo Finance and write data/nse.json.
Used by the GitHub Action (nse-data.yml) which runs every 5 minutes during
NSE market hours (Mon-Fri, 09:00-15:40 IST). The JSON is committed to the
repo so forcetradingyt.github.io can serve live-ish data as a static file.
"""
import json, os, datetime
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

SYMBOLS = {
    # key            yahoo symbol
    "NIFTY 50":    "%5ENSEI",
    "BANKNIFTY":   "%5ENSEBANK",
    "SENSEX":      "%5EBSESN",
    "RELIANCE":    "RELIANCE.NS",
    "HDFCBANK":    "HDFCBANK.NS",
    "TATASTEEL":   "TATASTEEL.NS",
    "INFY":        "INFY.NS",
    "SBIN":        "SBIN.NS",
    "ADANIENT":    "ADANIENT.NS",
    "ITC":         "ITC.NS",
    "BHARTIARTL":  "BHARTIARTL.NS",
    "MARUTI":      "MARUTI.NS",
}

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "nse.json"))


def fetch(symbol: str):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=15m"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode())
    meta = data["chart"]["result"][0]["meta"]
    price = meta.get("regularMarketPrice")
    prev = meta.get("chartPreviousClose") or meta.get("previousClose")
    pct = ((price - prev) / prev * 100) if prev else 0.0

    # intraday sparkline from closes
    series = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
    spark = [round(c, 2) for c in series if c is not None][-40:]

    return {
        "price": round(price, 2),
        "change": round(price - prev, 2) if prev else 0.0,
        "pct": round(pct, 2),
        "spark": spark,
    }


def main():
    out = {"updated": datetime.datetime.now(datetime.timezone.utc).isoformat(), "quotes": {}}
    ok = 0
    for key, sym in SYMBOLS.items():
        try:
            out["quotes"][key] = fetch(sym)
            ok += 1
            print(f"  ok  {key:12s} {out['quotes'][key]['price']:>12,.2f} {out['quotes'][key]['pct']:>7.2f}%")
        except Exception as e:
            print(f"  ERR {key}: {e}")
    if ok == 0:
        raise SystemExit("All fetches failed — keeping previous data file.")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))
    print(f"wrote {OUT} with {ok}/{len(SYMBOLS)} quotes")


if __name__ == "__main__":
    main()
