import os
import logging
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, session, flash, redirect, url_for, abort, jsonify
from project import db
import bcrypt

def create_app(test_config=None):
    app = Flask(__name__)

    # Configure logging
    if not app.debug:
        # Ensures logs are only set up for non-debug mode
        logging.basicConfig(filename='/var/log/app/app.log', level=logging.INFO,
                            format='%(asctime)s:%(levelname)s:%(message)s')

    # Use test config if passed
    if test_config:
        app.config.update(test_config)
    else:
        # Default production config
        db_user = os.getenv('SQL_USERNAME', 'myuser')
        db_password = os.getenv('SQL_PASSWORD', 'mypassword')
        db_host = os.getenv('SQL_HOST', 'db')
        db_port = os.getenv('SQL_PORT', '3306')
        db_name = os.getenv('SQL_DATABASE', 'shareSpace')
        app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        from project import models
        db.create_all()

    return app

    # ====================
    # Routes and helpers
    # ====================

    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get("logged_in"):
                flash("Please log in.")
                return jsonify({"status": 0, "message": "Please log in."}), 401
            return f(*args, **kwargs)
        return decorated_function

    @app.route("/")
    def index():
        entries = db.session.query(models.Post)
        print(f"Session data: {session}")
        print(f"{session.get('username') or 'No user'} is logged in")
        return render_template("index.html", entries=entries)

    @app.route("/add", methods=["POST"])
    def add_entry():
        if not session.get("logged_in"):
            abort(401)
        new_entry = models.Post(request.form["title"], request.form["text"], session.get("user_id"))
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
                session["user_id"] = user.id
                session["username"] = user.name
                print("Session set for user:", session["username"])
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
                session["user_id"] = newuser.id
                flash("New User Created")
                return redirect(url_for("index"))
            except Exception as e:
                return render_template("newuser.html", error="Error when adding user")
        else:
            return render_template("newuser.html")

    @app.route("/logout")
    def logout():
        session.pop("logged_in", None)
        session.pop("user_id", None)
        flash("You were logged out")
        return redirect(url_for("index"))

    @app.route("/delete/<int:post_id>", methods=["GET"])
    @login_required
    def delete_entry(post_id):
        result = {"status": 0, "message": "Error"}
        try:
            db.session.query(models.Post).filter_by(id=post_id).delete()
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
        return render_template("search.html", entries=entries, query=query)

    @app.route("/like_post/<int:post_id>", methods=["POST"])
    @login_required
    def like_post(post_id):
        user_id = session.get("user_id")
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
        if "username" in session:
            return f"Logged in as: {session['username']}"
        return "Not logged in"


    @app.route("/profile")
    @login_required
    def profile():
        user_id = session.get("user_id")
        user = db.session.query(models.User).get(user_id)
        user_posts = db.session.query(models.Post).filter_by(user_id=user_id).all()
        return render_template("profile.html", posts=user_posts, user=user)

    return app

# Run the app directly (development only)
if __name__ == "__main__":
    create_app().run(host='0.0.0.0')
