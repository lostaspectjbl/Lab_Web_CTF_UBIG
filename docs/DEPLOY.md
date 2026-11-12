# Panduan Deployment Server Linux & aaPanel

Panduan langkah demi langkah untuk mengunggah repositori soal CTF Nusatech ke GitHub pribadi, men-deploy pada server Linux dengan panel aaPanel, melakukan verifikasi, dan mengamankan akses publik.

---

## 1. Unggah Repositori ke GitHub Pribadi

Lakukan langkah ini di **Komputer Lokal** Anda:

> ⚠️ **Pastikan repositori disetel sebagai PRIVATE** agar peserta lomba tidak dapat melihat kode sumber maupun kunci jawaban.

1. Buka [GitHub](https://github.com), buat repositori baru dengan nama misalnya `ctf-nusatech-labs`, dan pilih **Private**.
2. Di terminal komputer lokal pada folder proyek `c:\Soal WEb` (atau path folder proyek Anda):

```bash
# [Terminal Komputer Lokal]
# Inisialisasi Git dan tambahkan remote repositori GitHub Anda
git remote add origin https://github.com/USERNAME-ANDA/ctf-nusatech-labs.git

# Pastikan branch utama bernama main
git branch -M main

# Unggah seluruh kode ke branch main
git push -u origin main
```
*Catatan:* Jika diminta autentikasi kata sandi oleh Git, gunakan **Personal Access Token (Classic)** dengan hak akses `repo` yang dapat dibuat melalui menu *GitHub Settings &rarr; Developer Settings &rarr; Personal access tokens*.

---

## 2. Pemasangan & Konfigurasi di Server (aaPanel)

Lakukan langkah ini melalui **Terminal SSH Server** (misalnya via PuTTY, Terminal VSCode SSH, atau fitur Terminal di dashboard aaPanel):

### Langkah 2.1: Kloning Repositori ke Direktori Server
Target direktori yang disepakati adalah `/www/ctf-labs`:

```bash
# [Terminal Server SSH]
# Masuk ke direktori web aaPanel
cd /www

# Unduh repositori privat menggunakan Personal Access Token Anda
git clone https://USERNAME-ANDA:TOKEN-GITHUB@github.com/USERNAME-ANDA/ctf-nusatech-labs.git ctf-labs

# Masuk ke direktori project yang baru diunduh
cd /www/ctf-labs
```

### Langkah 2.2: Konfigurasi File Lingkungan (.env)
File `.env` berisi nilai rahasia seperti kunci sesi Flask dan flag yang akan dibaca oleh platform CTFd:

```bash
# [Terminal Server SSH]
# Salin template konfigurasi lingkungan
cp .env.example .env

# Edit file .env menggunakan text editor nano
nano .env
```

Untuk menghasilkan string acak yang aman sebagai `SECRET_KEY_1` sampai `SECRET_KEY_6`, Anda dapat menjalankan perintah OpenSSL berikut di baris perintah:

```bash
# [Terminal Server SSH]
# Contoh perintah pembuat kunci rahasia acak 32 karakter
openssl rand -hex 16
```

Contoh isi file `.env` di server produksi:
```ini
SECRET_KEY_1=a3f9c812d4b7e651908a2c4e6f1837b2
SECRET_KEY_2=91b4e2c7a8d5f30614e892c57b1049fa
SECRET_KEY_3=e72c5b9014a8f3d6b1297e54c8a160df
SECRET_KEY_4=08b3a7f2e1c9d4659b8a1c3e5d7204fa
SECRET_KEY_5=3c9e1fa74d82b056e1824a7c9d05f31b
SECRET_KEY_6=b8104e7a2d9c3f6514e802a57c913bfa

FLAG_1=CTF{nusatech_sqli_where_clause_retrieval_89f3}
FLAG_2=CTF{nusatech_sqli_auth_bypass_admin_panel_10d2}
FLAG_3=CTF{nusatech_client_price_tampering_trust_4b71}
FLAG_4=CTF{nusatech_high_level_logic_negative_qty_992a}
FLAG_5=CTF{nusatech_inconsistent_email_control_b831}
FLAG_6=CTF{nusatech_flawed_promo_enforcement_chain_7c0e}
```
*(Tekan `CTRL + O` lalu `Enter` untuk menyimpan, kemudian `CTRL + X` untuk keluar dari nano).*

### Langkah 2.3: Build Image dan Jalankan Container
Jalankan Docker Compose untuk membangun image dan mengaktifkan 6 container lab:

```bash
# [Terminal Server SSH]
docker compose up -d --build
```
*Jika server Anda masih menggunakan Docker Compose versi lama (v1), gunakan perintah:*
```bash
docker-compose up -d --build
```

---

## 3. Verifikasi Status & Uji Coba Layanan

Setelah proses build selesai, pastikan seluruh container berjalan dengan semestinya:

### Langkah 3.1: Periksa Daftar Container
```bash
# [Terminal Server SSH]
docker compose ps
```
Pastikan status seluruh container `nusatech-lab1` sampai `nusatech-lab6` berada pada kondisi `Up` (berjalan) dan memetakan port `0.0.0.0:8011-8016->5000/tcp`.

### Langkah 3.2: Uji Respon Pengalihan Root (HTTP 302)
Setiap lab harus otomatis mengalihkan permintaan root `/` ke endpoint spesifiknya:

```bash
# [Terminal Server SSH]
# Uji port 8011 sampai 8016 (seluruhnya harus menghasilkan status HTTP 302 Found)
for port in {8011..8016}; do
  curl -s -o /dev/null -w "Port $port: HTTP %{http_code}\n" http://127.0.0.1:$port/
done
```
Output yang diharapkan:
```text
Port 8011: HTTP 302
Port 8012: HTTP 302
Port 8013: HTTP 302
Port 8014: HTTP 302
Port 8015: HTTP 302
Port 8016: HTTP 302
```

### Langkah 3.3: Uji Eksploitasi Pembuktian (Proof-of-Concept Lab 1)
Jalankan satu perintah curl untuk membuktikan bahwa celah SQL Injection pada Lab 1 bekerja dan menampilkan flag yang telah dikonfigurasi:

```bash
# [Terminal Server SSH]
curl -s "http://127.0.0.1:8011/lab1?category=Elektronik'+OR+1=1--" | grep -o 'CTF{[^}]*}'
```
Jika berhasil, terminal server akan langsung mencetak string flag Lab 1 Anda.

---

## 4. Konfigurasi Akses dari Luar (Public Access)

Pilih salah satu dari dua metode di bawah ini sesuai arsitektur jaringan Anda:

### Opsi A: Akses Langsung Menggunakan Port Host (Port 8011-8016)
Paling sederhana dan cepat jika peserta mengakses via alamat IP atau subdomain utama:
1. **Buka Port di Panel aaPanel**:
   - Masuk ke dashboard aaPanel web Anda (`http://IP-SERVER:8888`).
   - Buka menu **Security** pada bilah sisi kiri.
   - Pada bagian **Firewall Rules**, tambahkan port `8011:8016` (TCP), beri keterangan *"CTF Labs Nusatech"*, lalu klik **Add**.
2. **Buka Port di Cloud Provider (Security Group)**:
   - Jika server Anda berada di AWS, GCP, DigitalOcean, Alibaba Cloud, atau provider VPS lainnya, buka pengaturan firewall / Security Group VPS Anda.
   - Tambahkan Inbound Rule: Protokol **TCP**, Port Range **8011-8016**, Source **0.0.0.0/0** (Anywhere).
3. Tautan untuk peserta lomba:
   - Lab 1: `http://IP-SERVER:8011`
   - Lab 2: `http://IP-SERVER:8012`
   - ... dan seterusnya hingga port `8016`.

### Opsi B: Menggunakan Subdomain & Reverse Proxy aaPanel + SSL (Rekomendasi)
Paling rapi dan profesional jika Anda memiliki domain resmi (misal: `domainctf.id`):
1. **Buat DNS Record A**:
   - Di DNS manager (Cloudflare/Namecheap/dll), arahkan subdomain ke IP server:
     - `lab1.domainctf.id` &rarr; IP-SERVER
     - `lab2.domainctf.id` &rarr; IP-SERVER
     - ... hingga `lab6.domainctf.id`.
2. **Ubah Binding docker-compose.yml agar Tidak Terbuka Langsung ke Publik**:
   - Ubah pemetaan port di `docker-compose.yml` menjadi `127.0.0.1:8011:5000` (agar hanya dapat diakses secara lokal oleh Nginx Reverse Proxy).
   - Jalankan `docker compose up -d` untuk menerapkan perubahan.
3. **Tambahkan Website & Reverse Proxy di aaPanel**:
   - Masuk ke menu **Website** di aaPanel, klik **Add Site**.
   - Masukkan Domain: `lab1.domainctf.id`, pilih PHP Version: *Pure Python/Static*.
   - Setelah site terbentuk, klik nama domain tersebut &rarr; buka tab **Reverse Proxy** &rarr; klik **Add Reverse Proxy**:
     - Proxy Name: `lab1-proxy`
     - Target URL: `http://127.0.0.1:8011`
     - Sent Domain: `$host`
     - Klik **Save**.
   - Buka tab **SSL** di konfigurasi website yang sama, centang Let's Encrypt, lalu klik **Apply** untuk mengaktifkan HTTPS gratis.
   - Ulangi langkah serupa untuk `lab2` s/d `lab6`.

---

## 5. Pemeliharaan & Perawatan Berkala

### Memperbarui Kode (Update):
Jika terdapat perbaikan kode di komputer lokal dan telah di-push ke GitHub:
```bash
# [Terminal Server SSH]
cd /www/ctf-labs
git pull
docker compose up -d --build
```

### Memeriksa Log Container:
Jika ada peserta yang melaporkan kendala pada lab tertentu:
```bash
# [Terminal Server SSH]
# Lihat log seluruh container secara real-time
docker compose logs -f

# Atau lihat log spesifik salah satu container (misal Lab 3)
docker compose logs -f lab3
```

### Merestart Satu Lab:
Jika database salah satu lab perlu di-reset atau container mengalami kendala:
```bash
# [Terminal Server SSH]
docker compose restart lab2
```

### Menghentikan Semua Lab:
Setelah kompetisi CTF selesai:
```bash
# [Terminal Server SSH]
docker compose down
```

---

## 6. Panduan Troubleshooting

| Gejala Masalah | Penyebab Umum | Solusi Perbaikan |
| :--- | :--- | :--- |
| **Container berstatus *Exit (1)*** | Variabel lingkungan pada `.env` belum diisi atau salah penulisan nama variabel. | Periksa log dengan `docker compose logs labN`. Pastikan seluruh `SECRET_KEY_1..6` dan `FLAG_1..6` memiliki nilai di `.env`. |
| **Error *port is already allocated*** | Port 8011-8016 telah digunakan oleh proses lain di host. | Cek proses yang menduduki port: `sudo lsof -i :8011` atau `sudo netstat -tlpn \| grep 8011`. Matikan proses tersebut atau ubah port host di `docker-compose.yml`. |
| **Bisa di-curl dari lokal server, tapi tidak bisa dibuka dari browser peserta** | Firewall server atau Security Group cloud provider masih memblokir port 8011-8016. | Buka menu Security di aaPanel dan tambahkan port `8011:8016`. Pastikan juga panel cloud provider (AWS/DigitalOcean Security Group) mengizinkan inbound traffic ke port tersebut. |
| **Data peserta bercampur atau sesi tertukar** | Dua peserta berbagi browser yang sama tanpa menggunakan mode penyamaran (*Incognito*). | Sesi peserta disimpan via cookie sesi terenkripsi. Peserta cukup mengklik link **Reset Sesi** pada navbar untuk mengosongkan keranjang dan saldo mereka. |
