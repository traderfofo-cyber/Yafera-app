import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io

# ---------------------------------------------------------
# CONFIGURATION ET CONSTANTES
# ---------------------------------------------------------
st.set_page_config(page_title="Yafera Pro v4.1", page_icon="🐂", layout="wide")

# Définition des structures de colonnes
COLS = {
    "Bovins": ["Projet", "Nom", "Description", "Prix Achat", "Date Achat", "Statut", "Prix Vente", "Date Vente", "Profit"],
    "Depenses": ["Projet", "Type", "Montant", "Date", "Note"],
    "Journal": ["Projet", "Date", "Commentaire"]
}

# Connexion
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_read(sheet):
    try:
        df = conn.read(worksheet=sheet, ttl="0")
        if df is None or df.empty:
            return pd.DataFrame(columns=COLS[sheet])
        return df
    except Exception:
        return pd.DataFrame(columns=COLS[sheet])

def clean_for_pdf(text):
    """Nettoie le texte pour éviter les erreurs d'encodage FPDF Latin-1"""
    return str(text).encode('latin-1', 'replace').decode('latin-1')

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Paramètres")
    projet = st.selectbox("📁 PROJET ACTIF", ["Yafera 1", "Yafera 2", "Test Elevage"])
    page = st.radio("MENU", ["📊 BILAN", "🐂 TROUPEAU", "💸 DÉPENSES", "📝 JOURNAL"])
    st.divider()
    st.info(f"Connecté à : {projet}")

# ---------------------------------------------------------
# PAGE TROUPEAU
# ---------------------------------------------------------
if page == "🐂 TROUPEAU":
    st.subheader(f"Gestion du Troupeau - {projet}")
    t1, t2 = st.tabs(["➕ ACHAT / ENTRÉE", "💰 VENTE / SORTIE"])

    with t1:
        with st.form("achat", clear_on_submit=True):
            nom = st.text_input("Nom / ID du Bœuf (Unique)")
            pa = st.number_input("Prix d'Achat (FCFA)", min_value=0, step=5000)
            dt = st.date_input("Date d'Achat", datetime.now())
            desc = st.text_area("Notes (Origine, race, poids...)")
            
            if st.form_submit_button("ENREGISTRER L'ACHAT"):
                df = safe_read("Bovins")
                new_row = {
                    "Projet": projet, "Nom": nom, "Description": desc, 
                    "Prix Achat": pa, "Date Achat": dt.strftime('%Y-%m-%d'), 
                    "Statut": "Présent", "Prix Vente": 0, "Date Vente": "-", "Profit": 0
                }
                updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                conn.update(worksheet="Bovins", data=updated_df)
                st.success(f"✅ {nom} ajouté au troupeau !")
                st.rerun()

    with t2:
        df = safe_read("Bovins")
        if not df.empty:
            presents_df = df[(df["Projet"] == projet) & (df["Statut"] == "Présent")]
            presents_list = presents_df["Nom"].tolist()
            
            if presents_list:
                choix = st.selectbox("Sélectionner l'animal vendu", presents_list)
                pv = st.number_input("Prix de Vente (FCFA)", min_value=0, step=5000)
                dv = st.date_input("Date de Vente", datetime.now())
                
                if st.button("VALIDER LA VENTE"):
                    idx = df[df["Nom"] == choix].index[0]
                    pa_animal = pd.to_numeric(df.at[idx, "Prix Achat"])
                    
                    df.at[idx, "Statut"] = "Vendu"
                    df.at[idx, "Prix Vente"] = pv
                    df.at[idx, "Date Vente"] = dv.strftime('%Y-%m-%d')
                    df.at[idx, "Profit"] = pv - pa_animal
                    
                    conn.update(worksheet="Bovins", data=df)
                    st.success(f"💰 Vente de {choix} enregistrée !")
                    st.rerun()
            else:
                st.info("Aucun animal présent en stock.")

# ---------------------------------------------------------
# PAGE DÉPENSES
# ---------------------------------------------------------
elif page == "💸 DÉPENSES":
    st.subheader(f"Dépenses - {projet}")
    with st.form("dep", clear_on_submit=True):
        cat = st.selectbox("Type", ["Aliment", "Santé", "Transport", "Main d’œuvre", "Autre"])
        m = st.number_input("Montant (FCFA)", min_value=0, step=500)
        d = st.date_input("Date", datetime.now())
        note = st.text_area("Détails")
        
        if st.form_submit_button("ENREGISTRER LA DÉPENSE"):
            df = safe_read("Depenses")
            new_dep = {"Projet": projet, "Type": cat, "Montant": m, "Date": d.strftime('%Y-%m-%d'), "Note": note}
            updated_df = pd.concat([df, pd.DataFrame([new_dep])], ignore_index=True)
            conn.update(worksheet="Depenses", data=updated_df)
            st.success("✅ Dépense enregistrée")

# ---------------------------------------------------------
# PAGE BILAN
# ---------------------------------------------------------
elif page == "📊 BILAN":
    st.subheader(f"Tableau de Bord - {projet}")
    df_b = safe_read("Bovins")
    df_d = safe_read("Depenses")

    # Filtrage par projet
    df_b_proj = df_b[df_b["Projet"] == projet] if not df_b.empty else pd.DataFrame()
    df_d_proj = df_d[df_d["Projet"] == projet] if not df_d.empty else pd.DataFrame()

    if not df_b_proj.empty:
        # Calculs sécurisés
        invest = pd.to_numeric(df_b_proj["Prix Achat"], errors="coerce").sum()
        ventes = pd.to_numeric(df_b_proj["Prix Vente"], errors="coerce").sum()
        frais = pd.to_numeric(df_d_proj["Montant"], errors="coerce").sum() if not df_d_proj.empty else 0
        
        total_sorties = invest + frais
        benef_net = ventes - total_sorties
        roi = (benef_net / total_sorties * 100) if total_sorties > 0 else 0

        # Affichage Métriques
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Invest. (Achats)", f"{invest:,.0f} F")
        c2.metric("Frais Annexes", f"{frais:,.0f} F")
        c3.metric("Bénéfice Net", f"{benef_net:,.0f} F", delta=f"{benef_net:,.0f} F")
        c4.metric("ROI (%)", f"{roi:.1f} %")

        st.write("### Détails du troupeau")
        st.dataframe(df_b_proj, use_container_width=True, hide_index=True)

        st.divider()
        
        # Génération PDF
        if st.button("📄 Préparer le Rapport PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(200, 10, clean_for_pdf(f"RAPPORT DE GESTION - {projet}"), ln=True, align='C')
            pdf.ln(10)
            
            pdf.set_font("Arial", "", 12)
            pdf.cell(100, 10, clean_for_pdf(f"Date du rapport : {datetime.now().strftime('%d/%m/%Y')}"))
            pdf.ln(15)
            
            # Données financières
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(200, 10, "RESUME FINANCIER", ln=True, fill=True)
            pdf.cell(200, 10, clean_for_pdf(f"Total Achats : {invest:,.0f} FCFA"), ln=True)
            pdf.cell(200, 10, clean_for_pdf(f"Total Frais : {frais:,.0f} FCFA"), ln=True)
            pdf.cell(200, 10, clean_for_pdf(f"Total Ventes : {ventes:,.0f} FCFA"), ln=True)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(200, 10, clean_for_pdf(f"BENEFICE NET : {benef_net:,.0f} FCFA"), ln=True)
            
            # Export
            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.download_button(
                label="⬇️ Télécharger le PDF",
                data=pdf_output,
                file_name=f"Bilan_{projet}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
    else:
        st.warning("Aucune donnée disponible pour calculer un bilan.")

# ---------------------------------------------------------
# PAGE JOURNAL
# ---------------------------------------------------------
elif page == "📝 JOURNAL":
    st.subheader(f"Journal de bord - {projet}")
    
    with st.expander("➕ Ajouter une observation"):
        note = st.text_area("Observation (Santé, météo, alimentation...)")
        if st.button("ENREGISTRER LA NOTE"):
            df = safe_read("Journal")
            new_j = {"Projet": projet, "Date": datetime.now().strftime('%d/%m/%Y %H:%M'), "Commentaire": note}
            conn.update(worksheet="Journal", data=pd.concat([df, pd.DataFrame([new_j])], ignore_index=True))
            st.success("Note enregistrée")
            st.rerun()
    
    st.divider()
    df_j = safe_read("Journal")
    if not df_j.empty:
        journal_proj = df_j[df_j["Projet"] == projet].iloc[::-1] # Plus récent en premier
        if not journal_proj.empty:
            for i, row in journal_proj.iterrows():
                st.info(f"📅 **{row['Date']}**\n\n{row['Commentaire']}")
        else:
            st.write("Le journal est vide.")
