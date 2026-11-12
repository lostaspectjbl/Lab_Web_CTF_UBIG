# CTF Web Labs

Enam lab CTF web yang sengaja rentan, dibuat untuk latihan SQL injection dan
business logic. Semua lab berjalan dari satu aplikasi Flask dan satu image
Docker; setiap container hanya mengaktifkan satu lab.

> **Peringatan:** aplikasi ini sengaja memiliki celah keamanan. Jangan pernah
> menaruhnya di internet terbuka tanpa isolasi, dan jangan memakai kredensial
> atau flag asli di luar lingkungan latihan. Simpan repo ini sebagai **private**.

## Daftar Lab

| Lab | Tema | Port host | Poin CTFd |
| --- | --- | --- | --- |
| 1 | SQL injection pada filter kategori | 8011 | 30 |
| 2 | SQL injection pada form login | 8012 | 40 |
| 3 | Manipulasi harga di hidden input | 8013 | 40 |
| 4 | Quantity negatif pada keranjang | 8014 | 60 |
| 5 | Business logic pada perubahan email | 8015 | 60 |
| 6 | Tumpukan kupon diskon | 8016 | 70 |

## Menjalankan Secara Lokal

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Buka `http://127.0.0.1:5000`. Tanpa variabel `LAB`, semua lab aktif dan
halaman utama menampilkan tautan ke enam lab. Untuk hanya menjalankan satu lab:

```bash
LAB=1 FLAG_1='CTF{contoh}' SECRET_KEY='rahasia-lokal' python app.py
```

Database SQLite dibuat ulang setiap aplikasi start. Lokasi default
`/tmp/lab.db`, dapat diganti dengan `DB_PATH`.

## Menjalankan dengan Docker Compose

```bash
cp .env.example .env
# isi SECRET_KEY_1..6 dan FLAG_1..6 di .env
docker compose up -d --build
```

Enam container akan listen di port 8011 sampai 8016. Cek status:

```bash
docker compose ps
```

Panduan deploy lengkap untuk aaPanel ada di [docs/DEPLOY.md](docs/DEPLOY.md).

## Variabel Lingkungan

| Variabel | Wajib | Keterangan |
| --- | --- | --- |
| `LAB` | Tidak | `1`-`6` untuk mode satu lab; kosong berarti semua lab aktif |
| `SECRET_KEY_n` | Ya (Docker) | Secret key Flask untuk container lab `n` |
| `SECRET_KEY` | Tidak | Fallback secret key untuk pemakaian lokal |
| `FLAG_n` | Ya (Docker) | Flag untuk lab `n` |
| `DB_PATH` | Tidak | Lokasi file SQLite, default `/tmp/lab.db` |

Nilai flag dan secret asli hanya boleh berada di `.env` (tidak di-commit) atau
di environment server.

## Tes

```bash
pip install pytest
python -m pytest -q
```

Tes mencakup eksploit tiap lab, percobaan normal yang tidak boleh mendapat
flag, dan isolasi mode `LAB`.

## Struktur

```text
app.py               aplikasi Flask dan seluruh lab
tests/test_labs.py   tes otomatis
Dockerfile           image aplikasi
docker-compose.yml   enam service lab
docs/                panduan deploy, bahan CTFd, kunci jawaban
```

## Catatan Desain

- Satu image, banyak container: `LAB` memilih lab aktif sehingga tiap peserta
  hanya melihat tantangan miliknya.
- State disimpan di session cookie dan SQLite; tidak ada volume agar container
  mudah dihapus dan dibuat ulang.
- Flag dibaca dari environment. Jika tidak diisi, aplikasi memakai flag
  pengembangan `CTF{dev_only_lab_N}` yang tidak boleh dipakai untuk lomba.
- Kunci jawaban pengajar ada di `docs/SOLUTIONS.md`; file itu tidak ikut ke
  dalam image Docker.
