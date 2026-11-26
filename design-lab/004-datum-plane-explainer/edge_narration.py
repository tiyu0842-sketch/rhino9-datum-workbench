# -*- coding: utf-8 -*-
"""edge_narration.py —— 用微软 Edge 神经语音（晓晓）合成中文旁白（国内网络直连）"""
import asyncio, os, sys
import edge_tts
import narration as N

VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "+8%"   # 略快，适配镜头时长
OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vo_edge")
os.makedirs(OUTDIR, exist_ok=True)

async def one(i, text):
    path = os.path.join(OUTDIR, "ve_%02d.mp3" % i)
    comm = edge_tts.Communicate(text, VOICE, rate=RATE)
    await comm.save(path)
    return path

async def main():
    for i, text in enumerate(N.VOICEOVER):
        p = await one(i, text)
        print("EDGE %02d %s" % (i, p))
    print("EDGE_DONE", len(N.VOICEOVER))

if __name__ == "__main__":
    asyncio.run(main())
