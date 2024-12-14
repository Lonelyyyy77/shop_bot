from database.db import get_connection

def add_admin(admin_id):
    query = "INSERT INTO admins (tg_id) VALUES (?)"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (admin_id,))
        conn.commit()

def get_all_admins():
    query = "SELECT * FROM admins"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()

