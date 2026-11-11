// Luckjary Fine Jewelry - Main Interactive Scripts

document.addEventListener('DOMContentLoaded', () => {
    initProductGalleryZoom();
    initCartDrawer();
    initMobileNavDrawer();
    initDeliveryPincode();
    initSearchPlaceholderRotation();
    initCardTouchSwiping();
});

// 1. High-Resolution Magnifying Zoom for Product Detail Page
function initProductGalleryZoom() {
    const zoomContainers = document.querySelectorAll('.interactive-zoom');
    zoomContainers.forEach(container => {
        const img = container.querySelector('img');
        if (!img) return;

        container.addEventListener('mousemove', (e) => {
            const rect = container.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;
            img.style.transformOrigin = `${x}% ${y}%`;
            img.style.transform = 'scale(2.0)';
        });

        container.addEventListener('mouseleave', () => {
            img.style.transform = 'scale(1)';
            img.style.transformOrigin = 'center center';
        });
    });

    // Thumbnail Switcher
    const thumbnails = document.querySelectorAll('.gallery-thumb');
    const mainImg = document.getElementById('mainProductImage');
    if (thumbnails.length && mainImg) {
        thumbnails.forEach(thumb => {
            thumb.addEventListener('click', () => {
                const newSrc = thumb.dataset.fullSrc || thumb.src;
                mainImg.src = newSrc;
                thumbnails.forEach(t => t.classList.remove('border-gold-500', 'ring-2', 'ring-[#C5A059]'));
                thumb.classList.add('border-gold-500', 'ring-2', 'ring-[#C5A059]');
            });
        });
    }
}

// 2. Slide-Out Cart Drawer Controls
function initCartDrawer() {
    const drawer = document.getElementById('cartDrawer');
    const overlay = document.getElementById('cartOverlay');
    const openBtns = document.querySelectorAll('.open-cart-drawer');
    const closeBtn = document.getElementById('closeCartDrawer');

    if (!drawer || !overlay) return;

    function openDrawer() {
        drawer.classList.remove('translate-x-full');
        overlay.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    function closeDrawer() {
        drawer.classList.add('translate-x-full');
        overlay.classList.add('hidden');
        document.body.style.overflow = '';
    }

    openBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            if (window.location.pathname.includes('/cart/')) return;
            e.preventDefault();
            openDrawer();
        });
    });

    if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
    if (overlay) overlay.addEventListener('click', closeDrawer);
}

// 3. Mobile Navigation Drawer Controls
function initMobileNavDrawer() {
    const drawer = document.getElementById('mobileNavDrawer');
    const overlay = document.getElementById('mobileDrawerOverlay');
    const openBtn = document.getElementById('mobileMenuBtn');
    const closeBtn = document.getElementById('closeMobileDrawerBtn');

    if (!drawer || !overlay || !openBtn) return;

    function openMobileDrawer() {
        drawer.classList.remove('-translate-x-full');
        overlay.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    function closeMobileDrawer() {
        drawer.classList.add('-translate-x-full');
        overlay.classList.add('hidden');
        document.body.style.overflow = '';
    }

    openBtn.addEventListener('click', openMobileDrawer);
    if (closeBtn) closeBtn.addEventListener('click', closeMobileDrawer);
    if (overlay) overlay.addEventListener('click', closeMobileDrawer);
}

// 4. Copy to Clipboard Utility
function copyToClipboard(text, elementId) {
    navigator.clipboard.writeText(text).then(() => {
        const el = document.getElementById(elementId);
        if (el) {
            const originalText = el.innerText;
            el.innerText = 'Copied!';
            el.classList.add('text-emerald-600');
            setTimeout(() => {
                el.innerText = originalText;
                el.classList.remove('text-emerald-600');
            }, 2000);
        }
    });
}

// 5. Where to Deliver? Delivery Pincode Modal & Hydration (GIVA Style)
function initDeliveryPincode() {
    const savedPin = localStorage.getItem('luckjary_pincode');
    const savedCity = localStorage.getItem('luckjary_city');
    if (savedPin) {
        updateHeaderPincodeDisplay(savedPin, savedCity);
    }
}

function openPincodeModal() {
    const modal = document.getElementById('pincodeModal');
    if (modal) {
        modal.classList.remove('hidden');
        const input = document.getElementById('modalPincodeInput');
        if (input) {
            input.value = localStorage.getItem('luckjary_pincode') || '';
            input.focus();
        }
    }
}

function closePincodeModal() {
    const modal = document.getElementById('pincodeModal');
    if (modal) modal.classList.add('hidden');
}

function applyPincode(e) {
    if (e) e.preventDefault();
    const input = document.getElementById('modalPincodeInput');
    const code = input ? input.value.trim() : '';
    if (!code || code.length < 4) {
        showPincodeFeedback('Please enter a valid 5 or 6 digit pincode', false);
        return;
    }
    savePincode(code);
}

function setQuickPincode(code, city) {
    const input = document.getElementById('modalPincodeInput');
    if (input) input.value = code;
    savePincode(code, city);
}

function savePincode(code, city) {
    localStorage.setItem('luckjary_pincode', code);
    if (city) localStorage.setItem('luckjary_city', city);
    updateHeaderPincodeDisplay(code, city);
    showPincodeFeedback(`✓ Deliverable to ${city || 'your location'} (${code}) — Free Insured Express Delivery in 2-3 Business Days!`, true);
    setTimeout(() => {
        closePincodeModal();
    }, 1200);
}

function updateHeaderPincodeDisplay(code, city) {
    const titleEl = document.getElementById('deliveryTitleText');
    const subEl = document.getElementById('deliverySubtitleText');
    if (titleEl && subEl) {
        if (code) {
            titleEl.textContent = `Deliver to: ${code}`;
            subEl.textContent = city ? `${city} (Change)` : 'Change Pincode';
        } else {
            titleEl.textContent = 'Where to Deliver?';
            subEl.textContent = 'Update Delivery Pincode';
        }
    }
}

function showPincodeFeedback(msg, isSuccess) {
    const fb = document.getElementById('pincodeFeedback');
    if (!fb) return;
    fb.classList.remove('hidden');
    if (isSuccess) {
        fb.className = 'mt-4 p-3 rounded-lg border text-xs bg-emerald-50 text-emerald-800 border-emerald-200 font-medium';
    } else {
        fb.className = 'mt-4 p-3 rounded-lg border text-xs bg-rose-50 text-rose-800 border-rose-200 font-medium';
    }
    fb.innerHTML = msg;
}

// 6. Dynamic Rotating Search Placeholder (GIVA style: Search "Pendants")
const searchPlaceholders = [
    'Search "Pendants"',
    'Search "Diamond Rings"',
    'Search "Gold Mangalsutra"',
    'Search "Silver Earrings"',
    'Search "Solitaire Necklaces"',
    'Search "Tennis Bracelets"',
    'Search "Evil Eye Jewellery"',
    'Search "Pearl Chokers"'
];
let currentPlaceholderIdx = 0;

function initSearchPlaceholderRotation() {
    setInterval(() => {
        const desktopInput = document.getElementById('mainSearchInput');
        const mobileInput = document.getElementById('mobileSearchInput');
        currentPlaceholderIdx = (currentPlaceholderIdx + 1) % searchPlaceholders.length;
        const nextText = searchPlaceholders[currentPlaceholderIdx];
        
        if (desktopInput && document.activeElement !== desktopInput) {
            desktopInput.setAttribute('placeholder', nextText);
        }
        if (mobileInput && document.activeElement !== mobileInput) {
            mobileInput.setAttribute('placeholder', nextText);
        }
    }, 2800);
}

// 7. Multi-Image Product Card Swiping & Navigation (Mia by Tanishq / GIVA style)
function swipeCardImage(prodId, direction) {
    const mediaContainer = document.getElementById('card-media-' + prodId);
    const img = document.getElementById('card-img-' + prodId);
    if (!mediaContainer || !img) return;

    let images = [];
    try {
        const raw = mediaContainer.dataset.images;
        images = typeof raw === 'string' ? JSON.parse(raw) : (raw || []);
    } catch (e) {
        images = [];
    }
    
    // Fallback to data attributes if dataset.images isn't present
    if (!images.length) {
        if (img.dataset.primary) images.push(img.dataset.primary);
        if (img.dataset.secondary && img.dataset.secondary !== img.dataset.primary) {
            images.push(img.dataset.secondary);
        }
    }

    if (images.length <= 1) return;

    let currentIndex = parseInt(mediaContainer.dataset.current || '0', 10);
    if (isNaN(currentIndex)) currentIndex = 0;

    let nextIndex = (currentIndex + direction + images.length) % images.length;
    mediaContainer.dataset.current = nextIndex;

    // Smooth subtle cross-fade transition
    img.style.opacity = '0.7';
    img.src = images[nextIndex];
    setTimeout(() => {
        img.style.opacity = '1';
    }, 120);

    // Update dynamic dots
    const dots = mediaContainer.querySelectorAll('.carousel-dot-' + prodId);
    dots.forEach((dot, idx) => {
        if (idx === nextIndex) {
            dot.className = 'carousel-dot-' + prodId + ' h-1 rounded-full shadow-sm transition-all duration-300 w-4 bg-white';
        } else {
            dot.className = 'carousel-dot-' + prodId + ' h-1 rounded-full shadow-sm transition-all duration-300 w-1.5 bg-white/60';
        }
    });
}

function goToCardImage(prodId, targetIndex) {
    const mediaContainer = document.getElementById('card-media-' + prodId);
    const img = document.getElementById('card-img-' + prodId);
    if (!mediaContainer || !img) return;

    let images = [];
    try {
        const raw = mediaContainer.dataset.images;
        images = typeof raw === 'string' ? JSON.parse(raw) : (raw || []);
    } catch (e) {
        images = [];
    }
    if (images.length <= targetIndex || targetIndex < 0) return;

    mediaContainer.dataset.current = targetIndex;
    img.style.opacity = '0.7';
    img.src = images[targetIndex];
    setTimeout(() => {
        img.style.opacity = '1';
    }, 120);

    const dots = mediaContainer.querySelectorAll('.carousel-dot-' + prodId);
    dots.forEach((dot, idx) => {
        if (idx === targetIndex) {
            dot.className = 'carousel-dot-' + prodId + ' h-1 rounded-full shadow-sm transition-all duration-300 w-4 bg-white';
        } else {
            dot.className = 'carousel-dot-' + prodId + ' h-1 rounded-full shadow-sm transition-all duration-300 w-1.5 bg-white/60';
        }
    });
}

function toggleCardImage(prodId, direction) {
    swipeCardImage(prodId, direction === 'prev' ? -1 : 1);
}

// 8. Mobile Touch Swipe Gesture Support for Product Cards
function initCardTouchSwiping() {
    const cardMediaList = document.querySelectorAll('[id^="card-media-"]');
    cardMediaList.forEach(container => {
        let touchStartX = 0;
        let touchEndX = 0;

        container.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });

        container.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            const diff = touchEndX - touchStartX;
            if (Math.abs(diff) > 40) {
                const prodId = container.dataset.cardId;
                if (prodId) {
                    if (diff < 0) {
                        swipeCardImage(prodId, 1); // Swipe left -> next image
                    } else {
                        swipeCardImage(prodId, -1); // Swipe right -> prev image
                    }
                }
            }
        }, { passive: true });
    });
}
