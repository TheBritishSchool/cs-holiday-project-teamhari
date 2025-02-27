from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from extensions import mysql

requests_bp = Blueprint('requests_bp', __name__)

@requests_bp.route('/RequestTutor', methods=['GET', 'POST'])
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
            return redirect(url_for('main.home'))
        except Exception as e:
            return render_template('RequestTutor.html', error=f"Request failed: {str(e)}")
        finally:
            cur.close()

    return render_template('RequestTutor.html')