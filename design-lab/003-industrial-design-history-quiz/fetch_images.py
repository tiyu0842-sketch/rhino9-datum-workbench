# -*- coding: utf-8 -*-
"""
fetch_images.py — 从 Wikimedia Commons 抓公有领域 / CC 授权实物图

纪律：
1. 只取 Commons，记录每张图的标题、作者、授权、来源页；
2. 不下载无授权信息的图；抓取失败就跳过，不硬凑；
3. 统一压到 460×340 JPEG q70（学习用，不需要原始分辨率）；
4. 结果写 content/images.json，由 build_app.py 内嵌进单文件。
"""
import io
import json
import os
import re
import time
import urllib.parse
import urllib.request

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(HERE, "content")
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)

UA = {"User-Agent": "DesignHistoryStudyApp/1.0 (educational offline app; local use)"}
ALLOW = ("PD", "CC0", "CC BY", "FAL", "Public domain")

# 每件作品对应的英文检索词（Commons 上英文命中率远高于中文）
QUERIES = {
    "c01-w0": "Yangshao painted pottery basin fish",
    "c01-w1": "Longshan black pottery stem cup",
    "c01-w2": "Chinese jade bi disc",
    "c02-w0": "Houmuwu ding bronze",
    "c02-w1": "Chinese bronze jue vessel",
    "c02-w2": "Chinese jade pendant set",
    "c03-w0": "Chinese lacquer ear cup Han",
    "c03-w1": "Mawangdui gauze robe",
    "c03-w2": "Han dynasty roof tile dang",
    "c04-w0": "Yue kiln celadon chicken head ewer",
    "c04-w1": "celadon lotus bowl",
    "c04-w2": "Yungang Grottoes Buddha",
    "c05-w0": "Tang sancai horse",
    "c05-w1": "Yue kiln secret color celadon",
    "c05-w2": "Tang dynasty chair furniture",
    "c06-w0": "Ru ware bowl",
    "c06-w1": "Jun ware flower pot",
    "c06-w2": "Ding ware white porcelain plate",
    "c06-w3": "Song dynasty table furniture",
    "c07-w0": "Yuan blue and white porcelain meiping",
    "c07-w1": "David vase Yuan blue white",
    "c07-w2": "Chinese carved red lacquer box",
    "c08-w0": "Ming horseshoe armchair huanghuali",
    "c08-w1": "Ming official hat armchair",
    "c08-w2": "Ming protruding head table",
    "c08-w3": "Ming blue and white porcelain bowl",
    "c08-w4": "Yixing zisha teapot",
    "c09-w0": "Qing taishi armchair",
    "c09-w1": "Qing famille rose vase",
    "c09-w2": "Chinese export armorial porcelain",
    "c10-w0": "Chinese calendar poster month card",
    "c10-w1": "Chen Zhifo pattern design",
    "c10-w2": "Shanghai Art Deco furniture",
    "c11-w0": "Chinese state banquet porcelain",
    "c11-w1": "new Chinese style furniture",
    "c11-w2": "Chinese bamboo weaving craft",
    "w01-w0": "Parthenon Doric columns",
    "w01-w1": "Greek black figure amphora",
    "w01-w2": "Roman glass bowl",
    "w02-w0": "Gothic cathedral flying buttress",
    "w02-w1": "medieval chest furniture",
    "w02-w2": "stained glass window cathedral",
    "w03-w0": "Florence Cathedral dome Brunelleschi",
    "w03-w1": "cassone Italian Renaissance chest",
    "w03-w2": "Vitruvian Man da Vinci",
    "w04-w0": "Rococo armchair France",
    "w04-w1": "Chippendale chair",
    "w04-w2": "Chinese export porcelain bowl",
    "w05-w0": "Wedgwood jasperware vase",
    "w05-w1": "Robert Adam interior chair",
    "w05-w2": "Empire style chair",
    "w06-w0": "Crystal Palace Paxton",
    "w06-w1": "Thonet chair 14",
    "w06-w2": "Great Exhibition 1851 exhibits",
    "w07-w0": "Morris chair",
    "w07-w1": "William Morris wallpaper pattern",
    "w07-w2": "Red House Webb Morris",
    "w08-w0": "Guimard Metro entrance",
    "w08-w1": "Tiffany lamp",
    "w08-w2": "Art Nouveau poster Mucha",
    "w09-w0": "Mackintosh high back chair",
    "w09-w1": "Peter Behrens AEG kettle",
    "w09-w2": "Secession Building Vienna",
    "w10-w0": "Red Blue Chair Rietveld",
    "w10-w1": "Wassily chair Breuer",
    "w10-w2": "Bauhaus Dessau building",
    "w10-w3": "Bauhaus lamp MT8",
    "w11-w0": "Chrysler Building spire",
    "w11-w1": "Art Deco poster",
    "w11-w2": "streamlined train 1930s",
    "w12-w0": "Coca Cola contour bottle",
    "w12-w1": "Bell 500 telephone",
    "w12-w2": "Greyhound bus Silversides",
    "w13-w0": "Braun SK4 radio",
    "w13-w1": "Volkswagen Beetle 1950",
    "w13-w2": "Tulip chair Saarinen",
    "w13-w3": "Panton chair",
    "w14-w0": "pop art poster 1960s",
    "w14-w1": "Sacco bean bag chair",
    "w14-w2": "inflatable chair design",
    "w15-w0": "Carlton bookcase Sottsass",
    "w15-w1": "Memphis design lamp",
    "w15-w2": "postmodern architecture facade",
    "w16-w0": "iPhone first generation",
    "w16-w1": "Muji minimal design",
    "w16-w2": "sustainable design recycle product",
}


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()[:90]


def get_json(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=18) as r:
                return json.load(r)
        except Exception:
            if i == tries - 1:
                return None
            time.sleep(1.2 * (i + 1))
    return None


def get_bytes(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=22) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                return None
            time.sleep(1.2 * (i + 1))
    return None


def search_image(query):
    params = {
        "action": "query", "generator": "search",
        "gsrsearch": "filetype:bitmap " + query,
        "gsrnamespace": "6", "gsrlimit": "6",
        "prop": "imageinfo", "iiprop": "url|extmetadata",
        "iiurlwidth": "520", "format": "json",
    }
    d = get_json("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params))
    if not d:
        return None
    pages = d.get("query", {}).get("pages", {})
    # 优先按搜索排名（pageid 不保证顺序，用 index）
    cand = sorted(pages.values(), key=lambda p: p.get("index", 99))
    for p in cand:
        try:
            ii = p["imageinfo"][0]
            em = ii.get("extmetadata", {})
            lic = em.get("LicenseShortName", {}).get("value", "")
            if not any(lic.startswith(a) for a in ALLOW):
                continue
            thumb = ii.get("thumburl") or ii.get("url")
            if not thumb:
                continue
            return {
                "title": p["title"].replace("File:", ""),
                "page": ii.get("descriptionurl", ""),
                "license": lic[:40],
                "author": strip_html(em.get("Artist", {}).get("value", "")),
                "url": thumb,
            }
        except (KeyError, IndexError):
            continue
    return None


def main():
    out = {}
    if os.path.exists(os.path.join(CONTENT, "images.json")):
        out = json.load(open(os.path.join(CONTENT, "images.json"), encoding="utf-8"))
    total = len(QUERIES)
    for n, (key, q) in enumerate(QUERIES.items(), 1):
        if key in out and os.path.exists(os.path.join(ASSETS, key + ".jpg")):
            print("[%2d/%d] skip %s" % (n, total, key), flush=True)
            continue
        info = search_image(q)
        if not info:
            print("[%2d/%d] NO MATCH %s (%s)" % (n, total, key, q), flush=True)
            continue
        raw = get_bytes(info["url"])
        if not raw:
            print("[%2d/%d] DL FAIL %s" % (n, total, key), flush=True)
            continue
        try:
            im = Image.open(io.BytesIO(raw)).convert("RGB")
            im.thumbnail((460, 340), Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=70, optimize=True)
            data = buf.getvalue()
        except Exception as e:
            print("[%2d/%d] IMG FAIL %s %s" % (n, total, key, e), flush=True)
            continue
        with open(os.path.join(ASSETS, key + ".jpg"), "wb") as f:
            f.write(data)
        info["bytes"] = len(data)
        out[key] = info
        print("[%2d/%d] OK %s %6d B | %s | %s" % (
            n, total, key, len(data), info["license"], info["title"][:42]), flush=True)
        with open(os.path.join(CONTENT, "images.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
    print("DONE %d/%d images, %.1f MB" % (
        len(out), total,
        sum(v.get("bytes", 0) for v in out.values()) / 1024 / 1024), flush=True)


if __name__ == "__main__":
    main()
