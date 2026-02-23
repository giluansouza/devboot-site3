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
        setMenuIcon('menu');
        updateHeaderState();
    };

    const openMenu = () => {
        mobileMenu.classList.remove('hidden');
        mobileMenu.classList.add('flex');
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

    window.addEventListener('scroll', () => {
        updateHeaderState();
        updateDesktopActiveLink();
    });

    window.addEventListener('resize', () => {
        if (window.innerWidth >= 1024) {
            closeMenu();
        }
    });

    updateHeaderState();
    updateDesktopActiveLink();
});
