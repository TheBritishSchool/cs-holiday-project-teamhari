from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# defining references to the database, encryption and login manager
mysql = MySQL(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Function to initialize database tables
def init_db():
    cur = mysql.connection.cursor()
    
    # Create users table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL
    )
    ''')
    
    # Create TutorRequests table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS TutorRequests (
        id INT AUTO_INCREMENT PRIMARY KEY,
        subject VARCHAR(100) NOT NULL,
        description TEXT NOT NULL,
        user_id INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    mysql.connection.commit()
    cur.close()

# User class for Login
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    if user:
        return User(id=user[0], username=user[1])
    return None

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed_password))
            mysql.connection.commit()
            return redirect(url_for('login'))
        except Exception as e:
            return render_template('register.html', error=f"Registration failed: {str(e)}")
        finally:
            cur.close()

    return render_template('register.html')

@app.route('/RequestTutor', methods=['GET', 'POST'])
@login_required
def RequestTutor():
    if request.method == 'POST':
        subject = request.form['subject']
        description = request.form['description']
        
        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO TutorRequests (subject, description, user_id) VALUES (%s, %s, %s)", 
                       (subject, description, current_user.id))
            mysql.connection.commit()
            return redirect(url_for('home'))
        except Exception as e:
            return render_template('RequestTutor.html', error=f"Request failed: {str(e)}")
        finally:
            cur.close()

    return render_template('RequestTutor.html')

@app.route('/home')
@login_required
def home():
    # Get all tutor requests
    cur = mysql.connection.cursor()
    cur.execute('''
    SELECT r.id, r.subject, r.description, r.created_at, u.username 
    FROM TutorRequests r 
    JOIN users u ON r.user_id = u.id
    ORDER BY r.created_at DESC
    ''')
    requests = cur.fetchall()
    cur.close()
    
    return render_template('home.html', username=current_user.username, requests=requests)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Run the Flask app
if __name__ == '__main__':
    with app.app_context():
        init_db()  # Initialize database on startup
    app.run(debug=True)