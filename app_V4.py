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

# Connexion simplifiée utilisant l'ID de vos secrets
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_read(sheet_name):
    try:
        # On lit l'onglet spécifique (Bovins, Depenses ou Journal)
        df = conn.read(worksheet=sheet_name, ttl=0)
        return df if df is not None else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Paramètres")
    # C'est ce nom qui sera écrit dans la colonne "Projet" de votre Google Sheet
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
            nom = st.text_input("Nom / ID du Bœuf (Unique)")
            pa = st.number_input("Prix d'Achat (FCFA)", min_value=0)
            dt = st.date_input("Date d'Achat", datetime.now())
            desc = st.text_area("Notes (Origine, race, poids...)")
            
            if st.form_submit_button("ENREGISTRER L'ACHAT"):
                if nom:
                    df = safe_read("Bovins")
                    new_data = pd.DataFrame([{
                        "Projet": projet, 
                        "Nom": nom, 
                        "Description": desc, 
                        "Prix Achat": pa, 
                        "Date Achat": str(dt), 
                        "Statut": "Présent", 
                        "Prix Vente": 0, 
                        "Date Vente": "-", 
                        "Profit": 0
                    }])
                    updated_df = pd.concat([df, new_data], ignore_index=True)
                    conn.update(worksheet="Bovins", data=updated_df)
                    st.success(f"Bœuf {nom} enregistré dans le projet {projet} !")
                    st.rerun()
                else:
                    st.error("Veuillez donner un nom au bœuf.")

    with t2:
        df = safe_read("Bovins")
        if not df.empty and "Projet" in df.columns:
            # On ne montre que les boeufs "Présents" du projet sélectionné
            presents = df[(df["Projet"] == projet) & (df["Statut"] == "Présent")]["Nom"].tolist()
            if presents:
                choix = st.selectbox("Sélectionner le bœuf à vendre", presents)
                pv = st.number_input("Prix de Vente (FCFA)", min_value=0)
                dv = st.date_input("Date de Vente", datetime.now())
                
                if st.button("VALIDER LA VENTE"):
                    idx = df[(df["Nom"] == choix) & (df["Projet"] == projet)].index[0]
                    df.at[idx, "Statut"] = "Vendu"
                    df.at[idx, "Prix Vente"] = pv
                    df.at[idx, "Date Vente"] = str(dv)
                    df.at[idx, "Profit"] = pv - df.at[idx, "Prix Achat"]
                    conn.update(worksheet="Bovins", data=df)
                    st.success(f"Vente de {choix} enregistrée !")
                    st.rerun()
            else:
                st.info("Aucun bœuf disponible à la vente pour ce projet.")

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
            new_dep = pd.DataFrame([{"Projet": projet, "Type": cat, "Montant": m, "Date": str(d), "Note": note}])
            updated_df = pd.concat([df, new_dep], ignore_index=True)
            conn.update(worksheet="Depenses", data=updated_df)
            st.success("Dépense ajoutée au projet !")
            st.rerun()

# ---------------------------------------------------------
# PAGE BILAN
# ---------------------------------------------------------
elif page == "📊 BILAN":
    st.subheader(f"Bilan Financier - {projet}")
    df_b = safe_read("Bovins")
    df_d = safe_read("Depenses")

    if not df_b.empty and "Projet" in df_b.columns:
        # Filtrer les données pour le projet sélectionné
        df_b_proj = df_b[df_b["Projet"] == projet]
        df_d_proj = df_d[df_d["Projet"] == projet] if not df_d.empty else pd.DataFrame()

        invest = pd.to_numeric(df_b_proj["Prix Achat"], errors="coerce").sum()
        ventes = pd.to_numeric(df_b_proj["Prix Vente"], errors="coerce").sum()
        frais = pd.to_numeric(df_d_proj["Montant"], errors="coerce").sum() if not df_d_proj.empty else 0
        
        benef_net = ventes - (invest + frais)
        roi = (benef_net / (invest + frais) * 100) if (invest + frais) > 0 else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Investi", f"{invest + frais:,.0f} F")
        c2.metric("Bénéfice Net", f"{benef_net:,.0f} F", delta=f"{benef_net}")
        c3.metric("Rentabilité (ROI)", f"{roi:.1f} %")
        
        st.write("---")
        st.write("### Détails du troupeau")
        st.dataframe(df_b_proj)
    else:
        st.warning("Aucune donnée trouvée pour ce projet. Commencez par ajouter un bœuf !")

# ---------------------------------------------------------
# PAGE JOURNAL
# ---------------------------------------------------------
elif page == "📝 JOURNAL":
    st.subheader(f"Journal de bord - {projet}")
    note = st.text_area("Observation du jour...")
    if st.button("ENREGISTRER LA NOTE"):
        if note:
            df = safe_read("Journal")
            new_note = pd.DataFrame([{"Projet": projet, "Date": str(datetime.now().strftime("%d/%m/%Y %H:%M")), "Commentaire": note}])
            conn.update(worksheet="Journal", data=pd.concat([df, new_note], ignore_index=True))
            st.success("Note enregistrée dans le journal !")
            st.rerun()
    
    st.write("---")
    df_j = safe_read("Journal")
    if not df_j.empty and "Projet" in df_j.columns:
        # Afficher les notes du projet, les plus récentes en haut
        st.table(df_j[df_j["Projet"] == projet].iloc[::-1])
