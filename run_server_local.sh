#!/bin/bash
# run dbbact sequence translator
source activate dbbact2
echo "running dbbact sequence translator server local. to access send requests to http://127.0.0.1:5021"
export DBBACT_SEQUENCE_TRANSLATOR_SERVER_TYPE="main"
gunicorn 'dbbact_sequence_translator.Server_Main:gunicorn(debug_level=2)' -b 0.0.0.0:5021 --workers 1 --name=main-sequence-translator-dbbact --timeout 300 --reload
