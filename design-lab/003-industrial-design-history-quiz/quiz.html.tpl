<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>工业设计史 · 每日闯关</title>
<style>
  :root{
    --bg:#14161a; --panel:#1c1f25; --ink:#e8e9ec; --muted:#9aa0aa;
    --line:#2c313a; --accent:#ff8a28; --good:#8bd17c; --bad:#ff6b5e; --q:#5cc8e8;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
       font-family:"Microsoft YaHei","微软雅黑",sans-serif;line-height:1.6}
  .wrap{max-width:760px;margin:0 auto;padding:24px 18px 60px}
  header{display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap}
  h1{font-size:22px;font-weight:600;margin:0}
  .sub{font-size:13px;color:var(--muted)}
  .streak{font-size:13px;color:var(--accent)}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:14px;
        padding:20px;margin-top:18px}
  .topic{font-size:12px;color:var(--q);letter-spacing:.05em}
  .q{font-size:18px;font-weight:600;margin:8px 0 16px}
  .opt{display:block;width:100%;text-align:left;background:transparent;color:var(--ink);
       border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:8px 0;
       font-size:15px;cursor:pointer;transition:.15s;font-family:inherit}
  .opt:hover:not(:disabled){border-color:var(--q)}
  .opt:disabled{cursor:default}
  .opt.right{border-color:var(--good);background:rgba(139,209,124,.12)}
  .opt.wrong{border-color:var(--bad);background:rgba(255,107,94,.12)}
  .evidence{margin-top:14px;padding:12px 14px;border-left:3px solid var(--q);
            background:rgba(92,200,232,.07);font-size:13px;color:var(--muted);display:none}
  .evidence b{color:var(--ink)}
  .bar{height:6px;background:var(--line);border-radius:3px;overflow:hidden;margin-top:18px}
  .bar>i{display:block;height:100%;background:var(--accent);width:0;transition:.3s}
  .row{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}
  button.act{background:var(--accent);color:#1a1206;border:0;border-radius:9px;
             padding:10px 18px;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit}
  button.ghost{background:transparent;color:var(--muted);border:1px solid var(--line);
             padding:10px 16px;border-radius:9px;cursor:pointer;font-family:inherit;font-size:14px}
  .stat{display:flex;gap:20px;font-size:13px;color:var(--muted);margin-top:14px;flex-wrap:wrap}
  .stat b{color:var(--ink);font-size:16px}
  .list{font-size:14px}
  .list li{margin:8px 0}
  .tag{font-size:11px;padding:2px 8px;border-radius:20px;background:var(--line);color:var(--muted)}
  .done{text-align:center;padding:40px 20px}
  .done h2{font-size:26px;margin:0 0 10px}
  .hidden{display:none}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1>工业设计史 · 每日闯关</h1>
      <div class="sub">题源：何人可《工业设计史》重点总结要点（考研必考）· 每题可核对原文</div>
    </div>
    <div class="streak" id="streak">连续 0 天</div>
  </header>

  <div class="card" id="stage">
    <div class="topic" id="topic">加载中…</div>
    <div class="q" id="q"></div>
    <div id="opts"></div>
    <div class="evidence" id="ev"></div>
    <div class="bar"><i id="prog"></i></div>
    <div class="row">
      <button class="act" id="next" disabled>下一题 →</button>
      <button class="ghost" id="skip">跳过</button>
    </div>
  </div>

  <div class="card done hidden" id="finish">
    <h2>今日闯关完成</h2>
    <div class="sub" id="finishStat"></div>
    <div class="row" style="justify-content:center">
      <button class="act" id="again">再练一次（含错题）</button>
      <button class="ghost" id="viewWrong">只看错题</button>
    </div>
  </div>

  <div class="card">
    <div class="topic">错题本</div>
    <div class="stat">
      <span>累计答对 <b id="cntRight">0</b></span>
      <span>累计答错 <b id="cntWrong">0</b></span>
      <span>题库 <b id="cntTotal">0</b> 题</span>
    </div>
    <ul class="list" id="wrongList"></ul>
    <div class="row">
      <button class="ghost" id="clear">清空错题本</button>
    </div>
  </div>

  <div class="card" style="font-size:12px;color:var(--muted)">
    <b>数据纪律</b>：本页题库来自本机 DOC 原文，每题 evidence 都在源文件中核对过；
    答错会显示原文片段便于复习。题目数量受限于可读的原始资料（扫描版 PDF 未能提取），
    后续补题须通过原文校验，不会混入编造内容。进度与错题保存在浏览器本地。
  </div>
</div>

<script id="quiz" type="application/json">__QUIZ_DATA__</script>
<script>
(function(){
  "use strict";
  const DATA = JSON.parse(document.getElementById('quiz').textContent);
  const ALL = DATA.questions || [];
  const KEY = 'idh_quiz_v1';
  let store = {right:0, wrong:0, wrongIds:[], lastDay:'', streak:0, doneIds:[]};
  try{ const s=localStorage.getItem(KEY); if(s) store=Object.assign(store,JSON.parse(s)); }catch(e){}
  const save=()=>{ try{ localStorage.setItem(KEY,JSON.stringify(store)); }catch(e){} };

  const $=id=>document.getElementById(id);
  const today=new Date().toISOString().slice(0,10);
  if(store.lastDay!==today){
    store.doneIds=[];
    const y=new Date(Date.now()-864e5).toISOString().slice(0,10);
    store.streak = store.lastDay===y ? store.streak+1 : 1;
    store.lastDay=today; save();
  }
  $('streak').textContent='连续 '+store.streak+' 天';
  $('cntTotal').textContent=ALL.length;

  // 每日一关：从题库取 5 题（固定步长按日期偏移，不用随机 → 可复现）
  const PER=5;
  const dayOffset=(new Date(today).getDate()*7)%Math.max(1,ALL.length);
  let queue=[];
  function buildQueue(onlyWrong){
    let pool = onlyWrong ? ALL.filter(q=>store.wrongIds.includes(q.id)) : ALL;
    if(!pool.length) pool=ALL;
    queue=[];
    for(let i=0;i<PER;i++) queue.push(pool[(dayOffset+i*3)%pool.length]);
    // 去重
    const seen=new Set(); queue=queue.filter(q=>!seen.has(q.id)&&seen.add(q.id));
    idx=0; answered=false;
  }
  let idx=0, answered=false;

  function render(){
    const stage=$('stage'), finish=$('finish');
    if(idx>=queue.length){
      stage.classList.add('hidden'); finish.classList.remove('hidden');
      $('finishStat').textContent='本关 '+queue.length+' 题 · 答对 '+queue.filter(q=>store.doneIds.includes(q.id)).length;
      return;
    }
    stage.classList.remove('hidden'); finish.classList.add('hidden');
    const q=queue[idx];
    $('topic').textContent=(idx+1)+' / '+queue.length+'  ·  '+q.topic;
    $('q').textContent=q.q;
    const box=$('opts'); box.innerHTML='';
    q.options.forEach((o,i)=>{
      const b=document.createElement('button');
      b.className='opt'; b.textContent=String.fromCharCode(65+i)+'. '+o;
      b.onclick=()=>answer(q,i,b);
      box.appendChild(b);
    });
    $('ev').style.display='none'; $('ev').innerHTML='';
    $('next').disabled=true; $('prog').style.width=(idx/queue.length*100)+'%';
    answered=false;
  }

  function answer(q,i,btn){
    if(answered) return; answered=true;
    const ok=i===q.answer;
    [...$('opts').children].forEach((b,j)=>{
      b.disabled=true;
      if(j===q.answer) b.classList.add('right');
      else if(j===i) b.classList.add('wrong');
    });
    if(ok){
      store.right++;
      if(!store.doneIds.includes(q.id)) store.doneIds.push(q.id);
      const k=store.wrongIds.indexOf(q.id);
      if(k>=0) store.wrongIds.splice(k,1);
    }else{
      store.wrong++;
      if(!store.wrongIds.includes(q.id)) store.wrongIds.push(q.id);
    }
    save(); updateStats();
    const ev=$('ev');
    ev.innerHTML='<b>'+(ok?'答对了':'正确答案：'+String.fromCharCode(65+q.answer))+'</b><br>原文：'+q.evidence
                +'<br><span style="color:#6f7681">来源：'+q.source+'</span>';
    ev.style.display='block';
    $('next').disabled=false;
  }

  function updateStats(){
    $('cntRight').textContent=store.right;
    $('cntWrong').textContent=store.wrong;
    const ul=$('wrongList'); ul.innerHTML='';
    if(!store.wrongIds.length){ ul.innerHTML='<li class="sub">暂无错题</li>'; return; }
    ALL.filter(q=>store.wrongIds.includes(q.id)).forEach(q=>{
      const li=document.createElement('li');
      li.innerHTML='<span class="tag">'+q.topic+'</span> '+q.q;
      ul.appendChild(li);
    });
  }

  $('next').onclick=()=>{ idx++; render(); };
  $('skip').onclick=()=>{ idx++; render(); };
  $('again').onclick=()=>{ buildQueue(false); render(); };
  $('viewWrong').onclick=()=>{ buildQueue(true); render(); };
  $('clear').onclick=()=>{ store.wrongIds=[]; save(); updateStats(); };

  buildQueue(false); updateStats(); render();
})();
</script>
</body>
</html>
