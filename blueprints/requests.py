from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from extensions import mysql
import os
from werkzeug.utils import secure_filename
from flask import current_app

#file path and validation

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


requests_bp = Blueprint('requests_bp', __name__)

@requests_bp.route('/RequestTutor', methods=['GET', 'POST'])
@login_required
def RequestTutor():
    if request.method == 'POST':
        subject = request.form['subject']
        description = request.form['description']
        file = request.files['image']
        image_filename = None
        if file and allowed_file(file.filename): 
            image_filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'],image_filename))

        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO TutorRequests (subject, description, user_id,image_path) VALUES (%s, %s, %s,%s)",
                        (subject, description, current_user.id,image_filename))
            mysql.connection.commit()
            return redirect(url_for('main.home'))
        except Exception as e:
            return render_template('RequestTutor.html', error=f"Request failed: {str(e)}")
        finally:
            cur.close()

    return render_template('RequestTutor.html')