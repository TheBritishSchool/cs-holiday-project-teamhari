import MySQLdb

# Replace these values with your actual database credentials
HOST = 'bkfanudhuvqg1xriyhdm-mysql.services.clever-cloud.com'
USER = 'uraexz57rm9ktsv8'
PASSWORD = 'XXeJ8prWdlq5SfsiFxwy'
DATABASE = 'bkfanudhuvqg1xriyhdm'
PORT = 3306

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
