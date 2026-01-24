import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Config
st.set_page_config(page_title="Yafera Pro v3.3", page_icon="🐂", layout="wide")

# Connexion
conn = st.connection("gsheets", type=GSheetsConnection)

# Fonction de lecture ultra-robuste
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
# PAGE DÉPENSES (Version ultra-simplifiée pour éviter l'erreur)
# ---------------------------------------------------------
if page == "💸 DÉPENSES":
    st.header("💸 Gestion des Dépenses")
    
    with st.form("form_dep", clear_on_submit=True):
        cat = st.selectbox("Type", ["Aliment", "Santé/Vétérinaire", "Transport", "Main d'oeuvre", "Autre"])
        m = st.number_input("Montant (FCFA)", min_value=0, step=500)
        dt = st.date_input("Date", datetime.now())
        note = st.text_input("Commentaire")
        submit = st.form_submit_button("ENREGISTRER")
        
        if submit and m > 0:
            try:
                # On récupère l'existant
                existing_df = safe_read("Depenses")
                # On crée la nouvelle ligne
                new_data = pd.DataFrame([{"Type": cat, "Montant": m, "Date": str(dt), "Note": note}])
                # On fusionne
                updated_df = pd.concat([existing_df, new_data], ignore_index=True)
                # On écrase proprement la feuille avec les nouvelles données
                conn.update(worksheet="Depenses", data=updated_df)
                st.success(f"C'est noté : {m} F pour {cat}")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Erreur technique : {e}. Vérifie que l'onglet 'Depenses' existe bien dans ton Google Sheets.")

# ---------------------------------------------------------
# PAGE BILAN
# ---------------------------------------------------------
elif page == "📊 BILAN":
    st.header("📊 Tableau de Bord")
    df_b = safe_read("Bovins")
    df_d = safe_read("Depenses")
    
    c1, c2, c3, c4 = st.columns(4)
    
    # Calculs avec gestion des erreurs si colonnes absentes
    presents = df_b[df_b['Statut'] == 'Présent'] if 'Statut' in df_b.columns else pd.DataFrame()
    vendus = df_b[df_b['Statut'] == 'Vendu'] if 'Statut' in df_b.columns else pd.DataFrame()
    
    prof = pd.to_numeric(vendus['Profit'], errors='coerce').sum() if 'Profit' in vendus.columns else 0
    deps = pd.to_numeric(df_d['Montant'], errors='coerce').sum() if 'Montant' in df_d.columns else 0
    val = pd.to_numeric(presents['Prix Achat'], errors='coerce').sum() if 'Prix Achat' in presents.columns else 0
    
    c1.metric("Bœufs au parc", len(presents))
    c2.metric("Valeur Stock (F)", f"{val:,.0f}")
    c3.metric("Profit Ventes (F)", f"{prof:,.0f}")
    c4.metric("BÉNÉFICE NET (F)", f"{prof - deps:,.0f}")
    
    st.dataframe(df_b, use_container_width=True)

# ---------------------------------------------------------
# PAGE TROUPEAU
# ---------------------------------------------------------
elif page == "🐂 TROUPEAU":
    st.header("🐂 Gestion du Troupeau")
    t1, t2 = st.tabs(["➕ ACHAT", "💰 VENTE"])
    
    with t1:
        with st.form("f_a", clear_on_submit=True):
            nom = st.text_input("Nom/ID")
            pa = st.number_input("Prix d'Achat", min_value=0)
            desc = st.text_area("Description")
            dt_a = st.date_input("Date d'Achat", datetime.now())
            if st.form_submit_button("VALIDER ACHAT"):
                df = safe_read("Bovins")
                new = pd.DataFrame([{"Nom": nom, "Description": desc, "Prix Achat": pa, "Date Achat": str(dt_a), "Statut": "Présent", "Profit": 0}])
                conn.update(worksheet="Bovins", data=pd.concat([df, new], ignore_index=True))
                st.success("Bœuf enregistré")
                st.cache_data.clear()

    with t2:
        df_v = safe_read("Bovins")
        if not df_v.empty and 'Statut' in df_v.columns:
            presents_list = df_v[df_v['Statut'] == 'Présent']['Nom'].tolist()
            if presents_list:
                choix = st.selectbox("Vendre quel bœuf ?", presents_list)
                pv = st.number_input("Prix de Vente", min_value=0)
                if st.button("CONFIRMER LA VENTE"):
                    idx = df_v[df_v['Nom'] == choix].index[0]
                    df_v.at[idx, 'Statut'] = 'Vendu'
                    df_v.at[idx, 'Prix Vente'] = pv
                    df_v.at[idx, 'Profit'] = pv - df_v.at[idx, 'Prix Achat']
                    conn.update(worksheet="Bovins", data=df_v)
                    st.success("Vente réussie !")
                    st.cache_data.clear()
            else: st.info("Aucun bœuf présent.")
        else: st.info("Le registre est vide.")

# ---------------------------------------------------------
# PAGE JOURNAL
# ---------------------------------------------------------
elif page == "📝 JOURNAL":
    st.header("📝 Journal")
    note_j = st.text_area("Observations...")
    if st.button("ENREGISTRER AU JOURNAL"):
        df_j = safe_read("Journal")
        new_j = pd.DataFrame([{"Date": str(datetime.now().date()), "Commentaire": note_j}])
        conn.update(worksheet="Journal", data=pd.concat([df_j, new_j], ignore_index=True))
        st.success("Note ajoutée")
        st.cache_data.clear()
    st.dataframe(safe_read("Journal"), use_container_width=True)
