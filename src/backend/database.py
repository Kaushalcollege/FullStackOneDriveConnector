import psycopg2
from psycopg2.extras import RealDictCursor

#Using the same database. -- Azure Connector.
hostname = 'localhost'
database = 'AzureConnector'
username = 'postgres'
port_id = 5432
pwd = "Prince@2709"

#define a connection method for every-time use.
def get_connection():
    return psycopg2.connect(
        dbname = database,
        user = username,
        password = pwd,
        host =  hostname,
        port = port_id,
        cursor_factory=RealDictCursor
    )

#now whenever we need a connection, we can import this function from database.py.