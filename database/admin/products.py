import sqlite3
import logging

from database.db import get_connection, DB_NAME


def add_product_to_db(name, price, desc, image_path, category):
    query = """
    INSERT INTO catalog_products (name, price, desc, image_path, category)
    VALUES (?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (name, price, desc, image_path, category))
        conn.commit()


def add_category_to_db(category_name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
    conn.commit()
    conn.close()


def get_categories_from_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM categories")
    categories = cursor.fetchall()
    conn.close()

    return [{'id': category[0], 'name': category[1]} for category in categories]


def get_products_by_category(category):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, price, desc, image_path, category
        FROM catalog_products
        WHERE category = ?
    """, (category,))
    products = cursor.fetchall()
    conn.close()

    return [{
        'id': product[0],
        'name': product[1],
        'price': product[2],
        'description': product[3],
        'photo_path': product[4],
        'category': product[5]
    } for product in products]


def get_catalog_products_from_db(category_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, desc, image_path, category FROM catalog_products WHERE category=?", (category_name,))
    products = cursor.fetchall()
    conn.close()

    logging.info(products)
    return [{'id': product[0], 'name': product[1], 'price': product[2], 'description': product[3], 'image_path': product[4], 'category': product[5]} for product in products]
