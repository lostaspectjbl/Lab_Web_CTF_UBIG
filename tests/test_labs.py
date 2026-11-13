import os
import tempfile

import pytest

os.environ["DB_PATH"] = os.path.join(
    tempfile.mkdtemp(prefix="ctf-labs-test-"), "bootstrap.db"
)
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ.pop("LAB", None)
for number in range(1, 7):
    os.environ[f"FLAG_{number}"] = f"CTF{{test_flag_{number}}}"

from app import create_app  # noqa: E402


def flag(number):
    return f"CTF{{test_flag_{number}}}"


def assert_has_flag(response, number):
    assert flag(number) in response.get_data(as_text=True)


def assert_no_flag(response, number):
    assert flag(number) not in response.get_data(as_text=True)


@pytest.fixture
def make_client(tmp_path, monkeypatch):
    def _make(lab=None, name="lab.db"):
        monkeypatch.setenv("DB_PATH", str(tmp_path / name))
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


def test_index_lists_all_labs(client):
    response = client.get("/")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    for number in range(1, 7):
        assert f"/lab{number}" in body


def test_lab1_sqli_exploit(client):
    response = client.get(
        "/lab1", query_string={"category": "Gifts' OR 1=1--"}
    )
    assert response.status_code == 200
    assert_has_flag(response, 1)


def test_lab1_normal_category_hides_flag(client):
    response = client.get("/lab1", query_string={"category": "Gifts"})
    assert response.status_code == 200
    assert_no_flag(response, 1)


def test_lab1_homepage_shows_pokemon_cards(client):
    res = client.get("/lab1")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Charizard" in html
    assert "Pikachu" in html
    assert "Vintage &amp; Base Set" in html
    assert "/static/img/pokemon/charizard.jpg" in html


def test_lab2_sqli_login_exploit(client):
    # Step 1: Login bypass SQL Injection
    login_res = client.post(
        "/lab2", data={"username": "administrator'--", "password": "x"}, follow_redirects=True
    )
    assert login_res.status_code == 200
    assert "Panel Administrator" in login_res.get_data(as_text=True)
    # Flag belum muncul hanya dengan login
    assert_no_flag(login_res, 2)

    # Step 2: Administrator mengubah nilai rapor siswa (id=1, Budi Santoso) dari 45 ke 85
    update_res = client.post(
        "/lab2/update-grade", data={"student_id": "1", "grade": "85"}, follow_redirects=True
    )
    assert update_res.status_code == 200
    assert_has_flag(update_res, 2)
    assert "Tuntas" in update_res.get_data(as_text=True)


def test_lab2_normal_login_does_not_show_flag(client):
    response = client.post(
        "/lab2", data={"username": "wiener", "password": "peter"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert "hanya untuk administrator" in response.get_data(as_text=True)
    assert_no_flag(response, 2)


def test_lab2_logout_redirects_to_lab2(client):
    # Login sebagai wiener
    client.post("/lab2", data={"username": "wiener", "password": "peter"}, follow_redirects=True)
    # Logout harus redirect kembali ke /lab2, bukan dashboard utama /
    res_logout = client.get("/lab2/logout", follow_redirects=False)
    assert res_logout.status_code == 302
    assert res_logout.headers["Location"] == "/lab2"

    # Follow redirect dan pastikan form login muncul kembali
    res_page = client.get("/lab2/logout", follow_redirects=True)
    body = res_page.get_data(as_text=True)
    assert "Sistem Informasi E-Rapor Akademik" in body
    assert "Masuk ke Portal" in body
    assert "wiener" in body or "Masuk ke Portal" in body


def test_lab2_unauthorized_grade_update_blocked(client):
    # Akses update nilai tanpa login
    res_anon = client.post("/lab2/update-grade", data={"student_id": "1", "grade": "90"}, follow_redirects=True)
    assert_no_flag(res_anon, 2)
    # Login sebagai wiener lalu coba ubah nilai
    client.post("/lab2", data={"username": "wiener", "password": "peter"})
    res_guru = client.post("/lab2/update-grade", data={"student_id": "1", "grade": "90"}, follow_redirects=True)
    assert_no_flag(res_guru, 2)


def test_lab3_price_tampering_exploit(client):
    # Login dulu
    client.post("/lab3/login", data={"username": "wiener", "password": "peter"})
    response = client.post(
        "/lab3", data={"pid": "1", "price": "1"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert_has_flag(response, 3)


def test_lab3_full_price_is_rejected(client):
    # Login dulu
    client.post("/lab3/login", data={"username": "wiener", "password": "peter"})
    response = client.post(
        "/lab3", data={"pid": "1", "price": "1337"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert_no_flag(response, 3)


def test_lab3_cart_workflow_exploit(client):
    # Login dulu
    client.post("/lab3/login", data={"username": "wiener", "password": "peter"})
    client.post("/lab3", data={"action": "add", "pid": "1", "price": "0.50", "qty": "1"})
    client.post("/lab3", data={"action": "add", "pid": "8", "price": "4.99", "qty": "2"})
    cart_page = client.get("/lab3")
    body = cart_page.get_data(as_text=True)
    assert "Keranjang Belanja" in body
    response = client.post("/lab3", data={"action": "checkout"}, follow_redirects=True)
    assert response.status_code == 200
    assert_has_flag(response, 3)


def test_lab3_cart_empty_action(client):
    # Login dulu
    client.post("/lab3/login", data={"username": "wiener", "password": "peter"})
    client.post("/lab3", data={"action": "add", "pid": "1", "price": "1.00", "qty": "1"})
    client.post("/lab3", data={"action": "empty"}, follow_redirects=True)
    cart_page = client.get("/lab3")
    assert "Keranjang Belanja" not in cart_page.get_data(as_text=True)


def test_lab3_requires_login_for_checkout(client):
    # Tanpa login, POST harus ditolak
    response = client.post(
        "/lab3", data={"pid": "1", "price": "1"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert_no_flag(response, 3)
    assert "login" in response.get_data(as_text=True).lower()


def test_lab3_unauthenticated_view_shows_catalog_without_credit(client):
    # Akses awal langsung menampilkan katalog kartu tanpa dinding login / informasi berlebih
    res = client.get("/lab3")
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "Katalog Kartu Pokémon" in body
    assert "Charizard Holo 1st Edition" in body
    # Kredit belum terlihat sebelum login
    assert "Your credit" not in body
    # Tombol Add to cart mengarahkan ke login
    assert "/lab3/login" in body


def test_lab3_login_page_renders(client):
    res = client.get("/lab3/login")
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "Login Pelanggan" in body
    assert "wiener:peter" in body


def test_lab3_repeater_server_sync_workflow(client):
    # Simulasi: login di browser
    client.post("/lab3/login", data={"username": "wiener", "password": "peter"})
    # Simulasi Burp Repeater: request add to cart dengan harga dimanipulasi ($1.99)
    res_add = client.post("/lab3", data={"action": "add", "pid": "1", "price": "1.99", "qty": "1"})
    assert res_add.status_code == 302

    # Simulasi browser di-refresh: server harus mengembalikan cart dengan harga $1.99 yang tersimpan
    res_refresh = client.get("/lab3")
    body = res_refresh.get_data(as_text=True)
    assert "$1.99" in body
    assert "Charizard Holo 1st Edition" in body

    # Checkout dari browser
    res_checkout = client.post("/lab3", data={"action": "checkout"}, follow_redirects=True)
    assert res_checkout.status_code == 200
    assert_has_flag(res_checkout, 3)


def test_lab3_receipt_contains_flag_and_item_details(client):
    client.post("/lab3/login", data={"username": "wiener", "password": "peter"})
    client.post("/lab3", data={"action": "add", "pid": "1", "price": "1.00", "qty": "1"})
    response = client.post("/lab3", data={"action": "checkout"}, follow_redirects=True)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    # Struk pembelian ditampilkan
    assert "Struk Bukti Pembelian Kartu" in body
    assert "Charizard Holo 1st Edition" in body
    assert "LUNAS / PAID" in body
    assert flag(3) in body
    # Notifikasi flash adalah pesan formal bukti transaksi, bukan string flag mentah
    assert "Bukti transaksi" in body


def test_lab3_logout_redirects_to_lab3(client):
    client.post("/lab3/login", data={"username": "wiener", "password": "peter"})
    res = client.get("/lab3/logout", follow_redirects=False)
    assert res.status_code == 302
    assert res.headers["Location"] == "/lab3"


def test_lab4_negative_quantity_exploit(client):
    client.post("/lab4/login", data={"username": "wiener", "password": "peter"})
    client.post("/lab4", data={"action": "add", "pid": "1", "qty": "1"})
    client.post("/lab4", data={"action": "add", "pid": "2", "qty": "-15"})
    response = client.post(
        "/lab4", data={"action": "checkout"}, follow_redirects=True
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Struk Bukti Pembelian" in html or "receipt" in html.lower()
    assert_has_flag(response, 4)


def test_lab4_normal_checkout_is_rejected(client):
    client.post("/lab4/login", data={"username": "wiener", "password": "peter"})
    client.post("/lab4", data={"action": "add", "pid": "1", "qty": "1"})
    response = client.post(
        "/lab4", data={"action": "checkout"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert_no_flag(response, 4)


def test_lab4_requires_login_for_checkout(client):
    response = client.post(
        "/lab4", data={"action": "checkout"}, follow_redirects=False
    )
    assert response.status_code == 302
    assert "/lab4/login" in response.headers["Location"]


def test_lab4_login_page_renders(client):
    response = client.get("/lab4/login")
    assert response.status_code == 200
    assert "wiener:peter" in response.get_data(as_text=True)


def test_lab4_logout_redirects_to_lab4(client):
    client.post("/lab4/login", data={"username": "wiener", "password": "peter"})
    res = client.get("/lab4/logout", follow_redirects=False)
    assert res.status_code == 302
    assert res.headers["Location"] == "/lab4"


def test_lab4_receipt_contains_flag_and_item_details(client):
    client.post("/lab4/login", data={"username": "wiener", "password": "peter"})
    client.post("/lab4", data={"action": "add", "pid": "1", "qty": "1"})
    client.post("/lab4", data={"action": "add", "pid": "2", "qty": "-15"})
    response = client.post(
        "/lab4", data={"action": "checkout"}, follow_redirects=True
    )
    html = response.get_data(as_text=True)
    assert "PKM-" in html
    assert "Sertifikat Keaslian" in html
    assert_has_flag(response, 4)


def test_lab4_cart_increment_decrement(client):
    client.post("/lab4/login", data={"username": "wiener", "password": "peter"})
    # Add item with qty 1
    client.post("/lab4", data={"action": "add", "pid": "2", "qty": "1"})
    res = client.get("/lab4")
    html = res.get_data(as_text=True)
    assert "Pikachu" in html

    # Increment to qty 2
    client.post("/lab4", data={"action": "add", "pid": "2", "qty": "1"})
    res = client.get("/lab4")
    html = res.get_data(as_text=True)
    assert "Pikachu" in html

    # Decrement back to qty 1
    client.post("/lab4", data={"action": "add", "pid": "2", "qty": "-1"})
    res = client.get("/lab4")
    html = res.get_data(as_text=True)
    assert "Pikachu" in html

    # Decrement to qty 0 -> item removed
    res = client.post("/lab4", data={"action": "add", "pid": "2", "qty": "-1"}, follow_redirects=True)
    html = res.get_data(as_text=True)
    assert "dihapus dari keranjang" in html
    # Cart should be empty now - no cart table shown
    assert "Keranjang Belanja" not in html


def test_lab5_robots_txt_discloses_admin_panel(client):
    res = client.get("/robots.txt")
    assert res.status_code == 200
    assert "/lab5/admin-panel" in res.get_data(as_text=True)

    res5 = client.get("/lab5/robots.txt")
    assert res5.status_code == 200
    assert "/lab5/admin-panel" in res5.get_data(as_text=True)


def test_lab5_homepage_shows_store_catalog(client):
    res = client.get("/lab5")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Katalog Kartu Pokémon" in html
    assert "Charizard Holo" in html
    # Should NOT have the login or register form directly embedded in the homepage
    assert 'action="/lab5/login"' not in html
    assert 'action="/lab5/register"' not in html


def test_lab5_login_and_register_pages_are_separated(client):
    # Login page
    res_login = client.get("/lab5/login")
    assert res_login.status_code == 200
    html_login = res_login.get_data(as_text=True)
    assert "Masuk ke Akun" in html_login
    assert 'action="/lab5/login"' in html_login
    assert 'action="/lab5/register"' not in html_login

    # Register page
    res_reg = client.get("/lab5/register")
    assert res_reg.status_code == 200
    html_reg = res_reg.get_data(as_text=True)
    assert "Daftar Akun Baru" in html_reg
    assert "@gembeng.com" in html_reg
    assert 'action="/lab5/register"' in html_reg
    assert 'action="/lab5/login"' not in html_reg


def test_lab5_my_account_requires_login(client):
    res = client.get("/lab5/my-account", follow_redirects=False)
    assert res.status_code == 302
    assert "/lab5/login" in res.headers["Location"]


def test_lab5_admin_panel_access_denied_without_admin(client):
    res = client.get("/lab5/admin-panel")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Akses Ditolak" in html or "jangannangis" in html


def test_lab5_email_verification_and_exploit(client):
    # 1. Register with @exploit-lab.net
    client.post(
        "/lab5/register",
        data={"username": "alice", "password": "pw", "email": "alice@exploit-lab.net"},
        follow_redirects=True,
    )

    # 2. Cannot login before verification
    res_fail = client.post(
        "/lab5/login",
        data={"username": "alice", "password": "pw"},
        follow_redirects=True,
    )
    assert "belum diverifikasi" in res_fail.get_data(as_text=True)

    # 3. Check Email Client for verification link
    res_mail = client.get("/lab5/email-client")
    html_mail = res_mail.get_data(as_text=True)
    assert "alice@exploit-lab.net" in html_mail
    import re
    token_match = re.search(r"token=([a-f0-9]+)", html_mail)
    assert token_match, "Verification token should be present in email client"
    token = token_match.group(1)

    # 4. Verify account
    res_verify = client.get(f"/lab5/verify?token={token}", follow_redirects=True)
    assert "berhasil diverifikasi" in res_verify.get_data(as_text=True)

    # 5. Login successfully
    res_login = client.post(
        "/lab5/login",
        data={"username": "alice", "password": "pw"},
        follow_redirects=True,
    )
    assert "Selamat datang, alice" in res_login.get_data(as_text=True)

    # 6. Still user, accessing admin-panel is denied
    res_admin_denied = client.get("/lab5/admin-panel")
    assert "Akses Ditolak" in res_admin_denied.get_data(as_text=True)

    # 7. Update email to @gembeng.com (domain used by jangannangis)
    client.post("/lab5/update-email", data={"email": "alice@gembeng.com"}, follow_redirects=True)

    # 8. Now admin, access admin panel
    res_admin = client.get("/lab5/admin-panel")
    assert res_admin.status_code == 200
    assert "Panel Administrasi" in res_admin.get_data(as_text=True)
    assert "carlos" in res_admin.get_data(as_text=True)

    # 9. Delete user carlos
    res_delete = client.post("/lab5/admin/delete", data={"username": "carlos"}, follow_redirects=True)
    assert res_delete.status_code == 200
    html_del = res_delete.get_data(as_text=True)
    assert "carlos" in html_del and "berhasil dihapus" in html_del
    assert_has_flag(res_delete, 5)


def test_lab5_cannot_delete_jangannangis(client):
    # Setup verified admin
    client.post("/lab5/register", data={"username": "hacker", "password": "pw", "email": "hacker@exploit-lab.net"})
    res_mail = client.get("/lab5/email-client")
    import re
    token = re.findall(r"token=([a-f0-9]+)", res_mail.get_data(as_text=True))[-1]
    client.get(f"/lab5/verify?token={token}")
    client.post("/lab5/login", data={"username": "hacker", "password": "pw"})
    client.post("/lab5/update-email", data={"email": "hacker@gembeng.com"})

    # Try to delete jangannangis
    res = client.post("/lab5/admin/delete", data={"username": "jangannangis"}, follow_redirects=True)
    assert "tidak dapat dihapus" in res.get_data(as_text=True)


def test_lab6_homepage_shows_catalog_and_newsletter(client):
    res = client.get("/lab6")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Charizard" in html
    assert "Langganan Berita Koran Kabar" in html
    assert "/lab6/newsletter" in html


def test_lab6_register_awards_newcust5(client):
    res = client.post(
        "/lab6/register",
        data={"username": "trainer1", "password": "password123"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "NEWCUST5" in html
    assert "Selamat datang, trainer1" in html


def test_lab6_newsletter_awards_signup30(client):
    res = client.post(
        "/lab6/newsletter",
        data={"email": "reader@example.com"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "SIGNUP30" in html


def test_lab6_cart_quantity_increment_decrement(client):
    # Initial cart view has quantity 1
    res = client.get("/lab6/cart")
    assert res.status_code == 200

    # Increment quantity by 1 -> qty 2
    res_inc = client.post(
        "/lab6/cart",
        data={"action": "add", "pid": 1, "qty": 1},
        follow_redirects=True,
    )
    assert res_inc.status_code == 200
    html_inc = res_inc.get_data(as_text=True)
    assert "Jumlah barang di keranjang berhasil ditambahkan" in html_inc
    assert "$2674.00" in html_inc  # 1337 * 2

    # Decrement quantity by 1 -> qty 1
    res_dec = client.post(
        "/lab6/cart",
        data={"action": "add", "pid": 1, "qty": -1},
        follow_redirects=True,
    )
    assert res_dec.status_code == 200
    html_dec = res_dec.get_data(as_text=True)
    assert "Jumlah barang di keranjang berhasil dikurangi" in html_dec
    assert "$1337.00" in html_dec


def test_lab6_item_in_cart_cannot_be_removed(client):
    # Try to reduce quantity when already at 1 -> blocked, stays 1
    res = client.post(
        "/lab6/cart",
        data={"action": "add", "pid": 1, "qty": -1},
        follow_redirects=True,
    )
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "tidak dapat dihilangkan" in html
    assert "$1337.00" in html

    # Try empty cart -> blocked, stays 1
    res_empty = client.post(
        "/lab6/cart",
        data={"action": "empty"},
        follow_redirects=True,
    )
    assert res_empty.status_code == 200
    assert "tidak dapat dihilangkan" in res_empty.get_data(as_text=True)


def test_lab6_unauthenticated_view_shows_catalog_without_credit(client):
    res = client.get("/lab6")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Charizard" in html
    assert "NEWCUST5" in html  # Kupon pertama muncul di bagian atas
    assert "Your credit" not in html  # Tanpa login, kredit tidak kelihatan


def test_lab6_requires_login_for_checkout(client):
    res = client.post("/lab6/checkout")
    assert res.status_code == 302
    assert "/lab6/login" in res.headers["Location"]


def test_lab6_login_shows_credit(client):
    client.post("/lab6/login", data={"username": "trainer1", "password": "password123"})
    res = client.get("/lab6")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Your credit: $100.00" in html


def test_lab6_receipt_contains_flag(client):
    client.post("/lab6/login", data={"username": "trainer1", "password": "password123"})
    # Alternating coupons until balance is sufficient
    for _ in range(7):
        client.post("/lab6/coupon", data={"code": "NEWCUST5"})
        client.post("/lab6/coupon", data={"code": "SIGNUP30"})
    res = client.post("/lab6/checkout", follow_redirects=True)
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Struk Bukti Pembelian Kartu" in html
    assert "Sertifikat Keaslian Kepemilikan Charizard Holo 1st Edition" in html
    assert_has_flag(res, 6)


def test_lab6_stacked_coupons_exploit(client):
    client.post("/lab6/login", data={"username": "trainer1", "password": "password123"})
    for _ in range(7):
        client.post("/lab6/coupon", data={"code": "NEWCUST5"})
        client.post("/lab6/coupon", data={"code": "SIGNUP30"})
    response = client.post("/lab6/checkout", follow_redirects=True)
    assert response.status_code == 200
    assert_has_flag(response, 6)


def test_lab6_same_coupon_twice_is_rejected(client):
    client.post("/lab6/login", data={"username": "trainer1", "password": "password123"})
    client.post("/lab6/coupon", data={"code": "NEWCUST5"})
    response = client.post(
        "/lab6/coupon", data={"code": "NEWCUST5"}, follow_redirects=True
    )
    assert "tidak bisa dipakai dua kali" in response.get_data(as_text=True)
    response = client.post("/lab6/checkout", follow_redirects=True)
    assert_no_flag(response, 6)


@pytest.mark.parametrize("lab", range(1, 7))
def test_lab_mode_restricts_other_labs(make_client, lab):
    lab_client = make_client(lab=lab)
    response = lab_client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/lab{lab}")
    assert lab_client.get(f"/lab{lab}").status_code == 200
    other = 1 if lab != 1 else 2
    assert lab_client.get(f"/lab{other}").status_code == 404
    assert lab_client.get("/reset").status_code == 302


def test_multi_tenant_isolation_lab3(make_client):
    app_client_1 = make_client(lab=3)
    app_client_2 = make_client(lab=3)

    # Participant 1 logs in and adds item to cart
    app_client_1.post("/lab3/login", data={"username": "wiener", "password": "peter"})
    app_client_1.post("/lab3", data={"action": "add", "pid": "1", "price": "1.00", "qty": "1"})

    # Participant 2 logs in with same username
    app_client_2.post("/lab3/login", data={"username": "wiener", "password": "peter"})

    # Participant 2's page must NOT contain Charizard in cart (cart count is 0)
    res2 = app_client_2.get("/lab3")
    body2 = res2.get_data(as_text=True)
    assert "Keranjang Belanja Anda Kosong" in body2 or "Item: 0" in body2 or ">0</p>" in body2

    # Participant 1's page has 1 item in cart
    res1 = app_client_1.get("/lab3")
    body1 = res1.get_data(as_text=True)
    assert "Charizard Holo 1st Edition" in body1


def test_multi_tenant_isolation_lab5(make_client):
    app_client_1 = make_client(lab=5)
    app_client_2 = make_client(lab=5)

    # Participant 1 accesses as admin and deletes carlos
    with app_client_1.session_transaction() as sess:
        sess["member"] = "jangannangis"
    app_client_1.post("/lab5/admin/delete", data={"username": "carlos"}, follow_redirects=True)

    res1 = app_client_1.get("/lab5/admin-panel")
    assert "carlos@exploit-lab.net" not in res1.get_data(as_text=True)

    # In Participant 2's session, carlos must STILL be present
    with app_client_2.session_transaction() as sess:
        sess["member"] = "jangannangis"
    res2 = app_client_2.get("/lab5/admin-panel")
    assert "carlos@exploit-lab.net" in res2.get_data(as_text=True)


def test_lab_reset_route(make_client):
    app_client = make_client(lab=3)
    app_client.post("/lab3/login", data={"username": "wiener", "password": "peter"})
    app_client.post("/lab3", data={"action": "add", "pid": "1", "price": "1.00", "qty": "1"})
    res = app_client.get("/lab3")
    assert "Charizard Holo 1st Edition" in res.get_data(as_text=True)

    # Reset lab 3
    reset_res = app_client.get("/lab3/reset", follow_redirects=True)
    assert reset_res.status_code == 200
    assert "berhasil di-reset" in reset_res.get_data(as_text=True)

    # Cart is now empty
    res_after = app_client.get("/lab3")
    assert "Keranjang Belanja" not in res_after.get_data(as_text=True)

