"""Splice payload.json into template.html to produce the project's index.html.

Run from the project's src/ directory (or anywhere; paths are relative to this file):
    python inject.py

Also runs catalog/tools/wrap_for_pages.py and add_catalog_link.py on the result, since a
regenerated page silently drops both the breadcrumb and (for an Artifact-shaped fragment)
the standalone-document wrapping otherwise.
"""
import json
import pathlib
import subprocess
import sys

SRC = pathlib.Path(__file__).resolve().parent
PROJECT = SRC.parent
TEMPLATE = SRC / "template.html"
PAYLOAD = PROJECT / "payload.json"
OUT = PROJECT / "index.html"

# workspace root: walk up from the project dir to find the one containing catalog/ and projects/
def find_root(start):
    p = start
    while p != p.parent:
        if (p / "catalog").is_dir() and (p / "projects").is_dir():
            return p
        p = p.parent
    raise SystemExit("could not find the workspace root (expected catalog/ and projects/ siblings)")

ROOT = find_root(PROJECT)


def main():
    template = TEMPLATE.read_text(encoding="utf-8")
    payload = PAYLOAD.read_text(encoding="utf-8")
    out = template.replace("{{PAYLOAD}}", payload)
    OUT.write_text(out, encoding="utf-8", newline="\n")
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")

    tools = ROOT / "catalog" / "tools"
    py = sys.executable
    subprocess.run([py, str(tools / "wrap_for_pages.py"), str(OUT)], check=True)
    subprocess.run([py, str(tools / "add_catalog_link.py"), str(OUT)], check=True)


if __name__ == "__main__":
    main()
