from flask import Flask, request, render_template, redirect, url_for
from extensions import mysql, bcrypt, login_manager,mail
from blueprints.auth import auth
from blueprints.requests import requests_bp
from flask_login import login_required, current_user
from flask_mail import Mail, Message
from flask_login import UserMixin
import os
from werkzeug.utils import secure_filename
from flask import flash
from dotenv import load_dotenv
load_dotenv()
import cloudinary
import cloudinary.uploader

cloudinary.config( 
  cloud_name = os.getenv('CLOUDINARY_URL').split('@')[-1], 
  api_key = os.getenv('CLOUDINARY_URL').split('//')[1].split(':')[0],
  api_secret = os.getenv('CLOUDINARY_URL').split(':')[2].split('@')[0]
)

# Database credentials
HOST = os.environ.get("MYSQL_HOST")
USER = os.environ.get("MYSQL_USER")
PASSWORD = os.environ.get("MYSQL_PASSWORD")
DATABASE = os.environ.get("MYSQL_DATABASE")
PORT = os.environ.get("MYSQL_PORT")
UPLOAD_FOLDER = 'static/uploads'

app = Flask(__name__)

# Secret key for session management
app.secret_key = app.secret_key = os.environ.get("SECRET_KEY", "fallback_secret_for_local")


# Database configuration
app.config['MYSQL_HOST'] = HOST
app.config['MYSQL_USER'] = USER
app.config['MYSQL_PASSWORD'] = PASSWORD
app.config['MYSQL_DB'] = DATABASE
app.config['MYSQL_PORT'] = PORT

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False  
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")   
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")     

mail.init_app(app)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize extensions
mysql.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"

# Register blueprints
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(requests_bp, url_prefix='/requests')

class User(UserMixin):
    def __init__(self, id, username, email,year):
        self.id = id
        self.username = username
        self.email = email
        self.year = year 

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()                                 

    if user:
        return User(id=user[0], username=user[1],email=user[3],year = user[4])
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
    cur.execute('SELECT COUNT(*) FROM Requesthelp')
    total_requests = cur.fetchone()[0]
    
    # Get the help requests for the current page
    cur.execute('''
    SELECT r.id, r.subject, r.description, r.created_at, u.username,r.image_path 
    FROM Requesthelp r 
    JOIN users u ON r.user_id = u.id
    ORDER BY r.created_at DESC
    LIMIT %s OFFSET %s
    ''', (per_page, offset))
    requests = cur.fetchall()
    
    request_ids = [req[0] for req in requests]
    if request_ids:  # check if list is not empty
        format_strings = ','.join(['%s'] * len(request_ids))
        cur.execute(f'''
            SELECT re.request_id, re.message, re.created_at, u.username
            FROM Replies re
            JOIN users u ON re.user_id = u.id
            WHERE re.request_id IN ({format_strings})
            ORDER BY re.created_at ASC
        ''', tuple(request_ids))
        all_replies = cur.fetchall()
    else:
        all_replies = []
    
    replies_dict = {}
    for reply in all_replies:
        req_id = reply[0]
        if req_id not in replies_dict:
            replies_dict[req_id] = []
        replies_dict[req_id].append(reply)

    requests_with_replies = []
    for req in requests:
        req_id = req[0]
        requests_with_replies.append({
            "id": req[0],
            "subject": req[1],
            "description": req[2],
            "created_at": req[3],
            "username": req[4],
            "image_path": req[5],
            "replies": replies_dict.get(req_id, [])  # get all replies for this request
    })
    
    

    cur.close()
    
   
    total_pages = (total_requests + per_page - 1) // per_page
    
    return render_template('home.html', username=current_user.username, requests=requests_with_replies, page=page, total_pages=total_pages)

# Function to initialize database tables
def init_db():
    print(f"Connecting to MySQL at {app.config['MYSQL_HOST']}:{app.config['MYSQL_PORT']} with user {app.config['MYSQL_USER']}")
    cur = mysql.connection.cursor()

    # Create users table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL
    )
    ''')

    # Create Requesthelp table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS Requesthelp (
        id INT AUTO_INCREMENT PRIMARY KEY,
        subject VARCHAR(100) NOT NULL,
        description TEXT NOT NULL,
        user_id INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS Replies (
        id INT AUTO_INCREMENT PRIMARY KEY, 
        user_id INT, 
        request_id INT, 
        message TEXT NOT NULL, 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (request_id) REFERENCES Requesthelp(id)
        
    )
    ''')
    
    cur.execute('''
    CREATE TABLE IF NOT EXISTS Tutorprofiles(
        user_id INT, 
        username varchar(50), 
        bio MEDIUMTEXT, 
        email varchar(100), 
        subjects TEXT, 
        userimage_path TEXT, 
        timing TEXT, 
        FOREIGN KEY (user_id) REFERENCES users(id)
    )       
    ''')

    mysql.connection.commit()
    cur.close()

    
@app.route("/replies/<int:request_id>",methods = ["POST"])
@login_required
def reply_request(request_id):
    message = request.form["message"]
    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO Replies (user_id,request_id,message) VALUES (%s,%s,%s)",(current_user.id,request_id,message) 
    )
    mysql.connection.commit()
    flash("Successfuly posted reply!")

    cur.execute('''
        SELECT u.email, u.username
        FROM Requesthelp r
        JOIN users u on r.user_id = u.id
        where r.id = (%s)
    ''',(request_id,))
    creator = cur.fetchone()
    cur.close()

    if creator:
        recipient_email = creator[0]
        recipient_username = creator[1]
        if recipient_email and recipient_email != current_user.email: 
            try: 
                from app import mail
                msg = Message(
                    subject = "New reply to your request on the TBS forum",
                    sender = app.config['MAIL_USERNAME'],
                    recipients = [recipient_email]
                )
                msg.body = f"Hi {recipient_username},\n\n{current_user.username} replied to your request:\n\n\"{message}\"\n\nOpen the site to reply."
                mail.send(msg)
            except Exception as e:
                print("Warning: failed to send email notification:", e)
    
    return redirect(url_for('home'))

@app.route("/tutor")
@login_required
def tutor(): 
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Tutorprofiles WHERE user_id = %s ",(current_user.id,))
    profile = cur.fetchone()
    cur.close()
    if profile: 
        return render_template("Tutorprofile.html",profile = profile)

    else : 
        return render_template("applytutor.html")
    
@app.route("/applytutor",methods  = ["POST"])
@login_required
def applytutor():
    bio = request.form["BIO"]
    subjects = request.form["subjects"]
    timing = request.form["timings"]
    image = request.files.get('image')
    image_filename = None
    if image and image.filename != "":
        upload_result = cloudinary.uploader.upload(image)
        image_url = upload_result['secure_url']
    
    if current_user.year < 10 or current_user.year > 13:
        flash("Only students in Years 10 to 13 can apply to be a tutor.", "error")
        return redirect(url_for("tutor"))
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO Tutorprofiles(user_id,username,bio,email,subjects,userimage_path,timing)  VALUES(%s,%s,%s,%s,%s,%s,%s)",
                 (current_user.id,current_user.username,bio,current_user.email,subjects,image_url,timing))
    mysql.connection.commit()
    cur.close()
    flash("Successfully made profile!")
    return redirect(url_for("tutor"))

@app.route("/tutorprofiles")
@login_required
def tutorprofiles(): 
    cur=mysql.connection.cursor()
    cur.execute("SELECT * FROM Tutorprofiles")
    tutors = cur.fetchall()
    cur.close()
    return render_template("tutordashboard.html",tutors=tutors)

@app.route("/editprofile", methods=["GET","POST"])
@login_required
def editprofile():
    cur = mysql.connection.cursor()

    
    cur.execute("SELECT * FROM Tutorprofiles WHERE user_id=%s", (current_user.id,))
    profile = cur.fetchone()

    if request.method == "POST":
        bio = request.form.get("BIO", profile[2])  
        subjects = request.form.get("subjects", profile[4])
        timing = request.form.get("timings", profile[6]) 
        image = request.files.get("image")
        image_filename = profile[5]  

        if image and image.filename != "":
            upload_result = cloudinary.uploader.upload(image)
            image_url = upload_result['secure_url']
        else: 
            flash("invalid file")
            return redirect("editprofile")

        cur.execute("""
            UPDATE Tutorprofiles
            SET bio=%s, subjects=%s, userimage_path=%s, timing=%s
            WHERE user_id=%s
        """, (bio, subjects, image_url, timing, current_user.id))
        mysql.connection.commit()

        cur.execute("SELECT * FROM Tutorprofiles WHERE user_id=%s", (current_user.id,))
        profile = cur.fetchone()
        flash("Saved changes")
        return redirect(url_for("tutor"))

    cur.close()
    return render_template("editprofile.html", profile=profile)

# Run the Flask app
if __name__ == '__main__':
    with app.app_context():
        init_db()  # Initialize database on startup
    app.run(debug=True)


