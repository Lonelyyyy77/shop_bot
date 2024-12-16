import sqlite3

DB_NAME = 'test.db'

def get_connection():
    return sqlite3.connect(DB_NAME)

def create_tables():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER
        )
        """)

        cursor.execute("""
                CREATE TABLE IF NOT EXISTS catalog_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name STRING,
                    price REAL,
                    desc TEXT,
                    image_path,
                    category INTEGER
                )
                """)

        cursor.execute("""
                    CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name STRING
                    )
                    """)

        cursor.execute("""
                    CREATE TABLE IF NOT EXISTS menu_images (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        button_text TEXT NOT NULL,
                        image_path TEXT
                    )
                    """)
        conn.commit()
