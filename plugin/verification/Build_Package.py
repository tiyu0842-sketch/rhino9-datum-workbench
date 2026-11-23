# -*- coding: utf-8 -*-
"""Build the v1.8 toolbar + Yak package. Pure local Python 3, no Rhino needed.

    python verification/Build_Package.py

Idempotent: each block is skipped when its macro already exists in the RUI.
v1.8 adds the JZ alias command + letter-coded menus; the toolbar stays at 9
buttons (all changes are in the .rhp), so no new RUI blocks are inserted.
"""
import io
import os
import shutil
import zipfile
import hashlib
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUI = os.path.join(ROOT, "DatumPlanePlugin.rui")
INSTALL = os.path.join(ROOT, "install")
# 编译时 Rhino 正加载着 canonical 的 .rhp（Assembly.LoadFrom 会锁文件），
# 所以 Roslyn 输出到 DatumPlanePlugin_vNN.rhp，打包时再以正式名装进 yak。
RHP_SRC = os.path.join(ROOT, "DatumPlanePlugin_v210.rhp")
if not os.path.exists(RHP_SRC):
    RHP_SRC = os.path.join(ROOT, "DatumPlanePlugin.rhp")
YAK = os.path.join(ROOT, "DatumPlane_v2_10.yak")

# --- v1.6 normal-view button ---
ITEM_GUID = "E1F2A3B4-1111-4C5D-8E6F-0A1B2C3D4E5F"
MACRO_GUID = "F2A3B4C5-2222-4D6E-9F70-1B2C3D4E5F60"
ICON_GUID = "A3B4C5D6-3333-4E7F-A081-2C3D4E5F6071"

SVG_LIGHT = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40">'
             '<g stroke-linecap="round" stroke-linejoin="round">'
             '<path d="M4 7 H36 V33 H4 Z" fill="none" stroke="#0B5FA5" stroke-width="1.8"/>'
             '<path d="M20 7 V33" fill="none" stroke="#0B5FA5" stroke-width="1.8"/>'
             '<path d="M24 15 H33 V27 H24 Z" fill="#1E90FF" fill-opacity="0.28" stroke="#0B5FA5" stroke-width="1.6"/>'
             '<path d="M28.5 9 V16 M26 13.5 L28.5 16 L31 13.5" fill="none" stroke="#0B5FA5" stroke-width="1.6"/>'
             '<path d="M8 14 H16 M8 19 H16 M8 24 H13" fill="none" stroke="#0B5FA5" stroke-width="1.4"/>'
             '</g></svg>')
SVG_DARK = SVG_LIGHT.replace("#0B5FA5", "#8CCBFF").replace("#1E90FF", "#2E9FFF")

# --- v1.7 Alias eye-care button: soft gradient card + iso flow lines ---
ITEM_ALIAS = "B4C5D6E7-4444-4F80-91A2-3D4E5F607182"
MACRO_ALIAS = "C5D6E7F8-5555-4081-A2B3-4E5F60718293"
ICON_ALIAS = "D6E7F809-6666-4182-B3C4-5F607182934A"

SVG_ALIAS_LIGHT = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40">'
                   '<defs><linearGradient id="bgA" x1="0" y1="0" x2="0" y2="1">'
                   '<stop offset="0" stop-color="#C9CEC7"/><stop offset="1" stop-color="#A0AAA0"/>'
                   '</linearGradient></defs>'
                   '<g stroke-linecap="round" stroke-linejoin="round">'
                   '<rect x="3.5" y="5.5" width="33" height="29" rx="2.5" fill="url(#bgA)" stroke="#0B5FA5" stroke-width="1.6"/>'
                   '<path d="M7 27 C13 20, 19 24, 23 17 S32 12, 34 15" fill="none" stroke="#2A6A5E" stroke-width="1.7"/>'
                   '<path d="M8 21 C14 15, 20 19, 24 13" fill="none" stroke="#3F646C" stroke-width="1.1"/>'
                   '<path d="M10 32 C16 26, 22 29, 26 22" fill="none" stroke="#3F646C" stroke-width="1.1"/>'
                   '<path d="M13 9 V33" fill="none" stroke="#3F646C" stroke-width="1" stroke-dasharray="2 2.5"/>'
                   '<path d="M27 9 V33" fill="none" stroke="#3F646C" stroke-width="1" stroke-dasharray="2 2.5"/>'
                   '</g></svg>')
SVG_ALIAS_DARK = (SVG_ALIAS_LIGHT
                  .replace("#C9CEC7", "#2B3134").replace("#A0AAA0", "#3C4448")
                  .replace("#0B5FA5", "#8CCBFF").replace("#2A6A5E", "#9ED8C6")
                  .replace("#3F646C", "#8FB4BA"))

# --- v1.7 restore button: viewport frame + undo arc ---
ITEM_REST = "E7F8091A-7777-4293-C4D5-607182934A5B"
MACRO_REST = "F8091A2B-8888-43A4-D5E6-7182934A5B6C"
ICON_REST = "091A2B3C-9999-44B5-E6F7-82934A5B6C7D"

SVG_REST_LIGHT = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40">'
                  '<g fill="none" stroke="#0B5FA5" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
                  '<path d="M4 9 H36 V31 H4 Z"/>'
                  '<path d="M12 22 A8 8 0 1 1 20 26"/>'
                  '<path d="M20 22 L20 26 L24 26"/>'
                  '</g></svg>')
SVG_REST_DARK = SVG_REST_LIGHT.replace("#0B5FA5", "#8CCBFF")


def item(guid, macro, en, zh):
    return ('<tool_bar_item guid="%s"><text><locale_1033>%s</locale_1033>'
            '<locale_2052>%s</locale_2052></text>'
            '<left_macro_id>%s</left_macro_id></tool_bar_item>') % (guid, en, zh, macro)


def macro(guid, icon_guid, script, en, zh, tip_en, tip_zh):
    return ('<macro_item guid="%s" bitmap_id="%s">'
            '<button_text><locale_1033>%s</locale_1033><locale_2052>%s</locale_2052></button_text>'
            '<menu_text><locale_1033>%s</locale_1033><locale_2052>%s</locale_2052></menu_text>'
            '<tooltip><locale_1033>%s</locale_1033><locale_2052>%s</locale_2052></tooltip>'
            '<script>! %s</script></macro_item>') % (
        guid, icon_guid, en, zh, en, zh, tip_en, tip_zh, script)


def icon(guid, light, dark):
    return '<icon guid="%s"><light>%s</light><dark>%s</dark></icon>' % (guid, light, dark)


s = io.open(RUI, encoding="utf-8").read()

# --- v2.6 wording: directional three-tone clay (not flat AO white model) ---
s = s.replace("环境光遮蔽白模 + 等参线，看清曲面走向与结构（实测不吃到 255）",
              "方向光三度灰阶 + 等参线，亮面/中间调/暗面看清曲面走向（纯白 0.00%）")
s = s.replace("AO clay + isocurves: read surface flow, no 255 blow-out",
              "Three-tone clay + isocurves: read surface flow with light/mid/dark, no 255 blow-out")
s = s.replace("Alias 护眼显示", "Alias 观测显示")
s = s.replace("把各视口还原为启用护眼显示之前的模式",
              "把各视口还原为启用观测显示之前的模式")

# --- v2.10 wording: only the active viewport changes (per-viewport independence) ---
s = s.replace("方向光三度灰阶 + 等参线，亮面/中间调/暗面看清曲面走向（纯白 0.00%）",
              "只改当前活动视口：方向光三度灰阶 + 等参线，看清曲面走向（纯白 0.00%，其他视口不动）")
s = s.replace("Three-tone clay + isocurves: read surface flow with light/mid/dark, no 255 blow-out",
              "Active viewport only: three-tone clay + isocurves, no 255 blow-out")
s = s.replace("柔和渐变背景 + 等参线，护眼并看清曲面走向与趋势",
              "只改当前活动视口：柔和渐变背景 + 等参线，看清曲面走向（其他视口不动）")
s = s.replace("Soft gradient background + isocurves to read surface flow",
              "Active viewport only: soft gradient background + isocurves to read surface flow")
s = s.replace("把各视口还原为启用观测显示之前的模式",
              "只还原本工具改过的视口，回到原显示模式")
s = s.replace("Restore the display mode each viewport had before",
              "Restore only the viewports this tool changed")


def insert_once(sentinel, items_xml, macros_xml, icons_xml):
    global s
    if sentinel in s:
        print("RUI: %s already present, left unchanged" % sentinel)
        return
    for tag in ("</tool_bar>", "</macros>", "</icons>"):
        assert s.count(tag) == 1, "anchor not unique: " + tag
    s = s.replace("</tool_bar>", items_xml + "</tool_bar>")
    s = s.replace("</macros>", macros_xml + "</macros>")
    s = s.replace("</icons>", icons_xml + "</icons>")
    print("RUI: inserted %s" % sentinel)


insert_once(
    "_DatumPlaneNormalView",
    item(ITEM_GUID, MACRO_GUID, "Normal view", "基准面法向视图"),
    macro(MACRO_GUID, ICON_GUID, "_DatumPlaneNormalView",
          "Normal view", "基准面法向视图",
          "Vertically split Top; camera perpendicular to datum",
          "垂直分割 Top 视图，生成相机垂直于基准面的第 5 个法向视图"),
    icon(ICON_GUID, SVG_LIGHT, SVG_DARK))

insert_once(
    "_AliasStyleLight",
    item(ITEM_ALIAS, MACRO_ALIAS, "Alias eye-care", "Alias 护眼显示"),
    macro(MACRO_ALIAS, ICON_ALIAS, "_AliasStyleLight",
          "Alias eye-care", "Alias 护眼显示",
          "Soft gradient background + isocurves to read surface flow",
          "柔和渐变背景 + 等参线，护眼并看清曲面走向与趋势"),
    icon(ICON_ALIAS, SVG_ALIAS_LIGHT, SVG_ALIAS_DARK))

insert_once(
    "_AliasStyleRestore",
    item(ITEM_REST, MACRO_REST, "Restore display", "还原显示"),
    macro(MACRO_REST, ICON_REST, "_AliasStyleRestore",
          "Restore display", "还原显示模式",
          "Restore the display mode each viewport had before",
          "把各视口还原为启用护眼显示之前的模式"),
    icon(ICON_REST, SVG_REST_LIGHT, SVG_REST_DARK))

with io.open(RUI, "w", encoding="utf-8", newline="") as f:
    f.write(s)

tree = ET.parse(RUI)
root = tree.getroot()
items = root.findall(".//tool_bar_item")
macros = root.findall(".//macro_item")
icons = root.findall(".//icon")
print("RUI XML OK: tool_bar_item=%d macro_item=%d icon=%d" % (len(items), len(macros), len(icons)))
assert len(items) == 9 and len(macros) == 9 and len(icons) == 9, "RUI counts must be 9/9/9"

ids = {m.get("guid"): m for m in macros}
icon_ids = {i.get("guid") for i in icons}
for macro_guid, icon_guid, script in (
        (MACRO_GUID, ICON_GUID, "_DatumPlaneNormalView"),
        (MACRO_ALIAS, ICON_ALIAS, "_AliasStyleLight"),
        (MACRO_REST, ICON_REST, "_AliasStyleRestore")):
    assert macro_guid in ids, "macro missing: " + macro_guid
    assert ids[macro_guid].get("bitmap_id") == icon_guid and icon_guid in icon_ids, \
        "icon chain broken: " + macro_guid
    assert script in (ids[macro_guid].findtext("script") or ""), "script missing: " + script
    assert any((i.find("left_macro_id") is not None and
                (i.find("left_macro_id").text or "").strip() == macro_guid) for i in items), \
        "toolbar item chain broken: " + macro_guid
print("RUI GUID chains: closed (9 buttons, 3 verified chains)")

for f in ("DatumPlanePlugin.rui", "README.md", "REVIEW.md"):
    shutil.copyfile(os.path.join(ROOT, f), os.path.join(INSTALL, f))
shutil.copyfile(RHP_SRC, os.path.join(INSTALL, "DatumPlanePlugin.rhp"))
print("install/: synced rhp + rui + README + REVIEW")

manifest = """---
name: \u57fa\u51c6\u9762\u5de5\u5177
version: 2.10.0.0
authors:
- DatumPlane Tools
description: Rhino 9 datum plane v2.10 - Alias study display applies to the ACTIVE viewport only (other viewports untouched; all-view sync is optional and off by default), restore touches only the viewports this tool changed, two Alias modes distinguished by isocurve density (Light 0 = edges only, Dark 1 = one internal isocurve), click a planar face directly with no Ctrl+Shift, directional three-tone clay display, per-viewport CPlane restore, self-healing leaked CPlanes, 5th normal viewport, bilingual prompts
url: https://www.rhino3d.com
keywords: []
platform: win
"""
with io.open(os.path.join(ROOT, "manifest.yml"), "w", encoding="utf-8", newline="\n") as f:
    f.write(manifest)

FILES = ["DatumPlanePlugin.rhp", "DatumPlanePlugin.rui",
         "DatumPlane_dark.svg", "DatumPlane_light.svg",
         "manifest.yml", "README.md", "REVIEW.md"]
with zipfile.ZipFile(YAK, "w", zipfile.ZIP_DEFLATED) as z:
    for f in FILES:
        src = RHP_SRC if f == "DatumPlanePlugin.rhp" else os.path.join(ROOT, f)
        z.write(src, f)
print("built %s (%d bytes)" % (YAK, os.path.getsize(YAK)))
for f in FILES:
    src = RHP_SRC if f == "DatumPlanePlugin.rhp" else os.path.join(ROOT, f)
    print("   %-28s %7d" % (f, os.path.getsize(src)))
print("sha256 yak =", hashlib.sha256(open(YAK, "rb").read()).hexdigest())
print("sha256 rhp =", hashlib.sha256(open(RHP_SRC, "rb").read()).hexdigest())
