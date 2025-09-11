from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from extensions import mysql
import os
from werkzeug.utils import secure_filename
from flask import current_app
from flask import flash
import cloudinary

#file path and validation

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


requests_bp = Blueprint('requests_bp', __name__)

@requests_bp.route('/Requesthelp', methods=['GET', 'POST'])
@login_required
def Requesthelp():
    if request.method == 'POST':
        subject = request.form['subject']
        description = request.form['description']
        file = request.files['image']
        image_url = None

        if file and allowed_file(file.filename): 
            upload_result = cloudinary.uploader.upload(file)
            image_url = upload_result['secure_url']

        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO Requesthelp (subject, description, user_id,image_path) VALUES (%s, %s, %s,%s)",
                        (subject, description, current_user.id,image_url))
            mysql.connection.commit()
            flash("Succesfully posted request!")
            return redirect(url_for('main.home'))
        except Exception as e:
            return render_template('Requesthelp.html', error=f"Request failed: {str(e)}")
        finally:
            cur.close()

    return render_template('Requesthelp.html')