(function () {
  'use strict';
  var root = document.documentElement;
  var clamp = function (v, a, b) { return Math.min(b === undefined ? 1 : b, Math.max(a || 0, v)); };
  var lerp = function (a, b, t) { return a + (b - a) * t; };
  var ease = function (t) { return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
  var mq = window.matchMedia('(prefers-reduced-motion: reduce)');
  var reduce = false;
  function ramp(x, a, b) {
    if (reduce) return x >= (a + b) / 2 ? 1 : 0;
    return clamp((x - a) / (b - a));
  }
  function store(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  /* ---------------- prototype controls ---------------- */
  var sysBtns = document.querySelectorAll('.dock [data-sys]');
  function setSys(s) {
    if (s === 'vale') { root.setAttribute('data-sys', 'vale'); } else root.removeAttribute('data-sys');
    sysBtns.forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-sys') === s)); });
    store('devboot-proto-sistema', s);
    requestAnimationFrame(function () { measure(); frame(); });
  }
  sysBtns.forEach(function (b) { b.addEventListener('click', function () { setSys(b.getAttribute('data-sys')); }); });
  setSys(root.getAttribute('data-sys') === 'vale' ? 'vale' : 'neutro');

  var themeBtn = document.getElementById('themeBtn');
  function isDark() {
    var t = root.getAttribute('data-theme');
    if (t) return t === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  function labelTheme() {
    var l = isDark() ? 'Mudar para o tema claro' : 'Mudar para o tema escuro';
    themeBtn.setAttribute('aria-label', l); themeBtn.setAttribute('title', l);
  }
  themeBtn.addEventListener('click', function () {
    var dark = !isDark();
    root.setAttribute('data-theme', dark ? 'dark' : 'light');
    store('devboot-tema', dark ? 'escuro' : 'claro');
    labelTheme();
  });
  labelTheme();

  var motionBtn = document.getElementById('motionBtn');
  function setReduce() {
    reduce = mq.matches || root.getAttribute('data-motion') === 'menos';
    root.classList.toggle('reduce', reduce);
    motionBtn.setAttribute('aria-pressed', String(root.getAttribute('data-motion') === 'menos'));
  }
  motionBtn.addEventListener('click', function () {
    var on = root.getAttribute('data-motion') !== 'menos';
    if (on) root.setAttribute('data-motion', 'menos'); else root.removeAttribute('data-motion');
    store('devboot-proto-movimento', on ? 'menos' : 'normal');
    setReduce(); frame();
  });
  if (mq.addEventListener) mq.addEventListener('change', function () { setReduce(); frame(); });
  setReduce();

  /* ---------------- WhatsApp: compose the link, never open it ---------------- */
  var MSG = {
    geral: 'Olá, vim pelo site da Devboot e quero conversar.',
    sistema: 'Olá, vim pelo site da Devboot e quero conversar sobre um sistema.',
    automacao: 'Olá, vim pelo site da Devboot e quero conversar sobre automação.',
    cameras: 'Olá, vim pelo site da Devboot e quero um orçamento de câmeras.',
    acesso: 'Olá, vim pelo site da Devboot e quero um orçamento de controle de acesso.'
  };
  var toast = document.getElementById('toast'), toastUrl = document.getElementById('toastUrl'), tTimer;
  var toastText = document.getElementById('toastText');
  function showToast(url, msg) {
    toastText.textContent = '\u201c' + msg + '\u201d';
    toastUrl.textContent = url;
    toast.classList.add('show');
    clearTimeout(tTimer); tTimer = setTimeout(function () { toast.classList.remove('show'); }, 9000);
  }
  document.querySelectorAll('[data-wa]').forEach(function (b) {
    b.addEventListener('click', function () {
      var m = MSG[b.getAttribute('data-wa')] || MSG.geral;
      showToast('https://wa.me/5587991402037?text=' + encodeURIComponent(m), m);
    });
  });
  document.getElementById('toastClose').addEventListener('click', function () { toast.classList.remove('show'); });
  function copyText(text, btn) {
    var done = function () { var o = btn.textContent; btn.textContent = 'Copiado'; setTimeout(function () { btn.textContent = o; }, 1600); };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () { selectText(btn); });
    } else selectText(btn);
  }
  function selectText(btn) {
    var el = btn.id === 'toastCopy' ? toastUrl : btn.parentNode;
    var r = document.createRange(); r.selectNodeContents(el);
    var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
  }
  document.getElementById('toastCopy').addEventListener('click', function (e) { copyText(toastUrl.textContent, e.currentTarget); });
  document.querySelectorAll('[data-copy]').forEach(function (b) {
    b.addEventListener('click', function () { copyText(b.getAttribute('data-copy'), b); });
  });

  /* ---------------- scroll driver: reads position, writes transform/opacity/clip-path only ---------------- */
  function progress(sec, st) {
    var r = sec.getBoundingClientRect();
    var dist = sec.offsetHeight - st.offsetHeight;
    var top = parseFloat(getComputedStyle(st).top) || 0;
    return dist > 0 ? clamp((top - r.top) / dist) : 0;
  }

  // hero
  var hero = document.getElementById('topo'), hs = hero.querySelector('.sticky');
  var comp = hero.querySelector('.comp'), slot = comp.querySelector('.ph-slot'), fly = hero.querySelector('.fly');
  var fades = comp.querySelectorAll('.fade'), copyA = hero.querySelector('.copy-a'), copyB = hero.querySelector('.copy-b');
  var heroCap = hero.querySelector('.hero-cap');
  var M = null;

  // stage
  var stage = document.getElementById('frentes'), ss = stage.querySelector('.sticky');
  var U = 6.4;
  var scSw = stage.querySelector('.sc-sw'), swPhone = stage.querySelector('.sw-phone'), swLaptop = scSw.querySelector('.laptop');
  var swTops = scSw.querySelectorAll('.swap-top');
  var scAuto = stage.querySelector('.sc-auto'), scCam = stage.querySelector('.sc-cam'), camPhoto = scCam.querySelector('.photo');
  var camImg = scCam.querySelector('img');
  var scAccPhoto = stage.querySelector('.sc-acc-photo'), scAcc = stage.querySelector('.sc-acc'), screenOff = stage.querySelector('.screen-off');
  var beats = stage.querySelectorAll('.beat'), bars = stage.querySelectorAll('.rail .bar i'), railBtns = stage.querySelectorAll('.rail button');
  var mediaCap = stage.querySelector('.media-cap');
  var CAPS = [
    [1.5, 'Na tela: ConferePlaca, sistema web da Devboot.'],
    [2.0, 'Na tela: CamSeek, ferramenta de projeto de CFTV da Devboot.'],
    [4.0, 'Imagem pendente: depende do caso real de automação.'],
    [5.0, 'Foto: Intelbras. Câmera bullet VIP 5440 IA, vendida na loja.'],
    [5.5, 'Foto: Intelbras. Controlador facial SS 3542 MF, vendido na loja.'],
    [99, 'Controlador facial Intelbras SS 3542 MF.']
  ];
  var lastBeat = -1, lastCap = '';
  var closeMedia = document.querySelector('.close-media');

  function measure() {
    comp.style.transform = '';
    var H = hs.clientHeight, W = hs.clientWidth, desk = W >= 900;
    // place the composition under the first headline
    var aBottom = copyA.offsetTop + copyA.offsetHeight;
    comp.style.setProperty('--comp-top', (aBottom + Math.max(18, H * .03)) + 'px');
    var sr = hs.getBoundingClientRect(), cr = comp.getBoundingClientRect(), pr = slot.getBoundingClientRect();
    var room = parseFloat(getComputedStyle(root).getPropertyValue('--dock-room')) || 76;
    var bBottom = copyB.offsetTop + copyB.offsetHeight;
    // phone: the zoomed phone sits between the second headline and the dock, never over either
    var PH = desk ? H * .8 : Math.min(H * .52, H - room + 8 - bBottom - 14), PW = PH * 9 / 19.5;
    if (!desk && PW > W * .62) { PW = W * .62; PH = PW * 19.5 / 9; }
    fly.style.width = PW + 'px'; fly.style.height = PH + 'px';
    var cx = desk ? W * .7 : W / 2;
    var cy = desk ? H * .52 : H - room - PH / 2 + 8;
    M = {
      H: H, W: W, cl: cr.left - sr.left, ct: cr.top - sr.top, cw: cr.width, ch: cr.height,
      sl: pr.left - sr.left, st: pr.top - sr.top, sw: pr.width, PW: PW, PH: PH,
      tx: cx - PW / 2, ty: cy - PH / 2
    };
    // phone: the frame may grow past the screen edges (clipped); desktop: it stops at the edges
    M.sg = desk ? Math.min(1.14, (W * .98) / M.cw, (H * .9) / M.ch) : Math.min(1.3, (H * .9) / M.ch);
    M.dy = H * .5 - (M.ct + M.ch / 2);
  }

  function heroFrame() {
    var p = progress(hero, hs);
    if (reduce) {
      comp.style.transform = '';
      var b = p > .45 ? 1 : 0;
      copyA.style.transform = copyB.style.transform = '';
      copyA.style.opacity = 1 - b; copyB.style.opacity = b;
      heroCap.style.opacity = 1 - b;
      fades.forEach(function (f) { f.style.opacity = 1; });
      var sx0 = M.sl, sy0 = M.st;
      fly.style.transform = 'translate3d(' + sx0 + 'px,' + sy0 + 'px,0) scale(' + (M.sw / M.PW) + ')';
      comp.style.opacity = 1 - b * .85;
      return;
    }
    comp.style.opacity = '';
    var g = ease(ramp(p, 0, .3)), z = ease(ramp(p, .34, .74));
    var s = lerp(1, M.sg, g), dy = M.dy * g;
    comp.style.transform = 'translate3d(0,' + dy.toFixed(2) + 'px,0) scale(' + (s * (1 + .1 * z)).toFixed(4) + ')';
    var cx = M.cl + M.cw / 2, cy = M.ct + M.ch / 2;
    var sx = cx + (M.sl - cx) * s, sy = cy + dy + (M.st - cy) * s, sw = M.sw * s;
    var bx = lerp(sx, M.tx, z), by = lerp(sy, M.ty, z), bw = lerp(sw, M.PW, z);
    fly.style.transform = 'translate3d(' + bx.toFixed(2) + 'px,' + by.toFixed(2) + 'px,0) scale(' + (bw / M.PW).toFixed(4) + ')';
    var fo = 1 - ramp(p, .36, .62);
    fades.forEach(function (f) { f.style.opacity = fo.toFixed(3); });
    var a = ramp(p, .06, .24);
    copyA.style.opacity = (1 - a).toFixed(3);
    copyA.style.transform = 'translate3d(0,' + (-36 * a).toFixed(1) + 'px,0)';
    var bIn = ramp(p, .58, .74);
    copyB.style.opacity = bIn.toFixed(3);
    copyB.style.transform = 'translate3d(0,' + (28 * (1 - bIn)).toFixed(1) + 'px,0)';
    heroCap.style.opacity = (1 - ramp(p, .03, .16)).toFixed(3);
  }

  function setT(el, t) { el.style.transform = reduce ? '' : t; }

  function stageFrame() {
    var p = progress(stage, ss), u = p * U;
    // beats swap in place
    var bi = u < 1 ? 0 : u < 2 ? 1 : u < 4 ? 2 : u < 5 ? 3 : 4;
    if (bi !== lastBeat) {
      beats.forEach(function (b, i) { b.classList.toggle('on', i === bi); b.classList.toggle('past', i < bi); });
      var ch = bi < 2 ? 0 : bi < 3 ? 1 : 2;
      railBtns.forEach(function (b, i) { if (i === ch) b.setAttribute('aria-current', 'step'); else b.removeAttribute('aria-current'); });
      lastBeat = bi;
    }
    for (var c = 0; c < CAPS.length; c++) if (u < CAPS[c][0]) { if (CAPS[c][1] !== lastCap) { mediaCap.textContent = CAPS[c][1]; lastCap = CAPS[c][1]; } break; }
    bars[0].style.transform = 'scaleX(' + clamp(u / 2).toFixed(3) + ')';
    bars[1].style.transform = 'scaleX(' + clamp((u - 2) / 2).toFixed(3) + ')';
    bars[2].style.transform = 'scaleX(' + clamp((u - 4) / 2.4).toFixed(3) + ')';

    // software: laptop settles, phone slides in, screens change product, then the scene steps back
    var e1 = ease(ramp(u, 0, .6)), e2 = ease(ramp(u, .4, .95));
    setT(swLaptop, 'scale(' + lerp(.94, 1, e1).toFixed(4) + ')');
    setT(swPhone, 'translate3d(' + (40 * (1 - e2)).toFixed(1) + '%,' + (6 * (1 - e2)).toFixed(1) + '%,0)');
    swPhone.style.opacity = e2.toFixed(3);
    var sw = ramp(u, 1.35, 1.65);
    swTops.forEach(function (t) { t.style.opacity = sw.toFixed(3); });
    var rec = ease(ramp(u, 1.9, 2.3)), out = ramp(u, 3.72, 3.98);
    setT(scSw, 'scale(' + (1 - .14 * rec).toFixed(4) + ')');
    scSw.style.opacity = ((1 - .86 * rec) * (1 - out)).toFixed(3);

    // automação: the honest gap
    var ai = ramp(u, 2.1, 2.4) * (1 - ramp(u, 3.65, 3.92));
    scAuto.style.opacity = ai.toFixed(3);
    setT(scAuto, 'translate3d(0,' + (16 * (1 - ramp(u, 2.1, 2.4))).toFixed(1) + 'px,0)');

    // câmeras: the photo opens out of a smaller frame
    var ci = ease(ramp(u, 3.85, 4.5));
    scCam.style.opacity = (ramp(u, 3.78, 3.95) * (1 - ramp(u, 4.92, 5.18))).toFixed(3);
    if (reduce) { camPhoto.style.clipPath = ''; camImg.style.transform = ''; }
    else {
      camPhoto.style.clipPath = 'inset(' + (16 * (1 - ci)).toFixed(2) + '% ' + (12 * (1 - ci)).toFixed(2) + '% round ' + lerp(34, 22, ci).toFixed(1) + 'px)';
      camImg.style.transform = 'scale(' + (lerp(1.2, 1, ci) * (1 + .05 * ramp(u, 4.5, 5.1))).toFixed(4) + ')';
    }

    // acesso: photo, then the device alone, then its screen lights up
    var ap = ramp(u, 4.92, 5.18) * (1 - ramp(u, 5.45, 5.75));
    scAccPhoto.style.opacity = ap.toFixed(3);
    setT(scAccPhoto, 'scale(' + (1 + .06 * ramp(u, 5.1, 5.75)).toFixed(4) + ')');
    var ar = ease(ramp(u, 5.45, 5.85));
    scAcc.style.opacity = ar.toFixed(3);
    setT(scAcc, 'translate3d(0,' + (8 * (1 - ar)).toFixed(2) + '%,0) scale(' + lerp(.9, 1, ar).toFixed(4) + ')');
    screenOff.style.opacity = (1 - ramp(u, 5.85, 6.15)).toFixed(3);
  }

  function closeFrame() {
    if (reduce) { closeMedia.style.transform = ''; closeMedia.style.opacity = ''; return; }
    var r = closeMedia.getBoundingClientRect(), vh = window.innerHeight;
    var t = ease(clamp((vh - r.top) / (vh * .8)));
    closeMedia.style.transform = 'scale(' + lerp(1.22, 1, t).toFixed(4) + ')';
    closeMedia.style.opacity = lerp(.35, 1, t).toFixed(3);
  }

  function frame() {
    if (!M) measure();
    heroFrame(); stageFrame(); closeFrame();
  }

  railBtns.forEach(function (b) {
    b.addEventListener('click', function () {
      var u0 = parseFloat(b.getAttribute('data-go')) + .05;
      var top = stage.getBoundingClientRect().top + window.scrollY;
      var dist = stage.offsetHeight - ss.offsetHeight;
      window.scrollTo({ top: top + dist * (u0 / U) + 2, behavior: reduce ? 'auto' : 'smooth' });
    });
  });

  var ticking = false;
  function onScroll() { if (!ticking) { ticking = true; requestAnimationFrame(function () { ticking = false; frame(); }); } }
  window.addEventListener('scroll', onScroll, { passive: true });
  var lastW = window.innerWidth, lastH = hs.clientHeight;
  window.addEventListener('resize', function () {
    if (window.innerWidth === lastW && Math.abs(hs.clientHeight - lastH) < 2) return;
    lastW = window.innerWidth; lastH = hs.clientHeight;
    measure(); frame();
  });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { measure(); frame(); });
  window.addEventListener('load', function () { measure(); frame(); });
  measure(); frame();
})();
