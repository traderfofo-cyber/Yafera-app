import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuration
st.set_page_config(page_title="Yafera Pro TEST", layout="wide")

# Connexion Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Lecture sécurisée
def load_data(sheet_name):
    try:
        df = conn.read(worksheet=sheet_name, ttl=0)
        return df
    except:
        return pd.DataFrame(columns=["Projet", "Nom", "Prix Achat", "Statut"])

st.title("🧪 Mode Test - Yafera Pro")

# ===== FORMULAIRE =====
with st.form("test_form"):
    st.subheader("Ajouter un Bœuf")
    nom = st.text_input("Nom du bœuf")
    prix = st.number_input("Prix d'achat (FCFA)", min_value=0)
    submit = st.form_submit_button("TESTER L'ENREGISTREMENT")

    if submit:
        try:
            existing_data = load_data("Bovins")

            new_line = pd.DataFrame([{
                "Projet": "Test",
                "Nom": nom,
                "Prix Achat": prix,
                "Statut": "Présent"
            }])

            updated_df = pd.concat([existing_data, new_line], ignore_index=True)

            # ⚠️ très important : pas d'index
            conn.update(
                worksheet="Bovins",
                data=updated_df,
            )

            st.success("🔥 ÉCRITURE OK — le bœuf est dans Google Sheets !")

        except Exception as e:
            st.error("❌ Erreur d’écriture")
            st.code(str(e))

# ===== AFFICHAGE =====
st.subheader("📄 Données actuelles")
data = load_data("Bovins")
st.dataframe(data, use_container_width=True)

