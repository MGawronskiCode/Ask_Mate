import csv
import os

import psycopg2
import psycopg2.extras


def read_data_from_file(file_name):
    data_list = []
    try:
        with open(file_name, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data_list.append(row)
        return data_list
    except IOError:
        return "IOError"


def write_data_to_file(file_name, fieldnames, data_to_add, mode='a', separator=','):
    if mode == 'a':
        with open(file_name, mode) as file:
            writer = csv.DictWriter(file, fieldnames, delimiter=",")  # fieldnames=DATA_HEADER
            writer.writerow(data_to_add)
    elif mode == 'w':
        with open(file_name, mode) as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=separator)  # fieldnames=DATA_HEADER
            writer.writeheader()
            writer.writerows(data_to_add)


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
