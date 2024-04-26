import os
import sqlite3


class ApplicationDataManager:
    # Singleton design pattern
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ApplicationDataManager, cls).__new__(cls)
        return cls._instance

    connection = None # get from the sql.connect() method
    def __init__(self, connection):
        self.connection = connection

    def getCollection(self):
        # sqlite is one-threaded, so we can use the same connection
        self.connection = sqlite3.connect(os.getenv('DB_PATH') or 'db.sqlite3')
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM applications")
        rows = cursor.fetchall()
        return rows

    def insert(self, application):
        self.connection = sqlite3.connect(os.getenv('DB_PATH') or 'db.sqlite3')
        cursor = self.connection.cursor()
        application['create_date'] = 'now'
        application = (application['firstname'], application['lastname'], application['email'], application['phone'], application['address'], application['expected_salary'], application['create_date'], application['resume'])
        cursor.execute("INSERT INTO applications (firstname, lastname, email, phone, address, expected_salary, create_date, resume) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", application)
        self.connection.commit()
        return cursor.lastrowid
