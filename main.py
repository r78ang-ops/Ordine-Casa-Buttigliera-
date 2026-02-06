import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Ordini Casa Buttigliera Alta", layout="wide", page_icon="🏠")

st.title("🏠 Ordine Casa Buttigliera Alta")
st.markdown("---")

# URL del tuo Google Sheet (Copia l'indirizzo del browser del tuo foglio)
# Assicurati che il foglio sia condiviso come "Chiunque abbia il link può visualizzare"
URL_SHEET = "INSERISCI_QUI_IL_LINK_DEL_TUO_GOOGLE_SHEET"

# Connessione a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read()

def carica_dati():
    # Leggiamo i dati dal foglio Google
    df = conn.read(spreadsheet=URL_SHEET)
    df.columns = [str(c).strip() for c in df.columns]
    
    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data']).dt.date
    
    if 'Consegnato' in df.columns:
        df['Consegnato'] = df['Consegnato'].fillna(False).astype(bool)
    
    return df.sort_values(by=['Data', 'Prodotto'], ascending=[True, True])

df_raw = carica_dati()
oggi = date.today()

# --- SIDEBAR: AGGIUNGI NUOVO ORDINE ---
st.sidebar.header("➕ Nuovo Ordine")
with st.sidebar.form("form_nuovo", clear_on_submit=True):
    nuovo_nome = st.text_input("Cosa serve?")
    nuova_data = st.date_input("Entro quando?", value=oggi)
    
    if st.form_submit_button("Aggiungi alla Lista"):
        if nuovo_nome:
            nuova_riga = pd.DataFrame([{
                'ID': len(df_raw) + 1,
                'Prodotto': nuovo_nome,
                'Data': nuova_data.strftime('%Y-%m-%d'),
                'Consegnato': False
            }])
            # Aggiorniamo il foglio Google
            df_updated = pd.concat([df_raw, nuova_riga], ignore_index=True)
            conn.update(spreadsheet=URL_SHEET, data=df_updated)
            st.sidebar.success("✅ Aggiunto!")
            st.rerun()

# --- LOGICA DI VISUALIZZAZIONE ---
# (Qui rimane la stessa logica principled di prima: Scaduti, Oggi, Futuri)
# ... [Logica dei filtri e render_row simile allo script precedente] ...

def render_row(row, idx):
    c1, c2, c3 = st.columns([0.5, 4, 1.5])
    with c1:
        # Nota: L'aggiornamento diretto del checkbox su Google Sheets 
        # richiede l'aggiornamento dell'intero foglio
        check = st.checkbox("Fatto", value=row['Consegnato'], key=f"row_{idx}", label_visibility="collapsed")
    with c2:
        if row['Consegnato']: st.markdown(f"~~{row['Prodotto']}~~")
        else: st.write(row['Prodotto'])
    with c3:
        st.caption(f"{row['Data']}")

    if check != row['Consegnato']:
        df_raw.at[idx, 'Consegnato'] = check
        conn.update(spreadsheet=URL_SHEET, data=df_raw)
        st.rerun()

# Visualizzazione semplice per test
for i, r in df_raw.iterrows():

    render_row(r, i)
