import React, { useState, useEffect } from 'react';
import {
  Code2,
  Smartphone,
  Truck,
  Building2,
  ChevronRight,
  Layers,
  Cpu,
  Database,
  Globe,
  MessageSquare,
  ShieldCheck,
  ScanEye,
  FileCheck,
  MapPin,
  Menu,
  X,
  ArrowUpRight,
  ExternalLink,
  Mail,
  Phone,
  Video, // Adicionado para Vídeo-rastreamento
  Monitor,
  Search,
  PenTool,
  Lock,
  Cloud
} from 'lucide-react';

const App = () => {
  const [activePage, setActivePage] = useState('home');
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navigate = (page) => {
    setActivePage(page);
    setMobileMenu(false);
    window.scrollTo(0, 0);
  };

  // --- COMPONENTES DE PÁGINAS ---

  const DevbootHome = () => (
    <div className="animate-in fade-in duration-700">
      {/* Hero Devboot */}
      <section className="relative pt-40 pb-24 px-6 overflow-hidden bg-slate-950">
        <div className="absolute top-0 right-0 w-1/2 h-full bg-blue-600/10 blur-[120px] rounded-full"></div>
        <div className="max-w-7xl mx-auto relative z-10">
          <div className="max-w-3xl space-y-8">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-blue-500/30 bg-blue-500/10 text-blue-400 text-xs font-bold tracking-widest uppercase">
              <Cpu size={14} /> Engenharia de Software de Alta Performance
            </div>
            <h1 className="text-5xl md:text-7xl font-black text-white leading-tight">
              Sua Software House <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">Especialista em Escala.</span>
            </h1>
            <p className="text-slate-400 text-lg md:text-xl max-w-2xl leading-relaxed">
              Transformamos desafios complexos em produtos digitais memoráveis com PHP/Laravel e React Native.
            </p>
            <div className="flex flex-wrap gap-4 pt-4">
              <button onClick={() => navigate('custom')} className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold flex items-center gap-2 transition-all group">
                Iniciar Projeto <ArrowUpRight className="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
              </button>
              <a href="#nossos-produtos" className="px-8 py-4 bg-slate-900 border border-slate-800 text-slate-300 hover:text-white rounded-xl font-bold transition-all">
                Ver Nossas Soluções
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="py-24 bg-white px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16 space-y-4">
            <h2 className="text-blue-600 font-bold uppercase tracking-widest text-sm italic">O Que Fazemos</h2>
            <h3 className="text-3xl md:text-5xl font-black text-slate-900">Desenvolvimento Customizado</h3>
          </div>

          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <h4 className="text-2xl font-bold text-slate-900 italic">Arquitetura Sob Medida</h4>
              <p className="text-slate-600 text-lg">
                Não usamos soluções genéricas. Analisamos seu fluxo de negócio para criar tecnologias que realmente impulsionam o seu faturamento.
              </p>

              <div className="space-y-4">
                <div className="p-6 rounded-2xl border border-slate-100 bg-slate-50 flex gap-6 items-center hover:border-blue-200 transition-colors group">
                  <div className="bg-white p-3 rounded-xl shadow-sm group-hover:bg-blue-600 group-hover:text-white transition-all"><Code2 /></div>
                  <div>
                    <h5 className="font-bold text-slate-900">Web com PHP/Laravel</h5>
                    <p className="text-sm text-slate-500">Backends robustos, APIs de alta velocidade e sistemas administrativos complexos.</p>
                  </div>
                </div>
                <div className="p-6 rounded-2xl border border-slate-100 bg-slate-50 flex gap-6 items-center hover:border-blue-200 transition-colors group">
                  <div className="bg-white p-3 rounded-xl shadow-sm group-hover:bg-blue-600 group-hover:text-white transition-all"><Smartphone /></div>
                  <div>
                    <h5 className="font-bold text-slate-900">Mobile com React Native</h5>
                    <p className="text-sm text-slate-500">Apps para iOS e Android com performance nativa e tempo recorde de lançamento.</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="relative">
                <div className="absolute -inset-4 bg-blue-100/50 blur-3xl rounded-full"></div>
                <div className="relative bg-slate-950 p-10 rounded-[3rem] text-white shadow-2xl border border-white/5">
                    <h4 className="text-2xl font-bold mb-6 flex items-center gap-2">
                        <Cpu className="text-blue-400" /> Software Factory Premium
                    </h4>
                    <p className="text-slate-400 mb-8 leading-relaxed">
                        Nossa "Fábrica de Software" opera sob padrões internacionais de qualidade, garantindo código limpo, testado e documentado.
                    </p>
                    <ul className="space-y-4">
                        {[
                            "Squads dedicados de engenharia",
                            "Consultoria técnica estratégica",
                            "Processos Ágeis (Scrum/Kanban)",
                            "Suporte e manutenção evolutiva"
                        ].map((item, i) => (
                            <li key={i} className="flex items-center gap-3 text-sm font-medium">
                                <div className="w-5 h-5 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400">✓</div>
                                {item}
                            </li>
                        ))}
                    </ul>
                    <div className="mt-10 p-6 bg-white/5 rounded-2xl border border-white/10">
                        <p className="text-xs text-blue-400 font-bold uppercase mb-2">Diferencial Devboot</p>
                        <p className="text-sm">Focamos em escalabilidade desde a primeira linha de código.</p>
                    </div>
                </div>
            </div>
          </div>
        </div>
      </section>

      {/* Proprietary Products Section */}
      <section id="nossos-produtos" className="py-24 bg-slate-50 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16 space-y-4">
            <h2 className="text-blue-600 font-bold uppercase tracking-widest text-sm italic">Soluções Proprietárias</h2>
            <h3 className="text-3xl md:text-5xl font-black text-slate-900">Produtos Prontos para Implementar</h3>
            <p className="text-slate-500 max-w-2xl mx-auto">Sistemas consolidados e testados, prontos para modernizar sua gestão hoje mesmo.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="group bg-white p-8 md:p-12 rounded-[2.5rem] shadow-sm border border-slate-100 hover:shadow-2xl hover:border-blue-200 transition-all">
                <div className="flex justify-between items-start mb-12">
                    <div className="bg-blue-600 p-4 rounded-2xl text-white shadow-lg shadow-blue-200"><Building2 size={32} /></div>
                    <span className="text-[10px] font-bold bg-blue-50 text-blue-600 px-3 py-1 rounded-full uppercase tracking-tighter">Public Tech</span>
                </div>
                <h4 className="text-3xl font-black text-slate-900 mb-4">GestorPM</h4>
                <p className="text-slate-600 mb-8 leading-relaxed">
                    Software completo para prefeituras. Gestão escolar com biometria facial, assinatura digital ICP-Brasil e portal da transparência.
                </p>
                <div className="flex gap-2 flex-wrap mb-8">
                    <span className="text-xs font-bold text-slate-400 border border-slate-200 px-3 py-1 rounded-lg">Educação</span>
                    <span className="text-xs font-bold text-slate-400 border border-slate-200 px-3 py-1 rounded-lg">Reconhecimento Facial</span>
                    <span className="text-xs font-bold text-slate-400 border border-slate-200 px-3 py-1 rounded-lg">Arquivos Nuvem</span>
                </div>
                <button onClick={() => navigate('gestorpm')} className="flex items-center gap-2 font-bold text-blue-600 group-hover:translate-x-2 transition-transform">
                    Conhecer GestorPM <ChevronRight />
                </button>
            </div>

            <div className="group bg-slate-900 p-8 md:p-12 rounded-[2.5rem] shadow-sm border border-slate-800 hover:shadow-2xl transition-all text-white">
                <div className="flex justify-between items-start mb-12">
                    <div className="bg-emerald-500 p-4 rounded-2xl text-white shadow-lg shadow-emerald-900/40"><Truck size={32} /></div>
                    <span className="text-[10px] font-bold bg-emerald-500/10 text-emerald-400 px-3 py-1 rounded-full uppercase tracking-tighter">Logistics Tech</span>
                </div>
                <h4 className="text-3xl font-black mb-4">FrotasPro</h4>
                <p className="text-slate-400 mb-8 leading-relaxed">
                    Sistema de gestão de frotas completo com vídeo-rastreamento em tempo real, telemetria avançada e controle de consumo.
                </p>
                <div className="flex gap-2 flex-wrap mb-8">
                    <span className="text-xs font-bold text-slate-500 border border-slate-700 px-3 py-1 rounded-lg">Vídeo-Rastreamento</span>
                    <span className="text-xs font-bold text-slate-500 border border-slate-700 px-3 py-1 rounded-lg">Telemetria</span>
                    <span className="text-xs font-bold text-slate-500 border border-slate-700 px-3 py-1 rounded-lg">BI de Custos</span>
                </div>
                <button onClick={() => navigate('frotaspro')} className="flex items-center gap-2 font-bold text-emerald-400 group-hover:translate-x-2 transition-transform">
                    Conhecer FrotasPro <ChevronRight />
                </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );

  const GestorPMPage = () => (
    <div className="animate-in slide-in-from-right duration-500">
      <section className="pt-32 pb-20 bg-gradient-to-b from-blue-50 to-white px-6">
        <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <span className="bg-blue-600 text-white px-4 py-1 rounded-full text-xs font-bold uppercase tracking-widest">Produto GestorPM</span>
            <h1 className="text-4xl md:text-5xl font-black text-slate-900 leading-tight">Gestão Pública Inteligente e Integrada</h1>
            <p className="text-slate-600 text-lg leading-relaxed">
              O GestorPM é a solução definitiva para municípios modernos que buscam digitalização total, segurança e transparência em um único ecossistema.
            </p>
            <div className="space-y-4">
              <div className="flex items-center gap-3 text-slate-700 p-4 bg-white rounded-2xl border border-slate-100">
                <ScanEye className="text-blue-600" size={24} />
                <span className="font-bold">Acesso Escolar com Reconhecimento Facial</span>
              </div>
              <div className="flex items-center gap-3 text-slate-700 p-4 bg-white rounded-2xl border border-slate-100">
                <FileCheck className="text-blue-600" size={24} />
                <span className="font-bold">Assinatura Digital & Gestão sem Papel</span>
              </div>
            </div>
            <button className="bg-blue-600 text-white px-8 py-4 rounded-xl font-bold shadow-lg shadow-blue-200">Agendar Demonstração Técnica</button>
          </div>
          <div className="bg-slate-200 rounded-3xl h-[400px] overflow-hidden shadow-2xl relative">
            <img src="https://images.unsplash.com/photo-1541829070764-84a7d30dee93?auto=format&fit=crop&q=80&w=1000" className="w-full h-full object-cover opacity-80" alt="Gestão Pública" />
            <div className="absolute inset-0 bg-blue-900/30 flex items-center justify-center p-8">
                <div className="bg-white/95 p-8 rounded-3xl backdrop-blur-md shadow-2xl border border-white">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center text-white"><ShieldCheck /></div>
                        <h5 className="font-black text-slate-900">Dashboard Prefeito</h5>
                    </div>
                    <p className="text-sm text-slate-500">Dados em tempo real de todas as secretarias.</p>
                </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );

  const FrotasProPage = () => (
    <div className="animate-in slide-in-from-right duration-500">
      <section className="pt-32 pb-20 bg-slate-950 text-white px-6">
        <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <span className="bg-emerald-500 text-white px-4 py-1 rounded-full text-xs font-bold uppercase tracking-widest">Produto FrotasPro</span>
            <h1 className="text-4xl md:text-5xl font-black leading-tight italic">Gestão de Frotas, Vídeo & Telemetria</h1>
            <p className="text-slate-400 text-lg leading-relaxed">
              Muito além do GPS. O FrotasPro é uma plataforma completa para monitoramento visual, comportamento do motorista e controle de custos operacionais.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-5 border border-slate-800 rounded-2xl bg-slate-900/50 hover:border-emerald-500/50 transition-colors">
                <Video className="text-emerald-400 mb-3" size={24} />
                <h4 className="font-bold text-white uppercase text-sm">Vídeo-Rastreamento</h4>
                <p className="text-xs text-slate-500 mt-2">Câmeras embarcadas com streaming em tempo real.</p>
              </div>
              <div className="p-5 border border-slate-800 rounded-2xl bg-slate-900/50 hover:border-emerald-500/50 transition-colors">
                <Cpu className="text-emerald-400 mb-3" size={24} />
                <h4 className="font-bold text-white uppercase text-sm">Telemetria Avançada</h4>
                <p className="text-xs text-slate-500 mt-2">Dados de RPM, velocidade e freadas bruscas.</p>
              </div>
              <div className="p-5 border border-slate-800 rounded-2xl bg-slate-900/50 hover:border-emerald-500/50 transition-colors">
                <Database className="text-emerald-400 mb-3" size={24} />
                <h4 className="font-bold text-white uppercase text-sm">Gestão de Custos</h4>
                <p className="text-xs text-slate-500 mt-2">Controle de combustível, pneus e manutenção.</p>
              </div>
              <div className="p-5 border border-slate-800 rounded-2xl bg-slate-900/50 hover:border-emerald-500/50 transition-colors">
                <ShieldCheck className="text-emerald-400 mb-3" size={24} />
                <h4 className="font-bold text-white uppercase text-sm">IA Antifadiga</h4>
                <p className="text-xs text-slate-500 mt-2">Alertas inteligentes de segurança para o condutor.</p>
              </div>
            </div>
            <button className="bg-emerald-500 text-white px-10 py-5 rounded-2xl font-black uppercase tracking-widest text-sm shadow-xl shadow-emerald-900/20 hover:scale-105 transition-transform">Solicitar Orçamento</button>
          </div>
          <div className="relative">
             <div className="absolute -inset-10 bg-emerald-500/10 blur-[100px] rounded-full"></div>
             <div className="relative bg-slate-900 p-3 rounded-[3rem] border border-slate-800 overflow-hidden shadow-2xl">
                <div className="absolute top-8 left-8 z-10 bg-red-600 px-3 py-1 rounded-full text-[10px] font-black animate-pulse flex items-center gap-1">
                    <div className="w-2 h-2 bg-white rounded-full"></div> LIVE: VEÍCULO 04
                </div>
                <img src="https://images.unsplash.com/photo-1519003722824-194d4455a60c?auto=format&fit=crop&q=80&w=1000" className="rounded-[2.5rem] grayscale hover:grayscale-0 transition-all duration-700" alt="Frotas" />
             </div>
          </div>
        </div>
      </section>
    </div>
  );

  const CustomDevPage = () => (
    <div className="animate-in slide-in-from-bottom duration-500">
        <section className="pt-32 pb-24 px-6 bg-slate-50">
            <div className="max-w-4xl mx-auto text-center space-y-8">
                <h2 className="text-4xl md:text-5xl font-black text-slate-900">Software Factory Premium</h2>
                <p className="text-slate-600 text-xl">Transformamos sua visão de negócio em sistemas digitais escaláveis com tecnologias de ponta.</p>

                <div className="grid md:grid-cols-2 gap-8 text-left">
                    <div className="bg-white p-8 rounded-3xl shadow-sm border border-slate-100 hover:border-blue-500 transition-colors">
                        <div className="bg-blue-50 w-14 h-14 rounded-2xl flex items-center justify-center mb-6"><Code2 className="text-blue-600" size={28} /></div>
                        <h3 className="text-2xl font-bold mb-3 text-slate-900">PHP & Laravel</h3>
                        <p className="text-slate-500 text-sm leading-relaxed">Nossa stack preferida para sistemas que exigem alta segurança, integridade de dados e complexidade de regras de negócio.</p>
                    </div>
                    <div className="bg-white p-8 rounded-3xl shadow-sm border border-slate-100 hover:border-indigo-500 transition-colors">
                        <div className="bg-indigo-50 w-14 h-14 rounded-2xl flex items-center justify-center mb-6"><Smartphone className="text-indigo-600" size={28} /></div>
                        <h3 className="text-2xl font-bold mb-3 text-slate-900">React Native</h3>
                        <p className="text-slate-500 text-sm leading-relaxed">Desenvolvemos aplicativos fluidos para Android e iOS, aproveitando o melhor de cada plataforma com performance otimizada.</p>
                    </div>
                </div>

                <div className="bg-slate-950 p-12 rounded-[3.5rem] mt-16 text-white text-left relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-blue-600/10 blur-3xl"></div>
                    <div className="relative z-10 grid md:grid-cols-2 gap-12 items-center">
                        <div>
                            <h4 className="text-3xl font-black mb-4 italic">Metodologia Devboot</h4>
                            <p className="text-slate-400 mb-6 italic">Garantimos transparência total durante o ciclo de vida do desenvolvimento.</p>
                            <div className="space-y-4">
                                {["Planning Semanal", "Code Review Rigoroso", "Deploy Contínuo", "QA Especializado"].map((t, i) => (
                                    <div key={i} className="flex items-center gap-2 text-sm">
                                        <ChevronRight className="text-blue-400" size={16} /> {t}
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="space-y-6">
                            <p className="text-slate-300">Pronto para dar o próximo passo na digitalização da sua empresa?</p>
                            <button className="w-full bg-blue-600 hover:bg-blue-700 py-5 rounded-2xl font-black uppercase tracking-widest flex items-center justify-center gap-2 transition-all">
                                Falar com Especialista <ArrowUpRight />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </div>
  )

  // --- RENDERIZADOR ---

  return (
    <div className="min-h-screen font-sans">
      {/* Header Fixo */}
      <nav className={`fixed w-full z-[100] transition-all duration-300 px-6 py-4 ${scrolled || activePage !== 'home' ? 'bg-white/95 backdrop-blur-md shadow-sm py-3' : 'bg-transparent'}`}>
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div
            onClick={() => navigate('home')}
            className="flex items-center gap-2 cursor-pointer group"
          >
            <div className="bg-blue-600 p-1.5 rounded-lg group-hover:rotate-12 transition-transform">
              <Code2 className="text-white w-5 h-5" />
            </div>
            <span className={`text-xl font-black tracking-tight ${scrolled || activePage !== 'home' ? 'text-slate-900' : 'text-white'}`}>
              DEVBOOT<span className="text-blue-500">.</span>
            </span>
          </div>

          <div className="hidden lg:flex items-center gap-10">
            {[
              { id: 'home', label: 'Home' },
              { id: 'custom', label: 'Software House' },
              { id: 'gestorpm', label: 'GestorPM' },
              { id: 'frotaspro', label: 'FrotasPro' }
            ].map(item => (
              <button
                key={item.id}
                onClick={() => navigate(item.id)}
                className={`text-sm font-bold uppercase tracking-widest transition-colors ${
                  activePage === item.id
                    ? 'text-blue-500'
                    : (scrolled || activePage !== 'home' ? 'text-slate-600 hover:text-blue-500' : 'text-white/70 hover:text-white')
                }`}
              >
                {item.label}
              </button>
            ))}
            <button className="bg-blue-600 text-white px-6 py-2.5 rounded-full font-bold text-xs uppercase tracking-widest hover:bg-blue-700 transition-all shadow-lg shadow-blue-200">
              Contato
            </button>
          </div>

          <button className="lg:hidden" onClick={() => setMobileMenu(!mobileMenu)}>
             {mobileMenu ? <X className={activePage === 'home' && !scrolled ? 'text-white' : 'text-slate-900'} /> : <Menu className={activePage === 'home' && !scrolled ? 'text-white' : 'text-slate-900'} />}
          </button>
        </div>
      </nav>

      {/* Mobile Menu Overlay */}
      {mobileMenu && (
        <div className="fixed inset-0 z-[90] bg-slate-950 p-12 flex flex-col items-center justify-center gap-8 animate-in fade-in zoom-in duration-300">
            {['home', 'custom', 'gestorpm', 'frotaspro'].map(p => (
                <button key={p} onClick={() => navigate(p)} className="text-3xl font-black text-white uppercase tracking-tighter italic hover:text-blue-500 transition-colors">
                    {p === 'home' ? 'Início' : p === 'custom' ? 'Software House' : p}
                </button>
            ))}
            <button onClick={() => setMobileMenu(false)} className="mt-8 text-slate-500 font-bold uppercase text-xs tracking-widest underline">Fechar Menu</button>
        </div>
      )}

      {/* Conteúdo Dinâmico */}
      <main>
        {activePage === 'home' && <DevbootHome />}
        {activePage === 'gestorpm' && <GestorPMPage />}
        {activePage === 'frotaspro' && <FrotasProPage />}
        {activePage === 'custom' && <CustomDevPage />}
      </main>

      {/* Footer Unificado */}
      <footer className="bg-slate-950 text-slate-400 py-20 px-6 border-t border-slate-900">
        <div className="max-w-7xl mx-auto grid md:grid-cols-4 gap-12 text-center md:text-left">
          <div className="col-span-2 space-y-6">
             <div className="flex items-center gap-2 text-white justify-center md:justify-start">
                <Code2 className="text-blue-500" />
                <span className="text-2xl font-black">DEVBOOT</span>
             </div>
             <p className="max-w-sm text-lg text-slate-500 mx-auto md:mx-0">
               Engenharia de software premium e produtos SaaS de alto impacto para prefeituras e logística.
             </p>
             <div className="flex gap-4 justify-center md:justify-start">
                <div className="bg-slate-900 p-2.5 rounded-lg hover:text-blue-400 transition-colors cursor-pointer"><Globe size={20} /></div>
                <div className="bg-slate-900 p-2.5 rounded-lg hover:text-blue-400 transition-colors cursor-pointer"><MessageSquare size={20} /></div>
             </div>
          </div>
          <div>
            <h4 className="text-white font-bold mb-6 italic uppercase tracking-widest text-sm">Soluções</h4>
            <ul className="space-y-4 text-sm">
              <li className="hover:text-white cursor-pointer transition-colors" onClick={() => navigate('gestorpm')}>GestorPM</li>
              <li className="hover:text-white cursor-pointer transition-colors" onClick={() => navigate('frotaspro')}>FrotasPro</li>
              <li className="hover:text-white cursor-pointer transition-colors" onClick={() => navigate('custom')}>Software Factory</li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-bold mb-6 italic uppercase tracking-widest text-sm">Conecte-se</h4>
            <ul className="space-y-4 text-sm">
              <li className="flex items-center gap-3 justify-center md:justify-start">
                <Mail size={16} className="text-blue-500" />
                comercial@devboot.com.br
              </li>
              <li className="flex items-center gap-3 justify-center md:justify-start">
                <Phone size={16} className="text-blue-500" />
                +55 (11) 9999-9999
              </li>
              <li className="flex items-center gap-3 justify-center md:justify-start">
                <MapPin size={16} className="text-blue-500" />
                São Paulo, SP
              </li>
            </ul>
          </div>
        </div>
        <div className="max-w-7xl mx-auto mt-20 pt-8 border-t border-slate-900 flex flex-col md:row justify-between items-center text-[10px] uppercase tracking-widest font-bold text-center">
           <p>© 2024 DEVBOOT TECNOLOGIA - DIGITAL SOLUTIONS</p>
           <div className="flex gap-8 mt-4 md:mt-0">
              <a href="#" className="hover:text-white transition-colors">Privacidade</a>
              <a href="#" className="hover:text-white transition-colors">Termos</a>
           </div>
        </div>
      </footer>
    </div>
  );
};

export default App;