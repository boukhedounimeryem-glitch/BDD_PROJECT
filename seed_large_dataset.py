"""
Script de génération d'un gros jeu de données pour la plateforme
Exam Scheduler.

Objectifs (approx.) :
- 7 départements
- > 200 formations
- 1 500+ modules
- plusieurs milliers d'étudiants
- inscriptions cohérentes avec les contraintes (FK, crédits, etc.)

Ce script NE modifie PAS le schéma, uniquement les données.
Il tronque les tables fonctionnelles puis insère de nouvelles données.
"""

import random
import sys
import io
from datetime import datetime

import psycopg2

from backend.database.connection import get_connection


if sys.platform == "win32":
    # Meilleure gestion des accents dans le terminal Windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


N_DEPARTEMENTS = 7
FORMATIONS_PER_DEPT = 30  # 7 * 30 = 210 formations
LEVELS = ["L1", "L2", "L3", "M1", "M2"]
MIN_MODULES_PER_FORMATION = 6
MAX_MODULES_PER_FORMATION = 9

STUDENTS_COUNT = 100  # 100 étudiants
PROFS_PER_DEPT = 7  # 7 * 7 = 49 professeurs + 1 supplémentaire = 50


DEPT_NAMES = [
    "Informatique",
    "Mathématiques",
    "Physique",
    "Chimie",
    "Électronique",
    "Gestion",
    "Mécanique",
]

FIRST_NAMES = [
    "Amine",
    "Sara",
    "Yanis",
    "Salma",
    "Rania",
    "Nabil",
    "Lina",
    "Soufiane",
    "Imane",
    "Youssef",
    "Hicham",
    "Kawtar",
    "Omar",
    "Aya",
    "Hanae",
    "Reda",
    "Noha",
    "Walid",
    "Nada",
]

LAST_NAMES = [
    "Kaci",
    "Benali",
    "Toumi",
    "El Idrissi",
    "Haddad",
    "Omar",
    "Fouad",
    "Karim",
    "Jawad",
    "Said",
    "Alaoui",
    "Berrada",
    "Mansouri",
    "Fassi",
    "Idrissi",
    "Ouazzani",
    "Tazi",
    "Bennani",
    "Chakir",
    "Aziz",
]


def main() -> None:
    print("=" * 60)
    print("GÉNÉRATION D'UN GROS JEU DE DONNÉES")
    print("=" * 60)

    conn = get_connection()
    cur = conn.cursor()

    try:
        print("\n🗑  Nettoyage des anciennes données...")
        # Ordre important à cause des contraintes de FK
        cur.execute(
            """
            TRUNCATE TABLE
                inscription,
                examen,
                etudiant,
                module,
                formation,
                professeur,
                salle,
                departement
            RESTART IDENTITY CASCADE;
            """
        )
        conn.commit()
        print("✅ Données tronquées.")

        # 1. Départements
        print("\n1️⃣  Insertion des départements...")
        dept_rows = [(i + 1, DEPT_NAMES[i % len(DEPT_NAMES)]) for i in range(N_DEPARTEMENTS)]
        cur.executemany(
            "INSERT INTO departement (id, nom) VALUES (%s, %s);",
            dept_rows,
        )
        print(f"   → {len(dept_rows)} départements insérés.")

        # 2. Formations
        print("\n2️⃣  Insertion des formations...")
        formations = []
        formation_id = 1
        for dept_id, dept_name in dept_rows:
            for k in range(FORMATIONS_PER_DEPT):
                level = random.choice(LEVELS)
                name = f"{level} - {dept_name} {k + 1}"
                nb_modules = random.randint(MIN_MODULES_PER_FORMATION, MAX_MODULES_PER_FORMATION)
                formations.append(
                    (formation_id, name, level, nb_modules, dept_id)
                )
                formation_id += 1

        cur.executemany(
            """
            INSERT INTO formation (id, nom, niveau, nb_modules, departement_id)
            VALUES (%s, %s, %s, %s, %s);
            """,
            formations,
        )
        print(f"   → {len(formations)} formations insérées.")

        # 3. Salles (lieux d'examen)
        print("\n3️⃣  Insertion des salles...")
        salles = []
        salle_id = 1
        # Quelques amphithéâtres
        for i in range(1, 6):
            salles.append((salle_id, f"Amphi {i}", 300, "amphi", f"Bloc A{i}"))
            salle_id += 1
        # Salles classiques
        for i in range(1, 31):
            cap = random.choice([20, 25, 30, 40, 60])
            salles.append((salle_id, f"Salle {i:03d}", cap, "salle", f"Bloc B{i%5+1}"))
            salle_id += 1

        cur.executemany(
            """
            INSERT INTO salle (id, nom, capacite, type, batiment)
            VALUES (%s, %s, %s, %s, %s);
            """,
            salles,
        )
        print(f"   → {len(salles)} salles insérées.")

        # 4. Professeurs
        print("\n4️⃣  Insertion des professeurs...")
        profs = []
        prof_id = 1
        for dept_id, dept_name in dept_rows:
            for i in range(PROFS_PER_DEPT):
                first = random.choice(FIRST_NAMES)
                last = random.choice(LAST_NAMES)
                name = f"Dr {last} {first}"
                specialite = f"Spécialité {dept_name}"
                profs.append((prof_id, name, specialite, dept_id))
                prof_id += 1
        
        # Ajouter un professeur supplémentaire pour atteindre 50
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"Dr {last} {first}"
        specialite = "Spécialité Interdépartementaire"
        profs.append((prof_id, name, specialite, 1))  # Assigné au premier département

        cur.executemany(
            """
            INSERT INTO professeur (id, nom, specialite, departement_id)
            VALUES (%s, %s, %s, %s);
            """,
            profs,
        )
        print(f"   → {len(profs)} professeurs insérés.")

        # 5. Modules
        print("\n5️⃣  Insertion des modules...")
        modules = []
        module_id = 1
        for f_id, name, level, nb_modules, dept_id in formations:
            nb = nb_modules
            for k in range(nb):
                m_name = f"Module {k + 1} - {name}"
                credits = random.choice([4, 5, 6])
                pre_req = None
                if k > 0 and random.random() < 0.3:
                    # 30% de chances d'avoir un prérequis dans la même formation
                    pre_req = module_id - 1
                modules.append((module_id, m_name, credits, f_id, pre_req))
                module_id += 1

        cur.executemany(
            """
            INSERT INTO module (id, nom, credits, formation_id, pre_requis_id)
            VALUES (%s, %s, %s, %s, %s);
            """,
            modules,
        )
        print(f"   → {len(modules)} modules insérés.")

        # 6. Étudiants
        print("\n6️⃣  Insertion des étudiants...")
        students = []
        student_id = 1
        formation_ids = [f[0] for f in formations]
        current_year = datetime.now().year

        for _ in range(STUDENTS_COUNT):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            promo = random.choice([current_year, current_year - 1, current_year - 2])
            fid = random.choice(formation_ids)
            students.append((student_id, last, first, promo, fid))
            student_id += 1

        cur.executemany(
            """
            INSERT INTO etudiant (id, nom, prenom, promotion, formation_id)
            VALUES (%s, %s, %s, %s, %s);
            """,
            students,
        )
        print(f"   → {len(students)} étudiants insérés.")

        # 7. Inscriptions
        print("\n7️⃣  Insertion des inscriptions (étudiant-module)...")
        # Indexation des modules par formation
        modules_by_formation = {}
        for m_id, m_name, credits, formation_id, pre_req in modules:
            modules_by_formation.setdefault(formation_id, []).append(m_id)

        inscriptions = []
        for s_id, nom, prenom, promo, fid in students:
            m_list = modules_by_formation.get(fid, [])
            if not m_list:
                continue
            # Chaque étudiant s'inscrit à 6–9 modules dans sa formation
            k = min(len(m_list), random.randint(6, 9))
            chosen = random.sample(m_list, k)
            for mid in chosen:
                inscriptions.append((s_id, mid, None))

        cur.executemany(
            """
            INSERT INTO inscription (etudiant_id, module_id, note)
            VALUES (%s, %s, %s);
            """,
            inscriptions,
        )
        print(f"   → {len(inscriptions)} inscriptions créées.")

        conn.commit()

        print("\n" + "=" * 60)
        print("✅ GROS JEU DE DONNÉES GÉNÉRÉ AVEC SUCCÈS")
        print("=" * 60)
        print(
            f"\nRésumé :\n"
            f"  - Départements : {len(dept_rows)}\n"
            f"  - Formations   : {len(formations)}\n"
            f"  - Modules      : {len(modules)}\n"
            f"  - Professeurs  : {len(profs)}\n"
            f"  - Étudiants    : {len(students)}\n"
            f"  - Inscriptions : {len(inscriptions)}\n"
        )

    except Exception as e:
        print(f"\n❌ Erreur pendant la génération : {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()


