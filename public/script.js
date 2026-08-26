document.addEventListener('DOMContentLoaded', () => {
    const mainNav = document.getElementById('main-nav');
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    const closeMobileMenuButton = document.getElementById('close-mobile-menu');

    const desktopNavLinks = Array.from(document.querySelectorAll('#main-nav .nav-link[href^="#"]'));
    const mobileMenuLinks = Array.from(document.querySelectorAll('#mobile-menu a'));
    const footerLinks = Array.from(document.querySelectorAll('.footer-page-link[href^="#"]'));

    const sectionMap = desktopNavLinks
        .map((link) => {
            const target = document.querySelector(link.getAttribute('href'));
            if (!target) return null;
            return { id: target.id, link, section: target };
        })
        .filter(Boolean);

    const isMenuOpen = () => mobileMenu.classList.contains('flex');

    const getMenuIconElement = () => {
        if (!mobileMenuButton) return null;
        return mobileMenuButton.querySelector('svg, [data-lucide]');
    };

    const setMenuIcon = (iconName) => {
        if (!mobileMenuButton) return;
        mobileMenuButton.innerHTML = `<i data-lucide="${iconName}"></i>`;
        lucide.createIcons();
    };

    const updateHeaderState = () => {
        const scrolled = window.scrollY > 50;
        mainNav.classList.toggle('scrolled', scrolled);

        const mobileMenuIcon = getMenuIconElement();
        if (!mobileMenuIcon) return;
        if (isMenuOpen()) {
            mobileMenuIcon.style.color = 'var(--white)';
            return;
        }
        mobileMenuIcon.style.color = scrolled ? 'var(--slate-900)' : 'var(--white)';
    };

    const updateDesktopActiveLink = () => {
        if (!sectionMap.length) return;

        let activeId = sectionMap[0].id;
        const currentY = window.scrollY + 140;

        sectionMap.forEach(({ id, section }) => {
            if (section.offsetTop <= currentY) {
                activeId = id;
            }
        });

        sectionMap.forEach(({ id, link }) => {
            link.classList.toggle('active', id === activeId);
        });
    };

    const closeMenu = () => {
        if (!isMenuOpen()) return;
        mobileMenu.classList.remove('flex');
        mobileMenu.classList.add('hidden');
        document.body.classList.remove('menu-open');
        setMenuIcon('menu');
        updateHeaderState();
    };

    const openMenu = () => {
        mobileMenu.classList.remove('hidden');
        mobileMenu.classList.add('flex');
        document.body.classList.add('menu-open');
        setMenuIcon('x');
        updateHeaderState();
    };

    mobileMenuButton?.addEventListener('click', () => {
        if (isMenuOpen()) {
            closeMenu();
            return;
        }
        openMenu();
    });

    closeMobileMenuButton?.addEventListener('click', closeMenu);

    mobileMenuLinks.forEach((link) => {
        link.addEventListener('click', () => {
            closeMenu();
        });
    });

    footerLinks.forEach((link) => {
        link.addEventListener('click', () => {
            closeMenu();
        });
    });

    /* Reveal on scroll. O estado inicial escondido vem do CSS sob .reveal-enabled,
       classe que o inline script do <head> adiciona antes do primeiro paint.
       A checagem é por getBoundingClientRect dentro do handler de scroll (que já é
       throttled por rAF): IntersectionObserver é throttled em abas em background e
       deixaria a página em branco nesses casos. */
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let pendingReveals = Array.from(document.querySelectorAll('.reveal'));

    const revealInView = () => {
        if (!pendingReveals.length) return;

        if (prefersReducedMotion) {
            pendingReveals.forEach((item) => item.classList.add('is-visible'));
            pendingReveals = [];
            return;
        }

        // Linha de disparo um pouco acima da borda inferior da viewport.
        const trigger = window.innerHeight * 0.88;
        pendingReveals = pendingReveals.filter((item) => {
            if (item.getBoundingClientRect().top >= trigger) return true;
            item.classList.add('is-visible');
            return false;
        });
    };

    // Avisa o fallback do <head> que o reveal assumiu o controle.
    document.documentElement.dataset.revealReady = '1';

    const scrollProgress = document.getElementById('scroll-progress');

    const updateScrollProgress = () => {
        if (!scrollProgress) return;
        const scrollable = document.documentElement.scrollHeight - window.innerHeight;
        const ratio = scrollable > 0 ? window.scrollY / scrollable : 0;
        scrollProgress.style.transform = `scaleX(${Math.min(Math.max(ratio, 0), 1)})`;
    };

    let ticking = false;
    const onScroll = () => {
        if (ticking) return;
        ticking = true;
        window.requestAnimationFrame(() => {
            updateHeaderState();
            updateDesktopActiveLink();
            updateScrollProgress();
            revealInView();
            ticking = false;
        });
    };

    window.addEventListener('scroll', onScroll, { passive: true });

    window.addEventListener('resize', () => {
        updateScrollProgress();
        revealInView();
        if (window.innerWidth >= 1024) {
            closeMenu();
        }
    });

    /* Em aba de fundo o requestAnimationFrame fica pausado, então o scroll que
       acontece antes de a aba ficar visível não é processado. Reavalia ao voltar. */
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) return;
        updateHeaderState();
        updateDesktopActiveLink();
        updateScrollProgress();
        revealInView();
    });

    updateHeaderState();
    updateDesktopActiveLink();
    updateScrollProgress();
    revealInView();
});
