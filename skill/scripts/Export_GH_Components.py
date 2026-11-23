# -*- coding: utf-8 -*-
"""
Export every registered Grasshopper component from the running Rhino (GH1).

Why not scrape the website: McNeel has no full component index page, and the
registered set on your machine includes add-ons the website does not know about.
The live ComponentServer is authoritative.

Usage (Rhino 9 Python, GH must be loaded / canvas open):

    p = r"<path-to>/Export_GH_Components.py"
    exec(compile(open(p, encoding="utf-8").read(), p, "exec"))

Output: gh_components_all.tsv next to this script by default.
Override with env var GH_EXPORT_OUT (absolute path).

Columns: Name, NickName, Category, SubCategory, ComponentGuid, Kind, Obsolete, Hidden

Refresh workflow after installing add-ons or upgrading Rhino:
    1) run this script
    2) regenerate references/grasshopper-component-index.md from the TSV
"""
import os
import clr

clr.AddReference("Grasshopper")
import Grasshopper

_HERE = os.getcwd()
try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except Exception:
    pass

OUT = os.environ.get("GH_EXPORT_OUT") or os.path.join(_HERE, "gh_components_all.tsv")


def _field(obj, *names):
    """Read the first existing attribute, also trying obj.Desc (proxy wrappers vary)."""
    for n in names:
        try:
            v = getattr(obj, n)
            if v is not None:
                return str(v)
        except Exception:
            pass
    try:
        desc = obj.Desc
        for n in names:
            try:
                v = getattr(desc, n)
                if v is not None:
                    return str(v)
            except Exception:
                pass
    except Exception:
        pass
    return ""


def main():
    server = Grasshopper.Instances.ComponentServer
    proxies = list(server.ObjectProxies)

    rows = []
    for p in proxies:
        try:
            rows.append((
                _field(p, "Name"),
                _field(p, "NickName", "Nickname"),
                _field(p, "Category"),
                _field(p, "SubCategory", "Subcategory"),
                _field(p, "ComponentGuid", "Guid"),
                _field(p, "Kind"),
                _field(p, "Obsolete"),
                _field(p, "Hidden"),
            ))
        except Exception:
            pass

    def clean(s):
        return s.replace("\t", " ").replace("\n", " ").replace("\r", " ")

    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write("\t".join(clean(x) for x in r) + "\n")

    cats = {}
    for r in rows:
        cats[r[2] or "(uncategorized)"] = cats.get(r[2] or "(uncategorized)", 0) + 1
    ordered = sorted(cats.items(), key=lambda kv: -kv[1])

    print("wrote: %s" % OUT)
    print("objects: %d | categories: %d" % (len(rows), len(cats)))
    for name, count in ordered:
        print("  %-24s %4d" % (name, count))
    return OUT


main()
