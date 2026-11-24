<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>设计史世界线 · 先理解，再巩固</title>
<style>
:root{
  --bg:#14161a; --panel:#1c1f25; --ink:#e8e9ec; --muted:#9aa0aa; --line:#2c313a;
  --accent:#ff8a28; --good:#8bd17c; --bad:#ff6b5e; --q:#5cc8e8; --card:#232730;
  --gold:#f5c86b; --radius:16px; --font:"Microsoft YaHei","微软雅黑",sans-serif;
}
html[data-theme="kitty"]{
  --bg:#fff5f8; --panel:#ffffff; --ink:#4a3540; --muted:#9b8390; --line:#f3d9e2;
  --accent:#ff7fa8; --good:#6fc98a; --bad:#ef7a86; --q:#8ab6e8; --card:#fffafc;
  --gold:#e8a93c; --radius:26px;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--font);line-height:1.7;
     transition:background .25s,color .25s}
body[data-kitty="1"]::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;
  background-image:radial-gradient(circle at 12% 18%,rgba(255,127,168,.10) 0 8px,transparent 9px),
                   radial-gradient(circle at 88% 72%,rgba(255,127,168,.08) 0 6px,transparent 7px);}
.wrap{max-width:760px;margin:0 auto;padding:22px 16px 80px;position:relative;z-index:1}
header{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap}
h1{font-size:22px;font-weight:600;margin:0;display:flex;align-items:center;gap:8px;line-height:1.3}
body[data-kitty="1"] h1::before{content:"✿";color:var(--accent);font-size:25px}
.sub{font-size:12px;color:var(--muted);margin-top:5px}
.tbtn{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:999px;
      padding:8px 15px;font-size:13px;cursor:pointer;font-family:inherit;white-space:nowrap}
.tbtn:hover{border-color:var(--accent)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
      padding:18px 20px;margin-top:16px}
.thread{background:linear-gradient(135deg,rgba(255,138,40,.10),rgba(92,200,232,.06));
        border-color:rgba(255,138,40,.35)}
body[data-kitty="1"] .thread{background:linear-gradient(135deg,rgba(255,127,168,.12),rgba(138,182,232,.08))}
.thread .q{font-size:18px;font-weight:600;color:var(--accent);line-height:1.5}
.thread .a{font-size:13px;color:var(--muted);margin-top:8px}
.tensions{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}
.ten{flex:1;min-width:170px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 12px}
.ten b{font-size:13px;color:var(--gold)}
.ten span{font-size:11px;color:var(--muted);display:block;margin-top:3px}
.sec{font-size:13px;font-weight:600;color:var(--muted);letter-spacing:.04em;margin:22px 0 2px}

/* ---- 世界线：一条竖河 ---- */
.river{position:relative;margin-top:14px;padding-left:34px}
.river::before{content:"";position:absolute;left:11px;top:8px;bottom:8px;width:2px;
  background:linear-gradient(180deg,var(--gold),var(--accent),var(--q),var(--good));opacity:.55;border-radius:2px}
.station{position:relative;margin-bottom:14px}
.station::before{content:"";position:absolute;left:-28px;top:20px;width:12px;height:12px;border-radius:50%;
  background:var(--panel);border:2.5px solid var(--accent);box-shadow:0 0 0 4px var(--bg);z-index:1}
body[data-kitty="1"] .station::before{box-shadow:0 0 0 4px var(--bg)}
.station.on::before{background:var(--accent)}
.st-head{width:100%;text-align:left;background:var(--panel);color:var(--ink);border:1px solid var(--line);
  border-radius:var(--radius);padding:14px 16px;cursor:pointer;font-family:inherit;transition:.15s}
.st-head:hover{border-color:var(--accent)}
.station.on .st-head{border-color:var(--accent);box-shadow:0 3px 18px rgba(255,138,40,.10)}
.yr{font-size:11px;color:var(--gold);font-weight:600;letter-spacing:.05em}
.era{font-size:17px;font-weight:600;margin-top:1px}
.tag{font-size:12px;color:var(--muted);margin-top:2px}
.shift{font-size:11px;color:var(--accent);margin-top:7px;padding-top:7px;border-top:1px dashed var(--line)}
.st-body{display:none;padding:4px 4px 2px}
.station.on .st-body{display:block}
.layer{margin-top:14px;padding-left:12px;border-left:3px solid var(--line)}
.layer.picture{border-color:var(--q)}
.layer.core{border-color:var(--accent)}
.layer.why{border-color:var(--gold)}
.lb{font-size:11px;font-weight:600;color:var(--muted);letter-spacing:.06em}
.layer.picture .lb{color:var(--q)} .layer.core .lb{color:var(--accent)} .layer.why .lb{color:var(--gold)}
.lt{font-size:13.5px;margin-top:3px}
.fun{margin-top:15px;background:var(--card);border:1px solid var(--line);border-radius:13px;padding:13px 15px}
.fun .kind{font-size:10px;padding:2px 8px;border-radius:999px;display:inline-block;margin-bottom:7px}
.fun .kind.real{background:rgba(139,209,124,.15);color:var(--good)}
.fun .kind.mind{background:rgba(245,200,107,.15);color:var(--gold)}
.fun .ft{font-size:14px;font-weight:600}
.fun .fx{font-size:13px;color:var(--ink);margin-top:5px}
.fun .punch{font-size:13px;color:var(--accent);margin-top:9px;font-style:italic}
.fun a{font-size:11px;color:var(--q);text-decoration:none;margin-top:8px;display:inline-block}
.fun a:hover{text-decoration:underline}
.consolid{margin-top:15px;display:flex;gap:9px;align-items:center;flex-wrap:wrap}
.cbtn{background:var(--accent);color:#1a1206;border:0;border-radius:11px;padding:9px 15px;
  font-size:13px;font-weight:600;cursor:pointer;font-family:inherit}
body[data-kitty="1"] .cbtn{color:#fff}
.cbtn:disabled{opacity:.5;cursor:default}
.noq{font-size:11px;color:var(--muted);font-style:italic}

/* ---- 巩固弹层 ---- */
.mask{display:none;position:fixed;inset:0;background:rgba(0,0,0,.62);z-index:20;
      align-items:center;justify-content:center;padding:16px}
.mask.on{display:flex}
.modal{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
  width:100%;max-width:560px;max-height:90vh;overflow:auto;padding:22px}
.mhead{display:flex;justify-content:space-between;align-items:center;gap:10px}
.mhead h3{margin:0;font-size:16px}
.x{background:transparent;border:0;color:var(--muted);font-size:24px;cursor:pointer;line-height:1}
.question{font-size:19px;font-weight:600;margin:16px 0 20px;line-height:1.5}
.opts{display:grid;grid-template-columns:1fr 1fr;gap:10px}
@media(max-width:520px){.opts{grid-template-columns:1fr}}
.opt{background:var(--card);color:var(--ink);border:1.5px solid var(--line);border-radius:13px;
  padding:12px;font-size:13.5px;cursor:pointer;font-family:inherit;text-align:left;
  min-height:52px;display:flex;align-items:center;gap:9px;transition:.15s}
.opt:hover:not(:disabled){border-color:var(--q)}
.opt .k{width:24px;height:24px;flex:0 0 24px;border-radius:50%;background:var(--line);
  display:flex;align-items:center;justify-content:center;font-size:12px;color:var(--muted)}
.opt:disabled{cursor:default}
.opt.right{border-color:var(--good);background:rgba(139,209,124,.12)}
.opt.wrong{border-color:var(--bad);background:rgba(255,107,94,.12)}
.ev{margin-top:14px;background:var(--card);border-radius:11px;padding:11px 13px;font-size:12px;display:none}
.ev.on{display:block}
.ev .src{color:var(--muted);font-size:11px;margin-top:5px}
.next{margin-top:16px}
.sci{margin-top:14px;border:1px solid var(--accent);border-radius:12px;padding:12px 14px;display:none;background:rgba(255,138,40,.05)}
.sci.on{display:block}
.sci .sh{font-size:15px;font-weight:600}
.sci .ss{font-size:13px;margin-top:6px}
.sci .sw{font-size:13px;color:var(--accent);margin-top:7px}
.sci .sm{font-size:11px;color:var(--muted);margin-top:8px}
.sci a{color:var(--q);font-size:11px}
.modal .hint{font-size:11px;color:var(--muted);margin-top:12px;line-height:1.6}

/* ---- 复习管理 ---- */
.stat{display:flex;gap:18px;flex-wrap:wrap;font-size:12px;color:var(--muted)}
.stat b{color:var(--ink);font-size:17px;display:block}
.board{margin-top:10px}
.brow{display:flex;justify-content:space-between;font-size:12px;padding:5px 0;border-bottom:1px dashed var(--line)}
.brow .rank{color:var(--gold);font-weight:600;width:26px}
.brow .sc{flex:1}
.brow .dt{color:var(--muted)}
.empty{font-size:12px;color:var(--muted)}
.foot{font-size:11px;color:var(--muted);margin-top:26px;line-height:1.7}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1>设计史世界线</h1>
      <div class="sub">__SUBTITLE__</div>
    </div>
    <button class="tbtn" id="theme">切换风格 ✿</button>
  </header>

  <div class="card thread">
    <div class="q" id="threadQ"></div>
    <div class="a" id="threadA"></div>
    <div class="tensions" id="tensions"></div>
  </div>

  <div class="sec">一条河 · 十一个弯道 —— 点开每一站，先读懂思想怎么变</div>
  <div class="river" id="river"></div>

  <div class="card" id="manage">
    <div class="sec" style="margin-top:0">复习管理（巩固层）</div>
    <div class="stat">
      <div><b id="mRight">0</b>累计答对</div>
      <div><b id="mWrong">0</b>累计答错</div>
      <div><b id="mDue">0</b>今日待复习</div>
      <div><b id="mStreak">0</b>连续天数</div>
    </div>
    <div class="consolid">
      <button class="cbtn" id="reviewDue">复习到期题</button>
      <button class="tbtn" id="reviewWrong">只看错题</button>
      <button class="tbtn" id="clearWrong">清空错题本</button>
    </div>
    <div class="board" id="board"></div>
  </div>

  <div class="foot" id="foot"></div>
</div>

<div class="mask" id="mask">
  <div class="modal">
    <div class="mhead"><h3 id="mTitle">巩固</h3><button class="x" id="mClose">×</button></div>
    <div id="mQuiz">
      <div class="question" id="question"></div>
      <div class="opts" id="opts"></div>
      <div class="ev" id="evidence"></div>
      <div class="sci" id="sci"></div>
      <div class="next"><button class="cbtn" id="nextQ" style="display:none">下一题 →</button></div>
    </div>
    <div class="hint">答错会自动展开科普卡：先给你一个画面，再讲清一个点，最后回到原文——这不是为了记住答案，是为了搞懂为什么。</div>
  </div>
</div>

<script id="worldData" type="application/json">__WORLD_DATA__</script>
<script id="quizData" type="application/json">__QUIZ_DATA__</script>
<script id="cardData" type="application/json">__CARD_DATA__</script>
<script>
(function(){
  const W=JSON.parse(document.getElementById('worldData').textContent);
  const Q=JSON.parse(document.getElementById('quizData').textContent).questions;
  const C=JSON.parse(document.getElementById('cardData').textContent);
  const $=id=>document.getElementById(id);
  const today=()=>new Date().toISOString().slice(0,10);
  const qById=id=>Q.find(q=>q.id===id);
  const STEPS=[1,2,4,7,15,30];

  // ---- 持久化状态 ----
  let S={right:0,wrong:0,wrongIds:[],lastDay:'',streak:0,srs:{},history:[],theme:'simple'};
  try{const raw=localStorage.getItem('ids_world_v1');if(raw)S=Object.assign(S,JSON.parse(raw));}catch(e){}
  function save(){try{localStorage.setItem('ids_world_v1',JSON.stringify(S));}catch(e){}}
  function touchDay(){
    const d=today();
    if(S.lastDay===d)return;
    const y=new Date(Date.now()-86400000).toISOString().slice(0,10);
    S.streak=(S.lastDay===y)?S.streak+1:1;S.lastDay=d;save();
  }

  // ---- 顶部主线 ----
  $('threadQ').textContent=W.thread.question;
  $('threadA').textContent=W.thread.answer;
  $('tensions').innerHTML=W.thread.tensions.map(t=>
    '<div class="ten"><b>'+t.name+'</b><span>'+t.desc+'</span></div>').join('');

  // ---- 世界线 ----
  let openIdx=-1;
  function renderRiver(){
    $('river').innerHTML=W.world.map((w,i)=>{
      const fun=w.fun, real=fun.kind==='真实轶事';
      const src=fun.src?('<a href="'+fun.src+'" target="_blank" rel="noopener">来源：'+(fun.srcn||'公开资料')+' ↗</a>'):'';
      const qids=(w.qids||[]);
      const qs=qids.map(id=>qById(id)).filter(Boolean);
      const cons=qs.length
        ? '<button class="cbtn" data-quiz="'+i+'">学完了，做 '+qs.length+' 题巩固 →</button>'
        : '<span class="noq">这一站暂无巩固题（题库只覆盖到工艺美术运动）——故事照常，题目待补</span>';
      return '<div class="station'+(openIdx===i?' on':'')+'" data-i="'+i+'">'+
        '<button class="st-head" data-open="'+i+'">'+
          '<div class="yr">'+w.years+'</div>'+
          '<div class="era">'+w.era+' <span class="tag">· '+w.tag+'</span></div>'+
          '<div class="shift">'+w.shift+'</div>'+
        '</button>'+
        '<div class="st-body">'+
          '<div class="layer picture"><div class="lb">画面 · 先看见</div><div class="lt">'+w.picture+'</div></div>'+
          '<div class="layer core"><div class="lb">核心思想 · 这一站在说什么</div><div class="lt">'+w.core+'</div></div>'+
          '<div class="layer why"><div class="lb">为什么变 · 上一站留下了什么</div><div class="lt">'+w.why+'</div></div>'+
          '<div class="fun"><span class="kind '+(real?'real':'mind')+'">'+(real?'真实轶事 · 可点来源':'记忆画面 · 帮你记，非史实')+'</span>'+
            '<div class="ft">'+fun.title+'</div><div class="fx">'+fun.text+'</div>'+
            '<div class="punch">'+fun.punch+'</div>'+src+'</div>'+
          '<div class="consolid">'+cons+'</div>'+
        '</div></div>';
    }).join('');
  }
  renderRiver();

  // ---- 答题（巩固层）----
  let queue=[],qi=0,answered=false,cur=null,modeLabel='巩固',fromStation=-1,roundScore=0;
  function openQuiz(list,label,station){
    queue=list.slice();qi=0;roundScore=0;modeLabel=label;fromStation=(station===undefined?-1:station);
    if(!queue.length){alert('没有可供巩固的题目');return;}
    $('mTitle').textContent=label;$('mask').classList.add('on');showQ();
  }
  function showQ(){
    if(qi>=queue.length){
      if(modeLabel.indexOf('巩固')===0)recordRound(roundScore,queue.length);
      $('mQuiz').innerHTML='<div class="question">这一站巩固完成 ✓</div>'+
        '<div class="sub">本轮 '+roundScore+' / '+queue.length+' 题正确 · 累计答对 '+S.right+' / 答错 '+S.wrong+'。'+
        '理解的河已经走完，题只是回头确认你真的 get 到了。</div>'+
        '<div class="next"><button class="cbtn" id="doneBtn">回到世界线</button></div>';
      $('doneBtn').onclick=closeMask;return;
    }
    cur=queue[qi];answered=false;
    $('mQuiz').innerHTML='<div class="question" id="question"></div><div class="opts" id="opts"></div>'+
      '<div class="ev" id="evidence"></div><div class="sci" id="sci"></div>'+
      '<div class="next"><button class="cbtn" id="nextQ" style="display:none">下一题 →</button></div>';
    $('question').textContent=cur.q;
    const keys=['A','B','C','D'];
    $('opts').innerHTML=cur.options.map((o,k)=>
      '<button class="opt" data-k="'+k+'"><span class="k">'+keys[k]+'</span><span>'+o+'</span></button>').join('');
    $('opts').querySelectorAll('.opt').forEach(b=>b.onclick=()=>answer(Number(b.dataset.k)));
  }
  function answer(k){
    if(answered)return;answered=true;
    const ok=k===cur.answer;
    $('opts').querySelectorAll('.opt').forEach((b,i)=>{
      b.disabled=true;
      if(i===cur.answer)b.classList.add('right');
      if(i===k&&!ok)b.classList.add('wrong');
    });
    if(!S.srs[cur.id])S.srs[cur.id]={step:0,due:0};
    if(ok){
      S.right++;roundScore++;S.srs[cur.id].step=Math.min(STEPS.length,S.srs[cur.id].step+1);
      const n=S.srs[cur.id].step;
      const d=new Date(Date.now()+STEPS[n-1]*86400000).toISOString().slice(0,10);
      S.srs[cur.id].due=d;
      S.wrongIds=S.wrongIds.filter(x=>x!==cur.id);
    }else{
      S.wrong++;S.srs[cur.id].step=0;S.srs[cur.id].due=today();
      if(!S.wrongIds.includes(cur.id))S.wrongIds.push(cur.id);
    }
    touchDay();save();renderManage();
    // 原文证据（题目答案的本源）
    const ev=$('evidence');
    ev.innerHTML='<b>原文依据</b><br>'+(cur.evidence||'（无原文片段）')+
      '<div class="src">来源：'+(cur.source||'本机 DOC')+'</div>';
    ev.classList.add('on');
    // 科普卡（错题教学）
    if(!ok&&C[String(cur.id)]){
      const c=C[String(cur.id)];
      const sci=$('sci');
      sci.innerHTML='<div class="sh">💡 '+c.point+'</div>'+
        '<div class="ss">'+c.scene+'</div>'+
        '<div class="sw">'+c.why+'</div>'+
        (c.more?'<div class="sm">延伸：'+c.more+'</div>':'')+
        (c.src?'<div class="sm"><a href="'+c.src+'" target="_blank" rel="noopener">扩展阅读 ↗</a></div>':'');
      sci.classList.add('on');
    }
    $('nextQ').style.display='inline-block';
    $('nextQ').onclick=()=>{qi++;showQ();};
  }
  function closeMask(){$('mask').classList.remove('on');}

  // ---- 复习管理 ----
  function renderManage(){
    $('mRight').textContent=S.right;$('mWrong').textContent=S.wrong;
    const due=S.wrongIds.filter(id=>!S.srs[id]||S.srs[id].due<=today()).length;
    $('mDue').textContent=due;$('mStreak').textContent=S.streak;
    const top=S.history.slice().sort((a,b)=>(b.score-a.score)||(b.rate-a.rate)).slice(0,5);
    $('board').innerHTML='<div class="sec" style="margin-top:14px">本地个人最佳 · Top 5</div>'+
      (top.length?top.map((h,i)=>'<div class="brow"><span class="rank">'+(i+1)+'</span>'+
        '<span class="sc">'+h.score+' / '+h.total+' 题 · '+Math.round(h.rate*100)+'%</span>'+
        '<span class="dt">'+h.date+'</span></div>').join(''):'<div class="empty">还没有成绩，去任意一站点「巩固」吧</div>');
  }
  function recordRound(score,total){
    S.history.push({date:today(),score:score,total:total,rate:score/total});
    if(S.history.length>30)S.history=S.history.slice(-30);save();renderManage();
  }
  renderManage();

  // ---- 事件绑定 ----
  $('river').addEventListener('click',e=>{
    const q=e.target.closest('[data-quiz]');
    if(q){const i=Number(q.dataset.quiz);openQuiz((W.world[i].qids||[]).map(qById).filter(Boolean),'巩固 · '+W.world[i].era,i);return;}
    const h=e.target.closest('[data-open]');
    if(h){openIdx=(openIdx===Number(h.dataset.open)?-1:Number(h.dataset.open));renderRiver();}
  });
  $('reviewDue').onclick=()=>openQuiz(S.wrongIds.filter(id=>!S.srs[id]||S.srs[id].due<=today()).map(qById).filter(Boolean),'复习 · 今日到期');
  $('reviewWrong').onclick=()=>openQuiz(S.wrongIds.map(qById).filter(Boolean),'复习 · 错题本');
  $('clearWrong').onclick=()=>{if(confirm('清空错题本？不会删除已掌握记录和成绩。')){S.wrongIds=[];save();renderManage();}};
  $('mClose').onclick=closeMask;
  $('mask').addEventListener('click',e=>{if(e.target===$('mask'))closeMask();});
  function applyTheme(){
    document.documentElement.dataset.theme=S.theme;
    document.body.dataset.kitty=(S.theme==='kitty'?'1':'0');
    $('theme').textContent=(S.theme==='kitty'?'切换风格 ☾':'切换风格 ✿');
  }
  $('theme').onclick=()=>{S.theme=(S.theme==='kitty'?'simple':'kitty');save();applyTheme();};
  applyTheme();

  // 题库覆盖缺口如实标注
  const covered=W.world.filter(w=>(w.qids||[]).length).length;
  $('foot').textContent='世界线 '+W.world.length+' 站 · 有巩固题 '+covered+' 站 · 题库仅覆盖前 '+covered+' 站。'+
    '轶事分「真实轶事（带来源）」与「记忆画面（非史实）」两类，已逐条标注。'+
    '本地进度存浏览器，清缓存会丢。';
})();
</script>
</body>
</html>
