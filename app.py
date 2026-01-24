import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuration du style et de la page
st.set_page_config(page_title="Yafera Pro v2", page_icon="🐂", layout="wide")

# CSS personnalisé pour un look "Premium"
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid #2e7d32; }
    div[data-testid="stSidebar"] { background-color: #1e2630; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #2e7d32; color: white; }
    h1, h2, h3 { color: #1e2630; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# Connexion à Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Navigation
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1998/1998610.png", width=100)
    st.title("YAFERA PRO")
    page = st.radio("MENU PRINCIPAL", ["📊 TABLEAU DE BORD", "🐂 MON TROUPEAU", "💸 DÉPENSES", "📝 JOURNAL"])
    st.info("Système de gestion d'embouche connecté.")

# ---------------------------------------------------------
# 1. TABLEAU DE BORD (BILAN AUTOMATIQUE)
# ---------------------------------------------------------
if page == "📊 TABLEAU DE BORD":
    st.title("📊 Bilan d'Activité")
    
    try:
        df_b = conn.read(worksheet="Bovins")
        df_d = conn.read(worksheet="Depenses")
        
        # Logique du Bilan Automatique
        presents = df_b[df_b['Statut'] == 'Présent']
        vendus = df_b[df_b['Statut'] == 'Vendu']
        
        total_profit_brut = vendus['Profit'].sum()
        total_depenses = df_d['Montant'].sum()
        benefice_net = total_profit_brut - total_depenses
        valeur_stock = presents['Prix Achat'].sum()

        # Affichage des Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Bœufs en Parc", len(presents))
        m2.metric("Valeur Stock (FCFA)", f"{valeur_stock:,.0f}")
        m3.metric("Profit Ventes", f"{total_profit_brut:,.0f}")
        m4.metric("BÉNÉFICE NET", f"{benefice_net:,.0f}", delta=float(benefice_net))

        st.subheader("📈 Aperçu du Stock")
        st.dataframe(df_b, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erreur de lecture : Vérifiez vos onglets Google Sheets. {e}")

# ---------------------------------------------------------
# 2. GESTION DU TROUPEAU
# ---------------------------------------------------------
elif page == "🐂 MON TROUPEAU":
    st.title("🐂 Gestion du Troupeau")
    tab_a, tab_v = st.tabs(["➕ NOUVEL ACHAT", "💰 ENREGISTRER UNE VENTE"])
    
    with tab_a:
        with st.form("form_achat"):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Nom/ID du bœuf")
            prix_a = c2.number_input("Prix d'Achat (FCFA)", min_value=0, step=5000)
            desc = st.text_input("Description (Race, Couleur, État)")
            photo = st.camera_input("Prendre une photo")
            if st.form_submit_button("VALIDER L'ENTRÉE"):
                if nom and prix_a > 0:
                    df_ex = conn.read(worksheet="Bovins")
                    new_line = pd.DataFrame([{
                        "Nom": nom, "Description": desc, "Prix Achat": prix_a,
                        "Date Achat": str(datetime.now().date()), "Statut": "Présent",
                        "Prix Vente": 0, "Date Vente": "", "Profit": 0, "Photo": "OK"
                    }])
                    df_up = pd.concat([df_ex, new_line], ignore_index=True)
                    conn.update(worksheet="Bovins", data=df_up)
                    st.success("Bœuf enregistré !")
                    st.balloons()

    with tab_v:
        df_v = conn.read(worksheet="Bovins")
        choix = st.selectbox("Sélectionner le bœuf vendu", df_v[df_v['Statut'] == 'Présent']['Nom'].unique())
        c3, c4 = st.columns(2)
        p_vente = c3.number_input("Prix de Vente (FCFA)", min_value=0)
        d_vente = c4.date_input("Date de vente")
        if st.button("CONFIRMER LA VENTE"):
            idx = df_v[df_v['Nom'] == choix].index[0]
            df_v.at[idx, 'Statut'] = 'Vendu'
            df_v.at[idx, 'Prix Vente'] = p_vente
            df_v.at[idx, 'Date Vente'] = str(d_vente)
            df_v.at[idx, 'Profit'] = p_vente - df_v.at[idx, 'Prix Achat']
            conn.update(worksheet="Bovins", data=df_v)
            st.success("Vente enregistrée et profit calculé !")

# ---------------------------------------------------------
# 3. DÉPENSES
# ---------------------------------------------------------
elif page == "💸 DÉPENSES":
    st.title("💸 Suivi des Frais")
    with st.form("f_dep"):
        cat = st.selectbox("Catégorie", ["Aliment", "Santé", "Transport", "Main d'oeuvre", "Autre"])
        montant = st.number_input("Montant (FCFA)", min_value=0)
        note = st.text_input("Détails de la dépense")
        if st.form_submit_button("ENREGISTRER LA DÉPENSE"):
            df_d = conn.read(worksheet="Depenses")
            new_d = pd.DataFrame([{"Type": cat, "Montant": montant, "Date": str(datetime.now().date()), "Note": note}])
            conn.update(worksheet="Depenses", data=pd.concat([df_d, new_d], ignore_index=True))
            st.success("Dépense ajoutée !")

# ---------------------------------------------------------
# 4. JOURNAL
# ---------------------------------------------------------
elif page == "📝 JOURNAL":
    st.title("📝 Journal de Bord")
    txt = st.text_area("Observations du jour...")
    if st.button("PUBLIER"):
        df_j = conn.read(worksheet="Journal")
        new_j = pd.DataFrame([{"Date": str(datetime.now().date()), "Commentaire": txt}])
        conn.update(worksheet="Journal", data=pd.concat([df_j, new_j], ignore_index=True))
        st.success("Note enregistrée")
    st.dataframe(conn.read(worksheet="Journal"), use_container_width=True)
