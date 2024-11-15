from sqlite3 import connect, Connection, Cursor
from .settings import create_db

def create(name :str ='db') -> tuple[Connection, Cursor]:
    if name:
        conn = connect(f'{name}.sqlite3')
        cur = conn.cursor()
    return conn,cur


def execute_query(query):
    if create_db:
        connection, cursor = create()
        with connection as connection:
            query = cursor.execute(query)
            connection.commit()
        return query
    