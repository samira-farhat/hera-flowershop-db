import mysql.connector

def connect_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Root",
            database="flowershop_management"
        )
        print("Connected to database successfully")
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

if __name__ == "__main__":
    connection = connect_db()
    if connection:
        connection.close()
