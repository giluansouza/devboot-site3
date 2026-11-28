(function () {
  'use strict';
  var root = document.documentElement;
  var mq = window.matchMedia('(prefers-reduced-motion: reduce)');
  // Scroll-driven animations run on the compositor in Chromium; everything else gets the
  // IntersectionObserver states with short transitions. No script runs per scrolled frame.
  var SDA = !!(window.CSS && CSS.supports('animation-timeline: view()') && CSS.supports('view-timeline-name: --x'));
  function store(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  /* ---------------- prototype controls ---------------- */
  var dock = document.getElementById('dock'), dockToggle = document.getElementById('dockToggle'), dockPanel = document.getElementById('dockPanel');
  function setDock(open) {
    dockPanel.hidden = !open;
    dockToggle.setAttribute('aria-expanded', String(open));
  }
  dockToggle.addEventListener('click', function () { setDock(dockPanel.hidden); });
  document.addEventListener('click', function (e) { if (!dock.contains(e.target)) setDock(false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !dockPanel.hidden) { setDock(false); dockToggle.focus(); } });

  var sysBtns = dockPanel.querySelectorAll('[data-sys]');
  function setSys(s) {
    if (s === 'vale') root.setAttribute('data-sys', 'vale'); else root.removeAttribute('data-sys');
    sysBtns.forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-sys') === s)); });
    store('devboot-proto-sistema', s);
  }
  sysBtns.forEach(function (b) { b.addEventListener('click', function () { setSys(b.getAttribute('data-sys')); measureSoon(); }); });
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
  function applyMotion() {
    var reduce = mq.matches || root.getAttribute('data-motion') === 'menos';
    root.classList.toggle('reduce', reduce);
    root.classList.toggle('sda', SDA && !reduce);
    motionBtn.setAttribute('aria-pressed', String(root.getAttribute('data-motion') === 'menos'));
  }
  motionBtn.addEventListener('click', function () {
    var on = root.getAttribute('data-motion') !== 'menos';
    if (on) root.setAttribute('data-motion', 'menos'); else root.removeAttribute('data-motion');
    store('devboot-proto-movimento', on ? 'menos' : 'normal');
    applyMotion();
  });
  if (mq.addEventListener) mq.addEventListener('change', applyMotion);
  applyMotion();

  /* ---------------- WhatsApp: compose the link, never open it ---------------- */
  var MSG = {
    geral: 'Olá, vim pelo site da Devboot e quero conversar.',
    sistema: 'Olá, vim pelo site da Devboot e quero conversar sobre um sistema.',
    automacao: 'Olá, vim pelo site da Devboot e quero conversar sobre automação.',
    cameras: 'Olá, vim pelo site da Devboot e quero um orçamento de câmeras.',
    acesso: 'Olá, vim pelo site da Devboot e quero um orçamento de controle de acesso.'
  };
  var toast = document.getElementById('toast'), toastUrl = document.getElementById('toastUrl'), toastText = document.getElementById('toastText'), tTimer;
  function showToast(url, msg) {
    toastText.textContent = '“' + msg + '”';
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
  document.getElementById('toastCopy').addEventListener('click', function (e) {
    var btn = e.currentTarget, text = toastUrl.textContent;
    var done = function () { btn.textContent = 'Copiado'; setTimeout(function () { btn.textContent = 'Copiar link'; }, 1600); };
    var select = function () { var r = document.createRange(); r.selectNodeContents(toastUrl); var s = getSelection(); s.removeAllRanges(); s.addRange(r); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, select); else select();
  });

  /* ---------------- hero geometry: measured once per resize, never per frame ----------------
     The frame is laid out at the size it has at the end of the zoom, so the phone stays sharp,
     and scaled down for the earlier states. Origin = the phone's centre. */
  var hero = document.getElementById('topo'), hs = hero.querySelector('.sticky');
  var copyA = hero.querySelector('.copy-a'), copyB = hero.querySelector('.copy-b');
  var FX = 1 - .04 - .19 / 2;                 // phone centre, share of frame width
  var PHW = .19 * 19.5 / 9;                   // phone height / frame width
  var FY = 1 - .02 - (PHW * 1.45) / 2;        // phone centre, share of frame height
  function measure() {
    var H = hs.clientHeight, W = hs.clientWidth, desk = W >= 900;
    var room = parseFloat(getComputedStyle(root).getPropertyValue('--dock-room')) || 68;
    // base frame: under the first headline
    var bw = Math.min(W, 1060, H * 1.28), bh = bw / 1.45;
    var bl = (W - bw) / 2, bt = copyA.offsetTop + copyA.offsetHeight + Math.max(18, H * .03);
    // zoom target for the phone: between the second headline and the dock
    var bBottom = copyB.offsetTop + copyB.offsetHeight;
    var PH = desk ? H * .8 : Math.min(H * .54, H - room - bBottom - 6);
    if (!desk && PH * 9 / 19.5 > W * .62) PH = W * .62 * 19.5 / 9;
    var tx = desk ? W * .7 : W / 2, ty = desk ? H * .52 : H - room - PH / 2 + 6;
    var zs = PH / (PHW * bw);
    var cw = bw * zs, ch = cw / 1.45;
    // grow state: frame centred, larger (phone: may pass the screen edges)
    var gs = desk ? Math.min(1.14, (W * .98) / bw, (H * .9) / bh) : Math.min(1.3, (H * .9) / bh);
    var basePx = bl + FX * bw, basePy = bt + FY * bh;
    var growPx = W / 2 + (FX - .5) * gs * bw, growPy = H / 2 + (FY - .5) * gs * bh;
    var v = {
      '--cw': cw + 'px', '--cl': (tx - FX * cw) + 'px', '--ct': (ty - FY * ch) + 'px',
      '--ox': (FX * 100) + '%', '--oy': (FY * 100) + '%',
      '--s0': (1 / zs).toFixed(5), '--t0x': (basePx - tx).toFixed(2) + 'px', '--t0y': (basePy - ty).toFixed(2) + 'px',
      '--s1': (gs / zs).toFixed(5), '--t1x': (growPx - tx).toFixed(2) + 'px', '--t1y': (growPy - ty).toFixed(2) + 'px',
      '--capt': (bt + bh + 12) + 'px'
    };
    for (var k in v) hs.style.setProperty(k, v[k]);
    hs.classList.add('measured');
  }
  var mTimer;
  function measureSoon() { clearTimeout(mTimer); mTimer = setTimeout(measure, 60); }
  var lastW = window.innerWidth, lastH = hs.clientHeight;
  window.addEventListener('resize', function () {
    // the phone's address bar changes the height while scrolling; only a real resize re-measures
    if (window.innerWidth === lastW && Math.abs(hs.clientHeight - lastH) < 120) return;
    lastW = window.innerWidth; lastH = hs.clientHeight;
    measureSoon();
  });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(measure);
  measure();

  /* ---------------- steps: one observer per pinned section, fires only when a step changes ---------------- */
  // The state is the last step whose top has passed the middle of the screen. It is computed
  // when a step enters or leaves the screen and once when scrolling ends, so a fast fling that
  // jumps over a whole step still lands on the right one.
  var watchers = [];
  function watchSteps(section, attr, onChange) {
    var steps = section.querySelectorAll('.step');
    function update() {
      var mid = window.innerHeight / 2, i = 0;
      for (var k = 0; k < steps.length; k++) if (steps[k].getBoundingClientRect().top <= mid) i = k;
      if (section.getAttribute(attr) !== String(i)) { section.setAttribute(attr, i); if (onChange) onChange(i); }
    }
    var atMiddle = new IntersectionObserver(update, { rootMargin: '-50% 0px -50% 0px', threshold: 0 });
    var onScreen = new IntersectionObserver(update, { threshold: [0, 1] });
    steps.forEach(function (s) { atMiddle.observe(s); onScreen.observe(s); });
    watchers.push(update);
    return steps;
  }
  window.addEventListener('scrollend', function () { watchers.forEach(function (u) { u(); }); });
  watchSteps(hero, 'data-step');

  var stage = document.getElementById('frentes');
  var railBtns = stage.querySelectorAll('.rail button');
  function railFor(beat) {
    var ch = beat < 2 ? 0 : beat < 3 ? 1 : 2;
    railBtns.forEach(function (b, i) { if (i === ch) b.setAttribute('aria-current', 'step'); else b.removeAttribute('aria-current'); });
  }
  var stageSteps = watchSteps(stage, 'data-beat', railFor);
  railFor(0);
  railBtns.forEach(function (b) {
    b.addEventListener('click', function () {
      var st = stageSteps[parseInt(b.getAttribute('data-go'), 10)];
      var y = st.getBoundingClientRect().top + window.scrollY - window.innerHeight / 2 + 4;
      window.scrollTo({ top: y, behavior: root.classList.contains('reduce') ? 'auto' : 'smooth' });
    });
  });
})();
