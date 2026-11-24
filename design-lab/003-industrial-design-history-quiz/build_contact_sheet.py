# -*- coding: utf-8 -*-
"""
build_contact_sheet.py — 把已抓的实物图拼成「联系表」，供一次性人工审查。

自动搜索难免张冠李戴（器形对不上、抓到插画、同一张图配了两件作品）。
生成带 key / 中文作品名 / Commons 标题的拼图，看一遍就能列出要剔除的 key。

用法：python build_contact_sheet.py  →  review_sheet_1.png, _2 ...
"""
import io
import json
import os
import re

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
CONTENT = os.path.join(HERE, "content")
META = os.path.join(CONTENT, "images.json")
PER = 25          # 每页 5×5
COLS = 5
CW, CH = 224, 208
IMG_W, IMG_H = 200, 138

FONT_PATHS = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/simhei.ttf",
]


def font(size, bold=False):
    paths = FONT_PATHS if not bold else [FONT_PATHS[1], FONT_PATHS[0], FONT_PATHS[2]]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def clip(s, n):
    s = str(s or "")
    return s if len(s) <= n else s[:n - 1] + "…"


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--new", action="store_true", help="只列本轮「精确文件名直取」新增的图，供增量审查")
    args = ap.parse_args()

    meta = json.load(open(META, encoding="utf-8")) if os.path.exists(META) else {}
    works = []
    for fn in ("content/china.json", "content/world.json"):
        for st in json.load(open(os.path.join(HERE, fn), encoding="utf-8"))["stations"]:
            for i, w in enumerate(st["works"]):
                works.append(("%s-w%d" % (st["id"], i), w["name"]))

    items = []
    for key, name in works:
        p = os.path.join(ASSETS, key + ".jpg")
        if os.path.exists(p) and (not args.new or meta.get(key, {}).get("method") == "exact"):
            items.append((key, name, meta.get(key, {}).get("title", "?"), p))
    # 未被 QUERIES 覆盖但也放了图的 key 也列出来
    known = {k for k, _ in works}
    for f in sorted(os.listdir(ASSETS)):
        if f.lower().endswith(".jpg"):
            k = os.path.splitext(f)[0]
            if k not in known:
                items.append((k, "（未登记）", meta.get(k, {}).get("title", "?"), os.path.join(ASSETS, f)))

    pages = (len(items) + PER - 1) // PER
    f_key, f_name, f_src, f_small = font(13, True), font(14, True), font(11), font(10)
    for pg in range(pages):
        chunk = items[pg * PER:(pg + 1) * PER]
        rows = (len(chunk) + COLS - 1) // COLS
        sheet = Image.new("RGB", (COLS * CW, rows * CH), "#f2efe9")
        d = ImageDraw.Draw(sheet)
        for idx, (key, name, title, path) in enumerate(chunk):
            x, y = (idx % COLS) * CW, (idx // COLS) * CH
            d.rectangle([x + 3, y + 3, x + CW - 3, y + CH - 3], fill="#ffffff", outline="#d9d2c5")
            try:
                im = Image.open(path).convert("RGB")
                im.thumbnail((IMG_W, IMG_H), Image.LANCZOS)
                bx = x + (CW - im.width) // 2
                by = y + 8 + (IMG_H - im.height) // 2
                sheet.paste(im, (bx, by))
            except Exception:
                d.text((x + 12, y + 50), "图片损坏", fill="#b00", font=f_small)
            ty = y + 8 + IMG_H + 4
            d.text((x + 10, ty), key, fill="#a4562f", font=f_key)
            d.text((x + 10, ty + 17), clip(name, 11), fill="#2f2b26", font=f_name)
            d.text((x + 10, ty + 36), clip(title, 26), fill="#7d7468", font=f_src)
        out = os.path.join(HERE, ("review_new_%d.png" if args.new else "review_sheet_%d.png") % (pg + 1))
        sheet.save(out)
        print("-> %s  %d 张" % (os.path.basename(out), len(chunk)))
    print("共 %d 张已抓图，%d 页" % (len(items), pages))


if __name__ == "__main__":
    main()
