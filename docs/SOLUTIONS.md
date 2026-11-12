# Kunci Jawaban Lengkap Lab CTF Nusatech

> 🔒 **DOKUMEN KHUSUS PENGAJAR / ADMINISTRATOR CTF**  
> Dilarang membagikan dokumen ini kepada peserta lomba. File ini dikecualikan dari Docker build image melalui konfigurasi `.dockerignore`.

---

## Lab 1 — Nusatech: Katalog Khusus (SQLi WHERE Clause)

- **Celah:** SQL Injection pada Klausa WHERE
- **Tujuan:** Menampilkan produk prototipe yang belum dirilis (`released = 0`) dan mendapatkan `FLAG_1` yang tersimpan pada deskripsi produk tersebut.
- **Langkah Eksploitasi:**
  1. Buka browser ke alamat `http://IP-SERVER:8011/lab1`.
  2. Perhatikan filter kategori yang tersedia di halaman katalog (misalnya filter `Elektronik`).
  3. Masukkan payload berikut pada input pencarian/filter kategori:
     ```sql
     Elektronik' OR 1=1--
     ```
     Atau jika diakses langsung melalui parameter query URL:
     ```text
     http://IP-SERVER:8011/lab1?category=Elektronik%27+OR+1%3D1--
     ```
  4. Halaman akan menampilkan seluruh produk di database, termasuk **Prototipe Sensor Cuaca v3** (`released=0`). Flag tertera pada deskripsi produk tersebut.
- **Akar Masalah:**
  Query SQL pada fungsi `lab1()` dibentuk menggunakan format string tanpa sanitasi:
  ```python
  f"SELECT * FROM products WHERE category = '{cat}' AND released = 1"
  ```
  Payload `Elektronik' OR 1=1--` mengubah query menjadi:
  ```sql
  SELECT * FROM products WHERE category = 'Elektronik' OR 1=1--' AND released = 1
  ```
  Kondisi `OR 1=1` selalu bernilai TRUE untuk setiap baris, sementara tanda `--` mematikan sisa filter `AND released = 1`.
- **Rekomendasi Perbaikan:**
  Gunakan query berparameter (*parameterized query*):
  ```python
  db.execute("SELECT * FROM products WHERE category = ? AND released = 1", (cat,))
  ```

---

## Lab 2 — Nusatech: Pintu Belakang Manajer (SQLi Login Bypass)

- **Celah:** SQL Injection pada Mekanisme Autentikasi
- **Tujuan:** Masuk sebagai administrator utama (`admin_utama`) tanpa mengetahui kata sandinya untuk mendapatkan `FLAG_2`.
- **Langkah Eksploitasi:**
  1. Buka browser ke alamat `http://IP-SERVER:8012/lab2`.
  2. Pada kolom **Nama Pengguna (Username)**, masukkan payload:
     ```text
     admin_utama'--
     ```
  3. Pada kolom **Kata Sandi (Password)**, isi dengan karakter sembarang (misalnya: `123`).
  4. Klik tombol **Masuk Sekarang**.
  5. Sistem akan menampilkan Dashboard Administrator Utama dengan token verifikasi `FLAG_2`.
- **Akar Masalah:**
  String formulir login digabungkan langsung ke dalam query autentikasi:
  ```python
  f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
  ```
  Payload menghasilkan:
  ```sql
  SELECT * FROM users WHERE username = 'admin_utama'--' AND password = '123'
  ```
  Karakter `--` mengabaikan seluruh pengecekan password, sehingga database mengembalikan baris user `admin_utama`.
- **Rekomendasi Perbaikan:**
  Gunakan *parameterized query* serta simpan kata sandi dalam bentuk *hash* yang aman (misalnya bcrypt/Argon2/PBKDF2 via `werkzeug.security`).

---

## Lab 3 — Nusatech: Diskon Mandiri (Excessive Trust in Client-Side Controls)

- **Celah:** Ketergantungan Berlebihan pada Kontrol Sisi Klien (*Hidden Field Tampering*)
- **Tujuan:** Membeli **Drone Elang X200** seharga $1.249,00 dengan modal saldo awal yang hanya $100.00 untuk mendapatkan `FLAG_3`.
- **Langkah Eksploitasi:**
  1. Buka browser ke alamat `http://IP-SERVER:8013/lab3`.
  2. Buka fitur *Developer Tools* browser (tekan `F12` atau klik kanan &rarr; *Inspect* pada kartu produk **Drone Elang X200**).
  3. Temukan elemen formulir tersembunyi pada kartu Drone:
     ```html
     <input type="hidden" name="price" value="1249.00">
     ```
  4. Ubah atribut `value` tersebut menjadi nominal kecil yang terjangkau oleh saldo Anda, misalnya:
     ```html
     <input type="hidden" name="price" value="1.00">
     ```
  5. Klik tombol **Tambah ke Keranjang**. Drone akan masuk ke keranjang belanja dengan harga satuan $1.00.
  6. *(Opsional)* Anda dapat menambahkan barang belanjaan lain ke dalam keranjang.
  7. Pada bagian tabel **Keranjang Penawaran Anda**, klik tombol **Konfirmasi & Bayar Pesanan**.
  8. Karena total belanja ($1.00) lebih kecil atau sama dengan saldo akun ($100.00), transaksi berhasil divalidasi dan `FLAG_3` akan muncul di notifikasi sukses.
- **Akar Masalah:**
  Server membaca dan memercayai parameter `price` yang dikirimkan oleh browser klien tanpa memverifikasinya kembali ke katalog database master.
- **Rekomendasi Perbaikan:**
  Hanya kirimkan `product_id` dari browser. Nilai harga resmi harus selalu ditarik dan dihitung dari database sisi server.

---

## Lab 4 — Nusatech: Keranjang Ajaib (Negative Quantity Logic Flaw)

- **Celah:** Celah Logika Bisnis Kuantitas Nilai Negatif
- **Tujuan:** Membeli **Drone Elang X200** ($1.249,00) dengan saldo $100.00 melalui manipulasi nilai total keranjang belanja menggunakan kuantitas negatif untuk mendapatkan `FLAG_4`.
- **Langkah Eksploitasi:**
  1. Buka browser ke alamat `http://IP-SERVER:8014/lab4`.
  2. Pada kartu produk **Drone Elang X200** ($1.249,00), masukkan jumlah `1`, lalu klik **Masukkan**. Subtotal keranjang saat ini adalah `$1.249,00`.
  3. Cari produk dengan harga murah, misalnya **Earbuds Gema Pro** ($42,00).
  4. Kita membutuhkan pengurangan sebesar minimal `$1.150,00` agar total belanja menjadi `$100,00` atau kurang.
     - Hitungan: $1.249 - ($42 × 28) = $1.249 - $1.176 = **$73.00**.
  5. Pada produk Earbuds Gema Pro, ubah jumlah input menjadi angka negatif: `-28`.
  6. Klik tombol **Masukkan**.
  7. Periksa tabel keranjang belanja:
     - Drone Elang X200: 1 unit &times; $1.249,00 = $1.249,00
     - Earbuds Gema Pro: -28 unit &times; $42,00 = -$1.176,00
     - **Total Tagihan: $73.00**
  8. Karena total tagihan ($73.00) berada di dalam rentang saldo ($0.00 &le; Total &le; $100.00) dan keranjang memuat Drone Elang X200 dengan kuantitas > 0, klik **Selesaikan Pesanan**.
  9. Transaksi berhasil dan notifikasi pesanan menampilkan `FLAG_4`.
- **Akar Masalah:**
  Server mengonversi input `qty` menjadi integer namun tidak memvalidasi batasan nilai minimum (`qty > 0`).
- **Rekomendasi Perbaikan:**
  Tolak setiap input kuantitas yang bernilai kurang dari atau sama dengan nol:
  ```python
  if qty is None or qty <= 0:
      flash("Kuantitas produk harus berupa angka positif.", "error")
  ```

---

## Lab 5 — Nusatech: Akses Internal Staf (Inconsistent Access Control)

- **Celah:** Inkonsistensi Validasi Domain pada Fitur Profil Pengguna
- **Tujuan:** Mendapatkan akses ke Portal Manajemen Staf Internal (`/lab5/internal`) yang dibatasi hanya untuk pemegang email berdomain `@nusatech.internal` untuk mendapatkan `FLAG_5`.
- **Langkah Eksploitasi:**
  1. Buka browser ke alamat `http://IP-SERVER:8015/lab5`.
  2. Pada formulir **Daftar Anggota Baru**, masukkan:
     - Nama Pengguna: `peserta1`
     - Alamat Email: `peserta1@gmail.com` (gunakan email publik biasa)
     - Kata Sandi: `password123`
  3. Klik **Daftar Akun Baru**. *(Catatan: jika Anda mencoba mendaftar dengan email `@nusatech.internal`, sistem akan menolak).*
  4. Masuk melalui formulir **Masuk ke Akun Member** menggunakan akun yang baru dibuat.
  5. Setelah berhasil masuk ke dashboard **Profil Pengguna Terdaftar**, temukan formulir **Perbarui Alamat Email**.
  6. Ubah alamat email menjadi alamat internal staf, misalnya:
     ```text
     peserta1@nusatech.internal
     ```
  7. Klik **Simpan Perubahan Email**. Sistem akan memperbarui email tanpa memblokir domain internal.
  8. Klik tombol **Buka Panel Internal &rarr;** atau buka URL `http://IP-SERVER:8015/lab5/internal`.
  9. Halaman Portal Manajemen Staf Internal akan terbuka dan menyajikan `FLAG_5`.
- **Akar Masalah:**
  Aturan bisnis yang melarang pendaftaran domain `@nusatech.internal` hanya diterapkan pada endpoint registrasi (`/lab5/register`), namun diabaikan pada endpoint pembaruan email (`/lab5/update-email`).
- **Rekomendasi Perbaikan:**
  Terapkan logika validasi domain yang seragam dan tersentralisasi pada seluruh endpoint yang memodifikasi data email pengguna, atau wajibkan verifikasi email berbasis token sebelum domain diaktifkan.

---

## Lab 6 — Nusatech: Promo Berantai (Flawed Business Rule Enforcement)

- **Celah:** Penegakan Aturan Kupon Promosi yang Tidak Tuntas (*State Validation Flaw*)
- **Tujuan:** Menumpuk kupon diskon secara bergantian hingga harga **Drone Elang X200** ($1.249,00) turun di bawah saldo akun ($100.00) untuk mendapatkan `FLAG_6`.
- **Langkah Eksploitasi:**
  1. Buka browser ke alamat `http://IP-SERVER:8016/lab6`.
  2. Masukkan kode kupon pertama: `HEMAT50`, lalu klik **Terapkan Kupon** (harga turun dari $1249.00 menjadi $1199.00).
  3. Masukkan kode kupon kedua: `DISKON30`, lalu klik **Terapkan Kupon** (harga turun 30% menjadi $839.30).
  4. Masukkan kembali kode kupon: `HEMAT50`, lalu klik **Terapkan Kupon** (harga turun menjadi $789.30).
  5. Lanjutkan pergantian kupon secara berselang-seling:
     - Putaran 3: `DISKON30` &rarr; $552.51, lalu `HEMAT50` &rarr; $502.51
     - Putaran 4: `DISKON30` &rarr; $351.76, lalu `HEMAT50` &rarr; $301.76
     - Putaran 5: `DISKON30` &rarr; $211.23, lalu `HEMAT50` &rarr; $161.23
     - Putaran 6: `DISKON30` &rarr; $112.86, lalu `HEMAT50` &rarr; $62.86
  6. Saat harga telah mencapai **$62.86** (sudah lebih kecil dari batas saldo $100.00), klik tombol **Bayar Sekarang &rarr;**.
  7. Pembayaran berhasil diproses dan notifikasi konfirmasi pesanan menyajikan `FLAG_6`.
- **Akar Masalah:**
  Sistem hanya memeriksa variabel `last_coupon` sesi saat ini:
  ```python
  if code == last_code:
      flash("Kode promosi yang sama tidak dapat digunakan dua kali berturut-turut.", "error")
  ```
  Sistem tidak mencatat riwayat pemakaian kupon dalam bentuk set/daftar (`used_coupons = set()`) yang melarang pemakaian ulang kupon yang pernah diterapkan sebelumnya.
- **Rekomendasi Perbaikan:**
  Simpan daftar semua kupon yang telah diterapkan dalam bentuk riwayat sesi atau database:
  ```python
  used_coupons = session.setdefault("used_coupons", [])
  if code in used_coupons:
      flash("Kupon promosi ini sudah pernah Anda gunakan sebelumnya.", "error")
  else:
      used_coupons.append(code)
  ```
