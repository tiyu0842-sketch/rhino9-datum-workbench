# -*- coding: utf-8 -*-
"""make_cover.py —— 用既有关键帧合成 B 站封面（确定性，无外部素材）。

纪律与 render.py 相同：不读系统时间、不用无种子随机、不联网。
输入是 `frames/00624.png`（第 04 镜 · 第 5 视图基准面法向），
输出 `cover_bilibili.png`（1146×717，B 站推荐 16:10）。

用法：
    python make_cover.py
"""

import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "frames", "00624.png")
OUT = os.path.join(HERE, "cover_bilibili.png")

W, H = 1146, 717

# 与 style.md §2 同一套 token（深色 Manim + Tech-Glow）
BG = (11, 14, 20)
INK = (245, 247, 250)
MUTED = (138, 148, 166)
ACCENT = (255, 176, 0)      # 橙黄：与片中高亮一致
CYAN = (94, 234, 212)
LINE = (42, 51, 66)

FONT_BD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_RG = r"C:\Windows\Fonts\msyh.ttc"
FONT_MONO = r"C:\Windows\Fonts\consola.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def text_w(draw, s, f):
    box = draw.textbbox((0, 0), s, font=f)
    return box[2] - box[0], box[3] - box[1]


def cover_crop(im, w, h, bias=0.58):
    """等比放大到铺满 (w,h)，再按 bias 横向裁切（0=靠左，1=靠右）。"""
    sw, sh = im.size
    scale = max(w / sw, h / sh)
    nw, nh = int(round(sw * scale)), int(round(sh * scale))
    im = im.resize((nw, nh), Image.LANCZOS)
    left = int(round((nw - w) * bias))
    top = int(round((nh - h) * 0.5))
    return im.crop((left, top, left + w, top + h))


def main():
    base = Image.open(SRC).convert("RGB")
    im = cover_crop(base, W, H, bias=0.50).convert("RGBA")

    # 1) 左侧压暗：让标题有稳定对比度，又不遮住几何
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = shade.load()
    for x in range(W):
        a = int(232 * max(0.0, (1.0 - x / 900.0)) ** 1.15)
        for y in range(H):
            px[x, y] = (BG[0], BG[1], BG[2], a)
    im = Image.alpha_composite(im, shade)

    # 2) 顶部 HUD 条 + 底部信息带：盖掉原片的帧号/字幕，避免和封面文字重复
    top = Image.new("RGBA", (W, 62), (BG[0], BG[1], BG[2], 252))
    im.alpha_composite(top, (0, 0))

    band = Image.new("RGBA", (W, H - 440), (BG[0], BG[1], BG[2], 0))
    bpx = band.load()
    for y in range(band.height):
        a = int(250 * min(1.0, y / 42.0))       # 42 px 渐变，避免硬边且不留残影
        for x in range(W):
            bpx[x, y] = (BG[0], BG[1], BG[2], a)
    im.alpha_composite(band, (0, 440))

    solid = Image.new("RGBA", (W, H - 500), (BG[0], BG[1], BG[2], 250))
    im.alpha_composite(solid, (0, 500))

    # 标题底板：四边羽化，压掉原片说明文字与几何边缘，保证标题对比度
    px0, py0, px1, py1 = 0, 70, 748, 360
    panel = Image.new("RGBA", (px1 - px0, py1 - py0), (BG[0], BG[1], BG[2], 0))
    ppx = panel.load()
    for y in range(panel.height):
        fy = min(1.0, y / 46.0, (panel.height - y) / 46.0)
        for x in range(panel.width):
            fx = min(1.0, x / 30.0, (panel.width - x) / 180.0)
            a = int(244 * fy * fx)
            ppx[x, y] = (BG[0], BG[1], BG[2], a)
    im.alpha_composite(panel, (px0, py0))

    d = ImageDraw.Draw(im)
    d.line([(0, 500), (W, 500)], fill=LINE + (255,), width=1)

    # 3) 顶部品牌线
    d.rectangle([64, 22, 244, 25], fill=ACCENT + (255,))

    f_tag = font(FONT_MONO, 21)
    f_h1 = font(FONT_BD, 62)
    f_h2 = font(FONT_BD, 62)
    f_sub = font(FONT_RG, 25)
    f_pill = font(FONT_RG, 19)
    f_credit = font(FONT_RG, 18)   # 含中文，等宽字体会渲染成方块

    d.text((64, 42), "DATUM PLANE  /  004", font=f_tag, fill=MUTED + (255,))

    d.text((64, 108), "斜面建模别扭？", font=f_h1, fill=INK + (255,))
    d.text((64, 180), "立一面基准面就懂了", font=f_h2, fill=ACCENT + (255,))

    d.text((66, 288), "一把可命名 / 可锁定 / 可还原的尺子", font=f_sub, fill=MUTED + (255,))

    # 4) 底部三个 pill（左侧，避开 B 站右下角时长角标）
    pills = ["纯代码生成", "零外部素材", "中文配音 · 62秒"]
    x, y = 64, H - 108
    for s in pills:
        tw, th = text_w(d, s, f_pill)
        pad_x, h_pill = 16, 38
        box = [x, y, x + tw + pad_x * 2, y + h_pill]
        d.rounded_rectangle(box, radius=6, outline=LINE + (255,), width=1,
                            fill=(19, 24, 33, 235))
        d.text((x + pad_x, y + (h_pill - th) / 2 - 2), s, font=f_pill, fill=CYAN + (255,))
        x = box[2] + 12

    # 5) 右下角来源（小字，不参与主信息）
    credit = "Rhino 9 · 犀流 004"
    cw, ch = text_w(d, credit, f_credit)
    d.text((W - 64 - cw, H - 56), credit, font=f_credit, fill=(107, 118, 134, 255))

    im.convert("RGB").save(OUT, "PNG", optimize=True)
    print("wrote", OUT, im.size, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
