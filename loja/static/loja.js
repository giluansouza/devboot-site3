/* Loja Devboot: enhancements only. Every page works without this file; it adds the theme
   button, the phone menu, the photo counter, the sticky buy bar and the 404 WhatsApp text. */
(function () {
  'use strict';
  var root = document.documentElement;
  var KEY = 'devboot-tema';

  /* ---- theme: the choice was applied before first paint by the inline script in <head> */
  var themeBtn = document.getElementById('themeBtn');
  function labelTheme() {
    if (!themeBtn) return;
    var dark = root.getAttribute('data-tema') === 'escuro';
    var l = dark ? 'Mudar para o tema claro' : 'Mudar para o tema escuro';
    themeBtn.setAttribute('aria-label', l);
    themeBtn.setAttribute('title', l);
  }
  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      var dark = root.getAttribute('data-tema') !== 'escuro';
      if (dark) root.setAttribute('data-tema', 'escuro'); else root.removeAttribute('data-tema');
      try { localStorage.setItem(KEY, dark ? 'escuro' : 'claro'); } catch (e) {}
      labelTheme();
    });
    labelTheme();
  }

  /* ---- phone menu */
  var nav = document.getElementById('nav');
  var burger = document.getElementById('burger');
  function closeMenu() {
    if (!nav || !burger) return;
    nav.removeAttribute('data-menu');
    burger.setAttribute('aria-expanded', 'false');
    burger.textContent = 'Menu';
  }
  if (nav && burger) {
    burger.addEventListener('click', function () {
      if (nav.getAttribute('data-menu') === 'aberto') { closeMenu(); return; }
      nav.setAttribute('data-menu', 'aberto');
      burger.setAttribute('aria-expanded', 'true');
      burger.textContent = 'Fechar';
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.getAttribute('data-menu') === 'aberto') { closeMenu(); burger.focus(); }
    });
  }

  /* ---- photo counter and thumbnails */
  var gal = document.getElementById('gal');
  if (gal) {
    var count = document.getElementById('count');
    var thumbs = document.querySelectorAll('[data-shot]');
    var n = gal.children.length;
    gal.addEventListener('scroll', function () {
      var i = Math.max(0, Math.min(n - 1, Math.round(gal.scrollLeft / gal.clientWidth)));
      if (count) count.textContent = (i + 1) + ' / ' + n;
      thumbs.forEach(function (t, k) { t.setAttribute('aria-current', String(k === i)); });
    }, { passive: true });
    thumbs.forEach(function (t) {
      t.addEventListener('click', function () {
        gal.scrollTo({ left: gal.clientWidth * Number(t.getAttribute('data-shot')) });
      });
    });
  }

  /* ---- sticky buy bar: appears once the main buttons have scrolled out above the screen
     (phone only; CSS hides it from 720 px). A scroll listener, not IntersectionObserver: the
     observer only fires when the buttons cross the screen, so a jump past them (a #fragment, a
     restored scroll position) would leave the bar hidden. */
  var sticky = document.getElementById('sticky');
  var target = document.getElementById('ctaMain');
  if (sticky && target) {
    var pendente = false;
    var atualizar = function () {
      pendente = false;
      var show = target.getBoundingClientRect().bottom <= 0;
      sticky.hidden = !show;
      document.body.classList.toggle('has-sticky', show);
    };
    window.addEventListener('scroll', function () {
      if (!pendente) { pendente = true; requestAnimationFrame(atualizar); }
    }, { passive: true });
    atualizar();
  }

  /* ---- 404: put the address that failed into the WhatsApp message */
  var wa404 = document.getElementById('wa404');
  if (wa404) {
    var base = wa404.getAttribute('data-wa-base');
    wa404.href = base + encodeURIComponent('Olá, tentei abrir ' + location.pathname + ' no site da Devboot e não encontrei.');
  }
})();
