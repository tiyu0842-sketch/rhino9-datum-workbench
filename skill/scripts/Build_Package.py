# -*- coding: utf-8 -*-
"""Generic Rhino 9 yak packager. Pure local Python 3, no Rhino needed.

Copy into a plugin's verification/ folder, edit the PROJECT BLOCK, then run:
    python verification/Build_Package.py

Handles: copy rhp/rui/docs/icons into install/, write manifest.yml, zip the
package with the canonical rhp filename (even when compiling to a variant
name to dodge Assembly.LoadFrom file locks), print sizes + sha256.
"""
import io
import os
import shutil
import zipfile
import hashlib

# ---------- PROJECT BLOCK: edit these per plugin ----------
ROOT = globals().get("ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = globals().get("PLUGIN") or "DatumPlanePlugin"     # rhp base name, no extension
VERSION = globals().get("VERSION") or "2.8.0.0"
PKG_NAME = globals().get("PKG_NAME") or "基准面工具"         # must match assembly title
DESCRIPTION = globals().get("DESCRIPTION") or "Rhino 9 plugin"
AUTHORS = globals().get("AUTHORS") or ["DatumPlane Tools"]
URL = globals().get("URL") or "https://www.rhino3d.com"
RHP_VARIANT = globals().get("RHP_VARIANT") or (PLUGIN + "_v28.rhp")
# Everything shipped in the yak. The rhp entry is remapped to PLUGIN + ".rhp".
FILES = globals().get("FILES") or [
    "DatumPlanePlugin.rhp", "DatumPlanePlugin.rui",
    "DatumPlane_dark.svg", "DatumPlane_light.svg",
    "manifest.yml", "README.md", "REVIEW.md",
]
# ---------- END PROJECT BLOCK ----------

INSTALL = os.path.join(ROOT, "install")
RHP_SRC = os.path.join(ROOT, RHP_VARIANT)
if not os.path.exists(RHP_SRC):
    RHP_SRC = os.path.join(ROOT, PLUGIN + ".rhp")
assert os.path.exists(RHP_SRC), "missing compiled rhp: " + RHP_SRC

short_version = ".".join(VERSION.split(".")[:3])
YAK = os.path.join(ROOT, globals().get("YAK_NAME") or (PLUGIN + "_v" + short_version.replace(".", "_") + ".yak"))
os.makedirs(INSTALL, exist_ok=True)

for name in FILES:
    if name == "manifest.yml":
        continue
    src = RHP_SRC if name == PLUGIN + ".rhp" else os.path.join(ROOT, name)
    if os.path.exists(src):
        shutil.copyfile(src, os.path.join(INSTALL, name))

manifest = """---
name: {name}
version: {version}
authors:
{authors}
description: {description}
url: {url}
keywords: []
platform: win
""".format(
    name=PKG_NAME,
    version=VERSION,
    authors="\n".join("- " + a for a in AUTHORS),
    description=DESCRIPTION,
    url=URL,
)
with io.open(os.path.join(ROOT, "manifest.yml"), "w", encoding="utf-8", newline="\n") as f:
    f.write(manifest)
shutil.copyfile(os.path.join(ROOT, "manifest.yml"), os.path.join(INSTALL, "manifest.yml"))
print("install/ synced: rhp + rui + docs + manifest")

with zipfile.ZipFile(YAK, "w", zipfile.ZIP_DEFLATED) as z:
    for name in FILES:
        src = RHP_SRC if name == PLUGIN + ".rhp" else os.path.join(ROOT, name)
        if not os.path.exists(src):
            print("  SKIP missing:", name)
            continue
        z.write(src, name)
        print("   %-28s %7d" % (name, os.path.getsize(src)))

print("built %s (%d bytes)" % (YAK, os.path.getsize(YAK)))
print("sha256 yak =", hashlib.sha256(open(YAK, "rb").read()).hexdigest())
print("sha256 rhp =", hashlib.sha256(open(RHP_SRC, "rb").read()).hexdigest())
print("NEXT: close any proxy, then Yak.exe install " + os.path.basename(YAK))
