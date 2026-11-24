# -*- coding: utf-8 -*-
"""
add_images.py — 傻瓜式本地放图

用户不用记 c08-w0.jpg 这种编码，只要把找到的实物图存成中文名
（如「圈椅.jpg」「汝窑.jpg」「下载 (1).png」）放进 assets/ 或指定目录，
脚本会自动模糊匹配到作品、压缩、改名、更新元数据，然后 build_app.py 内嵌。

用法：
  python add_images.py                    # 扫描 assets/ 里非规范命名的图片
  python add_images.py --dir "C:/Users/.../Desktop/设计史图片"
  python add_images.py --force            # 允许覆盖已有的自动抓取图（换图时用）
  python add_images.py --list             # 只列出匹配结果，不写入

纪律：不猜、不造假。匹配不上就明确报告「未匹配」，让人自己决定；
      人工图一律标注「本地图片 · 授权请自行核对」，不冒充 Commons 授权。
"""
import argparse
import difflib
import io
import json
import os
import re

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(HERE, "content")
ASSETS = os.path.join(HERE, "assets")
META = os.path.join(CONTENT, "images.json")
CANON = re.compile(r"^[cw]\d{2}-w\d+\.(jpg|jpeg|png|webp)$", re.I)
IMGS = (".jpg", ".jpeg", ".png", ".webp", ".bmp")


def norm(s):
    s = re.sub(r"[\(（].*?[\)）]", "", s or "")          # 去括号别名
    s = re.sub(r"[\s_\-—·、,，。.\[\]【】]", "", s)
    return s.lower()


def clean_name(s):
    s = re.sub(r"^(下载|img|image|微信图片|截图|photo|图片|屏幕截图)[_\-\s]*", "", s, flags=re.I)
    s = re.sub(r"[\(（]\d+[\)）]$", "", s)                # 「(1)」「（2）」
    s = re.sub(r"^\d{8,}[_\-]?", "", s)                   # 日期/长数字前缀
    return s.strip()


def load_works():
    out = []
    for fn in ("content/china.json", "content/world.json"):
        p = os.path.join(HERE, fn)
        if not os.path.exists(p):
            continue
        for st in json.load(open(p, encoding="utf-8"))["stations"]:
            for i, w in enumerate(st["works"]):
                out.append(("%s-w%d" % (st["id"], i), st["era"], w["name"]))
    return out


# 通用二字词不算有效重合，避免「宋代陶瓷.jpg」乱命中一片作品
GENERIC_BIGRAM = set("""中国 设计 现代 古典 古代 作品 家具 陶瓷 瓷器 工艺 风格 艺术 历史
时期 样式 红色 白色 青花 彩陶 青铜 漆器 玉器 椅子 桌子 瓶子 罐子 杯子""".split())


def meaningful_bigram(a, b):
    for i in range(len(a) - 1):
        g = a[i:i + 2]
        if g in b and g not in GENERIC_BIGRAM:
            return True
    return False


def best_match(fname, works):
    n = norm(clean_name(os.path.splitext(fname)[0]))
    if len(n) < 2:
        return None, 0.0
    best, score = None, 0.0
    for key, era, wname in works:
        nw = norm(wname)
        if not nw:
            continue
        if n == nw:
            sc = 1.0
        elif nw in n or n in nw:
            sc = 0.90 + min(len(nw), len(n)) / 200.0
        else:
            sc = difflib.SequenceMatcher(None, n, nw).ratio()
            # 「汝窑碗」→「汝窑天青釉洗」这类叫法差异，靠有意义的二字重合兜住
            if meaningful_bigram(n, nw):
                sc = max(sc, 0.72)
        if sc > score:
            score, best = sc, (key, era, wname)
    return best, score


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=ASSETS, help="放图目录，默认 assets/")
    ap.add_argument("--force", action="store_true", help="覆盖已有的自动抓取图")
    ap.add_argument("--list", action="store_true", help="只报告匹配，不写入")
    ap.add_argument("--threshold", type=float, default=0.62)
    args = ap.parse_args()

    works = load_works()
    keys = {w[0] for w in works}
    meta = json.load(open(META, encoding="utf-8")) if os.path.exists(META) else {}
    src_dir = os.path.abspath(args.dir)
    if not os.path.isdir(src_dir):
        print("目录不存在：%s" % src_dir)
        return

    files = [f for f in sorted(os.listdir(src_dir))
             if f.lower().endswith(IMGS) and not CANON.match(f) and not f.startswith(".")]
    report, added, skipped, unmatched = [], 0, 0, 0

    for f in files:
        src = os.path.join(src_dir, f)
        hit, score = best_match(f, works)
        if not hit or score < args.threshold:
            cand = ", ".join(w[2] for w in
                             sorted(works, key=lambda w: -difflib.SequenceMatcher(
                                 None, norm(clean_name(f)), norm(w[2])).ratio())[:3])
            report.append("未匹配  %-34s  最接近：%s" % (f[:34], cand))
            unmatched += 1
            continue
        key, era, wname = hit
        dst = os.path.join(ASSETS, key + ".jpg")
        if os.path.exists(dst) and not args.force:
            report.append("已存在  %-34s → %s（%s），加 --force 可替换" % (f[:34], key, wname))
            skipped += 1
            continue
        try:
            im = Image.open(src).convert("RGB")
            im.thumbnail((460, 340), Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=72, optimize=True)
            data = buf.getvalue()
        except Exception as e:
            report.append("打不开  %-34s  %s" % (f[:34], e))
            unmatched += 1
            continue
        report.append("匹配    %-34s → %-9s %-22s (%.2f)" % (f[:34], key, wname[:22], score))
        if args.list:
            continue
        with open(dst, "wb") as fh:
            fh.write(data)
        meta[key] = {
            "title": "本地图片（人工提供）",
            "page": "",
            "license": "本地图片 · 授权请自行核对",
            "author": "",
            "source": "人工放图：%s" % f,
            "bytes": len(data),
        }
        added += 1

    if not args.list and added:
        with open(META, "w", encoding="utf-8") as fh:
            json.dump(meta, fh, ensure_ascii=False, indent=1)

    print("\n".join(report) if report else "（目录里没有待处理的图片）")
    print("\n合计：新增 %d，已存在 %d，未匹配/打不开 %d，素材总数 %d/%d" % (
        added, skipped, unmatched, len([k for k in keys if os.path.exists(
            os.path.join(ASSETS, k + ".jpg"))]), len(keys)))
    if not args.list and added:
        print("下一步：python build_app.py  （图片会自动内嵌）")
    if unmatched:
        print("未匹配的图请改名为作品中文名后重跑，或查看 assets/图片命名清单.csv。")


if __name__ == "__main__":
    main()
