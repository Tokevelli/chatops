
# chatops
Group Project Code Dump

ShareSpace Social Media

ShareSpace -- a mini-blog-like-app
Install requirements

Be sure you have pip3 installed already (sudo apt install python3-pip)

pip3 install -r requirements.txt

python3 create_db.py # create the sqlite3 database
Run Flaskr

python3 -m flask -A project/app.py run --host=0.0.0.0 # This runs on port 5000 by default, use --port=#### to specify another port
Run Tests
python3 -m pytest

Note: In order to pass this test, you can run create_db.py and copy over the resulting .db file to this directory named test.db
