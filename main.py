import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Ordini Casa Buttigliera Alta", layout="wide", page_icon="🏠")

st.title("🏠 Ordine Casa Buttigliera Alta")
st.markdown("---")

# Connessione a Google Sheets 
# NOTA: Non serve mettere l'URL qui, lo legge in automatico dai Secrets!
conn = st.connection("gsheets", type=GSheetsConnection)

def carica_dati():
    # Leggiamo i dati (usa ttl=0 per avere dati sempre freschi quando ricarichi)
    df = conn.read(ttl=0)
    
    # Pulizia nomi colonne
    df.columns = [str(c).strip() for c in df.columns]
    
    # Se il foglio è vuoto, creiamo una struttura base
    if df.empty:
        return pd.DataFrame(columns=['ID', 'Prodotto', 'Data', 'Consegnato'])
    
    # Conversione Data
    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data']).dt.date
    
    # Conversione Consegnato
    if 'Consegnato' in df.columns:
        df['Consegnato'] = df['Consegnato'].fillna(False).astype(bool)
    else:
        df['Consegnato'] = False
    
    return df.sort_values(by=['Data', 'Prodotto'], ascending=[True, True])

# Caricamento iniziale
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
                'ID': int(df_raw['ID'].max() + 1) if not df_raw.empty else 1,
                'Prodotto': nuovo_nome,
                'Data': nuova_data.strftime('%Y-%m-%d'),
                'Consegnato': False
            }])
            # Uniamo e aggiorniamo Google Sheets
            df_updated = pd.concat([df_raw, nuova_riga], ignore_index=True)
            conn.update(data=df_updated)
            st.sidebar.success("✅ Aggiunto!")
            st.rerun()
        else:
            st.sidebar.warning("Inserisci una descrizione!")

# --- VISUALIZZAZIONE LISTA ---
def render_row(row, idx):
    c1, c2, c3 = st.columns([0.5, 4, 1.5])
    with c1:
        # Checkbox per segnare come fatto
        check = st.checkbox("Fatto", value=row['Consegnato'], key=f"row_{idx}", label_visibility="collapsed")
    with c2:
        if row['Consegnato']: 
            st.markdown(f"~~{row['Prodotto']}~~")
        else: 
            st.write(row['Prodotto'])
    with c3:
        # Colore rosso se scaduto
        data_colore = "red" if row['Data'] < oggi and not row['Consegnato'] else "gray"
        st.markdown(f":{data_colore}[{row['Data'].strftime('%d/%m/%Y')}]")

    # Se lo stato del checkbox cambia, aggiorna il database
    if check != row['Consegnato']:
        df_raw.at[idx, 'Consegnato'] = check
        conn.update(data=df_raw)
        st.rerun()

# Mostra i dati
if not df_raw.empty:
    for i, r in df_raw.iterrows():
        render_row(r, i)
else:
    st.info("La lista è vuota. Aggiungi il primo ordine dalla barra laterale!")
