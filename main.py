from flask import Flask, render_template, request, redirect, url_for #the main flask library with basic flask functions
from flask_mysqldb import MySQL #connection with the database thingy for password and username
from flask_bcrypt import Bcrypt #used for encryption of password
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user #manages variou user login related things that i dont want to explain
from config import Config #keeps secret stuff in a seperate folder so that no one will see it

app = Flask(__name__)
app.config.from_object(Config)

#defining references to the database, encryption and login manager
mysql = MySQL(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# User class for Login
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    #mysql.connection → Connects to MySQL database and .cursor() Creates a cursor object (cur) that llows us to Execute SQL queries (SELECT, INSERT, etc) and Fetch data from the database.
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone() #fetches 1 row of data where userid matches
    cur.close()
    if user:
        return User(id=user[0], username=user[1]) #returns the user data
    return None #if no user is found

@app.route('/') #home page
def index():
    return redirect(url_for('login')) #redirects to login page

@app.route('/login', methods=['GET', 'POST']) #get and post methods for login that is used to get and post data
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.check_password_hash(user[2], password):
            user_obj = User(id=user[0], username=user[1])
            login_user(user_obj)
            return redirect(url_for('home'))
        else:
            return render_template('login.html')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed_password))
        mysql.connection.commit()
        cur.close()
        

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/home')
@login_required
def home():
    return render_template('home.html', username=current_user.username)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
