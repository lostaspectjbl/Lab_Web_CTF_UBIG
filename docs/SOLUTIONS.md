# Kunci Jawaban Lab

> **Khusus pengajar.** Dokumen ini membocorkan seluruh langkah penyelesaian.
> Jangan membagikannya kepada peserta dan jangan menaruhnya di server challenge.
> File ini juga dikecualikan dari image Docker melalui `.dockerignore`.

## Prasyarat

- Gunakan alamat lab yang diberikan panitia, misalnya `http://IP-SERVER:8011`
  untuk Lab 1. Di dokumen ini alamat tersebut ditulis sebagai `{URL}`.
- Setiap lab berdiri sendiri. Jika sesi atau data uji perlu dibersihkan, buka
  `{URL}/reset`. Database juga dibuat ulang setiap container dijalankan ulang.
- Flag yang benar adalah nilai `FLAG_n` pada environment container. Jangan
  memakai flag pengembangan `CTF{dev_only_lab_N}` untuk lomba.

| Lab | Nama soal | Poin | Halaman awal |
| --- | --- | --- | --- |
| 1 | Toko Kategori | 30 | `{URL}/lab1` |
| 2 | Login Administrator | 40 | `{URL}/lab2` |
| 3 | Harga Spesial | 40 | `{URL}/lab3` |
| 4 | Keranjang Ajaib | 60 | `{URL}/lab4` |
| 5 | Email Perusahaan | 60 | `{URL}/lab5` |
| 6 | Kupon Berlapis | 70 | `{URL}/lab6` |

---

## Lab 1 - Toko Kartu Pokémon & Koleksi Rahasia (SQL Injection)

**Tujuan:** menampilkan kartu koleksi langka yang belum dirilis ke publik dan membaca flag di deskripsinya.

**Langkah:**

1. Buka `{URL}/lab1`.
2. Coba filter kategori normal, misalnya `Vintage & Base Set` atau `Gifts`. Hanya kartu yang sudah dirilis secara resmi yang tampil (`released = 1`).
3. Masukkan payload berikut pada input pencarian kategori atau via parameter URL:

   ```text
   Gifts' OR 1=1--
   ```

   Jika dikirim langsung via URL:

   ```text
   {URL}/lab1?category=Gifts%27%20OR%201%3D1--
   ```

4. Semua baris produk kartu akan ditampilkan, termasuk kartu rahasia bertajuk `Charizard 1st Edition Shadowless (Secret Vault Edition)` (`released = 0`).
5. Flag CTF Lab 1 tercantum pada deskripsi kartu tersebut dan banner Solved aktif.

**Payload inti:** `Gifts' OR 1=1--` atau cukup `' OR 1=1--`

**Mengapa berhasil:** input kategori disisipkan langsung ke query:

```sql
SELECT id, name, price, description, image, rating, released FROM products
WHERE category='Gifts' OR 1=1--' AND released=1
```

Bagian `OR 1=1` membuat kondisi selalu benar (TRUE), sedangkan tanda komentar `--` mengabaikan sisa query termasuk `AND released=1`.

**Perbaikan:** gunakan parameterized query (`WHERE category = ? AND released = 1`) dan validasi kategori terhadap daftar kategori yang diizinkan (allowlist).

---

## Lab 2 - Portal E-Rapor Sekolah (SQL Injection Login Bypass & Data Tampering)

**Tujuan:** masuk sebagai `administrator` melalui SQL injection pada form login portal e-rapor, lalu perbarui nilai salah satu murid yang berstatus Remedial agar tuntas dan mendapatkan flag.

**Langkah:**

1. Buka `{URL}/lab2`. Halaman menampilkan portal e-rapor sekolah beserta form login di sebelah kanan.
2. Isi kolom username dengan payload SQL injection bypass:

   ```text
   administrator'--
   ```

3. Isi kolom password dengan sembarang karakter (misal `x` atau `123`).
4. Klik **Masuk ke Portal**.
5. Anda akan berhasil masuk ke **Panel Administrator - Manajemen Nilai Rapor**.
6. Pada tabel daftar siswa, cari siswa yang berstatus **Remedial** (misalnya `Budi Santoso`, nilai `45`).
7. Ubah nilai di kotak input menjadi nilai tuntas (misalnya `85`), lalu klik tombol **Ubah**.
8. Nilai rapor berhasil diperbarui menjadi status **Tuntas**, dan kotak hijau berisi **FLAG Lab 2** langsung ditampilkan!

**Payload inti:** Username `administrator'--`, password bebas, lalu kirim form `POST /lab2/update-grade` dengan `student_id=1&grade=85`.

**Mengapa berhasil:**
1. Form login membentuk query dengan penggabungan string (string concatenation):
   ```sql
   SELECT username FROM users WHERE username='administrator'--' AND password='x'
   ```
   Karakter `--` membuat server mengomentari pengecekan password, sehingga query mengembalikan akun `administrator`.
2. Setelah sesi login admin diperoleh, panel manajemen nilai rapor terbuka dan mengizinkan modifikasi nilai siswa pada database, yang kemudian memicu penerbitan flag.

**Perbaikan:** gunakan parameterized query (`WHERE username = ?`), simpan password dalam bentuk hash aman (seperti argon2id atau bcrypt), dan terapkan otentikasi multi-faktor (MFA) untuk hak akses administratif sekolah.

---

## Lab 3 - Toko Kartu Pokémon (Manipulasi Hidden Input / Client-Side Price Tampering)

**Tujuan:** membeli kartu langka `Charizard Holo 1st Edition` seharga $1,337.00 dengan batas saldo kredit $100.00, lalu menerima struk bukti pembelian yang memuat flag.

**Langkah:**

1. Buka `{URL}/lab3`. Halaman langsung menampilkan etalase kartu Pokémon (Charizard, Pikachu, Mewtwo, Blastoise, dll.).
2. Klik **My account** atau tombol **Add to cart** untuk menuju ke `{URL}/lab3/login`. Masuk menggunakan akun demo `wiener:peter`.
3. Setelah login, informasi saldo (`Your credit: $100.00`) dan keranjang belanja aktif.
4. Pada kartu **Charizard Holo 1st Edition** (`pid=1`, harga resmi `$1337.00`):
   - **Metode A (DevTools / Inspect Element):** Buka Inspect Element (F12) pada tombol "Add to cart", ubah atribut `value="1337.00"` pada input `<input type="hidden" name="price" value="1337.00">` menjadi `1` atau `0.50`, lalu klik **Add to cart**.
   - **Metode B (Burp Suite Intercept / Repeater):** Tangkap request `POST /lab3`, ubah parameter `price=1337.00` menjadi `price=1`, kirim request, lalu refresh halaman browser Anda.
5. Kartu Charizard berhasil masuk ke **Keranjang Belanja** dengan harga terjangkau ($1.00).
6. Klik tombol **Place order** / **Checkout**.
7. Karena total harga ($1.00) berada di bawah saldo ($100.00), pesanan langsung disetujui (LUNAS/PAID).
8. Sistem menerbitkan **Struk Bukti Pembelian Kartu** resmi. Di bagian bawah rincian barang Charizard, tercantum kotak sertifikat keaslian kepemilikan kartu yang berisi **FLAG Lab 3**.

**Payload inti:** `action=add&pid=1&price=1&qty=1` lalu `action=checkout`.

**Mengapa berhasil:** server mempercayai parameter `price` yang dikirimkan client saat barang dimasukkan ke keranjang tanpa memvalidasi ulang harga produk terhadap katalog resmi di backend.

**Perbaikan:** abaikan parameter harga yang dikirim client. Ambil harga produk langsung dari database berdasarkan `pid`, hitung total belanja di server, dan gunakan tipe uang yang aman (misalnya integer sen).

---

## Lab 4 - Keranjang Ajaib (Quantity Negatif)

**Tujuan:** membuat total belanja masuk akal meskipun jaket berharga $1337.

**Langkah:**

1. Buka `{URL}/lab4`.
2. Tambahkan jaket (`pid=1`) dengan jumlah `1`.
3. Tambahkan Gift Card (`pid=2`) dengan jumlah `-131`.
4. Total keranjang menjadi:

   ```text
   1337 + (10 x -131) = 1337 - 1310 = 27
   ```

5. Klik checkout. Total $27 berada di antara 0 dan $100, dan jaket masih ada
   dengan jumlah positif. Flag Lab 4 muncul.

**Payload inti:** `pid=1&qty=1` lalu `pid=2&qty=-131`, kemudian checkout.

**Mengapa berhasil:** server tidak memeriksa batas bawah jumlah barang. Jumlah
negatif menghasilkan subtotal negatif dan menurunkan total.

**Perbaikan:** tolak jumlah `<= 0`, tetapkan batas maksimum, validasi ulang isi
keranjang di server, dan hitung total dari harga katalog.

---

## Lab 5 - Email Perusahaan & Escalation of Privileges (Access Control)

**Tujuan:** Mendapatkan hak akses administrator milik pengguna `jangannangis` via manipulasi domain email profil, mengakses panel admin tersembunyi, dan menghapus pengguna `carlos` untuk memperoleh flag.

**Langkah Penyelesaian:**

1. **Reconnaissance Direktori Admin:**
   - Akses `{URL}/robots.txt` atau `{URL}/lab5/robots.txt`.
   - Terlihat direktori yang disembunyikan: `Disallow: /lab5/admin-panel`.
   - Coba buka `{URL}/lab5/admin-panel`. Muncul pesan **Akses Ditolak: Administrator Saja** dengan informasi bahwa role admin dimiliki oleh pengguna `jangannangis` (@gembeng.com).

2. **Pendaftaran Akun & Verifikasi Email:**
   - Buka halaman pendaftaran di `{URL}/lab5`.
   - Perhatikan pengumuman: *"Jika Anda bekerja untuk jangannangis, maka gunakan alamat email resmi berakhiran @gembeng.com"*.
   - Jika Anda mencoba langsung mendaftar dengan `@gembeng.com`, email aktivasi tidak akan sampai karena server mail tersebut fiktif/internal dan lab menyediakan **Email Client** khusus domain `@exploit-lab.net`.
   - Daftarkan akun baru menggunakan domain email client lab, contohnya:
     ```text
     username: wiener
     password: peter
     email:    wiener@exploit-lab.net
     ```
   - Buka Email Client di `{URL}/lab5/email-client`.
   - Buka pesan verifikasi akun yang masuk, lalu klik tautan verifikasi (`/lab5/verify?token=...`). Akun berhasil diaktifkan.

3. **Login & Eksploitasi Update Email:**
   - Masuk ke `{URL}/lab5` dengan kredensial yang baru diverifikasi (`wiener:peter`).
   - Masuk ke menu **My Account**.
   - Pada form **Perbarui Alamat Email**, ubah alamat email Anda menjadi domain internal perusahaan:
     ```text
     wiener@gembeng.com
     ```
   - Karena endpoint update email tidak mewajibkan verifikasi ulang kepemilikan email baru dan mempercayai domain `@gembeng.com`, sistem otomatis memberikan peran **Administrator**.

4. **Akses Admin Panel & Hapus Pengguna Carlos:**
   - Buka panel administrasi di `{URL}/lab5/admin-panel` (atau klik tombol **Admin panel** yang kini muncul di menu).
   - Pada daftar pengguna aktif, cari akun `carlos`.
   - Klik tombol **Hapus Pengguna**.
   - Pengguna `carlos` terhapus dari sistem dan kotak sertifikat berisi flag Lab 5 akan muncul.

**Mengapa berhasil:**
Aplikasi mengasumsikan siapa pun yang memiliki email `@gembeng.com` adalah staf `jangannangis` yang berhak atas role administrator. Meskipun form pendaftaran membatasi akses melalui verifikasi email, fitur update profil (`/lab5/update-email`) memiliki celah logika karena langsung memperbarui database dan menaikkan privilege tanpa verifikasi token email ulang.

**Perbaikan:**
1. Pisahkan penetapan peran administratif dari alamat email (gunakan role-based access control / RBAC yang dikelola administrator secara eksplisit).
2. Terapkan verifikasi email ulang (kirim token konfirmasi ke alamat baru) sebelum email profil resmi diubah.
3. Lindungi endpoint panel admin dengan otentikasi sesi berbasis hak akses yang ketat, bukan sekadar string suffix email.

---

## Lab 6 - Kupon Berlapis (Logika Diskon)

**Tujuan:** Membeli kartu koleksi langka Charizard Holo 1st Edition seharga $1337.00 dengan batas kredit hanya $100.00 melalui eksploitasi penumpukan kupon diskon bertingkat.

**Langkah:**

1. **Eksplorasi Toko & Mendapatkan Kupon:**
   - Akses `{URL}/lab6`. Halaman utama menampilkan etalase toko Pokémon cards dengan kartu Charizard Holo 1st Edition seharga $1337.00 yang secara otomatis sudah masuk ke keranjang belanja (kuantitas 1 dan tidak dapat dihapus/dihilangkan).
   - **Kupon Pertama (`NEWCUST5`):** Langsung tercantum pada banner promo di bagian paling atas halaman lab (`{URL}/lab6` dan `{URL}/lab6/cart`). Kode kupon: `NEWCUST5` (potongan $5.00).
   - **Kupon Kedua (`SIGNUP30`):** Di bagian bawah halaman utama toko `{URL}/lab6`, isi form **Langganan Berita Koran Kabar Pokémon** dengan email Anda lalu submit. Notifikasi sistem akan memberikan kupon promosi newsletter: `SIGNUP30` (diskon 30%).
   - **Melihat Saldo Kredit:** Klik **My account** / **Register** untuk login atau mendaftar akun. Saldo kredit ($100.00) hanya akan muncul setelah pengguna masuk ke akun.

2. **Eksploitasi Celah Penumpukan Kupon di Keranjang Belanja:**
   - Pastikan Anda sudah login (`{URL}/lab6/login` atau `{URL}/lab6/register`).
   - Buka keranjang belanja di `{URL}/lab6/cart`.
   - Masukkan dan terapkan kupon secara bergantian (sistem hanya memeriksa apakah kupon yang dimasukkan sama persis dengan kupon terakhir, sehingga pergantian kode kupon akan lolos validasi berulang kali):

   ```text
   NEWCUST5 -> SIGNUP30 -> NEWCUST5 -> SIGNUP30 -> ...
   ```

3. **Ulangi Sebanyak 14 Kali (7 Pasang):**

   | Urutan | Kupon | Harga |
   | --- | --- | --- |
   | 0 | - | $1337.00 |
   | 1 | NEWCUST5 | $1332.00 |
   | 2 | SIGNUP30 | $932.40 |
   | 3 | NEWCUST5 | $927.40 |
   | 4 | SIGNUP30 | $649.18 |
   | 5 | NEWCUST5 | $644.18 |
   | 6 | SIGNUP30 | $450.93 |
   | 7 | NEWCUST5 | $445.93 |
   | 8 | SIGNUP30 | $312.15 |
   | 9 | NEWCUST5 | $307.15 |
   | 10 | SIGNUP30 | $215.00 |
   | 11 | NEWCUST5 | $210.00 |
   | 12 | SIGNUP30 | $147.00 |
   | 13 | NEWCUST5 | $142.00 |
   | 14 | SIGNUP30 | $99.40 |

4. **Checkout & Bukti Pembelian (Receipt):**
   - Setelah harga total tagihan turun menjadi **$99.40** (di bawah batas kredit $100.00), klik tombol **Place order** (Checkout).
   - Sistem menerbitkan struk pembelian resmi (*official purchase receipt*) dan sertifikat kepemilikan kartu yang menampilkan kode lisensi / flag Lab 6.

**Payload inti:** Terapkan kode `NEWCUST5` dan `SIGNUP30` secara berselang-seling sebanyak 14 kali di form kupon `{URL}/lab6/cart`, kemudian klik *Place order*.

**Mengapa berhasil:**
Sistem hanya memvalidasi apakah kode kupon yang baru diterapkan sama dengan kupon terakhir yang diterapkan (`code == last_coupon`). Tidak ada batasan frekuensi total pemakaian kupon per transaksi, tidak ada pembatasan penumpukan kupon berlainan jenis, dan kupon diskon persentase dihitung ulang terhadap saldo sisa diskon sebelumnya sehingga harga terdiskon secara geometris hingga berada di bawah batas saldo kredit.

**Perbaikan:**
1. Batasi maksimal 1 kode promo per transaksi checkout.
2. Catat riwayat penggunaan kupon per akun pengguna untuk mencegah kupon pendaftaran baru/newsletter digunakan berulang kali.
3. Tentukan aturan penumpukan kupon (*coupon stacking rules*) secara eksplisit di logika backend bila ingin mendukung lebih dari satu promo.
4. Lakukan kalkulasi harga akhir murni di server dengan basis harga katalog resmi tanpa mengizinkan iterasi penumpukan bebas.

---

## Verifikasi Cepat

| Lab | Bukti berhasil |
| --- | --- |
| 1 | Produk `Prototype Gadget` tampil dan deskripsinya memuat flag |
| 2 | Pesan login administrator dan flag tampil setelah payload username |
| 3 | Saldo berkurang sesuai harga yang diubah dan flag tampil |
| 4 | Total keranjang $27.00 dan flag tampil setelah checkout |
| 5 | Halaman `/lab5/admin` dapat dibuka setelah email diubah |
| 6 | Harga menjadi $99.40 dan flag tampil setelah checkout |

Untuk mengulang pengujian dari awal, buka `{URL}/reset` atau jalankan ulang
container lab. Jangan lupa mengganti flag sebelum lomba dimulai.
