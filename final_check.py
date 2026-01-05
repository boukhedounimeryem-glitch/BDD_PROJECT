"""
Vérification finale de la configuration
"""
import psycopg2
import sys
import io

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("="*60)
print("VÉRIFICATION FINALE")
print("="*60)

# Lire la configuration actuelle
print("\n📋 Configuration actuelle:")
try:
    with open("backend/database/connection.py", "r", encoding="utf-8") as f:
        content = f.read()
        import re
        port_match = re.search(r'port=(\d+)', content)
        password_match = re.search(r'password="([^"]*)"', content)
        if port_match:
            current_port = int(port_match.group(1))
            print(f"   Port: {current_port}")
        if password_match:
            current_password = password_match.group(1)
            print(f"   Password: {'(vide)' if current_password == '' else current_password}")
except Exception as e:
    print(f"   Erreur: {e}")

print("\n🔍 Test de connexion...")

# Tester avec le mot de passe actuel
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="exam_scheduler",
        user="postgres",
        password="1234",
        connect_timeout=5
    )
    print("✅ Connexion réussie avec le mot de passe '1234'!")
    conn.close()
    print("\n🚀 Tout est prêt! Vous pouvez lancer l'application:")
    print("   python main.py")
except psycopg2.OperationalError as e:
    error_str = str(e).lower()
    print(f"❌ Erreur: {str(e)}")
    
    if "password" in error_str or "authentication" in error_str:
        print("\n💡 Le mot de passe '1234' est incorrect.")
        print("\n📝 Pour corriger:")
        print("   1. Trouvez le mot de passe dans pgAdmin (PostgreSQL 18 → Properties → Connection)")
        print("   2. Modifiez backend/database/connection.py ligne 12")
        print("   3. Remplacez password=\"1234\" par password=\"VOTRE_MOT_DE_PASSE\"")
    elif "database" in error_str and "does not exist" in error_str:
        print("\n💡 La base de données 'exam_scheduler' n'existe pas.")
        print("\n📝 Pour créer la base:")
        print("   1. Connectez-vous à PostgreSQL 18 dans pgAdmin")
        print("   2. Clic droit sur Databases → Create → Database")
        print("   3. Nom: exam_scheduler")
        print("   4. Save")
    else:
        print(f"\n💡 Erreur de connexion: {str(e)}")

