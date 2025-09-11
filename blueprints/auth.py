from flask import Blueprint, render_template, request, redirect, url_for,current_app
from flask_login import UserMixin, login_user, login_required, logout_user
from extensions import mysql, bcrypt,mail
from flask_login import current_user
from flask import flash
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message

class User(UserMixin):
    def __init__(self, id, username, email,year):
        self.id = id
        self.username = username
        self.email = email
        self.year = year 

auth = Blueprint('auth', __name__)
def get_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

@auth.route("/confirm/<token>")
def confirm_email(token):
    serializer = get_serializer()
    try:
        email = serializer.loads(token, salt="email-confirm", max_age=3600)
    except:
        return "The confirmation link is invalid or has expired.", 400
    
    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET verified=TRUE WHERE email=%s", (email,))
    mysql.connection.commit()
    cur.close()
    
    flash("Your account has been verified!")
    return redirect(url_for("auth.login"))


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
            if not user[5]:  
                flash("Please verify your email before logging in.")
                return redirect(url_for("auth.login"))
            user_obj = User(id=user[0], username=user[1], email=user[3], year=user[4])
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
        ALLOWED_DOMAIN = "@gmail.com"

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

        serializer = get_serializer()
        token = serializer.dumps(email, salt="email-confirm")
        confirm_url = url_for("auth.confirm_email", token=token, _external=True)
    
        msg = Message("Confirm Your Email", recipients=[email],sender = current_app.config['MAIL_USERNAME'])
        msg.body = f"Click the link to confirm your email: {confirm_url}"
        mail.send(msg)
    
        flash("Check your email to confirm your account.")

        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO users (username, password_hash,email,year,verified) VALUES (%s, %s,%s,%s,%s)", (username, hashed_password,email,year,False))
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
