"""
game_html.py — the 3D racing client (Three.js + Web Audio), built as a string.

`build_game_html(cfg)` returns a complete standalone HTML document that can be
embedded with `streamlit.components.v1.html`, opened directly in a browser, or
published as an artifact.  All configuration is injected as a single JSON blob,
so there is no brace-escaping in the JavaScript below.
"""

from __future__ import annotations

import json
from typing import Any, Dict

FONT_LINK = ('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
             '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
             'family=Barlow+Condensed:wght@500;600;700;800&family=Barlow:wght@400;600;700'
             '&family=JetBrains+Mono:wght@600;800&display=swap">')

THREE_SOURCES = [
    "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js",
    "https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js",
    "https://unpkg.com/three@0.128.0/build/three.min.js",
]

DEFAULT_CFG: Dict[str, Any] = {
    "player": "Player1",
    "laps": 3,
    "power": 3,
    "track": 1,
    "aiCount": 3,
    "aiSkill": 0.82,
    "volume": 0.8,
    "quality": "high",
    "camera": "chase",
    "height": 620,
    "api": None,          # e.g. "http://192.168.1.20:8765"
    "apiPort": None,      # resolved against the browser host at runtime
    "room": None,         # multiplayer room code (None = solo)
    "pid": None,
    "hotseat": False,     # second local player on WASD
    "showHelp": True,
}

GAME_CSS = """
:root{
  --ink:#e8eefc; --panel:rgba(9,14,28,.82); --line:rgba(120,160,255,.28);
  --accent:#38bdf8; --good:#34d399; --warn:#fbbf24; --bad:#f87171;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0;height:100%;overflow:hidden;background:#05070f;
  font-family:'Barlow','Segoe UI',system-ui,-apple-system,Roboto,sans-serif;color:var(--ink)}
.num,#h-time,#h-lap,#h-pos,#h-best,#sp-val,#toast,.code{
  font-family:'JetBrains Mono',ui-monospace,Menlo,Consolas,monospace;
  font-variant-numeric:tabular-nums}
h1,h2,h4,#toast,.btn,#tools button{font-family:'Barlow Condensed','Barlow',sans-serif;
  text-transform:uppercase;letter-spacing:.06em}
#wrap{position:relative;width:100%;height:100vh;overflow:hidden;background:#05070f}
canvas#scene{display:block;width:100%;height:100%}
.panel{position:absolute;background:var(--panel);border:1px solid var(--line);
  border-radius:12px;backdrop-filter:blur(8px);box-shadow:0 8px 30px rgba(0,0,0,.45)}
#hud{top:12px;left:12px;padding:10px 14px;min-width:186px;z-index:6}
#hud .row{display:flex;justify-content:space-between;gap:16px;font-size:12px;
  letter-spacing:.4px;padding:2px 0;color:#9fb3d9;text-transform:uppercase}
#hud .row b{color:#fff;font-size:15px;font-variant-numeric:tabular-nums}
#hud .big{font-size:26px;line-height:1.1;color:var(--accent);
  font-weight:700;font-variant-numeric:tabular-nums}
#standings{top:12px;right:12px;padding:8px 10px;min-width:196px;z-index:6;font-size:12px}
#standings h4{margin:0 0 6px;font-size:11px;letter-spacing:1.4px;color:#8fa6cf;
  text-transform:uppercase;font-weight:600}
#standings .drv{display:flex;align-items:center;gap:7px;padding:3px 4px;border-radius:6px}
#standings .drv.me{background:rgba(56,189,248,.16)}
#standings .dot{width:9px;height:9px;border-radius:50%;flex:0 0 auto;
  box-shadow:0 0 6px currentColor}
#standings .nm{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#standings .gp{color:#8fa6cf;font-variant-numeric:tabular-nums;font-size:11px}
#speedo{bottom:14px;left:14px;padding:10px 14px;width:200px;z-index:6}
#speedo .val{font-size:34px;font-weight:800;line-height:1;color:#fff;
  font-variant-numeric:tabular-nums}
#speedo .unit{font-size:11px;color:#8fa6cf;letter-spacing:2px}
#speedbar,#nitrobar{height:7px;border-radius:4px;background:rgba(255,255,255,.12);
  overflow:hidden;margin-top:8px}
#speedfill{height:100%;width:0%;border-radius:4px;
  background:linear-gradient(90deg,#22d3ee,#38bdf8,#f43f5e);transition:width .08s linear}
#nitrofill{height:100%;width:100%;border-radius:4px;
  background:linear-gradient(90deg,#a855f7,#22d3ee);transition:width .12s linear}
#minimap{bottom:14px;right:14px;padding:8px;z-index:6}
#minimap canvas{display:block;border-radius:6px}
#toast{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
  font-size:56px;font-weight:900;letter-spacing:2px;text-shadow:0 6px 26px rgba(0,0,0,.8);
  z-index:8;pointer-events:none;opacity:0;transition:opacity .2s}
#msg{position:absolute;top:20%;left:50%;transform:translateX(-50%);z-index:8;
  font-size:15px;font-weight:700;padding:8px 18px;border-radius:20px;
  background:rgba(9,14,28,.85);border:1px solid var(--line);opacity:0;
  transition:opacity .25s;pointer-events:none}
#tools{position:absolute;top:12px;left:50%;transform:translateX(-50%);z-index:7;
  display:flex;gap:6px}
#tools button{background:rgba(9,14,28,.8);color:#cbd9f5;border:1px solid var(--line);
  border-radius:9px;padding:7px 11px;font-size:12px;cursor:pointer;font-weight:600}
#tools button:hover{background:rgba(56,189,248,.22);color:#fff}
.screen{position:absolute;inset:0;z-index:12;display:flex;align-items:center;
  justify-content:center;background:radial-gradient(ellipse at center,rgba(11,18,38,.86),rgba(3,6,14,.96))}
.card{width:min(660px,92%);max-height:92%;overflow:auto;padding:24px 26px;text-align:center;
  background:linear-gradient(160deg,rgba(17,26,50,.96),rgba(8,13,28,.97));
  border:1px solid var(--line);border-radius:18px;box-shadow:0 20px 70px rgba(0,0,0,.6)}
.card h1{margin:0 0 4px;font-size:30px;letter-spacing:1px}
.card h2{margin:0 0 12px;font-size:22px}
.card p{margin:4px 0 14px;color:#9fb3d9;font-size:13px;line-height:1.6}
.btn{display:inline-block;margin:6px 5px 0;padding:13px 26px;font-size:16px;font-weight:800;
  border:none;border-radius:11px;cursor:pointer;color:#04121f;
  background:linear-gradient(135deg,#34d399,#22d3ee);box-shadow:0 8px 24px rgba(34,211,238,.3)}
.btn.alt{background:linear-gradient(135deg,#818cf8,#a855f7);color:#fff;
  box-shadow:0 8px 24px rgba(168,85,247,.3)}
.btn:hover{filter:brightness(1.1)}
.keys{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;
  margin:14px 0 4px;text-align:left}
.keys div{background:rgba(255,255,255,.05);border:1px solid var(--line);
  border-radius:9px;padding:8px 10px;font-size:12px;color:#c2d2f0}
.keys b{color:#fff;display:block;font-size:11px;letter-spacing:1px;text-transform:uppercase}
table.res{width:100%;border-collapse:collapse;margin:10px 0;font-size:13px}
table.res th{color:#8fa6cf;font-size:10px;letter-spacing:1.2px;text-transform:uppercase;
  padding:6px;border-bottom:1px solid var(--line);text-align:left}
table.res td{padding:7px 6px;border-bottom:1px solid rgba(120,160,255,.12);
  font-variant-numeric:tabular-nums}
table.res tr.me td{background:rgba(56,189,248,.14);color:#fff;font-weight:700}
.tag{display:inline-block;padding:3px 9px;border-radius:20px;font-size:11px;font-weight:700;
  background:rgba(56,189,248,.2);color:#7dd3fc;margin:2px}
#lobby{margin:10px 0;font-size:13px;color:#a9bcdd}
#loaderr{color:#fca5a5;font-size:13px;margin-top:10px}
@media (max-width:640px){
  #standings,#minimap{display:none}
  #hud{padding:7px 10px;min-width:150px}
  #speedo{width:150px}
  .card h1{font-size:22px}
}
"""

GAME_JS = r"""
(function () {
  'use strict';
  var CFG = window.__RACE_CFG__ || {};
  // When the app only knows its port (LAN play), resolve the host at runtime so
  // phones joining through the QR code talk to the right machine.
  if (!CFG.api && CFG.apiPort) {
    CFG.api = window.location.protocol + '//' + window.location.hostname + ':' + CFG.apiPort;
  }
  var $ = function (id) { return document.getElementById(id); };
  var clamp = function (v, a, b) { return v < a ? a : (v > b ? b : v); };
  var lerp = function (a, b, t) { return a + (b - a) * t; };
  var fmt = function (s) {
    if (s == null || !isFinite(s)) return '--:--';
    var m = Math.floor(s / 60), r = s - m * 60;
    return m + ':' + (r < 10 ? '0' : '') + r.toFixed(2);
  };
  var esc = function (s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  };

  if (typeof THREE === 'undefined') {
    $('loaderr').textContent =
      'Could not load the 3D engine (three.js). Check your internet connection and reload.';
    return;
  }

  /* ===================================================================
     1. AUDIO — everything is synthesised, so there are no asset files
        to ship: engine note, acceleration, tyre screech, crash, nitro,
        crowd cheering, countdown beeps and the winner fanfare.
     =================================================================== */
  function AudioKit(volume) {
    this.ok = false;
    this.muted = false;
    this.master = null;
    this.vol = volume == null ? 0.8 : volume;
    this.ctx = null;
  }
  AudioKit.prototype.start = function () {
    if (this.ok) { if (this.ctx.state === 'suspended') this.ctx.resume(); return; }
    var AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    try { this.ctx = new AC(); } catch (e) { return; }
    var ctx = this.ctx;
    this.master = ctx.createGain();
    this.master.gain.value = this.vol;
    this.master.connect(ctx.destination);

    // --- shared noise buffer (2s of pink-ish noise) ---
    var len = ctx.sampleRate * 2, buf = ctx.createBuffer(1, len, ctx.sampleRate);
    var d = buf.getChannelData(0), b0 = 0, b1 = 0, b2 = 0;
    for (var i = 0; i < len; i++) {
      var w = Math.random() * 2 - 1;
      b0 = 0.997 * b0 + w * 0.029; b1 = 0.963 * b1 + w * 0.283; b2 = 0.57 * b2 + w * 1.022;
      d[i] = clamp((b0 + b1 + b2 + w * 0.1) * 0.16, -1, 1);
    }
    this.noise = buf;

    // --- crowd bed: filtered noise that swells on race events ---
    var crowdSrc = ctx.createBufferSource();
    crowdSrc.buffer = buf; crowdSrc.loop = true;
    var crowdFilt = ctx.createBiquadFilter();
    crowdFilt.type = 'bandpass'; crowdFilt.frequency.value = 900; crowdFilt.Q.value = 0.7;
    this.crowdGain = ctx.createGain(); this.crowdGain.gain.value = 0.0;
    crowdSrc.connect(crowdFilt); crowdFilt.connect(this.crowdGain);
    this.crowdGain.connect(this.master);
    crowdSrc.start(0);
    this.crowdSrc = crowdSrc;

    // --- engine: two detuned saws + sub sine through a low-pass ---
    this.engGain = ctx.createGain(); this.engGain.gain.value = 0.0;
    this.engFilt = ctx.createBiquadFilter();
    this.engFilt.type = 'lowpass'; this.engFilt.frequency.value = 900;
    this.osc = [];
    var shapes = ['sawtooth', 'sawtooth', 'square'];
    for (var k = 0; k < 3; k++) {
      var o = ctx.createOscillator();
      o.type = shapes[k];
      o.frequency.value = 60;
      o.detune.value = (k - 1) * 14;
      var g = ctx.createGain();
      g.gain.value = k === 2 ? 0.18 : 0.5;
      o.connect(g); g.connect(this.engFilt);
      o.start(0);
      this.osc.push(o);
    }
    this.engFilt.connect(this.engGain); this.engGain.connect(this.master);

    // --- rival engine hum (quieter, fixed-ish) ---
    this.rivalGain = ctx.createGain(); this.rivalGain.gain.value = 0;
    var ro = ctx.createOscillator(); ro.type = 'sawtooth'; ro.frequency.value = 70;
    var rf = ctx.createBiquadFilter(); rf.type = 'lowpass'; rf.frequency.value = 420;
    ro.connect(rf); rf.connect(this.rivalGain); this.rivalGain.connect(this.master);
    ro.start(0); this.rivalOsc = ro;

    // --- tyre screech ---
    var scr = ctx.createBufferSource(); scr.buffer = buf; scr.loop = true;
    var scrF = ctx.createBiquadFilter();
    scrF.type = 'bandpass'; scrF.frequency.value = 2600; scrF.Q.value = 6;
    this.scrGain = ctx.createGain(); this.scrGain.gain.value = 0;
    scr.connect(scrF); scrF.connect(this.scrGain); this.scrGain.connect(this.master);
    scr.start(0);

    // --- wind / rumble tied to speed ---
    var wind = ctx.createBufferSource(); wind.buffer = buf; wind.loop = true;
    var windF = ctx.createBiquadFilter(); windF.type = 'highpass'; windF.frequency.value = 1200;
    this.windGain = ctx.createGain(); this.windGain.gain.value = 0;
    wind.connect(windF); windF.connect(this.windGain); this.windGain.connect(this.master);
    wind.start(0);

    this.ok = true;
  };
  AudioKit.prototype.setVolume = function (v) {
    this.vol = v; if (this.master) this.master.gain.value = this.muted ? 0 : v;
  };
  AudioKit.prototype.toggleMute = function () {
    this.muted = !this.muted;
    if (this.master) this.master.gain.value = this.muted ? 0 : this.vol;
    return this.muted;
  };
  // Continuous per-frame update: engine pitch follows speed & throttle.
  AudioKit.prototype.drive = function (o) {
    if (!this.ok) return;
    var t = this.ctx.currentTime;
    var rpm = 0.12 + o.speedRatio * 0.88;
    var base = 52 + rpm * 230 + (o.boost ? 55 : 0);
    for (var i = 0; i < this.osc.length; i++) {
      var mult = i === 2 ? 0.5 : 1;
      this.osc[i].frequency.setTargetAtTime(base * mult, t, 0.05);
    }
    this.engFilt.frequency.setTargetAtTime(600 + rpm * 2600 + (o.throttle ? 700 : 0), t, 0.08);
    var g = o.running ? (0.05 + rpm * 0.1 + (o.throttle ? 0.045 : 0)) : 0.0;
    this.engGain.gain.setTargetAtTime(g, t, 0.09);
    this.windGain.gain.setTargetAtTime(o.speedRatio * o.speedRatio * 0.05, t, 0.15);
    this.scrGain.gain.setTargetAtTime(o.screech ? 0.11 : 0, t, o.screech ? 0.02 : 0.12);
    this.rivalGain.gain.setTargetAtTime(clamp(0.05 - o.rivalDist / 900, 0, 0.05), t, 0.2);
    if (this.rivalOsc) this.rivalOsc.frequency.setTargetAtTime(90 + rpm * 60, t, 0.2);
    this.crowdGain.gain.setTargetAtTime(o.crowd, t, 0.5);
  };
  AudioKit.prototype._burst = function (dur, freq, q, gain, type) {
    if (!this.ok) return;
    var ctx = this.ctx, t = ctx.currentTime;
    var s = ctx.createBufferSource(); s.buffer = this.noise;
    var f = ctx.createBiquadFilter();
    f.type = type || 'bandpass'; f.frequency.value = freq; f.Q.value = q;
    var g = ctx.createGain();
    g.gain.setValueAtTime(gain, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    s.connect(f); f.connect(g); g.connect(this.master);
    s.start(t); s.stop(t + dur + 0.02);
  };
  AudioKit.prototype._tone = function (freq, at, dur, gain, type) {
    if (!this.ok) return;
    var ctx = this.ctx, t = ctx.currentTime + at;
    var o = ctx.createOscillator(); o.type = type || 'triangle'; o.frequency.value = freq;
    var g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(gain, t + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g); g.connect(this.master); o.start(t); o.stop(t + dur + 0.05);
  };
  AudioKit.prototype.crash = function (hard) {
    this._burst(hard ? 0.6 : 0.28, hard ? 260 : 500, 0.8, hard ? 0.5 : 0.22, 'lowpass');
    this._tone(hard ? 70 : 120, 0, 0.28, hard ? 0.35 : 0.15, 'square');
    this.cheer(hard ? 0.6 : 0.25, 1.2);
  };
  AudioKit.prototype.nitro = function () {
    if (!this.ok) return;
    var ctx = this.ctx, t = ctx.currentTime;
    var s = ctx.createBufferSource(); s.buffer = this.noise;
    var f = ctx.createBiquadFilter(); f.type = 'bandpass'; f.Q.value = 3;
    f.frequency.setValueAtTime(400, t);
    f.frequency.exponentialRampToValueAtTime(4200, t + 0.5);
    var g = ctx.createGain();
    g.gain.setValueAtTime(0.22, t); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.6);
    s.connect(f); f.connect(g); g.connect(this.master); s.start(t); s.stop(t + 0.65);
  };
  AudioKit.prototype.beep = function (hi) { this._tone(hi ? 1180 : 620, 0, hi ? 0.7 : 0.16, 0.22, 'square'); };
  AudioKit.prototype.cheer = function (amount, dur) {
    if (!this.ok) return;
    var t = this.ctx.currentTime;
    this.crowdGain.gain.cancelScheduledValues(t);
    this.crowdGain.gain.setTargetAtTime(amount, t, 0.12);
    this.crowdGain.gain.setTargetAtTime(this.baseCrowd || 0.05, t + (dur || 2), 0.7);
  };
  AudioKit.prototype.fanfare = function (win) {
    var notes = win ? [523, 659, 784, 1047, 1319] : [392, 349, 294];
    for (var i = 0; i < notes.length; i++) {
      this._tone(notes[i], i * 0.15, 0.5, 0.2, 'triangle');
      if (win) this._tone(notes[i] / 2, i * 0.15, 0.5, 0.12, 'sawtooth');
    }
    this.cheer(win ? 0.42 : 0.12, 6);
  };
  AudioKit.prototype.blip = function () { this._tone(880, 0, 0.09, 0.12, 'sine'); };

  var AUDIO = new AudioKit(CFG.volume);

  /* ===================================================================
     2. SCENE
     =================================================================== */
  var wrap = $('wrap');
  var canvas = $('scene');
  var scene = new THREE.Scene();
  scene.background = new THREE.Color(0x9ed2f5);
  scene.fog = new THREE.Fog(0x9ed2f5, 220, 420);

  var HQ = CFG.quality !== 'low';
  var renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: HQ });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, HQ ? 2 : 1));
  if (HQ) {
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  }

  var camera = new THREE.PerspectiveCamera(58, 1, 0.5, 900);
  camera.position.set(0, 60, 40);

  function resize() {
    var w = wrap.clientWidth || window.innerWidth;
    var h = wrap.clientHeight || window.innerHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / Math.max(1, h);
    camera.updateProjectionMatrix();
  }
  window.addEventListener('resize', resize);

  scene.add(new THREE.HemisphereLight(0xdff1ff, 0x3f6b3a, 0.95));
  var sun = new THREE.DirectionalLight(0xfff4e0, 1.15);
  sun.position.set(70, 130, 50);
  if (HQ) {
    sun.castShadow = true;
    sun.shadow.mapSize.width = sun.shadow.mapSize.height = 1024;
    var sc = sun.shadow.camera;
    sc.left = -130; sc.right = 130; sc.top = 130; sc.bottom = -130; sc.far = 360;
  }
  scene.add(sun);

  // ---- ground ----
  var groundTex = (function () {
    var c = document.createElement('canvas'); c.width = c.height = 128;
    var x = c.getContext('2d');
    x.fillStyle = '#4e9a4a'; x.fillRect(0, 0, 128, 128);
    for (var i = 0; i < 900; i++) {
      x.fillStyle = ['#57a850', '#469143', '#63b45a'][i % 3];
      x.fillRect(Math.random() * 128, Math.random() * 128, 2, 2);
    }
    var t = new THREE.CanvasTexture(c);
    t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(40, 40);
    return t;
  })();
  var ground = new THREE.Mesh(
    new THREE.PlaneGeometry(700, 700),
    new THREE.MeshStandardMaterial({ map: groundTex, roughness: 1 })
  );
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.05;
  ground.receiveShadow = HQ;
  scene.add(ground);

  /* ===================================================================
     3. TRACK — road ribbon, curbs, lane markings, barriers, start /
        finish gantry with a board, grandstands and scenery.
     =================================================================== */
  var LAYOUTS = {
    1: { name: 'Sunset Oval', w: 9.5, pts: [
      [70,0],[64.4,29],[37.2,50.2],[0,54.6],[-32.8,44.4],[-56.9,25.6],
      [-70,0],[-64.4,-29],[-37.2,-50.2],[0,-54.6],[32.8,-44.4],[56.9,-25.6]] },
    2: { name: 'Harbour Sweep', w: 9.0, pts: [
      [64,0],[72.7,25.6],[57.4,48.8],[27.1,55.7],[0,49.3],[-20.1,41.2],[-39.1,33.2],
      [-55.8,19.6],[-64,0],[-62.5,-22],[-51.4,-43.7],[-28.9,-59.3],[0,-59.5],
      [21.9,-44.8],[33.1,-28.1],[45.5,-16]] },
    3: { name: 'Grand Circuit', w: 8.5, pts: [
      [73,0],[72.3,23.7],[54.8,41.4],[34.8,54.2],[10.3,52.5],[-8.4,43],[-31.2,48.7],
      [-64.9,49],[-74.6,24.4],[-59,0],[-51.8,-17],[-46.3,-35],[-31.3,-48.7],
      [-12.6,-64.5],[14.5,-74],[34.7,-54.2],[36.2,-27.4],[49.5,-16.2]] }
  };
  var LAY = LAYOUTS[CFG.track] || LAYOUTS[1];
  var ROAD_W = LAY.w;                     // half-width of the tarmac
  var curve = new THREE.CatmullRomCurve3(
    LAY.pts.map(function (p) { return new THREE.Vector3(p[0], 0, p[1]); }), true, 'catmullrom', 0.5);

  var SAMPLES = 720;
  var pts = [], tans = [], nors = [];
  for (var i = 0; i < SAMPLES; i++) {
    var t = i / SAMPLES;
    var p = curve.getPointAt(t);
    var tg = curve.getTangentAt(t).normalize();
    pts.push(p); tans.push(tg);
    nors.push(new THREE.Vector3(-tg.z, 0, tg.x).normalize());
  }
  var TRACK_LEN = curve.getLength();
  var SECTORS = 8;

  function strip(inner, outer, colorFn, y) {
    // Builds a flat non-indexed ribbon so each quad can have its own colour.
    var pos = [], col = [];
    var c = new THREE.Color();
    for (var i = 0; i < SAMPLES; i++) {
      var j = (i + 1) % SAMPLES;
      var a = pts[i], b = pts[j], na = nors[i], nb = nors[j];
      var p1 = [a.x + na.x * inner, y, a.z + na.z * inner];
      var p2 = [a.x + na.x * outer, y, a.z + na.z * outer];
      var p3 = [b.x + nb.x * inner, y, b.z + nb.z * inner];
      var p4 = [b.x + nb.x * outer, y, b.z + nb.z * outer];
      pos.push.apply(pos, p1.concat(p3, p2, p2, p3, p4));
      c.set(colorFn(i));
      for (var k = 0; k < 6; k++) col.push(c.r, c.g, c.b);
    }
    var g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
    g.computeVertexNormals();
    var m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({
      vertexColors: true, roughness: 0.85, side: THREE.DoubleSide
    }));
    m.receiveShadow = HQ;
    scene.add(m);
    return m;
  }

  // tarmac (subtle shade variation so speed reads better)
  strip(-ROAD_W, ROAD_W, function (i) { return (i % 24 < 12) ? 0x35393f : 0x32363c; }, 0.02);
  // curbs
  strip(ROAD_W, ROAD_W + 1.5, function (i) { return (Math.floor(i / 6) % 2) ? 0xe03131 : 0xf8f9fa; }, 0.06);
  strip(-ROAD_W - 1.5, -ROAD_W, function (i) { return (Math.floor(i / 6) % 2) ? 0xe03131 : 0xf8f9fa; }, 0.06);
  // white edge lines
  strip(ROAD_W - 0.7, ROAD_W - 0.2, function () { return 0xf1f3f5; }, 0.07);
  strip(-ROAD_W + 0.2, -ROAD_W + 0.7, function () { return 0xf1f3f5; }, 0.07);
  // dashed centre line
  strip(-0.22, 0.22, function (i) { return (Math.floor(i / 5) % 2) ? 0x32363c : 0xffd43b; }, 0.075);

  // ---- start / finish line + gantry board ----
  function checkerTexture() {
    var c = document.createElement('canvas'); c.width = 256; c.height = 64;
    var x = c.getContext('2d');
    var s = 32;
    for (var iy = 0; iy < c.height / s; iy++) {
      for (var ix = 0; ix < c.width / s; ix++) {
        x.fillStyle = ((ix + iy) % 2) ? '#111318' : '#ffffff';
        x.fillRect(ix * s, iy * s, s, s);
      }
    }
    return new THREE.CanvasTexture(c);
  }
  function signTexture(title, sub) {
    var c = document.createElement('canvas'); c.width = 1024; c.height = 200;
    var x = c.getContext('2d');
    var grd = x.createLinearGradient(0, 0, 0, 200);
    grd.addColorStop(0, '#101a33'); grd.addColorStop(1, '#060b18');
    x.fillStyle = grd; x.fillRect(0, 0, 1024, 200);
    x.strokeStyle = '#38bdf8'; x.lineWidth = 8; x.strokeRect(6, 6, 1012, 188);
    for (var i = 0; i < 16; i++) {           // checkered trim
      x.fillStyle = (i % 2) ? '#ffffff' : '#111318';
      x.fillRect(20 + i * 62, 18, 62, 16);
      x.fillStyle = (i % 2) ? '#111318' : '#ffffff';
      x.fillRect(20 + i * 62, 166, 62, 16);
    }
    x.fillStyle = '#ffffff'; x.textAlign = 'center';
    x.font = 'bold 76px Segoe UI, sans-serif';
    x.fillText(title, 512, 108);
    x.fillStyle = '#7dd3fc'; x.font = 'bold 34px Segoe UI, sans-serif';
    x.fillText(sub, 512, 152);
    return new THREE.CanvasTexture(c);
  }

  var startP = pts[0], startN = nors[0], startT = tans[0];
  var lineAngle = Math.atan2(startT.x, startT.z);

  // painted checkered start/finish strip across the tarmac
  var lineMesh = new THREE.Mesh(
    new THREE.PlaneGeometry(ROAD_W * 2 + 3, 4.5),
    new THREE.MeshStandardMaterial({ map: checkerTexture(), roughness: 0.9 })
  );
  lineMesh.rotation.x = -Math.PI / 2;
  lineMesh.rotation.z = -lineAngle;
  lineMesh.position.set(startP.x, 0.09, startP.z);
  scene.add(lineMesh);

  // gantry: two pillars, a truss and a big illuminated board
  var gantry = new THREE.Group();
  var pillarMat = new THREE.MeshStandardMaterial({ color: 0xced4da, metalness: 0.4, roughness: 0.5 });
  [-1, 1].forEach(function (s) {
    var pil = new THREE.Mesh(new THREE.BoxGeometry(1.4, 13, 1.4), pillarMat);
    pil.position.set(startN.x * s * (ROAD_W + 2.2), 6.5, startN.z * s * (ROAD_W + 2.2));
    pil.castShadow = HQ;
    gantry.add(pil);
    var foot = new THREE.Mesh(new THREE.BoxGeometry(3.2, 0.7, 3.2), pillarMat);
    foot.position.set(startN.x * s * (ROAD_W + 2.2), 0.35, startN.z * s * (ROAD_W + 2.2));
    gantry.add(foot);
  });
  var truss = new THREE.Mesh(new THREE.BoxGeometry(ROAD_W * 2 + 5.6, 0.5, 1.0), pillarMat);
  truss.position.y = 12.4;
  truss.rotation.y = -lineAngle;
  gantry.add(truss);
  var board = new THREE.Mesh(
    new THREE.PlaneGeometry(ROAD_W * 2 + 4.6, 3.4),
    new THREE.MeshBasicMaterial({ map: signTexture('START / FINISH', LAY.name.toUpperCase() + '  •  ' + CFG.laps + ' LAPS'), side: THREE.DoubleSide })
  );
  board.position.y = 10.2;
  board.rotation.y = -lineAngle + Math.PI / 2;
  gantry.add(board);
  var board2 = board.clone();
  board2.rotation.y = -lineAngle - Math.PI / 2;
  gantry.add(board2);

  // start lights above the line
  var lightBulbs = [];
  for (var li = 0; li < 5; li++) {
    var bulb = new THREE.Mesh(
      new THREE.SphereGeometry(0.5, 14, 14),
      new THREE.MeshBasicMaterial({ color: 0x3a0d0d })
    );
    var off = (li - 2) * 1.6;
    bulb.position.set(startT.x * 0 + startN.x * off, 13.4, startN.z * off);
    gantry.add(bulb);
    lightBulbs.push(bulb);
  }
  gantry.position.set(startP.x, 0, startP.z);
  scene.add(gantry);

  // ---- tyre barriers along the outside ----
  var barrierGeo = new THREE.CylinderGeometry(0.75, 0.75, 0.9, 10);
  var barrierMats = [
    new THREE.MeshStandardMaterial({ color: 0x1f2329, roughness: 1 }),
    new THREE.MeshStandardMaterial({ color: 0xd6d8db, roughness: 1 })
  ];
  var BARRIER = ROAD_W + 3.4;
  for (var bi = 0; bi < SAMPLES; bi += 9) {
    for (var side = -1; side <= 1; side += 2) {
      var mat = barrierMats[(bi / 9 | 0) % 2];
      var tyre = new THREE.Mesh(barrierGeo, mat);
      tyre.position.set(
        pts[bi].x + nors[bi].x * BARRIER * side, 0.45,
        pts[bi].z + nors[bi].z * BARRIER * side);
      tyre.castShadow = HQ;
      scene.add(tyre);
    }
  }

  // ---- grandstands + animated crowd ----
  var crowdMeshes = [];
  function grandstand(idx) {
    var p = pts[idx], n = nors[idx], tg = tans[idx];
    var g = new THREE.Group();
    for (var row = 0; row < 5; row++) {
      var tier = new THREE.Mesh(
        new THREE.BoxGeometry(30, 1.6, 2.6),
        new THREE.MeshStandardMaterial({ color: 0x9aa4b2, roughness: 0.9 }));
      tier.position.set(0, 1 + row * 1.5, -row * 2.4);
      tier.castShadow = HQ; tier.receiveShadow = HQ;
      g.add(tier);
      var count = 22;
      var geo = new THREE.SphereGeometry(0.42, 6, 6);
      var inst = new THREE.InstancedMesh(geo,
        new THREE.MeshStandardMaterial({ roughness: 0.9 }), count);
      var dummy = new THREE.Object3D(), col = new THREE.Color();
      for (var c2 = 0; c2 < count; c2++) {
        dummy.position.set(-14 + c2 * 1.3 + Math.random(), 2.3 + row * 1.5, -row * 2.4 + 0.4);
        dummy.updateMatrix();
        inst.setMatrixAt(c2, dummy.matrix);
        col.setHSL(Math.random(), 0.65, 0.55);
        inst.setColorAt(c2, col);
      }
      inst.userData.phase = Math.random() * 6.28;
      inst.userData.baseY = 2.3 + row * 1.5;
      g.add(inst);
      crowdMeshes.push(inst);
    }
    var roof = new THREE.Mesh(new THREE.BoxGeometry(31, 0.4, 12),
      new THREE.MeshStandardMaterial({ color: 0x1f6feb, roughness: 0.7 }));
    roof.position.set(0, 10.5, -5);
    g.add(roof);
    g.position.set(p.x + n.x * (ROAD_W + 15), 0, p.z + n.z * (ROAD_W + 15));
    g.rotation.y = Math.atan2(tg.x, tg.z) + Math.PI / 2;
    scene.add(g);
  }
  grandstand(30); grandstand(Math.floor(SAMPLES * 0.42)); grandstand(Math.floor(SAMPLES * 0.72));

  // ---- scenery: trees + flags, kept clear of the tarmac ----
  var treeTrunk = new THREE.CylinderGeometry(0.4, 0.55, 3, 6);
  var treeTop = new THREE.ConeGeometry(2.6, 6, 8);
  var trunkMat = new THREE.MeshStandardMaterial({ color: 0x6b4226 });
  var leafMat = new THREE.MeshStandardMaterial({ color: 0x2f7a3d });
  function distToTrack(x, z) {
    var best = 1e9;
    for (var i = 0; i < SAMPLES; i += 4) {
      var dx = pts[i].x - x, dz = pts[i].z - z;
      var d = dx * dx + dz * dz;
      if (d < best) best = d;
    }
    return Math.sqrt(best);
  }
  for (var tr = 0; tr < (HQ ? 90 : 40); tr++) {
    var tx = (Math.random() - 0.5) * 320, tz = (Math.random() - 0.5) * 320;
    if (distToTrack(tx, tz) < ROAD_W + 12) continue;
    var tg2 = new THREE.Group();
    var trunk = new THREE.Mesh(treeTrunk, trunkMat); trunk.position.y = 1.5;
    var top = new THREE.Mesh(treeTop, leafMat); top.position.y = 5.4;
    trunk.castShadow = top.castShadow = HQ;
    tg2.add(trunk); tg2.add(top);
    var s2 = 0.7 + Math.random() * 0.9;
    tg2.scale.set(s2, s2, s2);
    tg2.position.set(tx, 0, tz);
    scene.add(tg2);
  }

  /* ===================================================================
     4. CARS
     =================================================================== */
  function buildCar(colorHex, label) {
    var g = new THREE.Group();
    var paint = new THREE.MeshStandardMaterial({ color: colorHex, metalness: 0.45, roughness: 0.35 });
    var dark = new THREE.MeshStandardMaterial({ color: 0x14181f, roughness: 0.6 });

    var body = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.62, 4.6), paint);
    body.position.y = 0.62; body.castShadow = HQ; g.add(body);

    var nose = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.42, 1.3), paint);
    nose.position.set(0, 0.52, 2.7); g.add(nose);

    var cabin = new THREE.Mesh(new THREE.BoxGeometry(1.55, 0.62, 1.9),
      new THREE.MeshStandardMaterial({ color: 0x0b1220, metalness: 0.6, roughness: 0.15 }));
    cabin.position.set(0, 1.16, -0.25); cabin.castShadow = HQ; g.add(cabin);

    var helmet = new THREE.Mesh(new THREE.SphereGeometry(0.34, 12, 12),
      new THREE.MeshStandardMaterial({ color: 0xffffff }));
    helmet.position.set(0, 1.32, -0.1); g.add(helmet);

    var wing = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.14, 0.7), dark);
    wing.position.set(0, 1.28, -2.35); g.add(wing);
    [-1, 1].forEach(function (s) {
      var stalk = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.6, 0.14), dark);
      stalk.position.set(0.85 * s, 0.98, -2.35); g.add(stalk);
    });
    var frontWing = new THREE.Mesh(new THREE.BoxGeometry(2.5, 0.12, 0.6), dark);
    frontWing.position.set(0, 0.3, 3.2); g.add(frontWing);

    var wheelGeo = new THREE.CylinderGeometry(0.62, 0.62, 0.55, 14);
    var wheelMat = new THREE.MeshStandardMaterial({ color: 0x101317, roughness: 0.95 });
    var wheels = [];
    [[1.28, 1.6], [-1.28, 1.6], [1.28, -1.7], [-1.28, -1.7]].forEach(function (w) {
      var wh = new THREE.Mesh(wheelGeo, wheelMat);
      wh.rotation.z = Math.PI / 2;
      wh.position.set(w[0], 0.62, w[1]);
      wh.castShadow = HQ;
      g.add(wh); wheels.push(wh);
    });

    [-0.62, 0.62].forEach(function (x) {
      var lamp = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.2, 0.1),
        new THREE.MeshBasicMaterial({ color: 0xfff3bf }));
      lamp.position.set(x, 0.62, 3.35); g.add(lamp);
    });

    // nitro flame (hidden until boosting)
    var flame = new THREE.Mesh(new THREE.ConeGeometry(0.38, 2.1, 8),
      new THREE.MeshBasicMaterial({ color: 0x60a5fa, transparent: true, opacity: 0.85 }));
    flame.rotation.x = Math.PI / 2;
    flame.position.set(0, 0.6, -3.1);
    flame.visible = false;
    g.add(flame);

    // floating name plate
    var c = document.createElement('canvas'); c.width = 256; c.height = 64;
    var x2 = c.getContext('2d');
    x2.fillStyle = 'rgba(6,10,20,.8)';
    x2.fillRect(0, 0, 256, 64);
    x2.strokeStyle = '#' + colorHex.toString(16).padStart(6, '0');
    x2.lineWidth = 6; x2.strokeRect(3, 3, 250, 58);
    x2.fillStyle = '#fff'; x2.font = 'bold 34px Segoe UI, sans-serif';
    x2.textAlign = 'center'; x2.fillText(String(label).slice(0, 12), 128, 44);
    var plate = new THREE.Sprite(new THREE.SpriteMaterial({
      map: new THREE.CanvasTexture(c), depthTest: false, transparent: true }));
    plate.scale.set(6, 1.5, 1);
    plate.position.y = 3.4;
    g.add(plate);

    g.userData = { wheels: wheels, flame: flame, plate: plate, helmet: helmet };
    scene.add(g);
    return g;
  }

  var PALETTE = [0xef4444, 0x3b82f6, 0x22c55e, 0xf59e0b, 0xa855f7, 0x06b6d4, 0xec4899, 0x84cc16];
  var AI_NAMES = ['Vortex', 'Blaze', 'Nova', 'Rogue', 'Falcon', 'Titan', 'Zephyr'];

  function gridPose(slot) {
    // Grid boxes sit just past the line so the first crossing = lap 1 done.
    var idx = (10 + Math.floor(slot / 2) * 14) % SAMPLES;
    var lateral = (slot % 2 === 0 ? -1 : 1) * ROAD_W * 0.42;
    var p = pts[idx], n = nors[idx], tg = tans[idx];
    return {
      x: p.x + n.x * lateral, z: p.z + n.z * lateral,
      angle: Math.atan2(tg.x, tg.z), idx: idx
    };
  }

  function makeRacer(opts) {
    var pose = gridPose(opts.slot);
    return {
      id: opts.id, name: opts.name, kind: opts.kind, color: opts.color,
      mesh: buildCar(opts.color, opts.name),
      x: pose.x, z: pose.z, angle: pose.angle, speed: 0,
      idx: pose.idx, sector: Math.floor(pose.idx / (SAMPLES / SECTORS)),
      lap: 0, lapStart: 0, bestLap: null, laps: [],
      progress: 0, finished: false, finishTime: null, position: 1,
      offTrack: false, crashes: 0, topSpeed: 0, nitro: 1, boosting: false,
      hitCooldown: 0, aiJitter: Math.random() * 6.28,
      aiLine: (Math.random() - 0.5) * ROAD_W * 0.7, targetX: pose.x, targetZ: pose.z
    };
  }

  var MAX_SPEED = 26 + CFG.power * 3.6;     // world units / second
  var racers = [];
  var me = makeRacer({ id: 'me', name: CFG.player, kind: 'human', color: PALETTE[0], slot: 0 });
  racers.push(me);

  var hotseat = null;
  if (CFG.hotseat) {
    hotseat = makeRacer({ id: 'p2', name: CFG.player2 || 'Player 2', kind: 'human2',
      color: PALETTE[1], slot: 1 });
    racers.push(hotseat);
  }
  var aiStart = racers.length;
  for (var ai = 0; ai < (CFG.aiCount || 0); ai++) {
    racers.push(makeRacer({
      id: 'ai' + ai, name: AI_NAMES[ai % AI_NAMES.length], kind: 'ai',
      color: PALETTE[(aiStart + ai) % PALETTE.length], slot: aiStart + ai
    }));
  }
  var remotes = {};   // pid -> racer (multiplayer ghosts)

  /* ===================================================================
     5. INPUT
     =================================================================== */
  var keys = {};
  var CONSUMED = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', ' ', 'Spacebar'];
  window.addEventListener('keydown', function (e) {
    keys[e.key] = true;
    if (CONSUMED.indexOf(e.key) >= 0) e.preventDefault();
    var k = e.key.toLowerCase();
    if (k === 'c') cycleCamera();
    if (k === 'm') showMsg(AUDIO.toggleMute() ? '🔇 Sound off' : '🔊 Sound on');
    if (k === 'f') toggleFullscreen();
    if (k === 'r' && state.phase === 'racing') respawn(me);
    if (k === 'enter' && state.phase === 'ready') beginCountdown();
  });
  window.addEventListener('keyup', function (e) { keys[e.key] = false; });
  window.addEventListener('blur', function () { keys = {}; });

  // touch controls for phones joining via the QR code
  var touch = { l: false, r: false, up: false, down: false, boost: false };
  function bindTouch() {
    if (!('ontouchstart' in window)) return;
    var bar = document.createElement('div');
    bar.id = 'touchpad';
    bar.style.cssText = 'position:absolute;inset:auto 0 0 0;height:120px;z-index:9;' +
      'display:flex;gap:8px;padding:10px;pointer-events:none';
    var defs = [['◀', 'l'], ['▶', 'r'], ['NITRO', 'boost'], ['BRAKE', 'down'], ['GAS', 'up']];
    defs.forEach(function (d) {
      var b = document.createElement('div');
      b.textContent = d[0];
      b.style.cssText = 'flex:1;display:flex;align-items:center;justify-content:center;' +
        'background:rgba(9,14,28,.75);border:1px solid rgba(120,160,255,.3);border-radius:14px;' +
        'font-weight:800;font-size:16px;color:#e8eefc;pointer-events:auto;user-select:none';
      var on = function (e) { e.preventDefault(); touch[d[1]] = true; b.style.background = 'rgba(56,189,248,.4)'; };
      var off = function (e) { e.preventDefault(); touch[d[1]] = false; b.style.background = 'rgba(9,14,28,.75)'; };
      b.addEventListener('touchstart', on); b.addEventListener('touchend', off);
      b.addEventListener('touchcancel', off);
      bar.appendChild(b);
    });
    wrap.appendChild(bar);
  }
  bindTouch();

  /* ===================================================================
     6. TRACK MATHS — nearest sample, lap + sector bookkeeping
     =================================================================== */
  function nearestIdx(r) {
    var best = r.idx, bestD = 1e12;
    for (var o = -26; o <= 26; o++) {
      var i = (r.idx + o + SAMPLES) % SAMPLES;
      var dx = pts[i].x - r.x, dz = pts[i].z - r.z;
      var d = dx * dx + dz * dz;
      if (d < bestD) { bestD = d; best = i; }
    }
    if (bestD > 900) {                     // lost the plot: full search
      for (var j = 0; j < SAMPLES; j++) {
        var dx2 = pts[j].x - r.x, dz2 = pts[j].z - r.z;
        var d2 = dx2 * dx2 + dz2 * dz2;
        if (d2 < bestD) { bestD = d2; best = j; }
      }
    }
    r.idx = best;
    r.lateral = signedLateral(r, best);
    return best;
  }
  function signedLateral(r, i) {
    var dx = r.x - pts[i].x, dz = r.z - pts[i].z;
    return dx * nors[i].x + dz * nors[i].z;
  }

  function updateLap(r, now) {
    var sec = Math.floor(r.idx / (SAMPLES / SECTORS));
    if (sec === (r.sector + 1) % SECTORS) {
      r.sector = sec;
      if (sec === 0) {                       // crossed the finish line forwards
        var lapTime = now - r.lapStart;
        if (lapTime > 1) {                    // ignore a bounce across the line
          r.laps.push(lapTime);
          if (r.bestLap == null || lapTime < r.bestLap) r.bestLap = lapTime;
        }
        r.lapStart = now;
        r.lap++;
        if (r === me) {
          AUDIO.cheer(0.3, 2.2);
          if (r.lap < CFG.laps) showMsg('LAP ' + (r.lap + 1) + ' / ' + CFG.laps +
            (r.laps.length ? '  •  ' + fmt(r.laps[r.laps.length - 1]) : ''));
          else if (r.lap === CFG.laps) { /* handled by finish */ }
          if (r.lap === CFG.laps - 1) showMsg('🏁 FINAL LAP!');
        }
        if (r.lap >= CFG.laps && !r.finished) finishRacer(r, now);
      }
    } else if (sec === (r.sector - 1 + SECTORS) % SECTORS) {
      r.sector = sec;                        // going backwards; no lap credit
    }
    r.progress = r.lap * SAMPLES + r.idx;
  }

  function finishRacer(r, now) {
    r.finished = true;
    r.finishTime = now;                     // `now` is already race-relative
    r.position = racers.filter(function (o) { return o.finished; }).length;
    if (r === me) endRace();
    else if (state.phase === 'racing' && !me.finished) showMsg(r.name + ' finished P' + r.position);
  }

  function respawn(r) {
    var i = r.idx;
    r.x = pts[i].x; r.z = pts[i].z;
    r.angle = Math.atan2(tans[i].x, tans[i].z);
    r.speed = Math.min(r.speed, MAX_SPEED * 0.25);
    showMsg('Back on track');
  }

  /* ===================================================================
     7. PHYSICS
     =================================================================== */
  var PHYS = {
    accel: 15.5, brake: 26, drag: 0.62, offGrip: 0.52,
    turn: 2.45, boostMul: 1.36, boostDrain: 0.34, boostRegen: 0.11
  };

  function driveHuman(r, dt, ctrl) {
    var boostWanted = ctrl.boost && r.nitro > 0.02 && r.speed > 2;
    r.boosting = boostWanted;
    if (boostWanted) {
      r.nitro = Math.max(0, r.nitro - PHYS.boostDrain * dt);
      if (!r.wasBoost && r === me) AUDIO.nitro();
    } else {
      r.nitro = Math.min(1, r.nitro + PHYS.boostRegen * dt);
    }
    r.wasBoost = boostWanted;

    var cap = MAX_SPEED * (boostWanted ? PHYS.boostMul : 1) * (r.offTrack ? PHYS.offGrip : 1);
    if (ctrl.up) r.speed += PHYS.accel * dt * (r.offTrack ? 0.55 : 1);
    else if (ctrl.down) r.speed -= PHYS.brake * dt;
    else r.speed -= r.speed * PHYS.drag * dt;
    if (r.offTrack) r.speed -= r.speed * 1.15 * dt;
    r.speed = clamp(r.speed, -MAX_SPEED * 0.35, cap);

    var grip = clamp(Math.abs(r.speed) / 6, 0, 1);
    var highSpeedFade = 1 - 0.32 * clamp(r.speed / MAX_SPEED, 0, 1);
    var steer = (ctrl.left ? 1 : 0) - (ctrl.right ? 1 : 0);
    r.angle += steer * PHYS.turn * grip * highSpeedFade * dt * (r.speed < 0 ? -1 : 1);
    r.steer = steer;
    integrate(r, dt);
  }

  function driveAI(r, dt) {
    var look = 10 + Math.floor(r.speed * 0.62);
    var ti = (r.idx + look) % SAMPLES;
    var wobble = Math.sin(state.time * 0.7 + r.aiJitter) * 1.6;
    var tx = pts[ti].x + nors[ti].x * (r.aiLine + wobble);
    var tz = pts[ti].z + nors[ti].z * (r.aiLine + wobble);
    var want = Math.atan2(tx - r.x, tz - r.z);
    var diff = ((want - r.angle + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
    r.angle += clamp(diff, -PHYS.turn * dt * 1.4, PHYS.turn * dt * 1.4);

    // slow for corners: compare tangents ahead
    var a1 = tans[(r.idx + 6) % SAMPLES], a2 = tans[(r.idx + 40) % SAMPLES];
    var a3 = tans[(r.idx + 70) % SAMPLES];
    var bend = Math.max(1 - clamp(a1.dot(a2), -1, 1), (1 - clamp(a1.dot(a3), -1, 1)) * 0.7);
    var skill = CFG.aiSkill || 0.82;
    var target = MAX_SPEED * skill * clamp(1 - bend * 3.2, 0.32, 1);
    if (r.offTrack) target *= PHYS.offGrip;
    r.speed += clamp(target - r.speed, -PHYS.brake * dt, PHYS.accel * dt);
    r.speed = clamp(r.speed, 0, MAX_SPEED * 1.05);
    r.steer = clamp(diff * 3, -1, 1);
    integrate(r, dt);
  }

  function integrate(r, dt) {
    r.x += Math.sin(r.angle) * r.speed * dt;
    r.z += Math.cos(r.angle) * r.speed * dt;
    var i = nearestIdx(r);
    var lat = r.lateral;
    r.offTrack = Math.abs(lat) > ROAD_W;

    // barrier: push back onto the tarmac and scrub speed
    var limit = BARRIER - 0.9;
    if (Math.abs(lat) > limit) {
      var sign = lat > 0 ? 1 : -1;
      var over = Math.abs(lat) - limit;
      r.x -= nors[i].x * sign * over;
      r.z -= nors[i].z * sign * over;
      var hard = r.speed > MAX_SPEED * 0.55;
      if (r.hitCooldown <= 0) {
        r.crashes++;
        r.hitCooldown = 0.7;
        if (r === me) { AUDIO.crash(hard); shake(hard ? 0.9 : 0.4); }
      }
      r.speed *= hard ? 0.38 : 0.72;
      // steer back along the track direction
      var want2 = Math.atan2(tans[i].x, tans[i].z);
      var d2 = ((want2 - r.angle + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
      r.angle += d2 * 0.25;
    }
    if (Math.abs(r.speed) > r.topSpeed) r.topSpeed = Math.abs(r.speed);
    if (r.hitCooldown > 0) r.hitCooldown -= dt;
  }

  function collide(dt) {
    for (var a = 0; a < racers.length; a++) {
      for (var b = a + 1; b < racers.length; b++) {
        var A = racers[a], B = racers[b];
        var dx = B.x - A.x, dz = B.z - A.z;
        var d = Math.hypot(dx, dz);
        if (d < 3.4 && d > 0.001) {
          var push = (3.4 - d) / 2;
          var ux = dx / d, uz = dz / d;
          A.x -= ux * push; A.z -= uz * push;
          B.x += ux * push; B.z += uz * push;
          var closing = Math.abs(A.speed - B.speed);
          A.speed *= 0.9; B.speed *= 0.9;
          if ((A === me || B === me) && me.hitCooldown <= 0 && closing > 4) {
            me.hitCooldown = 0.5; me.crashes++;
            AUDIO.crash(false); shake(0.35);
          }
        }
      }
    }
  }

  /* ===================================================================
     8. CAMERA
     =================================================================== */
  var CAMS = ['chase', 'top', 'cinematic'];
  var camMode = CAMS.indexOf(CFG.camera) >= 0 ? CFG.camera : 'chase';
  var shakeAmt = 0;
  function shake(v) { shakeAmt = Math.min(1.2, shakeAmt + v); }
  function cycleCamera() {
    camMode = CAMS[(CAMS.indexOf(camMode) + 1) % CAMS.length];
    showMsg('Camera: ' + camMode);
    AUDIO.blip();
  }
  var camTarget = new THREE.Vector3();
  function updateCamera(dt) {
    var r = me;
    var desired = new THREE.Vector3();
    if (camMode === 'top') {
      desired.set(r.x, 70, r.z + 0.01);
      camTarget.set(r.x, 0, r.z);
    } else if (camMode === 'chase') {
      desired.set(r.x - Math.sin(r.angle) * 13, 7.5, r.z - Math.cos(r.angle) * 13);
      camTarget.set(r.x + Math.sin(r.angle) * 8, 1.6, r.z + Math.cos(r.angle) * 8);
    } else {
      desired.set(r.x - Math.sin(r.angle) * 22, 20, r.z - Math.cos(r.angle) * 22);
      camTarget.set(r.x, 1, r.z);
    }
    var k = 1 - Math.pow(0.0016, dt);
    camera.position.lerp(desired, camMode === 'top' ? 0.12 : k);
    if (shakeAmt > 0.001) {
      camera.position.x += (Math.random() - 0.5) * shakeAmt;
      camera.position.y += (Math.random() - 0.5) * shakeAmt;
      shakeAmt *= Math.pow(0.02, dt);
    }
    camera.lookAt(camTarget);
  }

  /* ===================================================================
     9. HUD, MINIMAP, MESSAGES
     =================================================================== */
  var msgTimer = 0;
  function showMsg(text) {
    var el = $('msg');
    el.innerHTML = text;
    el.style.opacity = 1;
    msgTimer = 2.4;
  }
  function bigToast(text, color) {
    var el = $('toast');
    el.textContent = text;
    el.style.color = color || '#fff';
    el.style.opacity = 1;
    setTimeout(function () { el.style.opacity = 0; }, 750);
  }

  var mini = $('mini').getContext('2d');
  var MINI = { w: 150, h: 150 };
  var bounds = (function () {
    var b = { x0: 1e9, x1: -1e9, z0: 1e9, z1: -1e9 };
    pts.forEach(function (p) {
      b.x0 = Math.min(b.x0, p.x); b.x1 = Math.max(b.x1, p.x);
      b.z0 = Math.min(b.z0, p.z); b.z1 = Math.max(b.z1, p.z);
    });
    return b;
  })();
  function miniPos(x, z) {
    var pad = 12;
    var sx = (MINI.w - pad * 2) / (bounds.x1 - bounds.x0);
    var sz = (MINI.h - pad * 2) / (bounds.z1 - bounds.z0);
    var s = Math.min(sx, sz);
    return [pad + (x - bounds.x0) * s, pad + (z - bounds.z0) * s];
  }
  function drawMini() {
    mini.clearRect(0, 0, MINI.w, MINI.h);
    mini.fillStyle = 'rgba(6,10,20,.55)';
    mini.fillRect(0, 0, MINI.w, MINI.h);
    mini.strokeStyle = '#5b6472'; mini.lineWidth = 6; mini.lineJoin = 'round';
    mini.beginPath();
    for (var i = 0; i <= SAMPLES; i += 6) {
      var p = miniPos(pts[i % SAMPLES].x, pts[i % SAMPLES].z);
      if (i === 0) mini.moveTo(p[0], p[1]); else mini.lineTo(p[0], p[1]);
    }
    mini.closePath(); mini.stroke();
    var sp = miniPos(startP.x, startP.z);
    mini.strokeStyle = '#fff'; mini.lineWidth = 3;
    mini.beginPath(); mini.arc(sp[0], sp[1], 4, 0, 6.3); mini.stroke();
    allRacers().forEach(function (r) {
      var p = miniPos(r.x, r.z);
      mini.fillStyle = '#' + r.color.toString(16).padStart(6, '0');
      mini.beginPath();
      mini.arc(p[0], p[1], r === me ? 4.6 : 3.2, 0, 6.3);
      mini.fill();
      if (r === me) { mini.strokeStyle = '#fff'; mini.lineWidth = 1.6; mini.stroke(); }
    });
  }

  function allRacers() {
    var out = racers.slice();
    for (var k in remotes) if (remotes.hasOwnProperty(k)) out.push(remotes[k]);
    return out;
  }

  function standings() {
    return allRacers().slice().sort(function (a, b) {
      if (a.finished !== b.finished) return a.finished ? -1 : 1;
      if (a.finished && b.finished) return (a.finishTime || 0) - (b.finishTime || 0);
      return b.progress - a.progress;
    });
  }

  function drawHUD() {
    var order = standings();
    var pos = order.indexOf(me) + 1;
    $('h-time').textContent = fmt(state.phase === 'racing' || state.phase === 'done'
      ? state.time : 0);
    $('h-lap').textContent = Math.min(me.lap + 1, CFG.laps) + ' / ' + CFG.laps;
    $('h-pos').textContent = pos + ' / ' + order.length;
    $('h-best').textContent = me.bestLap ? fmt(me.bestLap) : '--:--';
    var kmh = Math.abs(me.speed) * 7.2;
    $('sp-val').textContent = Math.round(kmh);
    $('speedfill').style.width = clamp(kmh / (MAX_SPEED * 7.2 * 1.36) * 100, 0, 100) + '%';
    $('nitrofill').style.width = (me.nitro * 100) + '%';

    var html = '';
    order.slice(0, 8).forEach(function (r, i) {
      var gap = r.finished ? fmt(r.finishTime)
        : (r === me ? 'L' + (r.lap + 1) : (r.progress >= me.progress ? '+' : '-') +
          Math.abs(Math.round((r.progress - me.progress) / SAMPLES * TRACK_LEN / 10) / 10) + 's');
      html += '<div class="drv' + (r === me ? ' me' : '') + '">' +
        '<span class="dot" style="background:#' + r.color.toString(16).padStart(6, '0') +
        ';color:#' + r.color.toString(16).padStart(6, '0') + '"></span>' +
        '<span style="width:14px;color:#8fa6cf">' + (i + 1) + '</span>' +
        '<span class="nm">' + esc(r.name) + (r.kind === 'remote' ? ' 🌐' : '') + '</span>' +
        '<span class="gp">' + gap + '</span></div>';
    });
    $('st-list').innerHTML = html;
  }

  /* ===================================================================
     10. MULTIPLAYER
     =================================================================== */
  var NET = {
    on: !!(CFG.api && CFG.room),
    pid: CFG.pid || null,
    lastSend: 0, lastOk: 0, startAt: 0, failed: 0, joined: false
  };
  function api(path, body) {
    var url = CFG.api + path;
    var opt = body
      ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
      : { method: 'GET' };
    return fetch(url, opt).then(function (r) { return r.json(); });
  }
  function netJoin() {
    if (!NET.on) return;
    api('/api/join', { room: CFG.room, name: CFG.player, pid: NET.pid })
      .then(function (r) {
        if (r && r.pid) {
          NET.pid = r.pid; NET.joined = true; NET.failed = 0;
          if (r.player && typeof r.player.slot === 'number') {
            me.color = PALETTE[r.player.slot % PALETTE.length];
          }
          $('lobby').textContent = 'Connected to room ' + CFG.room + ' as ' + CFG.player;
        }
      })
      .catch(function () {
        NET.failed++;
        $('lobby').textContent = 'Could not reach the race server — racing offline.';
      });
  }
  function netTick(now) {
    if (!NET.on || !NET.joined) return;
    if (now - NET.lastSend < 0.08) return;
    NET.lastSend = now;
    api('/api/pos', {
      room: CFG.room, pid: NET.pid, x: me.x, z: me.z, angle: me.angle,
      speed: me.speed, lap: me.lap, progress: me.progress,
      finished: me.finished, time: state.time,
      start: state.pendingStartBroadcast || false, start_delay: 3.2
    }).then(function (r) {
      state.pendingStartBroadcast = false;
      if (!r || r.error) return;
      NET.lastOk = now;
      NET.startAt = r.start_at || 0;
      NET.serverNow = r.now;
      syncRemotes(r.players || []);
      if (state.phase === 'ready' && NET.startAt && r.now < NET.startAt) {
        beginCountdown(Math.max(0.5, NET.startAt - r.now));
      }
    }).catch(function () { NET.failed++; });
  }
  function syncRemotes(list) {
    var seen = {};
    list.forEach(function (p) {
      if (!p || p.pid === NET.pid) return;
      seen[p.pid] = true;
      var r = remotes[p.pid];
      if (!r) {
        r = makeRacer({ id: p.pid, name: p.name, kind: 'remote',
          color: PALETTE[(p.slot || 0) % PALETTE.length], slot: (p.slot || 0) });
        r.kind = 'remote';
        remotes[p.pid] = r;
        showMsg('🏎️ ' + esc(p.name) + ' joined the race');
        AUDIO.cheer(0.3, 1.5);
      }
      r.netX = p.x; r.netZ = p.z; r.netAngle = p.angle;
      r.speed = p.speed || 0; r.lap = p.lap || 0;
      r.progress = p.progress || 0; r.finished = !!p.finished;
      r.finishTime = p.time || r.finishTime;
    });
    for (var pid in remotes) {
      if (remotes.hasOwnProperty(pid) && !seen[pid]) {
        scene.remove(remotes[pid].mesh);
        delete remotes[pid];
      }
    }
  }
  function moveRemotes(dt) {
    for (var pid in remotes) {
      if (!remotes.hasOwnProperty(pid)) continue;
      var r = remotes[pid];
      if (r.netX == null) continue;
      var k = 1 - Math.pow(0.0001, dt);
      r.x = lerp(r.x, r.netX, k);
      r.z = lerp(r.z, r.netZ, k);
      var d = ((r.netAngle - r.angle + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
      r.angle += d * k;
    }
  }

  function saveResult(r, position, field) {
    var payload = {
      driver: r.name, position: position, field: field,
      total_time: r.finishTime, best_lap: r.bestLap, laps: CFG.laps,
      track: CFG.track, power: CFG.power, top_speed: Math.round(r.topSpeed * 7.2),
      crashes: r.crashes, room: CFG.room || ''
    };
    // Local mirror so the board still works with no server.
    try {
      var key = 'turbo_leaderboard';
      var lb = JSON.parse(localStorage.getItem(key) || '[]');
      var row = null;
      for (var i = 0; i < lb.length; i++) if (lb[i].driver === r.name) row = lb[i];
      if (!row) { row = { driver: r.name, wins: 0, races: 0, points: 0, best: null }; lb.push(row); }
      row.races++;
      if (position === 1) row.wins++;
      row.points += Math.max(0, field - position + 1) * 40 + (position === 1 ? 60 : 0);
      if (r.finishTime != null && (row.best == null || r.finishTime < row.best)) row.best = r.finishTime;
      localStorage.setItem(key, JSON.stringify(lb));
      localStorage.setItem('turbo_last_driver', r.name);
    } catch (e) { /* storage disabled — no problem */ }
    if (CFG.api) {
      api('/api/result', payload).then(function () {
        $('save-note').textContent = '✅ Saved to the league leaderboard.';
      }).catch(function () {
        $('save-note').textContent = '⚠️ Offline — result stored in this browser only.';
      });
    } else {
      $('save-note').textContent = 'Result stored in this browser.';
    }
  }

  /* ===================================================================
     11. RACE FLOW
     =================================================================== */
  var state = {
    phase: 'ready',      // ready | countdown | racing | done
    time: 0, raceStart: 0, countdown: 0, lastBeep: -1, autopilot: false,
    pendingStartBroadcast: false
  };

  function beginCountdown(seconds) {
    if (state.phase !== 'ready') return;
    AUDIO.start();
    AUDIO.baseCrowd = 0.055;
    AUDIO.cheer(0.3, 3);
    $('screen-start').style.display = 'none';
    state.phase = 'countdown';
    state.countdown = seconds || 3.6;
    state.lastBeep = -1;
    if (NET.on) state.pendingStartBroadcast = true;
  }

  function startRacing() {
    state.phase = 'racing';
    state.raceStart = state.clock;
    state.time = 0;
    racers.forEach(function (r) { r.lapStart = 0; });
    bigToast('GO!', '#34d399');
    AUDIO.beep(true);
    AUDIO.cheer(0.42, 3.5);
    lightBulbs.forEach(function (b) { b.material.color.set(0x0d3a1a); });
  }

  function endRace() {
    if (state.phase === 'done') return;
    state.phase = 'done';
    var order = standings();
    var myPos = order.indexOf(me) + 1;
    var won = myPos === 1;
    AUDIO.fanfare(won);
    bigToast(won ? '🏆 WINNER!' : 'P' + myPos, won ? '#fbbf24' : '#e8eefc');
    saveResult(me, myPos, order.length);

    var rows = order.map(function (r, i) {
      return '<tr class="' + (r === me ? 'me' : '') + '"><td>' + (i + 1) + '</td><td>' +
        esc(r.name) + '</td><td>' + (r.finished ? fmt(r.finishTime) : 'DNF') + '</td><td>' +
        (r.bestLap ? fmt(r.bestLap) : '--') + '</td></tr>';
    }).join('');
    $('res-title').textContent = won ? '🏆 Victory!' : 'Race finished — P' + myPos;
    $('res-body').innerHTML =
      '<table class="res"><tr><th>Pos</th><th>Driver</th><th>Total</th><th>Best lap</th></tr>' +
      rows + '</table>' +
      '<div><span class="tag">Top speed ' + Math.round(me.topSpeed * 7.2) + ' km/h</span>' +
      '<span class="tag">Contacts ' + me.crashes + '</span>' +
      '<span class="tag">' + LAY.name + '</span>' +
      '<span class="tag">Engine ' + CFG.power + '/5</span></div>';
    $('screen-result').style.display = 'flex';
  }

  function resetRace() {
    $('screen-result').style.display = 'none';
    $('save-note').textContent = '';
    racers.forEach(function (r, i) {
      var pose = gridPose(i);
      r.x = pose.x; r.z = pose.z; r.angle = pose.angle; r.idx = pose.idx;
      r.sector = Math.floor(pose.idx / (SAMPLES / SECTORS));
      r.speed = 0; r.lap = 0; r.laps = []; r.bestLap = null; r.lapStart = 0;
      r.finished = false; r.finishTime = null; r.progress = 0;
      r.nitro = 1; r.crashes = 0; r.topSpeed = 0;
    });
    state.phase = 'ready';
    state.time = 0;
    lightBulbs.forEach(function (b) { b.material.color.set(0x3a0d0d); });
    $('screen-start').style.display = 'flex';
    if (NET.on) api('/api/pos', { room: CFG.room, pid: NET.pid, reset_start: true }).catch(function () {});
  }

  /* ===================================================================
     12. FULLSCREEN
     =================================================================== */
  var expanded = false;
  function toggleFullscreen() {
    var el = document.documentElement;
    var fsActive = document.fullscreenElement || document.webkitFullscreenElement;
    if (fsActive) {
      (document.exitFullscreen || document.webkitExitFullscreen).call(document);
      return;
    }
    // Streamlit renders us in an iframe: make sure it may go fullscreen.
    try {
      if (window.frameElement) {
        window.frameElement.setAttribute('allowfullscreen', 'true');
        window.frameElement.setAttribute('allow', 'fullscreen; autoplay');
      }
    } catch (e) { /* cross-origin: ignore */ }
    var req = el.requestFullscreen || el.webkitRequestFullscreen || el.msRequestFullscreen;
    if (req) {
      var p = req.call(el);
      if (p && p.catch) p.catch(expandInPage);
    } else {
      expandInPage();
    }
    setTimeout(resize, 120);
  }
  function expandInPage() {
    // Fallback: blow the iframe up to fill the host page.
    try {
      var fe = window.frameElement;
      if (!fe) { showMsg('Fullscreen blocked by the browser'); return; }
      expanded = !expanded;
      if (expanded) {
        fe.dataset.oldStyle = fe.getAttribute('style') || '';
        fe.setAttribute('style',
          'position:fixed;inset:0;width:100vw;height:100vh;z-index:2147483647;border:0;background:#05070f');
      } else {
        fe.setAttribute('style', fe.dataset.oldStyle || '');
      }
      showMsg(expanded ? 'Theatre mode — press F to exit' : 'Theatre mode off');
    } catch (e) {
      showMsg('Fullscreen blocked by the browser');
    }
    setTimeout(resize, 150);
  }
  document.addEventListener('fullscreenchange', function () { setTimeout(resize, 60); });

  /* ===================================================================
     13. MAIN LOOP
     =================================================================== */
  function updateCarVisual(r, dt) {
    r.mesh.position.set(r.x, 0, r.z);
    r.mesh.rotation.y = r.angle;
    var roll = clamp((r.steer || 0) * clamp(r.speed / MAX_SPEED, 0, 1) * 0.12, -0.12, 0.12);
    r.mesh.rotation.z = lerp(r.mesh.rotation.z || 0, -roll, 0.2);
    var spin = r.speed * dt * 1.6;
    r.mesh.userData.wheels.forEach(function (w, i) {
      w.rotation.x -= spin;
      if (i < 2) w.rotation.y = (r.steer || 0) * 0.35;
    });
    var f = r.mesh.userData.flame;
    f.visible = !!r.boosting;
    if (f.visible) f.scale.set(1, 0.7 + Math.random() * 0.7, 1);
    r.mesh.userData.plate.visible = (r !== me) || camMode === 'top';
  }

  var last = performance.now();
  function frame(now) {
    requestAnimationFrame(frame);
    var dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    state.clock = (state.clock || 0) + dt;

    if (state.phase === 'countdown') {
      state.countdown -= dt;
      var n = Math.ceil(state.countdown - 0.6);
      if (n !== state.lastBeep && n >= 1 && n <= 3) {
        state.lastBeep = n;
        bigToast(String(n), '#f87171');
        AUDIO.beep(false);
        for (var b = 0; b < lightBulbs.length; b++) {
          lightBulbs[b].material.color.set(b < (4 - n) * 1.6 ? 0xff2d2d : 0x3a0d0d);
        }
      }
      if (state.countdown <= 0.6 && state.lastBeep !== 0) { state.lastBeep = 0; }
      if (state.countdown <= 0) startRacing();
    }

    if (state.phase === 'racing') {
      state.time = state.clock - state.raceStart;
      var ctrl = {
        up: keys['ArrowUp'] || keys['w'] || keys['W'] || touch.up,
        down: keys['ArrowDown'] || keys['s'] || keys['S'] || touch.down,
        left: keys['ArrowLeft'] || keys['a'] || keys['A'] || touch.l,
        right: keys['ArrowRight'] || keys['d'] || keys['D'] || touch.r,
        boost: keys[' '] || keys['Spacebar'] || touch.boost
      };
      if (!me.finished) {
        if (state.autopilot) driveAI(me, dt);      // demo / self-test mode
        else driveHuman(me, dt, ctrl);
      }
      if (hotseat && !hotseat.finished) {
        driveHuman(hotseat, dt, {
          up: keys['i'] || keys['I'], down: keys['k'] || keys['K'],
          left: keys['j'] || keys['J'], right: keys['l'] || keys['L'],
          boost: keys['u'] || keys['U']
        });
      }
      racers.forEach(function (r) {
        if (r.kind === 'ai' && !r.finished) driveAI(r, dt);
      });
      collide(dt);
      moveRemotes(dt);
      racers.forEach(function (r) { if (!r.finished) updateLap(r, state.time); });
    } else {
      moveRemotes(dt);
      racers.forEach(function (r) { r.speed *= 0.9; });
    }

    // audio per-frame
    var rivalDist = 9999;
    allRacers().forEach(function (r) {
      if (r === me) return;
      rivalDist = Math.min(rivalDist, Math.hypot(r.x - me.x, r.z - me.z));
    });
    var sr = clamp(Math.abs(me.speed) / MAX_SPEED, 0, 1.4);
    AUDIO.drive({
      running: state.phase !== 'ready',
      speedRatio: sr,
      throttle: !!(keys['ArrowUp'] || keys['w'] || touch.up),
      boost: me.boosting,
      screech: state.phase === 'racing' &&
        ((me.offTrack && Math.abs(me.speed) > 6) ||
         (Math.abs(me.steer || 0) > 0.5 && Math.abs(me.speed) > MAX_SPEED * 0.62)),
      rivalDist: rivalDist,
      crowd: (AUDIO.baseCrowd || 0.05) + (state.phase === 'racing' ? sr * 0.02 : 0)
    });

    allRacers().forEach(function (r) { updateCarVisual(r, dt); });

    // crowd animation
    var ct = state.clock * 3;
    crowdMeshes.forEach(function (m) {
      m.position.y = Math.sin(ct + m.userData.phase) * 0.16;
    });

    updateCamera(dt);
    drawHUD();
    drawMini();
    netTick(state.clock);

    if (msgTimer > 0) {
      msgTimer -= dt;
      if (msgTimer <= 0) $('msg').style.opacity = 0;
    }
    renderer.render(scene, camera);
  }

  /* ===================================================================
     14. BOOT
     =================================================================== */
  $('btn-start').addEventListener('click', function () { beginCountdown(); });
  $('btn-again').addEventListener('click', function () { resetRace(); });
  $('btn-fs').addEventListener('click', toggleFullscreen);
  $('btn-cam').addEventListener('click', cycleCamera);
  $('btn-mute').addEventListener('click', function () {
    AUDIO.start();
    this.textContent = AUDIO.toggleMute() ? '🔇 Sound' : '🔊 Sound';
  });
  $('btn-help').addEventListener('click', function () {
    $('screen-start').style.display =
      $('screen-start').style.display === 'flex' ? 'none' : 'flex';
  });

  $('start-track').textContent = LAY.name;
  $('start-laps').textContent = CFG.laps;
  $('start-field').textContent = racers.length + (NET.on ? '+' : '');
  if (NET.on) {
    $('lobby').textContent = 'Joining room ' + CFG.room + '…';
    netJoin();
    setInterval(function () { if (!NET.joined) netJoin(); }, 4000);
    window.addEventListener('beforeunload', function () {
      if (NET.pid) navigator.sendBeacon && navigator.sendBeacon(
        CFG.api + '/api/leave',
        new Blob([JSON.stringify({ room: CFG.room, pid: NET.pid })], { type: 'application/json' }));
    });
  } else {
    $('lobby').textContent = '';
  }

  resize();
  window.__RACE_READY__ = true;
  window.__RACE_DEBUG__ = {
    state: state, racers: racers, me: me, cfg: CFG,
    startCountdown: beginCountdown, layout: LAY, trackLen: TRACK_LEN,
    autopilot: function (on) { state.autopilot = !!on; },
    reset: resetRace
  };
  requestAnimationFrame(frame);
})();
"""


def _body_html(cfg: Dict[str, Any]) -> str:
    return """
<div id="wrap">
  <canvas id="scene"></canvas>

  <div id="hud" class="panel">
    <div class="row"><span>Time</span><b class="big" id="h-time">0:00.00</b></div>
    <div class="row"><span>Lap</span><b id="h-lap">1 / 3</b></div>
    <div class="row"><span>Position</span><b id="h-pos">1 / 1</b></div>
    <div class="row"><span>Best lap</span><b id="h-best">--:--</b></div>
  </div>

  <div id="standings" class="panel">
    <h4>Race order</h4>
    <div id="st-list"></div>
  </div>

  <div id="tools">
    <button id="btn-fs" title="Fullscreen (F)">⛶ Fullscreen</button>
    <button id="btn-cam" title="Camera (C)">🎥 Camera</button>
    <button id="btn-mute" title="Mute (M)">🔊 Sound</button>
    <button id="btn-help">❔ Help</button>
  </div>

  <div id="speedo" class="panel">
    <div class="val" id="sp-val">0</div>
    <div class="unit">KM / H</div>
    <div id="speedbar"><div id="speedfill"></div></div>
    <div id="nitrobar"><div id="nitrofill"></div></div>
  </div>

  <div id="minimap" class="panel"><canvas id="mini" width="150" height="150"></canvas></div>

  <div id="toast"></div>
  <div id="msg"></div>

  <div class="screen" id="screen-start" style="display:flex">
    <div class="card">
      <h1>🏁 TURBO RACING LEAGUE</h1>
      <p><b id="start-track">Track</b> &nbsp;•&nbsp; <b id="start-laps">3</b> laps
         &nbsp;•&nbsp; <b id="start-field">1</b> cars on the grid</p>
      <div class="keys">
        <div><b>Steer</b> ← → or A / D</div>
        <div><b>Throttle</b> ↑ or W</div>
        <div><b>Brake</b> ↓ or S</div>
        <div><b>Nitro</b> Spacebar</div>
        <div><b>Camera</b> C</div>
        <div><b>Fullscreen</b> F</div>
        <div><b>Mute</b> M</div>
        <div><b>Recover</b> R</div>
      </div>
      <div id="lobby"></div>
      <button class="btn" id="btn-start">🟢 START RACE</button>
      <p style="margin-top:14px">Sound switches on when the race starts — headphones recommended.</p>
      <div id="loaderr"></div>
    </div>
  </div>

  <div class="screen" id="screen-result" style="display:none">
    <div class="card">
      <h2 id="res-title">Race finished</h2>
      <div id="res-body"></div>
      <div id="save-note" style="color:#86efac;font-size:12px;margin:8px 0"></div>
      <button class="btn" id="btn-again">🔁 RACE AGAIN</button>
    </div>
  </div>
</div>
"""


def build_game_html(cfg: Dict[str, Any]) -> str:
    """Full standalone HTML document (used by Streamlit's components.html)."""
    conf = dict(DEFAULT_CFG)
    conf.update(cfg or {})
    scripts = "\n".join(
        '<script src="%s" onerror="window.__threeFail=(window.__threeFail||0)+1"></script>' % s
        for s in THREE_SOURCES[:1]
    )
    fallback = """
<script>
if (typeof THREE === 'undefined') {
  var srcs = %s;
  (function load(i){
    if (i >= srcs.length) { return; }
    var s = document.createElement('script');
    s.src = srcs[i]; s.async = false;
    s.onerror = function(){ load(i+1); };
    document.head.appendChild(s);
  })(0);
}
</script>""" % json.dumps(THREE_SOURCES[1:])
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1,user-scalable=no'>"
        "<title>Turbo Racing League</title>"
        "%s<style>%s</style>%s%s</head><body>%s"
        "<script>window.__RACE_CFG__ = %s;</script>"
        "<script>\n%s\n</script></body></html>"
    ) % (FONT_LINK, GAME_CSS, scripts, fallback, _body_html(conf),
         json.dumps(conf), GAME_JS)


def build_artifact_body(cfg: Dict[str, Any]) -> str:
    """Body-only fragment (for hosts that supply their own HTML skeleton)."""
    conf = dict(DEFAULT_CFG)
    conf.update(cfg or {})
    return (
        "<title>Turbo Racing League</title>%s<style>%s</style>"
        '<script src="%s"></script>%s'
        "<script>window.__RACE_CFG__ = %s;</script><script>\n%s\n</script>"
    ) % (FONT_LINK, GAME_CSS, THREE_SOURCES[0], _body_html(conf), json.dumps(conf), GAME_JS)
