import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="Yafera Pro v4.1 (TEST)", page_icon="🧪", layout="wide")

# Design CSS pour un look pro
st.markdown("""
<style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

st.title("🧪 Yafera Test Lab - V4.1")

# ---------------------------------------------------------
# CONNEXION GOOGLE SHEETS
# ---------------------------------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_read(sheet):
    try:
        # On force la lecture sans cache pour les tests (ttl=0)
        df = conn.read(worksheet=sheet, ttl="0")
        return df if df is not None else pd.DataFrame()
    except Exception as e:
        st.error(f"Erreur de lecture onglet {sheet}: {e}")
        return pd.DataFrame()

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Paramètres")
    # Liste de projets dynamique (tu peux en ajouter ici)
    projet = st.selectbox("📁 PROJET ACTIF", ["Yafera 1", "Yafera 2", "Test Elevage"])
    page = st.radio("MENU", ["📊 BILAN", "🐂 TROUPEAU", "💸 DÉPENSES", "📝 JOURNAL"])

# ---------------------------------------------------------
# PAGE TROUPEAU
# ---------------------------------------------------------
if page == "🐂 TROUPEAU":
    st.subheader(f"Gestion du Troupeau - {projet}")
    t1, t2 = st.tabs(["➕ ACHAT", "💰 VENTE"])

    with t1:
        with st.form("achat", clear_on_submit=True):
            nom = st.text_input("Nom / ID du Bœuf")
            pa = st.number_input("Prix d'Achat (FCFA)", min_value=0)
            dt = st.date_input("Date d'Achat", datetime.now())
            desc = st.text_area("Notes (Provenance, poids...)")
            if st.form_submit_button("ENREGISTRER L'ACHAT"):
                df = safe_read("Bovins")
                new = pd.DataFrame([{
                    "Projet": projet, "Nom": nom, "Description": desc, 
                    "Prix Achat": pa, "Date Achat": str(dt), "Statut": "Présent",
                    "Prix Vente": 0, "Date Vente": "-", "Profit": 0
                }])
                conn.update(worksheet="Bovins", data=pd.concat([df, new], ignore_index=True))
                st.success(f"Bœuf {nom} ajouté au projet {projet}")

    with t2:
        df = safe_read("Bovins")
        if not df.empty and "Projet" in df.columns:
            # Filtrer par projet et statut
            presents = df[(df["Projet"] == projet) & (df["Statut"] == "Présent")]["Nom"].tolist()
            if presents:
                choix = st.selectbox("Sélectionner le bœuf à vendre", presents)
                pv = st.number_input("Prix de Vente", min_value=0)
                dv = st.date_input("Date de Vente", datetime.now())
                if st.button("VALIDER LA VENTE"):
                    # On met à jour la ligne correspondante dans le dataframe global
                    idx = df[df["Nom"] == choix].index[0]
                    df.at[idx, "Statut"] = "Vendu"
                    df.at[idx, "Prix Vente"] = pv
                    df.at[idx, "Date Vente"] = str(dv)
                    df.at[idx, "Profit"] = pv - df.at[idx, "Prix Achat"]
                    conn.update(worksheet="Bovins", data=df)
                    st.success(f"Vente de {choix} enregistrée !")
            else: st.info("Aucun bœuf 'Présent' dans ce projet.")

# ---------------------------------------------------------
# PAGE DÉPENSES
# ---------------------------------------------------------
elif page == "💸 DÉPENSES":
    st.subheader(f"Dépenses - {projet}")
    with st.form("dep", clear_on_submit=True):
        cat = st.selectbox("Type", ["Aliment", "Santé", "Transport", "Main d’œuvre", "Autre"])
        m = st.number_input("Montant (FCFA)", min_value=0)
        d = st.date_input("Date", datetime.now())
        note = st.text_area("Détails")
        if st.form_submit_button("ENREGISTRER LA DÉPENSE"):
            df = safe_read("Depenses")
            new = pd.DataFrame([{"Projet": projet, "Type": cat, "Montant": m, "Date": str(d), "Note": note}])
            conn.update(worksheet="Depenses", data=pd.concat([df, new], ignore_index=True))
            st.success("Dépense ajoutée")

# ---------------------------------------------------------
# PAGE BILAN (Avec Correction PDF)
# ---------------------------------------------------------
elif page == "📊 BILAN":
    st.subheader(f"Bilan Financier - {projet}")
    df_b = safe_read("Bovins")
    df_d = safe_read("Depenses")

    if not df_b.empty and "Projet" in df_b.columns:
        df_b_proj = df_b[df_b["Projet"] == projet]
        df_d_proj = df_d[df_d["Projet"] == projet] if not df_d.empty else pd.DataFrame()

        # Calculs
        invest = pd.to_numeric(df_b_proj["Prix Achat"], errors="coerce").sum()
        ventes = pd.to_numeric(df_b_proj["Prix Vente"], errors="coerce").sum()
        frais = pd.to_numeric(df_d_proj["Montant"], errors="coerce").sum() if not df_d_proj.empty else 0
        
        benef_net = ventes - (invest + frais)
        roi = (benef_net / invest * 100) if invest > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Investissement", f"{invest:,.0f} F")
        c2.metric("Autres Frais", f"{frais:,.0f} F")
        c3.metric("Bénéfice Net", f"{benef_net:,.0f} F")
        c4.metric("ROI", f"{roi:.1f} %")

        # Fonction PDF corrigée (utilisation de BytesIO pour éviter les erreurs de fichier)
        if st.button("📄 Générer le Rapport PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, f"RAPPORT YAFERA - {projet}", ln=True, align='C')
            pdf.set_font("Arial", "", 12)
            pdf.ln(10)
            pdf.cell(200, 10, f"Date: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
            pdf.cell(200, 10, f"Investissement Total: {invest:,.0f} FCFA", ln=True)
            pdf.cell(200, 10, f"Total des Frais: {frais:,.0f} FCFA", ln=True)
            pdf.cell(200, 10, f"Benefice Net: {benef_net:,.0f} FCFA", ln=True)
            
            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.download_button(label="⬇️ Télécharger le PDF", data=pdf_output, file_name=f"Bilan_{projet}.pdf", mime="application/pdf")
    else:
        st.warning("Aucune donnée trouvée pour ce projet.")

# ---------------------------------------------------------
# PAGE JOURNAL
# ---------------------------------------------------------
elif page == "📝 JOURNAL":
    st.subheader(f
