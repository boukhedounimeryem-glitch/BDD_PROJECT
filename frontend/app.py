import streamlit as st
import sys
import os

# Add project root to Python path so that backend imports work
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ======================
# IMPORTS BACKEND
# ======================
from backend.database.queries import (
    get_all_examens,
    get_examens_simple,
    get_modules,
    get_professeurs,
    get_salles,
    get_departements,
    get_formations_by_departement,
    get_examens_filtered,
    kpi_occupation_salles,
    kpi_examens_par_prof
)

from backend.services.examen_service import (
    create_examen,
    delete_examen,
    update_examen
)

from backend.optimization.scheduler import generate_schedule
import pandas as pd


def _safe_rerun() -> None:
    """
    Wrapper pour relancer proprement l'app, compatible avec les
    anciennes et nouvelles versions de Streamlit.
    """
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()


# ======================
# CONFIG STREAMLIT
# ======================
st.set_page_config(page_title="Exam Scheduler", layout="wide")

st.title("📅 Exam Scheduler")
st.caption("Interface de gestion et d’optimisation des examens")
st.divider()

# ======================
# CHARGEMENT GLOBAL DES DONNÉES
# ======================
with st.spinner("Chargement des données..."):
    try:
        modules = get_modules()
        professeurs = get_professeurs()
        salles = get_salles()
        departements = get_departements()
        examens_simple = get_examens_simple()
    except Exception as e:
        st.error(f"❌ Erreur de connexion à la base de données: {str(e)}")
        st.info(
            "💡 Vérifiez que PostgreSQL est démarré et que la base "
            "de données 'exam_scheduler' existe."
        )
        st.stop()

# Gardes simples pour éviter les crashes en cas de données manquantes
if not departements:
    st.warning("Aucun département trouvé. Ajoutez des données dans la base.")
    st.stop()

if not professeurs or not modules or not salles:
    st.warning(
        "Certaines données de référence sont manquantes "
        "(modules, professeurs ou salles). Complétez la base avant de continuer."
    )

# ======================
# 🔍 FILTRES ANALYTIQUES
# ======================
st.subheader("🔍 Filtres analytiques")

with st.container(border=True):
    col_dept, col_form, col_prof = st.columns(3)

    with col_dept:
        dept = st.selectbox(
            "Département",
            departements,
            format_func=lambda x: x["nom"],
            key="filter_dept",
        )

    formations = get_formations_by_departement(dept["id"])

    if not formations:
        st.info(
            "Aucune formation trouvée pour ce département. "
            "Ajoutez des formations dans la base de données."
        )
        st.stop()

    with col_form:
        formation = st.selectbox(
            "Formation",
            formations,
            format_func=lambda x: x["nom"],
            key="filter_form",
        )

    with col_prof:
        prof_filter = st.selectbox(
            "Professeur",
            professeurs,
            format_func=lambda x: x["nom"],
            key="filter_prof",
        )

filtered_examens = get_examens_filtered(
    dept_id=dept["id"],
    formation_id=formation["id"],
    professeur_id=prof_filter["id"],
)

st.dataframe(filtered_examens, use_container_width=True)

# ======================
# 📊 DASHBOARD KPI
# ======================
st.subheader("📊 Dashboard KPI")

col1, col2 = st.columns(2)

with col1:
    st.write("📌 Occupation des salles")
    occ = kpi_occupation_salles()
    st.dataframe(occ, use_container_width=True)

with col2:
    st.write("👨‍🏫 Examens par professeur")
    kpi_prof = kpi_examens_par_prof()
    st.dataframe(kpi_prof, use_container_width=True)

st.divider()

# ======================
# ⚙️ OPTIMISATION AUTO
# ======================
st.subheader("⚙️ Génération automatique")

if st.button("Générer l'emploi du temps automatiquement", key="btn_generate"):
    try:
        with st.spinner("Génération de l'emploi du temps..."):
            generate_schedule()
        st.success("Emploi du temps généré automatiquement")
        _safe_rerun()
    except Exception as e:
        st.error(f"❌ Erreur lors de la génération : {e}")

# ======================
# ➕ AJOUT EXAMEN
# ======================
st.subheader("➕ Ajouter un examen")

col1, col2, col3 = st.columns(3)

with col1:
    date = st.date_input("Date", key="add_date")
    heure = st.time_input("Heure de début", key="add_time")

with col2:
    duree = st.number_input(
        "Durée (minutes)",
        min_value=30,
        step=30,
        key="add_duree"
    )
    module = st.selectbox(
        "Module",
        modules,
        format_func=lambda x: x["nom"],
        key="add_module"
    )

with col3:
    professeur = st.selectbox(
        "Professeur",
        professeurs,
        format_func=lambda x: x["nom"],
        key="add_prof"
    )
    salle = st.selectbox(
        "Salle",
        salles,
        format_func=lambda x: x["nom"],
        key="add_salle"
    )

if st.button("Créer l'examen", key="btn_add"):
    success, message = create_examen(
        date,
        heure,
        duree,
        module["id"],
        professeur["id"],
        salle["id"]
    )

    if success:
        st.success(message)
        _safe_rerun()
    else:
        st.error(message)

# ======================
# 📋 EMPLOI DU TEMPS DES EXAMENS
# ======================
st.subheader("📋 Emploi du temps des examens")

examens = get_all_examens()

if examens:
    df = pd.DataFrame(examens)

    if df.empty:
        st.info("Aucun examen enregistré pour le moment.")
    else:
        # Renommer les colonnes uniquement si elles existent vraiment
        col_map = {
            "departement": "Département",
            "niveau": "Niveau",
            "formation": "Formation",
            "module": "Module",
            "date": "Date",
            "heure_debut": "Heure",
            "duree_minutes": "Durée (min)",
            "professeur": "Professeur",
            "salle": "Salle",
        }
        existing_map = {k: v for k, v in col_map.items() if k in df.columns}
        df = df.rename(columns=existing_map)

        # Si certaines colonnes attendues n'existent pas, on évite les erreurs
        has_dept = "Département" in df.columns
        has_form = "Formation" in df.columns
        has_date = "Date" in df.columns

        # Filtres emploi du temps
        with st.container(border=True):
            filt_col1, filt_col2, filt_col3 = st.columns(3)

            with filt_col1:
                if has_dept:
                    dept_choices = ["Tous"] + sorted(
                        df["Département"].unique().tolist()
                    )
                    dept_filter_tt = st.selectbox(
                        "Département", dept_choices, key="tt_dept"
                    )
                else:
                    dept_filter_tt = "Tous"
                    st.caption("Aucun champ département disponible dans les données.")

            with filt_col2:
                if has_form:
                    formation_choices = ["Tous"] + sorted(
                        df["Formation"].unique().tolist()
                    )
                    form_filter_tt = st.selectbox(
                        "Formation", formation_choices, key="tt_form"
                    )
                else:
                    form_filter_tt = "Tous"
                    st.caption("Aucun champ formation disponible dans les données.")

            with filt_col3:
                if has_date:
                    date_choices = ["Toutes les dates"] + sorted(
                        df["Date"].astype(str).unique().tolist()
                    )
                    date_filter_tt = st.selectbox(
                        "Date", date_choices, key="tt_date"
                    )
                else:
                    date_filter_tt = "Toutes les dates"
                    st.caption("Aucun champ date disponible dans les données.")

        # Application des filtres
        df_filtered = df.copy()
        if has_dept and dept_filter_tt != "Tous":
            df_filtered = df_filtered[df_filtered["Département"] == dept_filter_tt]
        if has_form and form_filter_tt != "Tous":
            df_filtered = df_filtered[df_filtered["Formation"] == form_filter_tt]
        if has_date and date_filter_tt != "Toutes les dates":
            df_filtered = df_filtered[
                df_filtered["Date"].astype(str) == date_filter_tt
            ]

        # Tri par date puis heure si dispo
        sort_cols = [c for c in ["Date", "Heure", "Formation"] if c in df_filtered.columns]
        if sort_cols:
            df_filtered = df_filtered.sort_values(by=sort_cols)

        if df_filtered.empty:
            st.info("Aucun examen ne correspond aux filtres sélectionnés.")
        else:
            display_cols = [
                c
                for c in [
                    "Date",
                    "Heure",
                    "Durée (min)",
                    "Département",
                    "Niveau",
                    "Formation",
                    "Module",
                    "Professeur",
                    "Salle",
                ]
                if c in df_filtered.columns
            ]
            st.dataframe(df_filtered[display_cols], use_container_width=True)
else:
    st.info("Aucun examen enregistré pour le moment.")

# ======================
# 🗑 SUPPRESSION
# ======================
st.subheader("🗑 Supprimer un examen")

if examens_simple:
    exam_to_delete = st.selectbox(
        "Choisir un examen à supprimer",
        examens_simple,
        format_func=lambda x: x["label"],
        key="delete_exam"
    )

    if st.button("Supprimer l'examen", key="btn_delete"):
        success, message = delete_examen(exam_to_delete["id"])

        if success:
            st.success(message)
            _safe_rerun()
        else:
            st.error(message)
else:
    st.info("Aucun examen à supprimer")

# ======================
# ✏️ MODIFICATION
# ======================
st.subheader("✏️ Modifier un examen")

if examens_simple:
    exam_to_edit = st.selectbox(
        "Choisir un examen à modifier",
        examens_simple,
        format_func=lambda x: x["label"],
        key="edit_exam"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        new_date = st.date_input("Nouvelle date", key="edit_date")
        new_time = st.time_input("Nouvelle heure", key="edit_time")

    with col2:
        new_duree = st.number_input(
            "Nouvelle durée (minutes)",
            min_value=30,
            step=30,
            key="edit_duree"
        )
        new_module = st.selectbox(
            "Nouveau module",
            modules,
            format_func=lambda x: x["nom"],
            key="edit_module"
        )

    with col3:
        new_prof = st.selectbox(
            "Nouveau professeur",
            professeurs,
            format_func=lambda x: x["nom"],
            key="edit_prof"
        )
        new_salle = st.selectbox(
            "Nouvelle salle",
            salles,
            format_func=lambda x: x["nom"],
            key="edit_salle"
        )

    if st.button("Modifier l'examen", key="btn_edit"):
        success, message = update_examen(
            exam_to_edit["id"],
            new_date,
            new_time,
            new_duree,
            new_module["id"],
            new_prof["id"],
            new_salle["id"]
        )

        if success:
            st.success(message)
            _safe_rerun()
        else:
            st.error(message)
