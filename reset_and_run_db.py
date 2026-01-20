"""
Script pour supprimer les objets existants et réexécuter db.sql
"""
import psycopg2
import sys
import io
import os
import base64
import hashlib
import hmac

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Importer la fonction de connexion
sys.path.insert(0, '.')
from backend.database.connection import get_connection

print("="*60)
print("RÉINITIALISATION ET EXÉCUTION DE db.sql")
print("="*60)

try:
    # Se connecter à la base de données
    print("🔌 Connexion à la base de données...")
    conn = get_connection()
    conn.autocommit = False
    
    cur = conn.cursor()
    
    # Supprimer les objets existants (dans l'ordre inverse des dépendances)
    print("\n🗑️  Suppression des objets existants...")
    
    drop_queries = [
        "DROP TRIGGER IF EXISTS trg_student_exam_per_day ON public.examen;",
        "DROP TRIGGER IF EXISTS trg_professor_max_exams ON public.examen;",
        "DROP TRIGGER IF EXISTS trg_exam_overlap ON public.examen;",
        "DROP FUNCTION IF EXISTS public.check_student_one_exam_per_day();",
        "DROP FUNCTION IF EXISTS public.check_professor_max_3_exams();",
        "DROP FUNCTION IF EXISTS public.check_exam_overlap();",
        "DROP TABLE IF EXISTS public.utilisateur CASCADE;",
        "DROP TABLE IF EXISTS public.inscription CASCADE;",
        "DROP TABLE IF EXISTS public.examen CASCADE;",
        "DROP TABLE IF EXISTS public.etudiant CASCADE;",
        "DROP TABLE IF EXISTS public.module CASCADE;",
        "DROP TABLE IF EXISTS public.salle CASCADE;",
        "DROP TABLE IF EXISTS public.professeur CASCADE;",
        "DROP TABLE IF EXISTS public.formation CASCADE;",
        "DROP TABLE IF EXISTS public.departement CASCADE;",
    ]
    
    for query in drop_queries:
        try:
            cur.execute(query)
        except Exception as e:
            print(f"   ⚠️  {str(e)[:60]}...")
    
    conn.commit()
    print("✅ Objets existants supprimés")
    
    # Lire et exécuter le fichier SQL
    sql_file = os.path.join('backend', 'database', 'db.sql')
    print(f"\n📖 Lecture du fichier: {sql_file}")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Remplacer CREATE par CREATE OR REPLACE pour les fonctions
    sql_content = sql_content.replace('CREATE FUNCTION', 'CREATE OR REPLACE FUNCTION')
    
    print("⚙️  Exécution du script SQL...")
    cur.execute(sql_content)
    conn.commit()
    print("✅ Script SQL exécuté avec succès!")

    def _hash_password(password: str, *, iterations: int = 210_000) -> str:
        salt = os.urandom(16)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return "pbkdf2_sha256$%d$%s$%s" % (
            iterations,
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(dk).decode("ascii"),
        )

    def _ensure_user(login: str, password: str, role: str, professeur_id=None, etudiant_id=None) -> None:
        cur.execute(
            """
            INSERT INTO public.utilisateur (login, password_hash, role, professeur_id, etudiant_id)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (login) DO UPDATE
            SET password_hash = EXCLUDED.password_hash,
                role = EXCLUDED.role,
                professeur_id = EXCLUDED.professeur_id,
                etudiant_id = EXCLUDED.etudiant_id;
            """,
            (login, _hash_password(password), role, professeur_id, etudiant_id),
        )

    print("\n👤 Création des comptes (admin/prof/étudiant)...")
    _ensure_user("admin", "admin123", "admin")

    cur.execute("SELECT id FROM public.professeur ORDER BY id;")
    prof_ids = [r['id'] if isinstance(r, dict) else r[0] for r in cur.fetchall()]
    for pid in prof_ids:
        _ensure_user(f"prof{pid}", "prof123", "prof", professeur_id=pid)

    cur.execute("SELECT id FROM public.etudiant ORDER BY id;")
    etu_ids = [r['id'] if isinstance(r, dict) else r[0] for r in cur.fetchall()]
    for eid in etu_ids:
        _ensure_user(f"etu{eid}", "etud123", "etudiant", etudiant_id=eid)
        _ensure_user(f"etud{eid}", "etud123", "etudiant", etudiant_id=eid)

    conn.commit()
    print("✅ Comptes créés.")
    
    # Vérifier les tables créées
    print("\n📊 Vérification des tables créées...")
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    print(f"   Tables trouvées: {len(tables)}")
    for row in tables:
        table_name = row['table_name'] if isinstance(row, dict) else row[0]
        try:
            cur.execute(f'SELECT COUNT(*) FROM public.{table_name};')
            result = cur.fetchone()
            count = result['count'] if isinstance(result, dict) else result[0]
            print(f"   ✅ {table_name}: {count} enregistrements")
        except Exception as e:
            print(f"   ⚠️  {table_name}: erreur - {str(e)[:50]}")
    
    cur.close()
    conn.close()
    
    print("\n" + "="*60)
    print("✅ BASE DE DONNÉES CRÉÉE ET REMPLIE!")
    print("="*60)
    print("\n🚀 Vous pouvez maintenant utiliser l'application!")
    print("   python main.py")
    print("\n🔐 Logins par défaut:")
    print("   - admin / admin123")
    print("   - prof<ID> / prof123    (ex: prof1 / prof123)")
    print("   - etu<ID> / etud123     (ex: etu1 / etud123)")
    print("   - etud<ID> / etud123    (ex: etud1 / etud123)")
    
except Exception as e:
    print(f"\n❌ Erreur: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

