from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import UserMixin, login_user, login_required, logout_user
from extensions import mysql, bcrypt
from flask_login import current_user
from flask import flash


auth = Blueprint('auth', __name__)

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: 
        return redirect(url_for('home'))
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
            flash("Succesfully logged in!")
            return redirect(url_for('home'))
        else:
            flash("invalid username or password")
            return redirect(url_for("auth.login"))

    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm_password']
        year = request.form['year']
        ALLOWED_DOMAIN = "@tbs.edu.np"

        email = request.form.get("email")

        if not email.endswith(ALLOWED_DOMAIN):
            flash("Registration is only allowed with TBS school emails.", "error")
            return redirect(url_for("auth.register"))

        if password != confirm:
            flash("Passwords do not match")
            return redirect(url_for("auth.register"))
        
        if len(password) < 8 or not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password):
            flash("Password must be at least 8 characters long and include both letters and numbers")
            return redirect(url_for("auth.register"))
       
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO users (username, password_hash,email,year) VALUES (%s, %s,%s,%s)", (username, hashed_password,email,year))
            mysql.connection.commit()
            flash("Succesfully registered!")
            return redirect(url_for('auth.login'))
        except Exception as e:
            return render_template('register.html', error=f"Registration failed: {str(e)}")
        finally:
            cur.close()

    return render_template('register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
