import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Yafera Pro V4.1", layout="wide")

st.title("🐂 Yafera Pro - Système de Gestion")

# --- CONNEXION SÉCURISÉE ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Erreur de connexion : Vérifie tes 'Secrets' dans Streamlit Cloud.")
    st.stop()

def safe_read(sheet_name):
    try:
        return conn.read(worksheet=sheet_name, ttl="0")
    except:
        return pd.DataFrame()

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.image("https://www.gstatic.com/images/branding/product/2x/sheets_2020q4_48dp.png", width=50)
    projet = st.selectbox("Choisir le Projet", ["Yafera_TEST", "Embouche_Principal"])
    page = st.radio("Navigation", ["📊 BILAN RÉEL", "🐂 GESTION TROUPEAU", "💸 DÉPENSES"])

# --- PAGE : GESTION TROUPEAU ---
if page == "🐂 GESTION TROUPEAU":
    st.header(f"Registre du Troupeau - {projet}")
    
    with st.form("form_achat"):
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Identifiant du Bœuf")
            prix_a = st.number_input("Prix d'Achat (FCFA)", min_value=0, step=5000)
        with col2:
            date_a = st.date_input("Date d'Achat", datetime.now())
            type_b = st.selectbox("Catégorie", ["Génisse", "Taurillon", "Bœuf de trait"])
        
        if st.form_submit_button("💾 ENREGISTRER L'ACHAT"):
            df = safe_read("Bovins")
            nouveau_boeuf = pd.DataFrame([{
                "Projet": projet, "Nom": nom, "Type": type_b, 
                "Prix Achat": prix_a, "Date Achat": str(date_a), 
                "Statut": "Présent", "Prix Vente": 0, "Profit": 0
            }])
            updated_df = pd.concat([df, nouveau_boeuf], ignore_index=True)
            conn.update(worksheet="Bovins", data=updated_df)
            st.success(f"✅ {nom} a été ajouté avec succès !")
            st.balloons()

# --- PAGE : DÉPENSES ---
elif page == "💸 DÉPENSES":
    st.header(f"Saisie des Dépenses - {projet}")
    with st.form("form_dep"):
        c1, c2 = st.columns(2)
        with c1:
            motif = st.selectbox("Motif", ["Alimentation", "Santé/Vétérinaire", "Main d'œuvre", "Transport"])
            montant = st.number_input("Montant (FCFA)", min_value=0)
        with c2:
            date_d = st.date_input("Date", datetime.now())
        
        if st.form_submit_button("📝 VALIDER LA DÉPENSE"):
            df_d = safe_read("Depenses")
            nouvelle_dep = pd.DataFrame([{
                "Projet": projet, "Motif": motif, "Montant": montant, "Date": str(date_d)
            }])
            updated_dep = pd.concat([df_d, nouvelle_dep], ignore_index=True)
            conn.update(worksheet="Depenses", data=updated_dep)
            st.success("✅ Dépense enregistrée !")

# --- PAGE : BILAN ---
elif page == "📊 BILAN RÉEL":
    st.header(f"Analyse de Performance - {projet}")
    
    df_b = safe_read("Bovins")
    df_d = safe_read("Depenses")

    if not df_b.empty:
        # Calculs
        total_achat = pd.to_numeric(df_b[df_b["Projet"] == projet]["Prix Achat"]).sum()
        total_frais = pd.to_numeric(df_d[df_d["Projet"] == projet]["Montant"]).sum() if not df_d.empty else 0
        total_investi = total_achat + total_frais
        
        # Affichage Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Investissement Total", f"{total_
