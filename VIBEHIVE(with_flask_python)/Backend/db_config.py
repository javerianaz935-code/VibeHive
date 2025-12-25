import mysql.connector

def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # your MySQL password
        database="vibehive"
    )
    return connection

