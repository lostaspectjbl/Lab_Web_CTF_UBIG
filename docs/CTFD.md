# Bahan Challenge untuk CTFd

Dokumen ini berisi nama soal, deskripsi, dan hint yang siap disalin ke CTFd.
Ganti `{URL}` dengan alamat lab yang bisa diakses peserta, misalnya
`http://IP-SERVER:8011` untuk Lab 1.

## Ringkasan

| Lab | Nama soal | Kategori | Poin | Endpoint |
| --- | --- | --- | --- | --- |
| 1 | Toko Kategori | Web | 30 | `{URL}/lab1` |
| 2 | Login Administrator | Web | 40 | `{URL}/lab2` |
| 3 | Harga Spesial | Web | 40 | `{URL}/lab3` |
| 4 | Keranjang Ajaib | Web | 60 | `{URL}/lab4` |
| 5 | Email Perusahaan | Web | 60 | `{URL}/lab5` |
| 6 | Kupon Berlapis | Web | 70 | `{URL}/lab6` |

Format flag: `CTF{...}`. Nilai flag harus sama dengan `FLAG_n` di `.env`
container yang bersangkutan. Jangan pernah menulis flag asli di dokumen ini.

## Cara Membuat di CTFd

1. Login sebagai admin, buka **Admin Panel > Challenges > Create Challenge**.
2. Isi **Name**, pilih **Category: Web**, dan tempel **Description** dari
   bagian di bawah.
3. Pada **Flags**, pilih tipe **static**, lalu isi nilai `FLAG_n` yang dipakai
   server. Jangan pakai flag contoh dari repo.
4. Tambahkan tiga **Hint** dengan biaya yang disarankan. Hint pertama gratis,
   hint kedua dan ketiga berbayar agar peserta berpikir dulu.
5. Simpan, lalu ulangi untuk Lab 2 sampai Lab 6.
6. Uji dengan akun peserta: buka challenge, pastikan URL benar, dan pastikan
   flag yang diterima CTFd cocok dengan flag di environment container.

Tips: satu subdomain per lab lebih rapi daripada satu port per lab. Jika
memakai port, pastikan semua port 8011-8016 terbuka di firewall.

## Lab 1 - Toko Buku & Manuskrip Rahasia (30 poin)

**Deskripsi:**

```text
Toko buku online di {URL}/lab1 menyediakan filter kategori novel. Katalog
hanya menampilkan buku-buku yang telah dirilis secara resmi. Namun, ada rumor
bahwa seorang penulis legendaris menyimpan draf manuskrip rahasia yang belum
pernah dirilis dan menyelipkan sesuatu di deskripsinya.

Celahnya ada pada cara filter kategori disusun di backend. Bisakah kamu
menemukan draf novel rahasia tersebut?
```

**Hint:**

1. (0 poin) Coba masukkan kategori yang ada (misal Mystery & Thriller atau Gifts),
   lalu perhatikan bagaimana hasilnya berubah saat kamu menambahkan karakter kutip.
2. (10 poin) Server menempelkan input kategori langsung ke dalam query SQL.
   Pikirkan cara membuat kondisi `WHERE` selalu bernilai benar.
3. (20 poin) Kamu tidak perlu mengetahui judul bukunya. Buat semua baris
   lolos filter, termasuk yang `released = 0`, lalu baca deskripsinya.

## Lab 2 - Portal E-Rapor Sekolah (40 poin)

**Deskripsi:**

```text
Portal E-Rapor Akademik di {URL}/lab2 digunakan untuk mengelola nilai rapor siswa.
Halaman login guru dan administrator memiliki kelemahan pada penyusunan query SQL.
Akun biasa seperti guru (wiener:peter) tidak memiliki hak akses mengubah nilai.

Tugasmu:
1. Masuk sebagai Administrator Kurikulum (administrator) menggunakan SQL Injection pada form login.
2. Temukan siswa yang masih berstatus Remedial (misal: Budi Santoso) dan perbarui nilainya agar Tuntas (nilai >= 75).
3. Flag akan langsung terbit setelah perubahan nilai rapor berhasil disimpan.
```

**Hint:**

1. (0 poin) Login dengan akun guru penguji `wiener:peter` berhasil, tetapi tidak memiliki hak mengubah nilai rapor siswa.
2. (10 poin) Query SQL login disusun dengan string formatting: `SELECT username FROM users WHERE username='...' AND password='...'`. Gunakan karakter kutip tunggal dan komentar `--` pada kolom username untuk mengabaikan password.
3. (20 poin) Masukkan `administrator'--` pada kolom username dan isi password dengan sembarang karakter. Setelah masuk ke Panel Administrator, ubah nilai salah satu siswa yang remedial menjadi tuntas (misal 85) untuk mendapatkan flag.

## Lab 3 - Harga Spesial (40 poin)

**Deskripsi:**

```text
Toko di {URL}/lab3 memberimu kredit $100. Jaket kulit di sana berharga $1337,
jadi mustahil dibeli dengan saldo normal.

Kabarnya harga dikirim dari browser lewat input tersembunyi. Tentukan sendiri
harga yang pantas untuk jaket itu dan dapatkan flag-nya.
```

**Hint:**

1. (0 poin) Inspect elemen form pembelian. Ada field yang tidak terlihat di
   halaman.
2. (10 poin) Server memakai harga yang dikirim browser, bukan harga di katalog.
   Ubah nilainya sebelum submit.
3. (20 poin) Harga harus tetap non-negatif dan tidak melebihi saldo. Coba
   angka yang sangat kecil tetapi masih diterima.

## Lab 4 - Keranjang Ajaib (60 poin)

**Deskripsi:**

```text
Keranjang belanja di {URL}/lab4 menerima jumlah barang dari form. Kreditmu
$100, sedangkan jaketnya $1337. Tidak ada diskon resmi di toko ini.

Namun, keranjang tampaknya percaya pada angka yang kamu kirim. Buat total
belanja menjadi masuk akal tanpa menambah saldo, lalu checkout.
```

**Hint:**

1. (0 poin) Coba tambahkan jaket dan satu barang murah. Perhatikan total di
   keranjang.
2. (10 poin) Berapa yang terjadi jika jumlah barang negatif? Apakah server
   memeriksa batas bawah?
3. (20 poin) Jaket harus tetap ada di keranjang dengan jumlah positif. Tambahkan
   barang murah dengan jumlah negatif yang cukup untuk menurunkan total di
   bawah $100.

## Lab 5 - Email Perusahaan (60 poin)

**Deskripsi:**

```text
Portal member di {URL}/lab5 melarang pendaftaran dengan email
`@ctf-corp.com`, karena domain itu khusus karyawan. Di baliknya ada halaman
admin yang hanya mau membuka pintu untuk email perusahaan.

Apakah larangan saat mendaftar benar-benar cukup?
```

**Hint:**

1. (0 poin) Daftar dengan email biasa, login, lalu lihat halaman
   `{URL}/lab5/admin`. Apa yang terjadi?
2. (10 poin) Ada endpoint untuk mengubah email setelah login. Periksa apakah
   endpoint itu melakukan pengecekan domain yang sama seperti saat daftar.
3. (20 poin) Daftar dengan email non-perusahaan, login, ubah email menjadi
   alamat `@ctf-corp.com`, lalu buka halaman admin.

## Lab 6 - Kupon Berlapis (70 poin)

**Deskripsi:**

```text
Toko di {URL}/lab6 menjual jaket seharga $1337. Ada dua kupon promosi:

- `NEWCUST5` : potongan $5
- `SIGNUP30` : diskon 30%

Aturannya hanya satu: kupon yang sama tidak boleh dipakai dua kali
berturut-turut. Kreditmu $100. Turunkan harga jaket sampai bisa checkout.
```

**Hint:**

1. (0 poin) Coba satu kupon, lalu checkout. Perhatikan harga dan pesan yang
   muncul.
2. (10 poin) Aturan hanya membandingkan kupon dengan kupon terakhir. Apakah
   kupon berbeda boleh ditumpuk tanpa batas?
3. (20 poin) Gantilah kedua kupon secara bergantian. Diskon persen akan
   memperkecil efek potongan tetap, jadi urutan pemakaian berpengaruh.

## Catatan Keamanan

- Jangan menaruh `docs/SOLUTIONS.md` di server challenge atau membagikannya
  kepada peserta.
- Jangan memakai flag contoh `CTF{dev_only_lab_N}` untuk lomba.
- Simpan `.env` dengan permission `600` dan jangan commit ke Git.
- Setiap container hanya mengaktifkan satu lab, sehingga peserta tidak bisa
  berpindah lab lewat URL yang sama.
