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
  function privacy() {
    var d = add('Usamos o que você escrever aqui só para responder e, se você confirmar, para a equipe da Devboot retornar o contato. Detalhes na ');
    var a = document.createElement('a'); a.href = '/privacidade/'; a.textContent = 'política de privacidade'; d.appendChild(a); d.appendChild(document.createTextNode('.'));
    log.scrollTop = log.scrollHeight;
  }
  function norm(t) { return (t || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, ''); }
  var ANS = [
    [/invest|aporte|rodada/, 'investidor'],
    [/piloto|testar|quero usar|participar|cadastr/, 'piloto'],
    [/preco|quanto custa|valor|mensalidade|plano|prazo/, 'Preços, prazos e condições são tratados pela equipe da Devboot. Quer que eu encaminhe o seu contato?'],
    [/dados|lgpd|privac|seguranc|seguro/, 'Quem pode o quê é decidido pelas regras do sistema, não pela IA. Os dados de cada empresa ficam isolados, ações sensíveis pedem a sua confirmação e tudo fica registrado.'],
    [/whats|zap|celular|audio/, 'No WhatsApp você manda um texto ou áudio, como "gastei 280 no mercado", e o One registra, responde com o resumo e avisa quando algo sai do previsto. Sem instalar nada.'],
    [/modelo|chatgpt|claude|gemini|llm|qual ia/, 'O One não depende de um único modelo de IA. Testamos vários num benchmark próprio e usamos o de melhor custo e qualidade para cada tarefa.'],
    [/devboot|quem s|sobre voces/, 'A Devboot desenvolve sistemas, automação e soluções de segurança eletrônica. O Devboot One é o nosso sistema de gestão que se adapta à empresa, gera telas sob demanda e executa tarefas com a sua confirmação.'],
    [/o que e|como funciona|o que faz|para que serve/, HOW],
    [/conta|financ|caixa|estoque|venda|pedido|cliente|fornecedor|planilha|tempo|demora|bagunca|controle|fechamento|rotina/, 'Isso é exatamente o tipo de coisa que o One resolve. Quer que eu cadastre a sua empresa como piloto? É só dizer "quero ser piloto".']
  ];
  var DEFAULT = 'Posso falar sobre o Devboot One, sobre a Devboot ou sobre como IA pode ajudar a sua empresa. Se quiser, me conte o que mais toma tempo na sua operação.';
  function answer(t) {
    var n = norm(t);
    for (var i = 0; i < ANS.length; i++) if (ANS[i][0].test(n)) return ANS[i][1];
    return DEFAULT;
  }
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
    privacy();
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
    else { var r = answer(t); if (r === 'piloto' || r === 'investidor') ask(r); else say(r); }
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

  /* ---------- Illustrative sections (values from the design canvas; rendered as text, never as HTML) ---------- */
  function el(tag, cls, txt) { var e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }
  function swap(p) { p.classList.toggle('swap', false); void p.offsetWidth; p.classList.toggle('swap', true); }
  function segs(name, items, render) {
    var bar = $('[data-segs="' + name + '"]'), panel = $('[data-panel="' + name + '"]');
    function pick(i, animate) {
      $$('button', bar).forEach(function (b, j) { b.setAttribute('aria-pressed', j === i ? 'true' : 'false'); });
      panel.textContent = ''; render(panel, items[i]); if (animate) swap(panel);
    }
    items.forEach(function (it, i) { var b = el('button', '', it.label); b.type = 'button'; b.addEventListener('click', function () { pick(i, true); }); bar.appendChild(b); });
    pick(0, false);
  }
  function mets(p, list) { var w = el('div', 'mets'); list.forEach(function (m) { var d = el('div', 'met'); d.appendChild(el('small', '', m[0])); d.appendChild(el('b', '', m[1])); w.appendChild(d); }); p.appendChild(w); }

  var DAYS = [
    { label: 'Dia 5', title: 'Contas a pagar', insight: '3 contas vencem nos próximos 5 dias. Seu saldo cobre todas.', action: 'Preparar pagamentos',
      metrics: [['Saldo disponível', 'R$ 12.480'], ['Vence em 5 dias', 'R$ 4.830'], ['Contas pendentes', '3']],
      rows: [['Aluguel', 'Hoje', 'R$ 2.700'], ['Fornecedor', 'Amanhã', 'R$ 1.850'], ['Internet e serviços', 'Dia 10', 'R$ 280']] },
    { label: 'Dia 15', title: 'Orçamento do mês', insight: 'No ritmo atual, o orçamento estoura antes do dia 30.', action: 'Ajustar orçamento',
      metrics: [['Despesas até hoje', 'R$ 8.340'], ['Orçamento usado', '76%'], ['Categoria crítica', 'Serviços']],
      rows: [['Alimentação', '', '85%', 85], ['Transporte', '', '60%', 60], ['Serviços', '', '92%', 92], ['Outros', '', '35%', 35]] },
    { label: 'Dia 30', title: 'Fechamento de novembro', insight: 'Resultado melhor que outubro. 3 lançamentos precisam de conferência.', action: 'Revisar pendências',
      metrics: [['Receitas', 'R$ 18.500'], ['Despesas', 'R$ 14.230'], ['Resultado', '+R$ 4.270']],
      rows: [['Transferência sem categoria', 'Classificar', 'R$ 350'], ['Despesa sem comprovante', 'Anexar', 'R$ 189'], ['Possível lançamento duplicado', 'Conferir', 'R$ 92']] }
  ];
  segs('days', DAYS, function (p, d) {
    var top = el('div', 'p-top'); top.appendChild(el('h3', '', d.title)); top.appendChild(el('p', 'p-insight', d.insight)); p.appendChild(top);
    mets(p, d.metrics);
    var rows = el('div', 'rows');
    d.rows.forEach(function (r) {
      var w = el('div', 'rw'); w.appendChild(el('span', 'a', r[0])); if (r[1]) w.appendChild(el('span', 'b', r[1]));
      if (r[3] != null) { var bar = el('span', 'meter'), i = el('i'); i.style.setProperty('--p', r[3] / 100); i.style.setProperty('--c', r[3] >= 90 ? 'var(--bad)' : r[3] >= 80 ? 'var(--warn)' : 'var(--acc)'); bar.appendChild(i); w.appendChild(bar); }
      w.appendChild(el('span', 'c' + (r[3] != null ? ' pc' : ''), r[2])); rows.appendChild(w);
    });
    p.appendChild(rows); p.appendChild(el('span', 'pill', d.action));
  });

  var GEN = [
    { label: 'Gastos da empresa no cartão pessoal', ask: 'Crie uma tela com as despesas da empresa pagas nos meus cartões pessoais.', title: 'Empresa no cartão pessoal',
      filters: ['Cartões pessoais', 'Centro de custo: empresa', 'Novembro'], metrics: [['Total no mês', 'R$ 3.140'], ['Lançamentos', '17'], ['Maior categoria', 'Combustível']],
      bars: [['Comb.', 150], ['Mat.', 95], ['Softw.', 70], ['Alim.', 55], ['Frete', 40], ['Outros', 25]] },
    { label: 'Parcelamentos dos próximos 12 meses', ask: 'Quero acompanhar as compras parceladas nos cartões pelos próximos 12 meses.', title: 'Parcelamentos',
      filters: ['Todos os cartões', 'Dez/26 a Nov/27'], metrics: [['Comprometido', 'R$ 18.450'], ['Parcelamentos ativos', '8'], ['Cai pela metade em', 'Maio']],
      bars: [['Dez', 160], ['Jan', 160], ['Fev', 140], ['Mar', 120], ['Abr', 90], ['Mai', 72], ['Jun', 55], ['Jul', 45], ['Ago', 30], ['Set', 20], ['Out', 15], ['Nov', 15]] },
    { label: 'Fluxo de caixa dos próximos 30 dias', ask: 'Mostre meu fluxo de caixa dos próximos 30 dias, semana a semana.', title: 'Fluxo de caixa · 30 dias',
      filters: ['Conta principal', 'Entradas e saídas previstas'], metrics: [['Saldo hoje', 'R$ 2.760'], ['Saídas previstas', 'R$ 5.000'], ['Projeção', '−R$ 1.240']],
      bars: [['Sem 1', 130], ['Sem 2', 90], ['Sem 3', 45], ['Sem 4', 18]] }
  ];
  segs('gen', GEN, function (p, g) {
    var a = el('div', 'askline');
    a.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/></svg>';
    a.appendChild(el('span', '', g.ask)); p.appendChild(a);
    var top = el('div', 'p-top'); top.style.marginTop = '18px'; top.appendChild(el('h3', '', g.title)); p.appendChild(top);
    var t = el('div', 'tags'); g.filters.forEach(function (f) { t.appendChild(el('span', '', f)); }); p.appendChild(t);
    mets(p, g.metrics);
    var ch = el('div', 'chart'); g.bars.forEach(function (b) { var c = el('div'), i = el('i'); i.style.height = b[1] + 'px'; c.appendChild(i); c.appendChild(el('span', '', b[0])); ch.appendChild(c); }); p.appendChild(ch);
    var pl = el('div', 'pills'); pl.appendChild(el('span', 'pill', 'Salvar no painel')); pl.lastChild.style.marginTop = '0'; pl.appendChild(el('span', 'pill pill-o', 'Exportar PDF')); p.appendChild(pl);
  });

  var SEG = [
    { label: 'Serviços', kind: 'Empresa de serviços', ask: 'Quem ainda não pagou este mês, e quanto sobra depois dos fornecedores?', metrics: [['A receber', 'R$ 18.400'], ['A pagar', 'R$ 12.250'], ['Previsto', 'R$ 6.150']], actions: ['Preparar cobranças', 'Projetar caixa', 'Gerar relatório'] },
    { label: 'Gráfica e fardamentos', kind: 'Produção sob encomenda', ask: 'Orçamento de 200 camisas personalizadas. Quando conseguimos entregar?', metrics: [['Custo estimado', 'R$ 4.200'], ['Preço sugerido', 'R$ 6.400'], ['Prazo', '7 dias']], actions: ['Gerar proposta em PDF', 'Simular margem', 'Criar pedido'] },
    { label: 'Farmácia', kind: 'Comércio com estoque', ask: 'O que preciso comprar esta semana e quais lotes estão perto do vencimento?', metrics: [['Repor', '12 produtos'], ['Perto do vencimento', '8 lotes'], ['Compra estimada', 'R$ 4.820']], actions: ['Preparar pedido de compra', 'Revisar lotes', 'Comparar fornecedores'] }
  ];
  segs('seg', SEG, function (p, g) {
    var k = el('p', 'p-kind', g.kind); k.style.cssText = 'font-size:.8125rem;color:var(--t2)'; p.appendChild(k);
    p.appendChild(el('p', 'askbub', g.ask)); mets(p, g.metrics);
    var pl = el('div', 'pills'); g.actions.forEach(function (a) { pl.appendChild(el('span', 'pill pill-o', a)); }); p.appendChild(pl);
  });

  /* Agent: confirm or restart; the five steps follow the state */
  var STEPS = ['Entende o pedido', 'Prepara a operação', 'Valida as regras', 'Você confirma', 'Executa e registra'];
  var stepsEl = $('[data-steps]'), agentDone = false;
  function paintSteps() {
    stepsEl.textContent = '';
    STEPS.forEach(function (n, i) {
      var fin = agentDone || i < 3, cur = !agentDone && i === 3;
      var li = el('li', fin ? 'ok' : cur ? 'cur' : ''); li.appendChild(el('span', 'd', String(i + 1))); li.appendChild(el('span', 'l', n));
      li.appendChild(el('span', 's', fin ? 'Feito' : cur ? 'Aguardando você' : 'Depois')); stepsEl.appendChild(li);
    });
    $('[data-agent=ask]').hidden = agentDone; $('[data-agent=done]').hidden = !agentDone;
  }
  $$('[data-agent-go]').forEach(function (b) {
    b.addEventListener('click', function () {
      agentDone = b.getAttribute('data-agent-go') === 'ok'; paintSteps();
      var t = $(agentDone ? '[data-agent=done] .btn' : '[data-agent=ask] .btn'); if (t) t.focus();
    });
  });
  paintSteps();
})();
