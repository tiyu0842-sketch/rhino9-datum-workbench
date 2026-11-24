<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>工业设计史 · 闯关复习</title>
<style>
:root{
  --bg:#14161a; --panel:#1c1f25; --ink:#e8e9ec; --muted:#9aa0aa; --line:#2c313a;
  --accent:#ff8a28; --good:#8bd17c; --bad:#ff6b5e; --q:#5cc8e8; --card:#232730;
  --radius:16px; --font:"Microsoft YaHei","微软雅黑",sans-serif; --deco:"";
}
html[data-theme="kitty"]{
  --bg:#fff5f8; --panel:#ffffff; --ink:#4a3540; --muted:#9b8390; --line:#f3d9e2;
  --accent:#ff7fa8; --good:#6fc98a; --bad:#ef7a86; --q:#8ab6e8; --card:#fffafc;
  --radius:26px; --font:"Microsoft YaHei","微软雅黑",sans-serif;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--font);line-height:1.65;
     transition:background .25s,color .25s}
body[data-kitty="1"]::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;
  background-image:radial-gradient(circle at 12% 18%,rgba(255,127,168,.10) 0 8px,transparent 9px),
                   radial-gradient(circle at 88% 72%,rgba(255,127,168,.08) 0 6px,transparent 7px);}
.wrap{max-width:720px;margin:0 auto;padding:22px 16px 70px;position:relative;z-index:1}
header{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
h1{font-size:21px;font-weight:600;margin:0;display:flex;align-items:center;gap:8px}
body[data-kitty="1"] h1::before{content:"✿";color:var(--accent);font-size:24px}
.sub{font-size:12px;color:var(--muted);margin-top:3px}
.tbtn{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:999px;
      padding:7px 14px;font-size:13px;cursor:pointer;font-family:inherit}
.tbtn:hover{border-color:var(--accent)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
      padding:20px;margin-top:16px}
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}
.tab{flex:1;min-width:92px;text-align:center;background:transparent;color:var(--muted);
     border:1px solid var(--line);border-radius:12px;padding:9px 6px;cursor:pointer;font-size:13px;font-family:inherit}
.tab.on{color:var(--accent);border-color:var(--accent);background:rgba(255,138,40,.07)}
body[data-kitty="1"] .tab.on{background:rgba(255,127,168,.12)}
.badge{display:inline-block;font-size:11px;padding:2px 9px;border-radius:999px;
       background:var(--line);color:var(--muted);margin-right:6px}
.due{color:var(--accent)}
.qcard{text-align:center;padding:30px 18px}
.qtype{font-size:12px;color:var(--muted);letter-spacing:.06em}
.question{font-size:21px;font-weight:600;margin:14px 0 24px;line-height:1.5}
.opts{display:grid;grid-template-columns:1fr 1fr;gap:10px}
@media(max-width:520px){.opts{grid-template-columns:1fr}}
.opt{background:var(--card);color:var(--ink);border:1.5px solid var(--line);
     border-radius:14px;padding:14px 12px;font-size:14px;cursor:pointer;
     font-family:inherit;transition:.15s;min-height:58px;display:flex;align-items:center;gap:9px}
.opt:hover:not(:disabled){border-color:var(--q);transform:translateY(-1px)}
.opt .k{width:26px;height:26px;flex:0 0 26px;border-radius:50%;background:var(--line);
        display:flex;align-items:center;justify-content:center;font-size:12px;color:var(--muted)}
.opt:disabled{cursor:default}
.opt.right{border-color:var(--good);background:rgba(139,209,124,.12)}
.opt.wrong{border-color:var(--bad);background:rgba(255,107,94,.12)}
.opt.right .k{background:var(--good);color:#12210e}
.opt.wrong .k{background:var(--bad);color:#2a0b0b}
.prog{height:6px;background:var(--line);border-radius:3px;overflow:hidden;margin-top:20px}
.prog>i{display:block;height:100%;background:var(--accent);width:0;transition:.3s}
.row{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}
.act{background:var(--accent);color:#1a1206;border:0;border-radius:11px;padding:10px 18px;
     font-size:14px;font-weight:600;cursor:pointer;font-family:inherit}
body[data-kitty="1"] .act{color:#fff}
.ghost{background:transparent;color:var(--muted);border:1px solid var(--line);
       padding:10px 16px;border-radius:11px;cursor:pointer;font-family:inherit;font-size:14px}
.act:disabled{opacity:.45;cursor:default}
.stat{display:flex;gap:18px;flex-wrap:wrap;font-size:12px;color:var(--muted)}
.stat b{color:var(--ink);font-size:17px;display:block}
.sec{font-size:13px;font-weight:600;margin-bottom:8px;color:var(--ink)}
.wrong-item{padding:10px 0;border-bottom:1px dashed var(--line);font-size:13px}
.wrong-item:last-child{border-bottom:0}
.wrong-item .m{font-size:11px;color:var(--muted)}
.dueitem{display:flex;justify-content:space-between;font-size:12px;padding:6px 0;color:var(--muted)}
.dueitem b{color:var(--ink)}
.mask{display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:20;
      align-items:center;justify-content:center;padding:18px}
.mask.on{display:flex}
.sheet{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
       max-width:560px;width:100%;max-height:86vh;overflow:auto;padding:24px}
.sheet h3{margin:0 0 6px;font-size:19px}
.scene{background:var(--card);border-radius:12px;padding:14px;font-size:14px;margin:14px 0}
.point{font-size:17px;font-weight:600;color:var(--accent);margin:10px 0}
.why{font-size:14px}
.more{font-size:13px;color:var(--muted);margin-top:10px;padding-top:10px;border-top:1px dashed var(--line)}
.src{font-size:11px;color:var(--muted);margin-top:10px;word-break:break-all}
.src a{color:var(--q)}
.evid{font-size:12px;color:var(--muted);background:var(--card);border-left:3px solid var(--q);
      padding:10px;margin-top:10px;border-radius:0 8px 8px 0}
.hidden{display:none}
.center{text-align:center}
.big{font-size:30px;font-weight:600;color:var(--accent)}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1>工业设计史 · 闯关复习</h1>
      <div class="sub">每日闯关 · 艾宾浩斯复习 · 错题科普 · 每题可追溯原文</div>
    </div>
    <button class="tbtn" id="themeBtn">切换：可爱风 ✿</button>
  </header>

  <div class="tabs">
    <button class="tab on" data-mode="daily">每日闯关</button>
    <button class="tab" data-mode="review">今日复习</button>
    <button class="tab" data-mode="wrong">错题重做</button>
  </div>

  <div class="card qcard" id="stage">
    <div class="qtype" id="qtype">准备中…</div>
    <div class="question" id="question"></div>
    <div class="opts" id="opts"></div>
    <div class="prog"><i id="prog"></i></div>
    <div class="row" style="justify-content:center">
      <button class="act" id="next" disabled>下一题 →</button>
      <button class="ghost" id="showSci">看科普卡</button>
    </div>
  </div>

  <div class="card center hidden" id="finish">
    <div class="big" id="finishBig">闯关完成</div>
    <div class="sub" id="finishSub"></div>
    <div class="row" style="justify-content:center">
      <button class="act" id="again">再来一轮</button>
    </div>
  </div>

  <div class="card">
    <div class="stat">
      <span>累计答对<b id="cRight">0</b></span>
      <span>错题<b id="cWrong">0</b></span>
      <span>连续打卡<b id="cStreak">0</b>天</span>
      <span>题库<b id="cTotal">0</b>题</span>
    </div>
  </div>

  <div class="card">
    <div class="sec">艾宾浩斯复习安排（1 / 2 / 4 / 7 / 15 / 30 天）</div>
    <div id="dueList"><div class="sub">暂无到期题目</div></div>
  </div>

  <div class="card">
    <div class="sec">错题本 · 点题看科普</div>
    <div id="wrongList"><div class="sub">暂无错题</div></div>
    <div class="row"><button class="ghost" id="clearWrong">清空错题本</button></div>
  </div>

  <div class="card" style="font-size:12px;color:var(--muted)">
    题目来自本机 DOC（每题原文可核），科普卡附可点开的外部来源。
    间隔重复与进度仅存在本浏览器，清缓存会丢失。
  </div>
</div>

<div class="mask" id="mask">
  <div class="sheet">
    <h3 id="sciTitle">科普卡</h3>
    <div class="sub" id="sciTopic"></div>
    <div class="scene" id="sciScene"></div>
    <div class="point" id="sciPoint"></div>
    <div class="why" id="sciWhy"></div>
    <div class="more" id="sciMore"></div>
    <div class="evid" id="sciEvid"></div>
    <div class="src" id="sciSrc"></div>
    <div class="row"><button class="act" id="closeSci">知道了</button></div>
  </div>
</div>

<script id="quiz" type="application/json">__QUIZ_DATA__</script>
<script id="cards" type="application/json">__CARD_DATA__</script>
<script>
(function(){
"use strict";
const Q=JSON.parse(document.getElementById('quiz').textContent).questions||[];
const C=JSON.parse(document.getElementById('cards').textContent)||{};
const KEY='idh_quiz_v2';
const DAILY=5;
const STEPS=[1,2,4,7,15,30];
const $=id=>document.getElementById(id);
const DAY=864e5;
const today=()=>new Date().toISOString().slice(0,10);
let S={right:0,wrong:0,wrongIds:[],lastDay:'',streak:0,srs:{},theme:'simple'};
try{const raw=localStorage.getItem(KEY);if(raw)S=Object.assign(S,JSON.parse(raw));}catch(e){}
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify(S));}catch(e){}};
function applyTheme(){
  document.documentElement.setAttribute('data-theme',S.theme);
  document.body.setAttribute('data-kitty',S.theme==='kitty'?'1':'0');
  $('themeBtn').textContent=S.theme==='kitty'?'切换：简约风':'切换：可爱风 ✿';
}
$('themeBtn').onclick=()=>{S.theme=S.theme==='kitty'?'simple':'kitty';save();applyTheme();};
applyTheme();

// 每日刷新与连续天数
const td=today();
if(S.lastDay!==td){
  const y=new Date(Date.now()-DAY).toISOString().slice(0,10);
  S.streak=S.lastDay===y?S.streak+1:1;
  S.lastDay=td;save();
}

let mode='daily',queue=[],idx=0,answered=false,current=null;
function qById(id){return Q.find(q=>q.id===id);}
function dueIds(){
  const n=Date.now();
  return Object.keys(S.srs).filter(id=>S.srs[id]&&S.srs[id].due<=n).map(Number);
}
function pick(pool,n){
  pool=pool.slice();
  const off=(new Date(td).getDate()*7)%Math.max(1,pool.length);
  const out=[];
  for(let i=0;i<n&&pool.length;i++){
    const k=(off+i*3)%pool.length;
    out.push(pool[k]);
  }
  return out;
}
function buildQueue(){
  if(mode==='daily') queue=pick(Q,DAILY);
  else if(mode==='review'){
    const d=dueIds();
    queue=d.length?pick(d.map(qById).filter(Boolean),DAILY):[];
  } else queue=pick(Q.filter(q=>S.wrongIds.includes(q.id)),DAILY);
  idx=0;render();
}
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));
  t.classList.add('on');mode=t.dataset.mode;buildQueue();
});

function render(){
  const st=$('stage'),fin=$('finish');
  if(!queue.length){
    st.classList.add('hidden');fin.classList.remove('hidden');
    $('finishBig').textContent=mode==='review'?'今天没有到期题':'暂无题目';
    $('finishSub').textContent=mode==='review'?'按 1/2/4/7/15/30 天安排，之后会提醒复习':
                              mode==='wrong'?'先去闯关积累错题':'题库加载中';
    return;
  }
  if(idx>=queue.length){
    st.classList.add('hidden');fin.classList.remove('hidden');
    $('finishBig').textContent='闯关完成';
    $('finishSub').textContent='本轮 '+queue.length+' 题 · 错题已加入科普复习清单';
    return;
  }
  st.classList.remove('hidden');fin.classList.add('hidden');
  current=queue[idx];answered=false;
  $('qtype').innerHTML='<span class="badge">'+current.topic+'</span>'+(idx+1)+' / '+queue.length;
  $('question').textContent=current.q;
  const box=$('opts');box.innerHTML='';
  current.options.forEach((o,i)=>{
    const b=document.createElement('button');b.className='opt';
    b.innerHTML='<span class="k">'+String.fromCharCode(65+i)+'</span><span>'+o+'</span>';
    b.onclick=()=>answer(i,b);box.appendChild(b);
  });
  $('prog').style.width=(idx/queue.length*100)+'%';
  $('next').disabled=true;
}

function answer(i,btn){
  if(answered)return;answered=true;
  const ok=i===current.answer;
  [...$('opts').children].forEach((b,j)=>{
    b.disabled=true;
    if(j===current.answer)b.classList.add('right');
    else if(j===i)b.classList.add('wrong');
  });
  const id=current.id;
  if(!S.srs[id])S.srs[id]={step:0,due:0};
  const r=S.srs[id];
  if(ok){
    S.right++;
    r.step=Math.min(STEPS.length-1,r.step+1);
    r.due=Date.now()+STEPS[r.step]*DAY;
    const k=S.wrongIds.indexOf(id);if(k>=0)S.wrongIds.splice(k,1);
  }else{
    S.wrong++;
    r.step=0;r.due=Date.now()+DAY;
    if(!S.wrongIds.includes(id))S.wrongIds.push(id);
    setTimeout(()=>openSci(id),650);
  }
  save();updateStats();$('next').disabled=false;
}

$('next').onclick=()=>{idx++;render();};
$('again').onclick=()=>buildQueue();
$('showSci').onclick=()=>{if(current)openSci(current.id);};
$('closeSci').onclick=()=>$('mask').classList.remove('on');
$('mask').onclick=e=>{if(e.target===$('mask'))$('mask').classList.remove('on');};
$('clearWrong').onclick=()=>{S.wrongIds=[];save();updateStats();};

function openSci(id){
  const c=C[String(id)];const q=qById(id);
  if(!c||!q)return;
  $('sciTitle').textContent=q.q;
  $('sciTopic').textContent=q.topic+' · 错题科普卡';
  $('sciScene').textContent=c.scene;
  $('sciPoint').textContent=c.point;
  $('sciWhy').textContent=c.why;
  $('sciMore').textContent=c.more;
  $('sciEvid').textContent='原文锚点：'+c.evidence;
  $('sciSrc').innerHTML=c.src
    ?'外部科普来源：<a href="'+c.src+'" target="_blank" rel="noopener">'+c.srcn+'</a>'
    :'外部科普来源：'+c.srcn;
  $('mask').classList.add('on');
}

function updateStats(){
  $('cRight').textContent=S.right;$('cWrong').textContent=S.wrong;
  $('cStreak').textContent=S.streak;$('cTotal').textContent=Q.length;
  const wl=$('wrongList');wl.innerHTML='';
  if(!S.wrongIds.length)wl.innerHTML='<div class="sub">暂无错题</div>';
  else S.wrongIds.forEach(id=>{
    const q=qById(id);if(!q)return;
    const d=document.createElement('div');d.className='wrong-item';
    d.innerHTML='<div>'+q.q+'</div><div class="m"><a href="#" data-id="'+id+'">看科普卡 →</a> · '+q.topic+'</div>';
    d.querySelector('a').onclick=e=>{e.preventDefault();openSci(id);};
    wl.appendChild(d);
  });
  const dl=$('dueList');dl.innerHTML='';
  const d=dueIds();
  if(!d.length)dl.innerHTML='<div class="sub">暂无到期题目；按 1/2/4/7/15/30 天自动安排</div>';
  else d.forEach(id=>{
    const q=qById(id);if(!q)return;
    const s=S.srs[id];
    const div=document.createElement('div');div.className='dueitem';
    div.innerHTML='<span>'+q.q.slice(0,26)+(q.q.length>26?'…':'')+'</span><b>第 '+(s.step+1)+' 阶</b>';
    dl.appendChild(div);
  });
}

buildQueue();updateStats();
})();
</script>
</body>
</html>
