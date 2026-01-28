import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# ---------------------------------------------------------
# CONFIGURATION DE LA PAGE
# ---------------------------------------------------------
st.set_page_config(page_title="Yafera Pro v4.1", page_icon="🐂", layout="wide")

# Connexion à Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_read(sheet_name):
    """Lit les données d'un onglet spécifique en évitant les erreurs."""
    try:
        df = conn.read(worksheet=sheet_name, ttl=0)
        return df if df is not None else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# ---------------------------------------------------------
# BARRE LATÉRALE (SIDEBAR)
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Paramètres")
    # Le projet choisi ici sera inscrit dans la colonne 'Projet' du tableau
    projet = st.selectbox("📁 PROJET ACTIF", ["Yafera 1", "Yafera 2", "Test Elevage"])
    page = st.radio("MENU", ["📊 BILAN", "🐂 TROUPEAU", "💸 DÉPENSES", "📝 JOURNAL"])
    st.write("---")
    st.info(f"Connecté à : {projet}")

# ---------------------------------------------------------
# PAGE TROUPEAU
# ---------------------------------------------------------
if page == "🐂 TROUPEAU":
    st.subheader(f"Gestion du Troupeau - {projet}")
    tab_achat, tab_vente = st.tabs(["➕ NOUVEL ACHAT", "💰 ENREGISTRER UNE VENTE"])

    with tab_achat:
        with st.form("form_achat", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nom = st.text_input("Nom / ID du Bœuf (Ex: Boeuf-01)")
                pa = st.number_input("Prix d'Achat (FCFA)", min_value=0, step=5000)
            with col2:
                dt = st.date_input("Date d'Achat", datetime.now())
                desc = st.text_area("Notes (Race, poids, etc.)")
            
            if st.form_submit_button("💾 ENREGISTRER L'ACHAT"):
                if nom:
                    df = safe_read("Bovins")
                    new_line = pd.DataFrame([{
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
                    # Mise à jour du fichier Google Sheet
                    updated_df = pd.concat([df, new_line], ignore_index=True)
                    conn.update(worksheet="Bovins", data=updated_df)
                    st.success(f"✅ {nom} ajouté au projet {projet} !")
                    st.rerun()
                else:
                    st.error("❌ Erreur : Le nom du bœuf est obligatoire.")

    with tab_vente:
        df = safe_read("Bovins")
        if not df.empty and "Projet" in df.columns:
            # Filtrer pour ne voir que les bœufs présents du projet actuel
            liste_presents = df[(df["Projet"] == projet) & (df["Statut"] == "Présent")]["Nom"].tolist()
            
            if liste_presents:
                with st.form("form_vente"):
                    choix = st.selectbox("Choisir le bœuf vendu", liste_presents)
                    pv = st.number_input("Prix de Vente (FCFA)", min_value=0, step=5000)
                    dv = st.date_input("Date de Vente", datetime.now())
                    
                    if st.form_submit_button("💰 VALIDER LA VENTE"):
                        # Trouver la ligne correspondante
                        mask = (df["Nom"] == choix) & (df["Projet"] == projet)
                        idx = df[mask].index[0]
                        
                        df.at[idx, "Statut"] = "Vendu"
                        df.at[idx, "Prix Vente"] = pv
                        df.at[idx, "Date Vente"] = str(dv)
                        df.at[idx, "Profit"] = pv - df.at[idx, "Prix Achat"]
                        
                        conn.update(worksheet="Bovins", data=df)
                        st.success(f"📈 Vente de {choix} confirmée !")
                        st.rerun()
            else:
                st.info("ℹ️ Aucun bœuf en stock pour ce projet.")

# ---------------------------------------------------------
# PAGE DÉPENSES
# ---------------------------------------------------------
elif page == "💸 DÉPENSES":
    st.subheader(f"Suivi des Dépenses - {projet}")
    with st.form("form_depense", clear_on_submit=True):
        type_dep = st.selectbox("Type de dépense", ["Alimentation", "Santé/Vétérinaire", "Transport", "Main d'œuvre", "Autre"])
        montant = st.number_input("Montant (FCFA)", min_value=0, step=1000)
        date_dep = st.date_input("Date", datetime.now())
        details = st.text_area("Commentaires")
        
        if st.form_submit_button("📝 ENREGISTRER LA DÉPENSE"):
            df = safe_read("Depenses")
            new_dep = pd.DataFrame([{"Projet": projet, "Type": type_dep, "Montant": montant, "Date": str(date_dep), "Note": details}])
            conn.update(worksheet="Depenses", data=pd.concat([df, new_dep], ignore_index=True))
            st.success("✅ Dépense enregistrée !")
            st.rerun()

# ---------------------------------------------------------
# PAGE BILAN
# ---------------------------------------------------------
elif page == "📊 BILAN":
    st.subheader(f"Bilan Financier : {projet}")
    df_b = safe_read("Bovins")
    df_d = safe_read("Depenses")

    if not df_b.empty and "Projet" in df_b.columns:
        # Calculs pour le projet sélectionné
        data_p = df_b[df_b["Projet"] == projet]
        data_d = df_d[df_d["Projet"] == projet] if not df_d.empty else pd.DataFrame()

        total_achat = pd.to_numeric(data_p["Prix Achat"]).sum()
        total_frais = pd.to_numeric(data_d["Montant"]).sum() if not data_d.empty else 0
        total_ventes = pd.to_numeric(data_p["Prix Vente"]).sum()
        
        benefice = total_ventes - (total_achat + total_frais)

        # Affichage des compteurs
        m1, m2, m3 = st.columns(3)
        m1.metric("Investissement Total", f"{total_achat + total_frais:,.0f} F")
        m2.metric("Ventes réalisées", f"{total_ventes:,.0f} F")
        m3.metric("Bénéfice/Perte", f"{benefice:,.0f} F", delta=f"{benefice}")

        st.write("### Liste des bœufs du projet")
        st.dataframe(data_p, use_container_width=True)
    else:
        st.warning("⚠️ Aucune donnée disponible. Ajoutez des bœufs pour voir le bilan.")

# ---------------------------------------------------------
# PAGE JOURNAL
# ---------------------------------------------------------
elif page == "📝 JOURNAL":
    st.subheader(f"Journal de bord - {projet}")
    note = st.text_area("Observations ou événements importants...")
    if st.button("📓 NOTER AU JOURNAL"):
        if note:
            df = safe_read("Journal")
            new_entry = pd.DataFrame([{"Projet": projet, "Date": datetime.now().strftime("%d/%m/%Y"), "Note": note}])
            conn.update(worksheet="Journal", data=pd.concat([df, new_entry], ignore_index=True))
            st.success("✅ Note ajoutée !")
            st.rerun()
    
    st.divider()
    df_j = safe_read("Journal")
    if not df_j.empty and "Projet" in df_j.columns:
        st.table(df_j[df_j["Projet"] == projet].iloc[::-1])
