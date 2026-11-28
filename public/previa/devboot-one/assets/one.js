/* Devboot One landing preview. No scroll handler: motion is CSS; this file only handles
   the theme switch, the reveal fallback, the WhatsApp toast and a scripted chat demo that sends nothing. */
(function () {
  'use strict';
  var root = document.documentElement;
  function $(s, c) { return (c || document).querySelector(s); }
  function $$(s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); }
  function store(k, v) { try { if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) {} }

  /* Provisional number (W1 pending). The page never prints it; the toast shows the composed link. */
  var WA = '5587991402037';
  var MSG = { one: 'Olá! Gostaria de saber mais sobre o Devboot One.' };

  /* ---------- Theme: auto -> claro -> escuro, site-wide key devboot-tema ---------- */
  var tbtn = $('.theme'), tlab = $('.theme-t', tbtn);
  var LABEL = { auto: 'Auto', claro: 'Claro', escuro: 'Escuro' };
  var NAME = { auto: 'automático', claro: 'claro', escuro: 'escuro' };
  function themeNow() { var t = root.getAttribute('data-theme'); return t === 'dark' ? 'escuro' : t === 'light' ? 'claro' : 'auto'; }
  function paintTheme() {
    var t = themeNow();
    tlab.textContent = LABEL[t];
    tbtn.setAttribute('aria-label', 'Tema: ' + NAME[t] + '. Alternar tema.');
  }
  tbtn.addEventListener('click', function () {
    var next = { auto: 'claro', claro: 'escuro', escuro: 'auto' }[themeNow()];
    if (next === 'auto') { root.removeAttribute('data-theme'); store('devboot-tema', null); }
    else { root.setAttribute('data-theme', next === 'escuro' ? 'dark' : 'light'); store('devboot-tema', next); }
    paintTheme();
  });
  paintTheme();

  /* ---------- Reveal fallback: IntersectionObserver class toggle, only where scroll timelines are missing ---------- */
  var nativeTimeline = window.CSS && CSS.supports && CSS.supports('animation-timeline: view()');
  var reveal = $$('.rv, .scene');
  if (!nativeTimeline) {
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (es) {
        es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });
      reveal.forEach(function (el) { io.observe(el); });
    } else {
      reveal.forEach(function (el) { el.classList.add('in'); });
    }
  }

  /* ---------- WhatsApp: show the composed link, never open it ---------- */
  var toast = $('.toast'), tlink = $('.toast-link'), thead = $('.toast-h'), tnote = $('.toast-n'), ttimer = 0, lastBtn = null;
  function showToast(btn, head, link, note) {
    lastBtn = btn;
    thead.textContent = head; tlink.textContent = link; tnote.textContent = note;
    tlink.hidden = !link;
    toast.hidden = false;
    clearTimeout(ttimer);
    ttimer = setTimeout(function () { toast.hidden = true; }, 9000);
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-wa]');
    if (b) {
      e.preventDefault();
      showToast(b, 'No site real, isto abre o WhatsApp com:', 'https://wa.me/' + WA + '?text=' + encodeURIComponent(MSG[b.getAttribute('data-wa')] || MSG.one), 'Número provisório (W1).');
      return;
    }
    var m = e.target.closest('[data-email]');
    if (m) { e.preventDefault(); showToast(m, 'No site real, isto abre o e-mail da Devboot.', '', 'Endereço pendente (D4).'); }
  });
  $('.toast-x').addEventListener('click', function () { toast.hidden = true; clearTimeout(ttimer); if (lastBtn) lastBtn.focus(); });

  /* ---------- Demo scene: the approve/cancel buttons end the demonstration ---------- */
  $$('[data-demo]').forEach(function (b) {
    b.addEventListener('click', function () {
      var box = b.closest('.confirm');
      $('.row', box).hidden = true;
      var done = $('.done', box); done.hidden = false;
    });
  });

  /* ---------- Scripted chat (demonstration of the flow; sends nothing, stores nothing) ---------- */
  var chat = $('#chat'), log = $('.log', chat), chips = $('.chips', chat), form = $('.ask'), input = $('#ask');
  var OPEN = 'Conte qual rotina você quer melhorar ou pergunte como funciona o Devboot One.';
  var HOW = 'Estamos criando um sistema de gestão em que você pode pedir o que precisa em linguagem natural, ver a resposta com os dados da operação e confirmar ações antes da execução.';
  var PH = { idle: input.placeholder, rotina: 'Descreva a rotina que quer melhorar', nome: 'Seu nome', contato: 'E-mail ou WhatsApp' };
  var st = { stage: 'idle', kind: null, lead: {} };
  var greeted = false;

  function add(text, cls) {
    var d = document.createElement('p'); d.className = 'msg ' + (cls || ''); d.textContent = text; log.appendChild(d); log.scrollTop = log.scrollHeight; return d;
  }
  function say(t) { return add(t); }
  function you(t) { return add(t, 'msg-u'); }
  function marker(t) { return add(t, 'msg-q'); }
  function setStage(s) { st.stage = s; input.placeholder = PH[s]; chips.hidden = s !== 'idle'; }
  function openChat(focus) {
    if (chat.hidden) { chat.hidden = false; }
    if (!greeted) { greeted = true; say(OPEN); }
    if (focus) input.focus();
  }
  $('.chat-min').addEventListener('click', function () { chat.hidden = true; input.focus(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !chat.hidden) { chat.hidden = true; input.focus(); } });
  input.addEventListener('focus', function () { openChat(false); });

  function ask(kind) {
    st.kind = kind; st.lead = {};
    if (kind === 'piloto') { say('Conte qual rotina você quer melhorar.'); setStage('rotina'); }
    else { say('A equipe da Devboot pode falar com você.'); privacyThenName(); }
  }
  function privacyThenName() {
    marker('[falta] Aviso de privacidade e link da política: texto ainda não definido.');
    say('Qual é o seu nome?'); setStage('nome');
  }
  function review() {
    setStage('review'); input.placeholder = PH.idle; chips.hidden = true;
    var L = st.lead, card = document.createElement('div'); card.className = 'card';
    card.innerHTML = '<h4>Resumo do contato</h4><dl></dl><div class="row"><button type="button" class="btn btn-p" data-r="ok">Confirmar envio</button><button type="button" class="btn btn-s" data-r="edit">Editar</button><button type="button" class="btn btn-s" data-r="cancel">Cancelar</button></div>';
    var rows = [['Assunto', st.kind === 'piloto' ? 'Piloto do Devboot One' : 'Investidor'], ['Produto', 'Devboot One'], ['Nome', L.nome], ['Contato', L.contato]];
    if (L.rotina) rows.push(['Descrição', L.rotina]);
    var dl = $('dl', card);
    rows.forEach(function (r) { var a = document.createElement('dt'), b = document.createElement('dd'); a.textContent = r[0]; b.textContent = r[1]; dl.appendChild(a); dl.appendChild(b); });
    log.appendChild(card); log.scrollTop = log.scrollHeight;
    $$('button', card).forEach(function (b) {
      b.addEventListener('click', function () {
        card.setAttribute('data-closed', '');
        var r = b.getAttribute('data-r');
        if (r === 'ok') { say('Fim da demonstração. Nenhum dado foi enviado.'); setStage('idle'); }
        else if (r === 'cancel') { say('Cancelado. Nenhum dado foi enviado.'); setStage('idle'); }
        else ask(st.kind);
        input.focus();
      });
    });
  }
  function start(kind, label) {
    openChat(false);
    if (label) you(label);
    ask(kind);
    input.focus();
  }
  function submit(text) {
    var t = text.trim(); if (!t) return;
    openChat(false); you(t); input.value = '';
    if (st.stage === 'rotina') { st.lead.rotina = t; privacyThenName(); }
    else if (st.stage === 'nome') { st.lead.nome = t; say('Qual e-mail ou WhatsApp podemos usar para o retorno?'); setStage('contato'); }
    else if (st.stage === 'contato') { st.lead.contato = t; review(); }
    else if (st.stage === 'review') { say('Use os botões do resumo: Confirmar envio, Editar ou Cancelar.'); }
    else { marker('[falta] Aqui entra a resposta do Devboot AI (tarefas I3 e I4).'); }
  }
  form.addEventListener('submit', function (e) { e.preventDefault(); submit(input.value); });
  chips.addEventListener('click', function (e) {
    var b = e.target.closest('[data-chip]'); if (!b) return;
    var c = b.getAttribute('data-chip');
    if (c === 'como') { you(b.textContent); say(HOW); input.focus(); }
    else start(c, b.textContent);
  });
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-chat]'); if (!b) return;
    start(b.getAttribute('data-chat'), null);
  });
})();
