import MySQLdb
import os

HOST = os.environ.get("MYSQL_HOST")
USER = os.environ.get("MYSQL_USER")
PASSWORD = os.environ.get("MYSQL_PASSWORD")
DATABASE = os.environ.get("MYSQL_DATABASE")
PORT = os.environ.get("MYSQL_PORT")

def test_connection():
    try:
        print(f"Connecting to MySQL at {HOST}:{PORT} with user {USER}")
        connection = MySQLdb.connect(
            host=HOST,
            user=USER,
            passwd=PASSWORD,
            db=DATABASE,
            port=PORT
        )
        print("Connection successful!")
        connection.close()
    except MySQLdb.OperationalError as e:
        print(f"OperationalError: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_connection()
