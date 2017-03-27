#!/bin/bash
source ../metterboard/venv/bin/activate
export FLASK_APP='metterboard.py'
flask initdb
flask run
