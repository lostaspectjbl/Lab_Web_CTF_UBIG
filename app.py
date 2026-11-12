import math
import os
import secrets
import sqlite3
import tempfile
from flask import (
    Flask,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

# ==============================================================================
# Master Data Produk & Pengaturan Toko "Nusatech"
# ==============================================================================
CREDIT = 100.0  # Saldo awal peserta dalam dolar

# Katalog 10 produk publik yang dapat dibeli
# Format: id: (nama, kategori, harga, rating, deskripsi, icon_type)
SHOP_PRODUCTS = {
    1: (
        "Drone Elang X200",
        "Elektronik",
        1249.0,
        5,
        "Drone fotografi profesional 4K HDR dengan gimbal stabilisasi 3-axis dan transmisi jarak jauh hingga 10 km.",
        "drone",
    ),
    2: (
        "Earbuds Gema Pro",
        "Elektronik",
        42.0,
        4,
        "Earphone nirkabel dengan Active Noise Cancellation (ANC), driver bass dinamis, dan baterai tahan 28 jam.",
        "audio",
    ),
    3: (
        "Tas Ransel Nomad 30L",
        "Aksesoris",
        79.5,
        5,
        "Ransel ergonomis tahan cuaca dengan kompartemen laptop 16 inci empuk dan material nilon Cordura anti air.",
        "bag",
    ),
    4: (
        "Lampu Pintar Senja",
        "Rumah Tangga",
        31.0,
        4,
        "Lampu meja LED pintar dengan 16 juta warna, pengatur ritme sirkadian, serta kontrol suara via asisten virtual.",
        "lamp",
    ),
    5: (
        "Kabel Multi Flexi-C",
        "Aksesoris",
        12.5,
        4,
        "Kabel jalinan nilon kevlar 3-in-1 mendukung pengisian daya cepat Power Delivery hingga 100W.",
        "cable",
    ),
    6: (
        "Powerbank Galaksi 20K",
        "Elektronik",
        54.0,
        5,
        "Pengisi daya portabel kapasitas 20.000 mAh dengan layar digital LED dan output triple port fast charging.",
        "battery",
    ),
    7: (
        "Mouse Optima Ergo",
        "Elektronik",
        37.5,
        4,
        "Mouse nirkabel desain ergonomis vertikal untuk mencegah ketegangan pergelangan tangan saat kerja berjam-jam.",
        "mouse",
    ),
    8: (
        "Sarung Tangan Touchscreen",
        "Wearable",
        8.99,
        3,
        "Sarung tangan termal hangat berbahan wol mikro dengan sensor konduktif untuk layar sentuh semua jenis smartphone.",
        "wearable",
    ),
    9: (
        "Tumbler Baja Everest",
        "Rumah Tangga",
        23.0,
        5,
        "Botol minum insulasi vakum ganda berdinding baja tahan karat SUS 304, menjaga suhu panas dan dingin hingga 24 jam.",
        "tumbler",
    ),
    10: (
        "Speaker Portabel Riak",
        "Elektronik",
        65.0,
        4,
        "Speaker bluetooth tahan air sertifikasi IPX7 dengan audio 360 derajat surround dan daya tahan baterai 15 jam.",
        "speaker",
    ),
}

# Icon SVG inline per kategori produk (tanpa request eksternal)
SVG_ICONS = {
    "drone": """<svg class="product-thumb-svg" viewBox="0 0 24 24" fill="none" stroke="#0e7c5f" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 12m-3 0a3 3 0 1 0 6 0a3 3 0 1 0 -6 0"/><line x1="9.5" y1="9.5" x2="4" y2="4"/><line x1="14.5" y1="9.5" x2="20" y2="4"/><line x1="9.5" y1="14.5" x2="4" y2="20"/><line x1="14.5" y1="14.5" x2="20" y2="20"/><circle cx="4" cy="4" r="2"/><circle cx="20" cy="4" r="2"/><circle cx="4" cy="20" r="2"/><circle cx="20" cy="20" r="2"/></svg>""",
    "audio": """<svg class="product-thumb-svg" viewBox="0 0 24 24" fill="none" stroke="#0e7c5f" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>""",
    "bag": """<svg class="product-thumb-svg" viewBox="0 0 24 24" fill="none" stroke="#0e7c5f" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10a4 4 0 0 1 4-4h8a4 4 0 0 1 4 4v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/><path d="M9 6V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/><line x1="8" y1="13" x2="16" y2="13"/></svg>""",
    "lamp": """<svg class="product-thumb-svg" viewBox="0 0 24 24" fill="none" stroke="#0e7c5f" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6"/><path d="M10 22h4"/><path d="M12 2a7 7 0 0 0-7 7c0 2.5 1.5 4.5 3 6h8c1.5-1.5 3-3.5 3-6a7 7 0 0 0-7-7z"/></svg>""",
    "cable": """<svg class="product-thumb-svg" viewBox="0 0 24 24" fill="none" stroke="#0e7c5f" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="6" rx="2"/><line x1="12" y1="8" x2="12" y2="16"/><rect x="8" y="16" width="8" height="6" rx="2"/></svg>""",
    "battery": """<svg class="product-thumb-svg" viewBox="0 0 24 24" fill="none" stroke="#0e7c5f" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="6" width="18" height="12" rx="2"/><line x1="23" y1="10" x2="23" y2="14"/><line x1="6" y1="12" x2="10" y2="12"/><line x1="8" y1="10" x2="8" y2="14"/></svg>""",
    "mouse": """<svg class="product-thumb-svg" viewBox="0 0 24 24" fill="none" stroke="#0e7c5f" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="2" width="14" height="20" rx="7"/><line x1="12" y1="6" x2="12" y2="10"/></svg>""",
    "wearable": """<svg class="product-thumb-svg" viewBox="0 0 24 24" fill="none" stroke="#0e7c5f" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0v8a4 4 0 0 1-4 4H10a4 4 0 0 1-4-4V8z"/><path d="M18 11a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2"/></svg>""",
    "tumbler": """<svg class="product-thumb-svg" viewBox="0 0 24 24" fill="none" stroke="#0e7c5f" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 2h10l-1.5 18a2 2 0 0 1-2 2h-3a2 2 0 0 1-2-2L7 2z"/><line x1="6" y1="6" x2="18" y2="6"/></svg>""",
    "speaker": """<svg class="product-thumb-svg" viewBox="0 0 24 24" fill="none" stroke="#0e7c5f" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="3"/><circle cx="12" cy="14" r="4"/><circle cx="12" cy="6" r="1"/></svg>""",
    "secret": """<svg class="product-thumb-svg" viewBox="0 0 24 24" fill="none" stroke="#b91c1c" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>""",
}


# ==============================================================================
# Inisialisasi Database SQLite
# ==============================================================================
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


def init_db(db_path, flags):
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass

    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS members")

    # Tabel produk untuk katalog dan Lab 1
    cur.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            rating INTEGER NOT NULL,
            description TEXT NOT NULL,
            icon_type TEXT NOT NULL,
            released INTEGER NOT NULL
        )
    """)

    # Seed 10 produk publik
    for pid, data in SHOP_PRODUCTS.items():
        name, cat, price, rating, desc, icon = data
        cur.execute(
            """INSERT INTO products (id, name, category, price, rating, description, icon_type, released)
               VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
            (pid, name, cat, price, rating, desc, icon),
        )

    # Seed produk tersembunyi (released=0) berisi FLAG_1
    flag_1 = flags.get(1, "CTF{placeholder_flag_1}")
    cur.execute(
        """INSERT INTO products (id, name, category, price, rating, description, icon_type, released)
           VALUES (11, 'Prototipe Sensor Cuaca v3', 'Elektronik', 899.0, 5, ?, 'secret', 0)""",
        (f"Unit pra-rilis sensor cuaca IoT untuk uji laboratorium. Kode lisensi firmware: {flag_1}",),
    )

    # Tabel users untuk login dan Lab 2
    cur.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # Admin dengan password acak & User reguler
    admin_pass = secrets.token_hex(16)
    cur.execute(
        "INSERT INTO users (username, password, role) VALUES ('admin_utama', ?, 'admin')",
        (admin_pass,),
    )
    cur.execute(
        "INSERT INTO users (username, password, role) VALUES ('budi_santoso', 'password123', 'customer')"
    )

    # Tabel members untuk registrasi, akun dan Lab 5
    cur.execute("""
        CREATE TABLE members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT NOT NULL
        )
    """)
    cur.execute(
        "INSERT INTO members (username, password_hash, email) VALUES ('andi_pratama', ?, 'andi@gmail.com')",
        (generate_password_hash("andi123"),),
    )

    conn.commit()
    conn.close()


# ==============================================================================
# Helper Fungsi Sesi
# ==============================================================================
def get_flag(lab_num):
    return current_app.config["FLAGS"].get(lab_num, f"CTF{{dev_flag_lab_{lab_num}}}")


def ensure_balance():
    if "balance" not in session:
        session["balance"] = CREDIT
    return float(session["balance"])


def ensure_cart_lab3():
    if "cart_lab3" not in session:
        session["cart_lab3"] = {}
    return dict(session["cart_lab3"])


def ensure_cart_lab4():
    if "cart_lab4" not in session:
        session["cart_lab4"] = {}
    return dict(session["cart_lab4"])


def ensure_lab6_price():
    if "lab6_price" not in session:
        session["lab6_price"] = 1249.0
    if "lab6_last_coupon" not in session:
        session["lab6_last_coupon"] = None
    return float(session["lab6_price"])


def current_member():
    username = session.get("member_user")
    if not username:
        return None
    return get_db().execute(
        "SELECT id, username, email FROM members WHERE username = ?", (username,)
    ).fetchone()


# ==============================================================================
# Template Dasar HTML (E-Commerce Nusatech)
# ==============================================================================
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ page_title }} - Nusatech Store</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <div class="announcement-bar">
    Gratis ongkir ke seluruh Indonesia untuk pesanan di atas $50 &middot; <strong>Nusatech Garansi Resmi 1 Tahun</strong>
  </div>

  <header class="site-header">
    <div class="header-container">
      <a href="{% if active_lab %}/lab{{ active_lab }}{% else %}/{% endif %}" class="brand-logo">
        <div class="brand-icon">N</div>
        <div class="brand-text">
          <h1>Nusatech</h1>
          <p>Belanja Cerdas &bull; Hidup Praktis</p>
        </div>
      </a>

      <nav>
        <ul class="nav-menu">
          {% if not active_lab %}
            <li><a class="nav-link {% if current_path == '/' %}active{% endif %}" href="/">Beranda</a></li>
            <li><a class="nav-link {% if current_path == '/lab1' %}active{% endif %}" href="/lab1">Katalog Produk</a></li>
            <li><a class="nav-link {% if current_path == '/lab2' %}active{% endif %}" href="/lab2">Masuk Akun</a></li>
            <li><a class="nav-link {% if current_path == '/lab3' %}active{% endif %}" href="/lab3">Promo Spesial</a></li>
            <li><a class="nav-link {% if current_path == '/lab4' %}active{% endif %}" href="/lab4">Keranjang</a></li>
            <li><a class="nav-link {% if current_path == '/lab5' %}active{% endif %}" href="/lab5">Akun Saya</a></li>
            <li><a class="nav-link {% if current_path == '/lab6' %}active{% endif %}" href="/lab6">Checkout</a></li>
          {% else %}
            {% if active_lab == 1 %}
              <li><a class="nav-link active" href="/lab1">Katalog Produk</a></li>
            {% elif active_lab == 2 %}
              <li><a class="nav-link active" href="/lab2">Masuk Akun</a></li>
            {% elif active_lab == 3 %}
              <li><a class="nav-link active" href="/lab3">Katalog &amp; Promo</a></li>
            {% elif active_lab == 4 %}
              <li><a class="nav-link active" href="/lab4">Keranjang Belanja</a></li>
            {% elif active_lab == 5 %}
              <li><a class="nav-link active" href="/lab5">Akun Saya</a></li>
            {% elif active_lab == 6 %}
              <li><a class="nav-link active" href="/lab6">Checkout Promo</a></li>
            {% endif %}
          {% endif %}

          {% if active_lab in [3, 4] or (not active_lab and current_path in ['/lab3', '/lab4']) %}
            <li>
              <div class="credit-pill">
                <span>Saldo Akun:</span> ${{ "%.2f"|format(balance if balance is defined else 100.0) }}
              </div>
            </li>
          {% endif %}

          {% if cart_count is defined and cart_count > 0 %}
            <li>
              <a href="{% if active_lab %}/lab{{ active_lab }}{% else %}/lab4{% endif %}" class="nav-link">
                Keranjang <span class="nav-badge">{{ cart_count }}</span>
              </a>
            </li>
          {% endif %}

          <li><a href="/reset" class="reset-link" title="Atur ulang sesi belanja">Reset Sesi</a></li>
        </ul>
      </nav>
    </div>
  </header>

  <main class="main-wrapper">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div class="flash-stack">
          {% for category, message in messages %}
            <div class="alert alert-{{ category }}">
              <div>{{ message|safe }}</div>
            </div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}

    {{ body|safe }}
  </main>

  <footer class="site-footer">
    <div class="footer-container">
      <div class="footer-copy">
        &copy; 2026 PT Nusatech Kreasi Digital. Hak Cipta Dilindungi.
        {% if show_debug_nav %}
          <a class="debug-link" href="/sitemap">Peta Situs</a>
        {% endif %}
      </div>
      <ul class="footer-links">
        <li><a href="#">Tentang Kami</a></li>
        <li><a href="#">Kontak Layanan</a></li>
        <li><a href="#">Kebijakan Privasi</a></li>
        <li><a href="#">Syarat &amp; Ketentuan</a></li>
      </ul>
    </div>
  </footer>
</body>
</html>
"""


# ==============================================================================
# Halaman Depan All-in-One (Saat LAB="")
# ==============================================================================
HOME_BODY = """
<div class="hero-card">
  <h2>Selamat Datang di Nusatech Store</h2>
  <p>Pusat perangkat pintar, gadget terkini, dan perlengkapan gaya hidup modern berkualitas tinggi dengan garansi resmi dan penawaran terbaik setiap hari.</p>
</div>

<div class="section-header">
  <h3 class="section-title">Jelajahi Portal Layanan Toko</h3>
</div>

<div class="product-grid" style="grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));">
  <div class="product-card">
    <div class="product-body">
      <span class="product-badge badge-category">Katalog &bull; Filter Produk</span>
      <h4 class="product-name" style="margin-top: 10px;">Katalog Produk &amp; Aksesoris</h4>
      <p class="product-desc">Cari dan saring katalog lengkap perlengkapan elektronik berdasarkan kategori minat Anda.</p>
      <div class="product-footer">
        <a href="/lab1" class="btn btn-primary">Buka Katalog</a>
      </div>
    </div>
  </div>

  <div class="product-card">
    <div class="product-body">
      <span class="product-badge badge-category">Autentikasi &bull; Pelanggan</span>
      <h4 class="product-name" style="margin-top: 10px;">Masuk ke Portal Akun</h4>
      <p class="product-desc">Akses dashboard akun pelanggan atau login pengelola toko untuk memantau status pesanan.</p>
      <div class="product-footer">
        <a href="/lab2" class="btn btn-primary">Halaman Masuk</a>
      </div>
    </div>
  </div>

  <div class="product-card">
    <div class="product-body">
      <span class="product-badge badge-category">Penawaran &bull; Khusus</span>
      <h4 class="product-name" style="margin-top: 10px;">Katalog Penawaran Spesial</h4>
      <p class="product-desc">Pesan produk unggulan langsung ke keranjang dengan diskon khusus dan konfirmasi kilat.</p>
      <div class="product-footer">
        <a href="/lab3" class="btn btn-primary">Lihat Penawaran</a>
      </div>
    </div>
  </div>

  <div class="product-card">
    <div class="product-body">
      <span class="product-badge badge-category">Belanja &bull; Checkout</span>
      <h4 class="product-name" style="margin-top: 10px;">Keranjang Belanja</h4>
      <p class="product-desc">Kelola jumlah unit barang belanjaan Anda sebelum melanjutkan ke pembayaran akhir.</p>
      <div class="product-footer">
        <a href="/lab4" class="btn btn-primary">Buka Keranjang</a>
      </div>
    </div>
  </div>

  <div class="product-card">
    <div class="product-body">
      <span class="product-badge badge-category">Keanggotaan &bull; Profil</span>
      <h4 class="product-name" style="margin-top: 10px;">Pendaftaran &amp; Profil Member</h4>
      <p class="product-desc">Daftar sebagai anggota Nusatech Club dan perbarui informasi kontak email terdaftar.</p>
      <div class="product-footer">
        <a href="/lab5" class="btn btn-primary">Kelola Profil</a>
      </div>
    </div>
  </div>

  <div class="product-card">
    <div class="product-body">
      <span class="product-badge badge-category">Promosi &bull; Diskon</span>
      <h4 class="product-name" style="margin-top: 10px;">Program Kupon Promosi</h4>
      <p class="product-desc">Gunakan voucher diskon promosi berkala untuk mendapatkan potongan harga produk incaran.</p>
      <div class="product-footer">
        <a href="/lab6" class="btn btn-primary">Klaim Kupon</a>
      </div>
    </div>
  </div>
</div>
"""


# ==============================================================================
# Template Halaman Tiap Lab
# ==============================================================================

# Lab 1 Template
LAB1_BODY = """
<div class="hero-card">
  <h2>Katalog Produk &amp; Inovasi Nusatech</h2>
  <p>Temukan produk teknologi terkini mulai dari perlengkapan elektronik, smart home, hingga aksesoris esensial sehari-hari.</p>
</div>

<div class="filter-bar">
  <div class="filter-categories">
    <span class="filter-label">Kategori:</span>
    <a href="/lab1" class="filter-pill {% if not active_cat %}active{% endif %}">Semua Produk</a>
    <a href="/lab1?category=Elektronik" class="filter-pill {% if active_cat == 'Elektronik' %}active{% endif %}">Elektronik</a>
    <a href="/lab1?category=Aksesoris" class="filter-pill {% if active_cat == 'Aksesoris' %}active{% endif %}">Aksesoris</a>
    <a href="/lab1?category=Rumah+Tangga" class="filter-pill {% if active_cat == 'Rumah Tangga' %}active{% endif %}">Rumah Tangga</a>
    <a href="/lab1?category=Wearable" class="filter-pill {% if active_cat == 'Wearable' %}active{% endif %}">Wearable</a>
  </div>

  <form method="GET" action="/lab1" class="filter-search">
    <input type="text" name="category" value="{{ search_val }}" placeholder="Filter kategori...">
    <button type="submit" class="btn btn-secondary btn-sm">Filter</button>
  </form>
</div>

{% if error_msg %}
  <div class="alert alert-error">
    {{ error_msg }}
  </div>
{% endif %}

<div class="product-grid">
  {% for p in products %}
    <div class="product-card">
      <div class="product-thumb">
        <span class="product-badge {% if p['released'] == 0 %}badge-unreleased{% else %}badge-category{% endif %}">
          {% if p['released'] == 0 %}Pra-Rilis Internal{% else %}{{ p['category'] }}{% endif %}
        </span>
        {{ svg_map.get(p['icon_type'], svg_map['secret'])|safe }}
      </div>
      <div class="product-body">
        <h4 class="product-name">{{ p['name'] }}</h4>
        <div class="product-rating">
          {% for _ in range(p['rating']) %}<span class="star-icon">&#9733;</span>{% endfor %}
          <span class="rating-count">({{ p['rating'] }}.0)</span>
        </div>
        <p class="product-desc">{{ p['description'] }}</p>
        <div class="product-footer">
          <div class="product-price">${{ "%.2f"|format(p['price']) }}</div>
          {% if p['released'] == 0 %}
            <button class="btn btn-secondary" disabled>Stok Terbatas / Internal</button>
          {% else %}
            <button class="btn btn-primary" onclick="alert('Produk siap dipesan di keranjang belanja!')">Lihat Detail</button>
          {% endif %}
        </div>
      </div>
    </div>
  {% else %}
    <div style="grid-column: 1 / -1; padding: 48px; text-align: center; color: var(--text-muted); background: white; border-radius: var(--radius-md); border: 1px solid var(--border);">
      Tidak ada produk yang sesuai dengan kategori yang dipilih.
    </div>
  {% endfor %}
</div>
"""

# Lab 2 Template
LAB2_BODY = """
<div style="max-width: 480px; margin: 32px auto;">
  <div class="auth-card">
    <div style="text-align: center; margin-bottom: 20px;">
      <div class="brand-icon" style="margin: 0 auto 12px; width: 44px; height: 44px; font-size: 1.4em;">N</div>
      <h3>Masuk ke Akun Anda</h3>
      <p class="subtitle">Kelola pesanan, alamat pengiriman, dan riwayat belanja Nusatech Anda.</p>
    </div>

    {% if login_error %}
      <div class="alert alert-error" style="margin-bottom: 18px;">
        {{ login_error }}
      </div>
    {% endif %}

    {% if admin_logged %}
      <div class="internal-panel" style="margin-bottom: 20px;">
        <div class="internal-badge">&#128274; Dashboard Administrator</div>
        <h4 style="color: var(--primary); font-size: 1.2em; margin-bottom: 6px;">Selamat Datang, Administrator Utama!</h4>
        <p style="font-size: 0.9em; color: var(--text-muted); margin-bottom: 14px;">Autentikasi manajemen sistem terkonfirmasi. Token verifikasi akses:</p>
        <div class="flag-box">{{ flag }}</div>
        <div style="margin-top: 18px;">
          <a href="/reset" class="btn btn-secondary btn-sm">Keluar Sesi</a>
        </div>
      </div>
    {% elif user_logged %}
      <div class="alert alert-info" style="margin-bottom: 20px;">
        <div>
          <strong>Halo, {{ user_logged }}!</strong>
          <p style="font-size: 0.9em; margin-top: 4px;">Anda berhasil masuk sebagai pelanggan reguler. Saat ini tidak ada laporan khusus di akun Anda.</p>
        </div>
      </div>
      <div style="text-align: center;">
        <a href="/reset" class="btn btn-secondary">Keluar Sesi</a>
      </div>
    {% else %}
      <form method="POST" action="/lab2">
        <div class="form-group">
          <label class="form-label" for="username">Nama Pengguna (Username)</label>
          <input class="form-input" type="text" id="username" name="username" required autofocus placeholder="Masukkan username">
        </div>

        <div class="form-group">
          <label class="form-label" for="password">Kata Sandi (Password)</label>
          <input class="form-input" type="password" id="password" name="password" required placeholder="Masukkan kata sandi">
        </div>

        <div style="margin-top: 24px;">
          <button type="submit" class="btn btn-primary btn-lg">Masuk Sekarang</button>
        </div>
      </form>
      <div style="margin-top: 20px; text-align: center; font-size: 0.85em; color: var(--text-muted);">
        Pelanggan demo: <code>budi_santoso</code> &bull; Password: <code>password123</code>
      </div>
    {% endif %}
  </div>
</div>
"""

# Lab 3 Template
LAB3_BODY = """
{% if cart_items %}
  <div class="cart-card">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h3 style="font-size: 1.3em; font-weight: 700;">Keranjang Penawaran Anda</h3>
      <form method="POST" action="/lab3">
        <input type="hidden" name="action" value="empty">
        <button type="submit" class="btn btn-secondary btn-sm">Kosongkan Keranjang</button>
      </form>
    </div>

    <div class="cart-table-wrapper">
      <table class="cart-table">
        <thead>
          <tr>
            <th>Nama Produk</th>
            <th class="text-right">Harga Satuan</th>
            <th class="text-center">Jumlah</th>
            <th class="text-right">Subtotal</th>
          </tr>
        </thead>
        <tbody>
          {% for item in cart_items %}
            <tr>
              <td style="font-weight: 600;">{{ item.name }}</td>
              <td class="text-right">${{ "%.2f"|format(item.price) }}</td>
              <td class="text-center">{{ item.qty }}</td>
              <td class="text-right" style="font-weight: 700;">${{ "%.2f"|format(item.subtotal) }}</td>
            </tr>
          {% endfor %}
          <tr class="total-row">
            <td colspan="3" class="text-right" style="padding-right: 16px;">Total Tagihan:</td>
            <td class="text-right total-amount">${{ "%.2f"|format(total) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px; flex-wrap: wrap; gap: 12px;">
      <div class="credit-pill">
        <span>Sisa Saldo Akun Anda:</span> ${{ "%.2f"|format(balance) }}
      </div>
      <form method="POST" action="/lab3">
        <input type="hidden" name="action" value="checkout">
        <button type="submit" class="btn btn-accent btn-lg">Konfirmasi &amp; Bayar Pesanan</button>
      </form>
    </div>
  </div>
{% endif %}

<div class="section-header">
  <h3 class="section-title">Katalog Produk Unggulan</h3>
</div>

<div class="product-grid">
  {% for pid, p in products.items() %}
    <div class="product-card">
      <div class="product-thumb">
        <span class="product-badge badge-category">{{ p[1] }}</span>
        {{ svg_map.get(p[5], svg_map['drone'])|safe }}
      </div>
      <div class="product-body">
        <h4 class="product-name">{{ p[0] }}</h4>
        <div class="product-rating">
          {% for _ in range(p[3]) %}<span class="star-icon">&#9733;</span>{% endfor %}
          <span class="rating-count">({{ p[3] }}.0)</span>
        </div>
        <p class="product-desc">{{ p[4] }}</p>
        <div class="product-footer">
          <div class="product-price">${{ "%.2f"|format(p[2]) }}</div>
          <form method="POST" action="/lab3">
            <input type="hidden" name="action" value="add">
            <input type="hidden" name="pid" value="{{ pid }}">
            <input type="hidden" name="price" value="{{ '%.2f'|format(p[2]) }}">
            <div class="qty-control" style="width: 100%; margin-bottom: 8px;">
              <span style="font-size: 0.85em; font-weight: 600;">Qty:</span>
              <input type="number" name="qty" value="1" min="1" class="qty-input">
              <button type="submit" class="btn btn-primary btn-sm" style="flex: 1;">Tambah ke Keranjang</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  {% endfor %}
</div>
"""

# Lab 4 Template
LAB4_BODY = """
{% if cart_items %}
  <div class="cart-card">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h3 style="font-size: 1.3em; font-weight: 700;">Daftar Belanja di Keranjang</h3>
      <form method="POST" action="/lab4">
        <input type="hidden" name="action" value="empty">
        <button type="submit" class="btn btn-secondary btn-sm">Kosongkan</button>
      </form>
    </div>

    <div class="cart-table-wrapper">
      <table class="cart-table">
        <thead>
          <tr>
            <th>Item Produk</th>
            <th class="text-right">Harga Resmi</th>
            <th class="text-center">Kuantitas</th>
            <th class="text-right">Total Nilai</th>
          </tr>
        </thead>
        <tbody>
          {% for item in cart_items %}
            <tr>
              <td style="font-weight: 600;">{{ item.name }}</td>
              <td class="text-right">${{ "%.2f"|format(item.price) }}</td>
              <td class="text-center">{{ item.qty }}</td>
              <td class="text-right" style="font-weight: 700;">${{ "%.2f"|format(item.subtotal) }}</td>
            </tr>
          {% endfor %}
          <tr class="total-row">
            <td colspan="3" class="text-right" style="padding-right: 16px;">Total Pembayaran:</td>
            <td class="text-right total-amount">${{ "%.2f"|format(total) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px; flex-wrap: wrap; gap: 12px;">
      <div class="credit-pill">
        <span>Batas Kredit Saldo Anda:</span> ${{ "%.2f"|format(balance) }}
      </div>
      <form method="POST" action="/lab4">
        <input type="hidden" name="action" value="checkout">
        <button type="submit" class="btn btn-accent btn-lg">Selesaikan Pesanan</button>
      </form>
    </div>
  </div>
{% endif %}

<div class="section-header">
  <h3 class="section-title">Pilih Barang untuk Ditambahkan</h3>
</div>

<div class="product-grid">
  {% for pid, p in products.items() %}
    <div class="product-card">
      <div class="product-thumb">
        <span class="product-badge badge-category">{{ p[1] }}</span>
        {{ svg_map.get(p[5], svg_map['drone'])|safe }}
      </div>
      <div class="product-body">
        <h4 class="product-name">{{ p[0] }}</h4>
        <p class="product-desc">{{ p[4] }}</p>
        <div class="product-footer">
          <div class="product-price">${{ "%.2f"|format(p[2]) }}</div>
          <form method="POST" action="/lab4">
            <input type="hidden" name="action" value="add">
            <input type="hidden" name="pid" value="{{ pid }}">
            <div class="qty-control" style="width: 100%;">
              <span style="font-size: 0.85em; font-weight: 600;">Jumlah:</span>
              <input type="number" name="qty" value="1" class="qty-input">
              <button type="submit" class="btn btn-primary btn-sm" style="flex: 1;">Masukkan</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  {% endfor %}
</div>
"""

# Lab 5 Template
LAB5_BODY = """
{% if member %}
  <div style="max-width: 640px; margin: 20px auto;">
    <div class="auth-card">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
        <div>
          <h3>Profil Pengguna Terdaftar</h3>
          <p class="subtitle" style="margin-bottom: 0;">Kelola data kontak dan akun Nusatech Anda.</p>
        </div>
        <a href="/reset" class="btn btn-secondary btn-sm">Keluar</a>
      </div>

      <div style="background: var(--bg-page); padding: 16px; border-radius: var(--radius-md); margin-bottom: 24px; border: 1px solid var(--border);">
        <p style="margin-bottom: 6px;"><strong>Nama Pengguna:</strong> {{ member['username'] }}</p>
        <p><strong>Alamat Email Aktif:</strong> <code style="color: var(--primary); font-weight: bold;">{{ member['email'] }}</code></p>
      </div>

      <h4 style="font-size: 1.05em; font-weight: 700; margin-bottom: 12px;">Perbarui Alamat Email</h4>
      <form method="POST" action="/lab5/update-email">
        <div class="form-group">
          <label class="form-label" for="new-email">Alamat Email Baru</label>
          <input class="form-input" type="email" id="new-email" name="email" value="{{ member['email'] }}" required>
          <p class="form-hint">Email ini akan digunakan untuk konfirmasi transaksi dan akses layanan akun.</p>
        </div>
        <button type="submit" class="btn btn-primary">Simpan Perubahan Email</button>
      </form>

      <div style="margin-top: 28px; padding-top: 20px; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">
        <div>
          <span style="font-size: 0.88em; font-weight: 600; color: var(--text-muted);">Pintu Khusus Staf Perusahaan:</span>
        </div>
        <a href="/lab5/internal" class="btn btn-outline btn-sm">Buka Panel Internal &rarr;</a>
      </div>
    </div>
  </div>
{% else %}
  <div class="auth-grid">
    <div class="auth-card">
      <h3>Masuk ke Akun Member</h3>
      <p class="subtitle">Bagi anggota yang telah memiliki akun terdaftar.</p>

      <form method="POST" action="/lab5/login">
        <div class="form-group">
          <label class="form-label" for="l-username">Nama Pengguna</label>
          <input class="form-input" type="text" id="l-username" name="username" required>
        </div>
        <div class="form-group">
          <label class="form-label" for="l-password">Kata Sandi</label>
          <input class="form-input" type="password" id="l-password" name="password" required>
        </div>
        <div style="margin-top: 20px;">
          <button type="submit" class="btn btn-primary btn-lg">Masuk Akun</button>
        </div>
      </form>
    </div>

    <div class="auth-card">
      <h3>Daftar Anggota Baru</h3>
      <p class="subtitle">Bergabung untuk menikmati berbagai kemudahan belanja online.</p>

      <form method="POST" action="/lab5/register">
        <div class="form-group">
          <label class="form-label" for="r-username">Nama Pengguna</label>
          <input class="form-input" type="text" id="r-username" name="username" required>
        </div>
        <div class="form-group">
          <label class="form-label" for="r-email">Alamat Email</label>
          <input class="form-input" type="email" id="r-email" name="email" placeholder="contoh@gmail.com" required>
          <p class="form-hint">Pendaftaran staf dengan domain <code>@nusatech.internal</code> harus melalui verifikasi khusus HR.</p>
        </div>
        <div class="form-group">
          <label class="form-label" for="r-password">Kata Sandi</label>
          <input class="form-input" type="password" id="r-password" name="password" required>
        </div>
        <div style="margin-top: 20px;">
          <button type="submit" class="btn btn-accent btn-lg">Daftar Akun Baru</button>
        </div>
      </form>
    </div>
  </div>
{% endif %}
"""

# Lab 5 Internal Dashboard Template
LAB5_INTERNAL_BODY = """
<div style="max-width: 680px; margin: 32px auto;">
  <div class="internal-panel">
    <div class="internal-badge">&#128274; Nusatech Internal Network</div>
    <h2 style="color: var(--primary); font-size: 1.6em; margin-bottom: 8px;">Portal Manajemen Staf Internal</h2>
    <p style="color: var(--text-muted); margin-bottom: 20px;">Selamat datang! Identitas email korporat Anda (<code>{{ member['email'] }}</code>) telah diverifikasi sebagai staf resmi Nusatech.</p>

    <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: var(--radius-md); padding: 20px; margin-bottom: 24px;">
      <h4 style="color: #166534; margin-bottom: 6px; font-size: 1.05em;">Token Akses Server Internal:</h4>
      <div class="flag-box">{{ flag }}</div>
    </div>

    <div style="display: flex; gap: 12px;">
      <a href="/lab5" class="btn btn-secondary">Kembali ke Akun Saya</a>
      <a href="/reset" class="btn btn-outline">Keluar Sesi</a>
    </div>
  </div>
</div>
"""

# Lab 6 Template
LAB6_BODY = """
<div style="max-width: 760px; margin: 24px auto;">
  <div class="cart-card">
    <div class="section-header" style="margin-bottom: 16px;">
      <div>
        <h3 style="font-size: 1.35em; font-weight: 700;">Checkout Pesanan Khusus</h3>
        <p style="color: var(--text-muted); font-size: 0.9em;">Gunakan kupon promosi yang valid untuk mendapatkan diskon terbaik.</p>
      </div>
    </div>

    <div class="cart-table-wrapper" style="margin-bottom: 24px;">
      <table class="cart-table">
        <thead>
          <tr>
            <th>Barang Pesanan</th>
            <th class="text-right">Harga Awal</th>
            <th class="text-center">Jumlah</th>
            <th class="text-right">Harga Setelah Kupon</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="font-weight: 700;">
              <span style="display: inline-block; width: 10px; height: 10px; background: var(--primary); border-radius: 50%; margin-right: 8px;"></span>
              Drone Elang X200
            </td>
            <td class="text-right">$1249.00</td>
            <td class="text-center">1</td>
            <td class="text-right total-amount" style="font-size: 1.25em;">${{ "%.2f"|format(price) }}</td>
          </tr>
          <tr class="total-row">
            <td colspan="3" class="text-right" style="padding-right: 16px;">Total Yang Harus Dibayar:</td>
            <td class="text-right total-amount">${{ "%.2f"|format(price) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div style="background: var(--bg-page); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 18px; margin-bottom: 24px;">
      <h4 style="font-size: 0.95em; font-weight: 700; margin-bottom: 8px;">Masukkan Kode Promo Anda</h4>
      <form method="POST" action="/lab6/coupon" class="coupon-box">
        <input type="text" name="code" placeholder="Contoh: HEMAT50" required autocomplete="off">
        <button type="submit" class="btn btn-primary" style="width: auto;">Terapkan Kupon</button>
      </form>
      <div style="margin-top: 10px; font-size: 0.82em; color: var(--text-muted);">
        Kupon aktif bulan ini: <code>HEMAT50</code> (Potongan langsung $50) dan <code>DISKON30</code> (Diskon 30% dari harga saat ini).
      </div>
    </div>

    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
      <div class="credit-pill">
        <span>Saldo Rekening Anda:</span> ${{ "%.2f"|format(balance) }}
      </div>
      <form method="POST" action="/lab6/checkout">
        <button type="submit" class="btn btn-accent btn-lg">Bayar Sekarang &rarr;</button>
      </form>
    </div>
  </div>
</div>
"""

# Halaman 404 & 403
NOT_FOUND_BODY = """
<div style="text-align: center; padding: 64px 20px;">
  <h2 style="font-size: 2.4em; color: #b91c1c; font-weight: 800; margin-bottom: 8px;">404</h2>
  <h3 style="font-size: 1.3em; margin-bottom: 12px;">Halaman Tidak Ditemukan</h3>
  <p style="color: var(--text-muted); max-width: 480px; margin: 0 auto 24px;">Alamat yang Anda tuju tidak tersedia atau telah dipindahkan ke tautan lain.</p>
  <a href="/" class="btn btn-primary btn-sm">Kembali ke Beranda</a>
</div>
"""

FORBIDDEN_BODY = """
<div style="text-align: center; padding: 64px 20px;">
  <h2 style="font-size: 2.4em; color: #b91c1c; font-weight: 800; margin-bottom: 8px;">403</h2>
  <h3 style="font-size: 1.3em; margin-bottom: 12px;">Akses Dibatasi</h3>
  <p style="color: var(--text-muted); max-width: 520px; margin: 0 auto 24px;">Halaman ini merupakan area terbatas yang hanya dapat dibuka oleh akun dengan otorisasi khusus.</p>
  <a href="/" class="btn btn-primary btn-sm">Kembali ke Beranda</a>
</div>
"""

SITEMAP_BODY = """
<div class="hero-card">
  <h2>Peta Situs Pengujian &bull; Nusatech</h2>
  <p>Daftar tautan langsung menuju semua modul layanan untuk keperluan peninjauan dan pengujian instruktur.</p>
</div>

<div class="cart-card">
  <ul style="list-style: none; display: flex; flex-direction: column; gap: 12px;">
    <li><a href="/lab1" class="btn btn-outline" style="justify-content: flex-start;">Lab 1: Katalog Produk (SQLi WHERE Clause) &rarr;</a></li>
    <li><a href="/lab2" class="btn btn-outline" style="justify-content: flex-start;">Lab 2: Masuk ke Akun (SQLi Login Bypass) &rarr;</a></li>
    <li><a href="/lab3" class="btn btn-outline" style="justify-content: flex-start;">Lab 3: Promo Spesial (Excessive Trust in Client-Side Price) &rarr;</a></li>
    <li><a href="/lab4" class="btn btn-outline" style="justify-content: flex-start;">Lab 4: Keranjang Belanja (High-Level Logic / Qty Flaw) &rarr;</a></li>
    <li><a href="/lab5" class="btn btn-outline" style="justify-content: flex-start;">Lab 5: Akun Saya &amp; Internal Panel (Inconsistent Email Control) &rarr;</a></li>
    <li><a href="/lab6" class="btn btn-outline" style="justify-content: flex-start;">Lab 6: Checkout Promo (Flawed Business Rule Enforcement) &rarr;</a></li>
  </ul>
</div>
"""


def render_page(template_body, page_title="Toko Online", **context):
    active_lab_val = current_app.config.get("LAB")
    active_lab = int(active_lab_val) if active_lab_val else None
    rendered_body = render_template_string(template_body, **context)
    return render_template_string(
        BASE_TEMPLATE,
        page_title=page_title,
        body=rendered_body,
        active_lab=active_lab,
        current_path=request.path,
        show_debug_nav=(os.environ.get("SHOW_DEBUG_NAV") == "1"),
        **context,
    )


# ==============================================================================
# Inisialisasi Factory Aplikasi Flask
# ==============================================================================
def create_app():
    app = Flask(__name__, static_folder="static")

    lab_env = os.environ.get("LAB", "").strip()
    if lab_env and lab_env not in {"1", "2", "3", "4", "5", "6"}:
        raise ValueError("Variabel lingkungan LAB harus bernilai antara 1 sampai 6 atau dikosongkan.")

    app.config["LAB"] = lab_env
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or os.environ.get(
        f"SECRET_KEY_{lab_env}", "dev-insecure-key-nusatech"
    )
    default_db = (
        os.path.join(tempfile.gettempdir(), "lab.db")
        if os.name == "nt"
        else "/tmp/lab.db"
    )
    app.config["DB_PATH"] = os.environ.get("DB_PATH", default_db)
    app.config["FLAGS"] = {
        n: os.environ.get(f"FLAG_{n}", f"CTF{{dev_flag_lab_{n}}}") for n in range(1, 7)
    }

    # Buat ulang database segar saat inisialisasi aplikasi
    init_db(app.config["DB_PATH"], app.config["FLAGS"])

    # Teardown database per request context
    @app.teardown_appcontext
    def close_db(error):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    # Middleware pembatasan rute saat mode per-lab (LAB="1".."6")
    @app.before_request
    def enforce_lab_mode():
        active = app.config["LAB"]
        if not active:
            return None

        path = request.path
        # Izinkan asset static dan route reset
        if path.startswith("/static") or path == "/reset":
            return None

        # Root dialihkan ke lab aktif
        if path == "/":
            return redirect(f"/lab{active}", code=302)

        # Rute lab aktif diizinkan
        allowed_prefix = f"/lab{active}"
        if path == allowed_prefix or path.startswith(allowed_prefix + "/"):
            return None

        # Path lain menghasilkan 404
        abort(404)

    # --------------------------------------------------------------------------
    # Rute Beranda & Utilitas
    # --------------------------------------------------------------------------
    @app.route("/")
    def index():
        return render_page(HOME_BODY, page_title="Beranda")

    @app.route("/reset")
    def reset_session():
        session.clear()
        flash("Sesi belanja dan pengaturan akun telah diatur ulang.", "info")
        active = app.config["LAB"]
        if active:
            return redirect(f"/lab{active}")
        return redirect("/")

    @app.route("/sitemap")
    def sitemap():
        if os.environ.get("SHOW_DEBUG_NAV") != "1":
            abort(404)
        return render_page(SITEMAP_BODY, page_title="Peta Situs")

    # --------------------------------------------------------------------------
    # Lab 1 - SQL Injection: WHERE clause retrieval of hidden data
    # --------------------------------------------------------------------------
    @app.route("/lab1")
    def lab1():
        cat = request.args.get("category", "").strip()
        db = get_db()
        error_msg = None
        products = []

        if cat:
            # Query rentan dengan penggabungan string langsung
            vulnerable_sql = f"SELECT * FROM products WHERE category = '{cat}' AND released = 1"
            try:
                products = db.execute(vulnerable_sql).fetchall()
            except sqlite3.Error:
                error_msg = "Terjadi gangguan saat memuat produk kategori tersebut. Silakan coba lagi nanti."
                products = []
        else:
            safe_sql = "SELECT * FROM products WHERE released = 1 ORDER BY id ASC"
            products = db.execute(safe_sql).fetchall()

        return render_page(
            LAB1_BODY,
            page_title="Katalog Produk",
            products=products,
            active_cat=cat,
            search_val=cat,
            error_msg=error_msg,
            svg_map=SVG_ICONS,
        )

    # --------------------------------------------------------------------------
    # Lab 2 - SQL Injection: Login Bypass
    # --------------------------------------------------------------------------
    @app.route("/lab2", methods=["GET", "POST"])
    def lab2():
        login_error = None
        admin_logged = False
        user_logged = None
        flag_2 = get_flag(2)

        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")

            # Query rentan pada klausa WHERE username dan password
            query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
            db = get_db()
            try:
                row = db.execute(query).fetchone()
            except sqlite3.Error:
                row = None
                login_error = "Terjadi gangguan pada server verifikasi akun."

            if row:
                if row["username"] == "admin_utama" or row["role"] == "admin":
                    admin_logged = True
                    session["lab2_admin"] = True
                else:
                    user_logged = row["username"]
                    session["lab2_user"] = row["username"]
            elif not login_error:
                login_error = "Nama pengguna atau kata sandi tidak sesuai. Silakan periksa kembali."

        if session.get("lab2_admin"):
            admin_logged = True
        elif session.get("lab2_user"):
            user_logged = session.get("lab2_user")

        return render_page(
            LAB2_BODY,
            page_title="Masuk ke Akun",
            login_error=login_error,
            admin_logged=admin_logged,
            user_logged=user_logged,
            flag=flag_2,
        )

    # --------------------------------------------------------------------------
    # Lab 3 - Business Logic: Excessive Trust in Client-Side Controls
    # --------------------------------------------------------------------------
    @app.route("/lab3", methods=["GET", "POST"])
    def lab3():
        balance = ensure_balance()
        cart = ensure_cart_lab3()

        if request.method == "POST":
            action = request.form.get("action", "")

            # Aksi 1: Tambah item ke keranjang
            if action == "add":
                pid = request.form.get("pid", type=int)
                qty = request.form.get("qty", 1, type=int)
                client_price = request.form.get("price", type=float)

                if pid not in SHOP_PRODUCTS or qty is None or qty <= 0:
                    flash("Jumlah unit atau produk tidak valid.", "error")
                    return redirect("/lab3")
                if client_price is None or not math.isfinite(client_price) or client_price < 0:
                    flash("Nominal harga produk tidak valid.", "error")
                    return redirect("/lab3")

                key = str(pid)
                if key in cart:
                    cart[key]["qty"] += qty
                    cart[key]["price"] = round(client_price, 2)
                else:
                    cart[key] = {"qty": qty, "price": round(client_price, 2)}

                session["cart_lab3"] = cart
                flash(f"<strong>{SHOP_PRODUCTS[pid][0]}</strong> berhasil ditambahkan ke keranjang belanja.", "success")
                return redirect("/lab3")

            # Aksi 2: Checkout pesanan
            if action == "checkout":
                items = []
                total = 0.0
                has_target = False

                for key, data in cart.items():
                    pid = int(key)
                    if pid not in SHOP_PRODUCTS:
                        continue
                    item_qty = data.get("qty", 1)
                    item_price = data.get("price", SHOP_PRODUCTS[pid][2])
                    subtotal = round(item_price * item_qty, 2)
                    total += subtotal
                    if pid == 1:
                        has_target = True
                    items.append({
                        "name": SHOP_PRODUCTS[pid][0],
                        "price": item_price,
                        "qty": item_qty,
                        "subtotal": subtotal,
                    })

                total = round(total, 2)
                if not items:
                    flash("Keranjang belanja Anda saat ini masih kosong.", "error")
                    return redirect("/lab3")

                if total > balance:
                    flash(f"Saldo akun (${balance:.2f}) tidak mencukupi untuk menyelesaikan transaksi senilai ${total:.2f}.", "error")
                    return redirect("/lab3")

                session["balance"] = round(balance - total, 2)
                session["cart_lab3"] = {}

                if has_target:
                    session["lab3_solved"] = True
                    flag_3 = get_flag(3)
                    flash(
                        f"Pesanan berhasil dikonfirmasi! Pembelian produk incaran terverifikasi. Token: <span class='flag-box'>{flag_3}</span>",
                        "success",
                    )
                else:
                    flash("Pesanan Anda telah berhasil diproses. Terima kasih telah berbelanja di Nusatech!", "success")
                return redirect("/lab3")

            # Aksi 3: Kosongkan keranjang
            if action == "empty":
                session["cart_lab3"] = {}
                flash("Keranjang belanja telah dikosongkan.", "info")
                return redirect("/lab3")

            # Fallback untuk pengujian langsung (API/test compatibility)
            pid = request.form.get("pid", type=int)
            client_price = request.form.get("price", type=float)
            if pid in SHOP_PRODUCTS and client_price is not None and math.isfinite(client_price):
                if client_price < 0 or client_price > balance:
                    flash("Harga tidak valid atau saldo tidak mencukupi.", "error")
                    return redirect("/lab3")
                session["balance"] = round(balance - client_price, 2)
                if pid == 1:
                    session["lab3_solved"] = True
                    flag_3 = get_flag(3)
                    flash(f"Pesanan berhasil! Kode: <span class='flag-box'>{flag_3}</span>", "success")
                else:
                    flash(f"Berhasil membeli {SHOP_PRODUCTS[pid][0]}.", "success")
                return redirect("/lab3")

        # Tampilan GET Lab 3
        cart_items = []
        total = 0.0
        for key, data in cart.items():
            pid = int(key)
            if pid not in SHOP_PRODUCTS:
                continue
            item_qty = data.get("qty", 1)
            item_price = data.get("price", SHOP_PRODUCTS[pid][2])
            subtotal = round(item_price * item_qty, 2)
            total += subtotal
            cart_items.append({
                "name": SHOP_PRODUCTS[pid][0],
                "price": item_price,
                "qty": item_qty,
                "subtotal": subtotal,
            })
        total = round(total, 2)
        total_qty = sum(item["qty"] for item in cart.values())

        return render_page(
            LAB3_BODY,
            page_title="Penawaran Spesial",
            products=SHOP_PRODUCTS,
            cart_items=cart_items,
            total=total,
            balance=balance,
            cart_count=total_qty,
            svg_map=SVG_ICONS,
        )

    # --------------------------------------------------------------------------
    # Lab 4 - Business Logic: High-Level Logic Vulnerability (Qty Flaw)
    # --------------------------------------------------------------------------
    @app.route("/lab4", methods=["GET", "POST"])
    def lab4():
        balance = ensure_balance()
        cart = ensure_cart_lab4()

        if request.method == "POST":
            action = request.form.get("action", "")

            if action == "add":
                pid = request.form.get("pid", type=int)
                qty = request.form.get("qty", type=int)

                if pid not in SHOP_PRODUCTS or qty is None:
                    flash("Produk atau jumlah barang tidak valid.", "error")
                    return redirect("/lab4")

                key = str(pid)
                cart[key] = cart.get(key, 0) + qty
                if cart[key] == 0:
                    del cart[key]
                session["cart_lab4"] = cart
                flash(f"Jumlah <strong>{SHOP_PRODUCTS[pid][0]}</strong> diperbarui di keranjang belanja.", "success")
                return redirect("/lab4")

            if action == "checkout":
                items = []
                total = 0.0

                for key, qty in cart.items():
                    pid = int(key)
                    if pid not in SHOP_PRODUCTS:
                        continue
                    price = SHOP_PRODUCTS[pid][2]
                    subtotal = round(price * qty, 2)
                    total += subtotal
                    items.append({
                        "name": SHOP_PRODUCTS[pid][0],
                        "price": price,
                        "qty": qty,
                        "subtotal": subtotal,
                    })

                total = round(total, 2)

                # Kondisi eksploitasi: Produk 1 (Drone) qty > 0 DAN 0 <= total <= balance
                if cart.get("1", 0) > 0 and 0.0 <= total <= balance:
                    session["lab4_solved"] = True
                    session["balance"] = round(balance - total, 2)
                    session["cart_lab4"] = {}
                    flag_4 = get_flag(4)
                    flash(
                        f"Pesanan Anda berhasil dikonfirmasi! Pengiriman Drone Elang X200 dijadwalkan. Kode verifikasi pesanan: <span class='flag-box'>{flag_4}</span>",
                        "success",
                    )
                    return redirect("/lab4")
                elif total > balance:
                    flash(f"Saldo akun (${balance:.2f}) tidak mencukupi untuk total tagihan sebesar ${total:.2f}.", "error")
                    return redirect("/lab4")
                else:
                    flash("Pesanan tidak dapat diproses. Keranjang harus memuat produk yang valid dengan total non-negatif.", "error")
                    return redirect("/lab4")

            if action == "empty":
                session["cart_lab4"] = {}
                flash("Keranjang belanja dikosongkan.", "info")
                return redirect("/lab4")

        # Tampilan GET Lab 4
        cart_items = []
        total = 0.0
        for key, qty in cart.items():
            pid = int(key)
            if pid not in SHOP_PRODUCTS:
                continue
            price = SHOP_PRODUCTS[pid][2]
            subtotal = round(price * qty, 2)
            total += subtotal
            cart_items.append({
                "name": SHOP_PRODUCTS[pid][0],
                "price": price,
                "qty": qty,
                "subtotal": subtotal,
            })
        total = round(total, 2)
        total_qty = sum(max(0, qty) for qty in cart.values())

        return render_page(
            LAB4_BODY,
            page_title="Keranjang Belanja",
            products=SHOP_PRODUCTS,
            cart_items=cart_items,
            total=total,
            balance=balance,
            cart_count=total_qty,
            svg_map=SVG_ICONS,
        )

    # --------------------------------------------------------------------------
    # Lab 5 - Inconsistent Security Controls (Email Domain Flaw)
    # --------------------------------------------------------------------------
    @app.route("/lab5")
    def lab5():
        member = current_member()
        return render_page(
            LAB5_BODY,
            page_title="Akun Saya",
            member=member,
        )

    @app.route("/lab5/register", methods=["POST"])
    def lab5_register():
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("Semua kolom pendaftaran wajib diisi.", "error")
            return redirect("/lab5")

        # Cek restriksi domain pada form registrasi
        if email.lower().endswith("@nusatech.internal"):
            flash(
                "Pendaftaran dengan domain internal @nusatech.internal dibatasi untuk staf resmi dan memerlukan verifikasi khusus oleh tim IT.",
                "error",
            )
            return redirect("/lab5")

        db = get_db()
        try:
            db.execute(
                "INSERT INTO members (username, password_hash, email) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), email),
            )
            db.commit()
            flash("Pendaftaran akun berhasil! Silakan masuk dengan kredensial baru Anda.", "success")
        except sqlite3.IntegrityError:
            flash("Nama pengguna sudah digunakan oleh anggota lain. Silakan pilih nama lain.", "error")

        return redirect("/lab5")

    @app.route("/lab5/login", methods=["POST"])
    def lab5_login():
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        row = get_db().execute(
            "SELECT * FROM members WHERE username = ?", (username,)
        ).fetchone()

        if row and check_password_hash(row["password_hash"], password):
            session["member_user"] = row["username"]
            flash(f"Selamat datang kembali, <strong>{row['username']}</strong>!", "success")
        else:
            flash("Nama pengguna atau kata sandi tidak cocok. Silakan coba lagi.", "error")

        return redirect("/lab5")

    @app.route("/lab5/update-email", methods=["POST"])
    def lab5_update_email():
        member = current_member()
        if not member:
            flash("Silakan masuk terlebih dahulu untuk memperbarui data akun.", "error")
            return redirect("/lab5")

        email = request.form.get("email", "").strip()
        if not email or "@" not in email:
            flash("Format alamat email yang dimasukkan tidak valid.", "error")
            return redirect("/lab5")

        # Celah: form update email TIDAK memvalidasi domain internal!
        db = get_db()
        db.execute(
            "UPDATE members SET email = ? WHERE id = ?",
            (email, member["id"]),
        )
        db.commit()
        flash("Alamat email berhasil diperbarui.", "success")
        return redirect("/lab5")

    @app.route("/lab5/internal")
    def lab5_internal():
        member = current_member()
        if not member:
            abort(403)

        # Hanya email berdomain @nusatech.internal yang diizinkan mengakses panel staf
        if member["email"].lower().endswith("@nusatech.internal"):
            session["lab5_solved"] = True
            flag_5 = get_flag(5)
            return render_page(
                LAB5_INTERNAL_BODY,
                page_title="Portal Staf Internal",
                member=member,
                flag=flag_5,
            )

        abort(403)

    # --------------------------------------------------------------------------
    # Lab 6 - Flawed Enforcement of Business Rules (Alternating Promo Code)
    # --------------------------------------------------------------------------
    @app.route("/lab6")
    def lab6():
        price = ensure_lab6_price()
        balance = ensure_balance()
        return render_page(
            LAB6_BODY,
            page_title="Checkout Promo",
            price=price,
            balance=balance,
        )

    @app.route("/lab6/coupon", methods=["POST"])
    def lab6_coupon():
        price = ensure_lab6_price()
        code = request.form.get("code", "").strip().upper()
        last_code = session.get("lab6_last_coupon")

        if not code:
            flash("Kode kupon promosi tidak boleh kosong.", "error")
        elif code == last_code:
            flash("Kode promosi yang sama tidak dapat digunakan dua kali berturut-turut.", "error")
        elif code == "HEMAT50":
            session["lab6_price"] = round(max(0.0, price - 50.0), 2)
            session["lab6_last_coupon"] = code
            flash("Kupon <strong>HEMAT50</strong> berhasil diterapkan: Potongan langsung $50.00.", "success")
        elif code == "DISKON30":
            session["lab6_price"] = round(price * 0.7, 2)
            session["lab6_last_coupon"] = code
            flash("Kupon <strong>DISKON30</strong> berhasil diterapkan: Diskon 30% dari harga saat ini.", "success")
        else:
            flash("Kode promo tidak terdaftar atau masa berlakunya telah berakhir.", "error")

        return redirect("/lab6")

    @app.route("/lab6/checkout", methods=["POST"])
    def lab6_checkout():
        price = ensure_lab6_price()
        balance = ensure_balance()

        if price <= balance:
            session["lab6_solved"] = True
            flag_6 = get_flag(6)
            flash(
                f"Selamat! Pesanan Drone Elang X200 berhasil dibayar dengan total harga promosi ${price:.2f}. Kode konfirmasi pesanan: <span class='flag-box'>{flag_6}</span>",
                "success",
            )
        else:
            flash(
                f"Harga saat ini (${price:.2f}) masih melebihi batas saldo akun Anda (${balance:.2f}). Silakan gunakan kupon promosi yang tersedia.",
                "error",
            )

        return redirect("/lab6")

    # --------------------------------------------------------------------------
    # Error Handlers
    # --------------------------------------------------------------------------
    @app.errorhandler(404)
    def handle_not_found(e):
        return render_page(NOT_FOUND_BODY, page_title="Halaman Tidak Ditemukan"), 404

    @app.errorhandler(403)
    def handle_forbidden(e):
        return render_page(FORBIDDEN_BODY, page_title="Akses Dibatasi"), 403

    return app


# Objek aplikasi WSGI untuk gunicorn
app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
