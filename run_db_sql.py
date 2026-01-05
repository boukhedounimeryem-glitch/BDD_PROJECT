"""
Script pour exécuter db.sql sur PostgreSQL 18
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
print("EXÉCUTION DE db.sql SUR POSTGRESQL 18")
print("="*60)

try:
    # Lire le fichier SQL
    sql_file = os.path.join('backend', 'database', 'db.sql')
    print(f"\n📖 Lecture du fichier: {sql_file}")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Se connecter à la base de données
    print("🔌 Connexion à la base de données...")
    conn = get_connection()
    conn.autocommit = False  # Utiliser des transactions
    
    cur = conn.cursor()
    
    # Exécuter le script SQL
    print("⚙️  Exécution du script SQL...")
    print("   (Cela peut prendre quelques secondes...)\n")
    
    # Exécuter le script en plusieurs parties pour gérer les erreurs
    try:
        # Remplacer CREATE FUNCTION par CREATE OR REPLACE FUNCTION si nécessaire
        sql_content = sql_content.replace('CREATE FUNCTION', 'CREATE OR REPLACE FUNCTION')
        cur.execute(sql_content)
        conn.commit()
        print("✅ Script SQL exécuté avec succès!")
        
    except psycopg2.Error as e:
        conn.rollback()
        print(f"❌ Erreur lors de l'exécution: {str(e)}")
        print(f"\n💡 Essayez d'exécuter le fichier manuellement dans pgAdmin:")
        print(f"   1. Ouvrez pgAdmin")
        print(f"   2. Connectez-vous à PostgreSQL 18")
        print(f"   3. Clic droit sur 'exam_scheduler' → Query Tool")
        print(f"   4. Ouvrez le fichier: {sql_file}")
        print(f"   5. Exécutez (F5)")
        raise
    
    # Vérifier les tables créées
    print("\n📊 Vérification des tables créées...")
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    print(f"   Tables trouvées: {len(tables)}")
    for (table_name,) in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cur.fetchone()[0]
        print(f"   - {table_name}: {count} enregistrements")
    
    cur.close()
    conn.close()
    
    print("\n" + "="*60)
    print("✅ BASE DE DONNÉES CRÉÉE ET REMPLIE!")
    print("="*60)
    print("\n🚀 Vous pouvez maintenant utiliser l'application!")
    print("   python main.py")
    
except FileNotFoundError:
    print(f"\n❌ Fichier non trouvé: {sql_file}")
    print("   Vérifiez que le fichier existe.")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Erreur: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

