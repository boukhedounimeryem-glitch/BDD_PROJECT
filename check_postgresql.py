"""
Script de diagnostic pour vérifier la connexion PostgreSQL
"""
import sys
import os
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    import psycopg2
    print("✅ Module psycopg2 installé")
except ImportError:
    print("❌ Module psycopg2 non installé. Installez-le avec: pip install psycopg2-binary")
    sys.exit(1)

# Paramètres de connexion
config = {
    "host": "localhost",
    "port": 5432,
    "database": "exam_scheduler",
    "user": "postgres",
    "password": "1234"
}

print("\n" + "="*50)
print("DIAGNOSTIC DE CONNEXION POSTGRESQL")
print("="*50)
print(f"\n📋 Paramètres de connexion:")
print(f"   Host: {config['host']}")
print(f"   Port: {config['port']}")
print(f"   Database: {config['database']}")
print(f"   User: {config['user']}")
print(f"   Password: {'*' * len(config['password'])}")

# Test 1: Connexion au serveur PostgreSQL (sans base spécifique)
print("\n🔍 Test 1: Connexion au serveur PostgreSQL...")
try:
    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        database="postgres",  # Base par défaut
        user=config["user"],
        password=config["password"]
    )
    print("✅ Connexion au serveur PostgreSQL réussie")
    conn.close()
except psycopg2.OperationalError as e:
    print(f"❌ Impossible de se connecter au serveur PostgreSQL")
    print(f"   Erreur: {str(e)}")
    print("\n💡 Solutions possibles:")
    print("   1. Vérifiez que PostgreSQL est démarré")
    print("   2. Vérifiez que le port 5432 est correct")
    print("   3. Vérifiez les identifiants (user/password)")
    sys.exit(1)

# Test 2: Vérifier si la base de données existe
print("\n🔍 Test 2: Vérification de l'existence de la base de données...")
try:
    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        database="postgres",
        user=config["user"],
        password=config["password"]
    )
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (config["database"],))
    exists = cur.fetchone()
    
    if exists:
        print(f"✅ La base de données '{config['database']}' existe")
    else:
        print(f"❌ La base de données '{config['database']}' n'existe pas")
        print("\n💡 Pour créer la base de données, exécutez:")
        print(f"   CREATE DATABASE {config['database']};")
        print("\n   Ou utilisez psql:")
        print(f"   psql -U {config['user']} -c \"CREATE DATABASE {config['database']};\"")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Erreur lors de la vérification: {str(e)}")
    sys.exit(1)

# Test 3: Connexion à la base de données spécifique
print(f"\n🔍 Test 3: Connexion à la base de données '{config['database']}'...")
try:
    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        database=config["database"],
        user=config["user"],
        password=config["password"]
    )
    print(f"✅ Connexion à la base de données '{config['database']}' réussie")
    
    # Test simple de requête
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print(f"✅ Version PostgreSQL: {version[0][:50]}...")
    cur.close()
    conn.close()
    
    print("\n" + "="*50)
    print("✅ TOUS LES TESTS SONT PASSÉS!")
    print("="*50)
    print("\n🚀 Vous pouvez maintenant lancer l'application avec:")
    print("   python main.py")
    print("   ou")
    print("   streamlit run frontend/app.py")
    
except psycopg2.OperationalError as e:
    print(f"❌ Impossible de se connecter à la base de données '{config['database']}'")
    print(f"   Erreur: {str(e)}")
    print("\n💡 Solutions possibles:")
    print(f"   1. Créez la base de données: CREATE DATABASE {config['database']};")
    print("   2. Vérifiez les permissions de l'utilisateur")
    sys.exit(1)

