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

REST = "https://api.wikimedia.org/core/v1/commons"
# 图片代理用浏览器 UA；REST 元数据用原来的教育用途 UA
BUA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}


# 系统代理对 wikimedia 域名 TLS 握手超时；REST 元数据走直连，图片代理走系统代理
DIRECT = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def get_json(url, tries=3, timeout=12):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with DIRECT.open(req, timeout=timeout) as r:
                return json.load(r)
        except Exception:
            if i == tries - 1:
                return None
            time.sleep(0.6)
    return None


def tokens(q):
    return [t for t in re.split(r"\W+", q.lower()) if len(t) >= 2]

# 通用词不算「特征词」：只命中 chair / vase / bowl 的图很可能是张冠李戴
STOP = set("""chair vase cup bowl plate lamp poster building design chinese dynasty style
ware pottery porcelain jpg jpeg png the of and with in a an red blue white black no
art new first set table box window door""".split())


def relevant(title, q):
    ts = set(tokens(title))
    qs = [t for t in tokens(q) if t not in STOP]
    return bool(qs) and sum(1 for t in qs if t in ts) >= 1


def original_from_thumb(turl):
    """Commons 缩略图 URL 可反推原图地址，省掉一次 REST 请求。
    /wikipedia/commons/thumb/9/94/Name.jpg/60px-Name.jpg
      -> https://upload.wikimedia.org/wikipedia/commons/9/94/Name.jpg
    """
    u = turl.split("?")[0]
    m = re.search(r"/thumb/([0-9a-fA-F]/[0-9a-fA-F]{2})/([^/]+)/\d+px-", u)
    if m:
        return "https://upload.wikimedia.org/wikipedia/commons/%s/%s" % (m.group(1), m.group(2))
    if "upload.wikimedia.org" in u and "px-" not in u:
        return u.replace("https://thumb.wikimedia.org/", "https://upload.wikimedia.org/")
    return None


def rest_search(q):
    """一次 REST 搜索同时拿到：文件 key、标题、原图 URL、原图页。"""
    ws = tokens(q)
    variants = [q]
    if len(ws) > 3:
        variants.append(" ".join(ws[:3]))
    if len(ws) > 2:
        variants.append(" ".join(ws[:2]))
    for v in variants:
        u = REST + "/search/page?" + urllib.parse.urlencode({"q": v, "limit": 8})
        d = get_json(u, tries=4, timeout=9)
        if not d:
            continue
        for pg in d.get("pages", []):
            k = pg.get("key", "")
            title = pg.get("title", k).replace("File:", "")
            if not (k.startswith("File:") and pg.get("thumbnail")):
                continue
            if not relevant(title, q):
                continue
            orig = original_from_thumb(pg["thumbnail"]["url"])
            if not orig:
                continue
            page = "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(k.replace(" ", "_"), safe=":")
            return {"key": k, "title": title, "url": orig, "page": page}
    return None


def proxy_urls(clean_url):
    path = clean_url.replace("https://", "").replace("http://", "")
    return [
        "https://images.weserv.nl/?url=" + path + "&w=520&output=jpg&q=82",
        "https://i0.wp.com/" + path,
    ]


def get_image(clean_url):
    for u in proxy_urls(clean_url):
        for opener in (urllib.request.build_opener(), DIRECT):
            try:
                req = urllib.request.Request(u, headers=BUA)
                with opener.open(req, timeout=18) as r:
                    b = r.read()
                im = Image.open(io.BytesIO(b)).convert("RGB")
                if im.width < 120 or im.height < 90:
                    continue
                return im
            except Exception:
                continue
    return None


def fetch_one(item, out):
    key, q = item
    dst = os.path.join(ASSETS, key + ".jpg")
    if os.path.exists(dst) and key in out:
        return ("skip", key, None, None)
    found = rest_search(q)
    if not found:
        return ("nomatch", key, q, None)
    im = get_image(found["url"])
    if im is None:
        return ("dlfail", key, q, None)
    im.thumbnail((460, 340), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=72, optimize=True)
    data = buf.getvalue()
    info = {
        "title": found["title"],
        "page": found["page"],
        "license": "Wikimedia Commons · 自由授权（详情见原图页）",
        "author": "见原图页",
        "source": "Wikimedia Commons via weserv / i0.wp.com 代理",
        "query": q,
        "bytes": len(data),
    }
    return ("ok", key, info, data)


def main():
    import argparse
    from concurrent.futures import ThreadPoolExecutor, as_completed
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--key", default="")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    # 软预检：网络是间歇性的，不通也继续，靠每件自己的重试去撞窗口
    probe = get_json(REST + "/search/page?q=Thonet&limit=1", tries=4, timeout=9)
    print(("REST OK" if probe else "REST 抖动（继续尝试）") + " · 并发 %d" % args.workers, flush=True)

    meta_path = os.path.join(CONTENT, "images.json")
    out = {}
    if os.path.exists(meta_path):
        out = json.load(open(meta_path, encoding="utf-8"))
    items = [(k, q) for k, q in QUERIES.items() if not args.key or k == args.key]
    if args.limit:
        items = items[:args.limit]
    total, ok, streak = len(items), 0, 0

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(fetch_one, it, out): it[0] for it in items}
        for n, f in enumerate(as_completed(futs), 1):
            try:
                status, key, info, data = f.result()
            except Exception as e:
                print("[%2d/%d] ERR %s %s" % (n, total, futs[f], e), flush=True)
                streak += 1
            else:
                if status == "ok":
                    with open(os.path.join(ASSETS, key + ".jpg"), "wb") as fh:
                        fh.write(data)
                    out[key] = info
                    ok += 1
                    streak = 0
                    print("[%2d/%d] OK %s %6d B | %s" % (
                        n, total, key, len(data), info["title"][:44]), flush=True)
                elif status == "skip":
                    ok += 1
                    print("[%2d/%d] skip %s" % (n, total, key), flush=True)
                else:
                    streak += 1
                    print("[%2d/%d] %-7s %s" % (n, total, status.upper(), key), flush=True)
            with open(meta_path, "w", encoding="utf-8") as fh:
                json.dump(out, fh, ensure_ascii=False, indent=1)
            # 连续 14 件全失败 = 本轮网络窗口关闭，收摊等下一轮
            if streak >= 14:
                print("NETWORK WINDOW CLOSED · 提前结束本轮（已抓的会保留）", flush=True)
                for g in futs:
                    g.cancel()
                break

    print("DONE %d/%d images, %.2f MB" % (
        ok, total, sum(v.get("bytes", 0) for v in out.values()) / 1024 / 1024), flush=True)


if __name__ == "__main__":
    main()
