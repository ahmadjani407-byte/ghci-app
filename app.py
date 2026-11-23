import streamlit as st
import requests
import pandas as pd
import datetime
import pytz
import random

st.set_page_config(page_title="GHCI SCANNER V2 - 24/7", layout="wide")

# ============ 1. KURS USD/IDR TERUPDATE ============
@st.cache_data(ttl=60)
def get_kurs_idr():
    try:
        # Coba dari CoinGecko / ExchangeRate
        r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=10).json()
        return float(r["rates"]["IDR"])
    except:
        try:
            r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=idr", timeout=10).json()
            return float(r["tether"]["idr"])
        except:
            return 16500.0 # Fallback kalau internet error

def rp(x):
    try:
        return f"Rp {x:,.0f}".replace(",", ".")
    except:
        return "Rp -"

# ============ 2. CEK PASAR SAHAM AS ON / OFF ============
def is_us_market_on():
    # Pasar AS: Senin-Jumat, 13:30 - 20:00 WIB (09:30-16:00 New York)
    now_wib = datetime.datetime.now(pytz.timezone("Asia/Jakarta"))
    weekday = now_wib.weekday() # 0=Senin, 5=Sabtu, 6=Minggu
    if weekday >= 5:
        return False, "WEEKEND"
    jam = now_wib.hour + now_wib.minute/60
    if 20.5 <= jam or jam < 13.5: # WIB: Tutup jam 03:30 WIB, Buka 20:30 WIB (DST) - disederhanakan 20:30-03:30
        # Biar gampang: ON jam 20:30 WIB - 03:30 WIB
        if jam >= 20.5 or jam < 3.5:
            return True, "ON"
        return False, "OFF"
    return False, "OFF"

# ============ 3. AMBIL DATA KRIPTO - SEMUA KELAS ============
@st.cache_data(ttl=60)
def get_crypto_data():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd", "order": "market_cap_desc",
            "per_page": 100, "page": 1,
            "sparkline": False, "price_change_percentage": "24h,7d"
        }
        r = requests.get(url, params=params, timeout=20).json()
        df = pd.DataFrame(r)
        return df
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_stock_data():
    # Pakai Yahoo Finance Chart API (gratis, tanpa key)
    tickers = ["IBIT", "NVDA", "AAPL", "TSLA", "MSFT", "AMD", "MSTR", "COIN"]
    rows = []
    for t in tickers:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{t}"
            j = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).json()
            meta = j["chart"]["result"][0]["meta"]
            price = meta.get("regularMarketPrice", 0)
            prev = meta.get("previousClose", price)
            chg = ((price - prev) / prev * 100) if prev else 0
            rows.append({"symbol": t, "price_usd": price, "chg": chg})
        except:
            continue
    return pd.DataFrame(rows)

# ============ 4. UI HEADER ============
st.title("🚀 GHCI SCANNER V2 - 24/7 NO LIMIT")
st.caption("Scan Besar, Menengah, Kecil | BTC = Gas & Rem | Harga Rupiah | Kripto 24/7 + Saham Kalau Pasar ON")

kurs = get_kurs_idr()
market_on, market_status = is_us_market_on()

col1, col2, col3 = st.columns(3)
col1.metric("💵 Kurs USD/IDR (Live)", rp(kurs))
col2.metric("🇺🇸 Pasar Saham AS", "🟢 ON - BUKA" if market_on else "🔴 OFF - TIDUR")
col3.metric("🕐 Jam Scan", datetime.datetime.now(pytz.timezone("Asia/Jakarta")).strftime("%H:%M:%S WIB"))

# TOMBOL SCAN ULANG - TANPA BATAS
if st.button("🔄 SCAN ULANG SEKARANG - CARI 4 KANDIDAT BARU", type="primary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.divider()

# ============ 5. ANALISA BTC - PATOKAN, BUKAN PINTU ============
df = get_crypto_data()
if df.empty:
    st.error("Gagal ambil data CoinGecko, pencet SCAN ULANG lagi bro!")
    st.stop()

btc = df[df["symbol"] == "btc"].iloc[0]
btc_price_idr = float(btc["current_price"]) * kurs
btc_chg24 = float(btc["price_change_percentage_24h"])
btc_chg7 = float(btc["price_change_percentage_7d_in_currency"]) if "price_change_percentage_7d_in_currency" in df.columns else 0

# Tentukan Rezim BTC
if btc_chg24 > 1.5 and btc_chg7 > 0:
    rezim = "BULLISH 🟢"
    modal_max = "70% - 100% - BOLEH NGEGAS!"
    modal_pct = 80
    allow_small = True
    pesan_btc = "Cuaca Cerah! Boleh gas, boleh masuk 1 Cheetah (koin kecil)."
elif btc_chg24 < -1.5:
    rezim = "BEARISH 🔴"
    modal_max = "MAX 20% - 30% - JALAN PELAN!"
    modal_pct = 25
    allow_small = False
    pesan_btc = "Cuaca Badai! Jangan ngegas. Modal kecil aja, cari yang kuat bertahan. Cheetah DILARANG!"
else:
    rezim = "NETRAL / SIDEWAYS 🟡"
    modal_max = "Sekitar 50% - MAIN AMAN"
    modal_pct = 50
    allow_small = False
    pesan_btc = "Cuaca Mendung. Main aman, ambil yang pasti-pasti aja."

st.subheader("👑 BTC = KOMANDAN (Patokan, Bukan Pintu Tutup)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Harga BTC", rp(btc_price_idr))
c2.metric("BTC 24 Jam", f"{btc_chg24:.2f}%")
c3.metric("Rezim Market", rezim)
c4.metric("Rekomendasi Modal", modal_max)
st.info(f"**{pesan_btc}** | Bearish bukan berarti STOP, tapi pelan-pelan. Bullish baru boleh masuk >50%.")

st.divider()

# ============ 6. SCORING & KATEGORI ============
def kategori(mcap):
    if mcap >= 1_000_000_000: return "BESAR 🐘"
    elif mcap >= 100_000_000: return "MENENGAH 🐎"
    elif mcap >= 10_000_000: return "KECIL 🐆"
    else: return "MICRO - BUANG"

df["kategori"] = df["market_cap"].apply(kategori)
df = df[df["kategori"] != "MICRO - BUANG"] # Buang yang terlalu gorengan / sepi
df = df[df["symbol"] != "btc"] # BTC gak ikut lomba, dia juri

# Skor sederhana: Momentum + Volume
# 24h naik + Volume gede = skor tinggi
df["score"] = df["price_change_percentage_24h"].fillna(0) * 2 + df["price_change_percentage_7d_in_currency"].fillna(0) * 1 + (df["total_volume"] / df["market_cap"] * 100).fillna(0)
df = df.sort_values("score", ascending=False)

# Pilih 4 Kandidat: 2 Besar, 1 Menengah, 1 Kecil (kalau boleh) / kalau Bearish: 3 Besar + 1 Menengah
besar = df[df["kategori"] == "BESAR 🐘"].head(3 if not allow_small else 2)
menengah = df[df["kategori"] == "MENENGAH 🐎"].head(1)
kecil = df[df["kategori"] == "KECIL 🐆"].head(1) if allow_small else pd.DataFrame()

kandidat = pd.concat([besar, menengah, kecil]).head(4)

st.subheader("🎯 4 KANDIDAT KRIPTO TERBAIK - HASIL SCAN INI")
st.caption(f"Scan jam {datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%H:%M:%S')} | Kurs Rp {kurs:,.0f} | Modal disarankan: {modal_max}")

for i, (_, row) in enumerate(kandidat.iterrows(), 1):
    harga_idr = float(row["current_price"]) * kurs
    with st.container(border=True):
        a, b, c, d = st.columns([1, 2, 2, 2])
        a.markdown(f"### #{i}")
        b.markdown(f"**{row['name']} ({row['symbol'].upper()})**\n\n{row['kategori']}")
        c.markdown(f"**Harga:** {rp(harga_idr)}\n\n**24h:** {row['price_change_percentage_24h']:.2f}% | **7d:** {row['price_change_percentage_7d_in_currency']:.2f}%")
        d.markdown(f"**Skor:** {row['score']:.1f}\n\n**Volume 24h:** {rp(float(row['total_volume'])*kurs)}")
        st.progress(min(max(modal_pct/100, 0.1), 1.0), text=f"Alokasi saran kalau ambil koin ini: ~{modal_pct//4}% dari total modal (Total modal dipakai: {modal_pct}%)")

st.divider()

# ============ 7. KANDIDAT SAHAM - KALAU PASAR ON ============
st.subheader("🇺🇸 KANDIDAT SAHAM AS")
if not market_on:
    st.warning("🔴 **PASAR SAHAM AS OFF** (Malam / Weekend / Libur). Paket saham tidur dulu. **TAPI KRIPTO DI ATAS TETAP JALAN!** Silakan trading kripto, atau pencet SCAN ULANG lagi nanti pas pasar buka.")
    st.info("Pasar AS buka: Senin-Jumat, jam 20:30 WIB - 03:30 WIB")
else:
    sdf = get_stock_data()
    if sdf.empty:
        st.warning("Data saham gagal diambil, coba SCAN ULANG lagi.")
    else:
        sdf = sdf.sort_values("chg", ascending=False).head(4)
        for i, (_, row) in enumerate(sdf.iterrows(), 1):
            harga_idr = float(row["price_usd"]) * kurs
            with st.container(border=True):
                a, b, c = st.columns([1, 2, 2])
                a.markdown(f"### #{i}")
                b.markdown(f"**{row['symbol']}**")
                c.markdown(f"**Harga:** {rp(harga_idr)} (${row['price_usd']:.2f})\n\n**Naik/Turun:** {row['chg']:.2f}%")

st.divider()
st.caption("⚠️ Bukan saran keuangan. Selalu pakai stop loss. Modal Bearish <50%, Bullish >50%. Scan ulang kapan aja, tanpa batas.")
