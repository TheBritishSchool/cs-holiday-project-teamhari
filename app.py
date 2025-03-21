from flask import Flask, request, render_template, redirect, url_for
from extensions import mysql, bcrypt, login_manager
from blueprints.auth import auth, User
from blueprints.requests import requests_bp
from flask_login import login_required, current_user

# Database credentials
HOST = 'bkfanudhuvqg1xriyhdm-mysql.services.clever-cloud.com'
USER = 'uraexz57rm9ktsv8'
PASSWORD = 'XXeJ8prWdlq5SfsiFxwy'
DATABASE = 'bkfanudhuvqg1xriyhdm'
PORT = 3306

app = Flask(__name__)

# Secret key for session management
app.secret_key = 'supersecretkey'

# Database configuration
app.config['MYSQL_HOST'] = HOST
app.config['MYSQL_USER'] = USER
app.config['MYSQL_PASSWORD'] = PASSWORD
app.config['MYSQL_DB'] = DATABASE
app.config['MYSQL_PORT'] = PORT

# Initialize extensions
mysql.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"

# Register blueprints
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(requests_bp, url_prefix='/requests')

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
    return redirect(url_for('auth.login'))

@app.route('/home')
@login_required
def home():
    # Get the current page number, default to 1 if not specified
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of requests per page
    offset = (page - 1) * per_page
    
    # Get the total number of tutor requests
    cur = mysql.connection.cursor()
    cur.execute('SELECT COUNT(*) FROM TutorRequests')
    total_requests = cur.fetchone()[0]
    
    # Get the tutor requests for the current page
    cur.execute('''
    SELECT r.id, r.subject, r.description, r.created_at, u.username 
    FROM TutorRequests r 
    JOIN users u ON r.user_id = u.id
    ORDER BY r.created_at DESC
    LIMIT %s OFFSET %s
    ''', (per_page, offset))
    requests = cur.fetchall()
    cur.close()
    
    # Calculate the total number of pages
    total_pages = (total_requests + per_page - 1) // per_page
    
    return render_template('home.html', username=current_user.username, requests=requests, page=page, total_pages=total_pages)

# Function to initialize database tables
def init_db():
    print(f"Connecting to MySQL at {app.config['MYSQL_HOST']}:{app.config['MYSQL_PORT']} with user {app.config['MYSQL_USER']}")
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

# Run the Flask app
if __name__ == '__main__':
    with app.app_context():
        init_db()  # Initialize database on startup
    app.run(debug=True)
