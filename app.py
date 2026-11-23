import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="GHCI V2 PRO", page_icon="🦅", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #0A0A0A; color: white; }
h1, h2, h3 { color: #FFD700 !important; }
div[data-testid="metric"] { background-color: #1A1A1A; border: 1px solid #FFD700; border-radius: 10px; padding: 10px; }
div[data-testid="metric"] label { color: #FFD700 !important; }
</style>
""", unsafe_allow_html=True)

st.title("🦅 GHCI V2 PRO - INSTITUTIONAL MONEY TRACKER")
st.markdown("**Jangan Lawan Paus. Ikuti Paus. | GHCI V2 FINAL LOCKED**")
st.markdown("---")

@st.cache_data(ttl=60)
def get_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd", timeout=10).json()
        return r['bitcoin']['usd'], r['ethereum']['usd']
    except:
        return 0, 0

if st.button("🔄 AMBIL HARGA LIVE SEKARANG"):
    st.rerun()

btc_price, eth_price = get_price()
st.info(f"💰 HARGA LIVE OTOMATIS: BTC = ${btc_price:,.0f} | ETH = ${eth_price:,.0f} | Diambil otomatis dari CoinGecko Gratis")

st.sidebar.header("📥 INPUT HARIAN - CUMA 1 ANGKA WAJIB")
st.sidebar.markdown("Data IBIT Flow masih manual karena API otomatisnya berbayar $200/bulan. Cara manual 10 detik ini paling akurat & gratis.")
ibit_flow = st.sidebar.number_input("IBIT Flow Hari Ini (Juta $) - Cek di farside.co.uk/btc", value=0, step=10)
total_etf_btc = st.sidebar.number_input("Total Netflow Semua ETF BTC (Juta $)", value=0, step=10)
etf_saham_flow = st.sidebar.number_input("Netflow SPY+QQQ (Miliar $)", value=0.0, step=0.1)
streak_ib = st.sidebar.selectbox("Streak IBIT 3 Hari?", ["Tidak Ada / Campuran", "Inflow 3 Hari Berturut-turut", "Outflow 3 Hari Berturut-turut"])
dark_pool = st.sidebar.selectbox("Dark Pool", ["Tidak Ada Data / Netral", "Akumulasi Terkonfirmasi", "Distribusi Terkonfirmasi"])
bias_13f = st.sidebar.selectbox("Bias 13F", ["Netral / Data Lama", "Akumulasi Kuat", "Distribusi Kuat"])

skor_13f = 20 if bias_13f == "Akumulasi Kuat" else -20 if bias_13f == "Distribusi Kuat" else 0
skor_etf_saham = 20 if etf_saham_flow > 1 else -20 if etf_saham_flow < -1 else 0
if streak_ib == "Inflow 3 Hari Berturut-turut" and total_etf_btc > 0:
    skor_ibit = 40
elif streak_ib == "Outflow 3 Hari Berturut-turut" and total_etf_btc < 0:
    skor_ibit = -40
elif ibit_flow > 300 and total_etf_btc > 0:
    skor_ibit = 20
elif ibit_flow < -300 and total_etf_btc < 0:
    skor_ibit = -20
else:
    skor_ibit = 0
skor_dark = 20 if dark_pool == "Akumulasi Terkonfirmasi" else -20 if dark_pool == "Distribusi Terkonfirmasi" else 0
total_skor = skor_13f + skor_etf_saham + skor_ibit + skor_dark

st.header("📊 SKOR MAKRO")
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("13F /20", skor_13f); c2.metric("ETF Saham /20", skor_etf_saham); c3.metric("IBIT /40", skor_ibit); c4.metric("Dark Pool /20", skor_dark); c5.metric("TOTAL", f"{total_skor}/100")

if total_skor >= 60: st.success(f"🟢 BULLISH KUAT ({total_skor}) - Paus Akumulasi")
elif total_skor >= 20: st.info(f"🟡 BULLISH LEMAH ({total_skor}) - Cicil 2% Modal")
elif total_skor >= -19: st.warning(f"⚪ WAIT ({total_skor}) - Jangan Paksakan Entry")
else: st.error(f"🔴 BEARISH ({total_skor}) - JANGAN BELI")

st.header("🎯 TOP 4 KANDIDAT")
harga_default = {"BTC / Bitcoin": btc_price, "ETH / Ethereum": eth_price, "NVDA": 185.0, "COIN / Coinbase": 320.0}
data=[]
for i, (nama, tipe) in enumerate([("BTC / Bitcoin","Crypto"),("ETH / Ethereum","Crypto"),("NVDA","Saham AS"),("COIN / Coinbase","Saham AS")]):
    with st.expander(f"#{i+1} {nama} - Harga Sudah Otomatis"):
        entry = st.number_input(f"Entry {nama} ($)", value=float(harga_default[nama]), key=f"e{i}")
        lolos = st.selectbox(f"Lolos Filter? {nama}", ["YA - Lolos Semua", "TIDAK"], key=f"f{i}")
        skor = st.slider(f"Skor {nama}", -100, 100, total_skor, key=f"s{i}")
        if entry>0 and lolos=="YA - Lolos Semua":
            sl, tp1, tp2 = round(entry*0.95,2), round(entry*1.10,2), round(entry*1.25,2)
            modal = "5% Modal" if skor>=60 else "2% Modal" if skor>=20 else "WAIT"
            status = "BELI KUAT" if skor>=60 else "BELI CICIL" if skor>=20 else "WAIT" if skor>=-19 else "HINDARI"
        else:
            sl=tp1=tp2=0; modal="0%"; status="WAIT - Filter Gagal"
        data.append([f"#{i+1}", nama, tipe, skor, entry, sl, tp1, tp2, modal, status])

df=pd.DataFrame(data, columns=["Rank","Aset","Tipe","Skor","Entry","SL (-5%)","TP1 (+10%)","TP2 (+25%)","% Modal","Status"])
st.dataframe(df, use_container_width=True)
st.info("⚠️ Bukan nasihat keuangan. Ini pembacaan aliran uang institusi. Selalu pakai SL. Jangan All-In. | GHCI V2 PRO - FINAL LOCKED")
