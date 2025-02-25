from main import app,request



@app.route('/RequestTutor',methods=['GET', 'POST'])
def RequestTutor():
    if request.method == 'POST':
        pass