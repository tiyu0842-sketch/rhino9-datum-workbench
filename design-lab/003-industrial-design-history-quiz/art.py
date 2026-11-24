# -*- coding: utf-8 -*-
"""
art.py — 设计史作品的 SVG 线描图库（离线、可换色、无外链）

设计原则
--------
1. 只用 <path>/<ellipse>/<line>，统一 160x120 视框；
2. 填色交给 CSS 变量 --glaze（每个作品可覆盖），描边用 currentColor → 自动跟随主题；
3. 对称器物用「画一半 + 镜像」，保证器形不歪；
4. 不是写实复原，是「可辨识的形体记号」——学习站要的是认得出，不是照片。
"""

W = 160
H = 120


def sym(inner):
    """把左半边镜像到右半边（视框宽 160）。"""
    return inner + '<g transform="translate(160,0) scale(-1,1)">' + inner + '</g>'


def vessel(profile, extra="", fill=True):
    """profile 为左侧外轮廓（开口路径，从口沿到足底），自动闭合填充 + 镜像描边。"""
    # profile 起止点都在中轴 x=80 上，Z 自动沿中轴闭合，不会出现接缝
    fill_path = '<path class="a" d="%s Z"/>' % profile if fill else ""
    outline = '<path class="b" d="%s"/>' % profile
    body = fill_path + outline
    return sym(body) + extra


def wrap(inner):
    return ('<svg class="art" viewBox="0 0 160 120" preserveAspectRatio="xMidYMid meet" '
            'aria-hidden="true">' + inner + '</svg>')


GROUND = '<path class="c" d="M16 106 H144"/>'

ART = {}

# ────────────────────────────── 中国 · 陶瓷 ──────────────────────────────
ART["cai_tao"] = wrap(
    '<ellipse class="b" cx="80" cy="56" rx="54" ry="8"/>'
    '<path class="a" d="M26 56 C32 92 128 92 134 56 Z"/>'
    '<path class="b" d="M30 72 l9 -7 l9 7 l9 -7 l9 7 l9 -7 l9 7 l9 -7 l9 7"/>'
    '<path class="c" d="M34 84 q46 14 92 0"/>'
    '<path class="b" d="M40 62 q40 8 80 0"/>' + GROUND)

ART["hei_tao"] = wrap(
    '<ellipse class="b" cx="80" cy="40" rx="26" ry="5"/>'
    '<path class="a" d="M54 40 C56 60 104 60 106 40 Z"/>'
    '<path class="b" d="M74 58 L71 90 M86 58 L89 90"/>'
    '<path class="a" d="M62 92 Q80 84 98 92 Q80 101 62 92 Z"/>'
    '<path class="c" d="M60 48 q20 6 40 0"/>' + GROUND)

ART["ding"] = wrap(
    '<path class="b" d="M52 44 q0 -12 12 -12 M108 44 q0 -12 -12 -12"/>'
    '<path class="a" d="M46 44 H114 V72 Q80 88 46 72 Z"/>'
    '<path class="b" d="M46 44 H114"/>'
    '<path class="c" d="M58 54 h16 v14 h-16 z M86 54 h16 v14 h-16 z"/>'
    '<path class="b" d="M54 84 l-5 20 M80 88 v18 M106 84 l5 20"/>'
    '<path class="c" d="M46 62 H114"/>' + GROUND)

ART["ma"] = wrap(
    '<ellipse class="a" cx="74" cy="68" rx="26" ry="13"/>'
    '<path class="a" d="M90 60 L100 34 L110 36 L104 64 Z"/>'
    '<path class="a" d="M98 36 L114 30 L122 40 L104 44 Z"/>'
    '<path class="b" d="M100 34 L102 24"/>'
    '<path class="b" d="M52 78 L50 104 M66 80 L65 104 M90 80 L92 104 M102 78 L106 104"/>'
    '<path class="b" d="M48 60 q-10 8 -8 22"/>'
    '<path class="c" d="M62 56 q14 -8 28 0 M60 72 q14 6 28 0 M96 40 l10 2"/>' + GROUND)

ART["ewer"] = wrap(
    '<path class="a" d="M64 56 q-16 14 -8 30 q8 14 24 14 q16 0 24 -14 q8 -16 -8 -30 z"/>'
    '<path class="b" d="M70 56 l-2 -16 h24 l-2 16"/>'
    '<path class="b" d="M68 40 h24"/>'
    '<path class="b" d="M64 60 q-18 -4 -22 -18"/>'
    '<path class="b" d="M104 60 q20 10 12 30"/>'
    '<path class="c" d="M62 78 q18 8 36 0"/>' + GROUND)

ART["meiping"] = wrap(
    vessel("M80 26 L72 27 Q66 29 69 37 Q46 52 48 74 Q50 96 80 100",
           '<path class="c" d="M52 66 q10 -8 20 0 t20 0 t16 -4"/>'
           '<path class="c" d="M54 82 q12 6 26 0 t22 -4"/>') + GROUND)

ART["bowl"] = wrap(
    '<ellipse class="b" cx="80" cy="52" rx="48" ry="6"/>'
    '<path class="a" d="M32 52 C38 88 122 88 128 52 Z"/>'
    '<path class="b" d="M68 90 h24"/>'
    '<path class="c" d="M50 62 l10 6 l-6 8 M96 58 l-8 10 l10 4 M74 70 l6 8"/>' + GROUND)

ART["vase_fencai"] = wrap(
    '<path class="a" d="M80 26 Q50 48 52 70 Q54 94 80 98 Q106 94 108 70 Q110 48 80 26 Z"/>'
    '<path class="b" d="M80 26 Q50 48 52 70 Q54 94 80 98"/>'
    '<path class="b" d="M80 26 Q110 48 108 70 Q106 94 80 98"/>'
    '<path class="b" d="M72 28 L70 18 H90 L88 28"/>'
    '<path class="c" d="M60 62 q14 10 28 0 q10 8 16 4"/>'
    '<circle class="c" cx="80" cy="54" r="4"/>' + GROUND)

ART["zisha"] = wrap(
    '<path class="a" d="M54 62 q0 -12 26 -12 q26 0 26 12 q0 22 -26 22 q-26 0 -26 -22 z"/>'
    '<path class="b" d="M54 62 h52"/>'
    '<path class="b" d="M76 50 q4 -8 8 0"/>'
    '<path class="b" d="M106 64 q18 2 16 16 q-2 10 -12 10"/>'
    '<path class="b" d="M54 66 q-18 4 -14 16"/>'
    '<path class="c" d="M62 72 q18 8 36 0"/>' + GROUND)

# ────────────────────────────── 中国 · 漆 / 织 / 玉 ──────────────────────────────
ART["lacquer"] = wrap(
    '<path class="a" d="M34 56 q46 -12 92 0 q-4 26 -46 26 q-42 0 -46 -26 z"/>'
    '<path class="b" d="M34 56 q-12 -4 -8 -10 q4 -6 12 0"/>'
    '<path class="b" d="M126 56 q12 -4 8 -10 q-4 -6 -12 0"/>'
    '<path class="c" d="M46 64 q34 -8 68 0 M52 74 q28 -6 56 0"/>' + GROUND)

ART["silk"] = wrap(
    '<rect class="a" x="30" y="34" width="100" height="60" rx="2"/>'
    '<path class="b" d="M30 34 h100 v60 h-100 z"/>'
    '<path class="c" d="M30 54 h100 M30 74 h100 M60 34 v60 M100 34 v60"/>'
    '<path class="c" d="M40 44 q8 8 16 0 q8 -8 16 0 M92 64 q8 8 16 0"/>' + GROUND)

ART["jade"] = wrap(
    '<circle class="a" cx="80" cy="68" r="36"/>'
    '<circle class="b" cx="80" cy="68" r="36"/>'
    '<circle class="b" cx="80" cy="68" r="9"/>'
    '<path class="c" d="M58 50 q6 8 0 16 M80 38 q8 8 0 16 M102 50 q-6 8 0 16 M52 76 q8 -4 14 4"/>' + GROUND)

# ────────────────────────────── 中国 · 家具 ──────────────────────────────
ART["quanyi"] = wrap(
    '<path class="b" d="M42 54 A38 30 0 0 1 118 54"/>'
    '<path class="b" d="M42 54 q-3 8 4 12 M118 54 q3 8 -4 12"/>'
    '<path class="a" d="M74 26 h12 v48 h-12 z"/>'
    '<path class="b" d="M48 74 H112"/>'
    '<path class="b" d="M52 74 V104 M46 80 V104 M108 74 V104 M114 80 V104"/>'
    '<path class="c" d="M46 64 L52 74 M114 64 L108 74 M48 86 q32 8 64 0 M52 96 H108"/>' + GROUND)

ART["guanmao"] = wrap(
    '<path class="b" d="M36 32 Q80 24 124 32"/>'
    '<path class="a" d="M72 40 h16 v32 h-16 z"/>'
    '<path class="b" d="M44 32 V72 M116 32 V72"/>'
    '<path class="b" d="M44 54 h16 M100 54 h16"/>'
    '<path class="b" d="M44 72 H116"/>'
    '<path class="b" d="M42 72 V104 M118 72 V104 M48 78 V104 M112 78 V104"/>'
    '<path class="c" d="M42 90 H118"/>' + GROUND)

ART["luohan"] = wrap(
    '<path class="a" d="M32 46 H128 V74 H32 Z"/>'
    '<path class="a" d="M24 58 H44 V74 H24 Z"/>'
    '<path class="b" d="M32 46 H128 M24 58 H44"/>'
    '<path class="b" d="M32 74 H128 M24 74 H44"/>'
    '<path class="b" d="M24 74 H136 V82 H24 Z"/>'
    '<path class="b" d="M30 82 V104 M130 82 V104 M38 82 V100 M122 82 V100"/>'
    '<path class="c" d="M40 54 H120 M40 64 H120"/>' + GROUND)

ART["qiaotou"] = wrap(
    '<path class="b" d="M16 60 q-4 -8 4 -12 M144 60 q4 -8 -4 -12"/>'
    '<path class="b" d="M16 60 H144"/>'
    '<path class="b" d="M24 60 V70 H136 V60"/>'
    '<path class="b" d="M30 70 V104 M130 70 V104"/>'
    '<path class="c" d="M30 96 H130 M58 70 q10 8 22 8 q12 0 22 -8"/>' + GROUND)

ART["taishi"] = wrap(
    '<path class="a" d="M66 36 h28 v34 h-28 z"/>'
    '<path class="b" d="M66 36 q14 -8 28 0"/>'
    '<circle class="c" cx="80" cy="52" r="8"/>'
    '<path class="b" d="M40 46 q-12 6 0 14 q-6 10 6 14 M120 46 q12 6 0 14 q6 10 -6 14"/>'
    '<path class="b" d="M40 74 H120"/>'
    '<path class="b" d="M42 74 V104 M118 74 V104 M48 80 V104 M112 80 V104"/>'
    '<path class="c" d="M40 88 H120 M42 98 H118"/>' + GROUND)

# ────────────────────────────── 中国 · 民国 ──────────────────────────────
ART["yuefenpai"] = wrap(
    '<rect class="b" x="30" y="20" width="100" height="82" rx="2"/>'
    '<path class="a" d="M44 34 q18 -8 34 6 q10 10 8 26 q-2 20 -14 26 q-14 6 -22 -4 q-10 -12 -12 -28 q-2 -18 6 -26 z"/>'
    '<circle class="b" cx="60" cy="44" r="9"/>'
    '<path class="c" d="M96 90 h26 M96 96 h26 M104 20 v12"/>'
    '<path class="b" d="M38 96 H122"/>' + GROUND)

# ────────────────────────────── 外国 · 建筑 ──────────────────────────────
ART["column"] = wrap(
    '<path class="b" d="M30 44 H82 L56 30 Z"/>'
    '<path class="b" d="M30 44 H82"/>'
    '<path class="b" d="M36 52 H76 M34 46 H78"/>'
    '<path class="c" d="M42 52 V92 M52 52 V92 M62 52 V92 M72 52 V92"/>'
    '<path class="b" d="M36 92 H76 M32 100 H80"/>'
    '<path class="c" d="M88 60 h56 M88 72 h56 M88 84 h56 M104 60 v24 M128 60 v24"/>' + GROUND)

ART["gothic"] = wrap(
    '<path class="b" d="M40 104 V58 Q40 26 80 16 Q120 26 120 58 V104"/>'
    '<path class="b" d="M62 104 V72 Q62 56 80 50 Q98 56 98 72 V104"/>'
    '<circle class="c" cx="80" cy="46" r="14"/>'
    '<path class="c" d="M80 32 V60 M66 46 H94 M70 36 L90 56 M90 36 L70 56"/>'
    '<path class="c" d="M44 66 V104 M116 66 V104"/>' + GROUND)

ART["chest"] = wrap(
    '<rect class="a" x="34" y="44" width="92" height="50"/>'
    '<path class="b" d="M34 44 h92 v50 h-92 z"/>'
    '<path class="b" d="M34 60 H126"/>'
    '<path class="c" d="M34 74 H126 M46 44 V94 M114 44 V94"/>'
    '<path class="b" d="M38 94 V104 M122 94 V104"/>'
    '<path class="c" d="M74 66 h12 v10 h-12 z"/>' + GROUND)

ART["dome"] = wrap(
    '<path class="b" d="M40 92 Q40 40 80 30 Q120 40 120 92"/>'
    '<path class="c" d="M56 88 Q56 48 80 40 Q104 48 104 88"/>'
    '<path class="c" d="M80 30 V92 M48 76 Q80 60 112 76"/>'
    '<path class="b" d="M74 30 h12 v-8 h-12 z"/>'
    '<path class="b" d="M32 92 H128"/>'
    '<path class="c" d="M32 100 H128"/>' + GROUND)

ART["crystal"] = wrap(
    '<path class="b" d="M22 96 V58 Q22 28 80 28 Q138 28 138 58 V96"/>'
    '<path class="c" d="M22 58 H138 M22 70 H138 M22 82 H138"/>'
    '<path class="c" d="M40 58 V96 M60 38 V96 M80 32 V96 M100 38 V96 M120 58 V96"/>'
    '<path class="b" d="M18 96 H142"/>'
    '<path class="b" d="M64 96 V80 Q80 72 96 80 V96"/>' + GROUND)

ART["bauhaus"] = wrap(
    '<rect class="a" x="28" y="52" width="72" height="46"/>'
    '<rect class="a" x="100" y="36" width="32" height="62"/>'
    '<path class="b" d="M28 52 h72 v46 h-72 z M100 36 h32 v62 h-32 z"/>'
    '<path class="c" d="M28 62 H100 M28 74 H100 M28 86 H100 M110 46 H122 M110 58 H122 M110 70 H122 M110 82 H122"/>'
    '<path class="b" d="M112 36 V26"/>'
    '<path class="c" d="M24 98 H136"/>' + GROUND)

ART["deco"] = wrap(
    '<path class="a" d="M60 96 V44 H100 V96 Z"/>'
    '<path class="a" d="M70 44 V28 H90 V44 Z"/>'
    '<path class="b" d="M80 28 V12"/>'
    '<path class="b" d="M60 96 h40"/>'
    '<path class="c" d="M68 54 h24 M68 64 h24 M68 74 h24 M68 84 h24"/>'
    '<path class="c" d="M72 28 L66 44 M88 28 L94 44"/>'
    '<path class="b" d="M48 96 H112"/>' + GROUND)

# ────────────────────────────── 外国 · 家具 ──────────────────────────────
ART["rococo"] = wrap(
    '<path class="b" d="M56 30 Q80 20 104 30"/>'
    '<path class="a" d="M74 30 h12 v26 h-12 z"/>'
    '<path class="b" d="M58 30 V56 M102 30 V56"/>'
    '<path class="b" d="M56 56 H104"/>'
    '<path class="b" d="M56 50 q-12 4 -2 12 M104 50 q12 4 2 12"/>'
    '<path class="b" d="M58 56 q-9 16 -1 26 q4 6 -3 10 M102 56 q9 16 1 26 q-4 6 3 10"/>'
    '<path class="b" d="M66 56 v22 M94 56 v22"/>'
    '<path class="c" d="M60 42 q20 -8 40 0 M62 34 q18 -6 36 0"/>' + GROUND)

ART["chippendale"] = wrap(
    '<path class="b" d="M50 34 Q80 26 110 34"/>'
    '<path class="a" d="M74 34 h12 v30 h-12 z"/>'
    '<path class="b" d="M56 34 V58 M104 34 V58"/>'
    '<path class="b" d="M56 58 H104"/>'
    '<path class="b" d="M56 52 q-10 4 -4 10 M104 52 q10 4 4 10"/>'
    '<path class="b" d="M58 58 q-6 20 2 30 M102 58 q6 20 -2 30"/>'
    '<path class="b" d="M62 58 V88 M98 58 V88"/>'
    '<path class="c" d="M62 84 H98"/>' + GROUND)

ART["morris_chair"] = wrap(
    '<path class="b" d="M46 24 H114 V70"/>'
    '<path class="c" d="M46 36 H114 M46 48 H114 M46 60 H114"/>'
    '<path class="b" d="M46 70 H114"/>'
    '<path class="b" d="M42 70 V104 M118 70 V104 M48 76 V100 M112 76 V100"/>'
    '<path class="b" d="M46 58 q-10 4 -4 12 M114 58 q10 4 4 12"/>'
    '<path class="c" d="M42 94 H118"/>' + GROUND)

ART["thonet"] = wrap(
    '<path class="b" d="M56 26 Q80 18 104 26 Q110 48 80 52 Q50 48 56 26 Z"/>'
    '<path class="c" d="M62 34 Q80 28 98 34"/>'
    '<path class="a" d="M54 56 H106 V62 H54 Z"/>'
    '<path class="b" d="M58 62 L46 104 M102 62 L114 104 M66 62 L62 104 M94 62 L98 104"/>'
    '<path class="c" d="M52 88 H108"/>' + GROUND)

ART["mackintosh"] = wrap(
    '<path class="b" d="M62 16 H98 V74"/>'
    '<path class="c" d="M68 24 H92 M68 34 H92 M68 44 H92 M68 54 H92 M68 64 H92 M62 34 H98 M62 54 H98"/>'
    '<path class="b" d="M58 74 H102"/>'
    '<path class="b" d="M58 74 V104 M102 74 V104 M64 74 V100 M96 74 V100"/>'
    '<path class="b" d="M58 62 L48 74 M102 62 L112 74"/>'
    '<path class="c" d="M58 92 H102"/>' + GROUND)

ART["redblue"] = wrap(
    '<path class="b" d="M40 34 H120"/>'
    '<path class="b" d="M44 34 V100 M116 34 V100"/>'
    '<path class="b" d="M40 60 H120"/>'
    '<path class="a" d="M40 60 H120 V66 H40 Z"/>'
    '<path class="a" d="M40 34 H50 V60 H40 Z"/>'
    '<path class="b" d="M50 66 V100"/>'
    '<path class="c" d="M40 92 H120"/>' + GROUND)

ART["wassily"] = wrap(
    '<path class="b" d="M42 30 V100 M118 30 V100"/>'
    '<path class="b" d="M42 30 H70 M90 30 H118"/>'
    '<path class="b" d="M34 98 H66 M94 98 H126"/>'
    '<path class="a" d="M52 40 H108 V52 H52 Z"/>'
    '<path class="a" d="M50 60 H110 V72 H50 Z"/>'
    '<path class="b" d="M52 40 V72 M108 40 V72"/>'
    '<path class="b" d="M42 46 H52 M108 46 H118"/>'
    '<path class="c" d="M56 46 H104 M56 66 H104"/>' + GROUND)

ART["barcelona"] = wrap(
    '<path class="b" d="M46 62 L74 96 M114 62 L86 96"/>'
    '<path class="b" d="M46 96 H74 M86 96 H114"/>'
    '<path class="a" d="M48 56 H112 V64 H48 Z"/>'
    '<path class="a" d="M52 40 H108 V54 H52 Z"/>'
    '<path class="c" d="M56 44 H104 M56 48 H104 M56 52 H104"/>'
    '<path class="b" d="M48 56 L52 40 M112 56 L108 40"/>' + GROUND)

ART["tulip"] = wrap(
    '<path class="b" d="M80 104 V76"/>'
    '<path class="b" d="M64 104 Q80 92 96 104"/>'
    '<path class="a" d="M58 56 Q80 42 102 56 Q104 66 80 68 Q56 66 58 56 Z"/>'
    '<path class="b" d="M58 56 Q80 42 102 56"/>'
    '<path class="b" d="M58 56 Q80 70 102 56"/>'
    '<path class="c" d="M80 68 V76"/>' + GROUND)

ART["panton"] = wrap(
    '<path class="a" d="M58 16 Q92 16 92 34 Q92 50 68 58 Q46 66 46 84 L46 92 L112 92 L112 84 L60 84 Q58 76 80 66 Q104 54 104 34 Q104 8 60 8 Z"/>'
    '<path class="b" d="M58 16 Q92 16 92 34 Q92 50 68 58 Q46 66 46 84 L46 92"/>'
    '<path class="b" d="M112 84 L60 84 Q58 76 80 66 Q104 54 104 34 Q104 8 60 8"/>'
    '<path class="c" d="M64 24 Q86 24 86 34 M52 78 Q80 74 104 60"/>' + GROUND)

ART["carlton"] = wrap(
    '<path class="b" d="M38 104 L48 34 L64 104 M122 104 L112 34 L96 104"/>'
    '<path class="a" d="M48 34 H64 V42 H48 Z"/>'
    '<path class="a" d="M96 34 H112 V42 H96 Z"/>'
    '<path class="c" d="M44 70 H116 M42 86 H118"/>'
    '<path class="b" d="M60 44 L64 70 M100 44 L96 70"/>'
    '<path class="c" d="M70 54 H90"/>' + GROUND)

# ────────────────────────────── 外国 · 产品 ──────────────────────────────
ART["guimard"] = wrap(
    '<path class="b" d="M50 104 Q46 60 62 44 M110 104 Q114 60 98 44"/>'
    '<path class="b" d="M62 44 q10 -10 18 -10 q8 0 18 10"/>'
    '<path class="c" d="M58 80 q4 -14 14 -18 M102 80 q-4 -14 -14 -18"/>'
    '<path class="b" d="M46 104 H66 M94 104 H114"/>'
    '<path class="a" d="M70 30 h20 v10 h-20 z"/>'
    '<path class="b" d="M70 40 h20"/>'
    '<circle class="c" cx="80" cy="24" r="3"/>' + GROUND)

ART["wedgwood"] = wrap(
    '<path class="a" d="M80 34 Q58 42 58 62 Q58 86 80 92 Q102 86 102 62 Q102 42 80 34 Z"/>'
    '<path class="b" d="M80 34 Q58 42 58 62 Q58 86 80 92 Q102 86 102 62 Q102 42 80 34"/>'
    '<path class="b" d="M72 34 V26 H88 V34"/>'
    '<path class="b" d="M74 34 H86"/>'
    '<path class="b" d="M68 92 H92 M73 92 V100 H87 V92"/>'
    '<path class="b" d="M60 46 q-14 6 -8 20 M100 46 q14 6 8 20"/>'
    '<path class="c" d="M66 62 q14 8 28 0 M68 74 q12 6 24 0"/>' + GROUND)

ART["lamp"] = wrap(
    '<path class="a" d="M62 34 L98 34 L110 16 L50 16 Z"/>'
    '<path class="b" d="M62 34 L98 34 L110 16 L50 16 Z"/>'
    '<path class="b" d="M80 34 V62"/>'
    '<circle class="b" cx="80" cy="64" r="4"/>'
    '<path class="b" d="M64 100 Q80 86 96 100 M66 100 H94"/>'
    '<path class="c" d="M80 68 V88"/>' + GROUND)

ART["poster"] = wrap(
    '<rect class="b" x="26" y="22" width="108" height="80"/>'
    '<path class="a" d="M26 84 L86 22 H118 L26 96 Z"/>'
    '<circle class="a" cx="104" cy="44" r="14"/>'
    '<path class="c" d="M36 94 L120 30"/>' + GROUND)

ART["coke"] = wrap(
    '<path class="a" d="M68 22 h24 v10 q10 14 6 32 q-4 20 2 38 h-40 q6 -18 2 -38 q-4 -18 6 -32 z"/>'
    '<path class="b" d="M68 22 h24 v10 q10 14 6 32 q-4 20 2 38 h-40 q6 -18 2 -38 q-4 -18 6 -32 z"/>'
    '<path class="c" d="M70 30 h20 M64 44 q16 8 32 0 M62 60 q18 8 36 0 M62 76 q18 8 36 0"/>' + GROUND)

ART["beetle"] = wrap(
    '<path class="a" d="M24 82 q-4 -26 24 -32 q26 -6 52 -4 q30 2 34 18 q4 14 -8 18 z"/>'
    '<path class="b" d="M24 82 q-4 -26 24 -32 q26 -6 52 -4 q30 2 34 18 q4 14 -8 18 z"/>'
    '<path class="c" d="M52 52 q10 -10 24 -10 q14 0 22 8 M56 54 V82 M96 54 V80"/>'
    '<circle class="b" cx="42" cy="88" r="7"/><circle class="b" cx="118" cy="88" r="7"/>'
    '<path class="c" d="M30 74 h16 M110 70 h16"/>' + GROUND)

ART["braun"] = wrap(
    '<rect class="a" x="30" y="40" width="100" height="46" rx="3"/>'
    '<path class="b" d="M30 40 h100 v46 h-100 z"/>'
    '<circle class="b" cx="48" cy="63" r="9"/>'
    '<path class="c" d="M66 50 h58 M66 58 h58 M66 66 h58 M66 74 h58 M78 50 V78"/>'
    '<path class="b" d="M40 86 h80"/>' + GROUND)

ART["iphone"] = wrap(
    '<rect class="a" x="56" y="20" width="48" height="80" rx="9"/>'
    '<rect class="b" x="56" y="20" width="48" height="80" rx="9"/>'
    '<rect class="b" x="70" y="24" width="20" height="4" rx="2"/>'
    '<path class="c" d="M62 38 h36 M62 50 h36 M62 62 h36 M62 74 h36"/>'
    '<circle class="b" cx="80" cy="92" r="3"/>' + GROUND)
