"""Fetch the raw Emmy nominations CSV.

Source: dmase2/emmys-data on GitHub, a canonical nominations CSV compiled for a
now-defunct "emmys app" project. No LICENSE file is present in that repo; the
underlying facts (who was nominated, who won, in what year) are historical
records of a public award, not the compiler's creative expression, so we treat
them as free to use the way Request Denied treated unlicensed DMV exports.

Run from anywhere:
    python fetch_data.py
Writes emmy_nominations.csv next to this script's parent directory.
"""
import urllib.request
import pathlib

URL = "https://raw.githubusercontent.com/dmase2/emmys-data/main/assets/data/emmy_nominations.csv"
OUT = pathlib.Path(__file__).resolve().parent.parent / "emmy_nominations.csv"

def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "quick-projects/1.0"})
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
    OUT.write_bytes(data)
    print(f"wrote {len(data):,} bytes to {OUT}")

if __name__ == "__main__":
    main()
