"""
Diagnostic du problème de port
"""
import psycopg2
import sys
import io

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("="*60)
print("DIAGNOSTIC DU PROBLEME DE PORT")
print("="*60)

# Tester différents ports
ports = [5432, 5433, 5434, 5435]
passwords = ["1234", "", "postgres", "admin"]

print("\nQuel port avez-vous modifie dans connection.py?")
print("Port actuel dans connection.py: 5432")

print("\nTest de connexion sur differents ports...")
print("="*60)

for port in ports:
    print(f"\nPort {port}:")
    for password in passwords:
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=port,
                database="postgres",
                user="postgres",
                password=password,
                connect_timeout=2
            )
            
            cur = conn.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            
            print(f"  OK! Port {port} fonctionne")
            print(f"  Mot de passe: {'(vide)' if password == '' else password}")
            print(f"  Version: {version[:50]}...")
            
            # Verifier la base
            cur.execute("SELECT 1 FROM pg_database WHERE datname = 'exam_scheduler'")
            if cur.fetchone():
                print(f"  Base 'exam_scheduler' existe")
            else:
                print(f"  Base 'exam_scheduler' n'existe pas")
            
            cur.close()
            conn.close()
            
            print(f"\nSOLUTION: Utilisez port={port} et password='{password}'")
            break
            
        except psycopg2.OperationalError as e:
            error_str = str(e).lower()
            if "password" in error_str or "authentication" in error_str:
                continue
            elif "could not connect" in error_str or "timeout" in error_str or "refused" in error_str:
                print(f"  Port {port} non accessible")
                break
            else:
                continue
        except Exception as e:
            continue
    else:
        continue
    break

print("\n" + "="*60)
print("Si aucun port ne fonctionne:")
print("1. Verifiez dans pgAdmin quel port utilise PostgreSQL 16")
print("2. Assurez-vous que PostgreSQL 16 est demarre")
print("3. Modifiez backend/database/connection.py avec le bon port")
print("="*60)

