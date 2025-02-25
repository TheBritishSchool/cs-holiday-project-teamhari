from main import app,request,mysql, redirect, url_for, render_template



@app.route('/RequestTutor',methods=['GET', 'POST'])
def RequestTutor():
    if request.method == 'POST':
        subject = request.form['subject']
        description = request.form['description']
        cur = mysql.connection.cursor() 
        cur.execute("INSERT INTO TutorReqests (subject, description) VALUES (%s, %s)", (subject, description))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('RequestTutor'))

    return render_template('RequestTutor.html')