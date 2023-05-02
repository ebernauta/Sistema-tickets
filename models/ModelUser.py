from .entities.User import User


class ModelUser():

    @classmethod
    def login(self, db, user):
        try:
            cursor = db.connection.cursor()
            sql = """SELECT id, username, password, fullname, email_confirmed FROM user 
                    WHERE username = '{}'""".format(user.username)
            cursor.execute(sql)
            row = cursor.fetchone()
            if row[2] is None:
                user = User(row[0], row[1], user.password, row[3], row[4])
                return user
            elif row != None:
                user = User(row[0], row[1], User.check_password(row[2], user.password), row[3], row[4])
                return user
            else:
                return None
        except Exception as ex:
            print(ex)

    @classmethod
    def get_by_id(self, db, id):
        try:
            cursor = db.connection.cursor()
            sql = "SELECT id, username, fullname FROM user WHERE id = {}".format(id)
            cursor.execute(sql)
            row = cursor.fetchone()
            if row != None:
                return User(row[0], row[1], None, row[2])
            else:
                return None
        except Exception as ex:
            raise Exception(ex)
    
    @classmethod
    def allUsers(self, db):
        try:
            cursor = db.connection.cursor()
            sql = "SELECT * FROM user"
            cursor.execute(sql)
            rows = cursor.fetchall()
            return rows
        except Exception as ex:
            raise Exception(ex)
        
    
    @classmethod
    def newUser(self, db, rut):
        try:
            cursor = db.connection.cursor()
            sql = """INSERT INTO user (id, username) 
                            VALUES (null,'{}')""".format(rut)
            cursor.execute(sql)
        except Exception as ex:
            raise Exception(ex)
    
    @classmethod
    def editUser(self, db, username, email, fullname, id_data):
        try:
            cursor = db.connection.cursor()
            sql = """ UPDATE user SET username='{}', email='{}', fullname='{}'
                    WHERE id='{}'""".format(username, email, fullname, id_data)
            cursor.execute(sql)
        except Exception as ex:
            raise Exception(ex)
