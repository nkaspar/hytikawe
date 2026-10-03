import os
import secrets
import sqlite3

from flask import Flask
from flask import abort, flash, redirect, render_template, request, session

import recipes
import users


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "development-secret-key")


@app.before_request
def ensure_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)


def require_login():
    if "user_id" not in session:
        abort(403)


def get_recipe_for_user(recipe_id):
    recipe = recipes.get_recipe(recipe_id)
    if not recipe:
        abort(404)
    if recipe["user_id"] != session["user_id"]:
        abort(403)
    return recipe


def valid_text(value, maximum_length):
    return bool(value and value.strip() and len(value) <= maximum_length)


def check_csrf():
    if session.get("csrf_token") != request.form.get("csrf_token"):
        abort(403)


def get_class_ids():
    class_ids = []
    for value in request.form.getlist("class_ids"):
        try:
            class_ids.append(int(value))
        except ValueError:
            return None
    return class_ids


@app.route("/")
def index():
    all_recipes = recipes.get_recipes()
    return render_template("index.html", recipes=all_recipes)


@app.route("/user/<int:user_id>")
def show_user(user_id):
    user = users.get_user(user_id)
    if not user:
        abort(404)
    user_recipes = users.get_recipes(user_id)
    return render_template("show_user.html", user=user, recipes=user_recipes)


@app.route("/find_recipe")
def find_recipe():
    query = request.args.get("query", "").strip()
    results = recipes.find_recipes(query) if query else []
    return render_template("find_recipe.html", query=query, recipes=results)


@app.route("/recipe/<int:recipe_id>")
def show_recipe(recipe_id):
    recipe = recipes.get_recipe(recipe_id)
    if not recipe:
        abort(404)
    classes = recipes.get_recipe_classes(recipe_id)
    comments = recipes.get_comments(recipe_id)
    return render_template(
        "show_recipe.html", recipe=recipe, classes=classes, comments=comments
    )


@app.route("/new_recipe")
def new_recipe():
    require_login()
    classes = recipes.get_classes()
    return render_template("new_recipe.html", classes=classes)


@app.route("/create_recipe", methods=["POST"])
def create_recipe():
    require_login()
    check_csrf()

    title = request.form.get("title", "").strip()
    ingredients = request.form.get("ingredients", "").strip()
    instructions = request.form.get("instructions", "").strip()
    class_ids = get_class_ids()
    if not valid_text(title, 100):
        flash("Title is required and must be at most 100 characters.")
        return redirect("/new_recipe")
    if not valid_text(ingredients, 5000):
        flash("Ingredients are required and must be at most 5000 characters.")
        return redirect("/new_recipe")
    if not valid_text(instructions, 10000):
        flash("Instructions are required and must be at most 10000 characters.")
        return redirect("/new_recipe")
    if not class_ids or not recipes.class_ids_exist(class_ids):
        flash("Select at least one valid classification.")
        return redirect("/new_recipe")

    recipe_id = recipes.add_recipe(
        title, ingredients, instructions, session["user_id"], class_ids
    )
    return redirect("/recipe/" + str(recipe_id))


@app.route("/edit_recipe/<int:recipe_id>")
def edit_recipe(recipe_id):
    require_login()
    recipe = get_recipe_for_user(recipe_id)
    classes = recipes.get_classes()
    selected_class_ids = [item["id"] for item in recipes.get_recipe_classes(recipe_id)]
    return render_template(
        "edit_recipe.html",
        recipe=recipe,
        classes=classes,
        selected_class_ids=selected_class_ids,
    )


@app.route("/update_recipe", methods=["POST"])
def update_recipe():
    require_login()
    check_csrf()

    recipe_id = request.form.get("recipe_id", type=int)
    if recipe_id is None:
        abort(403)
    get_recipe_for_user(recipe_id)

    title = request.form.get("title", "").strip()
    ingredients = request.form.get("ingredients", "").strip()
    instructions = request.form.get("instructions", "").strip()
    class_ids = get_class_ids()
    if not valid_text(title, 100):
        flash("Title is required and must be at most 100 characters.")
        return redirect("/edit_recipe/" + str(recipe_id))
    if not valid_text(ingredients, 5000):
        flash("Ingredients are required and must be at most 5000 characters.")
        return redirect("/edit_recipe/" + str(recipe_id))
    if not valid_text(instructions, 10000):
        flash("Instructions are required and must be at most 10000 characters.")
        return redirect("/edit_recipe/" + str(recipe_id))
    if not class_ids or not recipes.class_ids_exist(class_ids):
        flash("Select at least one valid classification.")
        return redirect("/edit_recipe/" + str(recipe_id))

    recipes.update_recipe(recipe_id, title, ingredients, instructions, class_ids)
    return redirect("/recipe/" + str(recipe_id))


@app.route("/remove_recipe/<int:recipe_id>", methods=["GET", "POST"])
def remove_recipe(recipe_id):
    require_login()
    recipe = get_recipe_for_user(recipe_id)

    if request.method == "GET":
        return render_template("remove_recipe.html", recipe=recipe)

    check_csrf()
    recipes.remove_recipe(recipe_id)
    return redirect("/")


@app.route("/add_comment", methods=["POST"])
def add_comment():
    require_login()
    check_csrf()
    recipe_id = request.form.get("recipe_id", type=int)
    if recipe_id is None:
        abort(403)

    recipe = recipes.get_recipe(recipe_id)
    if not recipe:
        abort(404)
    if recipe["user_id"] == session["user_id"]:
        abort(403)

    content = request.form.get("content", "").strip()
    if not valid_text(content, 1000):
        flash("Comment is required and must be at most 1000 characters.")
        return redirect("/recipe/" + str(recipe_id))

    recipes.add_comment(content, recipe_id, session["user_id"])
    return redirect("/recipe/" + str(recipe_id))


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/create", methods=["POST"])
def create():
    check_csrf()
    username = request.form.get("username", "").strip()
    password1 = request.form.get("password1", "")
    password2 = request.form.get("password2", "")
    if not valid_text(username, 30) or not password1:
        flash("Username and password are required.")
        return redirect("/register")
    if password1 != password2:
        flash("The passwords do not match.")
        return redirect("/register")

    try:
        users.create_user(username, password1)
    except sqlite3.IntegrityError:
        flash("That username is already taken.")
        return redirect("/register")

    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    check_csrf()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    user_id = users.check_login(username, password)
    if user_id:
        session.clear()
        session["user_id"] = user_id
        session["username"] = username
        session["csrf_token"] = secrets.token_hex(16)
        return redirect("/")

    flash("Invalid username or password.")
    return redirect("/login")


@app.route("/logout", methods=["POST"])
def logout():
    require_login()
    check_csrf()
    session.clear()
    return redirect("/")
