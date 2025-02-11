from project.app import db


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String, nullable=False)
    text = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Foreign key to User DSO
    user = db.relationship('User', backref='posts')  # Relationship back to User DSO

    def __init__(self, title, text, user_id):
        self.title = title
        self.text = text
        self.user_id = user_id # added 2.6.25 DSO

    def __repr__(self):
        return f"<title {self.title}>"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)

    def __init__(self, name, password):
        self.name = name
        self.password = password

    def __str__(self):
        return f"Username: {self.name}"

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('post_id', 'user_id', name='unique_like'),)

    def __repr__(self):
        return f'<Like post_id={self.post_id} user_id={self.user_id}>'
