import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import OperationalError

def get_connection():
    try:
        return psycopg2.connect(
            host="localhost",
            port=5432,
            database="exam_scheduler",
            user="postgres",
            password="mimibkh123",
            cursor_factory=RealDictCursor
        )
    except OperationalError as e:
        error_msg = str(e) if str(e) else repr(e)
        raise OperationalError(
            f"Impossible de se connecter à PostgreSQL. "
            f"Vérifiez que PostgreSQL est démarré et que la base de données 'exam_scheduler' existe.\n"
            f"Erreur: {error_msg}"
        )
