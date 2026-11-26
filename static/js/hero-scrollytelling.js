/**
 * LUCKJARY — Approach A: HTML5 Canvas Image Sequence Scrollytelling
 * Powered by GSAP ScrollTrigger + Lenis Smooth Scroll
 *
 * Drop rendered WebP frames into:
 *   /static/ring-frames/frame_0001.webp ... frame_0120.webp
 * Until frames are added, a crisp procedural 925 sterling silver ring
 * fallback renderer animates zoom, 3D rotation, and flight across the canvas.
 */
(function () {
    'use strict';

    const TOTAL_FRAMES = 120; // Easy-to-edit default frame count
    const FRAMES_BASE_PATH = '/static/ring-frames/';
    const PRELOAD_INITIAL_COUNT = 20;

    const container = document.getElementById('heroScrollytelling');
    const canvas = document.getElementById('scrollyRingCanvas');
    const heroCopy = document.getElementById('scrollyHeroCopy');
    const scrollCue = document.getElementById('scrollyScrollCue');
    const showcaseLabel = document.getElementById('scrollyShowcaseLabel');
    const cardsWrapper = document.getElementById('scrollyCardsWrapper');
    const cardsTrack = document.getElementById('scrollyCardsTrack');
    const progressBar = document.getElementById('scrollyProgressBar');

    if (!container || !canvas) return;

    const ctx = canvas.getContext('2d', { alpha: false });
    if (!ctx) return;

    const totalFrames = Math.max(
        10,
        parseInt(container.dataset.totalFrames || '', 10) || TOTAL_FRAMES
    );
    const desktopScrollDistance = Math.max(
        1200,
        parseInt(container.dataset.scrollDistance || '', 10) || 3500
    );

    const frameImages = new Array(totalFrames);
    const frameLoaded = new Array(totalFrames).fill(false);
    let useFallbackRenderer = false;
    let currentFrameIndex = 0;
    let currentProgress = 0;
    let canvasWidth = 0;
    let canvasHeight = 0;
    let dpr = 1;

    function getFrameUrl(index) {
        const padded = String(index + 1).padStart(4, '0');
        return `${FRAMES_BASE_PATH}frame_${padded}.webp`;
    }

    function resizeCanvas() {
        const rect = container.getBoundingClientRect();
        dpr = Math.min(window.devicePixelRatio || 1, 2);
        canvasWidth = Math.max(1, Math.round(rect.width));
        canvasHeight = Math.max(1, Math.round(rect.height));

        canvas.width = Math.round(canvasWidth * dpr);
        canvas.height = Math.round(canvasHeight * dpr);
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        renderCurrentFrame();
    }

    function drawImageCover(img) {
        const iw = img.naturalWidth || img.width;
        const ih = img.naturalHeight || img.height;
        if (!iw || !ih) return;

        ctx.fillStyle = '#121214';
        ctx.fillRect(0, 0, canvasWidth, canvasHeight);

        const scale = Math.max(canvasWidth / iw, canvasHeight / ih);
        const dw = iw * scale;
        const dh = ih * scale;
        const dx = (canvasWidth - dw) * 0.5;
        const dy = (canvasHeight - dh) * 0.5;
        ctx.drawImage(img, dx, dy, dw, dh);
    }

    /**
     * Procedural luxury 925 sterling silver solitaire ring fallback renderer.
     * Scales, rotates in 3D perspective, and flies cleanly as progress goes 0 -> 1.
     */
    function drawFallbackRing(progress) {
        const w = canvasWidth;
        const h = canvasHeight;
        const isMobile = w < 768;

        // Charcoal studio backdrop (#121214) with warm radial spotlight
        ctx.fillStyle = '#121214';
        ctx.fillRect(0, 0, w, h);

        // Flight path: starts right-of-center at 0% (beside hero text), glides center & zooms in
        const startX = isMobile ? w * 0.52 : w * 0.68;
        const endX = w * 0.5;
        const startY = isMobile ? h * 0.62 : h * 0.52;
        const endY = h * 0.46;

        const easeP = 1 - Math.pow(1 - Math.min(1, progress / 0.65), 2.2);
        const cx = startX + (endX - startX) * easeP;
        const cy = startY + (endY - startY) * easeP - Math.sin(progress * Math.PI) * (h * 0.04);

        const baseRadius = Math.min(w, h) * (isMobile ? 0.2 : 0.21);
        const zoomScale = 0.92 + progress * 0.85;
        const rotAngle = -0.35 + progress * Math.PI * 1.45;
        const tiltY = 0.58 + Math.sin(progress * Math.PI * 0.85) * 0.22;

        // Ambient studio glow behind ring
        const glow = ctx.createRadialGradient(cx, cy, 10, cx, cy, baseRadius * zoomScale * 2.4);
        glow.addColorStop(0, 'rgba(212, 175, 55, 0.16)');
        glow.addColorStop(0.45, 'rgba(229, 231, 235, 0.08)');
        glow.addColorStop(1, 'rgba(18, 18, 20, 0)');
        ctx.fillStyle = glow;
        ctx.fillRect(0, 0, w, h);

        ctx.save();
        ctx.translate(cx, cy);
        ctx.scale(zoomScale, zoomScale);
        ctx.rotate(rotAngle * 0.32);

        // Soft floor shadow
        ctx.save();
        ctx.translate(0, baseRadius * 0.92);
        ctx.scale(1.25, 0.24);
        const shadowGrad = ctx.createRadialGradient(0, 0, 5, 0, 0, baseRadius);
        shadowGrad.addColorStop(0, 'rgba(0, 0, 0, 0.65)');
        shadowGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = shadowGrad;
        ctx.beginPath();
        ctx.arc(0, 0, baseRadius, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();

        // Outer 925 sterling silver band (3D foreshortened ellipse)
        const rx = baseRadius;
        const ry = baseRadius * tiltY;
        const bandThickness = Math.max(12, baseRadius * 0.17);

        // Inner dark band depth
        ctx.beginPath();
        ctx.ellipse(0, bandThickness * 0.22, rx, ry, 0, 0, Math.PI * 2);
        ctx.lineWidth = bandThickness;
        ctx.strokeStyle = '#3f424a';
        ctx.stroke();

        // Main rhodium-plated 925 silver metallic sweep
        const silverGrad = ctx.createLinearGradient(-rx, -ry, rx, ry);
        silverGrad.addColorStop(0.0, '#7c808b');
        silverGrad.addColorStop(0.22, '#f4f6f9');
        silverGrad.addColorStop(0.42, '#a2a7b4');
        silverGrad.addColorStop(0.55, '#ffffff');
        silverGrad.addColorStop(0.75, '#737782');
        silverGrad.addColorStop(0.9, '#e5e7eb');
        silverGrad.addColorStop(1.0, '#52555e');

        ctx.beginPath();
        ctx.ellipse(0, 0, rx, ry, 0, 0, Math.PI * 2);
        ctx.lineWidth = bandThickness;
        ctx.strokeStyle = silverGrad;
        ctx.stroke();

        // Specular inner bevel highlight
        ctx.beginPath();
        ctx.ellipse(0, -bandThickness * 0.08, rx - bandThickness * 0.28, ry - bandThickness * 0.22, 0, 0.15, Math.PI - 0.15);
        ctx.lineWidth = 2.2;
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.55)';
        ctx.stroke();

        // Warm gold champagne reflection rim
        ctx.beginPath();
        ctx.ellipse(0, bandThickness * 0.15, rx + bandThickness * 0.36, ry + bandThickness * 0.26, 0, Math.PI * 0.12, Math.PI * 0.88);
        ctx.lineWidth = 1.4;
        ctx.strokeStyle = 'rgba(212, 175, 55, 0.45)';
        ctx.stroke();

        // Solitaire Crown & Faceted Diamond positioned along rotating rim
        const stoneAngle = -Math.PI * 0.5 + Math.sin(rotAngle) * 0.38;
        const sx = Math.cos(stoneAngle) * rx;
        const sy = Math.sin(stoneAngle) * ry - bandThickness * 0.45;
        const gemSize = baseRadius * 0.34;

        ctx.save();
        ctx.translate(sx, sy);

        // Cathedral prongs (925 silver)
        ctx.fillStyle = '#e5e7eb';
        [-0.75, 0.75].forEach(function (side) {
            ctx.beginPath();
            ctx.moveTo(side * gemSize * 0.6, gemSize * 0.45);
            ctx.lineTo(side * gemSize * 0.82, -gemSize * 0.15);
            ctx.lineTo(side * gemSize * 0.55, -gemSize * 0.28);
            ctx.closePath();
            ctx.fill();
        });

        // Diamond pavilion & crown
        const gemGrad = ctx.createLinearGradient(-gemSize, -gemSize, gemSize, gemSize);
        gemGrad.addColorStop(0, '#ffffff');
        gemGrad.addColorStop(0.35, '#dbeafe');
        gemGrad.addColorStop(0.6, '#f8fafc');
        gemGrad.addColorStop(0.85, '#fef3c7');
        gemGrad.addColorStop(1, '#cbd5e1');

        ctx.beginPath();
        ctx.moveTo(0, -gemSize * 0.85);
        ctx.lineTo(gemSize * 0.72, -gemSize * 0.32);
        ctx.lineTo(gemSize * 0.54, gemSize * 0.35);
        ctx.lineTo(0, gemSize * 0.58);
        ctx.lineTo(-gemSize * 0.54, gemSize * 0.35);
        ctx.lineTo(-gemSize * 0.72, -gemSize * 0.32);
        ctx.closePath();
        ctx.fillStyle = gemGrad;
        ctx.fill();
        ctx.lineWidth = 1.2;
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.85)';
        ctx.stroke();

        // Facet lines
        ctx.strokeStyle = 'rgba(148, 163, 184, 0.55)';
        ctx.lineWidth = 0.9;
        ctx.beginPath();
        ctx.moveTo(-gemSize * 0.72, -gemSize * 0.32);
        ctx.lineTo(gemSize * 0.72, -gemSize * 0.32);
        ctx.moveTo(-gemSize * 0.34, -gemSize * 0.62);
        ctx.lineTo(0, gemSize * 0.58);
        ctx.lineTo(gemSize * 0.34, -gemSize * 0.62);
        ctx.stroke();

        // Scintillation star glint synced to scroll progress
        const glintPulse = 0.45 + 0.55 * Math.abs(Math.sin(progress * Math.PI * 4));
        ctx.save();
        ctx.translate(-gemSize * 0.2, -gemSize * 0.42);
        ctx.rotate(progress * 2.5);
        ctx.fillStyle = `rgba(255, 255, 255, ${glintPulse.toFixed(2)})`;
        for (let k = 0; k < 2; k++) {
            ctx.rotate(Math.PI / 2);
            ctx.beginPath();
            ctx.ellipse(0, 0, gemSize * 0.55 * glintPulse, 1.4, 0, 0, Math.PI * 2);
            ctx.fill();
        }
        ctx.restore();

        ctx.restore(); // gem
        ctx.restore(); // ring

        // Subtle vignette so left-side hero text stays razor sharp
        const vignette = ctx.createLinearGradient(0, 0, w, 0);
        vignette.addColorStop(0, 'rgba(18, 18, 20, 0.78)');
        vignette.addColorStop(0.48, 'rgba(18, 18, 20, 0.25)');
        vignette.addColorStop(1, 'rgba(18, 18, 20, 0.35)');
        ctx.fillStyle = vignette;
        ctx.fillRect(0, 0, w, h);
    }

    function findNearestLoadedFrame(targetIdx) {
        if (frameLoaded[targetIdx] && frameImages[targetIdx]) {
            return frameImages[targetIdx];
        }
        for (let offset = 1; offset < totalFrames; offset++) {
            const back = targetIdx - offset;
            if (back >= 0 && frameLoaded[back] && frameImages[back]) return frameImages[back];
            const fwd = targetIdx + offset;
            if (fwd < totalFrames && frameLoaded[fwd] && frameImages[fwd]) return frameImages[fwd];
        }
        return null;
    }

    function renderCurrentFrame() {
        if (!canvasWidth || !canvasHeight) return;
        const clampedIdx = Math.max(0, Math.min(totalFrames - 1, Math.round(currentFrameIndex)));

        if (!useFallbackRenderer) {
            const img = findNearestLoadedFrame(clampedIdx);
            if (img) {
                drawImageCover(img);
                return;
            }
        }
        drawFallbackRing(currentProgress);
    }

    function loadSingleFrame(index) {
        return new Promise(function (resolve) {
            if (index < 0 || index >= totalFrames || frameImages[index]) {
                resolve(frameLoaded[index]);
                return;
            }
            const img = new Image();
            img.decoding = 'async';
            img.onload = function () {
                frameImages[index] = img;
                frameLoaded[index] = true;
                if (index === 0 || index === Math.round(currentFrameIndex)) {
                    renderCurrentFrame();
                }
                resolve(true);
            };
            img.onerror = function () {
                frameImages[index] = null;
                frameLoaded[index] = false;
                if (index === 0) {
                    useFallbackRenderer = true;
                    renderCurrentFrame();
                }
                resolve(false);
            };
            img.src = getFrameUrl(index);
        });
    }

    async function preloadFrames() {
        const firstOk = await loadSingleFrame(0);
        if (!firstOk) {
            useFallbackRenderer = true;
            renderCurrentFrame();
            return;
        }

        const initialLimit = Math.min(PRELOAD_INITIAL_COUNT, totalFrames);
        const initialBatch = [];
        for (let i = 1; i < initialLimit; i++) {
            initialBatch.push(loadSingleFrame(i));
        }
        await Promise.all(initialBatch);

        // Background lazy-loading for remaining frames in small batches
        let cursor = initialLimit;
        function loadNextBatch() {
            if (cursor >= totalFrames || useFallbackRenderer) return;
            const end = Math.min(totalFrames, cursor + 5);
            const batch = [];
            for (let i = cursor; i < end; i++) {
                batch.push(loadSingleFrame(i));
            }
            cursor = end;
            Promise.all(batch).then(function () {
                if (typeof window.requestIdleCallback === 'function') {
                    window.requestIdleCallback(loadNextBatch, { timeout: 250 });
                } else {
                    window.setTimeout(loadNextBatch, 30);
                }
            });
        }

        if (typeof window.requestIdleCallback === 'function') {
            window.requestIdleCallback(loadNextBatch, { timeout: 250 });
        } else {
            window.setTimeout(loadNextBatch, 50);
        }
    }

    // Quick View Modal Wiring for Glassmorphic Product Cards
    const qvModal = document.getElementById('scrollyQuickViewModal');
    const qvTitle = document.getElementById('qvTitle');
    const qvCategory = document.getElementById('qvCategory');
    const qvPrice = document.getElementById('qvPrice');
    const qvDesc = document.getElementById('qvDescription');
    const qvImg = document.getElementById('qvImage');
    const qvClose = document.getElementById('qvCloseBtn');
    const qvBackdrop = document.getElementById('qvBackdrop');

    function openQuickView(btn) {
        if (!qvModal || !btn) return;
        if (qvTitle) qvTitle.textContent = btn.dataset.title || '';
        if (qvCategory) qvCategory.textContent = btn.dataset.category || '925 Sterling Silver';
        if (qvPrice) qvPrice.textContent = btn.dataset.price || '';
        if (qvDesc) qvDesc.textContent = btn.dataset.desc || '';
        if (qvImg && btn.dataset.image) {
            qvImg.src = btn.dataset.image;
            qvImg.alt = btn.dataset.title || 'Luckjary Piece';
        }
        qvModal.classList.remove('hidden');
        qvModal.classList.add('flex');
        if (window.luckjaryLenis && typeof window.luckjaryLenis.stop === 'function') {
            window.luckjaryLenis.stop();
        }
    }

    function closeQuickView() {
        if (!qvModal) return;
        qvModal.classList.add('hidden');
        qvModal.classList.remove('flex');
        if (window.luckjaryLenis && typeof window.luckjaryLenis.start === 'function') {
            window.luckjaryLenis.start();
        }
    }

    document.querySelectorAll('.scrolly-quick-view-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            openQuickView(btn);
        });
    });
    if (qvClose) qvClose.addEventListener('click', closeQuickView);
    if (qvBackdrop) qvBackdrop.addEventListener('click', closeQuickView);
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeQuickView();
    });

    // Initialize Canvas & Preload Sequence
    resizeCanvas();
    preloadFrames();
    window.addEventListener('resize', resizeCanvas, { passive: true });

    // Setup GSAP ScrollTrigger + MatchMedia Timeline
    if (typeof window.gsap === 'undefined' || typeof window.ScrollTrigger === 'undefined') {
        return;
    }

    const gsap = window.gsap;
    const ScrollTrigger = window.ScrollTrigger;
    gsap.registerPlugin(ScrollTrigger);

    const mm = gsap.matchMedia();
    const frameState = { frame: 0 };

    const ctx = gsap.context(function () {
        // Desktop (>= 768px): Full Pinned 2-Phase Scrollytelling
        mm.add('(min-width: 768px) and (prefers-reduced-motion: no-preference)', function () {
            if (cardsWrapper) {
                cardsWrapper.classList.remove('scrolly-cards-static');
            }
            if (cardsTrack) {
                gsap.set(cardsTrack, { x: '100vw', opacity: 0.9 });
            }
            if (showcaseLabel) {
                gsap.set(showcaseLabel, { opacity: 0, y: 18 });
            }

            const tl = gsap.timeline({
                scrollTrigger: {
                    trigger: container,
                    start: 'top top',
                    end: `+=${desktopScrollDistance}`,
                    scrub: 0.8,
                    pin: true,
                    anticipatePin: 1,
                    invalidateOnRefresh: true,
                    onUpdate: function (self) {
                        currentProgress = self.progress;
                        if (progressBar) {
                            progressBar.style.transform = `scaleX(${self.progress.toFixed(4)})`;
                        }
                    },
                },
            });

            // Phase 1 (0% -> 55%): Scrub Ring Frames 0 -> TOTAL_FRAMES - 1 & Fade/Lift Hero Text
            tl.to(
                frameState,
                {
                    frame: totalFrames - 1,
                    ease: 'none',
                    duration: 0.55,
                    onUpdate: function () {
                        currentFrameIndex = frameState.frame;
                        renderCurrentFrame();
                    },
                },
                0
            );

            if (heroCopy) {
                tl.to(
                    heroCopy,
                    {
                        opacity: 0,
                        y: -52,
                        ease: 'power2.inOut',
                        duration: 0.36,
                        onUpdate: function () {
                            const op = parseFloat(gsap.getProperty(heroCopy, 'opacity'));
                            heroCopy.style.pointerEvents = op < 0.15 ? 'none' : 'auto';
                        },
                    },
                    0.04
                );
            }

            if (scrollCue) {
                tl.to(scrollCue, { opacity: 0, y: 20, duration: 0.12, ease: 'none' }, 0);
            }

            // Phase 2 (45% -> 100%): Overlap slightly & slide product cards Right -> Left
            if (showcaseLabel) {
                tl.to(showcaseLabel, { opacity: 1, y: 0, duration: 0.14, ease: 'power2.out' }, 0.45);
            }

            if (cardsTrack) {
                tl.fromTo(
                    cardsTrack,
                    { x: '100vw', opacity: 0.85 },
                    { x: '-35vw', opacity: 1, ease: 'none', duration: 0.55 },
                    0.45
                );
            }
        });

        // Mobile (< 768px): Shorter Pinned Scroll Distance + Responsive Card Travel
        mm.add('(max-width: 767px) and (prefers-reduced-motion: no-preference)', function () {
            if (cardsWrapper) {
                cardsWrapper.classList.remove('scrolly-cards-static');
            }
            if (cardsTrack) {
                gsap.set(cardsTrack, { x: '100vw', opacity: 0.9 });
            }
            if (showcaseLabel) {
                gsap.set(showcaseLabel, { opacity: 0, y: 14 });
            }

            const tl = gsap.timeline({
                scrollTrigger: {
                    trigger: container,
                    start: 'top top',
                    end: '+=2000',
                    scrub: 0.7,
                    pin: true,
                    anticipatePin: 1,
                    invalidateOnRefresh: true,
                    onUpdate: function (self) {
                        currentProgress = self.progress;
                        if (progressBar) {
                            progressBar.style.transform = `scaleX(${self.progress.toFixed(4)})`;
                        }
                    },
                },
            });

            tl.to(
                frameState,
                {
                    frame: totalFrames - 1,
                    ease: 'none',
                    duration: 0.52,
                    onUpdate: function () {
                        currentFrameIndex = frameState.frame;
                        renderCurrentFrame();
                    },
                },
                0
            );

            if (heroCopy) {
                tl.to(
                    heroCopy,
                    {
                        opacity: 0,
                        y: -36,
                        ease: 'power2.inOut',
                        duration: 0.32,
                        onUpdate: function () {
                            const op = parseFloat(gsap.getProperty(heroCopy, 'opacity'));
                            heroCopy.style.pointerEvents = op < 0.15 ? 'none' : 'auto';
                        },
                    },
                    0.03
                );
            }

            if (scrollCue) {
                tl.to(scrollCue, { opacity: 0, duration: 0.1 }, 0);
            }

            if (showcaseLabel) {
                tl.to(showcaseLabel, { opacity: 1, y: 0, duration: 0.14 }, 0.44);
            }

            if (cardsTrack) {
                tl.fromTo(
                    cardsTrack,
                    { x: '100vw', opacity: 0.88 },
                    {
                        x: function () {
                            const overflow = Math.max(240, cardsTrack.scrollWidth - window.innerWidth + 32);
                            return `-${overflow}px`;
                        },
                        opacity: 1,
                        ease: 'none',
                        duration: 0.56,
                    },
                    0.44
                );
            }
        });

        // Reduced Motion: Disable Pinning & Scrubbing, Show Clean Static Layout
        mm.add('(prefers-reduced-motion: reduce)', function () {
            currentFrameIndex = 0;
            currentProgress = 0.25;
            renderCurrentFrame();
            if (heroCopy) {
                gsap.set(heroCopy, { opacity: 1, y: 0, clearProps: 'transform' });
                heroCopy.style.pointerEvents = 'auto';
            }
            if (scrollCue) {
                scrollCue.style.display = 'none';
            }
            if (cardsWrapper) {
                cardsWrapper.classList.add('scrolly-cards-static');
            }
            if (cardsTrack) {
                gsap.set(cardsTrack, { x: 0, opacity: 1, clearProps: 'transform' });
            }
            if (showcaseLabel) {
                gsap.set(showcaseLabel, { opacity: 1, y: 0 });
            }
        });
    }, container);

    function cleanupScrollytelling() {
        window.removeEventListener('resize', resizeCanvas);
        mm.revert();
        ctx.revert();
    }

    window.addEventListener('pagehide', cleanupScrollytelling, { once: true });
})();
