/**
 * SmoothScrollProvider for LUCKJARY Storefront
 * Syncs official Lenis smooth scrolling directly with GSAP ScrollTrigger
 * using a single unified gsap.ticker animation loop (zero jitter).
 */
(function () {
    'use strict';

    if (typeof window === 'undefined') return;

    const prefersReducedMotion =
        window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (typeof window.gsap !== 'undefined' && typeof window.ScrollTrigger !== 'undefined') {
        window.gsap.registerPlugin(window.ScrollTrigger);
    }

    if (prefersReducedMotion || typeof window.Lenis === 'undefined' || typeof window.gsap === 'undefined') {
        return;
    }

    const lenis = new window.Lenis({
        lerp: 0.09,
        smoothWheel: true,
        syncTouch: false,
        anchors: true,
        respectReducedMotion: true,
    });

    window.luckjaryLenis = lenis;

    if (typeof window.ScrollTrigger !== 'undefined') {
        lenis.on('scroll', window.ScrollTrigger.update);
    }

    const tickerCallback = function (time) {
        lenis.raf(time * 1000);
    };

    window.gsap.ticker.add(tickerCallback);
    window.gsap.ticker.lagSmoothing(0);

    function destroySmoothScroll() {
        if (window.gsap && tickerCallback) {
            window.gsap.ticker.remove(tickerCallback);
        }
        if (lenis && typeof lenis.destroy === 'function') {
            lenis.destroy();
        }
        window.luckjaryLenis = null;
    }

    window.destroyLuckjarySmoothScroll = destroySmoothScroll;
    window.addEventListener('pagehide', destroySmoothScroll, { once: true });
})();
