from .connection import get_connection


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
