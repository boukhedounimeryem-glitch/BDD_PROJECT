"""
Script pour supprimer les objets existants et réexécuter db.sql
"""
import psycopg2
import sys
import io
import os

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
    
except Exception as e:
    print(f"\n❌ Erreur: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

