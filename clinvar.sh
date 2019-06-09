#!/bin/sh
echo 'hello from clinvar.sh'
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
echo 'calling mongod'
mongod &
echo 'back from mongod'
echo 'calling clinvar.py'
python3 clinvar.py
echo 'back from clinvar.py'
export FLASK_APP=cv_server.py
flask run
