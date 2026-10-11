/**
 * Compteurs animés pour les statistiques clés (accueil).
 * Démarre l'animation quand le bloc entre dans le viewport.
 */
(function () {
  function animateCounter(el) {
    if (el.dataset.animated === '1') return;
    el.dataset.animated = '1';

    const target = Number(el.dataset.target || 0);
    const suffix = el.dataset.suffix || '';
    if (!Number.isFinite(target) || target <= 0) {
      el.textContent = String(el.dataset.target || 0) + suffix;
      return;
    }

    const duration = 1200;
    const start = performance.now();

    function tick(now) {
      const progress = Math.min((now - start) / duration, 1);
      // Ease-out cubic pour un effet compteur plus naturel
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = Math.round(target * eased);
      el.textContent = String(value) + suffix;
      if (progress < 1) {
        requestAnimationFrame(tick);
      } else {
        el.textContent = String(target) + suffix;
      }
    }

    requestAnimationFrame(tick);
  }

  function initCounters() {
    const nodes = document.querySelectorAll('[data-counter]');
    if (!nodes.length) return;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      nodes.forEach((el) => {
        el.textContent = String(el.dataset.target || 0) + (el.dataset.suffix || '');
        el.dataset.animated = '1';
      });
      return;
    }

    if (!('IntersectionObserver' in window)) {
      nodes.forEach(animateCounter);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            animateCounter(entry.target);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.4 }
    );

    nodes.forEach((el) => observer.observe(el));
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCounters);
  } else {
    initCounters();
  }
})();
