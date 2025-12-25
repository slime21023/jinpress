/**
 * JinPress Furo-Style Theme - Main JavaScript
 */

(function() {
    'use strict';

    // ===== Mobile Menu =====
    function initMobileMenu() {
        const toggle = document.getElementById('mobile-menu-toggle');
        const sidebar = document.getElementById('sidebar');
        
        if (!toggle || !sidebar) return;
        
        toggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
            toggle.setAttribute('aria-expanded', sidebar.classList.contains('open'));
        });
        
        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
                sidebar.classList.remove('open');
                toggle.setAttribute('aria-expanded', 'false');
            }
        });
        
        // Close on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && sidebar.classList.contains('open')) {
                sidebar.classList.remove('open');
                toggle.setAttribute('aria-expanded', 'false');
            }
        });
    }

    // ===== Sidebar Subgroups =====
    function initSidebarSubgroups() {
        const toggles = document.querySelectorAll('.sidebar-subgroup-toggle');
        
        toggles.forEach(toggle => {
            toggle.addEventListener('click', () => {
                const expanded = toggle.getAttribute('aria-expanded') === 'true';
                toggle.setAttribute('aria-expanded', !expanded);
                
                const sublist = toggle.nextElementSibling;
                if (sublist) {
                    sublist.style.display = expanded ? 'none' : 'block';
                }
            });
        });
    }


    // ===== Smooth Scrolling =====
    function initSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(link => {
            link.addEventListener('click', (e) => {
                const href = link.getAttribute('href');
                if (href === '#') return;
                
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    const headerHeight = document.querySelector('.header')?.offsetHeight || 60;
                    const targetPosition = target.offsetTop - headerHeight - 16;
                    
                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                    
                    // Update URL without scrolling
                    history.pushState(null, '', href);
                }
            });
        });
    }

    // ===== Code Copy Button =====
    function initCodeCopy() {
        document.querySelectorAll('.page-content pre').forEach(pre => {
            // Skip if already has button
            if (pre.querySelector('.copy-code-btn')) return;
            
            const code = pre.querySelector('code');
            if (!code) return;
            
            const button = document.createElement('button');
            button.className = 'copy-code-btn';
            button.textContent = 'Copy';
            button.setAttribute('aria-label', 'Copy code to clipboard');
            
            button.addEventListener('click', async () => {
                try {
                    await navigator.clipboard.writeText(code.textContent);
                    button.textContent = 'Copied!';
                    button.classList.add('copied');
                    
                    setTimeout(() => {
                        button.textContent = 'Copy';
                        button.classList.remove('copied');
                    }, 2000);
                } catch (err) {
                    console.error('Failed to copy:', err);
                    button.textContent = 'Failed';
                    setTimeout(() => {
                        button.textContent = 'Copy';
                    }, 2000);
                }
            });
            
            pre.appendChild(button);
        });
    }


    // ===== Heading Anchors =====
    function initHeadingAnchors() {
        const headings = document.querySelectorAll('.page-content h1, .page-content h2, .page-content h3, .page-content h4, .page-content h5, .page-content h6');
        
        headings.forEach(heading => {
            if (!heading.id) {
                heading.id = heading.textContent
                    .toLowerCase()
                    .replace(/[^\w\s-]/g, '')
                    .replace(/\s+/g, '-')
                    .trim();
            }
            
            // Skip if already has anchor
            if (heading.querySelector('.heading-anchor')) return;
            
            const anchor = document.createElement('a');
            anchor.href = '#' + heading.id;
            anchor.className = 'heading-anchor';
            anchor.innerHTML = '#';
            anchor.setAttribute('aria-label', 'Link to this section');
            
            heading.appendChild(anchor);
        });
    }

    // ===== TOC Active State =====
    function initTocActiveState() {
        const tocLinks = document.querySelectorAll('.toc-link');
        const headings = document.querySelectorAll('.page-content h1, .page-content h2, .page-content h3, .page-content h4');
        
        if (!tocLinks.length || !headings.length) return;
        
        const headerHeight = document.querySelector('.header')?.offsetHeight || 60;
        
        function updateActiveLink() {
            let activeId = '';
            
            headings.forEach(heading => {
                const rect = heading.getBoundingClientRect();
                if (rect.top <= headerHeight + 100) {
                    activeId = heading.id;
                }
            });
            
            tocLinks.forEach(link => {
                const href = link.getAttribute('href');
                if (href === '#' + activeId) {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            });
        }
        
        window.addEventListener('scroll', updateActiveLink, { passive: true });
        updateActiveLink();
    }

    // ===== Highlight Current Page in Sidebar =====
    function highlightCurrentPage() {
        const currentPath = window.location.pathname;
        const sidebarLinks = document.querySelectorAll('.sidebar-link');
        
        sidebarLinks.forEach(link => {
            const linkPath = new URL(link.href).pathname;
            if (linkPath === currentPath || linkPath === currentPath + '/') {
                link.classList.add('active');
            }
        });
    }


    // ===== Dropdown Menus =====
    function initDropdowns() {
        const dropdowns = document.querySelectorAll('.nav-dropdown');
        
        dropdowns.forEach(dropdown => {
            const toggle = dropdown.querySelector('.dropdown-toggle');
            const menu = dropdown.querySelector('.dropdown-menu');
            
            if (!toggle || !menu) return;
            
            // Keyboard navigation
            toggle.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    const expanded = toggle.getAttribute('aria-expanded') === 'true';
                    toggle.setAttribute('aria-expanded', !expanded);
                }
            });
        });
    }

    // ===== External Links =====
    function initExternalLinks() {
        document.querySelectorAll('.page-content a[href^="http"]').forEach(link => {
            if (!link.hostname.includes(window.location.hostname)) {
                link.setAttribute('target', '_blank');
                link.setAttribute('rel', 'noopener noreferrer');
            }
        });
    }

    // ===== Initialize =====
    function init() {
        initMobileMenu();
        initSidebarSubgroups();
        initSmoothScrolling();
        initCodeCopy();
        initHeadingAnchors();
        initTocActiveState();
        highlightCurrentPage();
        initDropdowns();
        initExternalLinks();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
