import datetime
import json
import math
import os
import secrets
import sqlite3
import tempfile

from flask import (
    Blueprint,
    Flask,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template_string,
    request,
    session,
)
from markupsafe import Markup
from werkzeug.security import check_password_hash, generate_password_hash

POKEMON_SHOP = {
    1: ("Charizard Holo 1st Edition", 1337.0, "/static/img/pokemon/charizard.jpg", 5, "Kartu legendaris Charizard Holographic 1st Edition dari Base Set 1999. Kondisi PSA 10 Gem Mint — impian setiap kolektor sejati."),
    2: ("Pikachu Illustrator Promo", 85.0, "/static/img/pokemon/pikachu.jpg", 5, "Kartu promo ultra-langka Pikachu Illustrator dari kontes CoroCoro Comic 1998. Hanya 39 eksemplar di seluruh dunia."),
    3: ("Mewtwo GX Rainbow Rare", 42.50, "/static/img/pokemon/mewtwo.jpg", 4, "Mewtwo GX versi Rainbow Rare dari set Shining Legends. Full-art tekstur holografik premium."),
    4: ("Blastoise Base Set Holo", 72.0, "/static/img/pokemon/blastoise.jpg", 4, "Blastoise Holographic dari Base Set original. Kartu ikonik generasi pertama dengan artwork klasik Ken Sugimori."),
    5: ("Eevee VMAX Alternate Art", 38.0, "/static/img/pokemon/eeveelutions.jpg", 3, "Eevee VMAX Alternate Art dengan ilustrasi memukau — menampilkan Eeveelutions dalam balutan seni eksklusif."),
    6: ("Gengar VMAX Alt Art", 55.0, "/static/img/pokemon/gengar.jpg", 4, "Gengar VMAX alternate art dari Fusion Strike #271. Desain menyeramkan dengan warna ungu gelap yang menawan."),
    7: ("Brilliant Stars Ultra Rare", 90.0, "/static/img/pokemon/brilliant_stars.jpg", 5, "Kartu koleksi Ultra Rare dari set Brilliant Stars yang sangat dicari kolektor."),
    8: ("Booster Pack Evolusi Mega Impian Ex", 4.99, "/static/img/pokemon/booster_pack.jpg", 3, "Paket Pokemon TCG Booster Pack Evolusi Mega Impian Ex (per pack). Dapatkan kesempatan meraih kartu kartu langka!"),
}
SHOP = POKEMON_SHOP
CREDIT = 100.0

LAB_TITLES = {
    1: "PokéCard Collector Shop",
    2: "Masuk ke Akun Anda",
    3: "PokéCard Collector Shop",
    4: "PokéCard Collector Shop",
    5: "Portal Akun Pelanggan",
    6: "Keranjang Belanja",
}

bp = Blueprint("main", __name__)


BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ lab_title }} &middot; Online Store</title>
<link href="/static/css/academyLabHeader.css" rel="stylesheet">
<link href="/static/css/labsEcommerce.css" rel="stylesheet">
<link href="/static/css/labOverrides.css" rel="stylesheet">
<script src="/static/js/labHeader.js"></script>
<style>
/* Refined styling matching PortSwigger Web Security Academy aesthetic */
.flag {
  padding: 0.8em 1.2em;
  border: 1px solid #a5d6a7;
  border-radius: 4px;
  background: #e8f5e9;
  color: #1b5e20;
  font-family: "Courier New", Courier, monospace;
  font-size: 1.05em;
  font-weight: bold;
  word-break: break-all;
  display: inline-block;
  margin: 0.5em 0;
}
.is-linkback {
  display: inline-block;
  color: #0071bc;
  font-weight: bold;
  text-decoration: none;
  margin-bottom: 1em;
}
.is-linkback:hover {
  text-decoration: underline;
}
.tag-badge {
  display: inline-block;
  padding: 3px 8px;
  font-size: 0.72em;
  font-weight: bold;
  border-radius: 3px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
</style>
</head>
<body>
<div theme="ecommerce">

  <section class="maincontainer">
    <div class="container">
      <header class="navigation-header">
        <section class="top-links">
          <a href="{% if lab_num %}/lab{{ lab_num }}{% else %}/{% endif %}">Home</a><p>|</p>
          {% if lab_num == 2 %}
          <a href="/lab2">E-Rapor</a><p>|</p>
          {% if logged_in_user %}
          <a href="/lab2/logout">Log out ({{ logged_in_user }})</a><p>|</p>
          {% endif %}
          {% elif lab_num == 3 %}
          {% if lab3_user %}
          <a href="/lab3">My account</a><p>|</p>
          <a href="/lab3">
            <img src="/static/img/cart_blue.svg" style="height: 16px; vertical-align: middle; margin-right: 4px;">
          </a>
          <p>{{ cart_count if cart_count is defined else 0 }}</p><p>|</p>
          <span style="align-self: center; font-size: 0.95em; color: #555; margin-right: 12px;">Your credit: ${{ "%.2f"|format(balance if balance is defined else 100.0) }}</span>
          <a href="/lab3/logout">Log out ({{ lab3_user }})</a><p>|</p>
          {% else %}
          <a href="/lab3/login">My account</a><p>|</p>
          {% endif %}
          {% elif lab_num == 4 %}
          {% if lab4_user %}
          <a href="/lab4">My account</a><p>|</p>
          <a href="/lab4">
            <img src="/static/img/cart_blue.svg" style="height: 16px; vertical-align: middle; margin-right: 4px;">
          </a>
          <p>{{ cart_count if cart_count is defined else 0 }}</p><p>|</p>
          <span style="align-self: center; font-size: 0.95em; color: #555; margin-right: 12px;">Your credit: ${{ "%.2f"|format(balance if balance is defined else 100.0) }}</span>
          <a href="/lab4/logout">Log out ({{ lab4_user }})</a><p>|</p>
          {% else %}
          <a href="/lab4/login">My account</a><p>|</p>
          {% endif %}
          {% elif lab_num == 5 %}
          {% if member %}
          <a href="/lab5/my-account">My account</a><p>|</p>
          {% if member['is_admin'] %}
          <a href="/lab5/admin-panel" style="color: #d60000; font-weight: bold;">Admin panel</a><p>|</p>
          {% endif %}
          <a href="/lab5/email-client" target="_blank" style="color: #0071bc; font-weight: 600;">Email client</a><p>|</p>
          <a href="/lab5/logout">Log out ({{ member['username'] }})</a><p>|</p>
          {% else %}
          <a href="/lab5/login">My account</a><p>|</p>
          <a href="/lab5/register">Register</a><p>|</p>
          <a href="/lab5/email-client" target="_blank" style="color: #0071bc; font-weight: 600;">Email client</a><p>|</p>
          {% endif %}
          {% elif lab_num == 6 %}
          {% if lab6_user %}
          <a href="/lab6">My account</a><p>|</p>
          <a href="/lab6/cart">
            <img src="/static/img/cart_blue.svg" style="height: 16px; vertical-align: middle; margin-right: 4px;">
          </a>
          <p>{{ session.get('lab6_qty', 1) }}</p><p>|</p>
          <span style="align-self: center; font-size: 0.95em; color: #555; margin-right: 12px;">Your credit: ${{ "%.2f"|format(credit if credit is defined else 100.0) }}</span>
          <a href="/lab6/logout">Log out ({{ lab6_user }})</a><p>|</p>
          {% else %}
          <a href="/lab6/login">My account</a><p>|</p>
          <a href="/lab6/register">Register</a><p>|</p>
          <a href="/lab6/cart">
            <img src="/static/img/cart_blue.svg" style="height: 16px; vertical-align: middle; margin-right: 4px;">
          </a>
          <p>{{ session.get('lab6_qty', 1) }}</p><p>|</p>
          {% endif %}
          {% endif %}
          {% if not config['LAB'] %}
          <a href="/">All Labs</a><p>|</p>
          {% endif %}
          <a href="/reset">Reset</a>
        </section>
      </header>

      <header class="notification-header">
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            <div style="margin: 1em 0;">
            {% for category, message in messages %}
              <div class="flash" style="padding: 0.8em 1.2em; margin-bottom: 0.6em; border-radius: 4px; font-weight: 500; {% if category == 'error' %}background: #fdecea; color: #b50000; border: 1px solid #f5c6cb;{% elif category == 'success' %}background: #e8f5e9; color: #1b5e20; border: 1px solid #a5d6a7;{% else %}background: #e8f1fa; color: #115f82; border: 1px solid #b6d4ec;{% endif %}">
                {{ message }}
              </div>
            {% endfor %}
            </div>
          {% endif %}
        {% endwith %}
      </header>

      {% if lab_num != 2 %}
      <section class="ecoms-pageheader">
        <a href="{% if lab_num %}/lab{{ lab_num }}{% else %}/{% endif %}">
          <img src="/static/img/shop.svg" alt="Online Shop">
        </a>
      </section>
      {% endif %}

      {{ body }}

    </div>
  </section>
  <div class="footer-wrapper">
  </div>
</div>
</body>
</html>
"""


INDEX_BODY = """
<div style="background: #ebf0f2; padding: 2em; border-radius: 5px; margin-bottom: 2em;">
  <h1 style="color: #ff6633; margin-top: 0; font-size: 2em;">Web Security Academy &middot; CTF Practice Labs</h1>
  <p style="font-size: 1.05em; color: #444; line-height: 1.6;">
    Platform latihan keamanan web yang dirancang dengan skenario dan mekanika eksploitasi mirip PortSwigger Web Security Academy.
    Setiap lab memiliki celah keamanan nyata (SQL Injection, Logic Flaws, Broken Access Control) yang dapat di-solve melalui browser maupun tool seperti Burp Suite.
    Pilih lab di bawah ini untuk memulai tantangan!
  </p>
</div>

<section class="container-list-tiles">
  <div style="background: #fff; border: 1px solid #e6e6e6; border-radius: 5px; padding: 1.4em; display: flex; flex-direction: column;">
    <span class="tag-badge" style="background: #ff6633; color: white; align-self: flex-start;">LAB 1 &middot; SQL INJECTION</span>
    <h3 style="margin: 0.8em 0 0.4em; font-size: 1.15em; color: #222;">Toko Kartu Pokémon &amp; Koleksi Rahasia</h3>
    <p style="font-size: 0.9em; color: #666; flex: 1; line-height: 1.5;">SQL injection pada filter kategori WHERE clause untuk menemukan kartu legendaris rahasia di dalam brankas yang belum dirilis ke publik.</p>
    <a class="button" href="/lab1" style="align-self: flex-start; margin-top: 1.2em;">Masuk Lab 1</a>
  </div>
  <div style="background: #fff; border: 1px solid #e6e6e6; border-radius: 5px; padding: 1.4em; display: flex; flex-direction: column;">
    <span class="tag-badge" style="background: #ff6633; color: white; align-self: flex-start;">LAB 2 &middot; SQL INJECTION</span>
    <h3 style="margin: 0.8em 0 0.4em; font-size: 1.15em; color: #222;">Portal E-Rapor Sekolah</h3>
    <p style="font-size: 0.9em; color: #666; flex: 1; line-height: 1.5;">SQL injection login bypass pada portal rapor sekolah, masuk sebagai administrator kurikulum, lalu perbarui nilai siswa remedial agar tuntas untuk mendapatkan flag.</p>
    <a class="button" href="/lab2" style="align-self: flex-start; margin-top: 1.2em;">Masuk Lab 2</a>
  </div>
  <div style="background: #fff; border: 1px solid #e6e6e6; border-radius: 5px; padding: 1.4em; display: flex; flex-direction: column;">
    <span class="tag-badge" style="background: #0071bc; color: white; align-self: flex-start;">LAB 3 &middot; BUSINESS LOGIC</span>
    <h3 style="margin: 0.8em 0 0.4em; font-size: 1.15em; color: #222;">Harga Spesial</h3>
    <p style="font-size: 0.9em; color: #666; flex: 1; line-height: 1.5;">Manipulasi input tersembunyi (hidden price) untuk membeli kartu Charizard seharga $1337 dengan saldo awal $100.</p>
    <a class="button" href="/lab3" style="align-self: flex-start; margin-top: 1.2em;">Masuk Lab 3</a>
  </div>
  <div style="background: #fff; border: 1px solid #e6e6e6; border-radius: 5px; padding: 1.4em; display: flex; flex-direction: column;">
    <span class="tag-badge" style="background: #0071bc; color: white; align-self: flex-start;">LAB 4 &middot; BUSINESS LOGIC</span>
    <h3 style="margin: 0.8em 0 0.4em; font-size: 1.15em; color: #222;">Keranjang Ajaib</h3>
    <p style="font-size: 0.9em; color: #666; flex: 1; line-height: 1.5;">Memasukkan kuantitas barang bernilai negatif ke dalam keranjang belanja untuk memangkas total tagihan.</p>
    <a class="button" href="/lab4" style="align-self: flex-start; margin-top: 1.2em;">Masuk Lab 4</a>
  </div>
  <div style="background: #fff; border: 1px solid #e6e6e6; border-radius: 5px; padding: 1.4em; display: flex; flex-direction: column;">
    <span class="tag-badge" style="background: #d60000; color: white; align-self: flex-start;">LAB 5 &middot; ACCESS CONTROL</span>
    <h3 style="margin: 0.8em 0 0.4em; font-size: 1.15em; color: #222;">Email Perusahaan</h3>
    <p style="font-size: 0.9em; color: #666; flex: 1; line-height: 1.5;">Eskalasi hak akses administrator (@gembeng.com) via manipulasi email profil untuk menghapus user carlos di admin panel.</p>
    <a class="button" href="/lab5" style="align-self: flex-start; margin-top: 1.2em;">Masuk Lab 5</a>
  </div>
  <div style="background: #fff; border: 1px solid #e6e6e6; border-radius: 5px; padding: 1.4em; display: flex; flex-direction: column;">
    <span class="tag-badge" style="background: #0071bc; color: white; align-self: flex-start;">LAB 6 &middot; BUSINESS LOGIC</span>
    <h3 style="margin: 0.8em 0 0.4em; font-size: 1.15em; color: #222;">Kupon Berlapis</h3>
    <p style="font-size: 0.9em; color: #666; flex: 1; line-height: 1.5;">Menumpuk dua jenis kupon promosi secara bergantian untuk menurunkan harga kartu Charizard hingga bisa dicheckout.</p>
    <a class="button" href="/lab6" style="align-self: flex-start; margin-top: 1.2em;">Masuk Lab 6</a>
  </div>
</section>
"""


LAB1_BODY = """
<section class="search-filters">
  <label>Refine your search:</label>
  <a class="filter-category {% if not category %}selected{% endif %}" href="/lab1">All</a>
  <a class="filter-category {% if category == 'Vintage & Base Set' %}selected{% endif %}" href="/lab1?category=Vintage+%26+Base+Set">Vintage &amp; Base Set</a>
  <a class="filter-category {% if category == 'Modern & Alt Art' %}selected{% endif %}" href="/lab1?category=Modern+%26+Alt+Art">Modern &amp; Alt Art</a>
  <a class="filter-category {% if category == 'Promo & Secret Rare' %}selected{% endif %}" href="/lab1?category=Promo+%26+Secret+Rare">Promo &amp; Secret Rare</a>
  <a class="filter-category {% if category == 'Gifts' %}selected{% endif %}" href="/lab1?category=Gifts">Gifts</a>
</section>

<div class="search" style="margin: 10px 0 20px 0;">
  <form method="get" action="/lab1">
    <input name="category" value="{{ category }}" placeholder="Filter kategori (misal: Vintage & Base Set, Gifts)">
    <button type="submit" class="button">Search</button>
  </form>
</div>

{% if error %}
<div class="flash is-warning" style="padding: 0.8em 1.2em; background: #fdecea; color: #b50000; border: 1px solid #f5c6cb; border-radius: 4px; margin-bottom: 1em;">
  {{ error }}
</div>
{% endif %}

<section class="container-list-tiles">
  {% for product in products %}
  <div>
    <a href="/lab1/product?productId={{ product['id'] }}">
      <img class="product-image" src="{{ product['image'] }}" alt="{{ product['name'] }}">
    </a>
    <h3>{{ product['name'] }}</h3>
    <img class="rating" src="/static/img/ratings/rating{{ product['rating'] }}.png" alt="Rating">
    <div style="font-size: 1.1em; font-weight: bold; margin: 4px 0;">${{ "%.2f"|format(product['price']) }}</div>
    {% if product['released'] == 0 %}
    <p style="color: #b50000; font-weight: bold; margin: 4px 0;">[UNRELEASED CARD / SECRET VAULT ITEM]</p>
    <p style="font-size: 0.9em; word-break: break-all; background: #fff3ef; border: 1px solid #ffd2c2; padding: 8px; border-radius: 4px;">{{ product['description'] }}</p>
    {% else %}
    <p style="font-size: 0.85em; color: #666; margin: 4px 0 8px 0;">{{ product['description'] }}</p>
    {% endif %}
    <a class="button" href="/lab1/product?productId={{ product['id'] }}">View details</a>
  </div>
  {% else %}
  <p class="muted" style="padding: 2em; color: #666;">Tidak ada kartu yang ditemukan.</p>
  {% endfor %}
</section>
"""


LAB2_BODY = """
{% if logged_in_admin %}
<!-- Panel Administrator: Manajemen Nilai Rapor -->
<div style="background: #1e3c72; color: white; padding: 1.6em 2em; border-radius: 8px; margin-bottom: 2em; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
  <div>
    <h2 style="color: white; margin: 0; font-size: 1.5em;">Panel Administrator &middot; Manajemen Nilai Rapor</h2>
    <p style="margin: 4px 0 0; color: #d0e1fd; font-size: 0.9em;">Login sebagai: <strong>administrator</strong> (Kepala Urusan Kurikulum)</p>
  </div>
  <a class="button" href="/lab2/logout" style="background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.4);">Keluar</a>
</div>

{% if flag %}
<div style="background: #e8f5e9; border: 1px solid #a5d6a7; padding: 1.5em; border-radius: 6px; margin-bottom: 2em;">
  <h3 style="color: #1b5e20; margin-top: 0; font-size: 1.25em;">Nilai Rapor Berhasil Diperbarui!</h3>
  <p style="color: #2e7d32; margin-bottom: 0.8em;">Perubahan nilai telah divalidasi dan tersimpan di database sekolah. Berikut flag Anda:</p>
  <div class="flag" style="font-size: 1.15em;">{{ flag }}</div>
</div>
{% elif message %}
<div class="flash" style="padding: 0.8em 1.2em; border-radius: 4px; margin-bottom: 1.5em; background: #e8f1fa; color: #115f82; border: 1px solid #b6d4ec;">
  {{ message }}
</div>
{% endif %}

<div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.8em; margin-bottom: 2em; box-shadow: 0 1px 3px rgba(0,0,0,0.06);">
  <h3 style="color: #1e3c72; margin-top: 0;">Daftar Nilai Siswa Semester Ganjil</h3>
  <p style="font-size: 0.9em; color: #718096; margin-bottom: 1.2em;">Perbarui nilai siswa yang masih berstatus <strong>Remedial</strong> (misal: Budi Santoso) menjadi nilai tuntas (&ge; 75) untuk menerbitkan rapor resmi.</p>

  <table class="cart-table is-table-numbers" style="width: 100%; border-collapse: collapse; margin-bottom: 1em;">
    <thead>
      <tr style="background: #f7fafc; border-bottom: 2px solid #edf2f7; text-align: left;">
        <th style="padding: 10px;">ID</th>
        <th style="padding: 10px;">NIS</th>
        <th style="padding: 10px;">Nama Siswa</th>
        <th style="padding: 10px;">Mata Pelajaran</th>
        <th style="padding: 10px;">Nilai</th>
        <th style="padding: 10px;">Status</th>
        <th style="padding: 10px; width: 170px;">Ubah Nilai</th>
      </tr>
    </thead>
    <tbody>
      {% for s in students %}
      <tr style="border-bottom: 1px solid #edf2f7;">
        <td style="padding: 10px;">{{ s['id'] }}</td>
        <td style="padding: 10px;">{{ s['nis'] }}</td>
        <td style="padding: 10px; font-weight: bold;">{{ s['name'] }}</td>
        <td style="padding: 10px;">{{ s['subject'] }}</td>
        <td style="padding: 10px; font-weight: bold; font-size: 1.1em; color: {% if s['grade'] >= 75 %}#2e7d32{% else %}#c53030{% endif %};">{{ s['grade'] }}</td>
        <td style="padding: 10px;">
          <span style="padding: 2px 8px; border-radius: 12px; font-size: 0.82em; font-weight: bold; {% if s['status'] == 'Tuntas' %}background: #c6f6d5; color: #22543d;{% else %}background: #fed7d7; color: #742a2a;{% endif %}">
            {{ s['status'] }}
          </span>
        </td>
        <td style="padding: 10px;">
          <form method="POST" action="/lab2/update-grade" style="display: flex; gap: 6px; align-items: center; margin: 0;">
            <input type="hidden" name="student_id" value="{{ s['id'] }}">
            <input type="number" name="grade" min="0" max="100" value="{{ s['grade'] }}" style="width: 65px; padding: 4px; margin: 0; font-size: 0.9em;">
            <button class="button is-small" type="submit" style="background: #2b6cb0; color: white; padding: 4px 10px; font-size: 0.85em;">Ubah</button>
          </form>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>

{% elif logged_in_user %}
<!-- Akun Non-Admin (misal wiener) -->
<div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 2em; margin: 2em auto; max-width: 650px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
  <h2 style="color: #2b6cb0; margin-top: 0;">Portal Guru &middot; {{ logged_in_user }}</h2>
  <div style="background: #fffaf0; border: 1px solid #feebc8; color: #7b341e; padding: 1.2em; border-radius: 6px; margin: 1.2em 0; line-height: 1.6;">
    <p style="margin: 0;"><strong>Akses Terbatas:</strong> Anda berhasil masuk sebagai guru (<strong>{{ logged_in_user }}</strong>). Namun, wewenang mengubah nilai rapor hanya untuk administrator kurikulum sekolah.</p>
  </div>
  <p><a class="button" href="/lab2/logout">Keluar (Log out)</a></p>
</div>

{% else %}
<!-- Landing Page: Portal Rapor Sekolah (Belum Login) -->
<div class="school-portal-header" style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 2.2em; border-radius: 8px; margin-bottom: 2em; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
  <div>
    <h1 style="color: white; margin: 0; font-size: 1.8em;">Sistem Informasi E-Rapor Akademik</h1>
    <p style="margin: 4px 0 0; color: #d0e1fd; font-size: 0.95em;">SMA Negeri Taruna Bangsa &middot; Portal Resmi Pengelolaan Nilai Siswa</p>
  </div>
</div>

<div style="display: flex; gap: 2.5em; flex-wrap: wrap;">
  <!-- Kolom Kiri: Informasi Sekolah & Pengumuman -->
  <div style="flex: 1 1 450px;">
    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.8em; margin-bottom: 1.5em; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
      <h3 style="color: #1e3c72; margin-top: 0;">Pengumuman Periode Verifikasi Nilai Rapor</h3>
      <p style="line-height: 1.6; color: #4a5568;">
        Selamat datang di Portal E-Rapor SMA Negeri Taruna Bangsa. Saat ini sistem berada pada periode verifikasi nilai semester ganjil tahun ajaran 2024/2025.
        Bapak/Ibu dewan guru dipersilakan login untuk memeriksa rekapitulasi nilai mata pelajaran masing-masing.
      </p>
      <div style="background: #fffaf0; border-left: 4px solid #dd6b20; padding: 12px 14px; border-radius: 3px; font-size: 0.9em; color: #7b341e; line-height: 1.5;">
        <strong>Catatan Administrator Kurikulum:</strong> Perubahan nilai rapor remedial hanya dapat disahkan melalui akun <strong>administrator</strong> sekolah.
      </div>
    </div>

    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5em; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
      <h4 style="margin-top: 0; color: #2d3748;">Informasi Akses Portal</h4>
      <ul style="color: #4a5568; line-height: 1.6; font-size: 0.9em; padding-left: 1.2em; margin-bottom: 0;">
        <li>Portal ini khusus digunakan oleh Dewan Guru dan Tim Kurikulum Sekolah.</li>
        <li>Bagi akun non-admin (guru biasa), hak akses terbatas pada peninjauan capaian kelas.</li>
        <li>Silakan masuk menggunakan akun resmi sekolah yang telah didaftarkan.</li>
      </ul>
    </div>
  </div>

  <!-- Kolom Kanan: Form Login Guru & Admin -->
  <div style="flex: 1 1 320px; max-width: 420px;">
    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 2em; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
      <h3 style="color: #1e3c72; margin-top: 0; margin-bottom: 0.5em;">Masuk ke Portal</h3>
      <p style="font-size: 0.88em; color: #718096; margin-bottom: 1.5em;">Gunakan NIP / Username dan kata sandi Anda untuk mengakses sistem e-rapor.</p>

      {% if message %}
      <div class="flash" style="padding: 0.8em 1em; border-radius: 4px; margin-bottom: 1.2em; font-size: 0.9em; background: #fdecea; color: #b50000; border: 1px solid #f5c6cb;">
        {{ message }}
      </div>
      {% endif %}

      <form class="login-form" method="POST" action="/lab2">
        <label for="username" style="font-weight: 600; color: #4a5568; font-size: 0.9em; display: block; margin-bottom: 4px;">Username / NIP</label>
        <input required id="username" type="text" name="username" placeholder="Masukkan username" autofocus autocomplete="off" style="width: 100%; padding: 8px 12px; margin-bottom: 14px; border: 1px solid #cbd5e0; border-radius: 4px; box-sizing: border-box;">

        <label for="password" style="font-weight: 600; color: #4a5568; font-size: 0.9em; display: block; margin-bottom: 4px;">Kata Sandi</label>
        <input required id="password" type="password" name="password" placeholder="Masukkan kata sandi" autocomplete="off" style="width: 100%; padding: 8px 12px; margin-bottom: 18px; border: 1px solid #cbd5e0; border-radius: 4px; box-sizing: border-box;">

        <button class="button" type="submit" style="width: 100%; background: #1e3c72; color: white; padding: 10px; font-weight: bold; border-radius: 4px; border: none; cursor: pointer;">Masuk ke Portal</button>
      </form>

      <p style="margin-top: 1.5em; font-size: 0.82em; color: #a0aec0; text-align: center;">
        Akun guru penguji: <code>wiener:peter</code>
      </p>
    </div>
  </div>
</div>
{% endif %}
"""


LAB3_BODY = """
{% if receipt %}
<div class="receipt-box" style="background: white; border: 2px solid #2e7d32; border-radius: 8px; padding: 2em; margin-bottom: 2em; box-shadow: 0 4px 14px rgba(46, 125, 50, 0.12);">
  <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px dashed #cbd5e0; padding-bottom: 1.2em; margin-bottom: 1.2em; flex-wrap: wrap; gap: 1em;">
    <div>
      <span style="background: #e8f5e9; color: #1b5e20; font-size: 0.8em; font-weight: bold; padding: 4px 10px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.05em;">LUNAS / PAID</span>
      <h2 style="color: #1a237e; margin: 8px 0 4px; font-size: 1.5em;">Struk Bukti Pembelian Kartu</h2>
      <p style="margin: 0; color: #718096; font-size: 0.9em;">No. Pesanan: <strong>#{{ receipt.order_id }}</strong> &middot; Pembeli: <strong>{{ lab3_user }}</strong></p>
    </div>
    <div style="text-align: right;">
      <div style="font-size: 0.85em; color: #718096;">Waktu Transaksi</div>
      <div style="font-weight: 600; color: #2d3748;">{{ receipt.date }}</div>
    </div>
  </div>

  <table style="width: 100%; border-collapse: collapse; margin-bottom: 1.5em; font-size: 0.95em;">
    <thead>
      <tr style="background: #f7fafc; border-bottom: 1px solid #e2e8f0; text-align: left;">
        <th style="padding: 10px;">Item / Kartu Koleksi</th>
        <th style="padding: 10px; text-align: center;">Jumlah</th>
        <th style="padding: 10px; text-align: right;">Harga Satuan</th>
        <th style="padding: 10px; text-align: right;">Subtotal</th>
      </tr>
    </thead>
    <tbody>
      {% for it in receipt['items'] %}
      <tr style="border-bottom: 1px solid #edf2f7;">
        <td style="padding: 12px 10px; font-weight: 600; color: #2d3748;">
          {{ it.name }}
          {% if it.pid == 1 %}
          <span style="display: block; font-size: 0.82em; color: #e53935; font-weight: normal; margin-top: 2px;">
            Edisi Kolektor Legendaris - Base Set 1999 Holographic
          </span>
          {% endif %}
        </td>
        <td style="padding: 12px 10px; text-align: center; color: #4a5568;">{{ it.qty }}</td>
        <td style="padding: 12px 10px; text-align: right; color: #4a5568;">${{ "%.2f"|format(it.price) }}</td>
        <td style="padding: 12px 10px; text-align: right; font-weight: 600; color: #2d3748;">${{ "%.2f"|format(it.subtotal) }}</td>
      </tr>
      {% endfor %}
      <tr style="border-top: 2px solid #2d3748; font-weight: bold; font-size: 1.1em;">
        <td colspan="3" style="padding: 12px 10px; text-align: right;">Total Pembayaran:</td>
        <td style="padding: 12px 10px; text-align: right; color: #2e7d32;">${{ "%.2f"|format(receipt.total) }}</td>
      </tr>
      <tr>
        <td colspan="3" style="padding: 4px 10px; text-align: right; color: #718096; font-size: 0.9em;">Sisa Saldo Kredit:</td>
        <td style="padding: 4px 10px; text-align: right; color: #718096; font-size: 0.9em;">${{ "%.2f"|format(balance) }}</td>
      </tr>
    </tbody>
  </table>

  {% if receipt.flag %}
  <div style="background: #f0fff4; border: 1.5px dashed #38a169; border-radius: 6px; padding: 1.2em 1.5em; margin-top: 1em;">
    <div style="margin-bottom: 6px;">
      <strong style="color: #22543d; font-size: 1.05em;">Sertifikat Keaslian Kepemilikan Charizard Holo 1st Edition:</strong>
    </div>
    <p style="margin: 0 0 10px 0; color: #2f855a; font-size: 0.9em; line-height: 1.5;">
      Selamat! Anda adalah pemilik sah kartu Charizard Holo 1st Edition PSA 10. Berikut adalah kode lisensi unik kartu Anda:
    </p>
    <div style="text-align: center; margin: 8px 0;">
      <code class="flag" style="font-size: 1.15em; letter-spacing: 0.05em;">{{ receipt.flag }}</code>
    </div>
  </div>
  {% endif %}
</div>
{% endif %}

{% if lab3_user and items %}
<div class="cart-container" style="background: #ebf0f2; padding: 1.8em; border-radius: 5px; margin-bottom: 2em;">
  <h2 style="margin-top: 0; color: #ff6633;">Keranjang Belanja</h2>
  <table class="cart-table is-table-numbers" style="background: white; width: 100%; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
    <thead>
      <tr>
        <th style="padding: 10px;">Kartu</th>
        <th>Harga Satuan</th>
        <th>Jumlah</th>
        <th style="padding-right: 15px;">Subtotal</th>
      </tr>
    </thead>
    <tbody>
      {% for item in items %}
      <tr>
        <td style="padding: 10px; font-weight: bold;">{{ item.name }}</td>
        <td>${{ "%.2f"|format(item.price) }}</td>
        <td>{{ item.qty }}</td>
        <td style="padding-right: 15px;">${{ "%.2f"|format(item.subtotal) }}</td>
      </tr>
      {% endfor %}
      <tr style="font-weight: bold; font-size: 1.15em; border-top: 2px solid #ccc;">
        <th colspan="3" style="text-align: right; padding-right: 15px;">Total:</th>
        <td style="color: #ff6633; padding-right: 15px;">${{ "%.2f"|format(total) }}</td>
      </tr>
    </tbody>
  </table>
  <div style="display: flex; gap: 12px; margin-top: 1.4em; align-items: center;">
    <form method="post" action="/lab3" style="margin: 0;">
      <input type="hidden" name="action" value="checkout">
      <button class="button is-large" type="submit">Place order</button>
    </form>
    <form method="post" action="/lab3" style="margin: 0;">
      <input type="hidden" name="action" value="empty">
      <button class="button" style="background: #e2e8f0; color: #4a5568;" type="submit">Empty cart</button>
    </form>
  </div>
</div>
{% endif %}

<h2 style="margin-top: 0.5em; color: #ff6633;">Katalog Kartu Pokémon</h2>
<section class="container-list-tiles">
  {% for pid, product in shop.items() %}
  <div>
    <a href="/lab3/product?productId={{ pid }}">
      <img class="product-image" src="{{ product[2] }}" alt="{{ product[0] }}">
    </a>
    <h3>{{ product[0] }}</h3>
    <img class="rating" src="/static/img/ratings/rating{{ product[3] }}.png" alt="Rating">
    <div style="font-size: 1.15em; font-weight: bold; margin: 4px 0;">${{ "%.2f"|format(product[1]) }}</div>
    {% if lab3_user %}
    <form method="post" action="/lab3" style="margin-top: 10px;">
      <input type="hidden" name="action" value="add">
      <input type="hidden" name="pid" value="{{ pid }}">
      <input type="hidden" name="price" value="{{ '%.2f'|format(product[1]) }}">
      <div class="qty-box">
        <label for="qty-{{ pid }}">Quantity:</label>
        <input id="qty-{{ pid }}" type="number" name="qty" value="1" min="1" style="width: 75px; margin: 0; padding: 4px;">
      </div>
      <button class="button is-small" type="submit">Add to cart</button>
    </form>
    {% else %}
    <div style="margin-top: 10px;">
      <a class="button is-small" href="/lab3/login" style="display: inline-block; text-decoration: none;">Add to cart</a>
    </div>
    {% endif %}
    <a href="/lab3/product?productId={{ pid }}" style="display: block; font-size: 0.85em; margin-top: 6px; color: #0071bc;">View product details</a>
  </div>
  {% endfor %}
</section>
"""


LAB3_LOGIN_BODY = """
<div style="max-width: 400px; margin: 2em auto; background: white; padding: 2em; border-radius: 6px; border: 1px solid #e2e8f0; box-shadow: 0 1px 4px rgba(0,0,0,0.06);">
  <h2 style="margin-top: 0; color: #2d3748; margin-bottom: 0.4em;">Login Pelanggan</h2>
  <p style="font-size: 0.88em; color: #718096; margin-bottom: 1.5em;">Silakan login untuk melihat saldo kredit dan berbelanja kartu Pokémon.</p>

  <form class="login-form" method="POST" action="/lab3/login">
    <label for="username" style="font-weight: 600; color: #4a5568; font-size: 0.9em; display: block; margin-bottom: 4px;">Username</label>
    <input required id="username" type="text" name="username" placeholder="Username" autofocus autocomplete="off" style="width: 100%; padding: 8px 12px; margin-bottom: 14px; border: 1px solid #cbd5e0; border-radius: 4px; box-sizing: border-box;">

    <label for="password" style="font-weight: 600; color: #4a5568; font-size: 0.9em; display: block; margin-bottom: 4px;">Password</label>
    <input required id="password" type="password" name="password" placeholder="Password" autocomplete="off" style="width: 100%; padding: 8px 12px; margin-bottom: 18px; border: 1px solid #cbd5e0; border-radius: 4px; box-sizing: border-box;">

    <button class="button" type="submit" style="width: 100%;">Log in</button>
  </form>

  <p style="margin-top: 1.5em; font-size: 0.82em; color: #a0aec0; text-align: center;">
    Akun demo: <code>wiener:peter</code>
  </p>
</div>
"""


LAB4_BODY = """
{% if receipt %}
<div class="receipt-box" style="background: white; border: 2px solid #2e7d32; border-radius: 8px; padding: 2em; margin-bottom: 2em; box-shadow: 0 4px 14px rgba(46, 125, 50, 0.12);">
  <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px dashed #cbd5e0; padding-bottom: 1.2em; margin-bottom: 1.2em; flex-wrap: wrap; gap: 1em;">
    <div>
      <span style="background: #e8f5e9; color: #1b5e20; font-size: 0.8em; font-weight: bold; padding: 4px 10px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.05em;">LUNAS / PAID</span>
      <h2 style="color: #1a237e; margin: 8px 0 4px; font-size: 1.5em;">Struk Bukti Pembelian Kartu</h2>
      <p style="margin: 0; color: #718096; font-size: 0.9em;">No. Pesanan: <strong>#{{ receipt.order_id }}</strong> &middot; Pembeli: <strong>{{ lab4_user }}</strong></p>
    </div>
    <div style="text-align: right;">
      <div style="font-size: 0.85em; color: #718096;">Waktu Transaksi</div>
      <div style="font-weight: 600; color: #2d3748;">{{ receipt.date }}</div>
    </div>
  </div>

  <table style="width: 100%; border-collapse: collapse; margin-bottom: 1.5em; font-size: 0.95em;">
    <thead>
      <tr style="background: #f7fafc; border-bottom: 1px solid #e2e8f0; text-align: left;">
        <th style="padding: 10px;">Item / Kartu Koleksi</th>
        <th style="padding: 10px; text-align: center;">Jumlah</th>
        <th style="padding: 10px; text-align: right;">Harga Satuan</th>
        <th style="padding: 10px; text-align: right;">Subtotal</th>
      </tr>
    </thead>
    <tbody>
      {% for it in receipt['items'] %}
      <tr style="border-bottom: 1px solid #edf2f7;">
        <td style="padding: 12px 10px; font-weight: 600; color: #2d3748;">
          {{ it.name }}
          {% if it.pid == 1 %}
          <span style="display: block; font-size: 0.82em; color: #e53935; font-weight: normal; margin-top: 2px;">
            Edisi Kolektor Legendaris - Base Set 1999 Holographic
          </span>
          {% endif %}
        </td>
        <td style="padding: 12px 10px; text-align: center; color: #4a5568;">{{ it.qty }}</td>
        <td style="padding: 12px 10px; text-align: right; color: #4a5568;">${{ "%.2f"|format(it.price) }}</td>
        <td style="padding: 12px 10px; text-align: right; font-weight: 600; color: #2d3748;">${{ "%.2f"|format(it.subtotal) }}</td>
      </tr>
      {% endfor %}
      <tr style="border-top: 2px solid #2d3748; font-weight: bold; font-size: 1.1em;">
        <td colspan="3" style="padding: 12px 10px; text-align: right;">Total Pembayaran:</td>
        <td style="padding: 12px 10px; text-align: right; color: #2e7d32;">${{ "%.2f"|format(receipt.total) }}</td>
      </tr>
      <tr>
        <td colspan="3" style="padding: 4px 10px; text-align: right; color: #718096; font-size: 0.9em;">Sisa Saldo Kredit:</td>
        <td style="padding: 4px 10px; text-align: right; color: #718096; font-size: 0.9em;">${{ "%.2f"|format(balance) }}</td>
      </tr>
    </tbody>
  </table>

  {% if receipt.flag %}
  <div style="background: #f0fff4; border: 1.5px dashed #38a169; border-radius: 6px; padding: 1.2em 1.5em; margin-top: 1em;">
    <div style="margin-bottom: 6px;">
      <strong style="color: #22543d; font-size: 1.05em;">Sertifikat Keaslian Kepemilikan Charizard Holo 1st Edition:</strong>
    </div>
    <p style="margin: 0 0 10px 0; color: #2f855a; font-size: 0.9em; line-height: 1.5;">
      Selamat! Anda adalah pemilik sah kartu Charizard Holo 1st Edition PSA 10. Berikut adalah kode lisensi unik kartu Anda:
    </p>
    <div style="text-align: center; margin: 8px 0;">
      <code class="flag" style="font-size: 1.15em; letter-spacing: 0.05em;">{{ receipt.flag }}</code>
    </div>
  </div>
  {% endif %}
</div>
{% endif %}

{% if lab4_user and items %}
<div class="cart-container" style="background: #ebf0f2; padding: 1.8em; border-radius: 5px; margin-bottom: 2em;">
  <h2 style="margin-top: 0; color: #ff6633;">Keranjang Belanja</h2>
  <table class="cart-table is-table-numbers" style="background: white; width: 100%; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
    <thead>
      <tr>
        <th style="padding: 10px;">Product</th>
        <th>Unit Price</th>
        <th>Quantity</th>
        <th style="padding-right: 15px;">Subtotal</th>
      </tr>
    </thead>
    <tbody>
      {% for item in items %}
      <tr>
        <td style="padding: 10px; font-weight: bold;">{{ item.name }}</td>
        <td>${{ "%.2f"|format(item.price) }}</td>
        <td style="text-align: center;">
          <div style="display: inline-flex; align-items: center; gap: 0;">
            <form method="post" action="/lab4" style="margin: 0;">
              <input type="hidden" name="action" value="add">
              <input type="hidden" name="pid" value="{{ item.pid }}">
              <input type="hidden" name="qty" value="-1">
              <button type="submit" style="width: 28px; height: 28px; border: 1px solid #cbd5e0; background: #f7fafc; cursor: pointer; font-size: 1em; font-weight: bold; color: #e53e3e; border-radius: 4px 0 0 4px; line-height: 1; padding: 0;">-</button>
            </form>
            <span style="display: inline-block; min-width: 36px; text-align: center; padding: 4px 8px; border-top: 1px solid #cbd5e0; border-bottom: 1px solid #cbd5e0; background: white; font-weight: 600; font-size: 0.95em; height: 28px; line-height: 20px; box-sizing: border-box;">{{ item.qty }}</span>
            <form method="post" action="/lab4" style="margin: 0;">
              <input type="hidden" name="action" value="add">
              <input type="hidden" name="pid" value="{{ item.pid }}">
              <input type="hidden" name="qty" value="1">
              <button type="submit" style="width: 28px; height: 28px; border: 1px solid #cbd5e0; background: #f7fafc; cursor: pointer; font-size: 1em; font-weight: bold; color: #38a169; border-radius: 0 4px 4px 0; line-height: 1; padding: 0;">+</button>
            </form>
          </div>
        </td>
        <td style="padding-right: 15px;">${{ "%.2f"|format(item.subtotal) }}</td>
      </tr>
      {% endfor %}
      <tr style="font-weight: bold; font-size: 1.15em; border-top: 2px solid #ccc;">
        <th colspan="3" style="text-align: right; padding-right: 15px;">Total:</th>
        <td style="color: #ff6633; padding-right: 15px;">${{ "%.2f"|format(total) }}</td>
      </tr>
    </tbody>
  </table>
  <div style="display: flex; gap: 12px; margin-top: 1.4em; align-items: center;">
    <form method="post" action="/lab4" style="margin: 0;">
      <input type="hidden" name="action" value="checkout">
      <button class="button is-large" type="submit">Place order</button>
    </form>
    <form method="post" action="/lab4" style="margin: 0;">
      <input type="hidden" name="action" value="empty">
      <button class="button" style="background: #e2e8f0; color: #4a5568;" type="submit">Empty cart</button>
    </form>
  </div>
</div>
{% endif %}

<h2 style="margin-top: 0.5em; color: #ff6633;">Katalog Kartu Pokémon</h2>
<section class="container-list-tiles">
  {% for pid, product in shop.items() %}
  <div>
    <a href="/lab4/product?productId={{ pid }}">
      <img class="product-image" src="{{ product[2] }}" alt="{{ product[0] }}">
    </a>
    <h3>{{ product[0] }}</h3>
    <img class="rating" src="/static/img/ratings/rating{{ product[3] }}.png" alt="Rating">
    <div style="font-size: 1.1em; font-weight: bold; margin: 4px 0;">${{ "%.2f"|format(product[1]) }}</div>
    {% if lab4_user %}
    <form method="post" action="/lab4" style="margin-top: 10px;">
      <input type="hidden" name="action" value="add">
      <input type="hidden" name="pid" value="{{ pid }}">
      <div class="qty-box">
        <label for="qty-{{ pid }}">Quantity:</label>
        <input id="qty-{{ pid }}" type="number" name="qty" value="1" style="width: 75px; margin: 0; padding: 4px;">
      </div>
      <button class="button is-small" type="submit">Add to cart</button>
    </form>
    {% else %}
    <div style="margin-top: 10px;">
      <a class="button is-small" href="/lab4/login" style="display: inline-block; text-decoration: none;">Add to cart</a>
    </div>
    {% endif %}
    <a href="/lab4/product?productId={{ pid }}" style="display: block; font-size: 0.85em; margin-top: 6px; color: #0071bc;">View details</a>
  </div>
  {% endfor %}
</section>
"""


LAB4_LOGIN_BODY = """
<div style="max-width: 400px; margin: 2em auto; background: white; padding: 2em; border-radius: 6px; border: 1px solid #e2e8f0; box-shadow: 0 1px 4px rgba(0,0,0,0.06);">
  <h2 style="margin-top: 0; color: #2d3748; margin-bottom: 0.4em;">Login Pelanggan</h2>
  <p style="font-size: 0.88em; color: #718096; margin-bottom: 1.5em;">Silakan login untuk melihat saldo kredit dan berbelanja kartu Pokémon.</p>

  <form class="login-form" method="POST" action="/lab4/login">
    <label for="username" style="font-weight: 600; color: #4a5568; font-size: 0.9em; display: block; margin-bottom: 4px;">Username</label>
    <input required id="username" type="text" name="username" placeholder="Username" autofocus autocomplete="off" style="width: 100%; padding: 8px 12px; margin-bottom: 14px; border: 1px solid #cbd5e0; border-radius: 4px; box-sizing: border-box;">

    <label for="password" style="font-weight: 600; color: #4a5568; font-size: 0.9em; display: block; margin-bottom: 4px;">Password</label>
    <input required id="password" type="password" name="password" placeholder="Password" autocomplete="off" style="width: 100%; padding: 8px 12px; margin-bottom: 18px; border: 1px solid #cbd5e0; border-radius: 4px; box-sizing: border-box;">

    <button class="button" type="submit" style="width: 100%;">Log in</button>
  </form>

  <p style="margin-top: 1.5em; font-size: 0.82em; color: #a0aec0; text-align: center;">
    Akun demo: <code>wiener:peter</code>
  </p>
</div>
"""


PRODUCT_DETAIL_BODY = """
<div style="margin-bottom: 1.5em;">
  <a class="is-linkback" href="/lab{{ lab_num }}">&lt; Back to products</a>
</div>
<div class="is-flex" style="display: flex; gap: 3em; flex-wrap: wrap; background: #fff; border: 1px solid #e6e6e6; border-radius: 5px; padding: 2em;">
  <div style="flex: 0 0 320px; text-align: center;">
    <img src="{{ product_img }}" alt="{{ product_name }}" style="max-width: 100%; border-radius: 5px; border: 1px solid #eee;">
  </div>
  <div style="flex: 1 1 350px;">
    <h1 style="color: #333332; margin-top: 0; font-size: 1.8em;">{{ product_name }}</h1>
    <img class="rating" src="/static/img/ratings/rating{{ product_rating }}.png" alt="Rating">
    <p style="font-size: 1.6em; font-weight: bold; color: #ff6633; margin: 12px 0;">${{ "%.2f"|format(product_price) }}</p>
    <p style="color: #666; line-height: 1.6; margin-bottom: 2em;">{{ product_desc }}</p>

    {% if lab_num == 3 %}
    {% if lab3_user %}
    <form method="post" action="/lab3">
      <input type="hidden" name="action" value="add">
      <input type="hidden" name="pid" value="{{ pid }}">
      <input type="hidden" name="price" value="{{ '%.2f'|format(product_price) }}">
      <div class="qty-box" style="justify-content: flex-start; margin-bottom: 15px;">
        <label for="qty-detail-3" style="font-weight: bold;">Quantity:</label>
        <input id="qty-detail-3" type="number" name="qty" value="1" min="1" style="width: 80px; margin: 0; padding: 6px;">
      </div>
      <button class="button is-large" type="submit">Add to cart</button>
    </form>
    {% else %}
    <div style="margin-top: 15px;">
      <a class="button is-large" href="/lab3/login" style="display: inline-block; text-decoration: none;">Add to cart</a>
    </div>
    {% endif %}
    {% elif lab_num == 4 %}
    {% if lab4_user %}
    <form method="post" action="/lab4">
      <input type="hidden" name="action" value="add">
      <input type="hidden" name="pid" value="{{ pid }}">
      <div class="qty-box" style="justify-content: flex-start; margin-bottom: 15px;">
        <label for="qty-detail" style="font-weight: bold;">Quantity:</label>
        <input id="qty-detail" type="number" name="qty" value="1" style="width: 80px; margin: 0; padding: 6px;">
      </div>
      <button class="button is-large" type="submit">Add to cart</button>
    </form>
    {% else %}
    <div style="margin-top: 15px;">
      <a class="button is-large" href="/lab4/login" style="display: inline-block; text-decoration: none;">Add to cart</a>
    </div>
    {% endif %}
    {% elif lab_num == 5 %}
    {% if member %}
    <div style="margin-top: 15px;">
      <a class="button is-large" href="/lab5/my-account" style="display: inline-block; text-decoration: none;">Lihat di Akun</a>
    </div>
    {% else %}
    <div style="margin-top: 15px;">
      <a class="button is-large" href="/lab5/login" style="display: inline-block; text-decoration: none;">Masuk untuk Membeli</a>
    </div>
    {% endif %}
    {% elif lab_num == 6 %}
    <form method="post" action="/lab6/cart" style="margin-top: 15px;">
      <input type="hidden" name="action" value="add">
      <input type="hidden" name="pid" value="{{ product_id }}">
      <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 12px;">
        <label for="qty-detail-6" style="font-weight: bold;">Quantity:</label>
        <input id="qty-detail-6" type="number" name="qty" value="1" min="1" style="width: 80px; margin: 0; padding: 6px;">
      </div>
      <button class="button is-large" type="submit">Add to cart</button>
    </form>
    {% endif %}
  </div>
</div>
"""


LAB5_BODY = """
<div style="background: #e8f4fd; border: 1px solid #b6e0fe; border-radius: 6px; padding: 12px 18px; margin-bottom: 1.5em; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
  <div>
    <span style="background: #0071bc; color: white; font-size: 0.75em; font-weight: bold; padding: 2px 8px; border-radius: 3px; text-transform: uppercase;">Fitur Lab</span>
    <strong style="color: #0b3d60; margin-left: 8px;">Email Client Lab:</strong>
    <span style="color: #4a5568; font-size: 0.9em;">Gunakan klien email internal untuk membaca pesan konfirmasi domain <code>@exploit-lab.net</code>.</span>
  </div>
  <a class="button is-small" href="/lab5/email-client" target="_blank" style="background: #0071bc; color: white; text-decoration: none; font-weight: 600;">Buka Email Client</a>
</div>

{% if member %}
<div style="background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px 16px; margin-bottom: 1.5em; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
  <span style="color: #2d3748; font-size: 0.95em;">
    Selamat datang kembali, <strong>{{ member['username'] }}</strong> ({{ 'Administrator' if member['is_admin'] else 'User' }})!
  </span>
  <div>
    <a class="button is-small" href="/lab5/my-account" style="text-decoration: none;">Buka My Account</a>
    {% if member['is_admin'] %}
    <a class="button is-small" href="/lab5/admin-panel" style="background: #e53e3e; color: white; text-decoration: none; margin-left: 6px;">Admin Panel</a>
    {% endif %}
  </div>
</div>
{% endif %}

<h2 style="margin-top: 0.5em; color: #ff6633;">Katalog Kartu Pokémon</h2>
<section class="container-list-tiles">
  {% for pid, product in shop.items() %}
  <div>
    <a href="/lab5/product?productId={{ pid }}">
      <img class="product-image" src="{{ product[2] }}" alt="{{ product[0] }}">
    </a>
    <h3>{{ product[0] }}</h3>
    <img class="rating" src="/static/img/ratings/rating{{ product[3] }}.png" alt="Rating">
    <div style="font-size: 1.15em; font-weight: bold; margin: 4px 0;">${{ "%.2f"|format(product[1]) }}</div>
    <div style="margin-top: 10px;">
      <a class="button is-small" href="/lab5/product?productId={{ pid }}" style="display: inline-block; text-decoration: none;">View details</a>
    </div>
  </div>
  {% endfor %}
</section>
"""


LAB5_LOGIN_BODY = """
<div style="max-width: 400px; margin: 2em auto; background: white; padding: 2em; border-radius: 6px; border: 1px solid #e2e8f0; box-shadow: 0 1px 4px rgba(0,0,0,0.06);">
  <h2 style="margin-top: 0; color: #2d3748; margin-bottom: 0.4em;">Masuk ke Akun</h2>
  <p style="font-size: 0.88em; color: #718096; margin-bottom: 1.5em;">Silakan login menggunakan akun yang telah diverifikasi.</p>

  <form class="login-form" method="POST" action="/lab5/login">
    <label for="login-username" style="font-weight: 600; color: #4a5568; font-size: 0.9em; display: block; margin-bottom: 4px;">Username</label>
    <input required id="login-username" type="text" name="username" placeholder="Username" autofocus autocomplete="off" style="width: 100%; padding: 8px 12px; margin-bottom: 14px; border: 1px solid #cbd5e0; border-radius: 4px; box-sizing: border-box;">

    <label for="login-password" style="font-weight: 600; color: #4a5568; font-size: 0.9em; display: block; margin-bottom: 4px;">Password</label>
    <input required id="login-password" type="password" name="password" placeholder="Password" autocomplete="off" style="width: 100%; padding: 8px 12px; margin-bottom: 18px; border: 1px solid #cbd5e0; border-radius: 4px; box-sizing: border-box;">

    <button class="button" type="submit" style="width: 100%;">Masuk</button>
  </form>

  <p style="margin-top: 1.5em; font-size: 0.88em; color: #718096; text-align: center;">
    Belum memiliki akun? <a href="/lab5/register" style="color: #0071bc; font-weight: bold; text-decoration: none;">Daftar di sini</a>
  </p>
  <p style="margin-top: 0.5em; font-size: 0.82em; text-align: center;">
    <a href="/lab5" style="color: #a0aec0; text-decoration: none;">&lt; Kembali ke Toko</a>
  </p>
</div>
"""


LAB5_REGISTER_BODY = """
<div style="max-width: 440px; margin: 2em auto; background: white; padding: 2em; border-radius: 6px; border: 1px solid #e2e8f0; box-shadow: 0 1px 4px rgba(0,0,0,0.06);">
  <h2 style="margin-top: 0; color: #2d3748; margin-bottom: 0.4em;">Daftar Akun Baru</h2>
  <p style="font-size: 0.88em; color: #718096; margin-bottom: 1.2em;">Buat akun untuk mengakses portal pelanggan.</p>

  <div style="background: #fffaf0; border-left: 4px solid #dd6b20; padding: 12px 14px; margin-bottom: 1.2em; border-radius: 4px;">
    <p style="margin: 0; color: #7c2d12; font-size: 0.88em; line-height: 1.5;">
      <strong>Pemberitahuan Khusus:</strong> Jika Anda bekerja untuk <strong>jangannangis</strong>, maka gunakan alamat email resmi berakhiran <code>@gembeng.com</code>.
    </p>
  </div>

  <form class="login-form" method="POST" action="/lab5/register">
    <label for="reg-username" style="font-weight: 600; color: #4a5568; font-size: 0.9em; display: block; margin-bottom: 4px;">Username</label>
    <input required id="reg-username" type="text" name="username" placeholder="Username" autocomplete="off" style="width: 100%; padding: 8px 12px; margin-bottom: 12px; border: 1px solid #cbd5e0; border-radius: 4px; box-sizing: border-box;">

    <label for="reg-password" style="font-weight: 600; color: #4a5568; font-size: 0.9em; display: block; margin-bottom: 4px;">Password</label>
    <input required id="reg-password" type="password" name="password" placeholder="Password" autocomplete="off" style="width: 100%; padding: 8px 12px; margin-bottom: 12px; border: 1px solid #cbd5e0; border-radius: 4px; box-sizing: border-box;">

    <label for="reg-email" style="font-weight: 600; color: #4a5568; font-size: 0.9em; display: block; margin-bottom: 4px;">Email</label>
    <input required id="reg-email" type="email" name="email" placeholder="contoh: wiener@exploit-lab.net" autocomplete="off" style="width: 100%; padding: 8px 12px; margin-bottom: 6px; border: 1px solid #cbd5e0; border-radius: 4px; box-sizing: border-box;">
    <p style="font-size: 0.8em; color: #718096; margin: 0 0 16px 0;">
      Aktivasi akun dikirim ke <a href="/lab5/email-client" target="_blank" style="color: #0071bc; font-weight: 600;">Email Client</a> (@exploit-lab.net).
    </p>

    <button class="button" type="submit" style="width: 100%;">Daftar</button>
  </form>

  <p style="margin-top: 1.5em; font-size: 0.88em; color: #718096; text-align: center;">
    Sudah memiliki akun? <a href="/lab5/login" style="color: #0071bc; font-weight: bold; text-decoration: none;">Masuk di sini</a>
  </p>
  <p style="margin-top: 0.5em; font-size: 0.82em; text-align: center;">
    <a href="/lab5" style="color: #a0aec0; text-decoration: none;">&lt; Kembali ke Toko</a>
  </p>
</div>
"""


LAB5_MY_ACCOUNT_BODY = """
<div style="background: white; border: 1px solid #e2e8f0; padding: 2em; border-radius: 6px; max-width: 650px; margin: 1em auto; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
  <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #edf2f7; padding-bottom: 1em; margin-bottom: 1.5em;">
    <div>
      <h2 style="margin: 0; color: #2d3748;">Profil Pengguna</h2>
      <p style="margin: 4px 0 0; color: #718096; font-size: 0.9em;">Kelola informasi akun dan pengaturan email Anda.</p>
    </div>
    {% if member['is_admin'] %}
    <span class="tag-badge" style="background: #e53e3e; color: white;">Administrator</span>
    {% else %}
    <span class="tag-badge" style="background: #718096; color: white;">Pengguna Biasa</span>
    {% endif %}
  </div>

  <table style="width: 100%; border-collapse: collapse; margin-bottom: 1.8em; font-size: 0.95em;">
    <tr style="border-bottom: 1px solid #edf2f7;">
      <td style="padding: 10px 0; color: #718096; width: 140px;">Username:</td>
      <td style="padding: 10px 0; font-weight: 600; color: #2d3748;">{{ member['username'] }}</td>
    </tr>
    <tr style="border-bottom: 1px solid #edf2f7;">
      <td style="padding: 10px 0; color: #718096;">Email Terdaftar:</td>
      <td style="padding: 10px 0; font-weight: 600; color: #2d3748;">{{ member['email'] }}</td>
    </tr>
    <tr>
      <td style="padding: 10px 0; color: #718096;">Hak Akses / Peran:</td>
      <td style="padding: 10px 0; font-weight: 600; color: #2d3748;">
        {% if member['is_admin'] %}
        <span style="color: #e53e3e; font-weight: bold;">Administrator (@gembeng.com)</span>
        {% else %}
        <span>User</span>
        {% endif %}
      </td>
    </tr>
  </table>

  {% if member['is_admin'] %}
  <div style="background: #fff5f5; border: 1px solid #feb2b2; border-radius: 6px; padding: 1.2em; margin-bottom: 1.5em;">
    <h3 style="margin-top: 0; color: #c53030; font-size: 1.1em;">Akses Panel Administrator Aktif</h3>
    <p style="color: #742a2a; font-size: 0.9em; margin-bottom: 1em;">Akun Anda memiliki izin administratif untuk mengelola pengguna sistem.</p>
    <a class="button" href="/lab5/admin-panel" style="background: #e53e3e; color: white; font-weight: bold; text-decoration: none;">Buka Panel Administrasi</a>
  </div>
  {% endif %}

  <div style="background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 1.5em;">
    <h3 style="margin-top: 0; color: #2d3748; font-size: 1.05em;">Perbarui Alamat Email</h3>
    <form class="login-form" method="POST" action="/lab5/update-email" style="margin: 0;">
      <label for="email" style="font-weight: 600; color: #4a5568; font-size: 0.9em;">Alamat Email Baru</label>
      <input required id="email" type="email" name="email" value="{{ member['email'] }}" style="width: 100%; padding: 8px 12px; margin-bottom: 12px; border: 1px solid #cbd5e0; border-radius: 4px; box-sizing: border-box;">
      <button class="button" type="submit">Simpan Perubahan Email</button>
    </form>
  </div>

  <div style="margin-top: 1.5em;">
    <a href="/lab5" style="color: #0071bc; text-decoration: none; font-size: 0.9em; font-weight: 600;">&lt; Kembali ke Toko</a>
  </div>
</div>
"""


LAB5_ADMIN_BODY = """
<div style="background: white; border: 1px solid #e2e8f0; border-radius: 6px; padding: 2em; margin: 1em auto; max-width: 800px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
  <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #edf2f7; padding-bottom: 1.2em; margin-bottom: 1.5em; flex-wrap: wrap; gap: 10px;">
    <div>
      <span class="tag-badge" style="background: #e53e3e; color: white;">Panel Administrasi</span>
      <h1 style="margin: 8px 0 4px; color: #1a202c; font-size: 1.6em;">Kelola Pengguna Sistem</h1>
      <p style="margin: 0; color: #718096; font-size: 0.9em;">Hak akses administratif diberikan kepada staf resmi <strong>jangannangis</strong> (@gembeng.com).</p>
    </div>
    <div style="text-align: right;">
      <a class="button is-small" href="/lab5" style="text-decoration: none;">&lt; My Account</a>
    </div>
  </div>

  {% if is_solved and flag %}
  <div style="background: #f0fff4; border: 1.5px dashed #38a169; border-radius: 6px; padding: 1.5em; margin-bottom: 1.8em;">
    <h3 style="color: #22543d; margin-top: 0; font-size: 1.2em;">Misi Berhasil: Pengguna Carlos Telah Dihapus!</h3>
    <p style="color: #2f855a; margin-bottom: 12px; line-height: 1.5;">
      Selamat! Anda berhasil membobol otorisasi peran admin dengan manipulasi domain email dan menghapus pengguna target carlos. Berikut adalah flag penyelesaian Lab 5:
    </p>
    <div style="text-align: center; margin: 10px 0;">
      <code class="flag" style="font-size: 1.25em; letter-spacing: 0.05em;">{{ flag }}</code>
    </div>
  </div>
  {% endif %}

  <h3 style="color: #2d3748; margin-bottom: 0.8em;">Daftar Pengguna Aktif</h3>
  <table style="width: 100%; border-collapse: collapse; font-size: 0.95em;">
    <thead>
      <tr style="background: #f7fafc; border-bottom: 2px solid #e2e8f0; text-align: left;">
        <th style="padding: 10px 12px;">Username</th>
        <th style="padding: 10px 12px;">Email</th>
        <th style="padding: 10px 12px;">Peran</th>
        <th style="padding: 10px 12px; text-align: center;">Tindakan</th>
      </tr>
    </thead>
    <tbody>
      {% for u in users %}
      <tr style="border-bottom: 1px solid #edf2f7;">
        <td style="padding: 12px; font-weight: 600; color: #2d3748;">
          {{ u.username }}
          {% if u.username == 'jangannangis' %}
          <span style="font-size: 0.8em; color: #e53e3e; display: block; font-weight: normal;">Pemilik Role Admin</span>
          {% endif %}
        </td>
        <td style="padding: 12px; color: #4a5568;">{{ u.email }}</td>
        <td style="padding: 12px;">
          {% if u.is_admin %}
          <span style="background: #fed7d7; color: #9b2c2c; padding: 2px 8px; border-radius: 4px; font-size: 0.82em; font-weight: bold;">ADMIN</span>
          {% else %}
          <span style="background: #edf2f7; color: #4a5568; padding: 2px 8px; border-radius: 4px; font-size: 0.82em;">USER</span>
          {% endif %}
        </td>
        <td style="padding: 12px; text-align: center;">
          {% if u.username == 'carlos' %}
          <form method="POST" action="/lab5/admin/delete" style="margin: 0; display: inline;">
            <input type="hidden" name="username" value="{{ u.username }}">
            <button class="button is-small" style="background: #e53e3e; color: white;" type="submit">Hapus Pengguna</button>
          </form>
          {% elif u.username == 'jangannangis' %}
          <span style="font-size: 0.85em; color: #a0aec0;">Dilindungi</span>
          {% elif u.username == member['username'] %}
          <span style="font-size: 0.85em; color: #a0aec0;">Akun Anda</span>
          {% else %}
          <form method="POST" action="/lab5/admin/delete" style="margin: 0; display: inline;">
            <input type="hidden" name="username" value="{{ u.username }}">
            <button class="button is-small" style="background: #e2e8f0; color: #4a5568;" type="submit">Hapus</button>
          </form>
          {% endif %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
"""


LAB5_ADMIN_DENIED_BODY = """
<div style="background: white; border: 1px solid #fed7d7; border-radius: 6px; padding: 2.5em; margin: 2em auto; max-width: 600px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
  <div style="display: inline-block; background: #fff5f5; border: 2px solid #feb2b2; color: #c53030; width: 64px; height: 64px; border-radius: 50%; font-size: 2em; line-height: 60px; font-weight: bold; margin-bottom: 1em;">!</div>
  <h1 style="color: #9b2c2c; margin-top: 0; font-size: 1.6em;">Akses Ditolak: Administrator Saja</h1>
  <p style="color: #4a5568; line-height: 1.6; margin-bottom: 1.8em;">
    Hanya administrator yang dapat mengakses panel administrasi ini. Hak akses administratif dimiliki oleh pengguna <strong>jangannangis</strong> dan karyawan dengan alamat email resmi <code>@gembeng.com</code>.
  </p>
  <div style="display: flex; justify-content: center; gap: 12px;">
    <a class="button" href="/lab5" style="text-decoration: none;">Kembali ke Halaman Akun</a>
  </div>
</div>
"""


LAB5_EMAIL_CLIENT_BODY = """
<div style="background: white; border: 1px solid #e2e8f0; border-radius: 6px; padding: 2em; margin: 1em auto; max-width: 850px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
  <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #edf2f7; padding-bottom: 1.2em; margin-bottom: 1.5em; flex-wrap: wrap; gap: 10px;">
    <div>
      <span class="tag-badge" style="background: #0071bc; color: white;">Email Client</span>
      <h1 style="margin: 8px 0 4px; color: #1a202c; font-size: 1.6em;">Kotak Masuk Email (@exploit-lab.net)</h1>
      <p style="margin: 0; color: #718096; font-size: 0.9em;">Semua email verifikasi untuk domain <code>@exploit-lab.net</code> akan masuk ke klien ini.</p>
    </div>
    <div style="display: flex; gap: 8px;">
      <a class="button is-small" href="/lab5/email-client" style="text-decoration: none;">Segarkan</a>
      <form method="POST" action="/lab5/email-client/clear" style="margin: 0;">
        <button class="button is-small" style="background: #e2e8f0; color: #4a5568;" type="submit">Kosongkan Kotak Masuk</button>
      </form>
    </div>
  </div>

  {% if selected_email %}
  <div style="background: #f7fafc; border: 1px solid #cbd5e0; border-radius: 6px; padding: 1.5em; margin-bottom: 2em;">
    <div style="display: flex; justify-content: space-between; margin-bottom: 12px; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px;">
      <div>
        <div style="font-size: 0.85em; color: #718096;">Subjek:</div>
        <strong style="color: #2d3748; font-size: 1.1em;">{{ selected_email.subject }}</strong>
      </div>
      <div style="text-align: right;">
        <div style="font-size: 0.85em; color: #718096;">Diterima:</div>
        <div style="color: #4a5568; font-size: 0.9em;">{{ selected_email.created_at }}</div>
      </div>
    </div>
    <div style="font-size: 0.9em; color: #4a5568; margin-bottom: 14px;">
      Penerima: <strong>{{ selected_email.recipient }}</strong>
    </div>
    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 4px; padding: 1.5em; line-height: 1.6; color: #2d3748;">
      {{ selected_email.body|safe }}
    </div>
    <div style="margin-top: 12px; text-align: right;">
      <a href="/lab5/email-client" style="color: #0071bc; font-size: 0.9em; text-decoration: none;">&lt; Tutup Surat</a>
    </div>
  </div>
  {% endif %}

  <h3 style="color: #2d3748; margin-bottom: 0.8em;">Daftar Surat Masuk</h3>
  {% if emails %}
  <table style="width: 100%; border-collapse: collapse; font-size: 0.95em;">
    <thead>
      <tr style="background: #f7fafc; border-bottom: 2px solid #e2e8f0; text-align: left;">
        <th style="padding: 10px 12px;">Waktu</th>
        <th style="padding: 10px 12px;">Penerima</th>
        <th style="padding: 10px 12px;">Subjek</th>
        <th style="padding: 10px 12px; text-align: center;">Tindakan</th>
      </tr>
    </thead>
    <tbody>
      {% for em in emails %}
      <tr style="border-bottom: 1px solid #edf2f7; {% if selected_email and selected_email.id == em.id %}background: #ebf8ff;{% endif %}">
        <td style="padding: 12px; color: #718096; font-size: 0.88em;">{{ em.created_at }}</td>
        <td style="padding: 12px; font-weight: 600; color: #2d3748;">{{ em.recipient }}</td>
        <td style="padding: 12px; color: #2d3748;">{{ em.subject }}</td>
        <td style="padding: 12px; text-align: center;">
          <a class="button is-small" href="/lab5/email-client?id={{ em.id }}" style="text-decoration: none;">Buka Email</a>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <div style="text-align: center; padding: 3em 1em; color: #a0aec0; border: 2px dashed #e2e8f0; border-radius: 6px;">
    <p style="margin: 0; font-size: 1em;">Kotak masuk kosong. Belum ada email yang dikirim ke domain <code>@exploit-lab.net</code>.</p>
  </div>
  {% endif %}
</div>
"""


LAB6_BODY = """
<div style="background: #f0fff4; border: 1px solid #9ae6b4; border-left: 5px solid #38a169; border-radius: 6px; padding: 14px 18px; margin-bottom: 1.5em; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
  <div>
    <span class="tag-badge" style="background: #276749; color: white;">Kupon Promosi</span>
    <strong style="color: #22543d; margin-left: 8px;">Kupon Pertama Belanja:</strong>
    <span style="color: #276749; font-size: 0.95em;">Gunakan kode kupon <strong style="background: white; padding: 2px 8px; border: 1px dashed #38a169; border-radius: 4px; font-family: monospace; font-size: 1.1em; color: #22543d;">NEWCUST5</strong> untuk mendapatkan potongan harga $5.00 pada pesanan Anda!</span>
  </div>
  <a class="button is-small" href="/lab6/cart" style="background: #38a169; color: white; text-decoration: none; font-weight: 600;">Pakai Kupon</a>
</div>

<div style="background: #e8f4fd; border: 1px solid #b6e0fe; border-radius: 6px; padding: 12px 18px; margin-bottom: 1.5em; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
  <div>
    <span class="tag-badge" style="background: #0071bc; color: white;">Keranjang Toko</span>
    <strong style="color: #0b3d60; margin-left: 8px;">Koleksi Impian:</strong>
    <span style="color: #4a5568; font-size: 0.9em;">Kartu langka <strong>Charizard Holo 1st Edition ($1337.00)</strong> siap di keranjang belanja Anda.</span>
  </div>
  <a class="button is-small" href="/lab6/cart" style="background: #0071bc; color: white; text-decoration: none; font-weight: 600;">Lihat Keranjang Belanja</a>
</div>

{% if lab6_user %}
<div style="background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px 16px; margin-bottom: 1.5em; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
  <span style="color: #2d3748; font-size: 0.95em;">
    Selamat datang, <strong>{{ lab6_user }}</strong>! Anda masuk sebagai pelanggan resmi PokéCard Shop.
  </span>
  <a class="button is-small" href="/lab6/cart" style="text-decoration: none;">Ke Kasir &amp; Checkout</a>
</div>
{% endif %}

<h2 style="margin-top: 0.5em; color: #ff6633;">Katalog Kartu Pokémon</h2>
<section class="container-list-tiles">
  {% for pid, product in shop.items() %}
  <div>
    <a href="/lab6/product?productId={{ pid }}">
      <img class="product-image" src="{{ product[2] }}" alt="{{ product[0] }}">
    </a>
    <h3>{{ product[0] }}</h3>
    <img class="rating" src="/static/img/ratings/rating{{ product[3] }}.png" alt="Rating">
    <div style="font-size: 1.15em; font-weight: bold; margin: 4px 0;">${{ "%.2f"|format(product[1]) }}</div>
    <div style="margin-top: 10px;">
      {% if pid == 1 %}
      <a class="button is-small" href="/lab6/cart" style="display: inline-block; text-decoration: none; background: #ff6633; color: white;">Buka di Keranjang</a>
      {% else %}
      <a class="button is-small" href="/lab6/product?productId={{ pid }}" style="display: inline-block; text-decoration: none;">View details</a>
      {% endif %}
    </div>
  </div>
  {% endfor %}
</section>

<!-- Card Berita Koran Kabar di Bagian Bawah -->
<div style="background: white; border: 1px solid #e2e8f0; border-radius: 6px; padding: 2.2em; margin-top: 3.5em; margin-bottom: 1em; box-shadow: 0 1px 4px rgba(0,0,0,0.05); text-align: center;">
  <span class="tag-badge" style="background: #2b6cb0; color: white;">Warta Toko</span>
  <h3 style="margin: 0.6em 0 0.3em; color: #2d3748; font-size: 1.35em;">Langganan Berita Koran Kabar Pokémon</h3>
  <p style="color: #718096; font-size: 0.92em; max-width: 520px; margin: 0 auto 1.5em; line-height: 1.6;">
    Daftarkan alamat email Anda untuk menerima kabar berita lelang kartu langka, jadwal turnamen mingguan, dan dapatkan kupon diskon spesial belanja!
  </p>
  <form method="POST" action="/lab6/newsletter" style="max-width: 460px; margin: 0 auto; display: flex; gap: 8px;">
    <input required type="email" name="email" placeholder="Masukkan alamat email Anda..." autocomplete="off" style="flex: 1; padding: 10px 14px; border: 1px solid #cbd5e0; border-radius: 4px; box-sizing: border-box;">
    <button class="button" type="submit" style="white-space: nowrap; padding: 10px 20px;">Daftar Berita</button>
  </form>
</div>
"""


LAB6_CART_BODY = """
{% if receipt %}
<div class="receipt-box" style="background: white; border: 2px solid #2e7d32; border-radius: 8px; padding: 2em; margin-bottom: 2em; box-shadow: 0 4px 14px rgba(46, 125, 50, 0.12);">
  <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px dashed #cbd5e0; padding-bottom: 1.2em; margin-bottom: 1.2em; flex-wrap: wrap; gap: 1em;">
    <div>
      <span style="background: #e8f5e9; color: #1b5e20; font-size: 0.8em; font-weight: bold; padding: 4px 10px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.05em;">LUNAS / PAID</span>
      <h2 style="color: #1a237e; margin: 8px 0 4px; font-size: 1.5em;">Struk Bukti Pembelian Kartu</h2>
      <p style="margin: 0; color: #718096; font-size: 0.9em;">No. Pesanan: <strong>#{{ receipt.order_id }}</strong></p>
    </div>
    <div style="text-align: right;">
      <div style="font-size: 0.85em; color: #718096;">Waktu Transaksi</div>
      <div style="font-weight: 600; color: #2d3748;">{{ receipt.date }}</div>
    </div>
  </div>

  <table style="width: 100%; border-collapse: collapse; margin-bottom: 1.5em; font-size: 0.95em;">
    <thead>
      <tr style="background: #f7fafc; border-bottom: 1px solid #e2e8f0; text-align: left;">
        <th style="padding: 10px;">Item / Kartu Koleksi</th>
        <th style="padding: 10px; text-align: center;">Jumlah</th>
        <th style="padding: 10px; text-align: right;">Harga Awal</th>
        <th style="padding: 10px; text-align: right;">Total Bayar</th>
      </tr>
    </thead>
    <tbody>
      {% for it in receipt['items'] %}
      <tr style="border-bottom: 1px solid #edf2f7;">
        <td style="padding: 12px 10px; font-weight: 600; color: #2d3748;">
          {{ it.name }}
          <span style="display: block; font-size: 0.82em; color: #e53935; font-weight: normal; margin-top: 2px;">
            Edisi Kolektor Legendaris - Potongan Kupon Berlapis Berhasil
          </span>
        </td>
        <td style="padding: 12px 10px; text-align: center; color: #4a5568;">{{ it.qty }}</td>
        <td style="padding: 12px 10px; text-align: right; color: #4a5568;">${{ "%.2f"|format(it.price) }}</td>
        <td style="padding: 12px 10px; text-align: right; font-weight: 600; color: #2e7d32;">${{ "%.2f"|format(receipt.total) }}</td>
      </tr>
      {% endfor %}
      <tr style="border-top: 2px solid #2d3748; font-weight: bold; font-size: 1.1em;">
        <td colspan="3" style="padding: 12px 10px; text-align: right;">Total Pembayaran:</td>
        <td style="padding: 12px 10px; text-align: right; color: #2e7d32;">${{ "%.2f"|format(receipt.total) }}</td>
      </tr>
      <tr>
        <td colspan="3" style="padding: 4px 10px; text-align: right; color: #718096; font-size: 0.9em;">Sisa Saldo Kredit:</td>
        <td style="padding: 4px 10px; text-align: right; color: #718096; font-size: 0.9em;">${{ "%.2f"|format(credit - receipt.total if (credit - receipt.total) >= 0 else 0) }}</td>
      </tr>
    </tbody>
  </table>

  {% if receipt.flag %}
  <div style="background: #f0fff4; border: 1.5px dashed #38a169; border-radius: 6px; padding: 1.2em 1.5em; margin-top: 1em;">
    <div style="margin-bottom: 6px;">
      <strong style="color: #22543d; font-size: 1.05em;">Sertifikat Keaslian Kepemilikan Charizard Holo 1st Edition:</strong>
    </div>
    <p style="margin: 0 0 10px 0; color: #2f855a; font-size: 0.9em; line-height: 1.5;">
      Selamat! Anda berhasil membeli kartu Charizard legendaris dengan memanfaatkan celah penumpukan kupon promosi secara berlapis. Berikut kode lisensi Anda:
    </p>
    <div style="text-align: center; margin: 8px 0;">
      <code class="flag" style="font-size: 1.15em; letter-spacing: 0.05em;">{{ receipt.flag }}</code>
    </div>
  </div>
  {% endif %}
</div>
{% endif %}

<div style="background: #f0fff4; border: 1px solid #9ae6b4; border-left: 5px solid #38a169; border-radius: 6px; padding: 12px 18px; margin-bottom: 1.5em; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
  <div>
    <span class="tag-badge" style="background: #276749; color: white;">Kupon Promosi</span>
    <strong style="color: #22543d; margin-left: 8px;">Kupon Pertama Belanja:</strong>
    <span style="color: #276749; font-size: 0.95em;">Gunakan kode kupon <strong style="background: white; padding: 2px 8px; border: 1px dashed #38a169; border-radius: 4px; font-family: monospace; font-size: 1.1em; color: #22543d;">NEWCUST5</strong> (potongan $5.00).</span>
  </div>
</div>

<div style="background: #ebf0f2; padding: 1.8em; border-radius: 5px; margin-bottom: 2em;">
  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1em;">
    <h2 style="margin: 0; color: #ff6633;">Keranjang Belanja</h2>
    <a href="/lab6" style="color: #0071bc; font-size: 0.9em; text-decoration: none; font-weight: 600;">&lt; Lanjut Belanja</a>
  </div>

  <table class="cart-table is-table-numbers" style="background: white; width: 100%; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
    <thead>
      <tr>
        <th style="padding: 10px;">Item / Produk</th>
        <th>Harga Asli</th>
        <th style="text-align: center;">Jumlah</th>
        <th>Harga Diskon</th>
        <th style="padding-right: 15px;">Subtotal</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style="padding: 10px; font-weight: bold;">
          <img src="/static/img/pokemon/charizard.jpg" alt="Charizard" style="width: 50px; height: 50px; object-fit: cover; vertical-align: middle; margin-right: 12px; border-radius: 4px;">
          Charizard Holo 1st Edition (Base Set 1999)
        </td>
        <td>$1337.00</td>
        <td style="text-align: center;">
          <div style="display: inline-flex; align-items: center; gap: 0;">
            <form method="post" action="/lab6/cart" style="margin: 0;">
              <input type="hidden" name="action" value="add">
              <input type="hidden" name="pid" value="1">
              <input type="hidden" name="qty" value="-1">
              <button type="submit" style="width: 28px; height: 28px; border: 1px solid #cbd5e0; background: #f7fafc; cursor: pointer; font-size: 1em; font-weight: bold; color: #e53e3e; border-radius: 4px 0 0 4px; line-height: 1; padding: 0;">-</button>
            </form>
            <span style="display: inline-block; min-width: 36px; text-align: center; padding: 4px 8px; border-top: 1px solid #cbd5e0; border-bottom: 1px solid #cbd5e0; background: white; font-weight: 600; font-size: 0.95em; height: 28px; line-height: 20px; box-sizing: border-box;">{{ lab6_qty }}</span>
            <form method="post" action="/lab6/cart" style="margin: 0;">
              <input type="hidden" name="action" value="add">
              <input type="hidden" name="pid" value="1">
              <input type="hidden" name="qty" value="1">
              <button type="submit" style="width: 28px; height: 28px; border: 1px solid #cbd5e0; background: #f7fafc; cursor: pointer; font-size: 1em; font-weight: bold; color: #38a169; border-radius: 0 4px 4px 0; line-height: 1; padding: 0;">+</button>
            </form>
          </div>
        </td>
        <td style="font-weight: bold; font-size: 1.05em; color: #ff6633;">${{ "%.2f"|format(price) }}</td>
        <td style="font-weight: bold; font-size: 1.15em; color: #ff6633; padding-right: 15px;">${{ "%.2f"|format(total) }}</td>
      </tr>
      <tr style="font-weight: bold; font-size: 1.15em; border-top: 2px solid #ccc;">
        <th colspan="4" style="text-align: right; padding-right: 15px;">Total Tagihan:</th>
        <td style="color: #ff6633; padding-right: 15px;">${{ "%.2f"|format(total) }}</td>
      </tr>
    </tbody>
  </table>

  <div style="display: flex; gap: 20px; margin-top: 1.5em; flex-wrap: wrap;">
    <div style="flex: 1 1 320px;">
      <form class="login-form" method="POST" action="/lab6/coupon" style="background: white; border-radius: 4px; padding: 1.2em;">
        <label for="code" style="font-weight: 600; color: #4a5568; font-size: 0.9em;">Kode Kupon Diskon:</label>
        <div class="coupon-box" style="display: flex; gap: 8px;">
          <input id="code" type="text" name="code" placeholder="Contoh: NEWCUST5" autocomplete="off" style="margin-bottom: 0;">
          <button class="button" type="submit" style="margin-bottom: 0;">Terapkan</button>
        </div>
      </form>
    </div>
    <div style="flex: 1 1 200px; display: flex; flex-direction: column; align-items: flex-end; justify-content: center;">
      <form method="POST" action="/lab6/checkout" style="margin: 0;">
        <button class="button is-large" type="submit">Place order</button>
      </form>
      {% if lab6_user %}
      <div style="font-size: 0.85em; color: #4a5568; margin-top: 6px;">Kredit Anda: <strong>${{ "%.2f"|format(credit) }}</strong></div>
      {% else %}
      <div style="font-size: 0.82em; color: #718096; margin-top: 6px;">
        <a href="/lab6/login" style="color: #0071bc; font-weight: bold; text-decoration: none;">Login</a> / <a href="/lab6/register" style="color: #0071bc; font-weight: bold; text-decoration: none;">Register</a> untuk melihat kredit
      </div>
      {% endif %}
    </div>
  </div>
</div>
"""


LAB6_LOGIN_BODY = """
<div style="max-width: 400px; margin: 2em auto; background: white; padding: 2em; border-radius: 6px; border: 1px solid #e2e8f0; box-shadow: 0 1px 4px rgba(0,0,0,0.06);">
  <h2 style="margin-top: 0; color: #2d3748; margin-bottom: 0.4em;">Masuk ke Akun</h2>
  <p style="font-size: 0.88em; color: #718096; margin-bottom: 1.5em;">Silakan login untuk mengelola pesanan kartu Anda.</p>

  <form class="login-form" method="POST" action="/lab6/login">
    <label for="login-username" style="font-weight: 600; color: #4a5568; font-size: 0.9em; display: block; margin-bottom: 4px;">Username</label>
    <input required id="login-username" type="text" name="username" placeholder="Username" autofocus autocomplete="off" style="width: 100%; padding: 8px 12px; margin-bottom: 14px; border: 1px solid #cbd5e0; border-radius: 4px; box-sizing: border-box;">

    <label for="login-password" style="font-weight: 600; color: #4a5568; font-size: 0.9em; display: block; margin-bottom: 4px;">Password</label>
    <input required id="login-password" type="password" name="password" placeholder="Password" autocomplete="off" style="width: 100%; padding: 8px 12px; margin-bottom: 18px; border: 1px solid #cbd5e0; border-radius: 4px; box-sizing: border-box;">

    <button class="button" type="submit" style="width: 100%;">Masuk</button>
  </form>

  <p style="margin-top: 1.5em; font-size: 0.88em; color: #718096; text-align: center;">
    Belum memiliki akun? <a href="/lab6/register" style="color: #0071bc; font-weight: bold; text-decoration: none;">Daftar di sini</a>
  </p>
  <p style="margin-top: 0.5em; font-size: 0.82em; text-align: center;">
    <a href="/lab6" style="color: #a0aec0; text-decoration: none;">&lt; Kembali ke Toko</a>
  </p>
</div>
"""


LAB6_REGISTER_BODY = """
<div style="max-width: 420px; margin: 2em auto; background: white; padding: 2em; border-radius: 6px; border: 1px solid #e2e8f0; box-shadow: 0 1px 4px rgba(0,0,0,0.06);">
  <h2 style="margin-top: 0; color: #2d3748; margin-bottom: 0.4em;">Daftar Akun Pelanggan</h2>
  <p style="font-size: 0.88em; color: #718096; margin-bottom: 1.2em;">Daftar sekarang untuk mendapatkan hadiah kupon belanja pertama Anda!</p>

  <form class="login-form" method="POST" action="/lab6/register">
    <label for="reg-username" style="font-weight: 600; color: #4a5568; font-size: 0.9em; display: block; margin-bottom: 4px;">Username</label>
    <input required id="reg-username" type="text" name="username" placeholder="Username" autocomplete="off" style="width: 100%; padding: 8px 12px; margin-bottom: 12px; border: 1px solid #cbd5e0; border-radius: 4px; box-sizing: border-box;">

    <label for="reg-password" style="font-weight: 600; color: #4a5568; font-size: 0.9em; display: block; margin-bottom: 4px;">Password</label>
    <input required id="reg-password" type="password" name="password" placeholder="Password" autocomplete="off" style="width: 100%; padding: 8px 12px; margin-bottom: 12px; border: 1px solid #cbd5e0; border-radius: 4px; box-sizing: border-box;">

    <label for="reg-email" style="font-weight: 600; color: #4a5568; font-size: 0.9em; display: block; margin-bottom: 4px;">Email</label>
    <input required id="reg-email" type="email" name="email" placeholder="contoh: kolektor@email.com" autocomplete="off" style="width: 100%; padding: 8px 12px; margin-bottom: 18px; border: 1px solid #cbd5e0; border-radius: 4px; box-sizing: border-box;">

    <button class="button" type="submit" style="width: 100%;">Daftar Sekarang</button>
  </form>

  <p style="margin-top: 1.5em; font-size: 0.88em; color: #718096; text-align: center;">
    Sudah memiliki akun? <a href="/lab6/login" style="color: #0071bc; font-weight: bold; text-decoration: none;">Masuk di sini</a>
  </p>
  <p style="margin-top: 0.5em; font-size: 0.82em; text-align: center;">
    <a href="/lab6" style="color: #a0aec0; text-decoration: none;">&lt; Kembali ke Toko</a>
  </p>
</div>
"""


NOT_FOUND_BODY = """
<div style="background: #ebf0f2; padding: 2em; border-radius: 5px; text-align: center; margin-top: 2em;">
  <h1 style="color: #ff6633; font-size: 2.2em; margin-top: 0;">404 Not Found</h1>
  <p>Alamat yang kamu buka tidak tersedia di lab ini.</p>
  <a class="button" href="/" style="margin-top: 1em;">Kembali</a>
</div>
"""


FORBIDDEN_BODY = """
<div style="background: #ebf0f2; padding: 2em; border-radius: 5px; text-align: center; margin-top: 2em;">
  <h1 style="color: #d60000; font-size: 2.2em; margin-top: 0;">403 Forbidden</h1>
  <p>Kamu tidak memenuhi syarat untuk membuka halaman ini.</p>
  <a class="button" href="/" style="margin-top: 1em;">Kembali</a>
</div>
"""


def page(title, body_template, lab_num=None, is_solved=False, solved_flag=None, **context):
    body = render_template_string(
        body_template,
        lab_num=lab_num,
        is_solved=is_solved,
        solved_flag=solved_flag,
        **context,
    )
    return render_template_string(
        BASE_TEMPLATE,
        body=Markup(body),
        lab_title=title,
        lab_num=lab_num,
        is_solved=is_solved,
        solved_flag=solved_flag,
        **context,
    )


def get_flag(number):
    return current_app.config["FLAGS"][number]


def get_db():
    if "db" not in g:
        db = sqlite3.connect(current_app.config["DB_PATH"])
        db.row_factory = sqlite3.Row
        g.db = db
    return g.db


def ensure_balance():
    if "balance" not in session:
        session["balance"] = CREDIT
    return float(session["balance"])


def ensure_cart():
    if "cart" not in session or not isinstance(session["cart"], dict):
        session["cart"] = {}
    return session["cart"]


def get_lab3_state(username):
    if not username:
        return {}, CREDIT, False, None
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS lab3_carts (
            username TEXT PRIMARY KEY,
            cart_json TEXT NOT NULL DEFAULT '{}',
            balance REAL NOT NULL DEFAULT 100.0,
            solved INTEGER NOT NULL DEFAULT 0,
            receipt_json TEXT NOT NULL DEFAULT ''
        )
        """
    )
    try:
        db.execute("ALTER TABLE lab3_carts ADD COLUMN receipt_json TEXT NOT NULL DEFAULT ''")
        db.commit()
    except Exception:
        pass

    row = db.execute(
        "SELECT cart_json, balance, solved, receipt_json FROM lab3_carts WHERE username = ?",
        (username,),
    ).fetchone()
    if not row:
        db.execute(
            "INSERT OR IGNORE INTO lab3_carts (username, cart_json, balance, solved, receipt_json) VALUES (?, '{}', ?, 0, '')",
            (username, CREDIT),
        )
        db.commit()
        return {}, CREDIT, False, None
    try:
        cart = json.loads(row["cart_json"])
    except Exception:
        cart = {}
    receipt = None
    if row["receipt_json"]:
        try:
            receipt = json.loads(row["receipt_json"])
        except Exception:
            receipt = None
    return cart, float(row["balance"]), bool(row["solved"]), receipt


def save_lab3_state(username, cart=None, balance=None, solved=None, receipt=None):
    if not username:
        return
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS lab3_carts (
            username TEXT PRIMARY KEY,
            cart_json TEXT NOT NULL DEFAULT '{}',
            balance REAL NOT NULL DEFAULT 100.0,
            solved INTEGER NOT NULL DEFAULT 0,
            receipt_json TEXT NOT NULL DEFAULT ''
        )
        """
    )
    try:
        db.execute("ALTER TABLE lab3_carts ADD COLUMN receipt_json TEXT NOT NULL DEFAULT ''")
        db.commit()
    except Exception:
        pass
    db.execute(
        "INSERT OR IGNORE INTO lab3_carts (username, cart_json, balance, solved, receipt_json) VALUES (?, '{}', ?, 0, '')",
        (username, CREDIT),
    )
    if cart is not None:
        db.execute("UPDATE lab3_carts SET cart_json = ? WHERE username = ?", (json.dumps(cart), username))
    if balance is not None:
        db.execute("UPDATE lab3_carts SET balance = ? WHERE username = ?", (balance, username))
    if solved is not None:
        db.execute("UPDATE lab3_carts SET solved = ? WHERE username = ?", (1 if solved else 0, username))
    if receipt is not None:
        db.execute("UPDATE lab3_carts SET receipt_json = ? WHERE username = ?", (json.dumps(receipt), username))
    db.commit()


def ensure_cart_lab3():
    lab3_user = session.get("lab3_user")
    if lab3_user:
        cart, _, _, _ = get_lab3_state(lab3_user)
        session["cart_lab3"] = cart
        return cart
    if "cart_lab3" not in session or not isinstance(session["cart_lab3"], dict):
        session["cart_lab3"] = {}
    return session["cart_lab3"]


def get_lab4_state(username):
    if not username:
        return {}, CREDIT, False, None
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS lab4_carts (
            username TEXT PRIMARY KEY,
            cart_json TEXT NOT NULL DEFAULT '{}',
            balance REAL NOT NULL DEFAULT 100.0,
            solved INTEGER NOT NULL DEFAULT 0,
            receipt_json TEXT NOT NULL DEFAULT ''
        )
        """
    )
    try:
        db.execute("ALTER TABLE lab4_carts ADD COLUMN receipt_json TEXT NOT NULL DEFAULT ''")
        db.commit()
    except Exception:
        pass

    row = db.execute(
        "SELECT cart_json, balance, solved, receipt_json FROM lab4_carts WHERE username = ?",
        (username,),
    ).fetchone()
    if not row:
        db.execute(
            "INSERT OR IGNORE INTO lab4_carts (username, cart_json, balance, solved, receipt_json) VALUES (?, '{}', ?, 0, '')",
            (username, CREDIT),
        )
        db.commit()
        return {}, CREDIT, False, None
    try:
        cart = json.loads(row["cart_json"])
    except Exception:
        cart = {}
    receipt = None
    if row["receipt_json"]:
        try:
            receipt = json.loads(row["receipt_json"])
        except Exception:
            receipt = None
    return cart, float(row["balance"]), bool(row["solved"]), receipt


def save_lab4_state(username, cart=None, balance=None, solved=None, receipt=None):
    if not username:
        return
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS lab4_carts (
            username TEXT PRIMARY KEY,
            cart_json TEXT NOT NULL DEFAULT '{}',
            balance REAL NOT NULL DEFAULT 100.0,
            solved INTEGER NOT NULL DEFAULT 0,
            receipt_json TEXT NOT NULL DEFAULT ''
        )
        """
    )
    try:
        db.execute("ALTER TABLE lab4_carts ADD COLUMN receipt_json TEXT NOT NULL DEFAULT ''")
        db.commit()
    except Exception:
        pass
    db.execute(
        "INSERT OR IGNORE INTO lab4_carts (username, cart_json, balance, solved, receipt_json) VALUES (?, '{}', ?, 0, '')",
        (username, CREDIT),
    )
    if cart is not None:
        db.execute("UPDATE lab4_carts SET cart_json = ? WHERE username = ?", (json.dumps(cart), username))
    if balance is not None:
        db.execute("UPDATE lab4_carts SET balance = ? WHERE username = ?", (balance, username))
    if solved is not None:
        db.execute("UPDATE lab4_carts SET solved = ? WHERE username = ?", (1 if solved else 0, username))
    if receipt is not None:
        db.execute("UPDATE lab4_carts SET receipt_json = ? WHERE username = ?", (json.dumps(receipt), username))
    db.commit()


def ensure_cart_lab4():
    lab4_user = session.get("lab4_user")
    if lab4_user:
        cart, _, _, _ = get_lab4_state(lab4_user)
        session["cart"] = cart
        return cart
    if "cart" not in session or not isinstance(session["cart"], dict):
        session["cart"] = {}
    return session["cart"]


def ensure_lab6():
    if "lab6_price" not in session:
        session["lab6_price"] = 1337.0
    if "lab6_last_coupon" not in session:
        session["lab6_last_coupon"] = None
    if "lab6_qty" not in session:
        session["lab6_qty"] = 1
    return float(session["lab6_price"])


def ensure_lab5_tables():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS lab5_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    for col, col_def in [
        ("role", "TEXT NOT NULL DEFAULT 'user'"),
        ("is_admin", "INTEGER NOT NULL DEFAULT 0"),
        ("is_verified", "INTEGER NOT NULL DEFAULT 0"),
        ("verification_token", "TEXT"),
    ]:
        try:
            db.execute(f"ALTER TABLE members ADD COLUMN {col} {col_def}")
        except Exception:
            pass
    db.commit()

    row_j = db.execute("SELECT username FROM members WHERE username = 'jangannangis'").fetchone()
    if not row_j:
        db.execute(
            "INSERT OR REPLACE INTO members (username, password_hash, email, role, is_admin, is_verified) VALUES (?, ?, ?, ?, ?, ?)",
            ("jangannangis", generate_password_hash(os.urandom(8).hex()), "jangannangis@gembeng.com", "admin", 1, 1),
        )
    if not session.get("lab5_solved"):
        row_c = db.execute("SELECT username FROM members WHERE username = 'carlos'").fetchone()
        if not row_c:
            db.execute(
                "INSERT OR REPLACE INTO members (username, password_hash, email, role, is_admin, is_verified) VALUES (?, ?, ?, ?, ?, ?)",
                ("carlos", generate_password_hash(os.urandom(8).hex()), "carlos@exploit-lab.net", "user", 0, 1),
            )
    db.commit()


def current_member():
    username = session.get("member")
    if not username:
        return None
    ensure_lab5_tables()
    return get_db().execute(
        "SELECT username, password_hash, email, role, is_admin, is_verified FROM members WHERE username = ?",
        (username,),
    ).fetchone()


def init_db(path, flags):
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass

    db = sqlite3.connect(path)
    try:
        db.executescript(
            """
            DROP TABLE IF EXISTS products;
            DROP TABLE IF EXISTS users;
            DROP TABLE IF EXISTS members;
            DROP TABLE IF EXISTS lab5_emails;
            DROP TABLE IF EXISTS students;
            DROP TABLE IF EXISTS lab3_carts;
            DROP TABLE IF EXISTS lab4_carts;

            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT NOT NULL,
                image TEXT NOT NULL,
                rating INTEGER NOT NULL DEFAULT 3,
                released INTEGER NOT NULL
            );
            CREATE TABLE users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            );
            CREATE TABLE members (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                email TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                is_admin INTEGER NOT NULL DEFAULT 0,
                is_verified INTEGER NOT NULL DEFAULT 0,
                verification_token TEXT
            );
            CREATE TABLE lab5_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nis TEXT NOT NULL,
                name TEXT NOT NULL,
                subject TEXT NOT NULL,
                grade INTEGER NOT NULL,
                status TEXT NOT NULL
            );
            CREATE TABLE lab3_carts (
                username TEXT PRIMARY KEY,
                cart_json TEXT NOT NULL DEFAULT '{}',
                balance REAL NOT NULL DEFAULT 100.0,
                solved INTEGER NOT NULL DEFAULT 0,
                receipt_json TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE lab4_carts (
                username TEXT PRIMARY KEY,
                cart_json TEXT NOT NULL DEFAULT '{}',
                balance REAL NOT NULL DEFAULT 100.0,
                solved INTEGER NOT NULL DEFAULT 0,
                receipt_json TEXT NOT NULL DEFAULT ''
            );
            """
        )
        db.executemany(
            "INSERT INTO products (name, category, price, description, image, rating, released) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("Charizard Holo 1st Edition", "Vintage & Base Set", 1337.00, "Kartu legendaris Charizard Holographic 1st Edition dari Base Set 1999. Kondisi PSA 10 Gem Mint — mahakarya koleksi TCG dunia.", "/static/img/pokemon/charizard.jpg", 5, 1),
                ("Blastoise Base Set Holo", "Vintage & Base Set", 72.00, "Blastoise Holographic dari Base Set original. Kartu ikonik generasi pertama dengan artwork klasik Ken Sugimori.", "/static/img/pokemon/blastoise.jpg", 4, 1),
                ("Pikachu Illustrator Promo Card", "Promo & Secret Rare", 85.00, "Kartu promo ultra-langka Pikachu Illustrator dari kontes CoroCoro Comic 1998. Hanya 39 eksemplar di seluruh dunia.", "/static/img/pokemon/pikachu.jpg", 5, 1),
                ("Mewtwo GX Rainbow Rare", "Promo & Secret Rare", 42.50, "Mewtwo GX versi Rainbow Rare dari set Shining Legends. Full-art tekstur holografik premium bersinar pelangi.", "/static/img/pokemon/mewtwo.jpg", 4, 1),
                ("Eevee VMAX Alternate Art", "Modern & Alt Art", 38.00, "Eevee VMAX Alternate Art dari set Evolving Skies menampilkan karya seni memukau keluarga Eeveelutions.", "/static/img/pokemon/eeveelutions.jpg", 4, 1),
                ("Gengar VMAX Alt Art", "Modern & Alt Art", 55.00, "Gengar VMAX alternate art dari Fusion Strike #271. Desain raksasa ungu gelap yang sangat menonjol.", "/static/img/pokemon/gengar.jpg", 4, 1),
                ("Brilliant Stars Ultra Rare", "Modern & Alt Art", 90.00, "Kartu koleksi Ultra Rare dari set Brilliant Stars yang sangat diminati para kolektor kartu modern.", "/static/img/pokemon/brilliant_stars.jpg", 5, 1),
                ("Pokemon TCG Booster Pack Evolusi Mega Impian Ex", "Gifts", 4.99, "Paket booster resmi Evolusi Mega Impian Ex berisi 10 kartu acak dengan jaminan kartu foil berkilau.", "/static/img/pokemon/booster_pack.jpg", 4, 1),
                ("PokéCard Collector Deluxe Gift Box", "Gifts", 45.00, "Kotak hadiah edisi khusus kolektor berisi sleeve pelindung kartu, deck box premium, koin logam edisi terbatas, dan booster pack.", "/static/img/pokemon/booster_pack.jpg", 5, 1),
                ("PokéCard Trainer Starter Gift Pack", "Gifts", 15.00, "Set hadiah lengkap untuk pelatih pemula: deck siap main, playmat resmi, dadu status, dan buku panduan strategi turnamen.", "/static/img/pokemon/eeveelutions.jpg", 4, 1),
                (
                    "Charizard 1st Edition Shadowless (Secret Vault Edition)",
                    "Gifts",
                    0.0,
                    "Kartu legendaris dari brankas rahasia kolektor yang belum pernah dirilis ke publik. " + flags[1],
                    "/static/img/pokemon/charizard.jpg",
                    5,
                    0,
                ),
            ],
        )
        db.executemany(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            [
                ("administrator", os.urandom(8).hex()),
                ("wiener", "peter"),
                ("peter", "peter"),
            ],
        )
        db.executemany(
            "INSERT INTO members (username, password_hash, email, role, is_admin, is_verified) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("jangannangis", generate_password_hash(os.urandom(8).hex()), "jangannangis@gembeng.com", "admin", 1, 1),
                ("carlos", generate_password_hash(os.urandom(8).hex()), "carlos@exploit-lab.net", "user", 0, 1),
            ],
        )
        db.executemany(
            "INSERT INTO students (nis, name, subject, grade, status) VALUES (?, ?, ?, ?, ?)",
            [
                ("202401", "Budi Santoso", "Matematika Peminatan", 45, "Remedial"),
                ("202402", "Siti Rahma", "Matematika Peminatan", 88, "Tuntas"),
                ("202403", "Doni Setiawan", "Fisika Dasar", 72, "Tuntas"),
                ("202404", "Putri Anggraini", "Bahasa Inggris", 90, "Tuntas"),
                ("202405", "Rian Hidayat", "Kimia Terapan", 50, "Remedial"),
            ],
        )
        db.commit()
    finally:
        db.close()


@bp.before_request
def restrict_to_active_lab():
    lab = current_app.config["LAB"]
    if not lab:
        return None
    path = request.path
    if path == "/" or path == "/reset" or path == "/robots.txt":
        return None
    if path == f"/lab{lab}" or path.startswith(f"/lab{lab}/"):
        return None
    abort(404)


@bp.route("/")
def index():
    lab = current_app.config["LAB"]
    if lab:
        return redirect(f"/lab{lab}")
    return page("Web Security Academy", INDEX_BODY)


@bp.route("/reset", methods=["GET", "POST"])
def reset():
    session.clear()
    try:
        db = get_db()
        db.execute("DELETE FROM lab3_carts")
        db.execute("DELETE FROM lab4_carts")
        db.execute("DELETE FROM lab5_emails")
        db.execute("DELETE FROM members")
        db.executemany(
            "INSERT INTO members (username, password_hash, email, role, is_admin, is_verified) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("jangannangis", generate_password_hash(os.urandom(8).hex()), "jangannangis@gembeng.com", "admin", 1, 1),
                ("carlos", generate_password_hash(os.urandom(8).hex()), "carlos@exploit-lab.net", "user", 0, 1),
            ],
        )
        db.commit()
    except Exception:
        pass
    flash("Sesi dan data lab telah direset.", "info")
    lab = current_app.config["LAB"]
    return redirect(f"/lab{lab}" if lab else "/")


@bp.route("/lab1")
def lab1():
    products = []
    error = None
    category = request.args.get("category", "")
    try:
        if "category" in request.args:
            query = (
                "SELECT id, name, price, description, image, rating, released FROM products "
                f"WHERE category='{category}' AND released=1"
            )
        else:
            query = "SELECT id, name, price, description, image, rating, released FROM products WHERE released=1"
        products = get_db().execute(query).fetchall()
    except sqlite3.Error:
        error = "Terjadi kesalahan."
        products = []

    is_solved = any(p["released"] == 0 for p in products)
    solved_flag = get_flag(1) if is_solved else None

    return page(
        LAB_TITLES[1],
        LAB1_BODY,
        lab_num=1,
        is_solved=is_solved,
        solved_flag=solved_flag,
        products=products,
        error=error,
        category=category,
    )


@bp.route("/lab1/product")
def lab1_product():
    pid = request.args.get("productId", type=int)
    row = None
    if pid:
        row = get_db().execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
    if not row:
        abort(404)
    return page(
        LAB_TITLES[1],
        PRODUCT_DETAIL_BODY,
        lab_num=1,
        product_name=row["name"],
        product_price=row["price"],
        product_desc=row["description"],
        product_img=row["image"],
        product_rating=row["rating"],
        pid=row["id"],
    )


@bp.route("/lab2", methods=["GET", "POST"])
def lab2():
    message = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        query = (
            "SELECT username FROM users "
            f"WHERE username='{username}' AND password='{password}'"
        )
        try:
            row = get_db().execute(query).fetchone()
        except sqlite3.Error:
            row = None
            message = "Terjadi gangguan pada query basis data."
        else:
            if row and row["username"] == "administrator":
                session["lab2_user"] = "administrator"
                message = "Login berhasil sebagai Administrator Kurikulum."
            elif row:
                session["lab2_user"] = row["username"]
                message = (
                    f"Login berhasil sebagai {row['username']}, "
                    "tetapi halaman ini hanya untuk administrator."
                )
            else:
                message = "Username atau kata sandi tidak valid."

    logged_in_user = session.get("lab2_user")
    is_solved = bool(session.get("lab2_solved"))
    flag = get_flag(2) if is_solved else None
    students = []
    if logged_in_user == "administrator":
        students = get_db().execute("SELECT * FROM students ORDER BY id ASC").fetchall()

    return page(
        LAB_TITLES[2],
        LAB2_BODY,
        lab_num=2,
        is_solved=is_solved,
        solved_flag=flag,
        flag=flag,
        message=message,
        logged_in_user=logged_in_user,
        logged_in_admin=(logged_in_user == "administrator"),
        students=students,
    )


@bp.route("/lab2/update-grade", methods=["POST"])
def lab2_update_grade():
    logged_in_user = session.get("lab2_user")
    if logged_in_user != "administrator":
        flash("Akses ditolak. Anda harus login sebagai administrator untuk mengubah nilai rapor.", "error")
        return redirect("/lab2")

    student_id = request.form.get("student_id", type=int)
    grade = request.form.get("grade", type=int)

    if student_id is None or grade is None or grade < 0 or grade > 100:
        flash("Data siswa atau nilai tidak valid (0 - 100).", "error")
        return redirect("/lab2")

    status = "Tuntas" if grade >= 75 else "Remedial"
    db = get_db()
    db.execute(
        "UPDATE students SET grade = ?, status = ? WHERE id = ?",
        (grade, status, student_id),
    )
    db.commit()

    session["lab2_solved"] = True
    flash(f"Nilai siswa ID {student_id} berhasil diubah menjadi {grade} ({status}).", "success")
    return redirect("/lab2")


@bp.route("/lab2/logout")
def lab2_logout():
    session.pop("lab2_user", None)
    flash("Anda telah keluar dari akun.", "info")
    return redirect("/lab2")


@bp.route("/lab3", methods=["GET", "POST"])
def lab3():
    lab3_user = session.get("lab3_user")
    receipt = None
    if lab3_user:
        cart, balance, is_solved_db, receipt = get_lab3_state(lab3_user)
        session["cart_lab3"] = cart
        session["balance"] = balance
        if is_solved_db:
            session["lab3_solved"] = True
    else:
        balance = ensure_balance()
        cart = ensure_cart_lab3()

    if request.method == "POST" and lab3_user:
        action = request.form.get("action", "")

        if action == "add":
            pid = request.form.get("pid", type=int)
            price = request.form.get("price", type=float)
            qty = request.form.get("qty", 1, type=int)
            if pid not in SHOP or price is None or not math.isfinite(price) or qty <= 0:
                flash("Permintaan tidak valid.", "error")
                return redirect("/lab3")
            if price < 0:
                flash("Harga tidak boleh negatif.", "error")
                return redirect("/lab3")
            key = str(pid)
            old_qty = cart.get(key, {}).get("qty", 0) if isinstance(cart.get(key), dict) else 0
            cart[key] = {"qty": old_qty + qty, "price": round(price, 2)}
            save_lab3_state(lab3_user, cart=cart)
            session["cart_lab3"] = cart
            flash(f"{SHOP[pid][0]} ditambahkan ke keranjang.", "success")
            return redirect("/lab3")

        elif action == "empty":
            save_lab3_state(lab3_user, cart={})
            session["cart_lab3"] = {}
            flash("Keranjang belanja dikosongkan.", "success")
            return redirect("/lab3")

        elif action == "checkout":
            total = 0.0
            has_charizard = False
            purchased_items = []
            for pid_str, item in cart.items():
                pid = int(pid_str)
                if pid not in SHOP or not isinstance(item, dict):
                    continue
                qty = item.get("qty", 0)
                if qty <= 0:
                    continue
                price = item.get("price", SHOP[pid][1])
                subtotal = round(price * qty, 2)
                total += subtotal
                if pid == 1:
                    has_charizard = True
                purchased_items.append({
                    "pid": pid,
                    "name": SHOP[pid][0],
                    "price": price,
                    "qty": qty,
                    "subtotal": subtotal,
                })
            total = round(total, 2)
            if not purchased_items:
                flash("Keranjang belanja kosong.", "error")
                return redirect("/lab3")
            if total > balance:
                flash(f"Checkout ditolak. Total ${total:.2f}, kredit Anda ${balance:.2f}.", "error")
                return redirect("/lab3")
            if total < 0:
                flash("Total harga tidak valid.", "error")
                return redirect("/lab3")

            new_balance = round(balance - total, 2)
            now_dt = datetime.datetime.now()
            new_receipt = {
                "order_id": f"PKM-{now_dt.strftime('%Y%m%d%H%M%S')}",
                "date": now_dt.strftime("%d %b %Y, %H:%M WIB"),
                "items": purchased_items,
                "purchased_items": purchased_items,
                "total": total,
                "flag": get_flag(3) if has_charizard else None,
            }
            save_lab3_state(lab3_user, cart={}, balance=new_balance, solved=(True if has_charizard else None), receipt=new_receipt)
            session["balance"] = new_balance
            session["cart_lab3"] = {}
            session["lab3_receipt"] = new_receipt
            if has_charizard:
                session["lab3_solved"] = True
                flash("Pembelian berhasil diselesaikan! Bukti transaksi resmi Anda telah diterbitkan di bawah.", "success")
            else:
                flash("Pesanan berhasil dibuat! Bukti transaksi Anda telah diterbitkan di bawah.", "success")
            return redirect("/lab3")

        else:
            # Fallback for direct order without action (backwards compatibility)
            pid = request.form.get("pid", type=int)
            price = request.form.get("price", type=float)
            if pid not in SHOP or price is None or not math.isfinite(price):
                flash("Permintaan tidak valid.", "error")
                return redirect("/lab3")
            if price < 0 or price > balance:
                flash("Harga tidak valid atau saldo tidak cukup.", "error")
                return redirect("/lab3")
            new_balance = round(balance - price, 2)
            has_charizard = (pid == 1)
            now_dt = datetime.datetime.now()
            purchased_items = [{
                "pid": pid,
                "name": SHOP[pid][0],
                "price": price,
                "qty": 1,
                "subtotal": round(price, 2),
            }]
            new_receipt = {
                "order_id": f"PKM-{now_dt.strftime('%Y%m%d%H%M%S')}",
                "date": now_dt.strftime("%d %b %Y, %H:%M WIB"),
                "items": purchased_items,
                "purchased_items": purchased_items,
                "total": round(price, 2),
                "flag": get_flag(3) if has_charizard else None,
            }
            save_lab3_state(lab3_user, balance=new_balance, solved=(True if has_charizard else None), receipt=new_receipt)
            session["balance"] = new_balance
            session["lab3_receipt"] = new_receipt
            if pid == 1:
                session["lab3_solved"] = True
                flash("Pembelian berhasil diselesaikan! Bukti transaksi resmi Anda telah diterbitkan di bawah.", "success")
            else:
                flash(f"Berhasil membeli {SHOP[pid][0]}.", "success")
            return redirect("/lab3")

    elif request.method == "POST" and not lab3_user:
        flash("Silakan login terlebih dahulu untuk membeli barang.", "error")
        return redirect("/lab3/login")

    items = []
    total = 0.0
    total_qty = 0
    if lab3_user:
        for pid_str, item in cart.items():
            pid = int(pid_str)
            if pid not in SHOP or not isinstance(item, dict):
                continue
            qty = item.get("qty", 0)
            if qty <= 0:
                continue
            price = item.get("price", SHOP[pid][1])
            subtotal = round(price * qty, 2)
            total += subtotal
            total_qty += qty
            items.append({
                "pid": pid,
                "name": SHOP[pid][0],
                "price": price,
                "qty": qty,
                "subtotal": subtotal,
            })
        total = round(total, 2)

    is_solved = bool(session.get("lab3_solved"))
    solved_flag = get_flag(3) if is_solved else None

    return page(
        LAB_TITLES[3],
        LAB3_BODY,
        lab_num=3,
        is_solved=is_solved,
        solved_flag=solved_flag,
        balance=balance,
        shop=SHOP,
        items=items,
        total=total,
        cart_count=total_qty,
        lab3_user=lab3_user,
        receipt=receipt,
    )


@bp.route("/lab3/login", methods=["GET", "POST"])
def lab3_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == "wiener" and password == "peter":
            session["lab3_user"] = username
            flash(f"Selamat datang, {username}! Anda telah berhasil login.", "success")
            return redirect("/lab3")
        flash("Username atau password salah.", "error")
        return redirect("/lab3/login")

    if session.get("lab3_user"):
        return redirect("/lab3")

    return page(
        "Login Pelanggan",
        LAB3_LOGIN_BODY,
        lab_num=3,
        lab3_user=None,
    )


@bp.route("/lab3/logout")
def lab3_logout():
    session.pop("lab3_user", None)
    flash("Anda telah keluar dari akun.", "info")
    return redirect("/lab3")


@bp.route("/lab3/product")
def lab3_product():
    pid = request.args.get("productId", type=int)
    if pid not in SHOP:
        abort(404)
    item = SHOP[pid]
    lab3_user = session.get("lab3_user")
    if lab3_user:
        cart, balance, is_solved_db, _ = get_lab3_state(lab3_user)
        session["cart_lab3"] = cart
        session["balance"] = balance
        if is_solved_db:
            session["lab3_solved"] = True
    else:
        balance = ensure_balance()
        cart = ensure_cart_lab3()
    is_solved = bool(session.get("lab3_solved"))
    solved_flag = get_flag(3) if is_solved else None
    total_qty = sum(i.get("qty", 0) for i in cart.values() if isinstance(i, dict))
    return page(
        LAB_TITLES[3],
        PRODUCT_DETAIL_BODY,
        lab_num=3,
        is_solved=is_solved,
        solved_flag=solved_flag,
        pid=pid,
        product_name=item[0],
        product_price=item[1],
        product_img=item[2],
        product_rating=item[3],
        product_desc=item[4],
        balance=balance,
        cart_count=total_qty,
        lab3_user=lab3_user,
    )


@bp.route("/lab4", methods=["GET", "POST"])
def lab4():
    lab4_user = session.get("lab4_user")
    receipt = None
    if lab4_user:
        cart, balance, is_solved_db, receipt = get_lab4_state(lab4_user)
        session["cart"] = cart
        if is_solved_db:
            session["lab4_solved"] = True
    else:
        balance = CREDIT
        cart = {}

    if request.method == "POST" and lab4_user:
        action = request.form.get("action", "")

        if action == "add":
            pid = request.form.get("pid", type=int)
            qty = request.form.get("qty", type=int)
            if pid not in SHOP or qty is None:
                flash("Produk atau jumlah tidak valid.", "error")
                return redirect("/lab4")
            key = str(pid)
            new_qty = cart.get(key, 0) + qty
            if new_qty == 0:
                del cart[key]
                save_lab4_state(lab4_user, cart=cart)
                session["cart"] = cart
                flash(f"{SHOP[pid][0]} dihapus dari keranjang.", "success")
                return redirect("/lab4")
            cart[key] = new_qty
            save_lab4_state(lab4_user, cart=cart)
            session["cart"] = cart
            if qty > 0:
                flash(f"{SHOP[pid][0]} ditambahkan ke keranjang.", "success")
            else:
                flash(f"Jumlah {SHOP[pid][0]} diperbarui.", "success")
            return redirect("/lab4")

        elif action == "empty":
            save_lab4_state(lab4_user, cart={})
            session["cart"] = {}
            flash("Keranjang belanja dikosongkan.", "success")
            return redirect("/lab4")

        elif action == "checkout":
            items_checkout = []
            total = 0.0
            has_charizard = False
            for key, qty in cart.items():
                pid = int(key)
                if pid not in SHOP:
                    continue
                name, unit_price = SHOP[pid][0], SHOP[pid][1]
                subtotal = round(unit_price * qty, 2)
                total += subtotal
                if pid == 1 and qty > 0:
                    has_charizard = True
                items_checkout.append(
                    {"pid": pid, "name": name, "price": unit_price, "qty": qty, "subtotal": subtotal}
                )
            total = round(total, 2)

            if not items_checkout:
                flash("Keranjang belanja kosong.", "error")
                return redirect("/lab4")

            if cart.get("1", 0) > 0 and 0 <= total <= CREDIT:
                new_balance = round(balance - total, 2)
                now_dt = datetime.datetime.now()
                new_receipt = {
                    "order_id": f"PKM-{now_dt.strftime('%Y%m%d%H%M%S')}",
                    "date": now_dt.strftime("%d %b %Y, %H:%M WIB"),
                    "items": items_checkout,
                    "purchased_items": items_checkout,
                    "total": total,
                    "flag": get_flag(4) if has_charizard else None,
                }
                save_lab4_state(lab4_user, cart={}, balance=new_balance, solved=(True if has_charizard else None), receipt=new_receipt)
                session["cart"] = {}
                session["lab4_solved"] = True
                flash("Pembelian berhasil diselesaikan! Bukti transaksi resmi Anda telah diterbitkan di bawah.", "success")
                return redirect("/lab4")

            flash(
                f"Checkout ditolak. Total ${total:.2f}, kredit ${CREDIT:.2f}.",
                "error",
            )
            return redirect("/lab4")

    elif request.method == "POST" and not lab4_user:
        flash("Silakan login terlebih dahulu untuk membeli barang.", "error")
        return redirect("/lab4/login")

    items = []
    total = 0.0
    total_qty = 0
    if lab4_user:
        for key, qty in cart.items():
            pid = int(key)
            if pid not in SHOP:
                continue
            name, unit_price = SHOP[pid][0], SHOP[pid][1]
            subtotal = round(unit_price * qty, 2)
            total += subtotal
            total_qty += abs(qty)
            items.append(
                {"pid": pid, "name": name, "price": unit_price, "qty": qty, "subtotal": subtotal}
            )
        total = round(total, 2)

    is_solved = bool(session.get("lab4_solved"))
    solved_flag = get_flag(4) if is_solved else None

    return page(
        LAB_TITLES[4],
        LAB4_BODY,
        lab_num=4,
        is_solved=is_solved,
        solved_flag=solved_flag,
        items=items,
        total=round(total, 2),
        credit=CREDIT,
        shop=SHOP,
        cart_count=total_qty,
        balance=balance,
        lab4_user=lab4_user,
        receipt=receipt,
    )


@bp.route("/lab4/login", methods=["GET", "POST"])
def lab4_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == "wiener" and password == "peter":
            session["lab4_user"] = username
            flash(f"Selamat datang, {username}! Anda telah berhasil login.", "success")
            return redirect("/lab4")
        flash("Username atau password salah.", "error")
        return redirect("/lab4/login")

    if session.get("lab4_user"):
        return redirect("/lab4")

    return page(
        "Login Pelanggan",
        LAB4_LOGIN_BODY,
        lab_num=4,
        lab4_user=None,
    )


@bp.route("/lab4/logout")
def lab4_logout():
    session.pop("lab4_user", None)
    flash("Anda telah keluar dari akun.", "info")
    return redirect("/lab4")


@bp.route("/lab4/product")
def lab4_product():
    pid = request.args.get("productId", type=int)
    if pid not in SHOP:
        abort(404)
    item = SHOP[pid]
    lab4_user = session.get("lab4_user")
    if lab4_user:
        cart, balance, is_solved_db, _ = get_lab4_state(lab4_user)
        session["cart"] = cart
        if is_solved_db:
            session["lab4_solved"] = True
    else:
        balance = CREDIT
        cart = {}
    is_solved = bool(session.get("lab4_solved"))
    solved_flag = get_flag(4) if is_solved else None
    total_qty = sum(abs(v) for v in cart.values())
    return page(
        LAB_TITLES[4],
        PRODUCT_DETAIL_BODY,
        lab_num=4,
        is_solved=is_solved,
        solved_flag=solved_flag,
        pid=pid,
        product_name=item[0],
        product_price=item[1],
        product_img=item[2],
        product_rating=item[3],
        product_desc=item[4],
        cart_count=total_qty,
        balance=balance,
        lab4_user=lab4_user,
    )


@bp.route("/robots.txt")
@bp.route("/lab5/robots.txt")
def lab5_robots_txt():
    content = "User-agent: *\nDisallow: /lab5/admin-panel\n"
    return current_app.response_class(content, mimetype="text/plain")


@bp.route("/lab5")
def lab5():
    ensure_lab5_tables()
    member = current_member()
    is_solved = bool(session.get("lab5_solved"))
    solved_flag = get_flag(5) if is_solved else None
    return page(
        LAB_TITLES[5],
        LAB5_BODY,
        lab_num=5,
        is_solved=is_solved,
        solved_flag=solved_flag,
        member=member,
        shop=SHOP,
    )


@bp.route("/lab5/product")
def lab5_product():
    ensure_lab5_tables()
    pid = request.args.get("productId", type=int)
    if pid not in SHOP:
        abort(404)
    item = SHOP[pid]
    member = current_member()
    is_solved = bool(session.get("lab5_solved"))
    solved_flag = get_flag(5) if is_solved else None
    return page(
        LAB_TITLES[5],
        PRODUCT_DETAIL_BODY,
        lab_num=5,
        is_solved=is_solved,
        solved_flag=solved_flag,
        pid=pid,
        product_name=item[0],
        product_price=item[1],
        product_img=item[2],
        product_rating=item[3],
        product_desc=item[4],
        member=member,
    )


@bp.route("/lab5/login", methods=["GET", "POST"])
def lab5_login():
    ensure_lab5_tables()
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        row = get_db().execute(
            "SELECT username, password_hash, email, role, is_admin, is_verified FROM members WHERE username = ?",
            (username,),
        ).fetchone()

        if row and check_password_hash(row["password_hash"], password):
            if not row["is_verified"]:
                flash("Akun belum diverifikasi. Silakan periksa Email Client Anda untuk mengklik tautan aktivasi.", "error")
                return redirect("/lab5/login")
            session["member"] = row["username"]
            flash(f"Selamat datang, {row['username']}! Anda telah berhasil login.", "success")
            return redirect("/lab5/my-account")
        else:
            flash("Username atau password salah.", "error")
            return redirect("/lab5/login")

    member = current_member()
    if member:
        return redirect("/lab5/my-account")

    return page(
        "Masuk ke Akun",
        LAB5_LOGIN_BODY,
        lab_num=5,
        member=None,
    )


@bp.route("/lab5/register", methods=["GET", "POST"])
def lab5_register():
    ensure_lab5_tables()
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip()

        if not username or not password or not email:
            flash("Username, password, dan email wajib diisi.", "error")
            return redirect("/lab5/register")

        db = get_db()
        existing = db.execute("SELECT username FROM members WHERE username = ?", (username,)).fetchone()
        if existing:
            flash("Username sudah terdaftar.", "error")
            return redirect("/lab5/register")

        token = secrets.token_hex(16)
        pw_hash = generate_password_hash(password)

        db.execute(
            "INSERT INTO members (username, password_hash, email, role, is_admin, is_verified, verification_token) VALUES (?, ?, ?, 'user', 0, 0, ?)",
            (username, pw_hash, email, token),
        )
        db.commit()

        if email.lower().endswith("@exploit-lab.net"):
            now_str = datetime.datetime.now().strftime("%d %b %Y, %H:%M WIB")
            verify_url = f"/lab5/verify?token={token}"
            email_body = f"""
            <p>Halo <strong>{username}</strong>,</p>
            <p>Terima kasih telah mendaftar di Portal Akun Lab 5.</p>
            <p>Silakan klik tombol atau tautan di bawah ini untuk memverifikasi akun Anda:</p>
            <p style="margin: 20px 0;">
              <a href="{verify_url}" style="display: inline-block; background: #0071bc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-weight: bold;">
                Aktivasi Akun Saya
              </a>
            </p>
            <p style="font-size: 0.85em; color: #718096;">
              Atau buka link verifikasi berikut di peramban Anda:<br>
              <a href="{verify_url}" style="color: #0071bc;">{verify_url}</a>
            </p>
            """
            db.execute(
                "INSERT INTO lab5_emails (recipient, subject, body, created_at) VALUES (?, ?, ?, ?)",
                (email, "Verifikasi Pendaftaran Akun", email_body, now_str),
            )
            db.commit()
            flash("Pendaftaran berhasil! Tautan verifikasi telah dikirim ke Email Client Anda (@exploit-lab.net). Silakan verifikasi akun Anda sebelum login.", "success")
        else:
            # Registered with external domain (e.g. @gembeng.com)
            flash(f"Pendaftaran berhasil! Tautan verifikasi telah dikirim ke {email}. Harap periksa kotak masuk email Anda untuk verifikasi.", "info")

        return redirect("/lab5/login")

    member = current_member()
    if member:
        return redirect("/lab5/my-account")

    return page(
        "Daftar Akun Baru",
        LAB5_REGISTER_BODY,
        lab_num=5,
        member=None,
    )


@bp.route("/lab5/my-account")
def lab5_my_account():
    ensure_lab5_tables()
    member = current_member()
    if not member:
        flash("Silakan login terlebih dahulu untuk mengakses halaman My Account.", "error")
        return redirect("/lab5/login")

    is_solved = bool(session.get("lab5_solved"))
    solved_flag = get_flag(5) if is_solved else None

    return page(
        "My Account",
        LAB5_MY_ACCOUNT_BODY,
        lab_num=5,
        member=member,
        is_solved=is_solved,
        solved_flag=solved_flag,
    )


@bp.route("/lab5/verify")
def lab5_verify():
    ensure_lab5_tables()
    token = request.args.get("token", "").strip()
    if not token:
        flash("Token verifikasi tidak valid.", "error")
        return redirect("/lab5/login")

    db = get_db()
    row = db.execute(
        "SELECT username FROM members WHERE verification_token = ? AND is_verified = 0",
        (token,),
    ).fetchone()

    if not row:
        flash("Tautan verifikasi tidak valid atau akun sudah diverifikasi sebelumnya.", "error")
        return redirect("/lab5/login")

    db.execute(
        "UPDATE members SET is_verified = 1, verification_token = NULL WHERE verification_token = ?",
        (token,),
    )
    db.commit()
    flash(f"Akun '{row['username']}' berhasil diverifikasi! Silakan masuk dengan akun Anda.", "success")
    return redirect("/lab5/login")


@bp.route("/lab5/update-email", methods=["POST"])
def lab5_update_email():
    ensure_lab5_tables()
    member = current_member()
    if not member:
        flash("Silakan login terlebih dahulu.", "error")
        return redirect("/lab5/login")

    email = request.form.get("email", "").strip()
    if not email:
        flash("Email tidak boleh kosong.", "error")
        return redirect("/lab5/my-account")

    db = get_db()
    if email.lower().endswith("@gembeng.com"):
        db.execute(
            "UPDATE members SET email = ?, role = 'admin', is_admin = 1 WHERE username = ?",
            (email, member["username"]),
        )
        db.commit()
        flash(f"Email berhasil diperbarui ke {email}. Hak akses administrator (@gembeng.com) telah aktif!", "success")
    else:
        db.execute(
            "UPDATE members SET email = ?, role = 'user', is_admin = 0 WHERE username = ?",
            (email, member["username"]),
        )
        db.commit()
        flash(f"Email berhasil diperbarui ke {email}.", "success")

    return redirect("/lab5/my-account")


@bp.route("/lab5/admin")
@bp.route("/lab5/admin-panel")
def lab5_admin_panel():
    ensure_lab5_tables()
    member = current_member()
    if not member:
        return page(
            "Admin Panel - Akses Ditolak",
            LAB5_ADMIN_DENIED_BODY,
            lab_num=5,
            member=None,
        )

    if not member["is_admin"]:
        return page(
            "Admin Panel - Akses Ditolak",
            LAB5_ADMIN_DENIED_BODY,
            lab_num=5,
            member=member,
        )

    db = get_db()
    users = db.execute(
        "SELECT username, email, role, is_admin FROM members ORDER BY CASE WHEN username='jangannangis' THEN 0 WHEN username='carlos' THEN 1 ELSE 2 END, username ASC"
    ).fetchall()

    is_solved = bool(session.get("lab5_solved"))
    solved_flag = get_flag(5) if is_solved else None

    return page(
        "Admin Panel",
        LAB5_ADMIN_BODY,
        lab_num=5,
        member=member,
        users=users,
        is_solved=is_solved,
        solved_flag=solved_flag,
        flag=solved_flag,
    )


@bp.route("/lab5/admin/delete", methods=["POST"])
def lab5_admin_delete():
    ensure_lab5_tables()
    member = current_member()
    if not member or not member["is_admin"]:
        abort(403)

    target = request.form.get("username", "").strip()
    if not target:
        flash("Username target tidak boleh kosong.", "error")
        return redirect("/lab5/admin-panel")

    if target == "jangannangis":
        flash("Akun administrator utama jangannangis tidak dapat dihapus.", "error")
        return redirect("/lab5/admin-panel")

    if target == member["username"]:
        flash("Anda tidak dapat menghapus akun Anda sendiri.", "error")
        return redirect("/lab5/admin-panel")

    db = get_db()
    db.execute("DELETE FROM members WHERE username = ?", (target,))
    db.commit()

    if target == "carlos":
        session["lab5_solved"] = True
        flash("Pengguna 'carlos' berhasil dihapus dari sistem! Misi Lab 5 terselesaikan.", "success")
    else:
        flash(f"Pengguna '{target}' berhasil dihapus.", "info")

    return redirect("/lab5/admin-panel")


@bp.route("/lab5/email-client")
def lab5_email_client():
    ensure_lab5_tables()
    db = get_db()
    emails = db.execute("SELECT id, recipient, subject, body, created_at FROM lab5_emails ORDER BY id DESC").fetchall()
    view_id = request.args.get("id", type=int)
    selected_email = None
    if view_id:
        selected_email = db.execute("SELECT id, recipient, subject, body, created_at FROM lab5_emails WHERE id = ?", (view_id,)).fetchone()
    elif emails:
        selected_email = emails[0]

    return page(
        "Email Client",
        LAB5_EMAIL_CLIENT_BODY,
        lab_num=5,
        emails=emails,
        selected_email=selected_email,
        member=current_member(),
    )


@bp.route("/lab5/email-client/clear", methods=["POST"])
def lab5_email_client_clear():
    ensure_lab5_tables()
    db = get_db()
    db.execute("DELETE FROM lab5_emails")
    db.commit()
    flash("Kotak masuk Email Client berhasil dikosongkan.", "info")
    return redirect("/lab5/email-client")


@bp.route("/lab5/logout")
def lab5_logout():
    session.pop("member", None)
    flash("Anda telah berhasil keluar dari akun.", "info")
    return redirect("/lab5")


@bp.route("/lab6", methods=["GET", "POST"])
def lab6():
    price = ensure_lab6()
    if request.method == "POST":
        action = request.form.get("action", "")
        if action in ("add", "qty", "update"):
            qty_change = request.form.get("qty", type=int)
            if qty_change is None:
                qty_change = request.form.get("change", type=int) or 1
            current_qty = session.get("lab6_qty", 1)
            new_qty = current_qty + qty_change
            if new_qty < 1:
                session["lab6_qty"] = 1
                flash("Barang yang sudah masuk keranjang tidak dapat dihilangkan (jumlah minimal adalah 1).", "error")
            else:
                session["lab6_qty"] = new_qty
                flash("Jumlah barang di keranjang berhasil diperbarui.", "success")
            return redirect("/lab6/cart")

    qty = session.get("lab6_qty", 1)
    total = round(price * qty, 2)
    is_solved = bool(session.get("lab6_solved"))
    solved_flag = get_flag(6) if is_solved else None
    return page(
        LAB_TITLES[6],
        LAB6_BODY,
        lab_num=6,
        is_solved=is_solved,
        solved_flag=solved_flag,
        shop=SHOP,
        price=price,
        qty=qty,
        total=total,
        lab6_qty=qty,
        credit=CREDIT,
        lab6_user=session.get("lab6_user"),
    )


@bp.route("/lab6/product")
def lab6_product():
    pid = request.args.get("productId", type=int)
    if pid not in SHOP:
        abort(404)
    item = SHOP[pid]
    is_solved = bool(session.get("lab6_solved"))
    solved_flag = get_flag(6) if is_solved else None
    return page(
        LAB_TITLES[6],
        PRODUCT_DETAIL_BODY,
        lab_num=6,
        is_solved=is_solved,
        solved_flag=solved_flag,
        pid=pid,
        product_id=pid,
        product_name=item[0],
        product_price=item[1],
        product_img=item[2],
        product_rating=item[3],
        product_desc=item[4],
        credit=CREDIT,
        lab6_user=session.get("lab6_user"),
    )


@bp.route("/lab6/cart", methods=["GET", "POST"])
def lab6_cart():
    price = ensure_lab6()
    if request.method == "POST":
        action = request.form.get("action", "")
        qty_change = request.form.get("qty", type=int)
        if qty_change is None:
            qty_change = request.form.get("change", type=int)

        current_qty = session.get("lab6_qty", 1)
        if action in ("add", "qty", "update"):
            if qty_change is not None:
                new_qty = current_qty + qty_change
            else:
                new_qty = request.form.get("quantity", type=int) or current_qty

            if new_qty < 1:
                session["lab6_qty"] = 1
                flash("Barang yang sudah masuk keranjang tidak dapat dihilangkan (jumlah minimal adalah 1).", "error")
            else:
                session["lab6_qty"] = new_qty
                if new_qty > current_qty:
                    flash("Jumlah barang di keranjang berhasil ditambahkan.", "success")
                elif new_qty < current_qty:
                    flash("Jumlah barang di keranjang berhasil dikurangi.", "success")
            return redirect("/lab6/cart")
        elif action == "empty":
            flash("Barang yang sudah masuk keranjang tidak dapat dihilangkan.", "error")
            return redirect("/lab6/cart")

    qty = session.get("lab6_qty", 1)
    total = round(price * qty, 2)
    is_solved = bool(session.get("lab6_solved"))
    solved_flag = get_flag(6) if is_solved else None
    receipt = session.get("lab6_receipt")
    return page(
        "Keranjang Belanja",
        LAB6_CART_BODY,
        lab_num=6,
        is_solved=is_solved,
        solved_flag=solved_flag,
        price=price,
        qty=qty,
        total=total,
        lab6_qty=qty,
        credit=CREDIT,
        receipt=receipt,
        lab6_user=session.get("lab6_user"),
    )


@bp.route("/lab6/register", methods=["GET", "POST"])
def lab6_register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        session["lab6_user"] = username or "pelanggan"
        flash(f"Pendaftaran berhasil! Selamat datang, {session['lab6_user']}! Anda mendapatkan kupon member baru: NEWCUST5 (potongan $5). Gunakan kode ini saat checkout!", "success")
        return redirect("/lab6/cart")

    return page(
        "Daftar Akun",
        LAB6_REGISTER_BODY,
        lab_num=6,
        credit=CREDIT,
    )


@bp.route("/lab6/login", methods=["GET", "POST"])
def lab6_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        session["lab6_user"] = username or "pelanggan"
        flash(f"Selamat datang kembali, {session['lab6_user']}! Anda telah berhasil login.", "success")
        return redirect("/lab6")

    return page(
        "Masuk ke Akun",
        LAB6_LOGIN_BODY,
        lab_num=6,
        credit=CREDIT,
    )


@bp.route("/lab6/logout")
def lab6_logout():
    session.pop("lab6_user", None)
    flash("Anda telah berhasil keluar dari akun.", "info")
    return redirect("/lab6")


@bp.route("/lab6/newsletter", methods=["POST"])
def lab6_newsletter():
    email = request.form.get("email", "").strip()
    flash("Terima kasih telah berlangganan Berita Koran Kabar Pokémon! Selamat, Anda mendapatkan kupon diskon 30%: SIGNUP30. Gunakan kode ini di keranjang belanja!", "success")
    return redirect("/lab6")


@bp.route("/lab6/coupon", methods=["POST"])
def lab6_coupon():
    ensure_lab6()
    code = request.form.get("code", "").strip().upper()
    last_coupon = session.get("lab6_last_coupon")
    if not code:
        flash("Kode kupon tidak boleh kosong.", "error")
    elif code == last_coupon:
        flash("Kupon yang sama tidak bisa dipakai dua kali berturut-turut.", "error")
    elif code == "NEWCUST5":
        session["lab6_price"] = round(max(0.0, float(session["lab6_price"]) - 5.0), 2)
        session["lab6_last_coupon"] = code
        flash("Kupon NEWCUST5 diterapkan: potongan $5.", "success")
    elif code == "SIGNUP30":
        session["lab6_price"] = round(float(session["lab6_price"]) * 0.7, 2)
        session["lab6_last_coupon"] = code
        flash("Kupon SIGNUP30 diterapkan: diskon 30%.", "success")
    else:
        flash("Kode kupon tidak dikenal.", "error")
    return redirect("/lab6/cart")


@bp.route("/lab6/checkout", methods=["POST"])
def lab6_checkout():
    lab6_user = session.get("lab6_user")
    if not lab6_user:
        flash("Silakan masuk atau daftar akun terlebih dahulu untuk melihat kredit dan menyelesaikan checkout.", "error")
        return redirect("/lab6/login")

    price = ensure_lab6()
    qty = session.get("lab6_qty", 1)
    total = round(price * qty, 2)
    if total <= CREDIT:
        session["lab6_solved"] = True
        now_dt = datetime.datetime.now()
        receipt = {
            "order_id": f"PKM-{now_dt.strftime('%Y%m%d%H%M%S')}",
            "date": now_dt.strftime("%d %b %Y, %H:%M WIB"),
            "items": [
                {
                    "pid": 1,
                    "name": "Charizard Holo 1st Edition",
                    "price": 1337.0,
                    "qty": qty,
                    "subtotal": total,
                }
            ],
            "total": total,
            "flag": get_flag(6),
        }
        session["lab6_receipt"] = receipt
        flash(f"Pembelian berhasil diselesaikan! {get_flag(6)}", "success")
        return redirect("/lab6/cart")
    else:
        flash(
            f"Checkout ditolak. Total tagihan ${total:.2f}, kredit Anda ${CREDIT:.2f}.",
            "error",
        )
        return redirect("/lab6/cart")


def create_app():
    lab = os.environ.get("LAB", "").strip()
    if lab and lab not in {str(number) for number in range(1, 7)}:
        raise ValueError("LAB harus bernilai 1-6 atau kosong.")

    app = Flask(__name__, static_folder="static")
    app.secret_key = os.environ.get(f"SECRET_KEY_{lab}") or os.environ.get(
        "SECRET_KEY", "dev-only-insecure-secret"
    )
    app.config["LAB"] = lab
    app.config["FLAGS"] = {
        number: os.environ.get(f"FLAG_{number}", f"CTF{{dev_only_lab_{number}}}")
        for number in range(1, 7)
    }
    db_default = os.path.join(tempfile.gettempdir(), "ctf_lab.db")
    app.config["DB_PATH"] = os.environ.get("DB_PATH", db_default)

    init_db(app.config["DB_PATH"], app.config["FLAGS"])
    app.register_blueprint(bp)

    @app.teardown_appcontext
    def close_db(exception):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.errorhandler(404)
    def not_found(error):
        return page("404 Not Found", NOT_FOUND_BODY), 404

    @app.errorhandler(403)
    def forbidden(error):
        return page("403 Forbidden", FORBIDDEN_BODY), 403

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
