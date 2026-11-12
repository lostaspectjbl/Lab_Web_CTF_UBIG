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


def test_lab2_sqli_login_exploit(client):
    response = client.post(
        "/lab2", data={"username": "administrator'--", "password": "x"}
    )
    assert response.status_code == 200
    assert_has_flag(response, 2)


def test_lab2_normal_login_does_not_show_flag(client):
    response = client.post(
        "/lab2", data={"username": "wiener", "password": "peter"}
    )
    assert response.status_code == 200
    assert "hanya untuk administrator" in response.get_data(as_text=True)
    assert_no_flag(response, 2)


def test_lab3_price_tampering_exploit(client):
    response = client.post(
        "/lab3", data={"pid": "1", "price": "1"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert_has_flag(response, 3)


def test_lab3_full_price_is_rejected(client):
    response = client.post(
        "/lab3", data={"pid": "1", "price": "1337"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert_no_flag(response, 3)


def test_lab4_negative_quantity_exploit(client):
    client.post("/lab4", data={"action": "add", "pid": "1", "qty": "1"})
    client.post("/lab4", data={"action": "add", "pid": "2", "qty": "-131"})
    response = client.post(
        "/lab4", data={"action": "checkout"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert_has_flag(response, 4)


def test_lab4_normal_checkout_is_rejected(client):
    client.post("/lab4", data={"action": "add", "pid": "1", "qty": "1"})
    response = client.post(
        "/lab4", data={"action": "checkout"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert_no_flag(response, 4)


def test_lab5_email_change_exploit(client):
    client.post(
        "/lab5/register",
        data={"username": "bob", "password": "pw", "email": "bob@example.com"},
    )
    client.post(
        "/lab5/login", data={"username": "bob", "password": "pw"}
    )
    client.post("/lab5/update-email", data={"email": "bob@ctf-corp.com"})
    response = client.get("/lab5/admin")
    assert response.status_code == 200
    assert_has_flag(response, 5)


def test_lab5_corp_email_registration_is_blocked(client):
    response = client.post(
        "/lab5/register",
        data={
            "username": "eve",
            "password": "pw",
            "email": "eve@ctf-corp.com",
        },
        follow_redirects=True,
    )
    assert "tidak boleh dipakai" in response.get_data(as_text=True)
    client.post("/lab5/login", data={"username": "eve", "password": "pw"})
    assert client.get("/lab5/admin").status_code == 403


def test_lab5_normal_email_cannot_open_admin(client):
    client.post(
        "/lab5/register",
        data={"username": "carol", "password": "pw", "email": "carol@example.com"},
    )
    client.post("/lab5/login", data={"username": "carol", "password": "pw"})
    assert client.get("/lab5/admin").status_code == 403


def test_lab6_stacked_coupons_exploit(client):
    for _ in range(7):
        client.post("/lab6/coupon", data={"code": "NEWCUST5"})
        client.post("/lab6/coupon", data={"code": "SIGNUP30"})
    response = client.post("/lab6/checkout", follow_redirects=True)
    assert response.status_code == 200
    assert_has_flag(response, 6)


def test_lab6_same_coupon_twice_is_rejected(client):
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
