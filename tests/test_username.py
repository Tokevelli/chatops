import bcrypt
import pytest
from sqlalchemy import text
from project import db
from project.app import create_app
from project import models

@pytest.fixture
def client():
    """Setup test client and manually create test user with hashed password."""
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test_secret",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "TestUser": "TestUser",
        "TestPassword": "TestPass"
    })

    with app.app_context():
        db.create_all()

        password = app.config["TestPassword"]
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Insert test user directly into the database
        db.session.execute(text("""
            INSERT INTO user (name, password)
            VALUES (:name, :password)
        """), {'name': app.config["TestUser"], 'password': hashed_password})
        db.session.commit()

    with app.test_client() as client:
        yield client

    with app.app_context():
        db.drop_all()


def create_user(client, username, password):
    """User creation helper function"""
    return client.post(
        "/newuser",
        data=dict(username=username, password=password),
        follow_redirects=True,
    )


def login(client, username, password):
    """Login helper function"""
    return client.post(
        "/login",
        data=dict(username=username, password=password),
        follow_redirects=True,
    )


def logout(client):
    """Logout helper function"""
    return client.get("/logout", follow_redirects=True)


def test_check_session_with_user(client):
    rv = login(client, "TestUser", "TestPass")
    assert b"Logged in as:" in rv.data

    response = client.get("/check_session")
    assert "TestUser" in response.data.decode("utf-8")

def test_password_hashing(client):
    """Ensure that passwords are stored hashed and salted using bcrypt"""
    username = "saltyuser"
    password = "notplain123"
    create_user(client, username, password)

    user = models.User.query.filter_by(name=username).first()
    assert user is not None
    assert user.password != password
    assert user.password.startswith("$2b$")

def test_like_unlike_post(client):
    """Ensure users can like and unlike a post"""
    login(client, "TestUser", "TestPass")

    # Add a post to like
    client.post("/add", data=dict(title="LikeMe", text="Like this post"), follow_redirects=True)
    post = models.Post.query.filter_by(title="LikeMe").first()
    assert post is not None

    # Like the post (note: this route expects POST)
    rv = client.post(f"/like_post/{post.id}", follow_redirects=True)
    data = rv.get_json()
    assert data["status"] == "liked"
    assert data["likes_count"] == 1

    # Unlike the post
    rv = client.post(f"/like_post/{post.id}", follow_redirects=True)
    data = rv.get_json()
    assert data["status"] == "unliked"
    assert data["likes_count"] == 0

def test_profile_shows_user_posts(client):
    """Ensure the profile page displays only posts by the logged-in user"""
    login(client, "TestUser", "TestPass")

    # Create two posts for the logged-in user
    client.post("/add", data=dict(title="Test Post 1", text="Text A"), follow_redirects=True)
    client.post("/add", data=dict(title="Test Post 2", text="Text B"), follow_redirects=True)

    rv = client.get("/profile")
    assert b"Test Post 1" in rv.data
    assert b"Test Post 2" in rv.data
