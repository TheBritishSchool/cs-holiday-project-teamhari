from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import UserMixin, login_user, login_required, logout_user
from extensions import mysql, bcrypt

auth = Blueprint('auth', __name__)

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@auth.route('/login', methods=['GET', 'POST'])
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
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed_password))
            mysql.connection.commit()
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
