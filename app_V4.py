import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Yafera Pro v4.0",
    page_icon="🐂",
    layout="wide"
)

# ---------------------------------------------------------
# DESIGN GLOBAL
# ---------------------------------------------------------
st.markdown("""
<style>
body {background-color:#f4f6f9;}
.big-title {font-size:38px;font-weight:700;color:#2e7d32;}
.card {
    background-color:white;
    padding:20px;
    border-radius:15px;
    box-shadow:0 4px 10px rgba(0,0,0,0.1);
    margin-bottom:20px;
}
</style>
""", unsafe_allow_html=True)

st.image(
    "https://images.unsplash.com/photo-1605472560824-24c52acbf8d2",
    use_container_width=True
)

st.markdown(
    '<div class="big-title">🐂 YAFERA PRO – Gestion d’Embouche</div>',
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# CONNEXION GOOGLE SHEETS
# ---------------------------------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_read(sheet):
    try:
        df = conn.read(worksheet=sheet, ttl="0")
        return df if df is not None else pd.DataFrame()
    except:
        return pd.DataFrame()

# ---------------------------------------------------------
# SIDEBAR : MENU + PROJET
# ---------------------------------------------------------
with st.sidebar:
    st.title("YAFERA PRO v4.0")

    projet = st.selectbox(
        "📁 PROJET ACTIF",
        ["Embouche Yafera 1", "Embouche Yafera 2"]
    )

    page = st.radio("MENU", [
        "📊 BILAN",
        "📈 COMPARATIF",
        "🐂 TROUPEAU",
        "💸 DÉPENSES",
        "📝 JOURNAL"
    ])

# ---------------------------------------------------------
# PAGE TROUPEAU
# ---------------------------------------------------------
if page == "🐂 TROUPEAU":
    st.header("🐂 Gestion du Troupeau")

    t1, t2 = st.tabs(["➕ NOUVEL ACHAT", "💰 ENREGISTRER UNE VENTE"])

    with t1:
        with st.form("achat", clear_on_submit=True):
            nom = st.text_input("Nom / Numéro du Bœuf")
            pa = st.number_input("Prix d’Achat (FCFA)", min_value=0)
            dt = st.date_input("Date d’Achat", datetime.now())
            desc = st.text_area("Description")
            if st.form_submit_button("AJOUTER"):
                df = safe_read("Bovins")
                new = pd.DataFrame([{
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
                conn.update("Bovins", pd.concat([df, new], ignore_index=True))
                st.success("Bœuf ajouté")

    with t2:
        df = safe_read("Bovins")
        df = df[df["Projet"] == projet]

        presents = df[df["Statut"] == "Présent"]["Nom"].tolist()

        if presents:
            choix = st.selectbox("Bœuf vendu", presents)
            pv = st.number_input("Prix de Vente", min_value=0)
            dv = st.date_input("Date de Vente", datetime.now())

            if st.button("CONFIRMER LA VENTE"):
                i = df[df["Nom"] == choix].index[0]
                df.at[i, "Statut"] = "Vendu"
                df.at[i, "Prix Vente"] = pv
                df.at[i, "Date Vente"] = str(dv)
                df.at[i, "Profit"] = pv - df.at[i, "Prix Achat"]
                conn.update("Bovins", df)
                st.success("Vente enregistrée")
        else:
            st.info("Aucun bœuf présent")

# ---------------------------------------------------------
# PAGE DÉPENSES
# ---------------------------------------------------------
elif page == "💸 DÉPENSES":
    st.header("💸 Dépenses du Projet")

    with st.form("dep", clear_on_submit=True):
        cat = st.selectbox("Type", ["Aliment", "Santé", "Transport", "Main d’œuvre", "Autre"])
        m = st.number_input("Montant", min_value=0)
        d = st.date_input("Date", datetime.now())
        note = st.text_area("Commentaire")
        if st.form_submit_button("ENREGISTRER"):
            df = safe_read("Depenses")
            new = pd.DataFrame([{
                "Projet": projet,
                "Type": cat,
                "Montant": m,
                "Date": str(d),
                "Note": note
            }])
            conn.update("Depenses", pd.concat([df, new], ignore_index=True))
            st.success("Dépense ajoutée")

    st.dataframe(
        safe_read("Depenses")[lambda x: x["Projet"] == projet],
        use_container_width=True
    )

# ---------------------------------------------------------
# PAGE BILAN
# ---------------------------------------------------------
elif page == "📊 BILAN":
    st.header(f"📊 Bilan – {projet}")

    df_b = safe_read("Bovins")
    df_d = safe_read("Depenses")

    df_b = df_b[df_b["Projet"] == projet]
    df_d = df_d[df_d["Projet"] == projet]

    presents = df_b[df_b["Statut"] == "Présent"]
    vendus = df_b[df_b["Statut"] == "Vendu"]

    profit = pd.to_numeric(vendus["Profit"], errors="coerce").sum()
    dep = pd.to_numeric(df_d["Montant"], errors="coerce").sum()
    invest = pd.to_numeric(df_b["Prix Achat"], errors="coerce").sum()

    net = profit - dep
    roi = (net / invest * 100) if invest > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bœufs au parc", len(presents))
    c2.metric("Investissement", f"{invest:,.0f} F")
    c3.metric("Bénéfice Net", f"{net:,.0f} F")
    c4.metric("ROI", f"{roi:.2f} %")

    if st.button("📄 Télécharger le bilan PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"Bilan – {projet}", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Bénéfice Net : {net} FCFA", ln=True)
        pdf.cell(0, 10, f"ROI : {roi:.2f} %", ln=True)
        pdf.output("bilan.pdf")
        st.download_button("⬇️ Télécharger", open("bilan.pdf", "rb"), "bilan.pdf")

# ---------------------------------------------------------
# PAGE COMPARATIF
# ---------------------------------------------------------
elif page == "📈 COMPARATIF":
    st.header("📈 Comparatif des Projets")

    df_b = safe_read("Bovins")
    df_d = safe_read("Depenses")

    data = []

    for p in df_b["Projet"].unique():
        b = df_b[df_b["Projet"] == p]
        d = df_d[df_d["Projet"] == p]

        profit = pd.to_numeric(b[b["Statut"] == "Vendu"]["Profit"], errors="coerce").sum()
        dep = pd.to_numeric(d["Montant"], errors="coerce").sum()
        invest = pd.to_numeric(b["Prix Achat"], errors="coerce").sum()
        roi = (profit - dep) / invest * 100 if invest > 0 else 0

        data.append({
            "Projet": p,
            "Bénéfice Net": profit - dep,
            "ROI (%)": round(roi, 2)
        })

    df_c = pd.DataFrame(data)
    st.dataframe(df_c, use_container_width=True)
    st.bar_chart(df_c.set_index("Projet"))

# ---------------------------------------------------------
# PAGE JOURNAL
# ---------------------------------------------------------
elif page == "📝 JOURNAL":
    st.header("📝 Journal du Projet")

    note = st.text_area("Nouvelle note")
    if st.button("AJOUTER"):
        df = safe_read("Journal")
        new = pd.DataFrame([{
            "Projet": projet,
            "Date": str(datetime.now().date()),
            "Commentaire": note
        }])
        conn.update("Journal", pd.concat([df, new], ignore_index=True))
        st.success("Note enregistrée")

    st.dataframe(
        safe_read("Journal")[lambda x: x["Projet"] == projet],
        use_container_width=True
    )

