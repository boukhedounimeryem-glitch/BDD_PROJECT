from .connection import get_connection
import base64
import hashlib
import hmac


def get_all_examens():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            e.id,
            d.nom AS departement,
            f.niveau,
            f.nom AS formation,
            m.nom AS module,
            e.date,
            e.heure_debut,
            e.duree_minutes,
            p.nom AS professeur,
            s.nom AS salle
        FROM examen e
        JOIN module m ON m.id = e.module_id
        JOIN formation f ON f.id = m.formation_id
        JOIN departement d ON d.id = f.departement_id
        JOIN professeur p ON p.id = e.professeur_id
        JOIN salle s ON s.id = e.salle_id
        ORDER BY e.date, e.heure_debut, f.niveau, f.nom;
    """)

    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algo, iterations_str, salt_b64, dk_b64 = password_hash.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iterations_str)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(dk_b64.encode("ascii"))
        computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(computed, expected)
    except Exception:
        return False


def authenticate_user(login: str, password: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, login, password_hash, role, professeur_id, etudiant_id
        FROM public.utilisateur
        WHERE login = %s;
        """,
        (login,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    stored_hash = row["password_hash"] if isinstance(row, dict) else row[2]
    if not verify_password(password, stored_hash):
        return None

    if isinstance(row, dict):
        return {
            "id": row["id"],
            "login": row["login"],
            "role": row["role"],
            "professeur_id": row["professeur_id"],
            "etudiant_id": row["etudiant_id"],
        }

    return {
        "id": row[0],
        "login": row[1],
        "role": row[3],
        "professeur_id": row[4],
        "etudiant_id": row[5],
    }


def get_user_count() -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM public.utilisateur;")
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return 0
    return int(row["c"] if isinstance(row, dict) else row[0])

def get_examens_for_professeur(professeur_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            e.id,
            m.nom AS module,
            f.nom AS formation,
            f.niveau,
            e.date,
            e.heure_debut,
            e.duree_minutes,
            s.nom AS salle
        FROM examen e
        JOIN module m ON m.id = e.module_id
        JOIN formation f ON f.id = m.formation_id
        JOIN salle s ON s.id = e.salle_id
        WHERE e.professeur_id = %s
        ORDER BY e.date, e.heure_debut;
        """,
        (professeur_id,),
    )
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


def get_examens_for_etudiant(etudiant_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            e.id,
            d.nom AS departement,
            f.nom AS formation,
            f.niveau,
            m.nom AS module,
            e.date,
            e.heure_debut,
            e.duree_minutes,
            p.nom AS professeur,
            s.nom AS salle
        FROM inscription i
        JOIN examen e ON e.module_id = i.module_id
        JOIN module m ON m.id = e.module_id
        JOIN formation f ON f.id = m.formation_id
        JOIN departement d ON d.id = f.departement_id
        JOIN professeur p ON p.id = e.professeur_id
        JOIN salle s ON s.id = e.salle_id
        WHERE i.etudiant_id = %s
        ORDER BY e.date, e.heure_debut;
        """,
        (etudiant_id,),
    )
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


def get_modules():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nom FROM module ORDER BY nom;")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


def get_professeurs():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nom FROM professeur ORDER BY nom;")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


def get_salles():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nom FROM salle ORDER BY nom;")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def get_examens_simple():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            e.id,
            m.nom || ' | ' || e.date || ' ' || e.heure_debut AS label
        FROM examen e
        JOIN module m ON m.id = e.module_id
        ORDER BY e.date, e.heure_debut;
    """)

    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def get_departements():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nom FROM departement ORDER BY nom;")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


def get_formations_by_departement(dept_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nom
        FROM formation
        WHERE departement_id = %s
        ORDER BY nom;
    """, (dept_id,))
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


def get_examens_filtered(dept_id=None, formation_id=None, professeur_id=None):
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT
            e.id,
            m.nom AS module,
            e.date,
            e.heure_debut,
            p.nom AS professeur,
            s.nom AS salle
        FROM examen e
        JOIN module m ON m.id = e.module_id
        JOIN formation f ON f.id = m.formation_id
        JOIN professeur p ON p.id = e.professeur_id
        JOIN salle s ON s.id = e.salle_id
        WHERE 1=1
    """

    params = []

    if dept_id:
        query += " AND f.departement_id = %s"
        params.append(dept_id)

    if formation_id:
        query += " AND f.id = %s"
        params.append(formation_id)

    if professeur_id:
        query += " AND p.id = %s"
        params.append(professeur_id)

    query += " ORDER BY e.date, e.heure_debut;"

    cur.execute(query, params)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def kpi_occupation_salles():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            s.nom AS salle,
            COUNT(e.id) AS nb_examens
        FROM salle s
        LEFT JOIN examen e ON e.salle_id = s.id
        GROUP BY s.nom
        ORDER BY nb_examens DESC;
    """)

    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


def kpi_examens_par_prof():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            p.nom AS professeur,
            COUNT(e.id) AS nb_examens
        FROM professeur p
        LEFT JOIN examen e ON e.professeur_id = p.id
        GROUP BY p.nom
        ORDER BY nb_examens DESC;
    """)

    data = cur.fetchall()
    cur.close()
    conn.close()
    return data
