<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PDF Downloader - Kanun Patrika</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#09090b;--sf:#18181b;--sf2:#1f1f23;--bd:#27272a;--bdh:#3f3f46;--tx:#fafafa;--tx2:#a1a1aa;--tx3:#71717a;--ac:#6366f1;--ach:#818cf8;--gn:#22c55e;--rd:#ef4444;--am:#eab308;--r:10px;--rs:6px}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--tx);min-height:100vh;line-height:1.5;-webkit-font-smoothing:antialiased}
.app{max-width:960px;margin:0 auto;padding:32px 24px 64px}
.header{margin-bottom:32px}
.header h1{font-size:24px;font-weight:700;letter-spacing:-.5px}
.header p{color:var(--tx3);font-size:14px;margin-top:4px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px}
.stat{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);padding:16px;text-align:center}
.stat-value{display:block;font-size:28px;font-weight:700;font-variant-numeric:tabular-nums;line-height:1.2}
.stat-label{display:block;font-size:12px;color:var(--tx3);text-transform:uppercase;letter-spacing:.5px;margin-top:4px}
.stat--g .stat-value{color:var(--gn)}.stat--a .stat-value{color:var(--am)}.stat--r .stat-value{color:var(--rd)}
.pw{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);padding:20px 24px;margin-bottom:16px}
.pt{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:12px}
.ps{font-size:14px;color:var(--tx2)}.pp{font-size:22px;font-weight:700;font-variant-numeric:tabular-nums}
.pb{height:8px;background:var(--sf2);border-radius:999px;overflow:hidden;position:relative}
.pf{height:100%;width:0;border-radius:999px;background:linear-gradient(90deg,var(--ac),#8b5cf6,var(--ach));background-size:200% 100%;transition:width .4s ease;position:relative}
.pf::after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,transparent,rgba(255,255,255,.15),transparent);background-size:200% 100%;animation:sh 1.8s linear infinite}
.pf.done{background:var(--gn);background-size:100% 100%}.pf.done::after{animation:none}
.pf.cancelled{background:var(--rd);background-size:100% 100%}.pf.cancelled::after{animation:none}
@keyframes sh{0%{background-position:200% 0}100%{background-position:-200% 0}}
.pm{display:flex;gap:16px;margin-top:10px;font-size:13px;color:var(--tx3)}
.pm span{font-variant-numeric:tabular-nums}
.ctrls{display:flex;gap:10px;margin-bottom:28px}
.btn{display:inline-flex;align-items:center;gap:6px;padding:10px 20px;border:none;border-radius:var(--rs);font-size:14px;font-weight:600;cursor:pointer;transition:background .15s,opacity .15s;font-family:inherit}
.btn:disabled{opacity:.4;cursor:not-allowed}
.btn-p{background:var(--ac);color:#fff}.btn-p:hover:not(:disabled){background:var(--ach)}
.btn-d{background:#7f1d1d;color:var(--rd);border:1px solid rgba(239,68,68,.25)}.btn-d:hover:not(:disabled){background:#991b1b;color:#fca5a5}
.btn-g{background:var(--sf);color:var(--tx2);border:1px solid var(--bd)}.btn-g:hover:not(:disabled){background:var(--sf2);color:var(--tx)}
.fs{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);overflow:hidden}
.fh{display:flex;justify-content:space-between;align-items:center;padding:14px 20px;border-bottom:1px solid var(--bd)}
.fh h3{font-size:14px;font-weight:600}
.flt{display:flex;gap:4px}
.fb{padding:4px 12px;border:1px solid var(--bd);border-radius:999px;background:transparent;color:var(--tx3);font-size:12px;cursor:pointer;transition:all .15s;font-family:inherit}
.fb:hover{color:var(--tx2);border-color:var(--bdh)}.fb.active{background:var(--ac);color:#fff;border-color:var(--ac)}
.fl{max-height:420px;overflow-y:auto;overscroll-behavior:contain}
.fl::-webkit-scrollbar{width:6px}.fl::-webkit-scrollbar-track{background:transparent}.fl::-webkit-scrollbar-thumb{background:var(--bdh);border-radius:3px}
.fr{display:grid;grid-template-columns:6px 1fr auto;gap:14px;align-items:center;padding:10px 20px;border-bottom:1px solid var(--bd);font-size:13px;transition:background .1s}
.fr:last-child{border-bottom:none}.fr:hover{background:var(--sf2)}
.dt{width:6px;height:6px;border-radius:50%;background:var(--bdh)}
.dt-d{background:var(--gn)}.dt-s{background:var(--tx3)}.dt-f{background:var(--rd)}.dt-p{background:var(--bdh)}
.fn{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--tx2)}
.fn.dn{color:var(--tx)}
.bdg{font-size:12px;padding:2px 10px;border-radius:999px;white-space:nowrap;font-weight:500}
.bd-d{background:rgba(34,197,94,.12);color:var(--gn)}.bd-s{background:rgba(113,113,122,.12);color:var(--tx3)}
.bd-f{background:rgba(239,68,68,.12);color:var(--rd)}.bd-p{background:rgba(63,63,70,.2);color:var(--tx3)}
.emp{padding:48px 20px;text-align:center;color:var(--tx3);font-size:14px}
.emp svg{display:block;margin:0 auto 12px;opacity:.3}
.et{font-size:11px;color:var(--rd);opacity:.7;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
@media(max-width:640px){.stats{grid-template-columns:repeat(2,1fr)}.ctrls{flex-wrap:wrap}.btn{flex:1;justify-content:center}}
</style>
</head>
<body>
<div class="app">
<header class="header"><h1>PDF Downloader</h1><p>Kanun Patrika &mdash; Nepal Supreme Court Publications</p></header>
<div class="stats">
<div class="stat"><span class="stat-value" id="sT">0</span><span class="stat-label">Total</span></div>
<div class="stat stat--g"><span class="stat-value" id="sD">0</span><span class="stat-label">Downloaded</span></div>
<div class="stat stat--a"><span class="stat-value" id="sS">0</span><span class="stat-label">Skipped</span></div>
<div class="stat stat--r"><span class="stat-value" id="sF">0</span><span class="stat-label">Failed</span></div>
</div>
<div class="pw">
<div class="pt"><span class="ps" id="pSt">Ready</span><span class="pp" id="pPc">0%</span></div>
<div class="pb"><div class="pf" id="pFi"></div></div>
<div class="pm"><span id="pCt">&mdash;</span><span id="pSp">&mdash;</span><span id="pEt">&mdash;</span><span id="pSz">&mdash;</span></div>
</div>
<div class="ctrls">
<button class="btn btn-p" id="bS">&#9654; Start Download</button>
<button class="btn btn-d" id="bC" disabled>&#9632; Cancel</button>
<button class="btn btn-g" id="bR">&#8635; Reset</button>
</div>
<div class="fs">
<div class="fh"><h3>Files</h3>
<div class="flt">
<button class="fb active" data-f="all">All</button>
<button class="fb" data-f="downloaded">Downloaded</button>
<button class="fb" data-f="failed">Failed</button>
<button class="fb" data-f="skipped">Skipped</button>
<button class="fb" data-f="pending">Pending</button>
</div></div>
<div class="fl" id="fL">
<div class="emp" id="eS">
<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
No files yet. Click <strong>Start Download</strong> to begin.</div></div>
</div>
</div>
<script>
(function(){
var API='api.php',POLL=600,$=function(id){return document.getElementById(id)};
var tmr=null,run=false,files=[],filt='all',tot=0;
var eT=$('sT'),eD=$('sD'),eS=$('sS'),eF=$('sF'),eSt=$('pSt'),ePc=$('pPc'),eFi=$('pFi');
var eCt=$('pCt'),eSp=$('pSp'),eEt=$('pEt'),eSz=$('pSz'),eL=$('fL'),eE=$('eS');
var bS=$('bS'),bC=$('bC'),bR=$('bR');

fetch(API+'?action=status').then(function(r){return r.json()}).then(upd).catch(function(){});

bS.onclick=function(){bS.disabled=true;fetch(API+'?action=start').then(function(r){return r.json()}).then(function(d){
if(d.error){alert(d.error);bS.disabled=false;return}
files=[];tot=d.total||0;render();upd(d);startPoll()});
};
bC.onclick=function(){fetch(API+'?action=cancel')};
bR.onclick=function(){fetch(API+'?action=reset').then(function(){stopPoll();run=false;files=[];tot=0;resetUI();render()})};

document.querySelectorAll('.fb').forEach(function(b){b.onclick=function(){
document.querySelector('.fb.active').classList.remove('active');b.classList.add('active');
filt=b.dataset.f;render()}});

function startPoll(){if(tmr)return;run=true;bC.disabled=false;bS.disabled=true;tmr=setInterval(poll,POLL)}
function stopPoll(){clearInterval(tmr);tmr=null;bC.disabled=true;bS.disabled=false}

function poll(){fetch(API+'?action=status').then(function(r){return r.json()}).then(function(d){
upd(d);if(d.status==='completed'||d.status==='cancelled'||d.status==='idle'){stopPoll();run=false}}).catch(function(){})}

function upd(d){
eT.textContent=d.total||0;eD.textContent=d.downloaded||0;eS.textContent=d.skipped||0;eF.textContent=d.failed||0;
var done=d.completed||0,total=d.total||0,pct=total?Math.round(done/total*100):0;
ePc.textContent=pct+'%';eFi.style.width=pct+'%';
var st=d.status||'idle';
if(st==='running'){eSt.textContent='Downloading...';eFi.className='pf'}
else if(st==='completed'){eSt.textContent='Complete';eFi.className='pf done'}
else if(st==='cancelled'){eSt.textContent='Cancelled';eFi.className='pf cancelled'}
else{eSt.textContent='Ready';eFi.className='pf';eFi.style.width='0'}

var elapsed=d.startTime?(Date.now()/1000-d.startTime):0;
eCt.textContent=done+'/'+total+' files';
if(st==='running'&&elapsed>0){
var spd=done/elapsed,rem=(total-done)/spd;
eSp.textContent=fmtSpd(d.totalSize||0,elapsed);
eEt.textContent='~'+fmtTime(rem)+' left';
}else if(st==='completed'&&d.duration){eSp.textContent=fmtSpd(d.totalSize||0,d.duration);eEt.textContent='Done in '+fmtTime(d.duration)}
else{eSp.textContent='\u2014';eEt.textContent='\u2014'}
eSz.textContent=d.totalSize?fmtSize(d.totalSize):'\u2014';

if(d.files&&d.files.length>0){
var known=new Set(files.map(function(f){return f.name}));
d.files.forEach(function(f){if(!known.has(f.name))files.push(f)});
render()}
}

function render(){
var list=filt==='all'?files:files.filter(function(f){return f.status===filt});
eE.style.display=list.length?'none':'block';
var html='';
for(var i=0;i<list.length;i++){
var f=list[i],s=f.status||'pending';
var dc='dt dt-'+({downloaded:'d',skipped:'s',failed:'f'}[s]||'p');
var nc='fn'+(s==='downloaded'?' dn':'');
var bc='bdg bd-'+({downloaded:'d',skipped:'s',failed:'f'}[s]||'p');
var bl={downloaded:'Downloaded',skipped:'Skipped',failed:'Failed',pending:'Pending'}[s]||'Pending';
var title=f.error?' title="'+esc(f.error)+'"':'';
html+='<div class="fr"><div class="'+dc+'"></div><div class="'+nc+'"'+title+'>'+esc(f.name)+'</div><div class="'+bc+'">'+bl+(f.error?' - '+esc(f.error):'')+'</div></div>';
}
eL.innerHTML='<div class="emp" id="eS" style="display:'+(list.length?'none':'block')+'"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>No files yet. Click <strong>Start Download</strong> to begin.</div>'+html;
eL.scrollTop=eL.scrollHeight;
}

function resetUI(){
eT.textContent='0';eD.textContent='0';eS.textContent='0';eF.textContent='0';
eSt.textContent='Ready';ePc.textContent='0%';eFi.style.width='0';eFi.className='pf';
eCt.textContent='\u2014';eSp.textContent='\u2014';eEt.textContent='\u2014';eSz.textContent='\u2014';
}

function fmtSize(b){if(b<1024)return b+' B';if(b<1048576)return(b/1024).toFixed(1)+' KB';return(b/1048576).toFixed(1)+' MB'}
function fmtTime(s){if(s<60)return Math.round(s)+'s';var m=Math.floor(s/60),ss=Math.round(s%60);return m+'m '+ss+'s'}
function fmtSpd(b,s){var sp=s>0?b/s:0;return fmtSize(sp)+'/s'}
function esc(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML}
})();
</script>
</body>
</html>
