import mysql.connector
import time
import os
from mysql.connector import errors

DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'mysql'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', 'cursok8s'),
    'database': os.getenv('MYSQL_DATABASE', 'cursodb'),
}

def connect():
    while True:
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            print("Conectado a MySQL", flush=True)
            return conn
        except errors.Error as e:
            print(f"Esperando MySQL: {e}", flush=True)
            time.sleep(3)

def main():
    conn = connect()
    cursor = conn.cursor()

    while True:
        try:
            cursor.execute("SELECT id, payload FROM jobs ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED")
            row = cursor.fetchone()

            if row:
                job_id, payload = row
                cursor.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
                conn.commit()
                print(f"Procesado {payload}", flush=True)
            else:
                print("Sin jobs pendientes, esperando...", flush=True)

            time.sleep(5)
        except errors.Error as e:
            print(f"Error, reconectando: {e}", flush=True)
            conn = connect()
            cursor = conn.cursor()

if __name__ == '__main__':
    main()
