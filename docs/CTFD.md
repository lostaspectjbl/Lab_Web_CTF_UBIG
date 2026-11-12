# Panduan Pengaturan Soal CTFd Platform

Dokumen ini berisi materi deskripsi tantangan, petunjuk (*hints*), dan konfigurasi untuk dimasukkan ke dalam platform CTFd Anda.

---

## Panduan Cepat Menambahkan Soal di Admin Panel CTFd

1. Masuk ke dashboard Admin CTFd Anda (`http://IP-SERVER:8080/admin` atau domain CTFd Anda).
2. Klik menu **Challenges** pada bilah navigasi atas.
3. Klik tombol **New Challenge** (atau tanda `+`).
4. Pilih tipe: **Standard**.
5. Isi formulir tantangan sesuai data di bawah ini (Nama Soal, Kategori: `Web`, Nilai Poin, dan Deskripsi).
6. Pada tab **Flags**, pilih tipe **Static Flag**, lalu masukkan flag rahasia yang sama persis dengan yang Anda tuliskan di file `.env` server (`FLAG_n`).
7. Pada tab **Hints**, tambahkan 3 petunjuk bertingkat (opsional: dapat diberi pinalti poin atau gratis).
8. Ubah status soal dari **Hidden** menjadi **Visible** saat kompetisi dimulai.

---

## 1. Lab 1 — Katalog Produk Tersembunyi

- **Nama Soal:** Nusatech: Katalog Khusus
- **Kategori:** Web
- **Poin Rekomendasi:** 30 Poin
- **Tipe Flag:** Static Flag (Isi sesuai nilai `FLAG_1` di file `.env`)
- **Deskripsi Soal untuk Peserta:**
  ```markdown
  Nusatech Store baru saja meluncurkan platform katalog elektronik terpadu di `{URL}`.
  Namun, tim riset internal dikabarkan sedang mengembangkan sebuah unit sensor cuaca prototipe yang statusnya masih dirahasiakan dan belum dirilis untuk umum.

  Dapatkah Anda menemukan rincian lisensi firmware prototipe rahasia tersebut dari katalog produk?
  ```
- **Petunjuk Bertingkat (Hints):**
  1. *Hint 1 (Samar - 5 poin):* Perhatikan bagaimana filter kategori mengirimkan parameter melalui URL saat Anda menyaring produk.
  2. *Hint 2 (Sedang - 10 poin):* Sistem database di balik pencarian produk menyaring data dengan kondisi logika `released = 1`.
  3. *Hint 3 (Hampir Jelas - 15 poin):* Cobalah masukkan karakter tanda petik tunggal (`'`) untuk memanipulasi klausa WHERE agar kondisi selalu bernilai TRUE, dan gunakan tanda komentar SQL (`--`) untuk mengabaikan sisa query.

---

## 2. Lab 2 — Akses Administrator Toko

- **Nama Soal:** Nusatech: Pintu Belakang Manajer
- **Kategori:** Web
- **Poin Rekomendasi:** 40 Poin
- **Tipe Flag:** Static Flag (Isi sesuai nilai `FLAG_2` di file `.env`)
- **Deskripsi Soal untuk Peserta:**
  ```markdown
  Manajer operasional Nusatech Store memiliki portal akun khusus di `{URL}`.
  Kata sandi milik akun administrator utama (`admin_utama`) digenerate secara acak dan sangat kuat sehingga mustahil ditebak.

  Buktikan bahwa terdapat kelemahan pada mekanisme autentikasi formulir masuk yang memungkinkan Anda masuk sebagai pimpinan toko tanpa mengetahui kata sandinya!
  ```
- **Petunjuk Bertingkat (Hints):**
  1. *Hint 1 (Samar - 5 poin):* Kredensial login dikonfirmasi langsung ke database SQL tanpa preparasi parameter yang aman.
  2. *Hint 2 (Sedang - 10 poin):* Akun administrator di sistem ini bernama `admin_utama`.
  3. *Hint 3 (Hampir Jelas - 15 poin):* Karakter `--` dalam SQLite berfungsi untuk mematikan pengecekan kata sandi pada sisa baris query.

---

## 3. Lab 3 — Penawaran Terlalu Menarik

- **Nama Soal:** Nusatech: Diskon Mandiri
- **Kategori:** Web
- **Poin Rekomendasi:** 40 Poin
- **Tipe Flag:** Static Flag (Isi sesuai nilai `FLAG_3` di file `.env`)
- **Deskripsi Soal untuk Peserta:**
  ```markdown
  Toko Nusatech di `{URL}` memajang **Drone Elang X200** dengan harga resmi $1.249,00.
  Setiap pelanggan baru hanya diberikan kredit belanja sebesar $100.00 di akun mereka.

  Bisakah Anda mengakali formulir pemesanan barang sehingga Drone tersebut berhasil dibeli dan diverifikasi oleh sistem toko?
  ```
- **Petunjuk Bertingkat (Hints):**
  1. *Hint 1 (Samar - 5 poin):* Periksa elemen formulir HTML (*Inspect Element*) pada tombol pemesanan atau saat menambahkan barang ke keranjang.
  2. *Hint 2 (Sedang - 10 poin):* Apakah server benar-benar memeriksa keaslian nilai harga yang dikirimkan oleh browser Anda?
  3. *Hint 3 (Hampir Jelas - 15 poin):* Terdapat input tersembunyi berjenis `<input type="hidden" name="price" ...>`. Ubah nilainya menjadi nominal yang lebih kecil dari sisa saldo Anda (misalnya `$1.00`), masukkan ke keranjang belanja, lalu selesaikan pembayaran.

---

## 4. Lab 4 — Keajaiban Saldo Keranjang

- **Nama Soal:** Nusatech: Keranjang Ajaib
- **Kategori:** Web
- **Poin Rekomendasi:** 60 Poin
- **Tipe Flag:** Static Flag (Isi sesuai nilai `FLAG_4` di file `.env`)
- **Deskripsi Soal untuk Peserta:**
  ```markdown
  Sistem keranjang belanja di `{URL}` telah dirancang agar harga produk dibaca langsung dari katalog server tanpa memercayai input harga dari browser.
  Meskipun demikian, Anda tetap ingin memiliki **Drone Elang X200** ($1.249,00) dengan saldo awal yang hanya $100.00.

  Temukan anomali pada pemrosesan kuantitas barang belanjaan di keranjang untuk meloloskan transaksi pesanan Anda!
  ```
- **Petunjuk Bertingkat (Hints):**
  1. *Hint 1 (Samar - 10 poin):* Keranjang belanja memungkinkan Anda menambah atau mengurangi jumlah unit produk.
  2. *Hint 2 (Sedang - 15 poin):* Sistem mengonversi input jumlah barang menjadi angka bulat (*integer*), tetapi apakah ada batas nilai minimum yang divalidasi?
  3. *Hint 3 (Hampir Jelas - 25 poin):* Memasukkan kuantitas bernilai negatif pada produk lain yang berharga murah (misal Earbuds Gema Pro seharga $42.00) dapat memotong subtotal keranjang belanja secara drastis hingga total tagihan berada di antara $0 sampai $100.

---

## 5. Lab 5 — Saluran Staf Korporat

- **Nama Soal:** Nusatech: Akses Internal Staf
- **Kategori:** Web
- **Poin Rekomendasi:** 60 Poin
- **Tipe Flag:** Static Flag (Isi sesuai nilai `FLAG_5` di file `.env`)
- **Deskripsi Soal untuk Peserta:**
  ```markdown
  Nusatech memiliki portal staf internal yang hanya dapat dibuka oleh pemegang email resmi perusahaan (`@nusatech.internal`) di `{URL}`.
  Sistem registrasi umum menolak siapapun yang mencoba mendaftar dengan domain email tersebut.

  Telusuri alur manajemen akun pelanggan untuk mencari inkonsistensi kendali akses yang memungkinkan Anda mengakses Portal Staf Internal!
  ```
- **Petunjuk Bertingkat (Hints):**
  1. *Hint 1 (Samar - 10 poin):* Celah ini bukan injeksi SQL, melainkan inkonsistensi logika kendali otorisasi pengguna.
  2. *Hint 2 (Sedang - 15 poin):* Perhatikan perbedaan validasi masukan antara formulir registrasi awal dengan formulir pembaruan profil di dalam dashboard pengguna.
  3. *Hint 3 (Hampir Jelas - 25 poin):* Daftarkan akun baru menggunakan email publik biasa (misal `@gmail.com`), masuk ke akun, lalu ubah alamat email aktif Anda menjadi `namaAnda@nusatech.internal` melalui form profil. Setelah itu buka tautan Portal Staf Internal.

---

## 6. Lab 6 — Trik Kupon Bergantian

- **Nama Soal:** Nusatech: Promo Berantai
- **Kategori:** Web
- **Poin Rekomendasi:** 70 Poin
- **Tipe Flag:** Static Flag (Isi sesuai nilai `FLAG_6` di file `.env`)
- **Deskripsi Soal untuk Peserta:**
  ```markdown
  Nusatech Store mempromosikan dua kupon diskon resmi di `{URL}`:
  1. `HEMAT50` (Potongan harga tetap sebesar $50.00)
  2. `DISKON30` (Potongan harga sebesar 30% dari nilai saat ini)

  Sistem checkout toko melarang pelanggan menggunakan kode promo yang sama lebih dari satu kali secara berturut-turut.
  Dapatkah Anda menurunkan harga Drone Elang X200 ($1.249,00) hingga mencukupi batas saldo Anda ($100.00)?
  ```
- **Petunjuk Bertingkat (Hints):**
  1. *Hint 1 (Samar - 10 poin):* Sistem menyimpan kode promo terakhir yang Anda masukkan di sesi belanja.
  2. *Hint 2 (Sedang - 20 poin):* Validasi promo hanya memeriksa: *apakah kupon yang dimasukkan sama dengan kupon terakhir kali diaplikasikan?*
  3. *Hint 3 (Hampir Jelas - 30 poin):* Terapkan kode `HEMAT50`, kemudian terapkan `DISKON30`, lalu terapkan kembali `HEMAT50`, dan seterusnya secara bergantian sebanyak sekitar 6–7 kali hingga harga akhir drone turun di bawah $100.00 sebelum menekan tombol bayar.
