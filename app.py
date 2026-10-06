import os
import secrets
import sqlite3

from flask import Flask
from flask import abort, redirect, render_template, request, session

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


def validate_text(value, field_name, maximum_length):
    if not value:
        return field_name + " is required."
    if len(value) > maximum_length:
        return field_name + " must be at most " + str(maximum_length) + " characters."
    return None


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


def get_recipe_form():
    return {
        "title": request.form.get("title", "").strip(),
        "ingredients": request.form.get("ingredients", "").strip(),
        "instructions": request.form.get("instructions", "").strip(),
    }


def validate_recipe_form(recipe, class_ids):
    error = validate_text(recipe["title"], "Title", 100)
    if error:
        return error
    error = validate_text(recipe["ingredients"], "Ingredients", 5000)
    if error:
        return error
    error = validate_text(recipe["instructions"], "Instructions", 10000)
    if error:
        return error
    if class_ids is None:
        return "Select only available classifications."
    if not class_ids:
        return "Select at least one classification."
    if not recipes.class_ids_exist(class_ids):
        return "Select only available classifications."
    return None


def render_recipe_form(template_name, recipe, selected_class_ids, error=None):
    classes = recipes.get_classes()
    return render_template(
        template_name,
        recipe=recipe,
        classes=classes,
        selected_class_ids=selected_class_ids,
        error=error,
    )


def render_recipe_page(recipe, comment_content="", comment_error=None):
    classes = recipes.get_recipe_classes(recipe["id"])
    comments = recipes.get_comments(recipe["id"])
    return render_template(
        "show_recipe.html",
        recipe=recipe,
        classes=classes,
        comments=comments,
        comment_content=comment_content,
        comment_error=comment_error,
    )


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
    return render_recipe_page(recipe)


@app.route("/new_recipe")
def new_recipe():
    require_login()
    recipe = {"title": "", "ingredients": "", "instructions": ""}
    return render_recipe_form("new_recipe.html", recipe, [])


@app.route("/create_recipe", methods=["POST"])
def create_recipe():
    require_login()
    check_csrf()

    recipe = get_recipe_form()
    class_ids = get_class_ids()
    error = validate_recipe_form(recipe, class_ids)
    if error:
        return render_recipe_form("new_recipe.html", recipe, class_ids or [], error)

    recipe_id = recipes.add_recipe(
        recipe["title"],
        recipe["ingredients"],
        recipe["instructions"],
        session["user_id"],
        class_ids,
    )
    return redirect("/recipe/" + str(recipe_id))


@app.route("/edit_recipe/<int:recipe_id>")
def edit_recipe(recipe_id):
    require_login()
    recipe = get_recipe_for_user(recipe_id)
    selected_class_ids = [item["id"] for item in recipes.get_recipe_classes(recipe_id)]
    return render_recipe_form("edit_recipe.html", recipe, selected_class_ids)


@app.route("/update_recipe", methods=["POST"])
def update_recipe():
    require_login()
    check_csrf()

    recipe_id = request.form.get("recipe_id", type=int)
    if recipe_id is None:
        abort(403)
    get_recipe_for_user(recipe_id)

    recipe = get_recipe_form()
    class_ids = get_class_ids()
    error = validate_recipe_form(recipe, class_ids)
    if error:
        recipe["id"] = recipe_id
        return render_recipe_form("edit_recipe.html", recipe, class_ids or [], error)

    recipes.update_recipe(
        recipe_id,
        recipe["title"],
        recipe["ingredients"],
        recipe["instructions"],
        class_ids,
    )
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

    content = request.form.get("content", "").strip()
    error = validate_text(content, "Note", 1000)
    if error:
        return render_recipe_page(recipe, content, error)

    recipes.add_comment(content, recipe_id, session["user_id"])
    return redirect("/recipe/" + str(recipe_id))


@app.route("/register")
def register():
    return render_template("register.html", username="")


@app.route("/create", methods=["POST"])
def create():
    check_csrf()
    username = request.form.get("username", "").strip()
    password1 = request.form.get("password1", "")
    password2 = request.form.get("password2", "")
    error = validate_text(username, "Username", 30)
    if error:
        return render_template("register.html", username=username, error=error)
    if not password1:
        return render_template(
            "register.html", username=username, error="Password is required."
        )
    if password1 != password2:
        return render_template(
            "register.html", username=username, error="Passwords do not match."
        )

    try:
        users.create_user(username, password1)
    except sqlite3.IntegrityError:
        return render_template(
            "register.html", username=username, error="That username is already taken."
        )

    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", username="")

    check_csrf()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    error = validate_text(username, "Username", 30)
    if error:
        return render_template("login.html", username=username, error=error)
    if not password:
        return render_template(
            "login.html", username=username, error="Password is required."
        )
    user_id = users.check_login(username, password)
    if user_id:
        session.clear()
        session["user_id"] = user_id
        session["username"] = username
        session["csrf_token"] = secrets.token_hex(16)
        return redirect("/")

    return render_template(
        "login.html", username=username, error="Sign-in details are incorrect."
    )


@app.route("/logout", methods=["POST"])
def logout():
    require_login()
    check_csrf()
    session.clear()
    return redirect("/")
