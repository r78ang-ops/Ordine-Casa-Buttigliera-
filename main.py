import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import os

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Ordini Casa Buttigliera", layout="wide", page_icon="🏠")

# Ottieni la cartella del file per le immagini (conad.jpg e coop.jpg)
current_dir = os.path.dirname(os.path.abspath(__file__))

# --- NAVIGAZIONE LATERALE ---
PAGINA = st.sidebar.selectbox("Vai a:", [
    "Lista Spesa", 
    "Carta CONAD", 
    "Carta COOP", 
    "Volantini & Offerte 💰",
    "Trova Supermercati 📍"
])

# --- CONNESSIONE GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carica_dati():
    df = conn.read(ttl=0)
    df.columns = [str(c).strip() for c in df.columns]
    if df.empty:
        return pd.DataFrame(columns=['ID', 'Prodotto', 'Data', 'Consegnato'])
    df['Data'] = pd.to_datetime(df['Data']).dt.date
    df['Consegnato'] = df['Consegnato'].fillna(False).astype(bool)
    return df

# ==========================================
# PAGINA: LISTA SPESA
# ==========================================
if PAGINA == "Lista Spesa":
    st.title("🏠 Lista Spesa Buttigliera")
    df_raw = carica_dati()
    oggi = date.today()

    st.sidebar.header("➕ Nuovo Ordine")
    with st.sidebar.form("form_nuovo", clear_on_submit=True):
        nuovo_nome = st.text_input("Cosa serve?")
        nuova_data = st.date_input("Entro quando?", value=oggi)
        if st.form_submit_button("Aggiungi"):
            if nuovo_nome:
                nuova_riga = pd.DataFrame([{'ID': int(df_raw['ID'].max()+1) if not df_raw.empty else 1, 'Prodotto': nuovo_nome, 'Data': nuova_data, 'Consegnato': False}])
                conn.update(data=pd.concat([df_raw, nuova_riga], ignore_index=True))
                st.rerun()

    search = st.text_input("🔍 Cerca prodotto...", "").lower()
    df_visual = df_raw[df_raw['Prodotto'].str.lower().str.contains(search)] if search else df_raw

    def render_row(row, idx):
        c1, c2, c3 = st.columns([0.5, 4, 1.5])
        with c1:
            check = st.checkbox("Fatto", value=row['Consegnato'], key=f"r_{idx}", label_visibility="collapsed")
            if check != row['Consegnato']:
                df_raw.at[idx, 'Consegnato'] = check
                conn.update(data=df_raw)
                st.rerun()
        with c2: st.markdown(f"~~{row['Prodotto']}~~" if row['Consegnato'] else f"**{row['Prodotto']}**")
        with c3: st.caption(f"📅 {row['Data'].strftime('%d/%m')}")

    aperti = df_visual[df_visual['Consegnato'] == False]
    for label, d in [("🚨 SCADUTI", aperti[aperti['Data'] < oggi]), ("🔔 OGGI", aperti[aperti['Data'] == oggi]), ("🗓️ PROSSIMAMENTE", aperti[aperti['Data'] > oggi])]:
        if not d.empty:
            st.subheader(label)
            for i, r in d.iterrows(): render_row(r, i)
    
    with st.expander("✅ Completati"):
        for i, r in df_visual[df_visual['Consegnato'] == True].iterrows(): render_row(r, i)

# ==========================================
# PAGINA: CARTA CONAD
# ==========================================
elif PAGINA == "Carta CONAD":
    st.title("🛒 Carta Fedeltà CONAD")
    img = os.path.join(current_dir, "conad.jpg")
    if os.path.exists(img): 
        st.image(img, use_container_width=True)
    else: 
        st.error("Immagine conad.jpg non trovata su GitHub.")

# ==========================================
# PAGINA: CARTA COOP
# ==========================================
elif PAGINA == "Carta COOP":
    st.title("🛍️ Carta Fedeltà COOP")
    img = os.path.join(current_dir, "coop.jpg")
    if os.path.exists(img): 
        st.image(img, use_container_width=True)
    else: 
        st.error("Immagine coop.jpg non trovata su GitHub.")

# ==========================================
# PAGINA: VOLANTINI & OFFERTE (PromoQui)
# ==========================================
elif PAGINA == "Volantini & Offerte 💰":
    st.title("💰 Volantini Online - Avigliana")
    st.info("Tocca i pulsanti per aprire i volantini aggiornati su PromoQui.")
    
    st.markdown("---")
    
    # SEZIONE CONAD
    st.subheader("📕 Volantini CONAD")
    st.write("Sfoglia le offerte per il punto vendita di Via Falcone.")
    st.link_button("👉 APRI VOLANTINO CONAD", "https://www.promoqui.it/avigliana/conad/volantino", use_container_width=True)
    
    st.markdown("---") # Separatore visivo
    
    # SEZIONE COOP
    st.subheader("📗 Volantini COOP")
    st.write("Sfoglia le offerte per il centro Le Torri.")
    st.link_button("👉 APRI VOLANTINO COOP", "https://www.promoqui.it/avigliana/coop/volantino", use_container_width=True)

    st.markdown("---")
    
    # TUTTE LE ALTRE OFFERTE
    st.subheader("🔍 Altre Offerte")
    st.link_button("🌐 TUTTI I VOLANTINI DI AVIGLIANA", "https://www.promoqui.it/avigliana/offerte", use_container_width=True)

# ==========================================
# PAGINA: TROVA SUPERMERCATI
# ==========================================
elif PAGINA == "Trova Supermercati 📍":
    st.title("📍 Supermercati Vicini")
    st.write("Visualizza i supermercati intorno a te su Google Maps.")
    st.link_button("🗺️ APRI GOOGLE MAPS", "https://www.google.com/maps/search/supermercati+vicino+a+me/", use_container_width=True)
