#!/bin/sh
echo 'starting clinvar.sh'
echo 'calling cv_fetcher.py'
python3 cv_fetcher.py
echo 'back from cv_fetcher.py'
echo 'calling gunzip'
gunzip -v *.gz
echo 'back from gunzip'
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
echo 'starting mongod'
mongod --quiet &
echo 'back from mongod'
echo 'starting clinvar.py'
python3 clinvar.py
echo 'back from clinvar.py'
echo 'starting flask'
flask run --host=0.0.0.0
