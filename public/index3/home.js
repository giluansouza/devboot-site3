/* Devboot home, prototype 3. No library and no scroll listener: scroll-linked motion is CSS
   (animation-timeline, on the compositor); this script only splits headings into words, toggles
   one-shot reveal classes through IntersectionObserver, and runs the menu, toast and settings. */
(function () {
  'use strict';
  var root = document.documentElement;
  var WA = '5587991402037';
  var MSG = {
    geral: 'Olá, Devboot! Vim pelo site e quero conversar.',
    sistema: 'Olá, Devboot! Quero conversar sobre um sistema.',
    automacao: 'Olá, Devboot! Quero conversar sobre automação.',
    cameras: 'Olá, Devboot! Quero um orçamento de câmeras.',
    acesso: 'Olá, Devboot! Quero conversar sobre controle de acesso.',
    orcamento: 'Olá, Devboot! Quero um orçamento de segurança eletrônica.'
  };

  function store(k, v) { try { if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) {} }
  function calm() { return root.getAttribute('data-motion') === 'menos'; }
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* ---------- Split headings into word masks (keeps inline children such as .q intact) ---------- */
  function split(el) {
    var i = 0;
    function walk(node) {
      var kids = Array.prototype.slice.call(node.childNodes);
      kids.forEach(function (k) {
        if (k.nodeType === 3) {
          var parts = k.textContent.split(/(\s+)/);
          var frag = document.createDocumentFragment();
          parts.forEach(function (p) {
            if (!p) return;
            if (/^\s+$/.test(p)) { frag.appendChild(document.createTextNode(' ')); return; }
            var w = document.createElement('span'); w.className = 'w';
            var inner = document.createElement('span'); inner.textContent = p;
            w.style.setProperty('--i', i++);
            w.appendChild(inner); frag.appendChild(w);
          });
          node.replaceChild(frag, k);
        } else if (k.nodeType === 1 && k.classList.contains('q')) {
          var w = document.createElement('span'); w.className = 'w';
          w.style.setProperty('--i', i++);
          node.replaceChild(w, k);
          var inner = document.createElement('span'); inner.appendChild(k); w.appendChild(inner);
        } else if (k.nodeType === 1) {
          walk(k);
        }
      });
    }
    walk(el);
    el.style.setProperty('--n', i);
  }
  $$('[data-split]').forEach(split);

  /* ---------- Reveal on enter ---------- */
  var revealTargets = $$('.rise, .mask, [data-split], .ch-head, .foot-mark');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.01 });
    revealTargets.forEach(function (el) {
      if (el.closest('.hero')) return; // the hero plays on load
      io.observe(el);
    });
  } else {
    revealTargets.forEach(function (el) { el.classList.add('in'); });
  }

  function start() {
    root.classList.add('ready');
    $$('.hero .rise').forEach(function (el) { el.classList.add('in'); });
  }
  if (document.fonts && document.fonts.ready) {
    var started = false;
    var go = function () { if (!started) { started = true; requestAnimationFrame(start); } };
    document.fonts.ready.then(go);
    setTimeout(go, 700); // never hold the opening hostage to a slow font
  } else { start(); }

  /* ---------- Menu ---------- */
  var menu = $('#menu'), mbtn = $('.menu-btn'), mlabel = $('.menu-btn-t');
  function openMenu() {
    menu.hidden = false;
    mbtn.setAttribute('aria-expanded', 'true'); mlabel.textContent = 'Fechar';
    document.body.classList.add('menu-open');
    requestAnimationFrame(function () { requestAnimationFrame(function () { menu.classList.add('open'); }); });
    var first = $('a', menu); if (first) first.focus({ preventScroll: true });
  }
  function closeMenu(back) {
    menu.classList.remove('open');
    mbtn.setAttribute('aria-expanded', 'false'); mlabel.textContent = 'Menu';
    document.body.classList.remove('menu-open');
    setTimeout(function () { if (!menu.classList.contains('open')) menu.hidden = true; }, calm() ? 0 : 700);
    if (back) mbtn.focus();
  }
  mbtn.addEventListener('click', function () { if (mbtn.getAttribute('aria-expanded') === 'true') closeMenu(true); else openMenu(); });
  menu.addEventListener('click', function (e) { if (e.target.closest('a')) closeMenu(false); });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    if (mbtn.getAttribute('aria-expanded') === 'true') closeMenu(true);
    if (dbtn.getAttribute('aria-expanded') === 'true') toggleDial(false, true);
  });
  // keep Tab inside the open menu (menu links + the close button)
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Tab' || mbtn.getAttribute('aria-expanded') !== 'true') return;
    var f = $$('a, button', menu).concat([mbtn]);
    var i = f.indexOf(document.activeElement);
    if (e.shiftKey && (i <= 0)) { e.preventDefault(); f[f.length - 1].focus(); }
    else if (!e.shiftKey && i === f.length - 1) { e.preventDefault(); f[0].focus(); }
  });

  /* ---------- WhatsApp: in the prototype, show the composed link instead of opening it ---------- */
  var toast = $('.toast'), tlink = $('.toast-link'), tclose = $('.toast-x'), ttimer = 0, lastBtn = null;
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-wa]');
    if (!b) return;
    e.preventDefault();
    if (b.closest('.menu')) closeMenu(false);
    lastBtn = b;
    var msg = MSG[b.getAttribute('data-wa')] || MSG.geral;
    tlink.textContent = 'https://wa.me/' + WA + '?text=' + encodeURIComponent(msg);
    toast.hidden = false;
    clearTimeout(ttimer);
    ttimer = setTimeout(function () { toast.hidden = true; }, 9000);
  });
  tclose.addEventListener('click', function () { toast.hidden = true; clearTimeout(ttimer); if (lastBtn) lastBtn.focus(); });

  /* ---------- Settings dial ---------- */
  var dbtn = $('.dial-btn'), dpanel = $('#dial-panel');
  function toggleDial(open, back) {
    dpanel.hidden = !open;
    dbtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (!open && back) dbtn.focus();
  }
  dbtn.addEventListener('click', function () { toggleDial(dpanel.hidden); });
  document.addEventListener('click', function (e) {
    if (!dpanel.hidden && !e.target.closest('.dial')) toggleDial(false);
  });

  function current(set) {
    if (set === 'v') return root.getAttribute('data-v') || 'a';
    if (set === 'tema') { var t = root.getAttribute('data-theme'); return t === 'dark' ? 'escuro' : t === 'light' ? 'claro' : 'auto'; }
    return calm() ? 'menos' : 'normal';
  }
  function paint() {
    $$('.seg').forEach(function (g) {
      var cur = current(g.getAttribute('data-set'));
      $$('button', g).forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-val') === cur ? 'true' : 'false'); });
    });
  }
  $$('.seg').forEach(function (g) {
    g.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b) return;
      var set = g.getAttribute('data-set'), val = b.getAttribute('data-val');
      if (set === 'v') {
        root.setAttribute('data-v', val); store('devboot-proto3-variante', val);
      } else if (set === 'tema') {
        if (val === 'auto') { root.removeAttribute('data-theme'); store('devboot-tema', null); }
        else { root.setAttribute('data-theme', val === 'escuro' ? 'dark' : 'light'); store('devboot-tema', val); }
      } else {
        if (val === 'menos') root.setAttribute('data-motion', 'menos'); else root.removeAttribute('data-motion');
        store('devboot-proto3-movimento', val);
        if (val === 'normal') { $$('.rise, .mask, [data-split], .ch-head, .foot-mark').forEach(function (el) { el.classList.add('in'); }); }
      }
      paint();
    });
  });
  paint();

  /* ---------- Desktop delights: cursor preview on lists, magnetic buttons ---------- */
  var fine = window.matchMedia && matchMedia('(hover: hover) and (pointer: fine)').matches;
  if (fine) {
    var peek = $('.peek'), pimg = $('img', peek), ptxt = $('span', peek);
    var px = -999, py = -999, tx = -999, ty = -999, pRaf = 0, active = null;
    function pLoop() {
      pRaf = 0;
      var k = calm() ? 1 : 0.16;
      px += (tx - px) * k; py += (ty - py) * k;
      peek.style.transform = 'translate3d(' + (px + 24).toFixed(1) + 'px,' + (py - 90).toFixed(1) + 'px,0)';
      if (active && (Math.abs(tx - px) > 0.5 || Math.abs(ty - py) > 0.5)) pRaf = requestAnimationFrame(pLoop);
    }
    $$('[data-peek], [data-peek-text]').forEach(function (el) {
      if (!el.closest('.fronts') && !el.classList.contains('work')) return;
      el.addEventListener('mouseenter', function (e) {
        active = el;
        var src = el.getAttribute('data-peek');
        if (src) { pimg.src = src; peek.classList.remove('text'); }
        else { ptxt.textContent = el.getAttribute('data-peek-text'); peek.classList.add('text'); }
        tx = e.clientX; ty = e.clientY;
        if (px < -900) { px = tx; py = ty; }
        peek.classList.add('on');
        if (!pRaf) pRaf = requestAnimationFrame(pLoop);
      });
      el.addEventListener('mousemove', function (e) { tx = e.clientX; ty = e.clientY; if (!pRaf) pRaf = requestAnimationFrame(pLoop); });
      el.addEventListener('mouseleave', function () { active = null; peek.classList.remove('on'); });
    });

    $$('.magnet').forEach(function (b) {
      b.addEventListener('mousemove', function (e) {
        if (calm()) return;
        var r = b.getBoundingClientRect();
        var dx = (e.clientX - (r.left + r.width / 2)) * 0.18, dy = (e.clientY - (r.top + r.height / 2)) * 0.3;
        b.style.transform = 'translate(' + dx.toFixed(1) + 'px,' + dy.toFixed(1) + 'px)';
      });
      b.addEventListener('mouseleave', function () { b.style.transform = ''; });
    });
  }
})();
