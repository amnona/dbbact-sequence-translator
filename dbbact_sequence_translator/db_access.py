import psycopg2
import psycopg2.extras

from .utils import debug


def connect_translator_db(server_type=None, database=None, user=None, password=None, port=None, host=None):
    """
    connect to the sequence translator postgres database and return the connection and cursor

    Parameters
    ----------
    server_type: str
        type of server to connect to. overrides the other default parameters
        options are:
            'main', 'develop', 'test'
    database: str, optional
        name of the database to connect to (usually 'sequence_translator_dbbact'/'sequence_translator_dbbact_develop'/'sequence_translator_dbbact_test')
    host: str or False or None
        False to not pass host parameter
        None to use server_type defaults
        str to connect to given host

    Returns
    -------
    con : the psycopg database connection
    cur : the psycopg database cursor (DictCursor)
    """
    # set the default values
    chost = False
    cport = 5432
    cpassword = 'sequence_translator_dbbact'
    cuser = 'sequence_translator_dbbact'
    cdatabase = 'sequence_translator_dbbact'
    # process first server type and then override by function parameters
    if server_type is not None:
        debug(1, 'connecting to sequence translator database using server type %s' % server_type)
        if server_type == 'develop':
            cuser = 'sequence_translator_dbbact_develop'
            cdatabase = 'sequence_translator_dbbact_develop'
            cpassword = 'sequence_translator_dbbact_develop'
        elif server_type == 'test':
            cuser = 'sequence_translator_dbbact_test'
            cdatabase = 'sequence_translator_dbbact_test'
            cpassword = 'sequence_translator_dbbact_test'
        elif server_type == 'main':
            pass
        else:
            debug(6, 'translator server type has unrecognized value %s. please use one of ["main", "develop", "test"]. using "main" as default' % server_type)
    # override by function parameters
    if database is not None:
        cdatabase = database
    if user is not None:
        cuser = user
    if password is not None:
        cpassword = password
    if port is not None:
        cport = port
    if host is not None:
        chost = host
    # convert port to number since env. parameter can be str
    cport = int(cport)
    try:
        debug(1, 'connecting host=%s, database=%s, user=%s, port=%d' % (chost, cdatabase, cuser, cport))
        if chost is False:
            con = psycopg2.connect(database=cdatabase, user=cuser, password=cpassword, port=cport)
        else:
            con = psycopg2.connect(host=chost, database=cdatabase, user=cuser, password=cpassword, port=cport)
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
        debug(1, 'connected to database')
        return (con, cur)
    except psycopg2.DatabaseError as e:
        msg = 'Cannot connect to sequence translator database %s. Error %s' % (server_type, e)
        debug(3, msg)
        raise SystemError(msg)
        return None
