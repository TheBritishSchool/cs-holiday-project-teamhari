from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

mysql = MySQL()
bcrypt = Bcrypt()
login_manager = LoginManager()