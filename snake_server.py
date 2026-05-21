# =============================================
# SNAKE 3D — БҮГД НЭГ ФАЙЛД
# Суулгах:  pip install websockets
# Ажиллуулах: python snake_server.py
# Дараа нь браузерт: http://localhost:8080
# Railway deploy: Procfile → "web: python snake_server.py"
# =============================================
import asyncio, websockets, json, random, time, os
from http.server import BaseHTTPRequestHandler
from io import BytesIO

PORT_WS   = int(os.environ.get("PORT", 8765))
PORT_HTTP = int(os.environ.get("PORT_HTTP", 8080))
HOST      = "0.0.0.0"
BLOCK=25; WORLD_W=3000; WORLD_H=3000; TICK=0.11
MAX_ROOMS=20; MAX_PLAYERS=16; FOOD_COUNT=30

FOOD_TYPES=[
    {"pts":1,"coins":1,"w":55,"color":[255,70,70]},
    {"pts":2,"coins":2,"w":25,"color":[255,210,0]},
    {"pts":3,"coins":3,"w":13,"color":[0,230,120]},
    {"pts":5,"coins":5,"w":5, "color":[180,0,255]},
    {"pts":8,"coins":8,"w":2, "color":[255,130,0]},
]
PLAYER_COLORS=[
    {"top":[0,210,80],   "side":[0,140,50],  "head":[0,255,120]},
    {"top":[30,120,255], "side":[10,60,180], "head":[100,180,255]},
    {"top":[255,200,0],  "side":[180,130,0], "head":[255,230,80]},
    {"top":[255,80,0],   "side":[180,30,0],  "head":[255,160,60]},
    {"top":[180,0,255],  "side":[100,0,180], "head":[220,100,255]},
    {"top":[150,230,255],"side":[80,160,200],"head":[210,245,255]},
    {"top":[255,160,200],"side":[200,100,150],"head":[255,200,230]},
    {"top":[80,80,160],  "side":[40,40,100], "head":[180,180,255]},
]

# =============================================
# HTML (index.html агуулга)
# =============================================
HTML = r"""<!DOCTYPE html>
<html lang="mn">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,user-scalable=no">
<title>Snake 3D — Онлайн</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@400;600&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent;}
:root{--neon:#00ff88;--neon2:#00ccff;--danger:#ff3355;--gold:#ffd700;--bg:#060810;--border:#1a2240;}
html,body{width:100%;height:100%;overflow:hidden;background:var(--bg);font-family:'Rajdhani',sans-serif;touch-action:none;}
#lobby{position:fixed;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;
  background:radial-gradient(ellipse at 50% 0%,#0a1628,var(--bg) 70%);z-index:100;}
#lobby h1{font-family:'Orbitron',monospace;font-size:clamp(26px,7vw,52px);color:#fff;letter-spacing:4px;
  text-shadow:0 0 20px var(--neon),0 0 60px rgba(0,255,136,.3);animation:glow 2.5s ease-in-out infinite;}
@keyframes glow{0%,100%{text-shadow:0 0 20px var(--neon),0 0 60px rgba(0,255,136,.3);}
  50%{text-shadow:0 0 35px var(--neon),0 0 90px rgba(0,255,136,.5);}}
#lobby .sub{font-size:clamp(10px,3vw,14px);color:var(--neon2);letter-spacing:6px;opacity:.7;}
.igrp{display:flex;flex-direction:column;gap:5px;width:min(320px,88vw);}
.igrp label{font-size:11px;letter-spacing:2px;color:rgba(255,255,255,.45);text-transform:uppercase;}
.igrp input{background:rgba(255,255,255,.04);border:1px solid var(--border);color:#fff;
  font-family:'Rajdhani',sans-serif;font-size:18px;font-weight:600;padding:11px 14px;border-radius:10px;outline:none;transition:.2s;}
.igrp input:focus{border-color:var(--neon);box-shadow:0 0 0 2px rgba(0,255,136,.15);}
#btn-join{width:min(320px,88vw);padding:15px;border:none;border-radius:12px;
  background:linear-gradient(135deg,#00cc66,#00ff88);color:#000;
  font-family:'Orbitron',monospace;font-size:15px;font-weight:900;letter-spacing:2px;
  cursor:pointer;box-shadow:0 4px 24px rgba(0,255,136,.35);transition:.15s;}
#btn-join:active{transform:scale(.97);}
#lob-err{font-size:13px;color:var(--danger);min-height:16px;letter-spacing:1px;}
#skin-row{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;width:min(340px,90vw);}
.sk-card{width:54px;height:66px;border-radius:10px;border:2px solid var(--border);
  background:rgba(255,255,255,.03);display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:4px;cursor:pointer;transition:.15s;}
.sk-card.sel{border-color:var(--neon);background:rgba(0,255,136,.08);box-shadow:0 0 10px rgba(0,255,136,.3);}
.sk-card canvas{display:block;}
.sk-card span{font-size:9px;color:rgba(255,255,255,.6);letter-spacing:1px;}
#game{position:fixed;inset:0;display:none;flex-direction:column;}
#game.on{display:flex;}
#cwrap{position:relative;flex:1;overflow:hidden;}
canvas#c{display:block;width:100%;height:100%;}
#hud{position:absolute;top:0;left:0;right:0;display:flex;align-items:center;justify-content:space-between;
  padding:8px 14px;background:linear-gradient(180deg,rgba(6,8,16,.95),transparent);pointer-events:none;}
#hud-score{font-family:'Orbitron',monospace;font-size:clamp(15px,4vw,22px);color:#fff;text-shadow:0 0 10px var(--neon);}
#hud-r{font-size:11px;color:rgba(255,255,255,.5);text-align:right;line-height:1.7;}
#cdot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--danger);margin-right:4px;transition:.3s;}
#cdot.on{background:var(--neon);box-shadow:0 0 6px var(--neon);}
#lb{position:absolute;top:56px;right:8px;background:rgba(6,8,16,.88);border:1px solid var(--border);
  border-radius:10px;padding:7px 11px;min-width:130px;pointer-events:none;backdrop-filter:blur(8px);}
#lb h3{font-family:'Orbitron',monospace;font-size:9px;color:var(--gold);letter-spacing:2px;margin-bottom:5px;}
.lbr{display:flex;justify-content:space-between;gap:10px;font-size:11px;color:rgba(255,255,255,.7);padding:2px 0;}
.lbr.me{color:var(--neon);font-weight:700;}
#chatbox{position:absolute;bottom:155px;left:8px;display:flex;flex-direction:column;gap:3px;pointer-events:none;max-width:220px;}
.cmsg{font-size:11px;color:#fff;background:rgba(0,0,0,.6);padding:3px 8px;border-radius:6px;
  border-left:2px solid var(--neon2);animation:fchat 4s forwards;}
@keyframes fchat{0%,80%{opacity:1;}100%{opacity:0;}}
#death{position:absolute;inset:0;display:none;align-items:center;justify-content:center;flex-direction:column;gap:10px;
  background:rgba(0,0,0,.72);backdrop-filter:blur(4px);}
#death.show{display:flex;}
#death h2{font-family:'Orbitron',monospace;font-size:clamp(22px,7vw,46px);color:var(--danger);
  text-shadow:0 0 20px var(--danger);animation:shk .4s;}
@keyframes shk{0%,100%{transform:translateX(0);}25%{transform:translateX(-8px);}75%{transform:translateX(8px);}}
#death p{color:rgba(255,255,255,.55);font-size:13px;letter-spacing:2px;}
#joy-outer{position:absolute;bottom:20px;left:20px;width:100px;height:100px;border-radius:50%;
  border:2px solid rgba(100,180,255,.3);background:rgba(20,40,80,.35);touch-action:none;}
#joy-knob{width:44px;height:44px;border-radius:50%;
  background:radial-gradient(circle at 35% 35%,rgba(255,255,255,.9),rgba(0,160,255,.9));
  box-shadow:0 2px 12px rgba(0,150,255,.6);position:absolute;top:50%;left:50%;
  transform:translate(-50%,-50%);pointer-events:none;}
#mmc{position:absolute;bottom:155px;right:8px;border-radius:50%;border:2px solid rgba(80,140,220,.6);pointer-events:none;}
#cinput-wrap{position:absolute;bottom:135px;left:50%;transform:translateX(-50%);
  display:none;background:rgba(6,8,16,.95);border:1px solid var(--neon2);
  border-radius:12px;padding:8px 12px;width:min(300px,88vw);flex-direction:row;gap:8px;align-items:center;}
#cinput-wrap.show{display:flex;}
#cinput{flex:1;background:none;border:none;outline:none;color:#fff;font-family:'Rajdhani',sans-serif;font-size:16px;}
#csend{background:var(--neon2);color:#000;border:none;border-radius:8px;padding:6px 12px;font-weight:700;cursor:pointer;}
#btn-chat{position:absolute;bottom:28px;right:18px;width:52px;height:52px;border-radius:50%;
  border:1px solid var(--neon2);background:rgba(0,200,255,.15);color:var(--neon2);
  font-size:20px;display:flex;align-items:center;justify-content:center;cursor:pointer;}
</style>
</head>
<body>
<div id="lobby">
  <h1>🐍 SNAKE 3D</h1>
  <p class="sub">ОНЛАЙН МУЛЬТИПЛЕЙЕР</p>
  <div class="igrp"><label>Таны нэр</label>
    <input id="inp-name" type="text" maxlength="16" placeholder="Нэрээ оруул..." autocomplete="off"></div>
  <div class="igrp"><label>Өрөөний нэр</label>
    <input id="inp-room" type="text" maxlength="20" value="lobby" autocomplete="off"></div>
  <div id="skin-row"></div>
  <button id="btn-join">▶ ТОГЛООМ ЭХЛЭХ</button>
  <p id="lob-err"></p>
</div>
<div id="game">
  <div id="cwrap">
    <canvas id="c"></canvas>
    <div id="hud">
      <div id="hud-score">⭐ 0</div>
      <div id="hud-r"><span id="cdot"></span><span id="ctxt">Холбогдож байна...</span><br><span id="hud-det"></span></div>
    </div>
    <div id="lb"><h3>🏆 ТОП</h3><div id="lb-list"></div></div>
    <div id="chatbox"></div>
    <div id="death"><h2>ҮХЛЭЭ!</h2><p>Автоматаар дахин төрнө...</p></div>
    <canvas id="mmc" width="88" height="88"></canvas>
    <div id="joy-outer"><div id="joy-knob"></div></div>
    <div id="cinput-wrap"><input id="cinput" type="text" maxlength="60" placeholder="Мессеж..."><button id="csend">➤</button></div>
    <div id="btn-chat">💬</div>
  </div>
</div>
<script>
const BLOCK=25,WORLD_W=3000,WORLD_H=3000,INTERP=0.16;
const WS_URL=(location.protocol==='https:'?'wss':'ws')+'://'+location.host.replace(/:\d+$/,'')+':__WS_PORT__';
const SKINS=[
  {name:"Ногоон",top:[0,210,80],   side:[0,140,50],  head:[0,255,120]},
  {name:"Цэнхэр",top:[30,120,255], side:[10,60,180], head:[100,180,255]},
  {name:"Алт",   top:[255,200,0],  side:[180,130,0], head:[255,230,80]},
  {name:"Гал",   top:[255,80,0],   side:[180,30,0],  head:[255,160,60]},
  {name:"Нил",   top:[180,0,255],  side:[100,0,180], head:[220,100,255]},
  {name:"Мөс",   top:[150,230,255],side:[80,160,200],head:[210,245,255]},
];
let selSkin=0;
function rgb(c){return`rgb(${c[0]},${c[1]},${c[2]})`;}
function drawPrev(cv,sk){
  const c=cv.getContext('2d'),s=cv.width/5|0;c.clearRect(0,0,cv.width,cv.height);
  for(let i=0;i<5;i++){
    const x=i*s,top=i===0?sk.head:sk.top,side=sk.side,d=Math.max(3,s/5|0);
    c.fillStyle=rgb(side);
    c.beginPath();c.moveTo(x+s-1,d);c.lineTo(x+s-1,s+d-1);c.lineTo(x+s-d,s-1);c.lineTo(x+s-d,0);c.fill();
    c.beginPath();c.moveTo(x+d,s+d-1);c.lineTo(x+s-1,s+d-1);c.lineTo(x+s-d,s-1);c.lineTo(x,s-1);c.fill();
    c.fillStyle=rgb(top);c.beginPath();c.roundRect(x,0,s-d,s-d,i===0?5:2);c.fill();
  }
}
const sr=document.getElementById('skin-row');
SKINS.forEach((sk,i)=>{
  const div=document.createElement('div');div.className='sk-card'+(i===0?' sel':'');
  const cv=document.createElement('canvas');cv.width=52;cv.height=12;drawPrev(cv,sk);
  const lbl=document.createElement('span');lbl.textContent=sk.name;
  div.appendChild(cv);div.appendChild(lbl);
  div.onclick=()=>{selSkin=i;document.querySelectorAll('.sk-card').forEach((d,j)=>d.classList.toggle('sel',j===i));};
  sr.appendChild(div);
});
const canvas=document.getElementById('c'),ctx=canvas.getContext('2d');
const mmc=document.getElementById('mmc'),mmctx=mmc.getContext('2d');
function resize(){const dpr=devicePixelRatio;canvas.width=canvas.offsetWidth*dpr;canvas.height=canvas.offsetHeight*dpr;ctx.scale(dpr,dpr);}
window.addEventListener('resize',resize);
const W=()=>canvas.offsetWidth,H=()=>canvas.offsetHeight;
let myId=null,gs={players:{},foods:[],leaderboard:[]},camX=0,camY=0,ws=null,prevScore=0,prevAlive=true,parts=[];
function connect(name,room){
  const err=document.getElementById('lob-err');
  err.textContent='Холбогдож байна...';err.style.color='#aaa';
  ws=new WebSocket(WS_URL);
  ws.onopen=()=>ws.send(JSON.stringify({type:'join',name,room,skin:SKINS[selSkin]}));
  ws.onmessage=e=>{
    const d=JSON.parse(e.data);
    if(d.type==='joined'){
      myId=d.id;
      document.getElementById('lobby').style.display='none';
      document.getElementById('game').classList.add('on');
      resize();requestAnimationFrame(loop);
      document.getElementById('cdot').classList.add('on');
      document.getElementById('ctxt').textContent='ОНЛАЙН • '+name;
    }else if(d.type==='state'){
      gs=d;const me=d.players[myId];
      if(me){
        if(me.score>prevScore){spawnP(me.body[0],[0,255,136],6);prevScore=me.score;}
        if(!me.alive&&prevAlive){prevAlive=false;document.getElementById('death').classList.add('show');}
        else if(me.alive&&!prevAlive){prevAlive=true;document.getElementById('death').classList.remove('show');}
      }
      updHUD();updLB();
    }else if(d.type==='chat'){addChat(d.name,d.msg);}
    else if(d.type==='error'){err.textContent='⚠️ '+d.msg;err.style.color='#ff3355';}
  };
  ws.onerror=()=>{err.textContent='❌ Сервертэй холбогдож чадсангүй!';err.style.color='#ff3355';};
  ws.onclose=()=>{document.getElementById('cdot').classList.remove('on');document.getElementById('ctxt').textContent='ТАСАРСАН';};
}
function sndDir(d){if(ws&&ws.readyState===1)ws.send(JSON.stringify({type:'dir',dir:d}));}
function sndChat(m){if(ws&&ws.readyState===1&&m.trim())ws.send(JSON.stringify({type:'chat',msg:m}));}
function updHUD(){const me=gs.players[myId];if(!me)return;
  document.getElementById('hud-score').textContent='⭐ '+me.score;
  document.getElementById('hud-det').textContent=`Урт:${me.body.length}  Алсан:${me.kills}  👥${Object.keys(gs.players).length}`;}
function updLB(){document.getElementById('lb-list').innerHTML=
  (gs.leaderboard||[]).slice(0,8).map((e,i)=>`<div class="lbr${e.id===myId?' me':''}"><span>${i+1}. ${e.name.slice(0,10)}</span><span>${e.score}</span></div>`).join('');}
function addChat(name,msg){
  const b=document.getElementById('chatbox'),el=document.createElement('div');
  el.className='cmsg';el.textContent=`${name}: ${msg}`;b.appendChild(el);
  setTimeout(()=>el.remove(),4200);while(b.children.length>5)b.removeChild(b.firstChild);}
function updCam(hx,hy){
  const tx=Math.max(0,Math.min(hx-W()/2,WORLD_W-W()));
  const ty=Math.max(0,Math.min(hy-H()/2,WORLD_H-H()));
  camX+=(tx-camX)*INTERP;camY+=(ty-camY)*INTERP;}
function w2s(wx,wy){return[wx-camX,wy-camY];}
function onSc(wx,wy){const[sx,sy]=w2s(wx,wy);return sx>-BLOCK*2&&sx<W()+BLOCK*2&&sy>-BLOCK*2&&sy<H()+BLOCK*2;}
const bcache={};
function draw3D(x,y,top,side,size,isHead,dir){
  const key=`${top}|${side}|${size}|${isHead}|${dir}`;
  let s=bcache[key];
  if(!s){
    const d=Math.max(4,size/5|0),oc=document.createElement('canvas');
    oc.width=size+d;oc.height=size+d;const c2=oc.getContext('2d');
    const[sr2,sg,sb]=side,shad=`rgb(${Math.max(0,sr2-40)},${Math.max(0,sg-40)},${Math.max(0,sb-40)})`;
    c2.fillStyle=shad;
    c2.beginPath();c2.moveTo(size,d);c2.lineTo(size,size+d);c2.lineTo(size-d,size);c2.lineTo(size-d,0);c2.fill();
    c2.beginPath();c2.moveTo(d,size+d);c2.lineTo(size,size+d);c2.lineTo(size-d,size);c2.lineTo(0,size);c2.fill();
    c2.fillStyle=rgb(side);
    c2.beginPath();c2.moveTo(size-1,d);c2.lineTo(size-1,size+d-1);c2.lineTo(size-d,size-1);c2.lineTo(size-d,0);c2.fill();
    c2.beginPath();c2.moveTo(d,size+d-1);c2.lineTo(size-1,size+d-1);c2.lineTo(size-d,size-1);c2.lineTo(0,size-1);c2.fill();
    const[tr,tg,tb]=top;c2.fillStyle=rgb(top);c2.beginPath();c2.roundRect(0,0,size-d,size-d,isHead?6:3);c2.fill();
    c2.fillStyle=`rgba(${Math.min(255,tr+60)},${Math.min(255,tg+60)},${Math.min(255,tb+60)},.7)`;
    c2.beginPath();c2.roundRect(2,2,size-d-8,4,2);c2.fill();
    if(isHead&&dir){
      const[dx,dy]=dir,sz2=size-d;let e1,e2;
      if(dx>0){e1=[sz2-7,5];e2=[sz2-7,sz2-11];}else if(dx<0){e1=[4,5];e2=[4,sz2-11];}
      else if(dy>0){e1=[5,sz2-7];e2=[sz2-11,sz2-7];}else{e1=[5,4];e2=[sz2-11,4];}
      [[255,255,255,5],[20,20,50,3]].forEach(([r2,g2,b2,rad])=>{
        c2.fillStyle=`rgb(${r2},${g2},${b2})`;
        c2.beginPath();c2.arc(e1[0],e1[1],rad,0,Math.PI*2);c2.fill();
        c2.beginPath();c2.arc(e2[0],e2[1],rad,0,Math.PI*2);c2.fill();
      });
    }
    s=oc;bcache[key]=s;
  }
  ctx.drawImage(s,x,y);
}
function drawFood(f){
  const[sx,sy]=w2s(f.pos[0],f.pos[1]);if(!onSc(f.pos[0],f.pos[1]))return;
  const c=f.type.color,cx=sx+BLOCK/2,cy=sy+BLOCK/2,r=BLOCK/2-2;
  ctx.fillStyle=rgb(c);ctx.beginPath();ctx.arc(cx,cy,Math.max(4,r),0,Math.PI*2);ctx.fill();
  ctx.fillStyle='rgba(0,0,0,.3)';ctx.beginPath();ctx.arc(cx+2,cy+2,Math.max(2,r-3),0,Math.PI*2);ctx.fill();
  ctx.fillStyle='rgba(255,255,255,.7)';ctx.beginPath();ctx.arc(cx-r/3,cy-r/3,Math.max(2,r/3),0,Math.PI*2);ctx.fill();
  if(f.type.pts>=2){ctx.fillStyle='#fff';ctx.font='bold 10px Orbitron';ctx.fillText(`+${f.type.pts}`,sx,sy-2);}
}
function spawnP([wx,wy],color,count){
  const[sx,sy]=w2s(wx,wy);
  for(let i=0;i<count;i++){const a=Math.random()*Math.PI*2,sp=2+Math.random()*4;
    parts.push({x:sx,y:sy,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp,life:15+Math.random()*20|0,color,size:2+Math.random()*3|0});}
}
function updParts(){parts=parts.filter(p=>{
  p.x+=p.vx;p.y+=p.vy;p.vy+=.15;p.vx*=.92;p.vy*=.92;p.life--;if(p.life<=0)return false;
  ctx.globalAlpha=p.life/30;ctx.fillStyle=rgb(p.color);ctx.beginPath();ctx.arc(p.x,p.y,p.size,0,Math.PI*2);ctx.fill();
  ctx.globalAlpha=1;return true;});}
let mmf=0;
function drawMM(){mmf++;if(mmf%3!==0)return;
  const me=gs.players[myId];if(!me||!me.body.length)return;
  const[hx,hy]=me.body[0],R=44,VIEW=BLOCK*32;
  mmctx.clearRect(0,0,88,88);mmctx.save();
  mmctx.beginPath();mmctx.arc(R,R,R,0,Math.PI*2);mmctx.clip();
  mmctx.fillStyle='rgba(5,10,25,.9)';mmctx.fillRect(0,0,88,88);
  const tm=(wx,wy)=>[R+(wx-hx)/VIEW*R,R+(wy-hy)/VIEW*R];
  const ic=(x,y)=>Math.hypot(x-R,y-R)<R-3;
  gs.foods.forEach(f=>{const[mx,my]=tm(f.pos[0],f.pos[1]);if(!ic(mx,my))return;
    mmctx.fillStyle=`rgba(${f.type.color[0]},${f.type.color[1]},${f.type.color[2]},.8)`;
    mmctx.beginPath();mmctx.arc(mx,my,3,0,Math.PI*2);mmctx.fill();});
  Object.entries(gs.players).forEach(([pid,p])=>{
    if(!p.alive||!p.body.length)return;const[mx,my]=tm(p.body[0][0],p.body[0][1]);if(!ic(mx,my))return;
    const isMe=String(myId)===pid,sk=p.skin;
    mmctx.fillStyle=isMe?'#00ff88':rgb(sk.head);
    mmctx.beginPath();mmctx.arc(mx,my,isMe?7:5,0,Math.PI*2);mmctx.fill();});
  mmctx.restore();}
function drawGrid(){const ox=camX%BLOCK,oy=camY%BLOCK;
  ctx.strokeStyle='rgba(20,25,45,1)';ctx.lineWidth=1;
  for(let x=-ox;x<W();x+=BLOCK){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H());ctx.stroke();}
  for(let y=-oy;y<H();y+=BLOCK){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W(),y);ctx.stroke();}}
function loop(){
  ctx.fillStyle='#060810';ctx.fillRect(0,0,W(),H());
  const me=gs.players[myId];if(me&&me.body.length)updCam(me.body[0][0],me.body[0][1]);
  drawGrid();
  ctx.strokeStyle='#ff3355';ctx.lineWidth=3;
  const[lx]=w2s(0,0),[rx]=w2s(WORLD_W,0),[,ty]=w2s(0,0),[,by]=w2s(0,WORLD_H);
  [[lx,0,lx,H()],[rx,0,rx,H()],[0,ty,W(),ty],[0,by,W(),by]].forEach(([x1,y1,x2,y2])=>{
    const lo=Math.min(x1,x2),hi=Math.max(x1,x2),lt=Math.min(y1,y2),ht=Math.max(y1,y2);
    if(lo>-5&&lo<W()+5||lt>-5&&lt<H()+5){ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();}});
  gs.foods.forEach(drawFood);
  ctx.font='bold 11px Rajdhani';
  Object.entries(gs.players).forEach(([pid,p])=>{
    if(!p.alive||!p.body.length)return;const sk=p.skin;
    p.body.forEach((blk,i)=>{if(!onSc(blk[0],blk[1]))return;
      const[sx,sy]=w2s(blk[0],blk[1]);draw3D(sx,sy,i===0?sk.head:sk.top,sk.side,BLOCK,i===0,i===0?p.dir:null);});
    if(p.body.length){const[sx,sy]=w2s(p.body[0][0],p.body[0][1]);
      if(sx>0&&sx<W()&&sy>0&&sy<H()){ctx.fillStyle=String(myId)===pid?'#00ff88':'rgba(255,255,255,.85)';
        ctx.textAlign='center';ctx.fillText(p.name,sx+BLOCK/2,sy-5);ctx.textAlign='left';}}});
  updParts();drawMM();requestAnimationFrame(loop);}
const jo=document.getElementById('joy-outer'),jk=document.getElementById('joy-knob');
let jActive=false,jBX=0,jBY=0,lastD=null;
jo.addEventListener('touchstart',e=>{e.preventDefault();const t=e.touches[0],r=jo.getBoundingClientRect();
  jBX=r.left+r.width/2;jBY=r.top+r.height/2;jActive=true;mvJoy(t.clientX,t.clientY);},{passive:false});
jo.addEventListener('touchmove',e=>{e.preventDefault();mvJoy(e.touches[0].clientX,e.touches[0].clientY);},{passive:false});
jo.addEventListener('touchend',e=>{e.preventDefault();jActive=false;lastD=null;jk.style.transform='translate(-50%,-50%)';},{passive:false});
function mvJoy(cx,cy){const dx=cx-jBX,dy=cy-jBY,dist=Math.hypot(dx,dy),maxR=40;
  const ox=dist>maxR?dx/dist*maxR:dx,oy=dist>maxR?dy/dist*maxR:dy;
  jk.style.transform=`translate(calc(-50% + ${ox}px),calc(-50% + ${oy}px))`;if(dist<8)return;
  const d=Math.abs(dx)>=Math.abs(dy)?(dx>0?[BLOCK,0]:[-BLOCK,0]):(dy>0?[0,BLOCK]:[0,-BLOCK]);
  if(!lastD||d[0]!==lastD[0]||d[1]!==lastD[1]){lastD=d;sndDir(d);}}
document.addEventListener('keydown',e=>{
  const m={ArrowUp:[0,-BLOCK],ArrowDown:[0,BLOCK],ArrowLeft:[-BLOCK,0],ArrowRight:[BLOCK,0],
           w:[0,-BLOCK],s:[0,BLOCK],a:[-BLOCK,0],d:[BLOCK,0]};if(m[e.key])sndDir(m[e.key]);});
document.getElementById('btn-chat').addEventListener('click',()=>{
  document.getElementById('cinput-wrap').classList.toggle('show');
  if(document.getElementById('cinput-wrap').classList.contains('show'))document.getElementById('cinput').focus();});
document.getElementById('csend').addEventListener('click',()=>{
  const i=document.getElementById('cinput');sndChat(i.value);i.value='';
  document.getElementById('cinput-wrap').classList.remove('show');});
document.getElementById('cinput').addEventListener('keydown',e=>{
  if(e.key==='Enter'){sndChat(e.target.value);e.target.value='';
    document.getElementById('cinput-wrap').classList.remove('show');}});
document.getElementById('btn-join').addEventListener('click',()=>{
  const name=document.getElementById('inp-name').value.trim();
  const room=document.getElementById('inp-room').value.trim()||'lobby';
  if(!name){document.getElementById('lob-err').textContent='Нэрээ оруул!';return;}
  connect(name,room);});
document.getElementById('inp-name').addEventListener('keydown',e=>{
  if(e.key==='Enter')document.getElementById('btn-join').click();});
</script>
</body>
</html>"""

# =============================================
# GAME SERVER LOGIC
# =============================================
rooms = {}

class Room:
    def __init__(self, room_id):
        self.room_id=room_id; self.players={}; self.foods=[]; self.task=None; self.color_idx=0
        self._spawn_foods(FOOD_COUNT)
    def _rand_pos(self):
        return[random.randrange(BLOCK,WORLD_W-BLOCK*2,BLOCK),random.randrange(BLOCK,WORLD_H-BLOCK*2,BLOCK)]
    def _spawn_foods(self,n):
        taken={tuple(b) for p in self.players.values() for b in p["body"]}
        taken|={tuple(f["pos"]) for f in self.foods}
        for _ in range(n):
            for _ in range(200):
                pos=self._rand_pos()
                if tuple(pos) not in taken: break
            ft=random.choices(FOOD_TYPES,weights=[f["w"] for f in FOOD_TYPES])[0]
            self.foods.append({"pos":pos,"type":ft}); taken.add(tuple(pos))
    def add_player(self,ws,name,skin=None):
        sx=(WORLD_W//2//BLOCK)*BLOCK+random.randint(-10,10)*BLOCK
        sy=(WORLD_H//2//BLOCK)*BLOCK+random.randint(-10,10)*BLOCK
        color=skin if skin else PLAYER_COLORS[self.color_idx%len(PLAYER_COLORS)]
        self.color_idx+=1
        p={"id":id(ws),"name":name[:16],"body":[[sx,sy],[sx-BLOCK,sy],[sx-BLOCK*2,sy]],
           "dir":[BLOCK,0],"next_dir":[BLOCK,0],"alive":True,"score":0,
           "kills":0,"coins":0,"skin":color,"respawn_timer":0}
        self.players[ws]=p; return p
    def remove_player(self,ws): self.players.pop(ws,None)
    def set_dir(self,ws,d):
        p=self.players.get(ws)
        if not p or not p["alive"]: return
        cur=p["dir"]
        if d==[BLOCK,0]  and cur!=[-BLOCK,0]: p["next_dir"]=d
        if d==[-BLOCK,0] and cur!=[BLOCK,0]:  p["next_dir"]=d
        if d==[0,BLOCK]  and cur!=[0,-BLOCK]: p["next_dir"]=d
        if d==[0,-BLOCK] and cur!=[0,BLOCK]:  p["next_dir"]=d
    def _move_all(self):
        for ws,p in list(self.players.items()):
            if not p["alive"]:
                p["respawn_timer"]+=1
                if p["respawn_timer"]>50:
                    sx=random.randrange(BLOCK,WORLD_W-BLOCK*2,BLOCK)
                    sy=random.randrange(BLOCK,WORLD_H-BLOCK*2,BLOCK)
                    p["body"]=[[sx,sy],[sx-BLOCK,sy]]; p["dir"]=[BLOCK,0]
                    p["next_dir"]=[BLOCK,0]; p["alive"]=True; p["respawn_timer"]=0
                continue
            p["dir"]=p["next_dir"][:]
            head=p["body"][0]; nh=[head[0]+p["dir"][0],head[1]+p["dir"][1]]
            if nh[0]<0 or nh[0]>=WORLD_W or nh[1]<0 or nh[1]>=WORLD_H:
                p["alive"]=False; p["respawn_timer"]=0; continue
            p["body"].insert(0,nh)
            ate=False
            for f in self.foods[:]:
                if abs(nh[0]-f["pos"][0])<BLOCK and abs(nh[1]-f["pos"][1])<BLOCK:
                    p["score"]+=f["type"]["pts"]; p["coins"]+=f["type"]["coins"]
                    self.foods.remove(f); self._spawn_foods(1); ate=True; break
            if not ate: p["body"].pop()
    def _check_collisions(self):
        alive=[(ws,p) for ws,p in self.players.items() if p["alive"]]
        for ws1,p1 in alive:
            head=p1["body"][0]
            if head in p1["body"][1:]: p1["alive"]=False; p1["respawn_timer"]=0; continue
            for ws2,p2 in alive:
                if ws1==ws2: continue
                if head in p2["body"][1:]:
                    if len(p1["body"])<=len(p2["body"]):
                        p1["alive"]=False; p1["respawn_timer"]=0
                        p2["score"]+=p1["score"]//2+3; p2["kills"]+=1
                    break
            for ws2,p2 in alive:
                if ws1>=ws2: continue
                if p1["body"][0]==p2["body"][0]:
                    if len(p1["body"])>=len(p2["body"]):
                        p2["alive"]=False; p2["respawn_timer"]=0
                        p1["score"]+=p2["score"]//2+5; p1["kills"]+=1
                    else:
                        p1["alive"]=False; p1["respawn_timer"]=0
                        p2["score"]+=p1["score"]//2+5; p2["kills"]+=1
    def get_state(self):
        lb=sorted([{"id":p["id"],"name":p["name"],"score":p["score"],"kills":p["kills"],"alive":p["alive"]}
                   for p in self.players.values()],key=lambda x:x["score"],reverse=True)[:10]
        return{"type":"state",
               "players":{str(p["id"]):{"id":p["id"],"name":p["name"],"body":p["body"],"dir":p["dir"],
                          "alive":p["alive"],"score":p["score"],"kills":p["kills"],"skin":p["skin"]}
                          for p in self.players.values()},
               "foods":self.foods,"leaderboard":lb}
    async def game_loop(self):
        while self.players:
            t0=time.time(); self._move_all(); self._check_collisions()
            while len(self.foods)<FOOD_COUNT: self._spawn_foods(1)
            msg=json.dumps(self.get_state()); dead=[]
            for ws in list(self.players):
                try: await ws.send(msg)
                except: dead.append(ws)
            for ws in dead: self.remove_player(ws)
            await asyncio.sleep(max(0,TICK-(time.time()-t0)))
        rooms.pop(self.room_id,None)

async def ws_handler(ws):
    room_id=None; joined=False
    try:
        raw=await asyncio.wait_for(ws.recv(),timeout=15)
        msg=json.loads(raw)
        if msg.get("type")!="join":
            await ws.send(json.dumps({"type":"error","msg":"join мессеж илгээ"})); return
        name=str(msg.get("name","Тоглогч"))[:16]
        room_id=str(msg.get("room","lobby"))[:20]
        skin=msg.get("skin",None)
        if room_id not in rooms:
            if len(rooms)>=MAX_ROOMS:
                await ws.send(json.dumps({"type":"error","msg":"Өрөө дүүрсэн"})); return
            rooms[room_id]=Room(room_id)
        room=rooms[room_id]
        if len(room.players)>=MAX_PLAYERS:
            await ws.send(json.dumps({"type":"error","msg":"Өрөө дүүрсэн (max 16)"})); return
        player=room.add_player(ws,name,skin)
        joined=True
        await ws.send(json.dumps({"type":"joined","id":player["id"],"room":room_id,"name":name}))
        if room.task is None or room.task.done():
            room.task=asyncio.create_task(room.game_loop())
        async for raw2 in ws:
            try:
                m2=json.loads(raw2)
                if m2.get("type")=="dir": room.set_dir(ws,m2["dir"])
                elif m2.get("type")=="chat":
                    out=json.dumps({"type":"chat","name":name,"msg":str(m2.get("msg",""))[:100]})
                    for ows in list(room.players):
                        try: await ows.send(out)
                        except: pass
            except: pass
    except: pass
    finally:
        if joined and room_id and room_id in rooms:
            rooms[room_id].remove_player(ws)

# =============================================
# HTTP SERVER (HTML serve хийнэ)
# =============================================
async def http_handler(reader, writer):
    try:
        data = await reader.read(1024)
        html = HTML.replace("__WS_PORT__", str(PORT_WS))
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            f"Content-Length: {len(html.encode())}\r\n"
            "Connection: close\r\n\r\n"
        )
        writer.write(response.encode() + html.encode())
        await writer.drain()
    except: pass
    finally:
        writer.close()

# =============================================
# ЭХЛҮҮЛЭХ
# =============================================
async def main():
    http_srv = await asyncio.start_server(http_handler, HOST, PORT_HTTP)
    ws_srv   = await websockets.serve(ws_handler, HOST, PORT_WS)
    print(f"🐍 Snake 3D нэг файлаар ажиллаж байна!")
    print(f"   🌐 Браузер:   http://localhost:{PORT_HTTP}")
    print(f"   📡 WebSocket: ws://localhost:{PORT_WS}")
    print(f"   Гарахын тулд Ctrl+C дар")
    async with ws_srv:
        await asyncio.gather(http_srv.serve_forever(), asyncio.Future())

if __name__=="__main__":
    asyncio.run(main())
