import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Yafera Pro", page_icon="🐂")

st.title("🐂 Yafera Pro - Gestion de Ferme")

# Connexion au Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Menu latéral
menu = ["BOVINS", "DÉPENSES", "JOURNAL"]
choix = st.sidebar.selectbox("Menu", menu)

# --- SECTION BOVINS ---
if choix == "BOVINS":
    st.subheader("Enregistrer un nouveau Bovin")
    with st.form("bovin_form"):
        nom = st.text_input("Nom ou Numéro du Bouvier")
        race = st.selectbox("Race", ["Zébu", "Charolais", "Métis", "Autre"])
        prix_achat = st.number_input("Prix d'achat (F CFA)", min_value=0)
        date_achat = st.date_input("Date d'achat")
        date_vente_prevue = st.date_input("Date de vente prévue")
        submit = st.form_submit_button("ENREGISTRER LE BOVIN")
        
        if submit:
            new_data = pd.DataFrame([{"Nom": nom, "Race": race, "Prix Achat": prix_achat, "Date Achat": str(date_achat), "Date Vente": str(date_vente_prevue)}])
            old_data = conn.read(worksheet="Bovins")
            updated_df = pd.concat([old_data, new_data], ignore_index=True)
            conn.update(worksheet="Bovins", data=updated_df)
            st.success(f"Bovin {nom} enregistré avec succès !")

# --- SECTION DÉPENSES ---
elif choix == "DÉPENSES":
    st.subheader("Nouvelle Dépense")
    with st.form("depense_form"):
        categorie = st.selectbox("Catégorie", ["Aliment", "Santé", "Transport", "Main d'œuvre", "Autre"])
        montant = st.number_input("Montant (F CFA)", min_value=0)
        date_depense = st.date_input("Date")
        # Champ commentaire agrandi
        commentaire = st.text_area("Commentaire / Détails de la dépense")
        submit = st.form_submit_button("ENREGISTRER LA DÉPENSE")
        
        if submit:
            new_depense = pd.DataFrame([{"Date": str(date_depense), "Categorie": categorie, "Montant": montant, "Commentaire": commentaire}])
            # On lit l'onglet "Depenses"
            old_depenses = conn.read(worksheet="Depenses")
            updated_depenses = pd.concat([old_depenses, new_depense], ignore_index=True)
            conn.update(worksheet="Depenses", data=updated_depenses)
            st.success(f"C'est noté : {montant} F pour {categorie}")

# --- SECTION JOURNAL ---
elif choix == "JOURNAL":
    st.subheader("Historique des activités")
    
    tab1, tab2 = st.tabs(["Liste des Bovins", "Historique des Dépenses"])
    
    with tab1:
        st.write("### Vos Animaux")
        df_bovins = conn.read(worksheet="Bovins")
        st.dataframe(df_bovins)

    with tab2:
        st.write("### Vos Dépenses")
        df_depenses = conn.read(worksheet="Depenses")
        # On affiche les dépenses les plus récentes en haut
        if not df_depenses.empty:
            st.dataframe(df_depenses.iloc[::-1])
        else:
            st.info("Aucune dépense enregistrée pour le moment.")

