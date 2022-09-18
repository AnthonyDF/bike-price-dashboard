import pandas as pd
from dotenv import load_dotenv
import os
import pandas.io.sql as psql
from sqlalchemy import create_engine


def load_credentials():
    load_dotenv()  # take environment variables from .env.

    # Database settings
    username = os.environ.get('POSTGRES_USERNAME')
    password = os.environ.get('POSTGRES_PASSWORD')
    hostname = os.environ.get('POSTGRES_HOSTNAME')
    port = os.environ.get('POSTGRES_PORT')
    database = os.environ.get('POSTGRES_DATABASE')

    return {'username': username,
            'password': password,
            'hostname': hostname,
            'port': port,
            'database': database}


def get_table(table, verbose=True):
    if verbose:
        print(f'Importing {table} data from postgres db')

    env = load_credentials()

    engine = create_engine(f"postgresql://{env['username']}:{env['password']}@{env['hostname']}:{env['port']}/{env['database']}")
    sql_query = f"SELECT * FROM {table}"
    df = psql.read_sql(sql_query, engine)
    engine.dispose()

    return df