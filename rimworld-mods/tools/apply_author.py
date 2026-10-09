"""Stamp author.config into every mod's About/About.xml.

Sets <author> and replaces the part of <packageId> before the first dot,
keeping the mod's own name after it. Run from anywhere:

    python3 tools/apply_author.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read_config():
    cfg = {}
    for line in (ROOT / "author.config").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        cfg[key.strip()] = value.strip()
    return cfg


def xml_escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    cfg = read_config()
    author, prefix = cfg.get("author", ""), cfg.get("package_prefix", "")
    if not author or not re.fullmatch(r"[A-Za-z0-9]+", prefix):
        sys.exit("author.config needs an author and a package_prefix of letters and digits only")

    for about in sorted(ROOT.glob("*/About/About.xml")):
        text = about.read_text(encoding="utf-8")
        new = re.sub(r"<author>.*?</author>", f"<author>{xml_escape(author)}</author>", text, count=1)
        new = re.sub(r"<packageId>[^.<]+\.", f"<packageId>{prefix}.", new, count=1)
        if new != text:
            about.write_text(new, encoding="utf-8")
            print(f"updated {about.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
