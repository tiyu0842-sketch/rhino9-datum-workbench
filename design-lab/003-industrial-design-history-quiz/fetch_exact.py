# -*- coding: utf-8 -*-
"""
fetch_exact.py — v7：精确文件名直取 Commons 实物图

为什么重写（v6 的教训）：
  fetch_images.py 靠 REST 模糊搜索，且「取第一个通过宽松相关性检查的候选」，
  结果 57 张里 28 张张冠李戴（钟当电话、人像当 Sacco、图纸当实物椅……）。
  E-034 已证明：REST 元数据接口是间歇性窗口，常被误判成「全网不通」。

v7 换一条不依赖 REST 的路：
  1. content/image_targets.json 存每件作品**确认过的 Commons 精确文件名**（可多候选）；
  2. Commons 原图路径由文件名本地算出：md5(空格转下划线)[0] / md5[:2] / 文件名；
  3. 图片二进制走 i0.wp.com / images.weserv.nl 代理（这层实测是通的）；
  4. 文件名本身就是最强相关性校验，不再靠「命中 1 个特征词」猜；
  5. 全候选失败就留空，绝不硬凑；失败原因写 content/image_fetch_log.json。
  6. 新抓的图仍需人工联系表核对（build_contact_sheet.py → review_images.py），纪律不变。

纪律：只取 Commons 自由授权文件；压到 460×340 JPEG q72；增量落盘、只补缺口。
"""
import argparse
import hashlib
import io
import json
import os
import re
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(HERE, "content")
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)

META = os.path.join(CONTENT, "images.json")
TARGETS = os.path.join(CONTENT, "image_targets.json")
LOGPATH = os.path.join(CONTENT, "image_fetch_log.json")

BUA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
SYS = urllib.request.build_opener()                              # 走系统代理（图片代理需要）
DIRECT = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # 直连（备用）

# 这些词出现在文件名里，基本可以断定不是「实物照片」——直接跳过候选
BAD_WORDS = re.compile(r"\b(plan|plans|drawing|diagram|map|portrait|bust|sketch|"
                       r"engraving|illustration|elevation|section|blueprint|"
                       r"logo|chart|graph|signature|autograph|letter)\b", re.I)

LOCK = threading.Lock()


def commons_orig(name):
    """Commons 原图地址：md5(文件名) 的前 1 位 / 前 2 位。文件名空格转下划线。"""
    n = name.replace(" ", "_")
    h = hashlib.md5(n.encode("utf-8")).hexdigest()
    return ("https://upload.wikimedia.org/wikipedia/commons/%s/%s/%s"
            % (h[0], h[:2], urllib.parse.quote(n, safe="()_,.'-")))


def commons_page(name):
    n = name.replace(" ", "_")
    return ("https://commons.wikimedia.org/wiki/File:"
            + urllib.parse.quote(n, safe="()_,.'-"))


def proxy_urls(orig):
    clean = orig.replace("https://", "")
    q = urllib.parse.quote(clean, safe="/")
    return [
        "https://i0.wp.com/" + clean + "?w=700",
        "https://i1.wp.com/" + clean + "?w=700",
        "https://images.weserv.nl/?url=" + q + "&w=520&output=jpg&q=82",
        "https://wsrv.nl/?url=" + q + "&w=520&output=jpg&q=82",
        "https://i0.wp.com/" + clean,
    ]


def looks_like_photo(im):
    """轻量排除：太小的图、近乎纯白的空白页、明显是线稿的低色彩图。"""
    if im.width < 150 or im.height < 110:
        return False
    small = im.copy()
    small.thumbnail((64, 64))
    raw = small.tobytes()                       # 不用 getdata()，避免 Pillow 弃用告警
    px = [raw[i:i + 3] for i in range(0, len(raw), 3)]
    # 颜色标准差：线稿/图纸通常接近灰度且方差很低
    means = [sum(p[i] for p in px) / len(px) for i in range(3)]
    var = sum((p[0] - means[0]) ** 2 for p in px) / len(px)
    if var < 55:
        return False
    # 几乎全白（空白页 / 未渲染）
    white = sum(1 for p in px if min(p) > 244) / len(px)
    if white > 0.93:
        return False
    return True


def try_name(name, timeout=7):
    """试一个精确文件名；成功返回 (PIL.Image, 原图 URL)，失败返回 (None, 原因)。

    404/400 说明 Commons 上根本没有这个文件 → 立即判定「文件名不对」，
    不再浪费后续代理组合（所有代理都会 404）。超时/SSL 错误才继续换路重试。
    """
    if BAD_WORDS.search(name):
        return None, "badword"
    orig = commons_orig(name)
    last = "no-attempt"
    for pu in proxy_urls(orig):
        for label, opener in (("sys", SYS), ("direct", DIRECT)):
            try:
                req = urllib.request.Request(pu, headers=BUA)
                with opener.open(req, timeout=timeout) as r:
                    b = r.read()
                im = Image.open(io.BytesIO(b)).convert("RGB")
                if not looks_like_photo(im):
                    return None, "notphoto"
                return im, orig
            except urllib.error.HTTPError as e:
                last = "http%d-%s" % (e.code, label)
                if e.code in (400, 403, 404):
                    return None, "http%d" % e.code      # 文件不存在，快速失败
            except Exception as e:
                last = "%s-%s" % (type(e).__name__, label)
    return None, last


def fetch_one(item, out, log, use_rest=False):
    key, names = item
    dst = os.path.join(ASSETS, key + ".jpg")
    if os.path.exists(dst) and key in out:
        return ("skip", key, None, None, None)

    tried = []
    for name in names:
        im, info = try_name(name)
        if im is None:
            tried.append({"name": name, "why": info})
            continue
        im.thumbnail((460, 340), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=72, optimize=True)
        data = buf.getvalue()
        meta = {
            "title": name,
            "page": commons_page(name),
            "license": "Wikimedia Commons · 自由授权（详情见原图页）",
            "author": "见原图页",
            "source": "Wikimedia Commons · 精确文件名直取（MD5 路径 + 图片代理）",
            "method": "exact",
            "bytes": len(data),
        }
        return ("ok", key, meta, data, tried)

    # 精确候选全失败：可选 REST 模糊兜底（窗口开时才有用）
    if use_rest:
        try:
            from fetch_images import QUERIES, rest_search, get_image
            q = QUERIES.get(key, "")
            found = rest_search(q) if q else None
            if found:
                im = get_image(found["url"])
                if im is not None and looks_like_photo(im):
                    im.thumbnail((460, 340), Image.LANCZOS)
                    buf = io.BytesIO()
                    im.save(buf, "JPEG", quality=72, optimize=True)
                    data = buf.getvalue()
                    meta = {
                        "title": found["title"], "page": found["page"],
                        "license": "Wikimedia Commons · 自由授权（详情见原图页）",
                        "author": "见原图页",
                        "source": "Wikimedia Commons via REST 搜索 + 图片代理",
                        "query": q, "method": "rest-fallback", "bytes": len(data),
                    }
                    return ("ok", key, meta, data, tried + [{"name": "REST:" + q, "why": "ok"}])
                tried.append({"name": "REST:" + q, "why": "notphoto"})
            else:
                tried.append({"name": "REST:" + q, "why": "nomatch"})
        except Exception as e:
            tried.append({"name": "REST", "why": type(e).__name__})
    return ("fail", key, None, None, tried)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--key", default="")
    ap.add_argument("--rest", action="store_true", help="精确候选全失败时用 REST 模糊搜索兜底")
    ap.add_argument("--timeout", type=int, default=7)
    args = ap.parse_args()

    cfg = json.load(open(TARGETS, encoding="utf-8"))
    items = [(k, v) for k, v in cfg["targets"].items() if not args.key or k == args.key]
    out = json.load(open(META, encoding="utf-8")) if os.path.exists(META) else {}
    log = {}

    print("目标 %d 件 · 并发 %d · 精确文件名直取%s" % (
        len(items), args.workers, "（含 REST 兜底）" if args.rest else ""), flush=True)

    ok = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(fetch_one, it, out, log, args.rest): it[0] for it in items}
        for n, f in enumerate(as_completed(futs), 1):
            key = futs[f]
            try:
                status, key, meta, data, tried = f.result()
            except Exception as e:
                print("[%2d/%d] ERR  %s %s" % (n, len(items), key, e), flush=True)
                log[key] = [{"name": "exception", "why": str(e)}]
                continue
            if status == "ok":
                with LOCK:
                    with open(os.path.join(ASSETS, key + ".jpg"), "wb") as fh:
                        fh.write(data)
                    out[key] = meta
                    with open(META, "w", encoding="utf-8") as fh:
                        json.dump(out, fh, ensure_ascii=False, indent=1)
                ok += 1
                print("[%2d/%d] OK   %-8s %6d B | %s" % (
                    n, len(items), key, len(data), meta["title"][:52]), flush=True)
            else:
                status = "skip" if status == "skip" else "FAIL"
                print("[%2d/%d] %-4s %-8s %s" % (
                    n, len(items), status, key,
                    ", ".join(t["why"] for t in (tried or [])[:3])), flush=True)
            log[key] = tried or []
            with LOCK:
                with open(LOGPATH, "w", encoding="utf-8") as fh:
                    json.dump(log, fh, ensure_ascii=False, indent=1)

    print("\nDONE 本轮新增 %d 张，累计实物图 %d 张" % (ok, len(out)), flush=True)
    print("失败明细见 content/image_fetch_log.json；下一步：build_contact_sheet.py 生成联系表人工核对", flush=True)


if __name__ == "__main__":
    main()
