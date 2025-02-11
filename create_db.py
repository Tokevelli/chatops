# create_db.py


from project.app import app, db


with app.app_context():
    # Drop all existing tables and ensure a clean slate
    db.drop_all()
    
    # create the database and the db table
    db.create_all()

    # commit the changes
    db.session.commit()
