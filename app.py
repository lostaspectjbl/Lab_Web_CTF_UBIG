import math
import os
import sqlite3

from flask import (
    Blueprint,
    Flask,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template_string,
    request,
    session,
)
from markupsafe import Markup
from werkzeug.security import check_password_hash, generate_password_hash

SHOP = {
    1: ("Lightweight l33t Leather Jacket", 1337.0),
    2: ("Gift Card", 10.0),
    3: ("Eco Mug", 20.0),
}
CREDIT = 100.0

bp = Blueprint("main", __name__)


BASE_TEMPLATE = """
<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} &middot; CTF Labs</title>
<style>
:root {
  color-scheme: dark;
  --bg: #0b1020;
  --panel: #121a30;
  --panel2: #0e1528;
  --text: #e6edf7;
  --muted: #93a4c3;
  --accent: #5eead4;
  --accent2: #818cf8;
  --danger: #fb7185;
  --ok: #34d399;
  --border: #22304f;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  background: radial-gradient(1200px 600px at 10% -10%, #1b2a4a 0, transparent 60%), var(--bg);
  color: var(--text);
  min-height: 100vh;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
header {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border);
  background: rgba(9, 14, 28, .82);
  backdrop-filter: blur(8px);
  position: sticky;
  top: 0;
  z-index: 5;
}
.brand { font-weight: 800; letter-spacing: .04em; }
.brand span { color: var(--accent); }
nav { display: flex; flex-wrap: wrap; gap: .4rem; }
nav a {
  padding: .45rem .7rem;
  border-radius: .55rem;
  border: 1px solid transparent;
  color: var(--muted);
  font-size: .92rem;
}
nav a:hover { color: var(--text); background: var(--panel); border-color: var(--border); text-decoration: none; }
main { max-width: 980px; margin: 2rem auto 4rem; padding: 0 1.25rem; }
h1 { font-size: clamp(1.6rem, 4vw, 2.4rem); margin: .2rem 0 .4rem; }
h2 { margin-top: 0; }
p { line-height: 1.65; color: var(--muted); }
.panel {
  background: linear-gradient(180deg, var(--panel), var(--panel2));
  border: 1px solid var(--border);
  border-radius: 1rem;
  padding: 1.25rem;
  box-shadow: 0 18px 50px rgba(0, 0, 0, .25);
}
.grid { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }
.card {
  background: var(--panel2);
  border: 1px solid var(--border);
  border-radius: .85rem;
  padding: 1rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: .5rem;
}
.card h3 { margin: 0; font-size: 1.05rem; }
.card p { margin: 0; font-size: .9rem; }
.tag {
  display: inline-block;
  font-size: .72rem;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: var(--accent);
  border: 1px solid rgba(94, 234, 212, .35);
  background: rgba(94, 234, 212, .08);
  padding: .18rem .45rem;
  border-radius: 999px;
  width: max-content;
}
label { display: block; font-size: .88rem; color: var(--muted); margin-bottom: .3rem; }
input, select, button { font: inherit; }
input, select {
  width: 100%;
  padding: .65rem .75rem;
  border-radius: .6rem;
  border: 1px solid var(--border);
  background: #0a1224;
  color: var(--text);
  margin-bottom: .8rem;
}
button, .btn {
  display: inline-block;
  border: 0;
  border-radius: .6rem;
  padding: .65rem .95rem;
  font-weight: 700;
  cursor: pointer;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  color: #07111f;
}
button:hover { filter: brightness(1.08); }
.btn.secondary { background: transparent; color: var(--text); border: 1px solid var(--border); }
table { width: 100%; border-collapse: collapse; margin: .5rem 0 1rem; font-size: .92rem; }
th, td { text-align: left; padding: .65rem .5rem; border-bottom: 1px solid var(--border); vertical-align: top; }
th { color: var(--muted); font-weight: 600; font-size: .8rem; text-transform: uppercase; letter-spacing: .05em; }
.flag {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  background: rgba(52, 211, 153, .1);
  border: 1px dashed rgba(52, 211, 153, .55);
  color: var(--ok);
  padding: .75rem .9rem;
  border-radius: .6rem;
  word-break: break-all;
}
.flashes { display: grid; gap: .5rem; margin-bottom: 1rem; }
.flash { padding: .7rem .85rem; border-radius: .6rem; border: 1px solid var(--border); background: var(--panel); }
.flash.success { border-color: rgba(52, 211, 153, .5); color: var(--ok); }
.flash.error { border-color: rgba(251, 113, 133, .5); color: var(--danger); }
.flash.info { border-color: rgba(129, 140, 248, .5); color: #c7d2fe; }
.muted { color: var(--muted); }
.row { display: flex; flex-wrap: wrap; gap: .6rem; align-items: end; }
.row > * { flex: 1 1 160px; }
.row button { flex: 0 0 auto; }
footer { text-align: center; color: #64748b; font-size: .8rem; padding: 2rem 1rem; }
code {
  background: #0a1224;
  border: 1px solid var(--border);
  padding: .12rem .35rem;
  border-radius: .35rem;
  font-family: ui-monospace, monospace;
  font-size: .85em;
}
@media (max-width: 600px) {
  header { align-items: flex-start; }
  main { margin-top: 1.25rem; }
}
</style>
</head>
<body>
<header>
  <div class="brand">CTF<span>Labs</span></div>
  <nav>
  {% if config['LAB'] %}
    <a href="/lab{{ config['LAB'] }}">Lab {{ config['LAB'] }}</a>
  {% else %}
    <a href="/">Beranda</a>
    {% for n in range(1, 7) %}<a href="/lab{{ n }}">Lab {{ n }}</a>{% endfor %}
  {% endif %}
    <a href="/reset">Reset</a>
  </nav>
</header>
<main>
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
      <div class="flashes">
      {% for category, message in messages %}
        <div class="flash {{ category }}">{{ message }}</div>
      {% endfor %}
      </div>
    {% endif %}
  {% endwith %}
  {{ body }}
</main>
<footer>Lab ini sengaja rentan. Gunakan hanya di lingkungan latihan.</footer>
</body>
</html>
"""


INDEX_BODY = """
<div class="panel">
  <p class="tag">Platform Latihan</p>
  <h1>Enam lab web security</h1>
  <p>
    Setiap lab punya celah yang disengaja. Tujuannya bukan menebak flag,
    tetapi memahami kenapa celah itu muncul dan bagaimana memperbaikinya.
    Buka satu lab, ikuti petunjuknya, lalu reset sesi bila ingin mengulang.
  </p>
</div>

<div class="grid" style="margin-top: 1rem;">
  <div class="card">
    <p class="tag">Lab 1</p>
    <h3>Toko Hadiah</h3>
    <p>Filter kategori pada katalog toko. Ada barang yang belum dirilis.</p>
    <a class="btn" href="/lab1">Masuk Lab 1</a>
  </div>
  <div class="card">
    <p class="tag">Lab 2</p>
    <h3>Login Administrator</h3>
    <p>Form login lama dengan pemeriksaan akun yang kurang ketat.</p>
    <a class="btn" href="/lab2">Masuk Lab 2</a>
  </div>
  <div class="card">
    <p class="tag">Lab 3</p>
    <h3>Harga dari Klien</h3>
    <p>Toko percaya pada harga yang dikirim oleh browser.</p>
    <a class="btn" href="/lab3">Masuk Lab 3</a>
  </div>
  <div class="card">
    <p class="tag">Lab 4</p>
    <h3>Keranjang Ajaib</h3>
    <p>Keranjang belanja dengan aturan jumlah yang longgar.</p>
    <a class="btn" href="/lab4">Masuk Lab 4</a>
  </div>
  <div class="card">
    <p class="tag">Lab 5</p>
    <h3>Email Perusahaan</h3>
    <p>Panel admin hanya untuk domain perusahaan. Benarkah?</p>
    <a class="btn" href="/lab5">Masuk Lab 5</a>
  </div>
  <div class="card">
    <p class="tag">Lab 6</p>
    <h3>Kupon Beruntun</h3>
    <p>Diskon bertumpuk dengan satu aturan yang mudah dilewati.</p>
    <a class="btn" href="/lab6">Masuk Lab 6</a>
  </div>
</div>
"""


LAB1_BODY = """
<div class="panel">
  <p class="tag">Lab 1 &middot; SQL Injection</p>
  <h1>Toko Hadiah</h1>
  <p>
    Katalog ini menyaring produk berdasarkan kategori. Barang yang belum
    dirilis seharusnya tidak pernah tampil untuk pengunjung biasa.
  </p>
  <form method="get" action="/lab1" class="row">
    <div>
      <label for="category">Kategori</label>
      <input id="category" name="category" value="{{ category }}" placeholder="Gifts">
    </div>
    <button type="submit">Cari</button>
  </form>
  {% if error %}<div class="flash error">{{ error }}</div>{% endif %}
  {% if products %}
  <table>
    <thead><tr><th>Produk</th><th>Harga</th><th>Deskripsi</th></tr></thead>
    <tbody>
    {% for product in products %}
      <tr>
        <td>{{ product['name'] }}</td>
        <td>${{ "%.2f"|format(product['price']) }}</td>
        <td>{{ product['description'] }}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p class="muted">Tidak ada produk yang cocok.</p>
  {% endif %}
</div>
"""


LAB2_BODY = """
<div class="panel">
  <p class="tag">Lab 2 &middot; SQL Injection Login</p>
  <h1>Login Administrator</h1>
  <p>
    Halaman ini hanya menampilkan flag bila kamu masuk sebagai
    <code>administrator</code>. Akun lain akan ditolak.
  </p>
  <form method="post" action="/lab2">
    <label for="username">Username</label>
    <input id="username" name="username" autocomplete="off" placeholder="username">
    <label for="password">Password</label>
    <input id="password" name="password" type="password" autocomplete="off" placeholder="password">
    <button type="submit">Masuk</button>
  </form>
  {% if message %}<div class="flash {{ 'success' if flag else 'error' }}">{{ message }}</div>{% endif %}
  {% if flag %}<div class="flag">{{ flag }}</div>{% endif %}
</div>
"""


LAB3_BODY = """
<div class="panel">
  <p class="tag">Lab 3 &middot; Business Logic</p>
  <h1>Harga dari Klien</h1>
  <p>
    Saldo awal kamu adalah <strong>${{ "%.2f"|format(balance) }}</strong>.
    Beli jaket edisi terbatas untuk mendapatkan flag.
  </p>
  <table>
    <thead><tr><th>Produk</th><th>Harga</th><th>Aksi</th></tr></thead>
    <tbody>
    {% for pid, product in shop.items() %}
      <tr>
        <td>{{ product[0] }}</td>
        <td>${{ "%.2f"|format(product[1]) }}</td>
        <td>
          <form method="post" action="/lab3" class="row" style="margin: 0;">
            <input type="hidden" name="pid" value="{{ pid }}">
            <input type="hidden" name="price" value="{{ '%.2f'|format(product[1]) }}">
            <button type="submit">Beli</button>
          </form>
        </td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
</div>
"""


LAB4_BODY = """
<div class="panel">
  <p class="tag">Lab 4 &middot; Business Logic</p>
  <h1>Keranjang Ajaib</h1>
  <p>
    Kredit belanja kamu <strong>${{ "%.2f"|format(credit) }}</strong>.
    Checkout akan berhasil bila keranjang berisi jaket dan totalnya tidak
    melebihi kredit.
  </p>

  {% if items %}
  <table>
    <thead><tr><th>Produk</th><th>Harga</th><th>Jumlah</th><th>Subtotal</th></tr></thead>
    <tbody>
    {% for item in items %}
      <tr>
        <td>{{ item.name }}</td>
        <td>${{ "%.2f"|format(item.price) }}</td>
        <td>{{ item.qty }}</td>
        <td>${{ "%.2f"|format(item.subtotal) }}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
  <p>Total: <strong>${{ "%.2f"|format(total) }}</strong></p>
  <form method="post" action="/lab4">
    <input type="hidden" name="action" value="checkout">
    <button type="submit">Checkout</button>
  </form>
  {% else %}
  <p class="muted">Keranjang masih kosong.</p>
  {% endif %}

  <h2 style="margin-top: 1.5rem;">Tambah produk</h2>
  {% for pid, product in shop.items() %}
  <form method="post" action="/lab4" class="row">
    <div>
      <label>{{ product[0] }} (${{ "%.2f"|format(product[1]) }})</label>
    </div>
    <div>
      <label for="qty-{{ pid }}">Jumlah</label>
      <input id="qty-{{ pid }}" type="number" name="qty" value="1">
    </div>
    <input type="hidden" name="action" value="add">
    <input type="hidden" name="pid" value="{{ pid }}">
    <button type="submit">Tambah</button>
  </form>
  {% endfor %}
</div>
"""


LAB5_BODY = """
<div class="panel">
  <p class="tag">Lab 5 &middot; Broken Access Control</p>
  <h1>Email Perusahaan</h1>
  <p>
    Panel admin hanya boleh diakses oleh anggota dengan email
    <code>@ctf-corp.com</code>. Pendaftaran email perusahaan diblokir.
  </p>

  {% if member %}
    <p>Login sebagai <strong>{{ member['username'] }}</strong> ({{ member['email'] }}).</p>
    <form method="post" action="/lab5/update-email">
      <label for="email">Email baru</label>
      <input id="email" name="email" value="{{ member['email'] }}">
      <button type="submit">Simpan Email</button>
    </form>
    <p><a class="btn secondary" href="/lab5/admin">Buka Panel Admin</a></p>
  {% else %}
    <div class="grid">
      <div class="card">
        <h3>Login</h3>
        <form method="post" action="/lab5/login">
          <label for="login-username">Username</label>
          <input id="login-username" name="username" autocomplete="off">
          <label for="login-password">Password</label>
          <input id="login-password" name="password" type="password" autocomplete="off">
          <button type="submit">Masuk</button>
        </form>
      </div>
      <div class="card">
        <h3>Daftar</h3>
        <form method="post" action="/lab5/register">
          <label for="reg-username">Username</label>
          <input id="reg-username" name="username" autocomplete="off">
          <label for="reg-password">Password</label>
          <input id="reg-password" name="password" type="password" autocomplete="off">
          <label for="reg-email">Email</label>
          <input id="reg-email" name="email" type="email" autocomplete="off">
          <button type="submit">Daftar</button>
        </form>
      </div>
    </div>
  {% endif %}
</div>
"""


LAB5_ADMIN_BODY = """
<div class="panel">
  <p class="tag">Lab 5 &middot; Panel Admin</p>
  <h1>Panel Admin</h1>
  <p>Selamat, email <strong>{{ email }}</strong> diterima oleh panel.</p>
  <div class="flag">{{ flag }}</div>
</div>
"""


LAB6_BODY = """
<div class="panel">
  <p class="tag">Lab 6 &middot; Business Logic</p>
  <h1>Kupon Beruntun</h1>
  <p>
    Harga jaket saat ini <strong>${{ "%.2f"|format(price) }}</strong>.
    Kredit kamu <strong>${{ "%.2f"|format(credit) }}</strong>.
    Checkout berhasil bila harga tidak melebihi kredit.
  </p>
  <p class="muted">
    Kupon yang tersedia: <code>NEWCUST5</code> (potongan $5) dan
    <code>SIGNUP30</code> (diskon 30%). Kupon yang sama tidak dapat dipakai
    dua kali berturut-turut.
  </p>
  <form method="post" action="/lab6/coupon" class="row">
    <div>
      <label for="code">Kode kupon</label>
      <input id="code" name="code" autocomplete="off" placeholder="NEWCUST5">
    </div>
    <button type="submit">Pakai Kupon</button>
  </form>
  <form method="post" action="/lab6/checkout">
    <button type="submit">Checkout</button>
  </form>
</div>
"""


NOT_FOUND_BODY = """
<div class="panel">
  <p class="tag">404</p>
  <h1>Halaman tidak ditemukan</h1>
  <p>Alamat yang kamu buka tidak tersedia di lab ini.</p>
  <a class="btn" href="/">Kembali</a>
</div>
"""


FORBIDDEN_BODY = """
<div class="panel">
  <p class="tag">403</p>
  <h1>Akses ditolak</h1>
  <p>Kamu tidak memenuhi syarat untuk membuka halaman ini.</p>
  <a class="btn" href="/">Kembali</a>
</div>
"""


def page(title, body_template, **context):
    body = render_template_string(body_template, **context)
    return render_template_string(BASE_TEMPLATE, body=Markup(body), title=title)


def get_flag(number):
    return current_app.config["FLAGS"][number]


def get_db():
    if "db" not in g:
        db = sqlite3.connect(current_app.config["DB_PATH"])
        db.row_factory = sqlite3.Row
        g.db = db
    return g.db


def ensure_balance():
    if "balance" not in session:
        session["balance"] = CREDIT
    return float(session["balance"])


def ensure_cart():
    if "cart" not in session:
        session["cart"] = {}
    return dict(session["cart"])


def ensure_lab6():
    if "lab6_price" not in session:
        session["lab6_price"] = 1337.0
    if "lab6_last_coupon" not in session:
        session["lab6_last_coupon"] = None
    return float(session["lab6_price"])


def current_member():
    username = session.get("member")
    if not username:
        return None
    return get_db().execute(
        "SELECT username, password_hash, email FROM members WHERE username = ?",
        (username,),
    ).fetchone()


def init_db(path, flags):
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    if os.path.exists(path):
        os.remove(path)

    db = sqlite3.connect(path)
    try:
        db.executescript(
            """
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT NOT NULL,
                released INTEGER NOT NULL
            );
            CREATE TABLE users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            );
            CREATE TABLE members (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                email TEXT NOT NULL
            );
            """
        )
        db.executemany(
            "INSERT INTO products (name, category, price, description, released) VALUES (?, ?, ?, ?, ?)",
            [
                ("Gift Card", "Gifts", 10.0, "Kartu hadiah digital untuk teman.", 1),
                ("Plush Fox", "Pets", 25.0, "Boneka rubah yang lembut.", 1),
                ("Mechanical Keyboard", "Tech", 90.0, "Keyboard mekanik dengan switch biru.", 1),
                (
                    "Prototype Gadget",
                    "Gifts",
                    0.0,
                    "Barang rahasia yang belum dirilis. " + flags[1],
                    0,
                ),
            ],
        )
        db.executemany(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            [
                ("administrator", os.urandom(8).hex()),
                ("wiener", "peter"),
                ("peter", "peter"),
            ],
        )
        db.execute(
            "INSERT INTO members (username, password_hash, email) VALUES (?, ?, ?)",
            (
                "admin",
                generate_password_hash(os.urandom(8).hex()),
                "admin@ctf-corp.com",
            ),
        )
        db.commit()
    finally:
        db.close()


@bp.before_request
def restrict_to_active_lab():
    lab = current_app.config["LAB"]
    if not lab:
        return None
    path = request.path
    if path == "/" or path == "/reset":
        return None
    if path == f"/lab{lab}" or path.startswith(f"/lab{lab}/"):
        return None
    abort(404)


@bp.route("/")
def index():
    lab = current_app.config["LAB"]
    if lab:
        return redirect(f"/lab{lab}")
    return page("Beranda", INDEX_BODY)


@bp.route("/reset", methods=["GET", "POST"])
def reset():
    session.clear()
    flash("Sesi dan keranjang telah direset.", "info")
    lab = current_app.config["LAB"]
    return redirect(f"/lab{lab}" if lab else "/")


@bp.route("/lab1")
def lab1():
    products = []
    error = None
    category = request.args.get("category", "")
    try:
        if "category" in request.args:
            query = (
                "SELECT name, price, description FROM products "
                f"WHERE category='{category}' AND released=1"
            )
        else:
            query = "SELECT name, price, description FROM products WHERE released=1"
        products = get_db().execute(query).fetchall()
    except sqlite3.Error:
        error = "Terjadi kesalahan."
        products = []
    return page("Lab 1", LAB1_BODY, products=products, error=error, category=category)


@bp.route("/lab2", methods=["GET", "POST"])
def lab2():
    flag = None
    message = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        query = (
            "SELECT username FROM users "
            f"WHERE username='{username}' AND password='{password}'"
        )
        try:
            row = get_db().execute(query).fetchone()
        except sqlite3.Error:
            row = None
            message = "Terjadi kesalahan."
        else:
            if row and row["username"] == "administrator":
                flag = get_flag(2)
                message = "Login sebagai administrator berhasil."
            elif row:
                message = (
                    f"Login berhasil sebagai {row['username']}, "
                    "tetapi halaman ini hanya untuk administrator."
                )
            else:
                message = "Username atau password salah."
    return page("Lab 2", LAB2_BODY, flag=flag, message=message)


@bp.route("/lab3", methods=["GET", "POST"])
def lab3():
    balance = ensure_balance()
    if request.method == "POST":
        pid = request.form.get("pid", type=int)
        price = request.form.get("price", type=float)
        if pid not in SHOP or price is None or not math.isfinite(price):
            flash("Permintaan tidak valid.", "error")
            return redirect("/lab3")
        if price < 0 or price > balance:
            flash("Harga tidak valid atau saldo tidak cukup.", "error")
            return redirect("/lab3")
        session["balance"] = round(balance - price, 2)
        if pid == 1:
            flash(get_flag(3), "success")
        else:
            flash(f"Berhasil membeli {SHOP[pid][0]}.", "success")
        return redirect("/lab3")
    return page("Lab 3", LAB3_BODY, balance=balance, shop=SHOP)


@bp.route("/lab4", methods=["GET", "POST"])
def lab4():
    cart = ensure_cart()
    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "add":
            pid = request.form.get("pid", type=int)
            qty = request.form.get("qty", type=int)
            if pid not in SHOP or qty is None:
                flash("Produk atau jumlah tidak valid.", "error")
                return redirect("/lab4")
            key = str(pid)
            cart[key] = cart.get(key, 0) + qty
            if cart[key] == 0:
                del cart[key]
            session["cart"] = cart
            flash(f"{SHOP[pid][0]} ditambahkan ke keranjang.", "success")
            return redirect("/lab4")
        if action == "checkout":
            items = []
            total = 0.0
            for key, qty in cart.items():
                pid = int(key)
                if pid not in SHOP:
                    continue
                name, unit_price = SHOP[pid]
                subtotal = round(unit_price * qty, 2)
                total += subtotal
                items.append(
                    {"name": name, "price": unit_price, "qty": qty, "subtotal": subtotal}
                )
            total = round(total, 2)
            if cart.get("1", 0) > 0 and 0 <= total <= CREDIT:
                flash(get_flag(4), "success")
                session["cart"] = {}
                return redirect("/lab4")
            flash(
                f"Checkout ditolak. Total ${total:.2f}, kredit ${CREDIT:.2f}.",
                "error",
            )
            return redirect("/lab4")

    items = []
    total = 0.0
    for key, qty in cart.items():
        pid = int(key)
        if pid not in SHOP:
            continue
        name, unit_price = SHOP[pid]
        subtotal = round(unit_price * qty, 2)
        total += subtotal
        items.append(
            {"name": name, "price": unit_price, "qty": qty, "subtotal": subtotal}
        )
    return page(
        "Lab 4",
        LAB4_BODY,
        items=items,
        total=round(total, 2),
        credit=CREDIT,
        shop=SHOP,
    )


@bp.route("/lab5")
def lab5():
    member = current_member()
    return page("Lab 5", LAB5_BODY, member=member)


@bp.route("/lab5/register", methods=["POST"])
def lab5_register():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    email = request.form.get("email", "").strip()
    if not username or not password or not email:
        flash("Username, password, dan email wajib diisi.", "error")
    elif email.lower().endswith("@ctf-corp.com"):
        flash("Email perusahaan tidak boleh dipakai untuk mendaftar.", "error")
    else:
        try:
            db = get_db()
            db.execute(
                "INSERT INTO members (username, password_hash, email) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), email),
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash("Username sudah dipakai.", "error")
        else:
            flash("Pendaftaran berhasil. Silakan login.", "success")
    return redirect("/lab5")


@bp.route("/lab5/login", methods=["POST"])
def lab5_login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    row = get_db().execute(
        "SELECT username, password_hash, email FROM members WHERE username = ?",
        (username,),
    ).fetchone()
    if row and check_password_hash(row["password_hash"], password):
        session["member"] = row["username"]
        flash("Login berhasil.", "success")
    else:
        flash("Username atau password salah.", "error")
    return redirect("/lab5")


@bp.route("/lab5/update-email", methods=["POST"])
def lab5_update_email():
    member = current_member()
    if not member:
        flash("Silakan login terlebih dahulu.", "error")
        return redirect("/lab5")
    email = request.form.get("email", "").strip()
    if not email:
        flash("Email tidak boleh kosong.", "error")
    else:
        db = get_db()
        db.execute(
            "UPDATE members SET email = ? WHERE username = ?",
            (email, member["username"]),
        )
        db.commit()
        flash("Email berhasil diperbarui.", "success")
    return redirect("/lab5")


@bp.route("/lab5/admin")
def lab5_admin():
    member = current_member()
    if not member:
        abort(403)
    if member["email"].lower().endswith("@ctf-corp.com"):
        return page(
            "Lab 5 Admin",
            LAB5_ADMIN_BODY,
            flag=get_flag(5),
            email=member["email"],
        )
    abort(403)


@bp.route("/lab6")
def lab6():
    price = ensure_lab6()
    return page("Lab 6", LAB6_BODY, price=price, credit=CREDIT)


@bp.route("/lab6/coupon", methods=["POST"])
def lab6_coupon():
    ensure_lab6()
    code = request.form.get("code", "").strip().upper()
    last_coupon = session.get("lab6_last_coupon")
    if not code:
        flash("Kode kupon tidak boleh kosong.", "error")
    elif code == last_coupon:
        flash("Kupon yang sama tidak bisa dipakai dua kali berturut-turut.", "error")
    elif code == "NEWCUST5":
        session["lab6_price"] = round(max(0.0, float(session["lab6_price"]) - 5.0), 2)
        session["lab6_last_coupon"] = code
        flash("Kupon NEWCUST5 diterapkan: potongan $5.", "success")
    elif code == "SIGNUP30":
        session["lab6_price"] = round(float(session["lab6_price"]) * 0.7, 2)
        session["lab6_last_coupon"] = code
        flash("Kupon SIGNUP30 diterapkan: diskon 30%.", "success")
    else:
        flash("Kode kupon tidak dikenal.", "error")
    return redirect("/lab6")


@bp.route("/lab6/checkout", methods=["POST"])
def lab6_checkout():
    price = ensure_lab6()
    if price <= CREDIT:
        flash(get_flag(6), "success")
    else:
        flash(
            f"Harga masih ${price:.2f}, kredit kamu ${CREDIT:.2f}.",
            "error",
        )
    return redirect("/lab6")


def create_app():
    lab = os.environ.get("LAB", "").strip()
    if lab and lab not in {str(number) for number in range(1, 7)}:
        raise ValueError("LAB harus bernilai 1-6 atau kosong.")

    app = Flask(__name__)
    app.secret_key = os.environ.get(f"SECRET_KEY_{lab}") or os.environ.get(
        "SECRET_KEY", "dev-only-insecure-secret"
    )
    app.config["LAB"] = lab
    app.config["FLAGS"] = {
        number: os.environ.get(f"FLAG_{number}", f"CTF{{dev_only_lab_{number}}}")
        for number in range(1, 7)
    }
    app.config["DB_PATH"] = os.environ.get("DB_PATH", "/tmp/lab.db")

    init_db(app.config["DB_PATH"], app.config["FLAGS"])
    app.register_blueprint(bp)

    @app.teardown_appcontext
    def close_db(exception):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.errorhandler(404)
    def not_found(error):
        return page("404", NOT_FOUND_BODY), 404

    @app.errorhandler(403)
    def forbidden(error):
        return page("403", FORBIDDEN_BODY), 403

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
