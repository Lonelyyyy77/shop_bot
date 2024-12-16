import sqlite3

from database.db import DB_NAME


def get_menu_images_from_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, image_path, button_text FROM menu_images")
    menu_images = cursor.fetchall()
    conn.close()

    return menu_images