from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin


class User(UserMixin):

    def __init__(self, id, username, password, fullname="", email_confirmed="") -> None:
        self.id = id
        self.username = username
        self.password = password
        self.fullname = fullname
        self.email_confirmed = email_confirmed

    @classmethod
    def check_password(self, hashed_password, password):
        return check_password_hash(hashed_password, password)
    
    @classmethod
    def generatePasswordHash(self, password):
        print(password)
        return generate_password_hash(password)
    
#print(generate_password_hash("admin123"))
