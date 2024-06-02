import psycopg2
import yaml


def create_connection():
    with open("settings.yaml", 'r') as stream:
        config = yaml.safe_load(stream)

    db_config = config['database']

    conn = psycopg2.connect(
        dbname=db_config['name'],
        user=db_config['user'],
        password=db_config['password'],
        host=db_config['host'],
        port=db_config['port']
    )
    return conn

def get_password():
    with open("settings.yaml", 'r') as stream:
        config = yaml.safe_load(stream)
    return config['private_hash']['password']