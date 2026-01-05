"""
Test de la configuration actuelle
"""
import sys
import os
import io

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(__file__))

from backend.database.connection import get_connection

print("="*60)
print("TEST DE LA CONFIGURATION ACTUELLE")
print("="*60)

try:
    print("\nTentative de connexion...")
    conn = get_connection()
    print("✅ Connexion réussie!")
    
    # Test simple
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()['version']
    print(f"✅ Version PostgreSQL: {version[:60]}...")
    
    # Vérifier la base
    cur.execute("SELECT current_database();")
    db = cur.fetchone()['current_database']
    print(f"✅ Base de données actuelle: {db}")
    
    cur.close()
    conn.close()
    
    print("\n" + "="*60)
    print("✅ TOUT FONCTIONNE!")
    print("="*60)
    
except Exception as e:
    print(f"\nERREUR: {str(e)}")
    print(f"   Type: {type(e).__name__}")
    import traceback
    print(f"\nDetails complets:")
    traceback.print_exc()
    
    # Afficher la configuration actuelle
    print("\n📋 Configuration actuelle:")
    with open("backend/database/connection.py", "r") as f:
        content = f.read()
        import re
        port_match = re.search(r'port=(\d+)', content)
        password_match = re.search(r'password="([^"]*)"', content)
        if port_match:
            print(f"   Port: {port_match.group(1)}")
        if password_match:
            pwd = password_match.group(1)
            print(f"   Password: {'(vide)' if pwd == '' else '***'}")
    
    print("\n💡 Solutions possibles:")
    print("1. Vérifiez que le port est correct")
    print("2. Vérifiez que PostgreSQL est démarré sur ce port")
    print("3. Vérifiez que le mot de passe est correct")
    print("4. Vérifiez que la base de données 'exam_scheduler' existe")

