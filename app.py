import streamlit as st
import pandas as pd
from PIL import Image
import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Yafera Pro", layout="wide")

# Initialisation des données (pour le test, en mémoire)
if 'bovins' not in st.session_state:
    st.session_state.bovins = []
if 'notes' not in st.session_state:
    st.session_state.notes = []

st.title("🐂 Yafera Pro - Gestion d'Embouche")

# --- NAVIGATION ---
menu = st.sidebar.selectbox("Aller vers", 
    ["📊 Tableau de Bord", "🐄 Inventaire (Bovins)", "💸 Dépenses", "📓 Journal / Bloc-notes"])

# --- 1. TABLEAU DE BORD ---
if menu == "📊 Tableau de Bord":
    st.header("État Global de l'Exploitation")
    # Calculs simplifiés pour l'exemple
    nb_betes = len(st.session_state.bovins)
    st.metric("Nombre de bêtes", nb_betes)
    # Ici on ajoutera les calculs CA et Bénéfice basés sur les prix

# --- 2. GESTION D'INVENTAIRE (Avec Photo) ---
elif menu == "🐄 Inventaire (Bovins)":
    st.header("Gestion du Troupeau")
    
    with st.expander("➕ Ajouter un nouveau bœuf"):
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom ou Numéro du bœuf")
            race = st.selectbox("Race", ["Gobra", "Métis", "Zébu", "Autre"])
        with col2:
            prix_achat = st.number_input("Prix d'achat (FCFA)", min_value=0)
            date_entree = st.date_input("Date d'entrée", datetime.date.today())
        
        # --- PARTIE PHOTO ---
        st.subheader("📸 Photo de l'animal")
        source_photo = st.radio("Source de la photo", ["Galerie (Télécharger)", "Appareil Photo"])
        
        image_file = None
        if source_photo == "Galerie (Télécharger)":
            image_file = st.file_uploader("Choisir une image", type=["jpg", "jpeg", "png"])
        else:
            image_file = st.camera_input("Prendre une photo")

        if st.button("Enregistrer le bœuf"):
            nouvelle_bete = {
                "nom": nom, "race": race, "prix": prix_achat, 
                "date": date_entree, "photo": image_file
            }
            st.session_state.bovins.append(nouvelle_bete)
            st.success(f"Bœuf {nom} enregistré !")

    # Affichage de la liste
    for index, bete in enumerate(st.session_state.bovins):
        with st.container():
            c1, c2 = st.columns([1, 3])
            if bete["photo"]:
                c1.image(bete["photo"], width=150)
            c2.write(f"**Nom:** {bete['nom']} | **Race:** {bete['race']} | **Achat:** {bete['prix']} FCFA")
            st.divider()

# --- 3. DÉPENSES ---
elif menu == "💸 Dépenses":
    st.header("Suivi des Frais (Alimentation, Soins)")
    # Formulaire identique à celui du bœuf pour ajouter des frais

# --- 4. JOURNAL / BLOC-NOTES ---
elif menu == "📓 Journal / Bloc-notes":
    st.header("Journal de l'Exploitation")
    nouvelle_note = st.text_area("Écrire une observation (ex: météo, visite vétérinaire...)")
    if st.button("Ajouter au journal"):
        note_complete = f"{datetime.datetime.now().strftime('%d/%m/%Y %H:%M')} : {nouvelle_note}"
        st.session_state.notes.insert(0, note_complete)
    
    st.subheader("Notes précédentes")
    for n in st.session_state.notes:
        st.info(n)