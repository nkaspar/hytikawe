from werkzeug.security import check_password_hash, generate_password_hash

import db


def get_user(user_id):
    sql = "SELECT id, username FROM users WHERE id = ?"
    result = db.query(sql, [user_id])
    return result[0] if result else None


def get_recipes(user_id, limit, offset):
    sql = """SELECT id, title
        FROM recipes
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ? OFFSET ?"""
    return db.query(sql, [user_id, limit, offset])


def count_recipes(user_id):
    sql = "SELECT COUNT(*) AS count FROM recipes WHERE user_id = ?"
    return db.query(sql, [user_id])[0]["count"]


def create_user(username, password):
    password_hash = generate_password_hash(password)
    sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
    db.execute(sql, [username, password_hash])


def check_login(username, password):
    sql = "SELECT id, password_hash FROM users WHERE username = ?"
    result = db.query(sql, [username])
    if not result:
        return None

    user_id = result[0]["id"]
    password_hash = result[0]["password_hash"]
    if check_password_hash(password_hash, password):
        return user_id
    return None
