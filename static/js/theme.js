// Gestion du thème clair/sombre — transitions élégantes
(function () {
    'use strict';

    var html = document.documentElement;
    var themeToggle = document.getElementById('theme-toggle');
    var metaTheme = document.querySelector('meta[name="theme-color"]');
    var THEME_COLORS = { dark: '#2D2E32', light: '#c5ccd6' };

    function getInitialTheme() {
        try {
            var saved = localStorage.getItem('theme');
            if (saved === 'light' || saved === 'dark') return saved;
        } catch (e) {}
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
            return 'light';
        }
        return 'dark';
    }

    function updateChrome(theme) {
        if (metaTheme) metaTheme.setAttribute('content', THEME_COLORS[theme] || THEME_COLORS.dark);
        if (themeToggle) {
            themeToggle.setAttribute('aria-pressed', theme === 'light' ? 'true' : 'false');
            themeToggle.dataset.theme = theme;
        }
    }

    function applyTheme(theme) {
        html.setAttribute('data-theme', theme);
        try {
            localStorage.setItem('theme', theme);
        } catch (e) {}
        updateChrome(theme);
    }

    function setTheme(theme, withTransition) {
        if (theme !== 'light' && theme !== 'dark') theme = 'dark';
        if (html.getAttribute('data-theme') === theme) {
            updateChrome(theme);
            return;
        }

        var run = function () {
            applyTheme(theme);
        };

        if (withTransition && typeof document.startViewTransition === 'function') {
            document.startViewTransition(run);
            return;
        }

        if (withTransition) {
            html.classList.add('theme-animating');
            run();
            window.setTimeout(function () {
                html.classList.remove('theme-animating');
            }, 480);
            return;
        }

        run();
    }

    // Sync si le script inline a déjà posé data-theme
    var initial = html.getAttribute('data-theme') || getInitialTheme();
    applyTheme(initial);

    if (window.matchMedia) {
        var mediaQuery = window.matchMedia('(prefers-color-scheme: light)');
        var onSystemChange = function (e) {
            try {
                if (localStorage.getItem('theme')) return;
            } catch (err) {}
            setTheme(e.matches ? 'light' : 'dark', true);
        };
        if (mediaQuery.addEventListener) {
            mediaQuery.addEventListener('change', onSystemChange);
        } else if (mediaQuery.addListener) {
            mediaQuery.addListener(onSystemChange);
        }
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', function () {
            var current = html.getAttribute('data-theme') || 'dark';
            setTheme(current === 'light' ? 'dark' : 'light', true);
        });
    }
})();
