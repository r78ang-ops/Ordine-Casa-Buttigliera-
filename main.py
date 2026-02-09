import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Ordini Casa Buttigliera", layout="wide", page_icon="🏠")

# --- NAVIGAZIONE LATERALE ---
PAGINA = st.sidebar.selectbox("Vai a:", ["Lista Spesa", "Carta CONAD", "Carta COOP"])

# --- CONNESSIONE GOOGLE SHEETS ---
# Viene definita qui fuori così è accessibile se serve in futuro
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNZIONE CARICAMENTO DATI ---
def carica_dati():
    df = conn.read(ttl=0)
    # Pulizia nomi colonne da spazi extra
    df.columns = [str(c).strip() for c in df.columns]
    if df.empty:
        return pd.DataFrame(columns=['ID', 'Prodotto', 'Data', 'Consegnato'])
    # Formattazione tipi dati
    df['Data'] = pd.to_datetime(df['Data']).dt.date
    df['Consegnato'] = df['Consegnato'].fillna(False).astype(bool)
    return df

# ==========================================
# PAGINA 1: LISTA SPESA
# ==========================================
if PAGINA == "Lista Spesa":
    st.title("🏠 Lista Spesa Casa Buttigliera")
    st.markdown("---")

    df_raw = carica_dati()
    oggi = date.today()

    # --- SIDEBAR: AGGIUNGI & GESTISCI ---
    st.sidebar.header("➕ Nuovo Ordine")
    with st.sidebar.form("form_nuovo", clear_on_submit=True):
        nuovo_nome = st.text_input("Cosa serve?")
        nuova_data = st.date_input("Entro quando?", value=oggi)
        if st.form_submit_button("Aggiungi alla Lista"):
            if nuovo_nome:
                nuova_riga = pd.DataFrame([{
                    'ID': int(df_raw['ID'].max() + 1) if not df_raw.empty else 1,
                    'Prodotto': nuovo_nome,
                    'Data': nuova_data,
                    'Consegnato': False
                }])
                df_updated = pd.concat([df_raw, nuova_riga], ignore_index=True)
                conn.update(data=df_updated)
                st.sidebar.success("✅ Aggiunto!")
                st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Gestione Lista")

    # PULSANTE PER CANCELLARE COMPLETATI
    if st.sidebar.button("🗑️ Svuota Ordini Completati"):
        if not df_raw[df_raw['Consegnato'] == True].empty:
            df_pulito = df_raw[df_raw['Consegnato'] == False]
            conn.update(data=df_pulito)
            st.sidebar.warning("Ordini completati rimossi!")
            st.rerun()
        else:
            st.sidebar.info("Nulla da rimuovere.")

    # --- BARRA DI RICERCA ---
    search_query = st.text_input("🔍 Cerca prodotto...", "").lower()

    # Filtro ricerca
    if search_query:
        df_visual = df_raw[df_raw['Prodotto'].str.lower().str.contains(search_query)]
    else:
        df_visual = df_raw

    # --- FUNZIONE RENDERING RIGA ---
    def render_row(row, idx):
        c1, c2, c3 = st.columns([0.5, 4, 1.5])
        with c1:
            check = st.checkbox("Fatto", value=row['Consegnato'], key=f"row_{idx}", label_visibility="collapsed")
            if check != row['Consegnato']:
                df_raw.at[idx, 'Consegnato'] = check
                conn.update(data=df_raw)
                st.rerun()
        with c2:
            if row['Consegnato']: st.markdown(f"~~{row['Prodotto']}~~")
            else: st.write(f"**{row['Prodotto']}**")
        with c3:
            st.caption(f"📅 {row['Data'].strftime('%d/%m/%Y')}")

    # --- SUDDIVISIONE LISTE ---
    aperti = df_visual[df_visual['Consegnato'] == False]
    chiusi = df_visual[df_visual['Consegnato'] == True]

    scaduti = aperti[aperti['Data'] < oggi].sort_values('Data')
    per_oggi = aperti[aperti['Data'] == oggi].sort_values('Prodotto')
    futuri = aperti[aperti['Data'] > oggi].sort_values('Data')

    # --- VISUALIZZAZIONE SEZIONI ---
    if not scaduti.empty:
        st.error(f"🚨 SCADUTI ({len(scaduti)})")
        for i, r in scaduti.iterrows(): render_row(r, i)

    if not per_oggi.empty:
        st.warning(f"🔔 DA PRENDERE OGGI ({len(per_oggi)})")
        for i, r in per_oggi.iterrows(): render_row(r, i)

    if not futuri.empty:
        st.success(f"🗓️ PROSSIMAMENTE ({len(futuri)})")
        for i, r in futuri.iterrows(): render_row(r, i)

    st.markdown("---")
    with st.expander("✅ Vedi ordini completati"):
        if not chiusi.empty:
            for i, r in chiusi.sort_values('Data', ascending=False).iterrows():
                render_row(r, i)
        else:
            st.write("Nessun ordine completato.")

# ==========================================
# PAGINA 2: CARTA CONAD
# ==========================================
elif PAGINA == "Carta CONAD":
    st.title("🛒 Carta Fedeltà CONAD")
    st.info("Inquadra il codice alla cassa")
    # Carica l'immagine dal tuo repository GitHub (assicurati che il nome file sia corretto)
    st.image("CONAD.jpg", caption="Codice CONAD", use_container_width=True)

# ==========================================
# PAGINA 3: CARTA COOP
# ==========================================
elif PAGINA == "Carta COOP":
    st.title("🛍️ Carta Fedeltà COOP")
    st.info("Inquadra il codice alla cassa")
    # Carica l'immagine dal tuo repository GitHub (assicurati che il nome file sia corretto)
    st.image("COOP.jpg", caption="Codice COOP", use_container_width=True)

