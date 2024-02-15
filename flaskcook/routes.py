import os
import secrets
from PIL import Image
from flask import render_template, url_for, redirect, flash, request, abort
from flaskcook.forms import RegistrationForm, LoginForm, RecipeForm, UpdateProfileForm
from flaskcook.models import User, Recipe
from flaskcook import app, db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required

@app.route("/")
def home():
    recipes = Recipe.query.all()
    return render_template("home.html", recipes=recipes)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account created! You can now log in')
        return redirect(url_for("login"))

    return render_template("register.html", form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("home"))
        else:
            flash("Login Unsuccessful. Please check your username and password")
    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    logout_user()
    flash("You have been successfuly logged out!")
    return redirect(url_for("home"))

@app.route("/profile")
@login_required
def profile():
    image_file = url_for("static", filename="profile_pics/" + current_user.image_file)
    return render_template("profile.html", image_file=image_file)

def save_picture(form_picture, size, path):
    random_hex = secrets.token_hex(8)
    _, f_Ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_Ext
    print("App Root Path:", app.root_path)
    picture_path = os.path.join(app.root_path, path, picture_fn)
    i = Image.open(form_picture)
    i.thumbnail(size)
    print("Picture Path:", picture_path)
    i.save(picture_path)
    return picture_fn

@app.route("/profile/update", methods=['GET', 'POST'])
@login_required
def update_profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        if form.picture.data:
            size=(256,256)
            path = "static/profile_pics"
            picture_file = save_picture(form.picture.data, size, path)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account has been updated!")
        return redirect(url_for("profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template("update_profile.html", form=form)


@app.route("/recipe/new", methods=["GET", "POST"])
@login_required
def new_recipe():
    form = RecipeForm()
    picture_file = None
    if form.validate_on_submit():
        if form.picture.data:
            size = (512, 512)
            path = "static/pics"
            picture_file = save_picture(form.picture.data, size, path)
        recipe = Recipe(title=form.title.data, description=form.description.data, content=form.content.data, cook_time=form.cook_time.data, image_file=picture_file, author=current_user)
        db.session.add(recipe)
        db.session.commit()
        flash("Your recipe has been successfuly created!")
        return redirect(url_for("home"))
    return render_template("new_recipe.html", form=form)

@app.route("/recipe/<int:recipe_id>")
def recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    return render_template("recipe.html", recipe=recipe)

@app.route("/recipe/<int:recipe_id>/delete", methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.author != current_user:
        abort(403)
    db.session.delete(recipe)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for("home"))

@app.route("/recipe/<int:recipe_id>/update", methods=['GET', 'POST'])
@login_required
def update_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.author != current_user:
        abort(403)
    form = RecipeForm()
    if form.validate_on_submit():
        if form.picture.data:
            size = (512, 512)
            path = "static/pics"
            picture_file = save_picture(form.picture.data, size, path)
            recipe.image_file = picture_file
        recipe.title = form.title.data
        recipe.description = form.description.data
        recipe.content = form.content.data
        recipe.cook_time = form.cook_time.data
        db.session.commit()
        flash("Your recipe has been updated")
        return redirect(url_for("home"))
    elif request.method == "GET":
        form.title.data = recipe.title
        form.description.data = recipe.description
        form.content.data = recipe.content
        form.cook_time.data = recipe.cook_time
    return render_template("update_recipe.html", recipe=recipe, form=form)