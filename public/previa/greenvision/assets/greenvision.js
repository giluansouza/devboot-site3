/* GreenVision preview — behaviour. Nothing here listens to scroll or reads layout while scrolling.
   Reveals: IntersectionObserver class toggles, only where CSS scroll timelines are missing.
   Video: plays on wide screens only, never with reduced motion or a data saver, pauses off screen. */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var root = document.documentElement;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');

  /* ---------- WhatsApp: provisional number (W1 pending). Preview shows the link, never opens it ---------- */
  var WA = '5587991402037';
  var MSG = { gv: 'Olá! Gostaria de saber como funciona a GreenVision.' };
  var toast = $('.toast'), tlink = $('.toast-link'), tx = $('.toast-x'), ttimer = 0, lastBtn = null;

  function closeToast(back) {
    toast.hidden = true;
    clearTimeout(ttimer);
    if (back && lastBtn) lastBtn.focus();
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-wa]');
    if (!b) return;
    e.preventDefault();
    lastBtn = b;
    tlink.textContent = 'https://wa.me/' + WA + '?text=' + encodeURIComponent(MSG[b.getAttribute('data-wa')] || MSG.gv);
    toast.hidden = false;
    tx.focus({ preventScroll: true });
    clearTimeout(ttimer);
    ttimer = setTimeout(function () { closeToast(false); }, 12000);
  });
  tx.addEventListener('click', function () { closeToast(true); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !toast.hidden) closeToast(true);
  });

  /* ---------- Theme: site-wide key devboot-tema ('escuro' | 'claro'; absent = follow the system) ---------- */
  var tbtn = $('.theme');
  function effective() {
    var t = root.getAttribute('data-theme');
    if (t === 'dark' || t === 'light') return t;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  function label() { tbtn.setAttribute('aria-label', effective() === 'dark' ? 'Mudar para o tema claro' : 'Mudar para o tema escuro'); }
  tbtn.addEventListener('click', function () {
    var next = effective() === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('devboot-tema', next === 'dark' ? 'escuro' : 'claro'); } catch (e) {}
    label();
  });
  label();

  /* ---------- Reveal fallback (no CSS scroll timelines): one-shot class toggles ---------- */
  if (!root.classList.contains('sd')) {
    var targets = Array.prototype.slice.call(document.querySelectorAll('.rv, .stages'));
    if (!('IntersectionObserver' in window)) {
      targets.forEach(function (el) { el.classList.add('in'); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.12 });
      targets.forEach(function (el) { io.observe(el); });
    }
  }

  /* ---------- Click-to-play field videos (poster first; nothing downloads until the visitor asks) ---------- */
  Array.prototype.forEach.call(document.querySelectorAll('[data-video]'), function (fig) {
    var v = fig.querySelector('video'), b = fig.querySelector('.play'), want = false;
    function name() { return fig.querySelector('figcaption').textContent; }
    function apply() {
      var on = want && fig._vis !== false && !document.hidden;
      if (on) { var p = v.play(); if (p && p.catch) p.catch(function () {}); } else v.pause();
    }
    b.addEventListener('click', function () {
      if (!v.getAttribute('src')) v.src = v.getAttribute('data-src');
      want = !want;
      fig.classList.toggle('is-playing', want);
      b.setAttribute('aria-label', (want ? 'Pausar o vídeo: ' : 'Reproduzir o vídeo: ') + name());
      apply();
    });
    document.addEventListener('visibilitychange', apply);
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (en) { fig._vis = en[0].isIntersecting; apply(); }, { threshold: 0.1 }).observe(fig);
    }
  });

  /* ---------- Hero video: wide screens, no reduced motion, no data saver; pauses when off screen ---------- */
  var video = $('.hero-video'), vctl = $('.vctl');
  var wide = window.matchMedia('(min-width: 960px)');
  var conn = navigator.connection || {};
  var saver = conn.saveData === true || /(^|-)2g$/.test(conn.effectiveType || '');
  var userPaused = false, visible = true, loaded = false;

  function sync() {
    if (!loaded) return;
    var want = visible && !userPaused && !document.hidden && !reduce.matches && wide.matches;
    if (want) { var p = video.play(); if (p && p.catch) p.catch(function () {}); }
    else video.pause();
  }
  function startVideo() {
    if (loaded || reduce.matches || saver || !wide.matches) return;
    loaded = true;
    video.src = video.getAttribute('data-src');
    video.addEventListener('playing', function () { video.classList.add('on'); vctl.hidden = false; }, { once: true });
    video.addEventListener('error', function () { vctl.hidden = true; video.classList.remove('on'); });
    sync();
  }
  vctl.addEventListener('click', function () {
    userPaused = !userPaused;
    vctl.textContent = userPaused ? 'Reproduzir o vídeo' : 'Pausar o vídeo';
    sync();
  });
  document.addEventListener('visibilitychange', sync);
  reduce.addEventListener('change', function () { if (reduce.matches) { video.pause(); vctl.hidden = true; video.classList.remove('on'); } });
  wide.addEventListener('change', function () { startVideo(); sync(); });
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (en) { visible = en[0].isIntersecting; sync(); }, { threshold: 0.05 }).observe($('.hero'));
  }
  // start after the page is interactive so the poster and text paint first
  if (document.readyState === 'complete') setTimeout(startVideo, 300);
  else window.addEventListener('load', function () { setTimeout(startVideo, 300); });
})();
