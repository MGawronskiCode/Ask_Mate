import os

import psycopg2
import psycopg2.extras


def get_connection_string():
    user = os.environ.get('PSQL_USER_NAME')
    password = os.environ.get('PSQL_PASSWORD')
    host = os.environ.get('PSQL_HOST')
    port = os.environ.get('PSQL_PORT', 5432)
    dbname = os.environ.get('PSQL_DB_NAME')

    env_variables_defined = user and password and host and port and dbname

    if env_variables_defined:
        return f'postgresql://{user}:{password}@{host}:{port}/{dbname}'
    else:
        raise KeyError('Some necessary enviroment variable(s) not defined')


def open_database():
    try:
        connection_string = get_connection_string()
        connection = psycopg2.connect(connection_string)
        connection.autocommit = True
    except psycopg2.DatabaseError as exception:
        print('Database connection problem')
        raise exception
    return connection


def connection_handler(function):
    def wrapper(*args, **kwargs):
        connection = open_database()
        dict_cur = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        ret_value = function(dict_cur, *args, **kwargs)
        dict_cur.close()
        connection.close()
        return ret_value

    return wrapper

# todo: open/close once per app run
