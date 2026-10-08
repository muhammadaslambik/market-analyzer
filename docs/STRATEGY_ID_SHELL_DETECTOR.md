Strategi investasi Andry Hakim—yang dikenal di pasar saham Indonesia dengan julukan "Koko Backdoor Listing" atau filosofi "Cacing-Cacing Naga-Naga"—berfokus pada pencarian saham multibagger melalui aksi korporasi besar. Logika dasarnya adalah mencari perusahaan kecil ("cacing") dengan kinerja buruk yang akan dicaplok, diubah, atau disuntik aset raksasa (right issue / backdoor listing) oleh konglomerat atau investor visioner menjadi perusahaan raksasa ("naga").
Karena strategi ini bersifat event-driven (berbasis peristiwa korporasi), indikator teknikal murni seperti RSI atau MACD tidak bisa mendeteksinya. Mesin analisa Anda harus mengadopsi kombinasi filter fundamental (metrik kondisi "jelek"), data aksi korporasi, dan anomali volume.
Berikut adalah rancangan indikator dan metrik yang harus ditanamkan ke dalam mesin analisa Anda jika ingin mendeteksi saham tipe Andry Hakim:

1. Indikator Kondisi Perusahaan "Jelek" (Filter Awal)

Mesin Anda harus menyaring saham-saham yang secara fundamental terlihat hancur atau tidak menarik bagi investor ritel biasa, namun memiliki cangkang (shell) yang bersih untuk dicaplok.
• PBV (Price to Book Value) Rendah atau Negatif: Menyaring saham dengan harga pasar yang sudah sangat murah dibanding nilai bukunya, atau perusahaan yang ekuitasnya hampir habis (kandidat restrukturisasi).
• Kapitalisasi Pasar Kecil (Small Cap / Micro Cap): Batasi kapitalisasi pasar di bawah angka tertentu (misalnya < Rp 500 Miliar). Perusahaan kecil lebih murah dan lebih mudah untuk dicaplok melalui backdoor listing ketimbang perusahaan besar.
• Pendapatan Macet / Rugi Operasional: Screener mencari emiten yang tren laba bersihnya negatif atau pendapatannya stagnan, menandakan bisnis lamanya sudah mati dan pemilik lama kemungkinan besar bersedia menjual cangkang perusahaannya.

2. Indikator Struktur Kepemilikan (Penting untuk Menghindari Risiko)

Andry Hakim sering menekankan pentingnya melihat siapa pemilik di balik perusahaan tersebut.
• Kepemilikan Saham Publik Sangat Rendah (Saham Warkat/Tertidur): Saring saham yang kepemilikan masyarakatnya (free float) mendekati batas minimal regulasi (misal hanya 7%–15%). Mayoritas saham dikuasai pengendali tunggal. Ini membuat harga sangat mudah melesat (ringan) saat ada rumor positif karena suplai saham di pasar sangat sedikit.
• Pencarian Entitas Afiliasi (Text Mining Indicator): Buat algoritma pemindai berita korporasi untuk mendeteksi perpindahan kepemilikan minoritas ke nama-nama konglomerat, venture capital, atau holding company visioner sebelum right issue resmi diumumkan.

3. Indikator "Jejak Digital" Keterbukaan Informasi & Legalitas

Ini adalah indikator rahasia yang sering terlihat sebelum aksi korporasi besar seperti backdoor listing terjadi.
• Laporan Keuangan Audit Sukarela / Interim (Non-Kuartal IV): Biasanya perusahaan berskala kecil hanya mengaudit laporan keuangan tahunan (Kuartal IV). Jika mesin mendeteksi emiten kecil tiba-tiba melakukan Audit Laporan Keuangan pada Kuartal I, II, atau III, itu adalah indikator kuat (>80%) bahwa mereka sedang menyiapkan dokumen untuk Right Issue atau aksi korporasi besar.
• Keterbukaan Informasi Terkait RUPS / RUPSLB: Mesin harus menangkap kata kunci (keyword) spesifik pada keterbukaan informasi BEI seperti: "Perubahan Pengendali", "Peningkatan Modal Tanpa Hak Memesan Efek Terlebih Dahulu (PMTHMETD/Private Placement)", atau "Akuisisi".

4. Indikator Teknikal Kuantitatif (Deteksi Akumulasi Diam-diam)

Sebelum saham tipe ini meledak ribuan persen, para "orang dalam" atau investor besar biasanya melakukan akumulasi secara senyap. Gerakan ini bisa dideteksi dengan indikator berikut:
• Uptick Volume Setelah Sideways Panjang: Gunakan indikator OBV (On-Balance Volume) dan Chaikin Money Flow (CMF). Jika harga saham stagnan (jalan di tempat) namun OBV atau CMF melonjak naik secara konsisten selama beberapa minggu, itu tanda bandar/investor besar sedang mengumpulkan barang tanpa membuat harga naik terlalu cepat.
• Anomali Volume Spontan (Volume Spike): Buat aturan (rule) di mesin: jika volume harian tiba-tiba meledak > 500% dari rata-rata volume 20 hari terakhir (MA Volume) pada saham yang biasanya tidak likuid, mesin harus memberikan notifikasi alert.

Ringkasan Logika Mesin Analisa (Flowchart Sistem)

Mesin analisa Anda harus bekerja dengan urutan logika (Top-Down Screening) seperti ini:
[Mulai]
   │
   ▼
[Filter 1]: Cari Market Cap < Rp 500 Miliar & Kinerja Keuangan Jelek/Rugi.
   │
   ▼
[Filter 2]: Cari Saham yang Saham Publiknya Sedikit (Illiquid / Sepi).
   │
   ▼
[Filter 3]: Deteksi Alert Kuantitatif (Apakah ada lonjakan OBV atau Audit Laporan Keuangan Mendadak?).
   │
   ▼
[Output]: Tampilkan daftar saham "Cacing" yang berpotensi jadi "Naga".
Catatan Risiko Strategi:
Jika Anda mengadopsi cara ini ke dalam mesin, Anda wajib memasukkan parameter manajemen risiko yang sangat ketat. Saham tipe ini memiliki risiko Likuiditas (susah dijual kembali saat ingin keluar) dan risiko Suspensi (penghentian perdagangan oleh bursa jika kenaikan harga dinilai tidak wajar). Oleh karena itu, mesin harus membatasi porsi alokasi modal (position sizing) yang kecil untuk jenis saham ini.