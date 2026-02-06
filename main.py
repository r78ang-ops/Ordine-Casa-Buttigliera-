import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Ordini Casa Buttigliera", layout="wide", page_icon="🏠")

st.title("🏠 Ordine Casa Buttigliera Alta")
st.markdown("---")

# Connessione a Google Sheets (legge dai Secrets)
conn = st.connection("gsheets", type=GSheetsConnection)

def carica_dati():
    # ttl=0 per avere dati aggiornati in tempo reale
    df = conn.read(ttl=0)
    
    # Pulizia nomi colonne
    df.columns = [str(c).strip() for c in df.columns]
    
    if df.empty:
        return pd.DataFrame(columns=['ID', 'Prodotto', 'Data', 'Consegnato'])
    
    # Conversione Data corretta
    df['Data'] = pd.to_datetime(df['Data']).dt.date
    
    # Conversione Consegnato (gestisce celle vuote)
    if 'Consegnato' in df.columns:
        df['Consegnato'] = df['Consegnato'].fillna(False).astype(bool)
    else:
        df['Consegnato'] = False
        
    return df

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
                'Data': nuova_data,
                'Consegnato': False
            }])
            df_updated = pd.concat([df_raw, nuova_riga], ignore_index=True)
            conn.update(data=df_updated)
            st.sidebar.success("✅ Aggiunto!")
            st.rerun()

# --- LOGICA DI RAGGRUPPAMENTO (COME EXCEL) ---
def render_row(row, idx):
    c1, c2, c3 = st.columns([0.5, 4, 1.5])
    with c1:
        # Se l'utente clicca, aggiorna subito il foglio Google
        check = st.checkbox("Fatto", value=row['Consegnato'], key=f"row_{idx}", label_visibility="collapsed")
        if check != row['Consegnato']:
            df_raw.at[idx, 'Consegnato'] = check
            conn.update(data=df_raw)
            st.rerun()
            
    with c2:
        if row['Consegnato']:
            st.markdown(f"~~{row['Prodotto']}~~")
        else:
            st.write(f"**{row['Prodotto']}**")
            
    with c3:
        st.caption(f"📅 {row['Data'].strftime('%d/%m/%Y')}")

# Suddivisione Liste
ordini_aperti = df_raw[df_raw['Consegnato'] == False]
ordini_chiusi = df_raw[df_raw['Consegnato'] == True]

scaduti = ordini_aperti[ordini_aperti['Data'] < oggi].sort_values('Data')
da_fare_oggi = ordini_aperti[ordini_aperti['Data'] == oggi].sort_values('Prodotto')
futuri = ordini_aperti[ordini_aperti['Data'] > oggi].sort_values('Data')

# --- VISUALIZZAZIONE ---

# 1. SCADUTI (ROSSO)
if not scaduti.empty:
    st.error(f"🚨 SCADUTI ({len(scaduti)})")
    for i, r in scaduti.iterrows():
        render_row(r, i)
    st.markdown("---")

# 2. OGGI (ARANCIONE)
if not da_fare_oggi.empty:
    st.warning(f"🔔 DA PRENDERE OGGI ({len(da_fare_oggi)})")
    for i, r in da_fare_oggi.iterrows():
        render_row(r, i)
    st.markdown("---")

# 3. FUTURI (VERDE)
if not futuri.empty:
    st.success(f"🗓️ PROSSIMAMENTE ({len(futuri)})")
    for i, r in futuri.iterrows():
        render_row(r, i)
    st.markdown("---")

# 4. COMPLETATI
with st.expander("✅ Vedi ordini completati"):
    if not ordini_chiusi.empty:
        for i, r in ordini_chiusi.sort_values('Data', ascending=False).iterrows():
            render_row(r, i)
    else:
        st.write("Nessun ordine completato.")

if df_raw.empty:
    st.info("La lista è vuota. Inserisci qualcosa dalla barra laterale!")
