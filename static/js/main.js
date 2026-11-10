// Luckjary Fine Jewelry - Main Interactive Scripts

document.addEventListener('DOMContentLoaded', () => {
    initProductGalleryZoom();
    initCartDrawer();
    initMobileMenu();
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
            // If on cart page itself, allow normal navigation
            if (window.location.pathname.includes('/cart/')) return;
            e.preventDefault();
            openDrawer();
        });
    });

    if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
    if (overlay) overlay.addEventListener('click', closeDrawer);
}

// 3. Mobile Navigation Menu
function initMobileMenu() {
    const mobileBtn = document.getElementById('mobileMenuBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    if (mobileBtn && mobileMenu) {
        mobileBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }
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
