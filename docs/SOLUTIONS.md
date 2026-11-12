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

## Lab 1 - Toko Kategori (SQL Injection)

**Tujuan:** menampilkan produk yang belum dirilis dan membaca flag di
deskripsinya.

**Langkah:**

1. Buka `{URL}/lab1`.
2. Coba filter kategori normal, misalnya `Gifts`. Hanya produk yang sudah
   dirilis yang tampil.
3. Masukkan payload berikut pada kolom kategori:

   ```text
   Gifts' OR 1=1--
   ```

   Jika dikirim lewat URL, bentuk terenkodenya adalah:

   ```text
   {URL}/lab1?category=Gifts%27%20OR%201%3D1--
   ```

4. Semua produk, termasuk `Prototype Gadget`, akan tampil. Flag ada pada
   deskripsi produk tersebut.

**Payload inti:** `Gifts' OR 1=1--`

**Mengapa berhasil:** input kategori disisipkan langsung ke query:

```sql
SELECT name, price, description FROM products
WHERE category='Gifts' OR 1=1--' AND released=1
```

Bagian `OR 1=1` membuat kondisi selalu benar, sedangkan `--` mengabaikan sisa
query termasuk `AND released=1`.

**Perbaikan:** gunakan parameterized query (`WHERE category = ? AND released = 1`)
dan, bila perlu, validasi kategori terhadap daftar nilai yang diizinkan.

---

## Lab 2 - Login Administrator (SQL Injection)

**Tujuan:** masuk sebagai `administrator` tanpa mengetahui password-nya.

**Langkah:**

1. Buka `{URL}/lab2`.
2. Isi kolom username dengan:

   ```text
   administrator'--
   ```

3. Isi kolom password dengan sembarang nilai, misalnya `x`.
4. Submit. Halaman menampilkan flag Lab 2.

**Payload inti:** username `administrator'--`, password bebas.

**Mengapa berhasil:** query dibentuk dengan penggabungan string:

```sql
SELECT username FROM users
WHERE username='administrator'--' AND password='x'
```

`--` mengomentari pengecekan password, sehingga query hanya mencari username
`administrator`.

**Perbaikan:** gunakan parameterized query, simpan password sebagai hash
(misalnya `werkzeug.security`), dan jangan pernah menyusun query dengan
interpolasi string.

---

## Lab 3 - Harga Spesial (Manipulasi Hidden Input)

**Tujuan:** membeli jaket seharga $1337 dengan kredit $100.

**Langkah:**

1. Buka `{URL}/lab3`.
2. Inspect elemen form jaket. Ada dua input tersembunyi: `pid` dan `price`.
3. Ubah `value` pada input `price` dari `1337.00` menjadi `1`.
4. Submit form. Saldo berkurang $1 dan flag Lab 3 muncul.

**Payload inti:** `price=1` pada form pembelian `pid=1`.

**Mengapa berhasil:** server memakai harga yang dikirim browser. Validasi hanya
memeriksa `price >= 0` dan `price <= saldo`, bukan kecocokan dengan harga
katalog.

**Perbaikan:** abaikan harga dari client. Ambil harga dari database berdasarkan
`pid`, hitung di server, dan gunakan tipe uang yang aman (misalnya integer
sen).

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

## Lab 5 - Email Perusahaan (Business Logic)

**Tujuan:** membuka halaman admin yang hanya menerima email `@ctf-corp.com`.

**Langkah:**

1. Buka `{URL}/lab5`.
2. Daftar dengan email biasa, misalnya:

   ```text
   username: peserta
   password: rahasia123
   email:    peserta@example.com
   ```

   Jika username sudah dipakai, buka `{URL}/reset` lalu ulangi dengan username
   lain.

3. Login dengan akun tersebut.
4. Pada form ubah email, ganti email menjadi:

   ```text
   peserta@ctf-corp.com
   ```

5. Buka `{URL}/lab5/admin`. Flag Lab 5 tampil.

**Payload inti:** email akhir `peserta@ctf-corp.com`.

**Mengapa berhasil:** pengecekan domain hanya dilakukan saat pendaftaran.
Endpoint `update-email` menerima domain apa pun, sedangkan halaman admin hanya
memeriksa email yang tersimpan.

**Perbaikan:** terapkan validasi domain yang sama saat mendaftar dan mengubah
email, verifikasi kepemilikan email melalui token, dan jangan memakai domain
email sebagai satu-satunya penentu hak akses.

---

## Lab 6 - Kupon Berlapis (Logika Diskon)

**Tujuan:** menurunkan harga jaket dari $1337 menjadi maksimal $100.

**Langkah:**

1. Buka `{URL}/lab6`. Harga awal adalah $1337.00.
2. Terapkan kupon secara bergantian, mulai dari `NEWCUST5`:

   ```text
   NEWCUST5, SIGNUP30, NEWCUST5, SIGNUP30, ...
   ```

3. Ulangi sampai 14 kupon (7 pasang). Perhatikan harga setelah setiap kupon:

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

4. Setelah harga $99.40, klik checkout. Flag Lab 6 muncul.

**Payload inti:** gunakan `NEWCUST5` dan `SIGNUP30` secara bergantian sebanyak
14 kali, lalu checkout.

**Mengapa berhasil:** aturan hanya menolak kupon yang sama dengan kupon
terakhir. Tidak ada batas total pemakaian atau aturan bahwa kupon tidak boleh
ditumpuk, sehingga potongan tetap dan diskon persen dapat dikombinasikan
berulang kali.

**Perbaikan:** batasi satu kupon per transaksi atau lacak pemakaian kupon per
pengguna, tentukan aturan penumpukan secara eksplisit, dan hitung harga akhir
sepenuhnya di server.

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
