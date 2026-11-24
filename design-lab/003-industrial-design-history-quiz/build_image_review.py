# -*- coding: utf-8 -*-
"""
build_image_review.py — 生成「图片核对表.html」

把每件作品的【手绘线描】与【自动抓到的实物图】并排摆出来，
让人一眼审出张冠李戴；缺图的给出搜图入口；可直接看到来源与授权标注。

用法：python build_image_review.py   →  图片核对表.html
"""
import base64
import html
import json
import os
import urllib.parse

import art

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(HERE, "content")
ASSETS = os.path.join(HERE, "assets")
OUT = os.path.join(HERE, "图片核对表.html")
META = os.path.join(CONTENT, "images.json")


def esc(s):
    return html.escape(str(s or ""), quote=True)


def main():
    meta = json.load(open(META, encoding="utf-8")) if os.path.exists(META) else {}
    rows = []
    for fn, track in (("content/china.json", "中国"), ("content/world.json", "世界")):
        p = os.path.join(HERE, fn)
        for st in json.load(open(p, encoding="utf-8"))["stations"]:
            for i, w in enumerate(st["works"]):
                key = "%s-w%d" % (st["id"], i)
                path = os.path.join(ASSETS, key + ".jpg")
                photo = ""
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        photo = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("ascii")
                m = meta.get(key, {})
                q = w.get("name", "")
                commons = ("https://commons.wikimedia.org/w/index.php?title=Special:MediaSearch&type=image&search="
                           + urllib.parse.quote(q))
                baidu = ("https://image.baidu.com/search/index?tn=baiduimage&word="
                         + urllib.parse.quote(q))
                rows.append({
                    "key": key, "track": track, "era": st["era"], "name": w["name"],
                    "svg": art.ART.get(w.get("art"), ""), "tint": w.get("tint", "#b98d5e"),
                    "photo": photo, "title": m.get("title", ""),
                    "page": m.get("page", ""), "license": m.get("license", ""),
                    "source": m.get("source", ""), "review": m.get("review", ""),
                    "commons": commons, "baidu": baidu,
                })

    have = sum(1 for r in rows if r["photo"])
    manual = sum(1 for r in rows if r["photo"] and r["source"].startswith("人工"))
    cards = []
    for r in rows:
        status = "have" if r["photo"] else "miss"
        photo_html = ('<img src="%s" alt="%s">' % (r["photo"], esc(r["name"]))) if r["photo"] else \
            '<div class="none">尚缺实物图<br><small>点下方链接找图</small></div>'
        meta_line = esc(r["title"] or "—")
        src_line = esc(r["license"] or "—")
        badge = ('<span class="badge ok">已核对</span>' if r["review"] == "已核对" else
                 '<span class="badge approx">近似 · 建议核对</span>' if r["review"] == "近似" else
                 '<span class="badge miss">—</span>')
        page_link = ('<a href="%s" target="_blank" rel="noopener">原图页 ↗</a>' % esc(r["page"])) if r["page"] else ""
        cards.append("""
<div class="card %s" data-status="%s" data-track="%s" data-text="%s">
  <div class="pair">
    <div class="cell line"><div class="artbox" style="--glaze:%s">%s</div><span>线描（形体记号）</span></div>
    <div class="cell real">%s<span>实物图</span></div>
  </div>
  <div class="info">
    <div class="nm">%s <em>%s</em></div>
    <div class="era">%s · %s</div>
    <div class="src" title="%s">Commons：%s</div>
    <div class="lic">%s %s</div>
    <div class="links"><a href="%s" target="_blank" rel="noopener">维基共享资源 ↗</a>
      <a href="%s" target="_blank" rel="noopener">百度图片 ↗</a>%s</div>
  </div>
</div>""" % (
            status, status, r["track"], esc(r["name"] + " " + r["era"] + " " + r["key"]),
            esc(r["tint"]), r["svg"], photo_html,
            esc(r["name"]), esc(r["key"]), r["track"], esc(r["era"]),
            esc(r["title"]), meta_line, src_line, badge,
            esc(r["commons"]), esc(r["baidu"]), page_link))

    tpl = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>设计史长河 · 实物图核对表</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#f6f4ef;color:#2f2b26;font:14px/1.6 "Microsoft YaHei","PingFang SC",sans-serif}
.wrap{max-width:1280px;margin:0 auto;padding:26px 20px 60px}
h1{font:600 25px/1.3 "Noto Serif SC","Songti SC",serif;margin:0 0 6px}
.sub{color:#8a8175;font-size:13px;margin-bottom:18px}
.stats{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}
.stat{background:#fff;border:1px solid #e6e0d5;border-radius:12px;padding:10px 16px;min-width:120px}
.stat b{display:block;font-size:22px;color:#a4562f}
.stat span{font-size:11.5px;color:#8a8175}
.note{background:#fff8ea;border:1px solid #ecdcbb;border-left:3px solid #c89430;border-radius:10px;
  padding:12px 16px;font-size:12.5px;line-height:1.9;margin-bottom:18px}
.note code{background:#f2e9d6;padding:1px 5px;border-radius:4px;font-size:11.5px}
.bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:16px}
.chip{background:#fff;border:1px solid #e0d9cc;border-radius:999px;padding:6px 14px;cursor:pointer;font-size:12.5px}
.chip.on{background:#a4562f;border-color:#a4562f;color:#fff}
input.search{margin-left:auto;background:#fff;border:1px solid #e0d9cc;border-radius:999px;
  padding:7px 14px;font:inherit;font-size:12.5px;min-width:200px;outline:none}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px}
.card{background:#fff;border:1px solid #e6e0d5;border-radius:14px;overflow:hidden;box-shadow:0 2px 10px rgba(90,70,40,.05)}
.card.miss{border-color:#e7b9a6;background:#fffaf7}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:#eee7db}
.cell{background:#fff;min-height:150px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:8px}
.cell span{font-size:10.5px;color:#9b9184;margin-top:6px}
.cell .artbox{width:100%;height:120px;color:#6b5a45;--glaze:#b98d5e}
.cell .artbox svg{width:100%;height:100%}
.art .a{fill:var(--glaze);fill-opacity:.42}
.art .b{fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
.art .c{fill:none;stroke:currentColor;stroke-width:1;opacity:.42}
.cell.real img{max-width:100%;max-height:130px;object-fit:contain;border-radius:8px}
.cell .none{text-align:center;color:#b98a72;font-size:12px;height:120px;display:flex;
  flex-direction:column;justify-content:center;line-height:1.8}
.cell .none small{color:#b6a99a}
.info{padding:11px 13px 13px}
.nm{font-weight:600;font-size:14px}
.nm em{font-style:normal;font-size:10.5px;color:#a79c8c;font-weight:400;margin-left:5px}
.era{font-size:11px;color:#8a8175;margin:2px 0 7px}
.src{font-size:11px;color:#6b6155;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lic{font-size:10.5px;color:#9b9184;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.links{margin-top:9px;display:flex;gap:10px;flex-wrap:wrap}
.links a{font-size:11px;color:#a4562f;text-decoration:none;border-bottom:1px dotted #c99}
.links a:hover{color:#753a1e}
.badge{font-size:10px;padding:1px 7px;border-radius:999px;margin-left:4px}
.badge.ok{background:#e3f0e6;color:#3f7d54}
.badge.approx{background:#fbeed2;color:#a97716}
.badge.miss{color:#b6a99a}
.hide{display:none}
footer{margin-top:30px;font-size:11.5px;color:#9b9184;line-height:1.9}
</style></head><body><div class="wrap">
<h1>实物图核对表</h1>
<div class="sub">自动抓取的图可能张冠李戴 —— 左线描、右实物并排看一眼，不对就换。</div>
<div class="stats">
  <div class="stat"><b>__TOTAL__</b><span>作品总数</span></div>
  <div class="stat"><b>__HAVE__</b><span>已有实物图</span></div>
  <div class="stat"><b>__MISS__</b><span>尚缺</span></div>
  <div class="stat"><b>__MANUAL__</b><span>人工提供</span></div>
</div>
<div class="note">
<b>怎么换图（不用记编码）</b>：点卡片里的「百度图片 / 维基共享资源」找到满意的图，
存成<b>作品中文名</b>（如 <code>圈椅.jpg</code>）丢进 <code>assets/</code> →
运行 <code>python add_images.py --force</code> 自动匹配压缩 →
<code>python build_app.py</code> 内嵌。匹配不上会明确报「未匹配」，不会乱塞。<br>
<b>授权标注</b>：Commons 自动图统一写「自由授权（详情见原图页）」并附原图页链接；
人工放的图写「本地图片 · 授权请自行核对」。不编造作者与授权名。
</div>
<div class="bar">
  <button class="chip on" data-f="all">全部</button>
  <button class="chip" data-f="have">已有图</button>
  <button class="chip" data-f="miss">尚缺图</button>
  <button class="chip" data-f="china">中国线</button>
  <button class="chip" data-f="world">世界线</button>
  <input class="search" id="q" placeholder="搜作品名 / 站点 / 编码">
</div>
<div class="grid" id="grid">__CARDS__</div>
<footer>生成脚本：build_image_review.py · 数据：content/world.json、china.json、images.json、art.py · 单文件离线可用<br>
本表只用于人工核对与替换，不是学习主界面；主应用为 design-history.html。</footer>
</div>
<script>
var filter='all', q='';
function apply(){
  document.querySelectorAll('.card').forEach(function(c){
    var okF = filter==='all' || (filter==='have'&&c.dataset.status==='have')
      || (filter==='miss'&&c.dataset.status==='miss') || c.dataset.track===filter;
    var okQ = !q || c.dataset.text.toLowerCase().indexOf(q)>=0;
    c.classList.toggle('hide', !(okF&&okQ));
  });
}
document.querySelectorAll('.chip').forEach(function(b){ b.onclick=function(){
  document.querySelectorAll('.chip').forEach(function(x){x.classList.remove('on')});
  b.classList.add('on'); filter=b.dataset.f; apply(); };});
document.getElementById('q').addEventListener('input',function(e){q=e.target.value.trim().toLowerCase();apply();});
</script></body></html>"""
    out = (tpl.replace("__TOTAL__", str(len(rows)))
              .replace("__HAVE__", str(have))
              .replace("__MISS__", str(len(rows) - have))
              .replace("__MANUAL__", str(manual))
              .replace("__CARDS__", "\n".join(cards)))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(out)
    print("OK -> 图片核对表.html  %d 作品，%d 有图，%d 缺图，%.2f MB" % (
        len(rows), have, len(rows) - have, len(out.encode("utf-8")) / 1024 / 1024))


if __name__ == "__main__":
    main()
