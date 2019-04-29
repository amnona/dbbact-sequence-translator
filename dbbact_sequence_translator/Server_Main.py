import os

from flask import Flask, g, request

from .autodoc import auto
from .flask_translate import Translate_Obj
from .flask_docs import Docs_Flask_Obj
from .utils import debug, SetDebugLevel
from . import db_access


app = Flask(__name__)
app.register_blueprint(Translate_Obj)
app.register_blueprint(Docs_Flask_Obj)

auto.init_app(app)


# whenever a new request arrives, connect to the database and store in g.db
@app.before_request
def before_request():
    if request.remote_addr != '127.0.0.1':
        debug(6, 'got request for page %s' % request.url, request=request)
    else:
        debug(1, 'got local request for page %s' % request.url, request=request)
    con, cur = db_access.connect_translator_db(server_type=app.config.get('DBBACT_SERVER_TYPE'),
                                               host=app.config.get('DBBACT_POSTGRES_HOST'),
                                               port=app.config.get('DBBACT_POSTGRES_PORT'),
                                               database=app.config.get('DBBACT_POSTGRES_DATABASE'),
                                               user=app.config.get('DBBACT_POSTGRES_USER'),
                                               password=app.config.get('DBBACT_POSTGRES_PASSWORD'))
    g.con = con
    g.cur = cur


# and when the request is over, disconnect
@app.teardown_request
def teardown_request(exception):
    g.con.close()


# handle the cross-site scripting requests (CORS)
# code from https://stackoverflow.com/questions/25594893/how-to-enable-cors-in-flask-and-heroku
# used for the html interactive heatmaps that need reposnse from the dbbact api from within a browser
@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    # this part from: https://stackoverflow.com/questions/25727306/request-header-field-access-control-allow-headers-is-not-allowed-by-access-contr
    header["Access-Control-Allow-Headers"] = "Origin, X-Requested-With, Content-Type, Accept"
    return response


def gunicorn(server_type=None, pg_host=None, pg_port=None, pg_db=None, pg_user=None, pg_pwd=None, debug_level=6):
    '''The entry point for running the sequence translator api server through gunicorn (http://gunicorn.org/)
    to run sequence translator dbbact rest server using gunicorn, use:

    gunicorn 'dbbact_sequence_translator.Server_Main:gunicorn(server_type='main', debug_level=6)' -b 0.0.0.0:5021 --workers 4 --name=dbbact-sequence-translator


    Parameters
    ----------
    server_type: str or None, optional
        the server instance running. used for db_access(). can be: 'main','develop','test','local'
        None to use the DBBACT_SERVER_TYPE environment variable instead
    pg_host, pg_port, pg_db, pg_user, pg_pwd: str or None, optional
        str to override the env. variable and server_type selected postgres connection parameters
    debug_level: int, optional
        The minimal level of debug messages to log (10 is max, ~5 is equivalent to warning)

    Returns
    -------
    Flask app
    '''
    SetDebugLevel(debug_level)
    # to enable the stack traces on error
    # (from https://stackoverflow.com/questions/18059937/flask-app-raises-a-500-error-with-no-exception)
    app.debug = True
    debug(6, 'starting dbbact rest-api server using gunicorn, debug_level=%d' % debug_level)
    set_env_params()
    if server_type is not None:
        app.config['DBBACT_SEQUENCE_TRANSLATOR_SERVER_TYPE'] = server_type
    if pg_host is not None:
        app.config['DBBACT_SEQUENCE_TRANSLATOR_POSTGRES_HOST'] = pg_host
    if pg_port is not None:
        app.config['DBBACT_SEQUENCE_TRANSLATOR_POSTGRES_PORT'] = pg_port
    if pg_user is not None:
        app.config['DBBACT_SEQUENCE_TRANSLATOR_POSTGRES_USER'] = pg_user
    if pg_pwd is not None:
        app.config['DBBACT_SEQUENCE_TRANSLATOR_POSTGRES_PASSWORD'] = pg_user
    if pg_db is not None:
        app.config['DBBACT_SEQUENCE_TRANSLATOR_POSTGRES_DATABASE'] = pg_db

    return app


def set_env_params():
    # set the database access parameters
    env_params = ['DBBACT_SEQUENCE_TRANSLATOR_SERVER_TYPE', 'DBBACT_SEQUENCE_TRANSLATOR_POSTGRES_HOST', 'DBBACT_SEQUENCE_TRANSLATOR_POSTGRES_PORT', 'DBBACT_SEQUENCE_TRANSLATOR_POSTGRES_DATABASE', 'DBBACT_SEQUENCE_TRANSLATOR_POSTGRES_USER', 'DBBACT_SEQUENCE_TRANSLATOR_POSTGRES_PASSWORD']
    for cparam in env_params:
            cval = os.environ.get(cparam)
            if cval is not None:
                debug(5, 'using value %s for env. parameter %s' % (cval, cparam))
            app.config[cparam] = cval


if __name__ == '__main__':
    SetDebugLevel(1)
    debug(2, 'starting server')
    set_env_params()
    app.run(port=5001, threaded=True)
