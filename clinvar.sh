#!/bin/sh
python clinvar.py
export FLASK_APP=cv_server.py
flask run
