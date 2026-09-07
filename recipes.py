import db


def get_recipes():
    sql = """SELECT recipes.id, recipes.title, recipes.user_id, users.username
             FROM recipes, users
             WHERE recipes.user_id = users.id
             ORDER BY recipes.id DESC"""
    return db.query(sql)


def get_recipe(recipe_id):
    sql = """SELECT recipes.id, recipes.title, recipes.ingredients,
                    recipes.instructions, recipes.user_id, users.username
             FROM recipes, users
             WHERE recipes.user_id = users.id AND recipes.id = ?"""
    result = db.query(sql, [recipe_id])
    return result[0] if result else None


def find_recipes(query):
    sql = """SELECT recipes.id, recipes.title, recipes.user_id, users.username
             FROM recipes, users
             WHERE recipes.user_id = users.id
             AND (recipes.title LIKE ?
                  OR recipes.ingredients LIKE ?
                  OR recipes.instructions LIKE ?)
             ORDER BY recipes.id DESC"""
    search = "%" + query + "%"
    return db.query(sql, [search, search, search])


def add_recipe(title, ingredients, instructions, user_id):
    sql = """INSERT INTO recipes
             (title, ingredients, instructions, user_id)
             VALUES (?, ?, ?, ?)"""
    db.execute(sql, [title, ingredients, instructions, user_id])
    return db.last_insert_id()


def update_recipe(recipe_id, title, ingredients, instructions):
    sql = """UPDATE recipes
             SET title = ?, ingredients = ?, instructions = ?
             WHERE id = ?"""
    db.execute(sql, [title, ingredients, instructions, recipe_id])


def remove_recipe(recipe_id):
    sql = "DELETE FROM recipes WHERE id = ?"
    db.execute(sql, [recipe_id])
