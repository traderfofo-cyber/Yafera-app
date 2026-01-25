import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Yafera Pro", page_icon="🐂", layout="wide")

st.title("🐂 Yafera Pro - Gestion de Ferme")

# Connexion au Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Menu latéral
menu = ["BOVINS", "DÉPENSES", "JOURNAL"]
choix = st.sidebar.selectbox("Menu", menu)

# --- SECTION BOVINS ---
if choix == "BOVINS":
    st.subheader("Enregistrer ou Mettre à jour un Bovin")
    with st.form("bovin_form"):
        nom = st.text_input("Nom ou Numéro du Bouvier")
        race = st.selectbox("Race", ["Zébu", "Charolais", "Métis", "Autre"])
        prix_achat = st.number_input("Prix d'achat (F CFA)", min_value=0)
        prix_vente_reel = st.number_input("Prix de vente réel (F CFA) - Laisse à 0 si pas encore vendu", min_value=0)
        date_achat = st.date_input("Date d'achat")
        submit = st.form_submit_button("ENREGISTRER")
        
        if submit:
            new_data = pd.DataFrame([{"Nom": nom, "Race": race, "Prix Achat": prix_achat, "Prix Vente": prix_vente_reel, "Date Achat": str(date_achat)}])
            old_data = conn.read(worksheet="Bovins")
            updated_df = pd.concat([old_data, new_data], ignore_index=True)
            conn.update(worksheet="Bovins", data=updated_df)
            st.success(f"Données pour {nom} enregistrées !")

# --- SECTION DÉPENSES ---
elif choix == "DÉPENSES":
    st.subheader("Nouvelle Dépense (Santé, Aliment, etc.)")
    with st.form("depense_form"):
        categorie = st.selectbox("Catégorie", ["Aliment", "Santé", "Transport", "Main d'œuvre", "Autre"])
        montant = st.number_input("Montant (F CFA)", min_value=0)
        commentaire = st.text_area("Note / Commentaire")
        submit = st.form_submit_button("ENREGISTRER LA DÉPENSE")
        
        if submit:
            new_depense = pd.DataFrame([{"Date": str(pd.Timestamp.now().date()), "Categorie": categorie, "Montant": montant, "Commentaire": commentaire}])
            old_depenses = conn.read(worksheet="Depenses")
            updated_depenses = pd.concat([old_depenses, new_depense], ignore_index=True)
            conn.update(worksheet="Depenses", data=updated_depenses)
            st.success(f"Dépense de {montant} F enregistrée.")

# --- SECTION JOURNAL (LE BILAN DE PROFITS) ---
elif choix == "JOURNAL":
    st.subheader("📈 Bilan des Profits")
    
    df_bovins = conn.read(worksheet="Bovins")
    df_depenses = conn.read(worksheet="Depenses")
    
    # Calculs
    total_achats = df_bovins["Prix Achat"].sum() if not df_bovins.empty else 0
    total_ventes = df_bovins["Prix Vente"].sum() if not df_bovins.empty else 0
    total_frais = df_depenses["Montant"].sum() if not df_depenses.empty else 0
    
    # CALCUL DU PROFIT
    profit_net = total_ventes - (total_achats + total_frais)
    
    # Affichage des Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Ventes (Revenus)", f"{total_ventes:,.0f} F")
    col2.metric("Total Sorties (Achats + Frais)", f"{total_achats + total_frais:,.0f} F")
    
    # Affichage du profit en vert si positif, en rouge si négatif
    col3.metric("PROFIT NET", f"{profit_net:,.0f} F", delta=f"{profit_net:,.0f} F")
    
    st.divider()
    tab1, tab2 = st.tabs(["📋 Inventaire", "💸 Historique Dépenses"])
    with tab1:
        st.dataframe(df_bovins, use_container_width=True)
    with tab2:
        st.dataframe(df_depenses.iloc[::-1], use_container_width=True)

