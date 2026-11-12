# Nusatech CTF Practice Labs

Koleksi 6 lab tantangan keamanan aplikasi web (Web Security CTF) bernuansa toko online e-commerce modern: **Nusatech** (*"Belanja Cerdas, Hidup Praktis"*). Seluruh lab ditulis ulang dari awal dengan skenario dan konsep yang terinspirasi dari topik-topik web security ternama (SQL Injection, Business Logic Flaws, Broken Access Control).

> ⚠️ **PERINGATAN KEAMANAN:**
> Repositori ini berisi celah keamanan web yang **sengaja dibuat untuk tujuan edukasi dan latihan CTF**. 
> - **JANGAN** mempublikasikan repositori ini ke publik (harus disetel sebagai **PRIVATE REPOSITORY**).
> - **JANGAN** menaruh kredensial produksi, flag asli, atau kunci rahasia di dalam commit Git.

---

## Daftar Lab & Port

Setiap lab berjalan pada container mandiri dengan port host terisolasi:

| Lab | Modul Layanan | Port Host | Kategori Celah | Deskripsi Skenario |
| :--- | :--- | :---: | :--- | :--- |
| **Lab 1** | Katalog Produk | `8011` | SQL Injection (WHERE) | Filter kategori produk memungkinkan pengambilan data barang tersembunyi yang belum dirilis. |
| **Lab 2** | Masuk ke Akun | `8012` | SQL Injection (Auth) | Form login pelanggan rentan manipulasi query untuk masuk sebagai administrator tanpa password. |
| **Lab 3** | Penawaran Spesial | `8013` | Business Logic Flaw | Manipulasi harga produk pada kontrol sisi klien (*hidden field*) sebelum dimasukkan ke keranjang belanja. |
| **Lab 4** | Keranjang Belanja | `8014` | Business Logic Flaw | Input kuantitas barang belanjaan tanpa validasi nilai negatif untuk mengurangi total pembayaran akhir. |
| **Lab 5** | Akun Saya & Staf | `8015` | Access Control Flaw | Inkonsistensi validasi domain antara formulir pendaftaran dan pembaruan email untuk membobol portal internal. |
| **Lab 6** | Checkout Promo | `8016` | Business Logic Flaw | Sistem penegakan kupon promosi yang hanya memvalidasi pemakaian berturut-turut, memungkinkan perulangan kode diskon. |

---

## Saldo Akun Peserta & Master Data

- **Saldo Awal:** Setiap peserta diberikan saldo awal sebesar `$100.00` yang tersimpan pada cookie sesi bertanda tangan (Flask session).
- **Produk Incaran:** Pada Lab 3, Lab 4, dan Lab 6, target utama peserta adalah membeli **Drone Elang X200** yang memiliki harga resmi `$1.249,00`.
- **Domain Internal:** Pada Lab 5, portal staf internal (`/lab5/internal`) hanya dapat diakses oleh email dengan akhiran domain `@nusatech.internal`.

---

## Panduan Menjalankan Secara Lokal

### Prasyarat:
- Python 3.12 atau 3.13
- Pip

### 1. Mode All-in-One (Semua Lab Aktif)
Mode ini sangat cocok untuk pengajar atau pembuat soal yang ingin menguji semua tantangan dalam satu aplikasi tunggal:

```bash
# Buat dan aktifkan virtual environment
python -m venv .venv
# Di Windows:
.venv\Scripts\activate
# Di Linux/macOS:
source .venv/bin/activate

# Install dependensi
pip install -r requirements.txt

# Jalankan server pengembangan
python app.py
```
Akses di browser: `http://127.0.0.1:5000/`. Halaman beranda akan menampilkan tautan ke seluruh 6 lab.

### 2. Mode Per-Lab Tunggal
Untuk mensimulasikan lingkungan satu lab spesifik secara lokal:

```bash
# Contoh menjalankan hanya Lab 1:
export LAB=1                # Di Windows PowerShell: $env:LAB="1"
export FLAG_1="CTF{contoh_flag_lab1}"
python app.py
```
Akses di browser: `http://127.0.0.1:5000/`. Permintaan akan otomatis dialihkan (302) ke `/lab1`. Rute lab lain akan mengembalikan status `404 Not Found`.

---

## Panduan Menjalankan dengan Docker Compose

Untuk menyalakan ke-6 container sekaligus di server atau mesin lokal:

1. Salin template environment:
   ```bash
   cp .env.example .env
   ```
2. Isi kunci rahasia dan flag acak di file `.env`.
3. Jalankan container:
   ```bash
   docker compose up -d --build
   ```
   *(Atau gunakan perintah `docker-compose up -d --build` jika menggunakan versi lama).*

Periksa status container:
```bash
docker compose ps
```
Akses masing-masing lab melalui port `http://localhost:8011` hingga `http://localhost:8016`.

---

## Menjalankan Pengujian Otomatis (Unit Test)

Seluruh mekanisme eksploitasi dan batasan akses telah diuji secara otomatis menggunakan `pytest`:

```bash
pytest -v tests/test_labs.py
```

Pengujian memvalidasi:
1. Eksploitasi yang tepat pada masing-masing lab berhasil menampilkan flag.
2. Percobaan biasa atau input normal tidak membocorkan flag.
3. Mode isolasi `LAB=1` s/d `LAB=6` memblokir akses ke modul lab lain (404).

---

## Dokumentasi Tambahan

- [Panduan Deployment aaPanel & Linux Server](docs/DEPLOY.md)
- [Bahan Konfigurasi & Hint CTFd Platform](docs/CTFD.md)
- [Kunci Jawaban Lengkap Pengajar](docs/SOLUTIONS.md)
