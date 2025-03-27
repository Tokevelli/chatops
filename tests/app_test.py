import json
import pytest
from project import db, models
from project.app import create_app

@pytest.fixture
def client():
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test_secret_key",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "TestUser": "Bob",
        "TestPassword": "abc123"
    })

    with app.app_context():
        db.create_all()
        testuser = models.User(app.config["TestUser"], app.config["TestPassword"])
        db.session.add(testuser)
        db.session.commit()

    with app.test_client() as client:
        yield client

    with app.app_context():
        db.drop_all()


def login(client, username, password):
    return client.post(
        "/login",
        data=dict(username=username, password=password),
        follow_redirects=True,
    )


def logout(client):
    return client.get("/logout", follow_redirects=True)


def create_user(client, username, password):
    return client.post(
        "/newuser",
        data=dict(username=username, password=password),
        follow_redirects=True,
    )


def test_index(client):
    response = client.get("/", content_type="html/text")
    assert response.status_code == 200


def test_empty_db(client):
    rv = client.get("/")
    assert b"No entries yet. Add some!" in rv.data


def test_user_creation(client):
    response = login(client, "jeff", "mypass")
    assert b"Invalid username or password" in response.data
    response = create_user(client, "jeff", "mypass")
    assert b"New User Created" in response.data
    response = login(client, "jeff", "mypass")
    assert response.status_code == 200
    assert b"Logged in as" in response.data


def test_login_logout(client):
    rv = login(client, "Bob", "abc123")
    assert b"Logged in as" in rv.data
    rv = logout(client)
    assert b"You were logged out" in rv.data
    rv = login(client, "Bobx", "abc123")
    assert b"Invalid username or password" in rv.data
    rv = login(client, "Bob", "wrongpass")
    assert b"Invalid username or password" in rv.data


def test_messages(client):
    login(client, "Bob", "abc123")
    rv = client.post(
        "/add",
        data=dict(title="<Hello>", text="<strong>HTML</strong> allowed here"),
        follow_redirects=True,
    )
    assert b"No entries yet. Add some!" not in rv.data
    assert b"&lt;Hello&gt;" in rv.data
    assert b"<strong>HTML</strong> allowed here" in rv.data


def test_delete_message(client):
    rv = client.get("/delete/1")
    data = json.loads(rv.data)
    assert data["status"] == 0

    login(client, "Bob", "abc123")
    client.post(
        "/add",
        data=dict(title="ToDelete", text="This will be deleted"),
        follow_redirects=True,
    )

    post = models.Post.query.filter_by(title="ToDelete").first()
    assert post is not None

    rv = client.get(f"/delete/{post.id}")
    data = json.loads(rv.data)
    assert data["status"] == 1
