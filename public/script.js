document.addEventListener('DOMContentLoaded', () => {
    const mainNav = document.getElementById('main-nav');
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    const closeMobileMenuButton = document.getElementById('close-mobile-menu');
    const headerNavLinks = mainNav.querySelectorAll('button.nav-link[data-page]');
    const pageLinks = document.querySelectorAll('button[data-page]');
    const pageContents = document.querySelectorAll('.page-content');
    const logoLink = document.getElementById('logo');

    let activePageId = 'home'; // Default active page

    // Function to navigate between pages
    const navigate = (pageId) => {
        // Hide all page contents
        pageContents.forEach(page => page.classList.add('hidden'));

        // Show the selected page content
        const targetPage = document.getElementById(`${pageId}-page`);
        if (targetPage) {
            targetPage.classList.remove('hidden');
            // Scroll to top when navigating
            window.scrollTo(0, 0);
        }

        // Update active page state
        activePageId = pageId;

        // Update navigation link styles
        updateNavLinks();

        // Close mobile menu if open
        if (mobileMenu.classList.contains('flex')) {
            mobileMenu.classList.remove('flex');
            mobileMenu.classList.add('hidden');
            // Change menu icon to hamburger
            mobileMenuButton.querySelector('i').setAttribute('data-lucide', 'menu');
            lucide.createIcons();
        }
    };

    // Function to update navigation link active state and header style
    const updateNavLinks = () => {
        const scrolled = window.scrollY > 50 || activePageId !== 'home';
        if (scrolled) {
            mainNav.classList.add('scrolled');
            // Change mobile menu icon color to slate-900
            if (!mobileMenu.classList.contains('flex')) {
                mobileMenuButton.querySelector('i').style.color = 'var(--slate-900)';
            }
        } else {
            mainNav.classList.remove('scrolled');
            // Change mobile menu icon color to white
            if (!mobileMenu.classList.contains('flex')) {
                mobileMenuButton.querySelector('i').style.color = 'var(--white)';
            }
        }

        // Update desktop nav links
        headerNavLinks.forEach(link => {
            if (link.dataset.page === activePageId) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    };

    // Event listeners for page navigation
    pageLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = e.currentTarget.dataset.page;
            navigate(page);
        });
    });

    // Event Listener for logo to navigate to home
    logoLink.addEventListener('click', (e) => {
        e.preventDefault();
        navigate('home');
    });

    // Mobile menu toggle
    mobileMenuButton.addEventListener('click', () => {
        const isMobileMenuOpen = mobileMenu.classList.contains('flex');
        if (isMobileMenuOpen) {
            mobileMenu.classList.remove('flex');
            mobileMenu.classList.add('hidden');
            mobileMenuButton.querySelector('i').setAttribute('data-lucide', 'menu');
            updateNavLinks(); // Update icon color based on scroll/active page
        } else {
            mobileMenu.classList.remove('hidden');
            mobileMenu.classList.add('flex');
            mobileMenuButton.querySelector('i').setAttribute('data-lucide', 'x');
            mobileMenuButton.querySelector('i').style.color = 'var(--white)'; // Force white for open menu
        }
        lucide.createIcons();
    });

    closeMobileMenuButton.addEventListener('click', () => {
        mobileMenu.classList.remove('flex');
        mobileMenu.classList.add('hidden');
        mobileMenuButton.querySelector('i').setAttribute('data-lucide', 'menu');
        updateNavLinks(); // Update icon color based on scroll/active page
        lucide.createIcons();
    });

    // Scroll event for sticky header
    window.addEventListener('scroll', updateNavLinks);

    // Initial page load and setup
    navigate('home');
    updateNavLinks(); // Set initial nav state
});
