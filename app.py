import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuration
st.set_page_config(page_title="Yafera Pro v3", page_icon="🐂", layout="wide")

# Design Premium
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid #2e7d32; }
    div[data-testid="stSidebar"] { background-color: #1e2630; color: white; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #2e7d32; color: white; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# Connexion sécurisée
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_read(sheet_name, columns):
    """Fonction pour lire sans planter même si la feuille est vide ou absente"""
    try:
        data = conn.read(worksheet=sheet_name, ttl="0")
        if data.empty:
            return pd.DataFrame(columns=columns)
        return data
    except:
        return pd.DataFrame(columns=columns)

# Navigation
with st.sidebar:
    st.title("YAFERA PRO v3")
    page = st.radio("MENU", ["📊 BILAN", "🐂 TROUPEAU", "💸 DÉPENSES", "📝 JOURNAL"])

# --- STRUCTURE DES COLONNES ---
cols_bovins = ["Nom", "Description", "Prix Achat", "Date Achat", "Statut", "Prix Vente", "Date Vente", "Profit", "Photo"]
cols_depenses = ["Type", "Montant", "Date", "Note"]
cols_journal = ["Date", "Commentaire"]

# ---------------------------------------------------------
# 1. PAGE BILAN (Calculé en direct)
# ---------------------------------------------------------
if page == "📊 BILAN":
    st.header("📊 Tableau de Bord Financier")
    df_b = safe_read("Bovins", cols_bovins)
    df_d = safe_read("Depenses", cols_depenses)
    
    c1, c2, c3, c4 = st.columns(4)
    
    # Calculs sécurisés
    presents = df_b[df_b['Statut'] == 'Présent'] if not df_b.empty else pd.DataFrame()
    vendus = df_b[df_b['Statut'] == 'Vendu'] if not df_b.empty else pd.DataFrame()
    
    prof_brut = vendus['Profit'].sum() if not vendus.empty else 0
    total_dep = df_d['Montant'].sum() if not df_d.empty else 0
    stock_val = presents['Prix Achat'].sum() if not presents.empty else 0
    
    c1.metric("Bœufs au parc", len(presents))
    c2.metric("Valeur Stock (F)", f"{stock_val:,.0f}")
    c3.metric("Profit Ventes (F)", f"{prof_brut:,.0f}")
    c4.metric("BÉNÉFICE NET (F)", f"{prof_brut - total_dep:,.0f}")

    st.subheader("Liste des bœufs")
    st.dataframe(df_b, use_container_width=True)

# ---------------------------------------------------------
# 2. PAGE TROUPEAU
# ---------------------------------------------------------
elif page == "🐂 TROUPEAU":
    st.header("🐂 Gestion des bœufs")
    t1, t2 = st.tabs(["➕ ACHAT", "💰 VENTE"])
    
    with t1:
        with st.form("a"):
            n = st.text_input("Nom/Numéro")
            p = st.number_input("Prix d'Achat", min_value=0)
            d = st.text_input("Description")
            img = st.camera_input("Photo")
            if st.form_submit_button("ENREGISTRER"):
                df_ex = safe_read("Bovins", cols_bovins)
                new = pd.DataFrame([{"Nom": n, "Description": d, "Prix Achat": p, "Date Achat": str(datetime.now().date()), "Statut": "Présent", "Prix Vente": 0, "Profit": 0, "Photo": "Oui"}])
                conn.update(worksheet="Bovins", data=pd.concat([df_ex, new], ignore_index=True))
                st.success("Enregistré !")

    with t2:
        df_v = safe_read("Bovins", cols_bovins)
        if not df_v.empty and len(df_v[df_v['Statut'] == 'Présent']) > 0:
            choix = st.selectbox("Bœuf vendu :", df_v[df_v['Statut'] == 'Présent']['Nom'])
            pv = st.number_input("Prix de Vente", min_value=0)
            if st.button("VALIDER VENTE"):
                idx = df_v[df_v['Nom'] == choix].index[0]
                df_v.at[idx, 'Statut'] = 'Vendu'; df_v.at[idx, 'Prix Vente'] = pv
                df_v.at[idx, 'Profit'] = pv - df_v.at[idx, 'Prix Achat']
                conn.update(worksheet="Bovins", data=df_v)
                st.success("Vendu !")
        else:
            st.info("Aucun bœuf disponible à la vente.")

# ---------------------------------------------------------
# 3. PAGE DÉPENSES
# ---------------------------------------------------------
elif page == "💸 DÉPENSES":
    st.header("💸 Dépenses")
    with st.form("d"):
        cat = st.selectbox("Type", ["Aliment", "Santé", "Main d'oeuvre", "Autre"])
        m = st.number_input("Montant", min_value=0)
        if st.form_submit_button("AJOUTER"):
            df_d = safe_read("Depenses", cols_depenses)
            new_d = pd.DataFrame([{"Type": cat, "Montant": m, "Date": str(datetime.now().date())}])
            conn.update(worksheet="Depenses", data=pd.concat([df_d, new_d], ignore_index=True))
            st.success("Dépense notée !")

# ---------------------------------------------------------
# 4. PAGE JOURNAL
# ---------------------------------------------------------
elif page == "📝 JOURNAL":
    st.header("📝 Journal")
    txt = st.text_area("Note du jour")
    if st.button("SAUVEGARDER"):
        df_j = safe_read("Journal", cols_journal)
        new_j = pd.DataFrame([{"Date": str(datetime.now().date()), "Commentaire": txt}])
        conn.update(worksheet="Journal", data=pd.concat([df_j, new_j], ignore_index=True))
        st.success("Journal mis à jour !")
    st.dataframe(safe_read("Journal", cols_journal), use_container_width=True)

