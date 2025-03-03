import os
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, session, flash, redirect, url_for, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
import bcrypt

# create and initialize a new Flask app
app = Flask(__name__)

# Base directory
basedir = Path(__file__).resolve().parent

# Determine the database path
if os.getenv('FLASK_ENV') == 'production':
    db_path = "/app/dbdir/shareSpace.db"  # Corrected path inside the container
else:
    db_path = basedir.joinpath("shareSpace.db")  # Local development path

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL') or f"sqlite:///{db_path}"
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# init sqlalchemy
db = SQLAlchemy(app)

# Ensure models are loaded after Flask and db initialization
from project import models

# Decorator for requiring login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in.")
            return jsonify({"status": 0, "message": "Please log in."}), 401
        return f(*args, **kwargs)
    return decorated_function

# Route definitions
@app.route("/")
def index():
    """Searches the database for entries, then displays them."""
    entries = db.session.query(models.Post)
    print(f"Session data: {session}")  # Debugging session contents
    print(f"{session.get('username') or 'No user'} is logged in")
    return render_template("index.html", entries=entries)

@app.route("/add", methods=["POST"])
def add_entry():
    """Adds new post to the database."""
    if not session.get("logged_in"):
        abort(401)
    new_entry = models.Post(request.form["title"], request.form["text"], session.get("user_id")) # Modified DSO 2.9.25
    db.session.add(new_entry)
    db.session.commit()
    flash("New entry was successfully posted")
    return redirect(url_for("index"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user = db.session.query(models.User).filter_by(name=request.form["username"]).first()
        if user and user.check_password(request.form["password"]):
            session["logged_in"] = True
            session["user_id"] = user.id # Stores user_id in session
            session["username"] = user.name  # Set username in session
            print("Session set for user:", session["username"])  # Debugging line
            return redirect(url_for("index"))
        else:
            error = "Invalid username or password"
    return render_template("login.html", error=error)

@app.route("/newuser", methods=["GET", "POST"])
def new_user():
    if request.method == "POST" and request.form.get("password") and request.form.get("username"):
        newuser = models.User(request.form["username"], request.form["password"])
        try:
            db.session.add(newuser)
            db.session.commit()
            session["logged_in"] = True
            session["user_id"] = newuser.id  # Store user_id in session
            flash("New User Created")
            return redirect(url_for("index"))
        except Exception as e:
            return render_template("newuser.html", error="Error when adding user")
    else:
        return render_template("newuser.html")

@app.route("/logout")
def logout():
    """User logout/authentication/session management."""
    session.pop("logged_in", None)
    session.pop("user_id", None)  # Remove user_id from session DSO
    flash("You were logged out")
    return redirect(url_for("index"))

@app.route("/delete/<int:post_id>", methods=["GET"])
@login_required
def delete_entry(post_id):
    """Deletes post from database."""
    result = {"status": 0, "message": "Error"}
    try:
        new_id = post_id
        db.session.query(models.Post).filter_by(id=new_id).delete()
        db.session.commit()
        result = {"status": 1, "message": "Post Deleted"}
        flash("The entry was deleted.")
    except Exception as e:
        result = {"status": 0, "message": repr(e)}
    return jsonify(result)

@app.route("/search/", methods=["GET"])
def search():
    query = request.args.get("query")
    entries = db.session.query(models.Post)
    if query:
        return render_template("search.html", entries=entries, query=query)
    return render_template("search.html")

@app.route("/like_post/<int:post_id>", methods=["POST"])
@login_required
def like_post(post_id):
    user_id = session.get("user_id")  # Retrieve user_id from session
    if user_id is None:
        return jsonify({'status': 'error', 'message': 'User not logged in'}), 403

    like = db.session.query(models.Like).filter_by(post_id=post_id, user_id=user_id).first()
    if not like:
        new_like = models.Like(post_id=post_id, user_id=user_id)
        db.session.add(new_like)
        try:
            db.session.commit()
            likes_count = db.session.query(models.Like).filter_by(post_id=post_id).count()
            return jsonify({'status': 'liked', 'likes_count': likes_count})
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
    else:
        db.session.delete(like)
        db.session.commit()
        likes_count = db.session.query(models.Like).filter_by(post_id=post_id).count()
        return jsonify({'status': 'unliked', 'likes_count': likes_count})

@app.route("/check_session")
def check_session():
    if "user_id" in session:
        return f"User ID in session: {session['user_id']}"
    return "No user ID in session"

@app.route("/profile")  # Profile page route
@login_required
def profile():
    """Displays the profile page with user's posts."""
    user_id = session.get("user_id") 
    user = db.session.query(models.User).get(user_id)
    user_posts = db.session.query(models.Post).filter_by(user_id=user_id).all()
    return render_template("profile.html", posts=user_posts, user=user)

if __name__ == "__main__":
    app.run(host='0.0.0.0')

