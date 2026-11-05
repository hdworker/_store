#!/usr/bin/env python3
"""Регенерация reference-manifest.json в _store (дампы в git не хранятся)."""

import hashlib
import io
import json
import os
import re
import sys
import time

STORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(STORE, "reference")
CFG = os.path.join(REF, "config")


def read_text(path):
    try:
        return io.open(path, encoding="utf-8-sig", errors="replace").read()
    except OSError:
        return ""


def md5(path):
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return ""


def main():
    config_refs = []
    if os.path.isdir(CFG):
        for d in sorted(os.listdir(CFG)):
            p = os.path.join(CFG, d)
            if not os.path.isdir(p):
                continue
            files = 0
            total = 0
            for dp, _dn, fn in os.walk(p):
                for f in fn:
                    files += 1
                    try:
                        total += os.path.getsize(os.path.join(dp, f))
                    except OSError:
                        pass
            cfg = os.path.join(p, "Configuration.xml")
            name = version = ""
            if os.path.isfile(cfg):
                t = read_text(cfg)
                m = re.search(r"<Name>([^<]*)</Name>", t)
                v = re.search(r"<Version>([^<]*)</Version>", t)
                name = m.group(1).strip() if m else ""
                version = v.group(1).strip() if v else ""
            config_refs.append({
                "folder": d, "name": name, "version": version, "path": p,
                "files": files, "size_mb": round(total / 2 ** 20, 1),
                "config_md5": md5(cfg) if os.path.isfile(cfg) else "",
                "mtime": time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(p))),
            })

    idx = {}
    try:
        idx = json.load(io.open(os.path.join(STORE, "store-index.json"), encoding="utf-8-sig"))
    except Exception:
        pass

    manifest = {
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "note": "Генерируется tools/store-manifest.py; дампы в git не хранятся",
        "config_references": config_refs,
        "extension_snapshots": idx.get("reference_extensions", []),
    }
    out = os.path.join(STORE, "reference-manifest.json")
    io.open(out, "w", encoding="utf-8").write(json.dumps(manifest, ensure_ascii=False, indent=2))
    print("manifest: config refs=%d, extension snapshots=%d -> %s" %
          (len(config_refs), len(manifest["extension_snapshots"]), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
