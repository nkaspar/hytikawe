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


def get_classes():
    sql = """SELECT id, title, value
             FROM classes
             ORDER BY title, value"""
    return db.query(sql)


def get_recipe_classes(recipe_id):
    sql = """SELECT classes.id, classes.title, classes.value
             FROM recipe_classes, classes
             WHERE recipe_classes.class_id = classes.id
             AND recipe_classes.recipe_id = ?
             ORDER BY classes.title, classes.value"""
    return db.query(sql, [recipe_id])


def class_ids_exist(class_ids):
    placeholders = ", ".join("?" for _ in class_ids)
    sql = "SELECT id FROM classes WHERE id IN (" + placeholders + ")"
    return len(db.query(sql, class_ids)) == len(class_ids)


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


def add_recipe(title, ingredients, instructions, user_id, class_ids):
    sql = """INSERT INTO recipes
             (title, ingredients, instructions, user_id)
             VALUES (?, ?, ?, ?)"""
    db.execute(sql, [title, ingredients, instructions, user_id])
    recipe_id = db.last_insert_id()
    set_recipe_classes(recipe_id, class_ids)
    return recipe_id


def update_recipe(recipe_id, title, ingredients, instructions, class_ids):
    sql = """UPDATE recipes
             SET title = ?, ingredients = ?, instructions = ?
             WHERE id = ?"""
    db.execute(sql, [title, ingredients, instructions, recipe_id])
    set_recipe_classes(recipe_id, class_ids)


def set_recipe_classes(recipe_id, class_ids):
    sql = "DELETE FROM recipe_classes WHERE recipe_id = ?"
    db.execute(sql, [recipe_id])
    sql = """INSERT INTO recipe_classes (recipe_id, class_id)
             VALUES (?, ?)"""
    for class_id in class_ids:
        db.execute(sql, [recipe_id, class_id])


def remove_recipe(recipe_id):
    sql = "DELETE FROM recipes WHERE id = ?"
    db.execute(sql, [recipe_id])
