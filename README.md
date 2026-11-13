# Luckjary — Luxury Fine Jewelry E-Commerce Platform

A modern, high-converting, and SEO-optimized e-commerce web application tailored specifically for **Luckjary**, an upscale 925 sterling silver jewelry retail brand. Built with **Python (Django)**, **HTML5/Tailwind CSS**, and **SQLite**.

---

## 💎 Features & Requirements Implemented

### 1. User Authentication System
* **Secure Login & Registration:** Email-based authentication with cryptographically generated email verification tokens.
* **Email Verification Flow:** Dedicated activation endpoints with simulated one-click activation in preview mode.
* **User Profile Dashboard:** Dedicated client vault displaying order history, real-time shipment status badges, and address management.
* **Saved Addresses Book:** Add, edit, set default, and delete multiple shipping/billing destinations.
* **Guest Checkout & Post-Purchase Account Creation:** Guests can complete orders without pre-registration; upon purchase confirmation, an automatic 1-click password setup links their orders and creates an active account.

### 2. Order Management System (OMS)
* **Customer Side:**
  * Real-time order tracking portal (`/track/` and `/track/<order_number>/`).
  * 4-Stage visual fulfillment milestone timeline (Order Placed ➔ Atelier QC & Handcrafting ➔ Armored Courier Transit ➔ Delivered).
  * Direct courier telemetry: Carrier name (`FedEx Luxury Priority Overnight`), tracking code with 1-click clipboard copy, and chronological activity log.
* **Admin / Atelier Side:**
  * Custom Branded Centralized OMS Dashboard (`/oms/`):
    * Real-time KPI statistics: Gross Sales, Active Orders, Pending Intake, In QC, In Courier Transit.
    * Order Queue management with instant status filter tabs (`All`, `Pending`, `Processing`, `Shipped`, `Delivered`).
    * Quick Status Update modal: Update milestone, courier, tracking code, delivery date, and log notes.
    * Live Atelier Vault Inventory Manager with automatic low-stock alerts.
  * Standard customized Django Admin interface at `/admin/`.

### 3. Product Pages & UI/UX Design
* **Visual Gallery:** Immersive multi-image gallery with interactive thumbnail switching and a smooth hover-lens magnifier zoom.
* **Luxury Aesthetic:** Tailored palette (Alabaster White `#FAF9F6`, Champagne Gold `#C5A059`, Deep Onyx `#121212`), Cormorant Garamond & Cinzel typography, gold foil badges.
* **Advanced Filtering & Sorting:**
  * Filter by Material (18K Solid Gold, Platinum 950, Sterling Silver, Diamonds, Emeralds, Pearls, etc.).
  * Filter by Category (Rings, Necklaces, Earrings, Bracelets, Bridal & High Jewelry).
  * Filter by Aesthetic Style (Timeless Classic, Modern Minimalist, Bridal, Art Deco).
  * Price range filter ($min to $max).
  * Sort by Curated/Featured, Price: Low to High, Price: High to Low, New Arrivals, Customer Rating.
* **Bag & Checkout:** Slide-out shopping bag drawer, promo code engine (`LUCKJARY10` for 10% off, `VIPLUCK20` for 20% off), complimentary gift packaging toggle, and handwritten card inscription.
* **Wishlist:** Quick-save heart toggle and dedicated wishlist vault.

### 4. SEO & Organic Growth Optimization
* **Semantic HTML5:** Structured `<header>`, `<nav>`, `<main>`, `<article>`, `<aside>`, `<footer>`.
* **Dynamic Meta Tags:** Unique title tags, meta descriptions, canonical URLs, and Open Graph / Twitter Card tags for all dynamic and static pages.
* **Google Rich Snippet Schema:** Integrated JSON-LD structured data (`@type: "Product"`, `offers`, `aggregateRating`, `brand: "Luckjary"`).
* **Performance & Clean URLs:** Clean slug-based routing (`/shop/`, `/category/<slug>/`, `/product/<slug>/`), `sitemap.xml`, and `robots.txt`.

---

## 🔑 Pre-Seeded Test Credentials

| Role | Email | Password | Details |
|---|---|---|---|
| **Admin / OMS Staff** | `admin@luckjary.com` | `admin12345` | Access to `/oms/` and `/admin/` |
| **VIP Client** | `isabella.vance@example.com` | `luxury12345` | Active orders, saved addresses, verified email |

### Sample Seeded Orders for Live Tracking
* `LCK-202611-884102` (Status: **Shipped** via FedEx Priority)
* `LCK-202611-194056` (Status: **Processing** in Atelier)
* `LCK-202611-739201` (Status: **Delivered** to Park Ave)

---

## 🚀 Getting Started

```bash
# 1. Navigate to the project directory
cd luckjary

# 2. Run database migrations (already applied)
python manage.py migrate

# 3. Seed demo luxury catalog and orders (if needed)
python manage.py seed_luckjary

# 4. Run automated test suite
python manage.py test

# 5. Launch development server
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.
