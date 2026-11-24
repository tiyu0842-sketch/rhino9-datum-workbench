<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>设计史长河 · 时间线 / 卡片 / 题库</title>
<style>
:root{
  --bg:#f6f2ea; --panel:#fffdf7; --ink:#241f1b; --muted:#7e756a; --line:#e3d9c8;
  --accent:#b4553f; --accent2:#5c8a76; --gold:#a3822c; --card:#fffaf0;
  --good:#4f8a5f; --bad:#c0492f; --shadow:0 2px 10px rgba(60,40,20,.06);
  --serif:"Noto Serif SC","Songti SC","SimSun",serif;
  --sans:"Microsoft YaHei","PingFang SC","Hiragino Sans GB",sans-serif;
}
html[data-theme="kitty"]{
  --bg:#fff5f8; --panel:#fffdfd; --ink:#5b3d49; --muted:#a9808f; --line:#f2d6e1;
  --accent:#ef7fa3; --accent2:#86bfa4; --gold:#e0a33d; --card:#fffafc;
  --good:#59ad80; --bad:#e4768d; --shadow:0 3px 16px rgba(220,120,155,.10);
  --serif:"Noto Serif SC","Songti SC","SimSun",serif;
  --sans:"Microsoft YaHei","PingFang SC","Hiragino Sans GB",sans-serif;
}
html[data-theme="kitty"] body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;
  background-image:radial-gradient(circle at 12% 18%,rgba(239,127,163,.10) 0 7px,transparent 8px),
                   radial-gradient(circle at 86% 74%,rgba(134,191,164,.11) 0 6px,transparent 7px);}
html[data-theme="kitty"] .wrap{position:relative;z-index:1}
html[data-theme="kitty"] .brand h1::before{content:"✿";color:var(--accent);margin-right:6px}
html[data-theme="kitty"] .thread{background:linear-gradient(135deg,rgba(239,127,163,.12),rgba(134,191,164,.10));
  border-color:rgba(239,127,163,.35)}
html[data-theme="kitty"] .st::before{box-shadow:0 0 0 4px var(--bg)}
html[data-theme="kitty"] .panel,html[data-theme="kitty"] .qcard,html[data-theme="kitty"] .sthead,
html[data-theme="kitty"] .stbody,html[data-theme="kitty"] .modal,html[data-theme="kitty"] .btn,
html[data-theme="kitty"] .pill,html[data-theme="kitty"] .chip,html[data-theme="kitty"] .opt,
html[data-theme="kitty"] .wk,html[data-theme="kitty"] .pp,html[data-theme="kitty"] .statbox,
html[data-theme="kitty"] .schoolcard,html[data-theme="kitty"] .face{border-radius:20px}
html[data-theme="kitty"] .face,html[data-theme="kitty"] .flip{height:auto;min-height:420px}
html[data-theme="kitty"] .cardtop .sec::after{background:var(--line)}
html[data-theme="dark"]{
  --bg:#14161a; --panel:#1c1f24; --ink:#eae6df; --muted:#9b948a; --line:#2e3138;
  --accent:#e08a6a; --accent2:#7fb39c; --gold:#d8b45e; --card:#22252b;
  --good:#7ec08e; --bad:#ef8069; --shadow:0 2px 14px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.75;
     -webkit-font-smoothing:antialiased;transition:background .25s,color .25s}
h1,h2,h3,h4{font-family:var(--serif);font-weight:600;letter-spacing:.01em}
button{font-family:inherit;color:inherit}
.wrap{max-width:1080px;margin:0 auto;padding:20px 18px 90px}

/* ---------- 顶栏 ---------- */
header{display:flex;align-items:flex-end;justify-content:space-between;gap:14px;flex-wrap:wrap;
       padding-bottom:14px;border-bottom:1px solid var(--line)}
.brand h1{margin:0;font-size:24px;line-height:1.25}
.brand h1 b{color:var(--accent);font-weight:600}
.brand .sub{font-size:12px;color:var(--muted);margin-top:4px;letter-spacing:.02em}
.hbtns{display:flex;gap:8px;align-items:center}
.pill{background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:7px 13px;
      font-size:12.5px;cursor:pointer;white-space:nowrap;transition:.15s}
.pill:hover{border-color:var(--accent);color:var(--accent)}
.pill.on{background:var(--accent);border-color:var(--accent);color:#fff8f2}
html[data-theme="dark"] .pill.on{color:#1a120c}

/* ---------- 主导航 ---------- */
nav{display:flex;gap:4px;margin:14px 0 0;flex-wrap:wrap;background:var(--panel);
    border:1px solid var(--line);border-radius:14px;padding:4px;box-shadow:var(--shadow)}
nav button{flex:1;min-width:100px;background:transparent;border:0;border-radius:10px;padding:9px 6px;
           font-size:13.5px;cursor:pointer;color:var(--muted);transition:.15s}
nav button .n{font-size:11px;opacity:.7;margin-left:4px}
nav button.on{background:var(--card);color:var(--ink);box-shadow:inset 0 0 0 1px var(--line)}
nav button.on b{color:var(--accent)}

/* ---------- 作品线描图着色 ---------- */
.art{display:block;width:100%;height:100%;overflow:visible}
.art .a{fill:var(--glaze);fill-opacity:.42}
.art .b{fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
.art .c{fill:none;stroke:currentColor;stroke-width:1;opacity:.42}

/* 实物图 / 小幽默 */
.viewswitch{display:flex;gap:7px;margin:4px 0 10px}
.vbtn{background:var(--card);border:1px solid var(--line);border-radius:999px;padding:5px 13px;
  font-size:11.5px;color:var(--muted);cursor:pointer}
.vbtn.on{background:var(--accent);border-color:var(--accent);color:#fff8f2}
html[data-theme="dark"] .vbtn.on,html[data-theme="kitty"] .vbtn.on{color:#20140d}
.mart{position:relative}
.realimg{max-width:100%;max-height:190px;display:block;margin:0 auto;border-radius:12px;object-fit:contain}
.photoempty{text-align:center;font-size:12.5px;color:var(--muted);padding:26px 10px;line-height:1.9}
.photoempty a{color:var(--accent2)}
.photonote{font-size:11px;color:var(--muted);margin-top:8px;line-height:1.7}
.photonote a{color:var(--accent2)}
.pbadge{position:absolute;right:6px;top:6px;background:var(--accent2);color:#fff;border-radius:7px;
  font-size:9px;padding:1px 5px;letter-spacing:.04em}
.wk{position:relative}
.joke{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--gold);
  border-radius:13px;padding:11px 14px;margin-top:10px}
.joke .lb{font-size:10px;padding:1px 8px;border-radius:999px;background:rgba(163,130,44,.16);color:var(--gold)}
.joke .lb.real{background:rgba(92,138,118,.16);color:var(--accent2)}
.joke h4{margin:6px 0 0;font-size:13px}
.joke p{margin:4px 0 0;font-size:12.5px;line-height:1.75}
.joke .punch{font-size:12px;margin-top:6px}
.cardphoto{max-width:100%;max-height:88px;border-radius:9px;margin-top:8px;display:block}
.note .mono{border-color:var(--gold);color:var(--gold);font-size:66px;width:120px;height:120px}
/* ---------- 通用 ---------- */
.view{display:none;padding-top:18px}
.view.on{display:block}
.sec{font-family:var(--serif);font-size:14px;color:var(--muted);letter-spacing:.06em;margin:26px 0 10px;
     display:flex;align-items:center;gap:8px}
.sec::after{content:"";flex:1;height:1px;background:var(--line)}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:18px 20px;box-shadow:var(--shadow)}
.muted{color:var(--muted)}
.tiny{font-size:11.5px;color:var(--muted)}
.btn{background:var(--accent);color:#fff8f2;border:0;border-radius:11px;padding:10px 16px;
     font-size:13.5px;font-weight:600;cursor:pointer;transition:.15s}
.btn:hover{filter:brightness(1.06)}
html[data-theme="dark"] .btn{color:#20140d}
.btn.ghost{background:transparent;color:var(--ink);border:1px solid var(--line);font-weight:400}
.btn.ghost:hover{border-color:var(--accent);color:var(--accent)}
.btn:disabled{opacity:.45;cursor:default}
.chip{display:inline-flex;align-items:center;gap:5px;background:var(--card);border:1px solid var(--line);
      border-radius:999px;padding:4px 10px;font-size:11.5px;color:var(--muted);cursor:pointer;transition:.15s}
.chip:hover{border-color:var(--accent);color:var(--accent)}
.chip.on{background:var(--accent);border-color:var(--accent);color:#fff8f2}
html[data-theme="dark"] .chip.on{color:#20140d}

/* ---------- 主线 ---------- */
.thread{background:linear-gradient(135deg,rgba(180,85,63,.10),rgba(92,138,118,.08));
        border:1px solid rgba(180,85,63,.28);border-radius:18px;padding:20px 22px}
.thread .q{font-family:var(--serif);font-size:20px;line-height:1.5;color:var(--accent)}
.thread .a{font-size:13.5px;margin-top:8px;color:var(--ink)}
.tensions{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin-top:14px}
.ten{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 12px}
.ten b{display:block;font-size:12.5px;color:var(--gold)}
.ten span{font-size:11.5px;color:var(--muted)}
@media(max-width:700px){.tensions{grid-template-columns:1fr}}

/* ---------- 时间线 ---------- */
.tlbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:16px 0 4px}
.tlbar .sp{flex:1}
.search{background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:7px 14px;
  font-size:12.5px;color:var(--ink);font-family:inherit;min-width:220px;outline:none}
.search:focus{border-color:var(--accent)}
.search::placeholder{color:var(--muted)}
.river{position:relative;margin-top:16px;padding-left:44px}
.river::before{content:"";position:absolute;left:16px;top:6px;bottom:6px;width:2px;border-radius:2px;
  background:linear-gradient(180deg,var(--gold),var(--accent) 30%,var(--accent2) 70%,var(--accent2))}
.st{position:relative;margin-bottom:12px}
.st::before{content:"";position:absolute;left:-34px;top:24px;width:12px;height:12px;border-radius:50%;
  background:var(--panel);border:2.5px solid var(--accent);box-shadow:0 0 0 4px var(--bg)}
.st[data-track="china"]::before{border-color:var(--accent2)}
.st.open::before{background:var(--accent)}
.st[data-track="china"].open::before{background:var(--accent2)}
.sthead{width:100%;text-align:left;background:var(--panel);border:1px solid var(--line);border-radius:16px;
  padding:14px 16px;cursor:pointer;box-shadow:var(--shadow);transition:.15s}
.sthead:hover{border-color:var(--accent)}
.st.open .sthead{border-color:var(--accent);border-radius:16px 16px 0 0}
.st[data-track="china"].open .sthead{border-color:var(--accent2);border-radius:16px 16px 0 0}
.row1{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.yr{font-size:11.5px;font-weight:600;letter-spacing:.05em;color:var(--gold);font-variant-numeric:tabular-nums}
.lane{font-size:10px;padding:1px 7px;border-radius:999px;background:rgba(180,85,63,.12);color:var(--accent)}
.st[data-track="china"] .lane{background:rgba(92,138,118,.14);color:var(--accent2)}
.sthead h3{margin:3px 0 0;font-size:18px;line-height:1.35}
.sthead .tag{font-size:12px;color:var(--muted)}
.sthead .hook{font-size:12.5px;color:var(--accent);margin:6px 0 0;font-style:italic}
.thumbs{display:flex;gap:6px;margin-top:9px;flex-wrap:wrap}
.thumbs .tb{width:54px;height:40px;border-radius:7px;background:var(--card);border:1px solid var(--line);
  color:var(--ink);--glaze:#b98d5e;overflow:hidden;display:flex;align-items:center;justify-content:center}
.thumbs .tb svg{width:46px;height:34px}
.stbody{display:none;padding:16px 18px 14px;background:var(--panel);border:1px solid var(--line);border-top:0;border-radius:0 0 16px 16px;box-shadow:var(--shadow)}
.st.open .stbody{display:block}
.blk{margin-top:16px}
.blk .k{font-size:11px;letter-spacing:.08em;color:var(--muted);font-weight:600;margin-bottom:5px}
.blk .k i{font-style:normal;color:var(--accent)}
.blk p{margin:0;font-size:13.5px;line-height:1.85}
.works{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px;margin-top:8px}
.wk{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:10px;cursor:pointer;
  transition:.15s;display:flex;flex-direction:column}
.wk:hover{border-color:var(--accent);transform:translateY(-1px)}
.wk .artbox{height:104px;--glaze:#b98d5e;color:var(--ink);display:flex;align-items:center;justify-content:center;
  background:radial-gradient(circle at 50% 45%,rgba(180,85,63,.06),transparent 70%);border-radius:10px}
.wk .artbox svg{width:100%;height:100%}
.wk .nm{font-size:13px;font-weight:600;margin-top:6px;line-height:1.4}
.wk .mt{font-size:11px;color:var(--muted);margin-top:3px}
.people{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px}
.pp{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:8px 11px;cursor:pointer;
   max-width:100%;transition:.15s}
.pp:hover{border-color:var(--accent2)}
.pp b{font-size:13px}
.pp span{font-size:11px;color:var(--muted);margin-left:6px}
.pp em{display:block;font-style:normal;font-size:11.5px;color:var(--muted);margin-top:2px;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:340px}
.story,.fun{border-radius:14px;padding:13px 15px;margin-top:12px}
.story{background:rgba(92,138,118,.08);border:1px solid rgba(92,138,118,.28)}
.fun{background:rgba(163,130,44,.08);border:1px solid rgba(163,130,44,.28)}
.story .lb,.fun .lb{font-size:10px;padding:1px 8px;border-radius:999px;display:inline-block;margin-bottom:6px}
.story .lb{background:rgba(92,138,118,.16);color:var(--accent2)}
.fun .lb{background:rgba(163,130,44,.16);color:var(--gold)}
.story h4,.fun h4{margin:0;font-size:14px}
.story p,.fun p{margin:6px 0 0;font-size:13px;line-height:1.8}
.punch{font-size:12.5px;color:var(--accent);margin-top:8px;font-style:italic}
.stacts{display:flex;gap:9px;flex-wrap:wrap;margin-top:16px;align-items:center}
.near{font-size:11.5px;color:var(--muted);margin-top:12px;padding-top:10px;border-top:1px dashed var(--line)}
.near a{color:var(--accent2);cursor:pointer;text-decoration:none;border-bottom:1px dotted var(--accent2)}

/* ---------- 卡片模式 ---------- */
.cardtop{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
.dots{display:flex;gap:5px;flex-wrap:wrap}
.dot{width:16px;height:5px;border-radius:3px;background:var(--line)}
.dot.done{background:var(--accent2)}
.dot.now{background:var(--accent);width:26px}
.flipwrap{perspective:1400px;margin:16px auto 0;max-width:560px}
.flip{position:relative;width:100%;height:420px;transition:transform .6s cubic-bezier(.4,.2,.2,1);
  transform-style:preserve-3d;cursor:pointer}
.flip.back{transform:rotateY(180deg)}
.face{position:absolute;inset:0;backface-visibility:hidden;border-radius:20px;border:1px solid var(--line);
  background:var(--panel);box-shadow:var(--shadow);padding:20px;display:flex;flex-direction:column;
  overflow:hidden}
.face.rev{transform:rotateY(180deg)}
.face .top{display:flex;justify-content:space-between;align-items:center;font-size:11px;color:var(--muted)}
.face .artbig{flex:1;display:flex;align-items:center;justify-content:center;--glaze:#b98d5e;
  color:var(--ink)}
.face .artbig svg{width:78%;max-height:210px}
.face .mono{font-family:var(--serif);font-size:88px;line-height:1;width:150px;height:150px;border-radius:50%;
  border:2px solid var(--accent2);color:var(--accent2);display:flex;align-items:center;justify-content:center;
  background:radial-gradient(circle,rgba(92,138,118,.10),transparent 70%)}
.face h3{margin:0;font-size:20px;text-align:center;line-height:1.4}
.face .sm{text-align:center;font-size:12px;color:var(--muted);margin-top:4px}
.face .hintf{text-align:center;font-size:11px;color:var(--muted);margin-top:8px}
.face .kvs{display:grid;grid-template-columns:auto 1fr;gap:5px 12px;font-size:12.5px;margin-top:12px}
.face .kvs b{color:var(--muted);font-weight:400;white-space:nowrap}
.face .why{font-size:13px;line-height:1.8;margin-top:12px;padding-top:10px;border-top:1px dashed var(--line)}
.face .quote{font-family:var(--serif);font-size:13px;color:var(--accent);margin-top:10px;font-style:italic}
.cardbtns{display:flex;gap:9px;justify-content:center;margin-top:16px;flex-wrap:wrap}
.emptyhint{text-align:center;color:var(--muted);font-size:13px;padding:30px 0}

/* ---------- 题库 ---------- */
.banktabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}
.btab{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:7px 13px;font-size:12.5px;
  cursor:pointer}
.btab.on{background:var(--accent);border-color:var(--accent);color:#fff8f2}
html[data-theme="dark"] .btab.on{color:#20140d}
.filters{display:flex;gap:7px;flex-wrap:wrap;align-items:center;margin-bottom:12px}
.filters .lbl{font-size:11px;color:var(--muted);margin-right:2px}
.qcard{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:16px 18px;margin-bottom:12px;
  box-shadow:var(--shadow)}
.qmeta{display:flex;gap:7px;flex-wrap:wrap;align-items:center;font-size:11px;color:var(--muted);margin-bottom:8px}
.qmeta .t{background:var(--card);border:1px solid var(--line);border-radius:999px;padding:1px 8px}
.qmeta .s{color:var(--gold)}
.qt{font-size:14.5px;font-weight:600;line-height:1.7}
.opts{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:11px}
@media(max-width:640px){.opts{grid-template-columns:1fr}}
.opt{display:flex;gap:9px;align-items:flex-start;background:var(--card);border:1.5px solid var(--line);
  border-radius:11px;padding:10px 12px;font-size:13px;cursor:pointer;text-align:left;transition:.15s;line-height:1.6}
.opt:hover:not(:disabled){border-color:var(--accent2)}
.opt .kk{width:20px;height:20px;flex:0 0 20px;border-radius:50%;background:var(--line);color:var(--muted);
  display:flex;align-items:center;justify-content:center;font-size:11px}
.opt.sel{border-color:var(--accent2);background:rgba(92,138,118,.10)}
.opt.right{border-color:var(--good);background:rgba(79,138,95,.12)}
.opt.wrong{border-color:var(--bad);background:rgba(192,73,47,.10)}
.opt:disabled{cursor:default}
.exp{margin-top:11px;background:var(--card);border-radius:11px;padding:10px 12px;font-size:12.5px;line-height:1.75;
  border-left:3px solid var(--accent2)}
.exp b{color:var(--accent2)}
.points{margin:8px 0 0;padding-left:18px;font-size:12.5px;line-height:1.8}
.points li{margin-bottom:3px}
.qacts{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;align-items:center}
.bankfoot{position:sticky;bottom:12px;background:var(--panel);border:1px solid var(--line);border-radius:14px;
  padding:10px 14px;display:flex;justify-content:space-between;align-items:center;gap:10px;
  box-shadow:0 6px 20px rgba(0,0,0,.10);margin-top:14px}
.progressbar{height:6px;background:var(--line);border-radius:3px;overflow:hidden;flex:1;max-width:240px}
.progressbar i{display:block;height:100%;background:var(--accent2);width:0}
.schoolgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px}
.schoolcard{background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:12px 14px;cursor:pointer}
.schoolcard:hover{border-color:var(--accent)}
.schoolcard b{font-size:13.5px}
.schoolcard span{display:block;font-size:11.5px;color:var(--muted);margin-top:4px}
.countbig{font-family:var(--serif);font-size:26px;color:var(--accent)}

/* ---------- 我的 ---------- */
.statgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px}
.statbox{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:12px 14px}
.statbox b{font-family:var(--serif);font-size:24px;display:block;line-height:1.2}
.statbox span{font-size:11.5px;color:var(--muted)}
.bars{margin-top:8px}
.bar{display:grid;grid-template-columns:88px 1fr 44px;gap:9px;align-items:center;font-size:12px;margin:7px 0}
.bar .track{height:8px;background:var(--line);border-radius:4px;overflow:hidden}
.bar .track i{display:block;height:100%;background:linear-gradient(90deg,var(--accent2),var(--accent))}
.bar .num{text-align:right;color:var(--muted);font-variant-numeric:tabular-nums}

/* ---------- 弹层 ---------- */
.mask{position:fixed;inset:0;background:rgba(20,12,6,.55);backdrop-filter:blur(2px);z-index:50;
  display:none;align-items:center;justify-content:center;padding:16px}
.mask.on{display:flex}
.modal{background:var(--panel);border:1px solid var(--line);border-radius:20px;width:100%;max-width:720px;
  max-height:90vh;overflow:auto;padding:22px;box-shadow:0 20px 60px rgba(0,0,0,.3)}
.modal.slim{max-width:560px}
.mhead{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;position:sticky;top:-22px;
  background:var(--panel);padding:4px 0 8px;z-index:2}
.mhead h3{margin:0;font-size:17px;line-height:1.4}
.x{background:transparent;border:0;font-size:24px;line-height:1;color:var(--muted);cursor:pointer;padding:0 4px}
.mart{height:190px;--glaze:#b98d5e;color:var(--ink);display:flex;align-items:center;justify-content:center;
  background:radial-gradient(circle at 50% 45%,rgba(180,85,63,.07),transparent 72%);border-radius:14px;margin:6px 0 12px}
.mart svg{width:70%;height:100%}
.kv{display:grid;grid-template-columns:auto 1fr;gap:6px 14px;font-size:13px}
.kv b{color:var(--muted);font-weight:400;white-space:nowrap}
.qzhead{display:flex;justify-content:space-between;align-items:center;font-size:12px;color:var(--muted);
  margin-bottom:8px}
.qzbar{height:4px;background:var(--line);border-radius:2px;overflow:hidden;margin-bottom:14px}
.qzbar i{display:block;height:100%;background:var(--accent);width:0;transition:width .3s}
.qzq{font-size:17px;font-weight:600;line-height:1.6;margin:4px 0 14px;font-family:var(--serif)}
.qzfoot{display:flex;justify-content:space-between;align-items:center;margin-top:16px;gap:10px;flex-wrap:wrap}
.result{text-align:center;padding:10px 0}
.result .big{font-family:var(--serif);font-size:44px;color:var(--accent);line-height:1.1}
.result .sub{font-size:13px;color:var(--muted);margin-top:6px}
.sheet{display:grid;grid-template-columns:repeat(auto-fill,minmax(34px,1fr));gap:6px;margin-top:12px}
.sheet button{aspect-ratio:1;border-radius:7px;border:1px solid var(--line);background:var(--card);font-size:11px;
  cursor:pointer}
.sheet button.ok{background:rgba(79,138,95,.2);border-color:var(--good)}
.sheet button.no{background:rgba(192,73,47,.18);border-color:var(--bad)}
.sheet button.cur{outline:2px solid var(--accent)}
.toast{position:fixed;left:50%;bottom:26px;transform:translate(-50%,20px);background:var(--ink);color:var(--bg);
  padding:9px 16px;border-radius:999px;font-size:12.5px;opacity:0;pointer-events:none;transition:.25s;z-index:99}
.toast.on{opacity:1;transform:translate(-50%,0)}
footer{margin-top:40px;padding-top:16px;border-top:1px solid var(--line);font-size:11.5px;color:var(--muted);
  line-height:1.9}
@media(max-width:640px){
  .wrap{padding:14px 12px 80px}
  .flip{height:450px}
  .brand h1{font-size:20px}
  .river{padding-left:34px}
  .st::before{left:-27px}
  .river::before{left:12px}
}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand">
      <h1>设计史<b>长河</b></h1>
      <div class="sub">世界线 + 中国线 · 27 站 · 器物 / 人物 / 故事 / 题库</div>
    </div>
    <div class="hbtns">
      <button class="pill" id="themeBtn">夜间</button>
      <button class="pill" id="dailyBtn">每日一练</button>
      <button class="pill" id="quickQuiz">随机 10 题</button>
    </div>
  </header>

  <nav>
    <button class="on" data-view="timeline"><b>时间线</b><span class="n" id="cntStation"></span></button>
    <button data-view="cards"><b>卡片</b><span class="n" id="cntCard"></span></button>
    <button data-view="bank"><b>题库</b><span class="n" id="cntQ"></span></button>
    <button data-view="me"><b>我的</b></button>
  </nav>

  <!-- ============ 时间线 ============ -->
  <section class="view on" id="view-timeline">
    <div class="thread">
      <div class="q" id="threadQ"></div>
      <div class="a" id="threadA"></div>
      <div class="tensions" id="tensions"></div>
    </div>

    <div class="tlbar">
      <button class="chip on" data-track="all">全部并置</button>
      <button class="chip" data-track="world">只看世界</button>
      <button class="chip" data-track="china">只看中国</button>
      <span class="sp"></span>
      <input id="tlSearch" class="search" type="search" placeholder="搜：圈椅 / 汝窑 / 莫里斯 / 包豪斯…">
    </div>
    <div class="tlbar" style="margin-top:8px">
      <span class="tiny">门类</span>
      <button class="chip on" data-topic="all">全部</button>
      <button class="chip" data-topic="中国陶瓷">陶瓷</button>
      <button class="chip" data-topic="中国家具">家具</button>
      <button class="chip" data-topic="中国工艺">青铜·漆·玉</button>
      <button class="chip" data-topic="现代主义">现代主义</button>
      <button class="chip" data-topic="战后与当代">战后与当代</button>
      <span class="sp"></span>
      <span class="tiny" id="tlHint">按年代排序，同一时期中外对照</span>
    </div>
    <div class="river" id="river"></div>
  </section>

  <!-- ============ 卡片 ============ -->
  <section class="view" id="view-cards">
    <div class="panel">
      <div class="cardtop">
        <div>
          <div class="sec" style="margin:0 0 6px">卡片学习 · 每 10 张一组</div>
          <div class="tiny">正面看图与名字，翻面看年代、作者、一句话要点。组末自动进入相关测验。</div>
        </div>
        <div class="hbtns">
          <button class="pill" id="poolAll">全部</button>
          <button class="pill" id="poolChina">中国</button>
          <button class="pill" id="poolWorld">世界</button>
        </div>
      </div>
      <div class="tlbar" style="margin-bottom:0">
        <button class="btn" id="startGroup">开始一组（10 张）</button>
        <span class="tiny" id="cardPoolInfo"></span>
      </div>
    </div>

    <div id="cardStage" style="display:none">
      <div class="cardtop" style="margin-top:16px">
        <div class="dots" id="dots"></div>
        <div class="tiny" id="cardIdx"></div>
      </div>
      <div class="flipwrap">
        <div class="flip" id="flip">
          <div class="face" id="faceFront"></div>
          <div class="face rev" id="faceBack"></div>
        </div>
      </div>
      <div class="cardbtns">
        <button class="btn ghost" id="flipBtn">翻面</button>
        <button class="btn ghost" id="prevCard">上一张</button>
        <button class="btn" id="knowBtn">记住了 →</button>
        <button class="btn ghost" id="againBtn">再看看</button>
      </div>
      <div class="tiny" style="text-align:center;margin-top:10px">空格翻面 · ← → 切换</div>
    </div>
    <div id="cardIdle" class="emptyhint">选一个范围，点「开始一组」。<br>每组 10 张，结束后自动跳到该组相关测验。</div>
  </section>

  <!-- ============ 题库 ============ -->
  <section class="view" id="view-bank">
    <div class="banktabs">
      <button class="btab on" data-bmode="drill">刷题（即时解析）</button>
      <button class="btab" data-bmode="exam">组卷测验（20 题）</button>
      <button class="btab" data-bmode="school">院校高频</button>
      <button class="btab" data-bmode="wrong">错题本</button>
    </div>
    <div class="filters" id="bankFilters"></div>
    <div id="bankBody"></div>
  </section>

  <!-- ============ 我的 ============ -->
  <section class="view" id="view-me">
    <div class="panel">
      <div class="sec" style="margin-top:0">学习概况</div>
      <div class="statgrid" id="statGrid"></div>
      <div class="sec">分章正确率</div>
      <div class="bars" id="topicBars"></div>
      <div class="sec">最近测验</div>
      <div id="historyList"></div>
      <div class="sec">数据</div>
      <div class="hbtns">
        <button class="pill" id="resetAll">清空全部进度</button>
        <span class="tiny">进度存在本机浏览器 localStorage，换设备/清缓存会丢。</span>
      </div>
    </div>
  </section>

  <footer>
    内容以王受之《世界现代设计史》、何人可《工业设计史》、田自秉《中国工艺美术史》、王世襄《明式家具研究》等通行教材为骨架整理；
    图示为手绘线描「形体记号」，不是文物复原图。轶事分「有据」与「记忆画面」两类并已标注。
    题库中的院校标签表示「高频考区」，不是逐字真题。错读一处，请以原书为准。<br>
    主题：简约 / 夜间 / 可爱三态循环，点右上角切换。<br>
    结构参考：Design Is History 的时间线、刷刷题类产品的刷题闭环、中国工艺美术史课程的门类划分；机制照搬，内容与叙事重写。
  </footer>
</div>

<div class="mask" id="mask"><div class="modal" id="modal"></div></div>
<div class="toast" id="toast"></div>

<script id="DATA" type="application/json">__DATA__</script>
<script>
(function(){
"use strict";
const D = JSON.parse(document.getElementById('DATA').textContent);
const S_KEY = 'design_history_river_v1';
const $ = id => document.getElementById(id);
const today = () => new Date().toISOString().slice(0,10);
const esc = s => String(s==null?'':s).replace(/[&<>"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const shuffle = a => { a=a.slice(); for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];} return a; };
const nowISO = () => today();

/* ---------------- 状态 ---------------- */
let S = {right:0,wrong:0,seen:{},wrongIds:[],srs:{},cards:{},lastDay:'',streak:0,
         history:[],topicStat:{},theme:null,group:null};
try{const raw=localStorage.getItem(S_KEY); if(raw) S=Object.assign(S,JSON.parse(raw));}catch(e){}
function save(){ try{ localStorage.setItem(S_KEY, JSON.stringify(S)); }catch(e){} }
function touchDay(){
  const d=today(); if(S.lastDay===d) return;
  const y=new Date(Date.now()-86400000).toISOString().slice(0,10);
  S.streak = (S.lastDay===y) ? (S.streak+1) : 1; S.lastDay=d; save();
}
function toast(msg){ const t=$('toast'); t.textContent=msg; t.classList.add('on'); clearTimeout(t._t); t._t=setTimeout(()=>t.classList.remove('on'),1600); }

/* ---------------- 索引 ---------------- */
const STATIONS = D.stations;
const BY_ID = {}; STATIONS.forEach(s=>BY_ID[s.id]=s);
const CARDS = D.cards, QS = D.bank;
const Q_BY_ID = {}; QS.forEach(q=>Q_BY_ID[q.id]=q);
const TOPICS = [...new Set(QS.map(q=>q.topic))];
const ALL_WORKS = []; STATIONS.forEach(s=> s.works.forEach((w,i)=> ALL_WORKS.push({st:s, w:w, key:s.id+'-w'+i})));
const CARDS_BY_ID={}; CARDS.forEach(c=>CARDS_BY_ID[c.id]=c);

/* ---------------- 顶栏计数 ---------------- */
$('cntStation').textContent = STATIONS.length;
$('cntCard').textContent = CARDS.length;
$('cntQ').textContent = QS.length;
$('threadQ').textContent = D.thread.question;
$('threadA').textContent = D.thread.answer;
$('tensions').innerHTML = D.thread.tensions.map(t=>
  `<div class="ten"><b>${esc(t.name)}</b><span>${esc(t.desc)}</span></div>`).join('');

/* ---------------- 主题 ---------------- */
const THEME_NEXT={light:'dark',dark:'kitty',kitty:'light'};
const THEME_LABEL={light:'夜间',dark:'可爱',kitty:'简约'};
function applyTheme(){
  const sysDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const th = ['light','dark','kitty'].includes(S.theme) ? S.theme : (sysDark ? 'dark' : 'light');
  document.documentElement.dataset.theme = th;
  $('themeBtn').textContent = THEME_LABEL[th];
}
$('themeBtn').onclick = ()=>{
  const cur = document.documentElement.dataset.theme;
  S.theme = THEME_NEXT[cur] || 'light'; save(); applyTheme();
};
applyTheme();

/* ---------------- 视图切换 ---------------- */
document.querySelectorAll('nav button').forEach(b=>{
  b.onclick = ()=>{
    document.querySelectorAll('nav button').forEach(x=>x.classList.remove('on'));
    b.classList.add('on');
    document.querySelectorAll('.view').forEach(v=>v.classList.remove('on'));
    $('view-'+b.dataset.view).classList.add('on');
    try{ history.replaceState(null,'','#'+b.dataset.view); }catch(e){}
    window.scrollTo({top:0,behavior:'smooth'});
    if(b.dataset.view==='me') renderMe();
    if(b.dataset.view==='bank') renderBank();
  };
});
(function(){ const h=(location.hash||'').replace('#','');
  if(h && ['timeline','cards','bank','me'].includes(h)){
    const btn=document.querySelector('[data-view="'+h+'"]'); if(btn) btn.click();
  }})();
function gotoStation(id){
  const st = BY_ID[id]; if(!st) return;
  if(!document.querySelector('[data-view="timeline"]').classList.contains('on')){
    document.querySelector('[data-view="timeline"]').click();
  }
  openId = id; renderTimeline();
  setTimeout(()=>{
    const el = document.querySelector(`.st[data-id="${id}"]`);
    if(el){ el.scrollIntoView({behavior:'smooth',block:'center'}); }
  },60);
}

/* ---------------- 时间线 ---------------- */
let trackFilter='all', openId=null, focusTopic='all', tlQuery='';
(function(){ try{
  const q=new URLSearchParams(location.search).get('open');
  if(q && BY_ID[q]) openId=q;
}catch(e){} })();

function nearestOther(st){
  let best=null, bd=1e9;
  STATIONS.forEach(o=>{ if(o.track===st.track) return;
    const d=Math.abs((o.sort||0)-(st.sort||0));
    if(d<bd){bd=d;best=o;}
  });
  return best;
}

function stationHay(st){
  return [st.era, st.tag, st.year, st.hook,
    ...st.works.map(w=>w.name+' '+(w.author||'')),
    ...st.people.map(p=>p.n+' '+p.r)].join(' ').toLowerCase();
}
function stationDeep(st){
  return [st.background, st.shift, st.story.title, st.story.text, st.fun.title, st.fun.text]
    .join(' ').toLowerCase();
}
function renderTimeline(){
  const base = STATIONS.filter(s=> (trackFilter==='all' || s.track===trackFilter)
      && (focusTopic==='all' || (s.topics||[]).includes(focusTopic)));
  const q = tlQuery.toLowerCase();
  let picked = q ? base.filter(s=> stationHay(s).indexOf(q)>=0) : base.slice();
  if(q && picked.length<3) picked = base.filter(s=> stationHay(s).indexOf(q)>=0 || stationDeep(s).indexOf(q)>=0);
  const list = picked.slice().sort((a,b)=>(a.sort||0)-(b.sort||0));
  $('tlHint').textContent = trackFilter==='all'
    ? `共 ${list.length} 站 · 按年代并置，红点=世界 / 绿点=中国`
    : `共 ${list.length} 站 · ${trackFilter==='world'?'世界线':'中国线'}`;
  if(tlQuery && list.length){
    $('tlHint').textContent = `“${tlQuery}” 命中 ${list.length} 站 · 已展开第一条`;
    if(!list.some(s=>s.id===openId)) openId = list[0].id;
  }
  $('river').innerHTML = list.map(st=>{
    const isOpen = st.id===openId;
    const thumbs = st.works.slice(0,4).map(w=>
      `<div class="tb" style="--glaze:${w.tint||'#b98d5e'}">${w.svg}</div>`).join('');
    const nb = nearestOther(st);
    const near = nb ? `<div class="near">同期另一条线上：<a data-goto="${nb.id}">${esc(nb.era)}（${esc(nb.year)}）</a></div>` : '';
    return `<article class="st ${isOpen?'open':''}" data-id="${st.id}" data-track="${st.track}">
      <button class="sthead" data-open="${st.id}">
        <div class="row1"><span class="yr">${esc(st.year)}</span>
          <span class="lane">${st.track==='world'?'世界':'中国'}</span>
          <span class="tag">${esc(st.tag)}</span></div>
        <h3>${esc(st.era)}</h3>
        <div class="hook">${esc(st.hook)}</div>
        <div class="thumbs">${thumbs}</div>
      </button>
      <div class="stbody">
        <div class="blk"><div class="k">历史背景</div><p>${esc(st.background)}</p></div>
        <div class="blk"><div class="k">代表作品 · 点开看图与要点</div>
          <div class="works">${st.works.map((w,i)=>`
            <div class="wk" data-work="${st.id}-w${i}">
              <div class="artbox" style="--glaze:${w.tint||'#b98d5e'}">${w.svg}${w.photo?'<span class="pbadge">照</span>':''}</div>
              <div class="nm">${esc(w.name)}</div>
              <div class="mt">${esc(w.year)}${w.author?' · '+esc(w.author):''}</div>
            </div>`).join('')}</div></div>
        <div class="blk"><div class="k">人物 · 点开看理念</div>
          <div class="people">${st.people.map((p,i)=>`
            <div class="pp" data-person="${st.id}-p${i}"><b>${esc(p.n)}</b><span>${esc(p.y)}</span>
              <em>${esc(p.r)}</em></div>`).join('')}</div></div>
        <div class="story"><span class="lb">${st.story.kind==='real'?'小故事 · 有据':'小故事 · 记忆画面'}</span>
          <h4>${esc(st.story.title)}</h4><p>${esc(st.story.text)}</p>
          <div class="punch">${esc(st.story.punch)}</div></div>
        <div class="fun"><span class="lb">趣味事件</span>
          <h4>${esc(st.fun.title)}</h4><p>${esc(st.fun.text)}</p></div>
        ${(st.jokes||[]).length?`<div class="blk"><div class="k">笑一下 · 记忆钩子</div>
          ${st.jokes.map(j=>`<div class="joke"><span class="lb ${j.kind==='有据'?'real':''}">${esc(j.kind)}</span>
            <h4>${esc(j.title)}</h4><p>${esc(j.text)}</p><div class="punch">${esc(j.punch)}</div></div>`).join('')}</div>`:''}
        <div class="blk"><div class="k">它留下了什么 · 承上启下</div><p>${esc(st.shift)}</p></div>
        <div class="stacts">
          <button class="btn" data-quiz-stage="${st.id}">做本节测验（${QS.filter(q=>q.stage===st.id).length} 题）</button>
          <button class="btn ghost" data-cards-stage="${st.id}">用本节出卡片</button>
        </div>
        ${near}
      </div>
    </article>`;
  }).join('') || '<div class="emptyhint">没有符合条件的站点</div>';
}
renderTimeline();

$('river').addEventListener('click', e=>{
  const g = e.target.closest('[data-goto]');
  if(g){ gotoStation(g.dataset.goto); return; }
  const q = e.target.closest('[data-quiz-stage]');
  if(q){ const st=BY_ID[q.dataset.quizStage]; startQuiz(QS.filter(x=>x.stage===st.id), {title:'本节测验 · '+st.era}); return; }
  const c = e.target.closest('[data-cards-stage]');
  if(c){ startGroup('stage', c.dataset.cardsStage); return; }
  const w = e.target.closest('[data-work]');
  if(w){ openWork(w.dataset.work); return; }
  const p = e.target.closest('[data-person]');
  if(p){ openPerson(p.dataset.person); return; }
  const h = e.target.closest('[data-open]');
  if(h){ openId = (openId===h.dataset.open) ? null : h.dataset.open; renderTimeline(); }
});
document.querySelectorAll('[data-track]').forEach(b=>{
  b.onclick = ()=>{
    document.querySelectorAll('[data-track]').forEach(x=>x.classList.remove('on'));
    b.classList.add('on'); trackFilter=b.dataset.track; openId=null; renderTimeline();
  };
});
document.querySelectorAll('[data-topic]').forEach(b=>{
  b.onclick = ()=>{
    document.querySelectorAll('[data-topic]').forEach(x=>x.classList.remove('on'));
    b.classList.add('on'); focusTopic=b.dataset.topic; openId=null; renderTimeline();
  };
});
(function(){
  const el=$('tlSearch'); if(!el) return;
  let t=null;
  el.addEventListener('input', ()=>{
    clearTimeout(t);
    t=setTimeout(()=>{ tlQuery=el.value.trim(); openId=null; renderTimeline(); }, 160);
  });
})();

/* ---------------- 作品 / 人物弹层 ---------------- */
function openModal(html, slim){
  $('modal').className = 'modal' + (slim?' slim':'');
  $('modal').innerHTML = html;
  $('mask').classList.add('on');
  $('mask').scrollTop = 0;
}
function closeModal(){ $('mask').classList.remove('on'); }
$('mask').addEventListener('click', e=>{ if(e.target===$('mask')) closeModal(); });
document.addEventListener('keydown', e=>{ if(e.key==='Escape') closeModal(); });

let CUR_WORK=null, photoMode='line';
function renderPhoto(){
  const it=CUR_WORK; if(!it) return;
  const el=$('photoStage'); if(!el) return;
  if(photoMode==='photo' && it.photo){
    el.innerHTML=`<img class="realimg" src="${it.photo}" alt="${esc(it.name)}">`;
  }else if(photoMode==='photo'){
    el.innerHTML=`<div class="photoempty">本机还没有抓到这张作品的授权实物图。<br>
      <a href="${esc(it.photoSearch||'https://commons.wikimedia.org/')}" target="_blank" rel="noopener">维基共享资源（授权清晰）↗</a> ·
      <a href="https://image.baidu.com/search/index?tn=baiduimage&word=${encodeURIComponent(it.name)}" target="_blank" rel="noopener">百度图片（更全，注意版权）↗</a><br>
      线描图可以先认形体，实物图留着联网时再看。</div>`;
  }else{
    el.innerHTML=`<div class="artbig" style="--glaze:${it.tint||'#b98d5e'}">${it.svg}</div>`;
  }
  document.querySelectorAll('[data-pview]').forEach(b=>b.classList.toggle('on', b.dataset.pview===photoMode));
}
window.__showPhoto = m => { photoMode=m; renderPhoto(); };
function openWork(key){
  const w = ALL_WORKS.find(x=>x.key===key); if(!w) return;
  const st = w.st, it = w.w;
  CUR_WORK=it; photoMode=it.photo?'photo':'line';
  const pm=it.photoMeta||{};
  const credit=it.photo
    ? `<div class="photonote">实物图：Wikimedia Commons · ${esc(pm.license||'授权见图源')} · ${esc(pm.author||'作者未标注')}
         ${pm.page?`<a href="${esc(pm.page)}" target="_blank" rel="noopener">原图页 ↗</a>`:''}</div>`
    : `<div class="photonote">图示为手绘线描「形体记号」，不是文物复原图。</div>`;
  openModal(`
    <div class="mhead"><h3>${esc(it.name)}</h3><button class="x" onclick="__close()">×</button></div>
    <div class="viewswitch">
      <button class="vbtn" data-pview="photo" onclick="__showPhoto('photo')">实物照片</button>
      <button class="vbtn" data-pview="line" onclick="__showPhoto('line')">线描示意</button>
    </div>
    <div class="mart" id="photoStage"></div>
    ${credit}
    <div class="kv" style="margin-top:12px">
      <b>年代</b><span>${esc(it.year)}</span>
      <b>作者 / 产地</b><span>${esc(it.author||'—')}</span>
      <b>材料</b><span>${esc(it.mat||'—')}</span>
      <b>所属</b><span>${esc(st.era)} · ${esc(st.year)}</span>
    </div>
    <div class="blk" style="margin-top:14px"><div class="k">为什么重要</div><p>${esc(it.why)}</p></div>
    <div class="qacts" style="margin-top:16px"><button class="btn" onclick="__quizStage('${st.id}')">做本节的 ${QS.filter(q=>q.stage===st.id).length} 题</button></div>
  `);
  renderPhoto();
}
function openPerson(key){
  const st = STATIONS.find(s=> key.indexOf(s.id+'-p')===0);
  if(!st) return;
  const i = Number(key.split('-p')[1]); const p = st.people[i];
  openModal(`
    <div class="mhead"><h3>${esc(p.n)}</h3><button class="x" onclick="__close()">×</button></div>
    <div class="kv"><b>生卒</b><span>${esc(p.y)}</span><b>身份</b><span>${esc(p.r)}</span>
      <b>所处</b><span>${esc(st.era)} · ${esc(st.year)}</span></div>
    <div class="blk" style="margin-top:14px"><div class="k">他的主张 / 为什么记住他</div><p>${esc(p.idea)}</p></div>
    ${p.quote?`<div class="quote" style="font-family:var(--serif);color:var(--accent);font-size:14px;margin-top:12px">“${esc(p.quote)}”</div>`:''}
    <div class="qacts" style="margin-top:16px">
      <button class="btn ghost" onclick="__goto('${st.id}')">回到这一站</button>
      <button class="btn" onclick="__quizStage('${st.id}')">做本节测验</button>
    </div>
  `);
}
window.__close = closeModal;
window.__goto = gotoStation;
window.__quizStage = id => { closeModal(); const st=BY_ID[id]; startQuiz(QS.filter(x=>x.stage===id), {title:'本节测验 · '+st.era}); };

/* ---------------- 卡片模式 ---------------- */
let group = S.group || null;   // {ids:[], i:0, flipped:false, known:{}}
let poolMode = 'all';

function poolCards(mode, stageId){
  if(stageId) return CARDS.filter(c=>c.stage===stageId);
  if(mode==='china') return CARDS.filter(c=>c.track==='china');
  if(mode==='world') return CARDS.filter(c=>c.track==='world');
  return CARDS;
}
function updatePoolInfo(){
  const n = poolCards(poolMode).length;
  $('cardPoolInfo').textContent = `当前范围 ${n} 张可用 · 已看 ${Object.keys(S.cards).length} 张`;
}
['poolAll','poolChina','poolWorld'].forEach(id=>{
  $(id).onclick = ()=>{
    poolMode = id==='poolChina'?'china':(id==='poolWorld'?'world':'all');
    ['poolAll','poolChina','poolWorld'].forEach(x=>$(x).classList.remove('on'));
    $(id).classList.add('on'); updatePoolInfo();
  };
});
$('poolAll').classList.add('on');

function startGroup(mode, stageId){
  const pool = poolCards(stageId?null:poolMode, stageId);
  if(pool.length<4){ toast('这个范围的卡片太少'); return; }
  // 未看过的优先
  const unseen = pool.filter(c=>!S.cards[c.id]);
  const seen = pool.filter(c=>S.cards[c.id]);
  const pick = shuffle(unseen).concat(shuffle(seen)).slice(0,10);
  group = {ids: pick.map(c=>c.id), i:0, flipped:false, known:{}, mode: stageId?('stage:'+stageId):poolMode};
  S.group = group; save();
  $('cardIdle').style.display='none';
  $('cardStage').style.display='block';
  document.querySelector('[data-view="cards"]').click();
  renderCard();
}
$('startGroup').onclick = ()=> startGroup();

function renderCard(){
  if(!group){ return; }
  const c = CARDS_BY_ID[group.ids[group.i]];
  if(!c){ return; }
  $('dots').innerHTML = group.ids.map((_,i)=>
    `<div class="dot ${i<group.i?'done':''} ${i===group.i?'now':''}"></div>`).join('');
  const kindLabel = c.type==='work'?'作品':(c.type==='person'?'人物':(c.noteKind||'卡片'));
  $('cardIdx').textContent = `${group.i+1} / ${group.ids.length} · ${kindLabel} · ${c.stationTitle}`;
  const art = c.type==='work'
    ? `<div class="artbig" style="--glaze:${c.tint||'#b98d5e'}">${c.svg}${c.photo?`<img class="cardphoto" src="${c.photo}" alt="">`:''}</div>`
    : `<div class="artbig ${c.type==='note'?'note':''}"><div class="mono">${esc(c.initial)}</div></div>`;
  $('faceFront').innerHTML = `
    <div class="top"><span>${c.track==='china'?'中国线':'世界线'}</span><span>${esc(c.year||'')}</span></div>
    ${art}
    <h3>${esc(c.title)}</h3>
    <div class="sm">${esc(c.sub||'')}</div>
    <div class="hintf">点卡片翻面 →</div>`;
  const kvs = (c.meta||[]).map(([k,v])=>`<b>${esc(k)}</b><span>${esc(v)}</span>`).join('');
  $('faceBack').innerHTML = `
    <div class="top"><span>${kindLabel}</span><span>${esc(c.stationTitle)}</span></div>
    <h3 style="text-align:left;margin-top:8px;font-size:18px">${esc(c.title)}</h3>
    <div class="kvs">${kvs}</div>
    <div class="why">${esc(c.why)}</div>
    ${c.punch?`<div class="quote">${esc(c.punch)}</div>`:''}
    ${c.quote?`<div class="quote">“${esc(c.quote)}”</div>`:''}
    ${c.type==='work'&&c.photo?`<img class="cardphoto" src="${c.photo}" alt="${esc(c.title)}">`:''}
    <div class="hintf" style="margin-top:auto">记住关键点，就够了 —— 细节交给时间线。</div>`;
  $('flip').classList.toggle('back', !!group.flipped);
  updatePoolInfo();
}
$('flip').onclick = ()=>{ if(!group) return; group.flipped=!group.flipped; S.group=group; save(); $('flip').classList.toggle('back', group.flipped); };
$('flipBtn').onclick = ()=> $('flip').click();
$('prevCard').onclick = ()=>{ if(!group||group.i===0) return; group.i--; group.flipped=false; save(); renderCard(); };
function cardNext(known){
  if(!group) return;
  const id = group.ids[group.i];
  const rec = S.cards[id] || {seen:0,known:0};
  rec.seen++; if(known) rec.known++;
  S.cards[id]=rec;
  group.known[id]=!!known;
  if(group.i < group.ids.length-1){
    group.i++; group.flipped=false; save(); renderCard();
  }else{
    save(); finishGroup();
  }
}
$('knowBtn').onclick = ()=> cardNext(true);
$('againBtn').onclick = ()=> cardNext(false);

function finishGroup(){
  const ids = group.ids;
  const cards = ids.map(id=>CARDS_BY_ID[id]).filter(Boolean);
  const topics = [...new Set(cards.map(c=>c.topic).filter(Boolean))];
  const stages = [...new Set(cards.map(c=>c.stage))];
  let pool = QS.filter(q=> topics.includes(q.topic) || stages.includes(q.stage));
  if(pool.length<5) pool = QS.slice();
  const pick = shuffle(pool).slice(0,5);
  const knownN = Object.values(group.known).filter(Boolean).length;
  const title = `本组测验 · ${knownN}/${ids.length} 张已记住`;
  $('cardStage').style.display='none';
  startQuiz(pick, {title:title, after:()=>{
    group = null; S.group=null; save();
    $('cardIdle').style.display='block';
    $('cardIdle').innerHTML = '这一组完成了。可以「开始一组」继续，或者去题库按章节刷。';
  }, groupSummary:true});
}

/* ---------------- 答题引擎 ---------------- */
const QZ = {list:[], i:0, mode:'instant', ans:{}, title:'', after:null, examSubmitted:false};

function startQuiz(list, opt){
  opt = opt||{};
  if(!list || !list.length){ toast('这里暂时没有题目'); return; }
  QZ.list = list.slice(); QZ.i=0; QZ.ans={}; QZ.mode='instant';
  QZ.title = opt.title || '练习'; QZ.after = opt.after||null; QZ.examSubmitted=false;
  renderQuiz();
  $('mask').classList.add('on');
}
function renderQuiz(){
  const q = QZ.list[QZ.i];
  if(!q){ quizDone(); return; }
  const isTerm = q.type==='term' || q.type==='short';
  const progress = (QZ.i)/QZ.list.length*100;
  let optsHtml='';
  if(!isTerm){
    const keys=['A','B','C','D','E'];
    optsHtml = `<div class="opts">${q.options.map((o,k)=>
      `<button class="opt" data-opt="${k}"><span class="kk">${keys[k]}</span><span>${esc(o)}</span></button>`).join('')}</div>`;
  }
  $('modal').className='modal';
  $('modal').innerHTML = `
    <div class="mhead"><h3>${esc(QZ.title)}</h3><button class="x" onclick="__close()">×</button></div>
    <div class="qzhead"><span>第 ${QZ.i+1} / ${QZ.list.length} 题</span><span>${esc(q.topic)} · ${typeName(q.type)}</span></div>
    <div class="qzbar"><i style="width:${progress}%"></i></div>
    <div class="qzq">${esc(q.q)}</div>
    ${isTerm?`<div class="tiny">先自己在心里（或纸上）答一遍，再点「看评分要点」。</div>`:''}
    ${optsHtml}
    <div id="qfeed"></div>
    <div class="qzfoot">
      <span class="tiny">${(q.schools&&q.schools.length)?('高频考区：'+q.schools.join(' / ')):''}</span>
      <div class="hbtns">
        ${isTerm?`<button class="btn ghost" id="showPoints">看评分要点</button>
                  <button class="btn ghost" id="selfBad">没答上</button>
                  <button class="btn" id="selfGood">答对了</button>`
                :`<button class="btn" id="nextQ" style="display:none">下一题 →</button>`}
      </div>
    </div>`;
  if(!isTerm){
    $('modal').querySelectorAll('[data-opt]').forEach(b=> b.onclick=()=> answerOne(Number(b.dataset.opt)));
  }else{
    $('showPoints').onclick = ()=>{
      $('qfeed').innerHTML = `<div class="exp"><b>评分要点</b><ol class="points">${(q.points||[]).map(p=>`<li>${esc(p)}</li>`).join('')}</ol>
        <div style="margin-top:8px">${esc(q.answer||'')}</div></div>`;
    };
    $('selfGood').onclick = ()=> gradeTerm(true);
    $('selfBad').onclick = ()=> gradeTerm(false);
  }
}
function typeName(t){ return {single:'单选',multi:'多选',judge:'判断',term:'名词解释',short:'简答'}[t]||t; }

function answerOne(k){
  const q = QZ.list[QZ.i];
  const multi = q.type==='multi';
  if(multi){
    // 多选：先记录选择，点「提交」判定
    if(!QZ.ans[q.id]) QZ.ans[q.id]=[];
    const arr = QZ.ans[q.id];
    const idx = arr.indexOf(k);
    if(idx>=0) arr.splice(idx,1); else arr.push(k);
    $('modal').querySelectorAll('[data-opt]').forEach(b=>{
      b.classList.toggle('sel', arr.includes(Number(b.dataset.opt)));
    });
    if(!$('submitMulti')){
      const btn = document.createElement('button');
      btn.className='btn'; btn.id='submitMulti'; btn.textContent='提交答案';
      btn.style.marginTop='10px';
      btn.onclick = ()=> gradeMulti();
      $('qfeed').appendChild(btn);
    }
    return;
  }
  if(QZ.ans[q.id]!==undefined) return;
  QZ.ans[q.id]=k;
  const ok = k===q.answer;
  $('modal').querySelectorAll('[data-opt]').forEach((b,i)=>{
    b.disabled=true;
    if(i===q.answer) b.classList.add('right');
    if(i===k && !ok) b.classList.add('wrong');
  });
  record(q, ok);
  showExplain(q, ok);
  $('nextQ').style.display='inline-block';
  $('nextQ').onclick = ()=>{ QZ.i++; renderQuiz(); };
}
function gradeMulti(){
  const q = QZ.list[QZ.i];
  const arr = (QZ.ans[q.id]||[]).slice().sort();
  const tgt = q.answer.slice().sort();
  if(!arr.length){ toast('先选至少一项'); return; }
  if(QZ.ans[q.id+'_done']) return;
  QZ.ans[q.id+'_done']=true;
  const ok = arr.length===tgt.length && arr.every((v,i)=>v===tgt[i]);
  $('modal').querySelectorAll('[data-opt]').forEach((b,i)=>{
    b.disabled=true; b.classList.remove('sel');
    if(tgt.includes(i)) b.classList.add('right');
    if(arr.includes(i) && !tgt.includes(i)) b.classList.add('wrong');
  });
  $('submitMulti').disabled=true;
  record(q, ok); showExplain(q, ok);
  const nb=document.createElement('button'); nb.className='btn'; nb.style.marginTop='12px';
  nb.textContent='下一题 →'; nb.onclick=()=>{ QZ.i++; renderQuiz(); };
  $('qfeed').appendChild(nb);
}
function showExplain(q, ok){
  $('qfeed').innerHTML = `<div class="exp" style="border-left-color:${ok?'var(--good)':'var(--bad)'}">
    <b>${ok?'答对了':'再想一步'}</b> · ${esc(q.explain||'')}
    ${(q.schools&&q.schools.length)?`<div class="tiny" style="margin-top:6px">高频考区：${q.schools.join(' / ')} · 出处：${esc(q.src||'教材')}</div>`:''}
    </div>` + (q.type==='multi'?'':'');
}
function gradeTerm(ok){
  const q = QZ.list[QZ.i];
  if(QZ.ans[q.id]!==undefined) return;
  QZ.ans[q.id]=ok;
  record(q, ok);
  $('qfeed').innerHTML = `<div class="exp" style="border-left-color:${ok?'var(--good)':'var(--bad)'}">
    <b>${ok?'很好':'把这几条记住就够'}</b>
    <ol class="points">${(q.points||[]).map(p=>`<li>${esc(p)}</li>`).join('')}</ol>
    <div style="margin-top:8px">${esc(q.answer||'')}</div></div>`;
  const nb=document.createElement('button'); nb.className='btn'; nb.style.marginTop='12px';
  nb.textContent='下一题 →'; nb.onclick=()=>{ QZ.i++; renderQuiz(); };
  $('qfeed').appendChild(nb);
  $('showPoints').style.display='none'; $('selfGood').style.display='none'; $('selfBad').style.display='none';
}
function record(q, ok){
  S.seen[q.id]=(S.seen[q.id]||0)+1;
  const ts = S.topicStat[q.topic] || {r:0,w:0};
  if(ok){ S.right++; ts.r++; S.wrongIds=S.wrongIds.filter(x=>x!==q.id);
    if(!S.srs[q.id]) S.srs[q.id]={step:0};
    S.srs[q.id].step=Math.min(6,(S.srs[q.id].step||0)+1);
    S.srs[q.id].due=new Date(Date.now()+[1,2,4,7,15,30][S.srs[q.id].step-1]*86400000).toISOString().slice(0,10);
  }else{ S.wrong++; ts.w++; if(!S.wrongIds.includes(q.id)) S.wrongIds.push(q.id);
    S.srs[q.id]={step:0,due:today()};
  }
  S.topicStat[q.topic]=ts;
  touchDay(); save();
}
function quizDone(){
  const total = QZ.list.length;
  const correct = QZ.list.filter(q=>{
    if(q.type==='term'||q.type==='short') return QZ.ans[q.id]===true;
    if(q.type==='multi'){ const a=(QZ.ans[q.id]||[]).slice().sort(), t=q.answer.slice().sort();
      return a.length===t.length && a.every((v,i)=>v===t[i]); }
    return QZ.ans[q.id]===q.answer;
  }).length;
  const rate = Math.round(correct/total*100);
  S.history.push({date:today(),score:correct,total:total,rate:rate});
  if(S.history.length>40) S.history=S.history.slice(-40);
  save();
  $('modal').className='modal slim';
  $('modal').innerHTML = `
    <div class="mhead"><h3>${esc(QZ.title)}</h3><button class="x" onclick="__close()">×</button></div>
    <div class="result"><div class="big">${correct} / ${total}</div>
      <div class="sub">正确率 ${rate}% · ${rate>=80?'这一组掌握得不错':(rate>=50?'有一半需要回看':'先回时间线读一遍再来')}</div></div>
    <div class="sheet">${QZ.list.map((q,i)=>{
      const ok = q.type==='term'||q.type==='short' ? QZ.ans[q.id]===true
        : (q.type==='multi' ? (()=>{const a=(QZ.ans[q.id]||[]).slice().sort(),t=q.answer.slice().sort();return a.length===t.length&&a.every((v,j)=>v===t[j]);})()
        : QZ.ans[q.id]===q.answer);
      return `<button class="${ok?'ok':'no'}" title="${esc(q.q)}">${i+1}</button>`;
    }).join('')}</div>
    <div class="qzfoot">
      <button class="btn ghost" id="redoWrong">只重做错题</button>
      <button class="btn" id="finishQ">完成</button>
    </div>`;
  $('finishQ').onclick = ()=>{
    closeModal();
    if(QZ.after) QZ.after();
    if(document.querySelector('[data-view="me"]').classList.contains('on')) renderMe();
  };
  $('redoWrong').onclick = ()=>{
    const wrong = QZ.list.filter((q,i)=> {
      const ok = q.type==='term'||q.type==='short' ? QZ.ans[q.id]===true : (q.type==='multi'? false : QZ.ans[q.id]===q.answer);
      return !ok;
    });
    if(!wrong.length){ toast('没有错题'); return; }
    startQuiz(wrong,{title:'重做错题'});
  };
}

/* ---------------- 题库 ---------------- */
let bMode='drill', bTopic='all', bType='all', bSchool='all';
let drillList=[], drillIdx=0, drillAnswered=false;
let examList=[], examAns={};

function renderFilters(){
  const types = [['all','全部题型'],['single','单选'],['multi','多选'],['judge','判断'],['term','名词解释'],['short','简答']];
  const schools = [...new Set(QS.flatMap(q=>q.schools||[]))].sort();
  $('bankFilters').innerHTML = `
    <span class="lbl">章节</span>
    <button class="chip ${bTopic==='all'?'on':''}" data-ftopic="all">全部</button>
    ${TOPICS.map(t=>`<button class="chip ${bTopic===t?'on':''}" data-ftopic="${esc(t)}">${esc(t)}</button>`).join('')}
    <span class="lbl" style="margin-left:8px">题型</span>
    ${types.map(([v,n])=>`<button class="chip ${bType===v?'on':''}" data-ftype="${v}">${n}</button>`).join('')}
    <span class="lbl" style="margin-left:8px">院校</span>
    <select id="schoolSel" style="background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:5px 8px;font-size:12px;color:var(--ink)">
      <option value="all">全部</option>
      ${schools.map(s=>`<option value="${esc(s)}" ${bSchool===s?'selected':''}>${esc(s)}</option>`).join('')}
    </select>`;
  $('bankFilters').querySelectorAll('[data-ftopic]').forEach(b=>b.onclick=()=>{bTopic=b.dataset.ftopic;renderBank();});
  $('bankFilters').querySelectorAll('[data-ftype]').forEach(b=>b.onclick=()=>{bType=b.dataset.ftype;renderBank();});
  const sel=$('schoolSel'); if(sel) sel.onchange=()=>{ bSchool=sel.value; renderBank(); };
}
function filtered(){
  return QS.filter(q=>
    (bTopic==='all'||q.topic===bTopic) &&
    (bType==='all'||q.type===bType) &&
    (bSchool==='all'||(q.schools||[]).includes(bSchool)));
}
function renderBank(){
  renderFilters();
  const body=$('bankBody');
  if(bMode==='drill') return renderDrill(body);
  if(bMode==='exam') return renderExam(body);
  if(bMode==='school') return renderSchool(body);
  if(bMode==='wrong') return renderWrong(body);
}
document.querySelectorAll('[data-bmode]').forEach(b=>{
  b.onclick=()=>{
    document.querySelectorAll('[data-bmode]').forEach(x=>x.classList.remove('on'));
    b.classList.add('on'); bMode=b.dataset.bmode;
    if(bMode==='drill'){ drillList=shuffle(filtered()); drillIdx=0; drillAnswered=false; }
    if(bMode==='exam'){ examList=[]; examAns={}; }
    renderBank();
  };
});

function renderDrill(body){
  if(!drillList.length){ drillList=shuffle(filtered()); drillIdx=0; drillAnswered=false; }
  const list = filtered();
  if(!list.length){ body.innerHTML='<div class="emptyhint">这个筛选下没有题目，换一个条件。</div>'; return; }
  if(!list.includes(drillList[drillIdx])){ drillList=list.slice(); drillIdx=0; drillAnswered=false; }
  const q = drillList[drillIdx] || list[0];
  const isTerm = q.type==='term'||q.type==='short';
  const done = Object.keys(S.seen).length;
  body.innerHTML = `
    <div class="bankfoot" style="margin:0 0 14px">
      <span class="tiny">已做 ${done} / ${QS.length} 题 · 错题 ${S.wrongIds.length} 道</span>
      <div class="progressbar"><i style="width:${Math.min(100,done/QS.length*100)}%"></i></div>
      <button class="btn ghost" id="shuffleDrill">换一批顺序</button>
    </div>
    <div class="qcard" id="drillCard">
      <div class="qmeta"><span class="t">${esc(q.topic)}</span><span class="t">${typeName(q.type)}</span>
        ${(q.schools||[]).length?`<span class="s">高频：${q.schools.join(' / ')}</span>`:''}
        <span>第 ${drillIdx+1} / ${list.length}</span></div>
      <div class="qt">${esc(q.q)}</div>
      ${isTerm?'':`<div class="opts">${q.options.map((o,k)=>
        `<button class="opt" data-dopt="${k}"><span class="kk">${'ABCDE'[k]}</span><span>${esc(o)}</span></button>`).join('')}</div>`}
      <div id="dfeed"></div>
      <div class="qacts">
        ${isTerm?`<button class="btn ghost" id="dPoints">看评分要点</button>
                  <button class="btn ghost" id="dBad">没答上</button>
                  <button class="btn" id="dGood">答对了</button>`
                :`<button class="btn ghost" id="dNext">下一题 →</button>`}
        <button class="btn ghost" id="dPrev">← 上一题</button>
      </div>
    </div>`;
  if(!isTerm){
    body.querySelectorAll('[data-dopt]').forEach(b=> b.onclick=()=>{
      if(drillAnswered) return; drillAnswered=true;
      const k=Number(b.dataset.dopt);
      const multi = q.type==='multi';
      let ok;
      if(multi){ ok=false; }
      else{
        ok = k===q.answer;
        body.querySelectorAll('[data-dopt]').forEach((x,i)=>{
          x.disabled=true;
          if(i===q.answer) x.classList.add('right');
          if(i===k && !ok) x.classList.add('wrong');
        });
      }
      record(q, ok);
      $('dfeed').innerHTML = `<div class="exp" style="border-left-color:${ok?'var(--good)':'var(--bad)'}">
        <b>${ok?'答对了':'正确答案：'+'ABCDE'[q.answer]}</b> · ${esc(q.explain||'')}</div>`;
    });
  }else{
    $('dPoints').onclick=()=>{ $('dfeed').innerHTML=`<div class="exp"><b>评分要点</b>
      <ol class="points">${(q.points||[]).map(p=>`<li>${esc(p)}</li>`).join('')}</ol>
      <div style="margin-top:8px">${esc(q.answer||'')}</div></div>`; };
    $('dGood').onclick=()=>{ record(q,true); drillAnswered=true;
      $('dfeed').innerHTML=`<div class="exp" style="border-left-color:var(--good)"><b>记下了</b><ol class="points">${(q.points||[]).map(p=>`<li>${esc(p)}</li>`).join('')}</ol></div>`; };
    $('dBad').onclick=()=>{ record(q,false); drillAnswered=true;
      $('dfeed').innerHTML=`<div class="exp" style="border-left-color:var(--bad)"><b>这几条再读一遍</b><ol class="points">${(q.points||[]).map(p=>`<li>${esc(p)}</li>`).join('')}</ol></div>`; };
  }
  $('dNext').onclick=()=>{ drillIdx=(drillIdx+1)%list.length; drillAnswered=false; renderBank(); };
  $('dPrev').onclick=()=>{ drillIdx=(drillIdx-1+list.length)%list.length; drillAnswered=false; renderBank(); };
  $('shuffleDrill').onclick=()=>{ drillList=shuffle(list); drillIdx=0; drillAnswered=false; renderBank(); };
}

function renderExam(body){
  if(!examList.length){
    const pool = filtered().filter(q=>q.type!=='term'&&q.type!=='short');
    body.innerHTML = `
      <div class="panel">
        <div class="sec" style="margin-top:0">组卷测验</div>
        <p style="font-size:13px;margin:0 0 10px">按当前筛选条件（${esc(bTopic==='all'?'全部章节':bTopic)} / ${esc(bType==='all'?'全部客观题':typeName(bType))}）从 ${pool.length} 道客观题中随机抽 <b>20</b> 道，一次性作答、交卷后统一批改。</p>
        <button class="btn" id="makeExam">生成试卷</button>
        <span class="tiny" style="margin-left:8px">客观题不足 20 道时按实际数量出卷</span>
      </div>`;
    $('makeExam').onclick=()=>{
      examList = shuffle(pool).slice(0,Math.min(20,pool.length));
      examAns = {}; renderBank();
    };
    return;
  }
  const n=examList.length;
  body.innerHTML = `
    <div class="qcard">
      <div class="qmeta"><span class="t">${n} 题</span><span>交卷后统一批改</span></div>
      ${examList.map((q,i)=>`
        <div class="qblock" data-qi="${i}" style="padding:12px 0;border-bottom:1px dashed var(--line)">
          <div class="qt" style="font-size:14px">${i+1}. ${esc(q.q)}</div>
          <div class="opts">${q.options.map((o,k)=>
            `<button class="opt" data-ei="${i}" data-ek="${k}"><span class="kk">${'ABCDE'[k]}</span><span>${esc(o)}</span></button>`).join('')}</div>
        </div>`).join('')}
      <div class="qacts" style="margin-top:14px">
        <button class="btn" id="submitExam">交卷</button>
        <button class="btn ghost" id="abortExam">放弃</button>
        <span class="tiny" id="examCount">已答 0 / ${n}</span>
      </div>
    </div>`;
  body.querySelectorAll('[data-ei]').forEach(b=> b.onclick=()=>{
    const i=Number(b.dataset.ei), k=Number(b.dataset.ek), q=examList[i];
    if(q.type==='multi'){
      const a=examAns[i]||[]; const p=a.indexOf(k);
      if(p>=0) a.splice(p,1); else a.push(k);
      examAns[i]=a;
    }else{ examAns[i]=k; }
    const blk = body.querySelector(`.qblock[data-qi="${i}"]`);
    blk.querySelectorAll('[data-ek]').forEach(x=>{
      const kk=Number(x.dataset.ek);
      const sel = q.type==='multi' ? (examAns[i]||[]).includes(kk) : examAns[i]===kk;
      x.classList.toggle('sel', sel);
    });
    $('examCount').textContent = `已答 ${Object.keys(examAns).length} / ${n}`;
  });
  $('abortExam').onclick=()=>{ examList=[]; examAns={}; renderBank(); };
  $('submitExam').onclick=()=>{
    if(Object.keys(examAns).length<n && !confirm('还有题没答，确定交卷？')) return;
    let correct=0;
    examList.forEach((q,i)=>{
      const a=examAns[i];
      const ok = q.type==='multi'
        ? (Array.isArray(a) && a.slice().sort().join()===q.answer.slice().sort().join())
        : a===q.answer;
      if(ok) correct++; else record(q,false);
      if(ok) record(q,true);
    });
    S.history.push({date:today(),score:correct,total:n,rate:Math.round(correct/n*100)});
    if(S.history.length>40) S.history=S.history.slice(-40);
    save();
    $('modal').className='modal';
    $('modal').innerHTML=`
      <div class="mhead"><h3>测验结果</h3><button class="x" onclick="__close()">×</button></div>
      <div class="result"><div class="big">${correct} / ${n}</div>
        <div class="sub">正确率 ${Math.round(correct/n*100)}%</div></div>
      <div class="sheet">${examList.map((q,i)=>{
        const a=examAns[i];
        const ok = q.type==='multi' ? (Array.isArray(a)&&a.slice().sort().join()===q.answer.slice().sort().join()) : a===q.answer;
        return `<button class="${ok?'ok':'no'}">${i+1}</button>`;
      }).join('')}</div>
      <div class="sec">逐题解析</div>
      <div style="max-height:40vh;overflow:auto">
        ${examList.map((q,i)=>`<div style="font-size:12.5px;line-height:1.7;margin-bottom:10px">
          <b>${i+1}. ${esc(q.q)}</b><br>
          <span class="muted">正确答案：${q.type==='multi'?q.answer.map(k=>'ABCDE'[k]).join(''):'ABCDE'[q.answer]}</span><br>
          ${esc(q.explain||'')}</div>`).join('')}
      </div>
      <div class="qzfoot"><span class="tiny">错题已进入错题本</span><button class="btn" id="examDone">完成</button></div>`;
    $('examDone').onclick=()=>{ closeModal(); examList=[]; examAns={}; renderBank(); };
  };
}

function renderSchool(body){
  const schools = {};
  QS.forEach(q=> (q.schools||[]).forEach(s=>{
    schools[s]=schools[s]||{n:0,topics:{}};
    schools[s].n++; schools[s].topics[q.topic]=(schools[s].topics[q.topic]||0)+1;
  }));
  const arr = Object.entries(schools).sort((a,b)=>b[1].n-a[1].n);
  body.innerHTML = `
    <div class="panel" style="margin-bottom:14px">
      <div class="sec" style="margin-top:0">院校高频考区</div>
      <p style="font-size:12.5px;margin:0;color:var(--muted);line-height:1.8">
        按公开考纲与回忆版整理的「高频考区」，用于判断某个院校更常考哪一类题；
        <b>不是逐字真题</b>，也不标虚构年份。点开可按该院校筛题练习。</p>
    </div>
    <div class="schoolgrid">
      ${arr.map(([s,v])=>{
        const top = Object.entries(v.topics).sort((a,b)=>b[1]-a[1])[0];
        return `<div class="schoolcard" data-school="${esc(s)}">
          <b>${esc(s)}</b><span>高频 ${v.n} 个考点 · 侧重 ${esc(top[0])}</span></div>`;
      }).join('')}
    </div>
    <div class="sec">说明</div>
    <div class="tiny">院校标签依据的是这些考点在公开教材、考纲与考研回忆版中的重复出现频次，用于复习排序，不能当作某年某校的原题引用。</div>`;
  body.querySelectorAll('[data-school]').forEach(el=> el.onclick=()=>{
    bSchool = el.dataset.school; bTopic='all'; bType='all';
    bMode='drill'; drillList=[]; drillIdx=0; drillAnswered=false;
    document.querySelectorAll('[data-bmode]').forEach(x=>x.classList.toggle('on', x.dataset.bmode==='drill'));
    renderBank();
  });
}

function renderWrong(body){
  const list = S.wrongIds.map(id=>Q_BY_ID[id]).filter(Boolean);
  if(!list.length){ body.innerHTML='<div class="emptyhint">还没有错题。去刷题或做一组卡片测验吧。</div>'; return; }
  body.innerHTML = `
    <div class="panel" style="margin-bottom:14px">
      <div class="sec" style="margin-top:0">错题本 · ${list.length} 道</div>
      <div class="hbtns">
        <button class="btn" id="redoAllWrong">全部重做</button>
        <button class="btn ghost" id="clearWrong">清空错题本</button>
      </div>
    </div>
    ${list.map(q=>`<div class="qcard">
      <div class="qmeta"><span class="t">${esc(q.topic)}</span><span class="t">${typeName(q.type)}</span>
        <span>${(q.schools||[]).join(' / ')}</span></div>
      <div class="qt">${esc(q.q)}</div>
      <div class="exp" style="margin-top:10px"><b>要点</b> ${esc(q.type==='term'||q.type==='short' ? (q.points||[]).join('；') : q.explain)}</div>
    </div>`).join('')}`;
  $('redoAllWrong').onclick=()=> startQuiz(list,{title:'错题重做'});
  $('clearWrong').onclick=()=>{ if(confirm('清空错题本？已做的统计不会删。')){ S.wrongIds=[]; save(); renderBank(); } };
}

/* 顶部随机 10 题 */
$('quickQuiz').onclick=()=> startQuiz(shuffle(QS).slice(0,10), {title:'随机 10 题'});

/* 每日一练：错题到期 > 薄弱章节 > 没做过的 */
$('dailyBtn').onclick=()=>{
  const due = S.wrongIds.map(id=>Q_BY_ID[id]).filter(q=>q && (!S.srs[q.id] || (S.srs[q.id].due||'')<=today()));
  const weakTopics = Object.entries(S.topicStat)
    .map(([t,v])=>({t, n:v.r+v.w, rate:(v.r+v.w)?v.r/(v.r+v.w):1}))
    .filter(x=>x.n>=2).sort((a,b)=>a.rate-b.rate).slice(0,2).map(x=>x.t);
  const weak = QS.filter(q=>weakTopics.includes(q.topic) && !due.includes(q));
  const fresh = QS.filter(q=>!S.seen[q.id] && !due.includes(q) && !weak.includes(q));
  const pick = [...shuffle(due), ...shuffle(weak), ...shuffle(fresh)].slice(0,10);
  startQuiz(pick.length?pick:shuffle(QS).slice(0,10), {title:'每日一练 · 10 题'});
};

/* ---------------- 我的 ---------------- */
function renderMe(){
  const done = Object.keys(S.seen).length;
  const total = S.right+S.wrong;
  const rate = total? Math.round(S.right/total*100):0;
  const cardSeen = Object.keys(S.cards).length;
  let cardKnown=0; Object.values(S.cards).forEach(c=>{ if(c.known>0) cardKnown++; });
  $('statGrid').innerHTML=`
    <div class="statbox"><b>${total}</b><span>累计答题</span></div>
    <div class="statbox"><b>${rate}%</b><span>总正确率</span></div>
    <div class="statbox"><b>${done}/${QS.length}</b><span>题库覆盖</span></div>
    <div class="statbox"><b>${cardSeen}/${CARDS.length}</b><span>卡片已看</span></div>
    <div class="statbox"><b>${S.streak}</b><span>连续天数</span></div>`;
  const bars = TOPICS.map(t=>{
    const st=S.topicStat[t]||{r:0,w:0}; const n=st.r+st.w;
    const pct=n?Math.round(st.r/n*100):0;
    return `<div class="bar"><span>${esc(t)}</span><div class="track"><i style="width:${pct}%"></i></div><span class="num">${n?pct+'%':'—'}</span></div>`;
  }).join('');
  $('topicBars').innerHTML = bars;
  const hs = S.history.slice().reverse().slice(0,8);
  $('historyList').innerHTML = hs.length? hs.map(h=>
    `<div class="bar"><span>${h.date}</span><div class="track"><i style="width:${h.rate}%"></i></div><span class="num">${h.score}/${h.total}</span></div>`).join('')
    : '<div class="tiny">还没有测验记录。</div>';
}
$('resetAll').onclick=()=>{
  if(!confirm('清空全部进度（含错题本、卡片掌握、成绩）？此操作不可恢复。')) return;
  localStorage.removeItem(S_KEY);
  S={right:0,wrong:0,seen:{},wrongIds:[],srs:{},cards:{},lastDay:'',streak:0,history:[],topicStat:{},theme:document.documentElement.dataset.theme,group:null};
  group=null; save(); renderMe(); updatePoolInfo(); toast('已清空');
};

/* ---------------- 初始化 ---------------- */
if(S.group && S.group.ids && S.group.ids.length){
  group = S.group;
  const valid = group.ids.filter(id=>CARDS_BY_ID[id]);
  if(valid.length){
    group.ids = valid; if(group.i>=valid.length) group.i=valid.length-1;
    $('cardIdle').style.display='none';
    $('cardStage').style.display='block';
    renderCard();
  }else{ group=null; }
}
updatePoolInfo();
drillList = shuffle(QS);
renderBank();
renderMe();

/* 键盘 */
document.addEventListener('keydown', e=>{
  if($('mask').classList.contains('on')) return;
  if(!document.querySelector('[data-view="cards"]').classList.contains('on')) return;
  if(!group) return;
  if(e.code==='Space'){ e.preventDefault(); $('flip').click(); }
  if(e.key==='ArrowRight') cardNext(true);
  if(e.key==='ArrowLeft') $('prevCard').click();
});
})();
</script>
</body>
</html>
