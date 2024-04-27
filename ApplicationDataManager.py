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
        # Convert the list of tuples to a list of dictionaries
        output = []
        for row in rows:
            output.append({
                'id': row[0],
                'firstname': row[1],
                'lastname': row[2],
                'email': row[3],
                'phone': row[4],
                'address': row[5],
                'expected_salary': row[6],
                'create_date': row[7],
                'resume': row[8]
            })
        return output

    def insert(self, application):
        self.connection = sqlite3.connect(os.getenv('DB_PATH') or 'db.sqlite3')
        cursor = self.connection.cursor()
        application['create_date'] = 'now'
        application['resume'] = '' # TODO: make it later
        application = (application['firstname'], application['lastname'], application['email'], application['phone'], application['address'], application['expected_salary'], application['create_date'], application['resume'])
        cursor.execute("INSERT INTO applications (firstname, lastname, email, phone, address, expected_salary, create_date, resume) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", application)
        self.connection.commit()
        return cursor.lastrowid

    def update(self, application):
        self.connection = sqlite3.connect(os.getenv('DB_PATH') or 'db.sqlite3')
        cursor = self.connection.cursor()
        application = (application['firstname'], application['lastname'], application['email'], application['phone'], application['address'], application['expected_salary'], application['resume'], application['id'])
        cursor.execute("UPDATE applications SET firstname=?, lastname=?, email=?, phone=?, address=?, expected_salary=?, resume=? WHERE id=?", application)
        self.connection.commit()
        return cursor.lastrowid

    def delete(self, id):
        self.connection = sqlite3.connect(os.getenv('DB_PATH') or 'db.sqlite3')
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM applications WHERE id=?", (id,))
        self.connection.commit()
        return cursor.lastrowid

    def exportCSV(self):
        import pandas as pd
        from datetime import datetime

        self.connection = sqlite3.connect(os.getenv('DB_PATH') or 'db.sqlite3')
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM applications")
        rows = cursor.fetchall()
        # write it using pandas
        df = pd.DataFrame(rows, columns=['id', 'firstname', 'lastname', 'email', 'phone', 'address', 'expected_salary', 'create_date', 'resume'])
        file_name = 'export-' + str(datetime.now()) + '.csv'
        df.to_csv(file_name, index=False)
        return file_name
