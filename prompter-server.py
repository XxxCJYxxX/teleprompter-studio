#!/usr/bin/env python3
"""
提词器内网服务端 · Teleprompter LAN Server
===========================================
零依赖，Python 3 原生模块。
启动后在平板上打开本机 IP:8080 即可作为提词器客户端，
笔记本打开 /admin 编辑内容。

Usage:
    python3 prompter-server.py          # 默认端口 8080
    python3 prompter-server.py 9090     # 自定义端口
"""

import http.server
import json
import os
import socket
import socketserver
import sys
import threading
import time
import urllib.parse

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
HOST = '0.0.0.0'

state = {'content': '', 'version': 0, 'updated_at': time.time()}
state_lock = threading.Lock()

def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

# ═══════════════════════════════════════════════════════════════
#  CLIENT HTML
# ═══════════════════════════════════════════════════════════════

CLIENT_HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>提词器 · 客户端</title>
<style>
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
  :root{
    --bg:#0a0a0a;--text:#e8e6dd;--accent:#d4a853;
    --accent-dim:rgba(212,168,83,0.4);--panel-bg:rgba(20,20,24,0.94);
    --fs:48px;--lh:1.55;--ff:system-ui,-apple-system,'PingFang SC',sans-serif;
  }
  body{
    background:var(--bg);color:var(--text);
    font-family:var(--ff);overflow:hidden;
    height:100vh;height:100dvh;
    touch-action:none;-webkit-user-select:none;user-select:none;
  }
  #stage{position:fixed;inset:0;overflow:hidden}
  #stage.mirrored{transform:scaleX(-1)}
  #text-wrap{position:absolute;left:0;right:0;top:0;padding:50vh 0 60vh;transform:translateY(0px);will-change:transform}
  #text-content{
    width:min(90vw,900px);margin:0 auto;
    font-size:var(--fs);line-height:var(--lh);text-align:center;color:var(--text);
    white-space:pre-wrap;word-break:break-word;letter-spacing:.01em;
    transition:font-size .3s,line-height .3s;
  }
  #text-content p{min-height:calc(var(--fs)*var(--lh))}
  #fade-top,#fade-bottom{position:fixed;left:0;right:0;pointer-events:none;z-index:5}
  #fade-top{top:0;height:20vh;background:linear-gradient(to bottom,var(--bg),transparent)}
  #fade-bottom{bottom:0;height:20vh;background:linear-gradient(to top,var(--bg),transparent)}
  #guide{
    position:fixed;left:8%;right:8%;top:50%;height:1px;
    background:linear-gradient(90deg,transparent,var(--accent-dim) 20%,var(--accent-dim) 80%,transparent);
    pointer-events:none;z-index:4;
  }
  #guide::after{
    content:'';position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
    width:6px;height:6px;background:var(--accent);border-radius:50%;
  }

  /* Top bar */
  #top-bar{
    position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:50;
    display:flex;gap:6px;align-items:center;
    background:var(--panel-bg);border:1px solid rgba(255,255,255,.08);
    border-radius:20px;padding:6px 12px;font-size:11px;color:#999;
    backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);transition:opacity .4s;
  }
  #top-bar .dot{width:7px;height:7px;border-radius:50%;background:#4caf50;flex-shrink:0}
  #top-bar .dot.stale{background:#ff9800}

  #top-bar button,#bottom-bar button{
    background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);
    color:#ccc;border-radius:12px;padding:4px 10px;font-size:11px;
    font-family:inherit;cursor:pointer;white-space:nowrap;touch-action:manipulation;
  }
  #top-bar button:hover,#bottom-bar button:hover{background:rgba(255,255,255,.14)}
  #top-bar button.active,#bottom-bar button.active{background:rgba(212,168,83,.2);border-color:var(--accent);color:var(--accent)}
  #top-bar button.accent,#bottom-bar button.accent{border-color:var(--accent);color:var(--accent)}

  /* Bottom bar */
  #bottom-bar{
    position:fixed;bottom:16px;left:50%;transform:translateX(-50%);z-index:50;
    display:flex;gap:10px;align-items:center;
    background:var(--panel-bg);border:1px solid rgba(255,255,255,.08);
    border-radius:24px;padding:8px 14px;
    backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);transition:opacity .4s;
  }
  #btn-play{font-size:15px;font-weight:600;padding:8px 16px;border-radius:14px;flex-shrink:0}
  #btn-reset{font-size:16px;padding:6px 10px;flex-shrink:0}

  /* Speed picker - momentum scroll */
  #spd-wrap{position:relative;display:flex;align-items:center;overflow:hidden;width:200px;height:48px}
  #spd-wrap::before,#spd-wrap::after{
    content:'';position:absolute;top:0;bottom:0;width:70px;z-index:2;pointer-events:none;
  }
  #spd-wrap::before{left:0;background:linear-gradient(to right,var(--panel-bg),transparent)}
  #spd-wrap::after{right:0;background:linear-gradient(to left,var(--panel-bg),transparent)}
  #spd-indicator{
    position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
    width:54px;height:40px;border:2px solid var(--accent);border-radius:10px;
    pointer-events:none;z-index:1;
  }
  #spd-track{
    display:flex;align-items:center;gap:0;
    will-change:transform;cursor:grab;z-index:3;
  }
  #spd-track:active{cursor:grabbing}
  .spd-item{
    flex-shrink:0;width:56px;text-align:center;
    font-size:13px;color:#555;font-weight:500;
    padding:8px 0;cursor:pointer;user-select:none;
    -webkit-user-select:none;transition:color .15s,font-size .15s;
  }
  .spd-item.active{color:var(--accent);font-size:20px;font-weight:700}

  /* UI visibility */
  body.fs-hide-ui #top-bar,body.fs-hide-ui #bottom-bar{opacity:0;pointer-events:none}
  body.fs-hide-ui #fs-hint{opacity:.3}
  #fs-hint{
    position:fixed;bottom:40px;left:50%;transform:translateX(-50%);z-index:40;
    font-size:11px;color:rgba(255,255,255,.2);pointer-events:none;transition:opacity .8s;
  }
  .tag{font-size:10px;color:var(--accent);font-variant-numeric:tabular-nums}
  #conn-lost{
    display:none;position:fixed;top:10px;left:50%;transform:translateX(-50%);
    background:#c62828;color:#fff;padding:6px 16px;border-radius:14px;font-size:12px;z-index:60;
  }
  #conn-lost.show{display:block}

  @media(max-width:600px){
    :root{--fs:36px}
    #bottom-bar{padding:6px 10px;gap:6px;border-radius:18px}
    #spd-wrap{width:150px;height:40px}
    .spd-item{width:46px;font-size:11px}
    .spd-item.active{font-size:17px}
    #spd-indicator{width:46px;height:34px}
    #top-bar{font-size:10px;padding:4px 8px}
  }
</style>
</head>
<body>

<div id="stage"><div id="text-wrap"><div id="text-content"><p>等待管理端推送内容…</p></div></div></div>
<div id="fade-top"></div><div id="fade-bottom"></div><div id="guide"></div>
<div id="conn-lost">⚠ 连接中断，正在重连…</div>

<div id="top-bar">
  <div class="dot" id="conn-dot"></div>
  <span id="ver-tag">v0</span>
  <span class="tag" id="prog-tag">--</span>
  <button id="btn-fs" class="accent">⛶ 全屏</button>
  <button id="btn-mirror">🪞</button>
  <button id="btn-smaller">A-</button>
  <button id="btn-bigger">A+</button>
  <button id="btn-font">字体</button>
  <button id="btn-lh">行距</button>
</div>

<div id="bottom-bar">
  <button id="btn-play">▶ 播放</button>
  <div id="spd-wrap">
    <div id="spd-indicator"></div>
    <div id="spd-track"></div>
  </div>
  <button id="btn-reset" title="回到开头">↩</button>
</div>

<div id="fs-hint">轻触暂停 · 拖动回溯 · 翻动选速度</div>

<script>
(function(){
var $=function(id){return document.getElementById(id)};
var STEPS=[10,15,20,25,30,35,40,45,50,55,60,65,70,80,90,100];
var FONTS=[
  "system-ui,-apple-system,'PingFang SC',sans-serif",
  "'Noto Serif SC',Georgia,'Songti SC',serif",
  "'SF Mono','Fira Code','Consolas',monospace"
];
var LHEIGHTS=[1.35,1.55,1.85,2.2];
var LH_LABELS=['紧凑','标准','宽松','极宽'];

var content='',serverVer=-1,scrollY=0,totalH=0;
var speed=40,fsize=48,fidx=0,lidx=1;
var isPlay=false,isMir=false,isFS=false;
var af=null,lt=0,uiT=null;
var tsY=0,tsSY=0,tsOn=false,tsMv=false;
var pollT=null,recon=0;

var stage=$('stage'),tw=$('text-wrap'),tc=$('text-content');
var btnPlay=$('btn-play'),btnFS=$('btn-fs'),btnMir=$('btn-mirror');
var spdWrap=$('spd-wrap'),spdTrack=$('spd-track');
var progTag=$('prog-tag'),verTag=$('ver-tag');
var connDot=$('conn-dot'),connLost=$('conn-lost'),fsHint=$('fs-hint');

// ═══════════════════════════════════════════════════════
//  MOMENTUM SPEED PICKER
// ═══════════════════════════════════════════════════════
var currIdx=STEPS.indexOf(speed),trackX=0,trackW=0;
var vel=0,trk=false,sx=0,spx=0,st=0,lx=0,lt2=0,tid=null;

function buildPicker(){
  spdTrack.innerHTML='';
  STEPS.forEach(function(v,i){
    var d=document.createElement('div');
    d.className='spd-item';
    d.textContent=v;d.dataset.idx=i;
    spdTrack.appendChild(d);
  });
  trackW=STEPS.length*56;
  // Center first item
  var halfWrap=spdWrap.offsetWidth/2;
  trackX=halfWrap-28-currIdx*56;
  updateTrack(false);
}

function updateTrack(anim){
  spdTrack.style.transition=anim?'transform .25s cubic-bezier(.25,.8,.25,1.3)':'none';
  spdTrack.style.transform='translateX('+trackX+'px)';
  // Find nearest to center
  var cx=-trackX+spdWrap.offsetWidth/2;
  var ni=Math.round((cx-28)/56);
  ni=Math.max(0,Math.min(STEPS.length-1,ni));
  if(ni!==currIdx){
    currIdx=ni;speed=STEPS[ni];
    var items=spdTrack.querySelectorAll('.spd-item');
    items.forEach(function(el,i){el.classList.toggle('active',i===currIdx)});
  }
}

function snapTo(idx){
  currIdx=Math.max(0,Math.min(STEPS.length-1,idx));
  speed=STEPS[currIdx];
  var halfWrap=spdWrap.offsetWidth/2;
  trackX=halfWrap-28-currIdx*56;vel=0;
  updateTrack(true);
  var items=spdTrack.querySelectorAll('.spd-item');
  items.forEach(function(el,i){el.classList.toggle('active',i===currIdx)});
}

// Touch handlers
spdTrack.addEventListener('touchstart',function(e){
  e.preventDefault();
  trk=true;vel=0;tsMv=false;
  sx=e.touches[0].clientX;spx=trackX;
  lx=sx;lt2=Date.now();
  cancelTween();
  updateTrack(false);
},{passive:false});

spdTrack.addEventListener('touchmove',function(e){
  if(!trk)return;e.preventDefault();
  var x=e.touches[0].clientX;
  var dx=x-sx;
  if(Math.abs(dx)>3)tsMv=true;
  var now=Date.now(),dt=now-lt2;
  if(dt>0)vel=(x-lx)/dt*16.67;
  lx=x;lt2=now;
  trackX=spx+dx;
  clampX();
  updateTrack(false);
},{passive:false});

spdTrack.addEventListener('touchend',function(){
  if(!trk)return;trk=false;
  if(!tsMv){snapTo(currIdx);return}
  startMomentum();
});

// Mouse
spdTrack.addEventListener('mousedown',function(e){
  e.preventDefault();
  trk=true;vel=0;tsMv=false;
  sx=e.clientX;spx=trackX;
  lx=sx;lt2=Date.now();
  cancelTween();
  updateTrack(false);
});

window.addEventListener('mousemove',function(e){
  if(!trk)return;
  var dx=e.clientX-sx;
  if(Math.abs(dx)>3)tsMv=true;
  var now=Date.now(),dt=now-lt2;
  if(dt>0)vel=(e.clientX-lx)/dt*16.67;
  lx=e.clientX;lt2=now;
  trackX=spx+dx;
  clampX();
  updateTrack(false);
});

window.addEventListener('mouseup',function(){
  if(!trk)return;trk=false;
  if(!tsMv){snapTo(currIdx);return}
  startMomentum();
});

// Wheel (scroll wheel support for desktop)
spdWrap.addEventListener('wheel',function(e){
  e.preventDefault();
  cancelTween();
  trackX-=e.deltaY*0.5;
  clampX();
  updateTrack(false);
  debounceSnap();
},{passive:false});

var snapTmr=null;
function debounceSnap(){
  clearTimeout(snapTmr);
  snapTmr=setTimeout(function(){snapTo(currIdx)},150);
}

function clampX(){
  var halfWrap=spdWrap.offsetWidth/2;
  var maxX=halfWrap-28;
  var minX=-(STEPS.length*56-halfWrap+28);
  // Allow some overscroll
  if(trackX>maxX+40)trackX=maxX+40;
  else if(trackX<minX-40)trackX=minX-40;
}

function startMomentum(){
  var tVel=vel,fric=.945,minV=.15;
  function anim(){
    if(trk)return;
    trackX+=tVel;
    tVel*=fric;
    // Bounce at bounds
    var halfWrap=spdWrap.offsetWidth/2,maxX=halfWrap-28,minX=-(STEPS.length*56-halfWrap+28);
    if(trackX>maxX){trackX=maxX;tVel*=-.3}
    else if(trackX<minX){trackX=minX;tVel*=-.3}
    updateTrack(false);
    if(Math.abs(tVel)<minV){snapTo(currIdx);return}
    tid=requestAnimationFrame(anim);
  }
  tid=requestAnimationFrame(anim);
}

function cancelTween(){
  if(tid){cancelAnimationFrame(tid);tid=null}
}

// Click on individual speed items
spdTrack.addEventListener('click',function(e){
  if(tsMv)return;
  var el=e.target.closest('.spd-item');
  if(!el)return;
  snapTo(parseInt(el.dataset.idx));
});

// ═══════════════════════════════════════════════════════
//  TEXT RENDERING
// ═══════════════════════════════════════════════════════
function renderText(txt){
  content=txt||' ';
  var h=content.split('\n').map(function(l){
    var t=l.trim();if(!t)return'<p></p>';
    t=t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    t=t.replace(/\*\*(.+?)\*\*/g,'<b>$1</b>').replace(/\*(.+?)\*/g,'<i>$1</i>');
    return'<p>'+t+'</p>';
  }).join('\n');
  tc.innerHTML=h;calcTH();updProg();
}
function calcTH(){totalH=Math.max(0,tc.scrollHeight-window.innerHeight*.3)}
function applyVars(){
  document.documentElement.style.setProperty('--fs',fsize+'px');
  document.documentElement.style.setProperty('--lh',LHEIGHTS[lidx]);
  document.documentElement.style.setProperty('--ff',FONTS[fidx]);
}

// ═══════════════════════════════════════════════════════
//  SCROLL LOOP
// ═══════════════════════════════════════════════════════
function startA(){
  if(af)return;if(scrollY>=totalH){scrollY=0;updPos()}
  isPlay=true;lt=performance.now();
  btnPlay.textContent='⏸ 暂停';btnPlay.classList.add('active');loop();
}
function pauseA(){
  isPlay=false;if(af){cancelAnimationFrame(af);af=null}
  btnPlay.textContent='▶ 播放';btnPlay.classList.remove('active');
}
function stopA(){pauseA();scrollY=0;updPos();updProg()}
function loop(ts){
  if(!ts)ts=performance.now();
  var dt=Math.min((ts-lt)/1000,.1);lt=ts;
  scrollY+=speed*2.2*dt;
  if(Math.floor(ts/500)!==Math.floor((ts-dt*1000)/500))calcTH();
  if(scrollY>=totalH){pauseA();scrollY=totalH;updPos();updProg();return}
  updPos();updProg();
  af=requestAnimationFrame(loop);
}
function updPos(){tw.style.transform='translateY('+(scrollY*-1)+'px)'}
function updProg(){
  if(totalH<=0){progTag.textContent='--';return}
  progTag.textContent=Math.min(100,Math.round(scrollY/totalH*100))+'%';
}

// ═══════════════════════════════════════════════════════
//  TOUCH (stage)
// ═══════════════════════════════════════════════════════
stage.addEventListener('touchstart',function(e){
  if(e.target.closest('button')||e.target.closest('#bottom-bar')||e.target.closest('#top-bar')||e.target.closest('#spd-wrap'))return;
  e.preventDefault();tsOn=true;tsMv=false;
  tsY=e.touches[0].clientY;tsSY=scrollY;
  pauseA();showUI();
},{passive:false});
stage.addEventListener('touchmove',function(e){
  if(!tsOn)return;e.preventDefault();
  var dy=tsY-e.touches[0].clientY;
  if(Math.abs(dy)>3)tsMv=true;
  scrollY=Math.max(0,Math.min(totalH,tsSY+dy));
  updPos();updProg();
},{passive:false});
stage.addEventListener('touchend',function(){
  if(!tsOn)return;tsOn=false;
  if(!tsMv){if(isPlay)pauseA();else startA()}
  hideAfter();
});

// Mouse fallback
var md=false,msy=0,mss=0;
stage.addEventListener('mousedown',function(e){
  if(e.target.closest('button')||e.target.closest('#bottom-bar')||e.target.closest('#top-bar')||e.target.closest('#spd-wrap'))return;
  md=true;msy=e.clientY;mss=scrollY;pauseA();showUI();
});
window.addEventListener('mousemove',function(e){
  if(!md)return;scrollY=Math.max(0,Math.min(totalH,mss+(msy-e.clientY)));updPos();updProg();showUI();
});
window.addEventListener('mouseup',function(){
  if(!md)return;var mvd=Math.abs(scrollY-mss)>2;md=false;
  if(!mvd){if(isPlay)pauseA();else startA()}
  hideAfter();
});

// ═══════════════════════════════════════════════════════
//  UI
// ═══════════════════════════════════════════════════════
function showUI(){document.body.classList.remove('fs-hide-ui');clearTimeout(uiT)}
function hideAfter(){
  clearTimeout(uiT);
  if(isFS)uiT=setTimeout(function(){if(!tsOn&&!md)document.body.classList.add('fs-hide-ui')},3000);
}
function enterFS(){
  var el=document.documentElement;
  if(el.requestFullscreen)el.requestFullscreen();
  else if(el.webkitRequestFullscreen)el.webkitRequestFullscreen();
}
function exitFS(){
  if(document.fullscreenElement)document.exitFullscreen();
  else if(document.webkitFullscreenElement)document.webkitExitFullscreen();
}
function onFSC(){
  isFS=!!(document.fullscreenElement||document.webkitFullscreenElement);
  btnFS.textContent=isFS?'⛶ 退出':'⛶ 全屏';
  btnFS.classList.toggle('active',isFS);
  fsHint.style.display=isFS?'':'none';
  if(isFS)hideAfter();
  else{showUI();document.body.classList.remove('fs-hide-ui')}
}
document.addEventListener('fullscreenchange',onFSC);
document.addEventListener('webkitfullscreenchange',onFSC);
btnFS.addEventListener('click',function(){isFS?exitFS():enterFS()});

// ═══════════════════════════════════════════════════════
//  BUTTONS
// ═══════════════════════════════════════════════════════
btnPlay.addEventListener('click',function(){(isPlay?pauseA:startA)();})
btnMir.addEventListener('click',function(){isMir=!isMir;stage.classList.toggle('mirrored',isMir);btnMir.classList.toggle('active',isMir)})
$('btn-bigger').addEventListener('click',function(){fsize=Math.min(96,fsize+6);applyVars();calcTH()})
$('btn-smaller').addEventListener('click',function(){fsize=Math.max(20,fsize-6);applyVars();calcTH()})
$('btn-reset').addEventListener('click',function(){pauseA();scrollY=0;updPos();updProg();showUI()})
$('btn-font').addEventListener('click',function(){fidx=(fidx+1)%FONTS.length;applyVars();showToast('字体: '+(fidx===0?'无衬线':fidx===1?'衬线':'等宽'))})
$('btn-lh').addEventListener('click',function(){lidx=(lidx+1)%LHEIGHTS.length;applyVars();calcTH();showToast('行距: '+LH_LABELS[lidx])})

// Toast
function showToast(m){
  var t=document.createElement('div');
  t.style.cssText='position:fixed;bottom:100px;left:50%;transform:translateX(-50%);background:'+
    'var(--accent);color:var(--bg);padding:6px 18px;border-radius:16px;font-size:13px;font-weight:600;z-index:400;'+
    'animation:toastIn .25s ease,toastOut .25s ease 1.5s forwards';
  t.textContent=m;document.body.appendChild(t);
  setTimeout(function(){t.remove()},2000);
}
// Inject toast keyframes if not already present
if(!document.getElementById('toast-style')){
  var ts=document.createElement('style');ts.id='toast-style';
  ts.textContent='@keyframes toastIn{from{opacity:0;transform:translateX(-50%) translateY(8px)}}@keyframes toastOut{to{opacity:0;transform:translateX(-50%) translateY(-8px)}}';
  document.head.appendChild(ts);
}

// ═══════════════════════════════════════════════════════
//  KEYBOARD
// ═══════════════════════════════════════════════════════
document.addEventListener('keydown',function(e){
  if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA')return;
  switch(e.key){
    case' ':e.preventDefault();(isPlay?pauseA:startA)();break;
    case'Escape':stopA();showUI();break;
    case'ArrowLeft':e.preventDefault();snapTo(currIdx-1);break;
    case'ArrowRight':e.preventDefault();snapTo(currIdx+1);break;
    case'ArrowUp':fsize=Math.min(96,fsize+4);applyVars();calcTH();break;
    case'ArrowDown':fsize=Math.max(20,fsize-4);applyVars();calcTH();break;
    case'f':case'F':(isFS?exitFS:enterFS)();break;
    case'm':case'M':btnMir.click();break;
  }
});

// ═══════════════════════════════════════════════════════
//  POLL
// ═══════════════════════════════════════════════════════
function poll(){
  fetch('/api/version').then(function(r){return r.json()}).then(function(d){
    recon=0;connLost.classList.remove('show');connDot.classList.remove('stale');
    if(d.version!==serverVer){
      fetch('/api/content').then(function(r){return r.json()}).then(function(d2){
        if(d2.version!==serverVer){serverVer=d2.version;verTag.textContent='v'+serverVer;renderText(d2.content)}
      })
    }
  }).catch(function(){recon++;connDot.classList.add('stale');if(recon>3)connLost.classList.add('show')});
  pollT=setTimeout(poll,800);
}

// ═══════════════════════════════════════════════════════
//  INIT
// ═══════════════════════════════════════════════════════
buildPicker();applyVars();calcTH();updProg();
fetch('/api/content').then(function(r){return r.json()}).then(function(d){
  serverVer=d.version;verTag.textContent='v'+serverVer;renderText(d.content);
}).catch(function(){renderText('无法连接到服务端\n\n请确认 prompter-server.py 已启动')});
poll();
window.addEventListener('resize',function(){calcTH();if(scrollY>totalH){scrollY=totalH;updPos()};buildPicker()});
document.addEventListener('mousemove',function(){if(isFS)showUI();hideAfter()});
document.addEventListener('touchstart',function(e){if(isFS&&!e.target.closest('#spd-wrap')){showUI();hideAfter()}},{passive:true});
console.log('📱 提词器客户端 | 动量翻动选速度 | 轻触暂停 | 拖动回溯');
})();
</script>
</body>
</html>
'''

# ═══════════════════════════════════════════════════════════════
#  ADMIN HTML
# ═══════════════════════════════════════════════════════════════

ADMIN_HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>提词器 · 管理端</title>
<style>
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
  body{background:#0d0d12;color:#e8e4dd;font-family:system-ui,-apple-system,'PingFang SC',sans-serif;min-height:100vh;display:flex;justify-content:center;padding:24px 16px}
  .ctr{width:min(720px,100%);display:flex;flex-direction:column;gap:16px}
  h1{font-size:18px;font-weight:600;color:#d4a853;display:flex;align-items:center;gap:10px}
  h1 .badge{font-size:10px;background:rgba(212,168,83,.2);padding:2px 8px;border-radius:10px;font-weight:400}
  .info{display:flex;gap:16px;align-items:center;flex-wrap:wrap;font-size:12px;color:#888}
  .info .v{color:#d4a853;font-variant-numeric:tabular-nums}
  textarea{width:100%;background:#14141a;border:1px solid rgba(255,255,255,.1);color:#e8e4dd;border-radius:12px;padding:20px;font-size:15px;font-family:'SF Mono','Fira Code','Consolas','PingFang SC',monospace;line-height:1.7;resize:vertical;min-height:400px;outline:none;transition:border-color .2s}
  textarea:focus{border-color:rgba(212,168,83,.5)}
  textarea::placeholder{color:#555}
  .acts{display:flex;gap:10px;flex-wrap:wrap}
  button{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);color:#ccc;border-radius:10px;padding:10px 20px;font-size:13px;font-family:inherit;cursor:pointer;transition:all .15s}
  button:hover{background:rgba(255,255,255,.12)}
  button.pri{background:rgba(212,168,83,.15);border-color:#d4a853;color:#d4a853;font-weight:600}
  button.pri:hover{background:rgba(212,168,83,.25)}
  .status{font-size:12px;color:#4caf50;opacity:0;transition:opacity .3s}
  .status.on{opacity:1}
  .share{background:#14141a;border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:14px 18px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
  .share label{font-size:11px;color:#888}
  .share code{font-size:14px;color:#d4a853;background:rgba(212,168,83,.08);padding:6px 12px;border-radius:6px;font-family:'SF Mono',monospace;word-break:break-all}
  #drop-zone{border:2px dashed rgba(255,255,255,.1);border-radius:12px;padding:30px;text-align:center;color:#555;font-size:13px;transition:border-color .2s;cursor:pointer}
  #drop-zone:hover,#drop-zone.drag{border-color:rgba(212,168,83,.4);color:#888}
  hr{border:none;border-top:1px solid rgba(255,255,255,.06)}
  @media(max-width:600px){textarea{min-height:280px;font-size:14px}button{padding:8px 16px;font-size:12px}}
</style>
</head>
<body>
<div class="ctr">
  <h1>🎬 提词器管理端 <span class="badge">ADMIN</span></h1>
  <div class="share">
    <label>📱 客户端链接：</label>
    <code id="url">--</code>
    <button id="btn-copy" style="flex-shrink:0">复制</button>
  </div>
  <div class="info">
    <span>版本: <span class="v" id="v">--</span></span>
    <span>字数: <span class="v" id="cnt">--</span></span>
    <span class="status" id="saved">✓ 已推送</span>
  </div>
  <div id="drop-zone">📂 拖放 .txt / .md 文件到这里，或点击选择</div>
  <textarea id="ed" placeholder="在此编辑提词脚本…&#10;&#10;支持 **粗体** 和 *斜体* · 空行 = 停顿&#10;&#10;Cmd+S 或点击「推送」同步到客户端"></textarea>
  <div class="acts">
    <button class="pri" id="btn-push">📤 推送到客户端</button>
    <button id="btn-paste">📋 从剪贴板粘贴</button>
    <button id="btn-url">🌐 从 URL 加载</button>
    <button id="btn-clear">🗑 清空</button>
    <button id="btn-open">👁 预览客户端</button>
  </div>
  <hr>
  <div style="font-size:11px;color:#555">
    快捷键: <b>Cmd+S</b> 推送 &nbsp;|&nbsp;
    拖放文件 / 粘贴 / URL 均支持导入 &nbsp;|&nbsp;
    客户端：翻动选速度 · 拖动回溯 · 轻触暂停
  </div>
</div>
<input type="file" id="fi" accept=".txt,.md,.html,.htm,.csv,.json" style="display:none">

<script>
(function(){
var $=function(id){return document.getElementById(id)};
var ed=$('ed'),saved=$('saved'),v=$('v'),cnt=$('cnt'),url=$('url'),curV=0;
url.textContent=window.location.origin+'/';

$('btn-copy').addEventListener('click',function(){
  navigator.clipboard.writeText(window.location.origin+'/').then(function(){
    var b=$('btn-copy');b.textContent='已复制!';setTimeout(function(){b.textContent='复制'},1500);
  });
});

function load(){fetch('/api/content').then(function(r){return r.json()}).then(function(d){
  curV=d.version;v.textContent='v'+curV;if(d.content)ed.value=d.content;updCnt();
}).catch(function(){v.textContent='离线'})}

function push(){
  fetch('/api/content',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:ed.value})})
  .then(function(r){return r.json()}).then(function(d){
    curV=d.version;v.textContent='v'+curV;saved.classList.add('on');
    setTimeout(function(){saved.classList.remove('on')},2000);
  }).catch(function(){alert('推送失败，请确认服务端正在运行')});
}

function updCnt(){var t=ed.value;cnt.textContent=(t.trim()?t.trim().split(/\s+/).length:0)+' 词 / '+t.replace(/\s/g,'').length+' 字'}

// File drop zone
var dz=$('drop-zone');
dz.addEventListener('click',function(){$('fi').click()});
dz.addEventListener('dragover',function(e){e.preventDefault();dz.classList.add('drag')});
dz.addEventListener('dragleave',function(){dz.classList.remove('drag')});
dz.addEventListener('drop',function(e){e.preventDefault();dz.classList.remove('drag');
  var f=e.dataTransfer.files[0];if(f)readFile(f);
});

// Also drag on body
document.addEventListener('dragover',function(e){e.preventDefault();dz.classList.add('drag')});
document.addEventListener('drop',function(e){e.preventDefault();dz.classList.remove('drag');
  var f=e.dataTransfer.files[0];if(f)readFile(f);
});

function readFile(f){
  var r=new FileReader();r.onload=function(){ed.value=r.result;updCnt()};r.readAsText(f);
}

$('fi').addEventListener('change',function(){if(this.files[0]){readFile(this.files[0]);this.value=''}});

// Buttons
$('btn-push').addEventListener('click',push);
$('btn-paste').addEventListener('click',function(){
  navigator.clipboard.readText().then(function(t){if(t){ed.value=t;updCnt()}}).catch(function(){alert('无法读取剪贴板')});
});
$('btn-url').addEventListener('click',function(){
  var u=prompt('输入文本文件的 URL：');if(!u)return;
  fetch(u).then(function(r){return r.text()}).then(function(t){ed.value=t;updCnt()})
  .catch(function(){
    fetch('https://api.allorigins.win/raw?url='+encodeURIComponent(u)).then(function(r){return r.text()})
    .then(function(t){ed.value=t;updCnt()}).catch(function(){alert('加载失败，请检查链接')});
  });
});
$('btn-clear').addEventListener('click',function(){if(confirm('确定清空？')){ed.value='';updCnt()}});
$('btn-open').addEventListener('click',function(){window.open('/','_blank')});
ed.addEventListener('input',updCnt);

// Cmd+S
document.addEventListener('keydown',function(e){if((e.metaKey||e.ctrlKey)&&e.key==='s'){e.preventDefault();push()}});

load();updCnt();
})();
</script>
</body>
</html>
'''

# ═══════════════════════════════════════════════════════════════
#  HTTP SERVER
# ═══════════════════════════════════════════════════════════════

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ('/', '/client'):
            self._html(CLIENT_HTML)
        elif path == '/admin':
            self._html(ADMIN_HTML)
        elif path == '/api/content':
            with state_lock:
                self._json({'content': state['content'], 'version': state['version']})
        elif path == '/api/version':
            with state_lock:
                self._json({'version': state['version']})
        elif path == '/favicon.ico':
            self.send_response(204); self.end_headers()
        else:
            self.send_error(404)

    def do_POST(self):
        if urllib.parse.urlparse(self.path).path == '/api/content':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length) if length > 0 else b'{}'
            try: data = json.loads(body)
            except json.JSONDecodeError: self.send_error(400); return
            with state_lock:
                state['content'] = data.get('content', '')
                state['version'] += 1
                state['updated_at'] = time.time()
                self._json({'ok': True, 'version': state['version']})
            print(f"  📤 Content updated → v{state['version']} ({len(state['content'])} chars)")
        else:
            self.send_error(404)

    def _html(self, html):
        data = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(data))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def _json(self, obj):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(data))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {args[0]}")

if __name__ == '__main__':
    lan_ip = get_lan_ip()
    print()
    print("=" * 56)
    print("  🎬  提词器 · 内网服务端")
    print("=" * 56)
    print(f"\n  📱 客户端 (平板):  http://{lan_ip}:{PORT}/")
    print(f"  ✏️  管理端 (编辑):  http://{lan_ip}:{PORT}/admin")
    print(f"\n  本机:  http://127.0.0.1:{PORT}/admin")
    print("\n  按 Ctrl+C 停止")
    print("=" * 56 + "\n")

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer((HOST, PORT), Handler) as httpd:
        try: httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n  服务已停止 👋\n")
            httpd.shutdown()
