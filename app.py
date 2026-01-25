import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuration
st.set_page_config(page_title="Yafera Pro v3.3", page_icon="🐂", layout="wide")

# Connexion
conn = st.connection("gsheets", type=GSheetsConnection)

# Fonction de lecture sécurisée
def safe_read(sheet_name):
    try:
        df = conn.read(worksheet=sheet_name, ttl="0")
        return df if df is not None else pd.DataFrame()
    except:
        return pd.DataFrame()

# Navigation
with st.sidebar:
    st.title("YAFERA PRO v3.3")
    page = st.radio("MENU", ["📊 BILAN", "🐂 TROUPEAU", "💸 DÉPENSES", "📝 JOURNAL"])

# ---------------------------------------------------------
# PAGE DÉPENSES (Commentaires agrandis)
# ---------------------------------------------------------
if page == "💸 DÉPENSES":
    st.header("💸 Gestion des Dépenses")
    with st.form("form_dep", clear_on_submit=True):
        cat = st.selectbox("Type", ["Aliment", "Santé/Vétérinaire", "Transport", "Main d'oeuvre", "Autre"])
        m = st.number_input("Montant (FCFA)", min_value=0, step=500)
        dt = st.date_input("Date", datetime.now())
        # CHANGEMENT : text_area pour plus d'espace
        note = st.text_area("Commentaire détaillé") 
        submit = st.form_submit_button("ENREGISTRER LA DÉPENSE")
        
        if submit and m > 0:
            existing_df = safe_read("Depenses")
            new_data = pd.DataFrame([{"Type": cat, "Montant": m, "Date": str(dt), "Note": note}])
            updated_df = pd.concat([existing_df, new_data], ignore_index=True)
            conn.update(worksheet="Depenses", data=updated_df)
            st.success(f"Enregistré : {m} F pour {cat}")
            st.cache_data.clear()

# ---------------------------------------------------------
# PAGE TROUPEAU (Calendrier de vente inclus)
# ---------------------------------------------------------
elif page == "🐂 TROUPEAU":
    st.header("🐂 Gestion du Troupeau")
    t1, t2 = st.tabs(["➕ NOUVEL ACHAT", "💰 ENREGISTRER UNE VENTE"])
    
    with t1:
        with st.form("f_a", clear_on_submit=True):
            nom = st.text_input("Nom ou Numéro du Bœuf")
            pa = st.number_input("Prix d'Achat", min_value=0)
            dt_a = st.date_input("Date d'Achat", datetime.now())
            desc = st.text_area("Description (Race, couleur, etc.)")
            if st.form_submit_button("VALIDER L'ACHAT"):
                df = safe_read("Bovins")
                new = pd.DataFrame([{"Nom": nom, "Description": desc, "Prix Achat": pa, "Date Achat": str(dt_a), "Statut": "Présent", "Profit": 0, "Prix Vente": 0, "Date Vente": "-"}])
                conn.update(worksheet="Bovins", data=pd.concat([df, new], ignore_index=True))
                st.success(f"Bœuf {nom} ajouté au parc")
                st.cache_data.clear()

    with t2:
        df_v = safe_read("Bovins")
        if not df_v.empty and 'Statut' in df_v.columns:
            presents_list = df_v[df_v['Statut'] == 'Présent']['Nom'].tolist()
            if presents_list:
                choix = st.selectbox("Sélectionner le bœuf vendu", presents_list)
                pv = st.number_input("Prix de Vente Réel", min_value=0)
                dt_v = st.date_input("Date de la Vente", datetime.now()) # Calendrier de vente
                if st.button("CONFIRMER LA VENTE"):
                    idx = df_v[df_v['Nom'] == choix].index[0]
                    df_v.at[idx, 'Statut'] = 'Vendu'
                    df_v.at[idx, 'Prix Vente'] = pv
                    df_v.at[idx, 'Date Vente'] = str(dt_v)
                    df_v.at[idx, 'Profit'] = pv - df_v.at[idx, 'Prix Achat']
                    conn.update(worksheet="Bovins", data=df_v)
                    st.success(f"Vente de {choix} enregistrée !")
                    st.cache_data.clear()
            else: st.info("Aucun bœuf n'est actuellement marqué 'Présent'.")

# ---------------------------------------------------------
# PAGE BILAN (Calcul du Profit Net)
# ---------------------------------------------------------
elif page == "📊 BILAN":
    st.header("📊 Bilan Financier")
    df_b = safe_read("Bovins")
    df_d = safe_read("Depenses")
    
    # Sécurité pour les calculs
    for col in ['Statut', 'Profit', 'Prix Achat']:
        if col not in df_b.columns: df_b[col] = 0
    
    presents = df_b[df_b['Statut'] == 'Présent']
    vendus = df_b[df_b['Statut'] == 'Vendu']
    
    prof_ventes = pd.to_numeric(vendus['Profit'], errors='coerce').sum()
    total_deps = pd.to_numeric(df_d['Montant'], errors='coerce').sum() if not df_d.empty else 0
    val_stock = pd.to_numeric(presents['Prix Achat'], errors='coerce').sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Bœufs au parc", len(presents))
    c2.metric("Valeur du Stock", f"{val_stock:,.0f} F")
    # Le profit net déduit toutes les dépenses (aliment, etc.) du profit des ventes
    c3.metric("BÉNÉFICE NET", f"{prof_ventes - total_deps:,.0f} F", delta=f"{prof_ventes:,.0f} Profit Ventes")

    st.subheader("Détail du Troupeau")
    st.dataframe(df_b, use_container_width=True)

# ---------------------------------------------------------
# PAGE JOURNAL (Affichage auto des dépenses)
# ---------------------------------------------------------
elif page == "📝 JOURNAL":
    st.header("📝 Historique Complet")
    
    t_j1, t_j2 = st.tabs(["Dépenses", "Notes Journal"])
    
    with t_j1:
        st.write("### Liste des frais enregistrés")
        st.dataframe(safe_read("Depenses"), use_container_width=True)
        
    with t_j2:
        note_j = st.text_area("Nouvelle observation...")
        if st.button("AJOUTER AU JOURNAL"):
            df_j = safe_read("Journal")
            new_j = pd.DataFrame([{"Date": str(datetime.now().date()), "Commentaire": note_j}])
            conn.update(worksheet="Journal", data=pd.concat([df_j, new_j], ignore_index=True))
            st.success("Note enregistrée")
            st.cache_data.clear()
        st.dataframe(safe_read("Journal"), use_container_width=True)
