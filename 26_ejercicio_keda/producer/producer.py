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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            payload VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    count = 0
    while True:
        try:
            cursor.execute("INSERT INTO jobs (payload) VALUES (%s)", (f"job-{count}",))
            conn.commit()
            print(f"Insertado job-{count}", flush=True)
            count += 1
            time.sleep(1)
        except errors.Error as e:
            print(f"Error, reconectando: {e}", flush=True)
            conn = connect()
            cursor = conn.cursor()

if __name__ == '__main__':
    main()
