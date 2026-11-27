/**
 * Configurable Hero Render Video controller for Luckjary.
 * Supports:
 *  - "scrub": Apple-style frame-accurate scroll scrubbing painted onto a cover-fitted <canvas>
 *  - "autoplay": Smooth looping background playback that auto-pauses when scrolled out of view
 * Configured dynamically via data-* attributes set from Theme Customize in the dashboard.
 */
(function () {
    'use strict';

    const track = document.getElementById('heroScrollTrack');
    const stage = document.getElementById('heroStickyStage');
    const video = document.getElementById('heroRenderVideo');
    const canvas = document.getElementById('heroRenderCanvas');
    const fallbackImg = document.getElementById('heroFallbackImg');
    const contentEl = document.getElementById('heroOverlayContent');
    const scrollCueEl = document.getElementById('heroScrollCue');
    const progressEl = document.getElementById('heroScrollProgress');

    if (!track || !stage || !video || !canvas) return;

    const enabled = track.dataset.enabled !== 'false';
    if (!enabled) return;

    const mode = track.dataset.mode === 'autoplay' ? 'autoplay' : 'scrub';
    const smoothing = Math.min(0.5, Math.max(0.04, parseFloat(track.dataset.smoothing) || 0.16));
    const fadeOverlay = track.dataset.fadeOverlay !== 'false';
    const fadeStart = Math.min(0.95, Math.max(0.2, (parseFloat(track.dataset.fadeStart) || 70) / 100));

    const ctx = canvas.getContext('2d', { alpha: false });
    if (!ctx) return;

    const prefersReducedMotion =
        window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    let videoDuration = 0;
    let videoReady = false;
    let hasPaintedFirstFrame = false;
    let targetProgress = 0;
    let currentProgress = 0;
    let pendingTime = null;
    let rafId = null;
    let autoplayRafId = null;
    let iosPrimed = false;

    function clamp(val, min, max) {
        return Math.min(max, Math.max(min, val));
    }

    function resizeCanvas() {
        const rect = stage.getBoundingClientRect();
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        const targetW = Math.max(1, Math.round(rect.width * dpr));
        const targetH = Math.max(1, Math.round(rect.height * dpr));
        if (canvas.width !== targetW || canvas.height !== targetH) {
            canvas.width = targetW;
            canvas.height = targetH;
        }
        if (videoReady) {
            drawFrame();
        }
    }

    function drawFrame() {
        if (!video.videoWidth || !video.videoHeight || !canvas.width || !canvas.height) return;

        const cw = canvas.width;
        const ch = canvas.height;
        const vw = video.videoWidth;
        const vh = video.videoHeight;

        const scale = Math.max(cw / vw, ch / vh);
        const dw = vw * scale;
        const dh = vh * scale;
        const dx = (cw - dw) * 0.5;
        const dy = (ch - dh) * 0.5;

        ctx.drawImage(video, dx, dy, dw, dh);

        if (!hasPaintedFirstFrame) {
            hasPaintedFirstFrame = true;
            canvas.classList.add('is-ready');
            if (fallbackImg) {
                fallbackImg.style.opacity = '0';
            }
        }
    }

    function computeScrollProgress() {
        const rect = track.getBoundingClientRect();
        const scrollableDistance = track.offsetHeight - stage.offsetHeight;
        if (scrollableDistance > 20) {
            return clamp(-rect.top / scrollableDistance, 0, 1);
        }
        // Unpinned normal scroll mode: scrub smoothly as the hero scrolls out of view
        const normalTravel = Math.max(1, rect.height * 0.85);
        return clamp(-rect.top / normalTravel, 0, 1);
    }

    function releaseStickyPinOnFallback() {
        track.style.height = 'auto';
        track.style.minHeight = '82vh';
        stage.classList.remove('hero-sticky-stage');
        stage.classList.add('relative', 'min-h-[82vh]', 'w-full', 'overflow-hidden', 'bg-[#0F0F0F]');
        if (scrollCueEl) scrollCueEl.style.display = 'none';
        if (progressEl && progressEl.parentElement) progressEl.parentElement.style.display = 'none';
    }

    function updateOverlayChoreography(progress) {
        if (progressEl) {
            progressEl.style.transform = `scaleX(${progress.toFixed(4)})`;
        }

        if (scrollCueEl) {
            const cueOpacity = clamp(1 - progress / 0.08, 0, 1);
            scrollCueEl.style.opacity = cueOpacity.toFixed(3);
            scrollCueEl.style.transform = `translateY(${(progress * 40).toFixed(1)}px)`;
        }

        if (contentEl && !prefersReducedMotion && mode === 'scrub' && fadeOverlay) {
            const span = Math.max(0.05, 0.95 - fadeStart);
            const fadeOut = clamp((progress - fadeStart) / span, 0, 1);
            const opacity = 1 - fadeOut;
            const translateY = -fadeOut * 28;
            contentEl.style.opacity = opacity.toFixed(3);
            contentEl.style.transform = `translate3d(0, ${translateY.toFixed(1)}px, 0)`;
            contentEl.style.pointerEvents = opacity < 0.15 ? 'none' : 'auto';
        }
    }

    function requestVideoSeek(timeSec) {
        if (!videoReady || !videoDuration) return;
        const clampedTime = clamp(timeSec, 0, Math.max(0, videoDuration - 0.04));

        if (video.seeking) {
            pendingTime = clampedTime;
            return;
        }

        if (Math.abs(video.currentTime - clampedTime) > 0.012) {
            pendingTime = null;
            video.currentTime = clampedTime;
        }
    }

    function tick() {
        rafId = null;
        targetProgress = computeScrollProgress();

        const diff = targetProgress - currentProgress;
        if (Math.abs(diff) < 0.0005) {
            currentProgress = targetProgress;
        } else {
            currentProgress += diff * smoothing;
        }

        updateOverlayChoreography(currentProgress);

        if (mode === 'scrub' && videoReady && !prefersReducedMotion && videoDuration > 0) {
            requestVideoSeek(currentProgress * videoDuration);
        }

        if (Math.abs(targetProgress - currentProgress) >= 0.0005) {
            rafId = window.requestAnimationFrame(tick);
        }
    }

    function scheduleTick() {
        if (rafId === null) {
            rafId = window.requestAnimationFrame(tick);
        }
    }

    function startAutoplayPaintLoop() {
        if (autoplayRafId !== null) return;
        function paintLoop() {
            if (video.paused || video.ended) {
                autoplayRafId = null;
                return;
            }
            drawFrame();
            autoplayRafId = window.requestAnimationFrame(paintLoop);
        }
        autoplayRafId = window.requestAnimationFrame(paintLoop);
    }

    function setupAutoplayMode() {
        video.loop = true;
        if (prefersReducedMotion) return;

        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver(
                function (entries) {
                    entries.forEach(function (entry) {
                        if (entry.isIntersecting) {
                            const p = video.play();
                            if (p && typeof p.then === 'function') {
                                p.then(startAutoplayPaintLoop).catch(function () {});
                            } else {
                                startAutoplayPaintLoop();
                            }
                        } else {
                            video.pause();
                        }
                    });
                },
                { threshold: 0.15 }
            );
            observer.observe(stage);
        } else {
            const p = video.play();
            if (p && typeof p.then === 'function') {
                p.then(startAutoplayPaintLoop).catch(function () {});
            }
        }
    }

    function primeVideoForMobile() {
        if (iosPrimed || mode !== 'scrub') return;
        iosPrimed = true;
        if (video.readyState >= 2) return;
        const playPromise = video.play();
        if (playPromise && typeof playPromise.then === 'function') {
            playPromise
                .then(function () {
                    video.pause();
                    scheduleTick();
                })
                .catch(function () {});
        }
    }

    video.addEventListener('loadedmetadata', function () {
        if (Number.isFinite(video.duration) && video.duration > 0) {
            videoDuration = video.duration;
        }
        resizeCanvas();
    });

    video.addEventListener('loadeddata', function () {
        videoReady = true;
        if (Number.isFinite(video.duration) && video.duration > 0) {
            videoDuration = video.duration;
        }
        resizeCanvas();
        drawFrame();
        if (mode === 'autoplay') {
            setupAutoplayMode();
        } else {
            video.pause();
            scheduleTick();
        }
    });

    video.addEventListener('seeked', function () {
        drawFrame();
        if (mode === 'scrub' && pendingTime !== null) {
            const next = pendingTime;
            pendingTime = null;
            if (Math.abs(video.currentTime - next) > 0.012) {
                video.currentTime = next;
            }
        }
    });

    function handleVideoUnavailable() {
        canvas.classList.remove('is-ready');
        if (fallbackImg) {
            fallbackImg.style.opacity = '';
        }
        releaseStickyPinOnFallback();
    }

    video.addEventListener('error', handleVideoUnavailable);

    // Note: When <video> uses <source> children, HTTP 404 fires 'error' on the <source> tags (not <video>)
    const sources = video.querySelectorAll('source');
    if (sources.length === 0) {
        handleVideoUnavailable();
    } else {
        let failedSources = 0;
        sources.forEach(function (srcEl) {
            srcEl.addEventListener('error', function () {
                failedSources += 1;
                if (failedSources >= sources.length || video.networkState === 3) {
                    handleVideoUnavailable();
                }
            });
        });
    }

    window.addEventListener('scroll', scheduleTick, { passive: true });
    window.addEventListener(
        'resize',
        function () {
            resizeCanvas();
            scheduleTick();
        },
        { passive: true }
    );

    window.addEventListener('touchstart', primeVideoForMobile, { passive: true, once: true });
    window.addEventListener('pointerdown', primeVideoForMobile, { passive: true, once: true });

    resizeCanvas();
    updateOverlayChoreography(computeScrollProgress());
    video.load();
})();
