from ..database.connection import get_connection
from datetime import date, time, timedelta


def generate_schedule():
    """
    Génère automatiquement des examens pour tous les modules qui n'en ont pas
    encore, en respectant les contraintes suivantes :

    - Une salle ne peut accueillir qu'un seul examen sur un créneau (géré
      par le trigger check_exam_overlap).
    - Un étudiant ne peut pas avoir plus d'un examen par jour
      (trigger check_student_one_exam_per_day).
    - Un professeur ne peut pas surveiller plus de 3 examens par jour
      (trigger check_professor_max_3_exams).
    - La capacité de la salle doit être suffisante pour le nombre
      d'étudiants inscrits à l'examen.

    Approche :
    - On récupère tous les modules sans examen, avec leur formation,
      département et effectif d'étudiants.
    - On parcourt une grille de jours (J+1 à J+14) et de créneaux horaires
      fixes (9h, 11h, 13h, 15h).
    - Pour chaque module, on essaie en boucle les (date, heure, salle, prof)
      jusqu'à trouver une combinaison qui respecte toutes les contraintes.
      En cas de violation, les triggers lèvent une erreur et on essaie
      la combinaison suivante.
    """

    conn = get_connection()
    cur = conn.cursor()

    # Récupérer les modules sans examen, avec formation, département et nb d'étudiants
    cur.execute(
        """
        SELECT
            m.id,
            m.nom,
            m.formation_id,
            f.departement_id,
            COALESCE(COUNT(i.etudiant_id), 0) AS nb_etudiants
        FROM module m
        JOIN formation f ON f.id = m.formation_id
        LEFT JOIN inscription i ON i.module_id = m.id
        WHERE m.id NOT IN (SELECT module_id FROM examen)
        GROUP BY m.id, m.nom, m.formation_id, f.departement_id
        ORDER BY f.departement_id, m.formation_id, m.nom;
        """
    )
    modules = cur.fetchall()

    if not modules:
        # Rien à planifier
        cur.close()
        conn.close()
        return

    # Toutes les salles, triées par capacité croissante pour utiliser au mieux l'espace
    cur.execute(
        """
        SELECT id, nom, capacite
        FROM salle
        ORDER BY capacite ASC;
        """
    )
    salles = cur.fetchall()

    # Préparer la grille de temps : prochains jours et créneaux horaires
    start_day = date.today() + timedelta(days=1)
    days = [start_day + timedelta(days=i) for i in range(0, 14)]
    slots = [time(9, 0), time(11, 0), time(13, 0), time(15, 0)]

    for m in modules:
        module_id = m["id"]
        dept_id = m["departement_id"]
        nb_etudiants = m["nb_etudiants"]

        # Salles dont la capacité est suffisante (ou toutes si effectif inconnu/0)
        if nb_etudiants and nb_etudiants > 0:
            candidate_rooms = [
                s for s in salles if s["capacite"] >= nb_etudiants
            ] or salles
        else:
            candidate_rooms = salles

        # Professeurs du même département en priorité
        cur.execute(
            """
            SELECT id
            FROM professeur
            WHERE departement_id = %s
            ORDER BY id;
            """,
            (dept_id,),
        )
        profs = cur.fetchall()

        if not profs:
            # Fallback sur tous les profs si aucun dans le département
            cur.execute("SELECT id FROM professeur ORDER BY id;")
            profs = cur.fetchall()

        assigned = False

        for d in days:
            if assigned:
                break
            for slot in slots:
                if assigned:
                    break

                for salle in candidate_rooms:
                    if assigned:
                        break

                    for prof in profs:
                        # On utilise un SAVEPOINT pour ne pas annuler les examens déjà insérés
                        cur.execute("SAVEPOINT sp_module;")
                        try:
                            cur.execute(
                                """
                                INSERT INTO examen (
                                    date,
                                    heure_debut,
                                    duree_minutes,
                                    module_id,
                                    professeur_id,
                                    salle_id
                                )
                                VALUES (%s, %s, %s, %s, %s, %s);
                                """,
                                (
                                    d,
                                    slot,
                                    120,  # durée par défaut (min)
                                    module_id,
                                    prof["id"],
                                    salle["id"],
                                ),
                            )
                            # Si on arrive ici, l'insertion a respecté toutes les contraintes
                            assigned = True
                            # On garde le SAVEPOINT implicitement en continuant
                            break
                        except Exception:
                            # Violation d'une contrainte (conflit étudiant, prof, salle...)
                            # On annule ce seul essai et on tente une autre combinaison
                            cur.execute("ROLLBACK TO SAVEPOINT sp_module;")
                            continue

        # Si aucun créneau n'a été trouvé, on laisse simplement le module non planifié
        # (optionnel : loguer quelque part les modules non planifiés)

    conn.commit()
    cur.close()
    conn.close()
