from flask import Flask,render_template,request,redirect,url_for,session,jsonify
from flaskext.mysql import MySQL
from passlib.hash import sha256_crypt
from datetime import date
import os
from werkzeug import secure_filename


app=Flask(__name__)
app.config['MYSQL_DATABASE_USER'] = 'ahmed'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'sibi_forms'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['UPLOAD_FOLDER']='static/files'


app.secret_key="qwerty"
mysql = MySQL(app)

noti=[]
notiusr=""

@app.route('/check',methods=['POST'])
def check():
    conn=mysql.connect()
    cur=conn.cursor()
    user=request.form['username']
    query='''SELECT * FROM users WHERE username=%s'''
    cur.execute(query,(user))
    data=cur.fetchone()
    if data is None:
        return jsonify({'output':'username available'})
    else:
        return jsonify({'output':'username not available!!'})




@app.route('/authenticate/<formno>',methods=['GET','POST'])
def authenticate(formno):
    conn=mysql.connect()
    cur=conn.cursor()
    msg=None
    if request.method=='POST':
        user=request.form.get('user')
        password=request.form.get('pass')
        q='''SELECT * FROM users WHERE username=%s'''
        cur.execute(q,(user))
        d=cur.fetchone()
        if d is None:
            msg="authentication failed"
        else:
            check=sha256_crypt.verify(password,d[1])
            if check is False:
                msg="authentication failed"
            else:
                return redirect(url_for('responses',formno=formno))
        
    return render_template('authentication.html',msg=msg)

@app.route('/signup',methods=['GET','POST'])
def signup():
    conn=mysql.connect()
    cur=conn.cursor()
    msg=None

    if request.method=='POST':
        password=request.form.get("pass")
        username=request.form.get("user")
        passc=request.form.get("passc")

        cur.execute('''SELECT * FROM users WHERE username=%s''',(username))
        u=cur.fetchone()

        if u is None:
            if passc!=password:
                msg="passwords doesn't match"
            else:
                en_password = sha256_crypt.encrypt(password)
                cur.execute('''INSERT INTO users VALUES (%s,%s)''',(username,en_password))
                conn.commit()
                msg="user created successfully..please login to use"
        else:
            msg="username already taken"
    return render_template('register.html',msg=msg)

@app.route('/',methods=['GET','POST'])
@app.route('/login',methods=['GET','POST'])
def login():
    conn=mysql.connect()
    cur=conn.cursor()
    msg=None

    if request.method=='POST':
        password=request.form.get("pass")
        username=request.form.get("user")
        cur.execute('''SELECT * FROM users WHERE username=%s''',(username))
        data=cur.fetchone()
        check=sha256_crypt.verify(password,data[1])
        if data is None or check is False:
            msg="invalid username or password"
        else: 
            session['user']=username
            return redirect(url_for('home'))    
    return render_template("login.html",msg=msg)

@app.route('/home')
def home():
    conn=mysql.connect()
    cur=conn.cursor()
    msg=None
    q='''SELECT MAX(formno) FROM forms WHERE username=%s'''
    cur.execute(q,session['user'])
    nf=cur.fetchone()
    global noti
    global notiusr
    q='''SELECT DISTINCT formno , title FROM forms WHERE username=%s'''
    cur.execute(q,session['user'])
    data=cur.fetchall()
    if notiusr==session['user']:
        return render_template('home.html',user=session['user'],nf=nf[0],data=data,noti=noti)
    else:
        return render_template('home.html',user=session['user'],nf=nf[0],data=data,noti=None)

        
@app.route('/createform',methods=['GET','POST'])
def createform():
    conn=mysql.connect()
    cur=conn.cursor()
    msg=None
    query='''SELECT MAX(formno) FROM forms WHERE username=%s'''
    cur.execute(query,session['user'])
    data=cur.fetchone()
    if data[0] is None:
        formno=1
    else:
        formno=int(data[0]) + 1

    if request.method=='POST':
        #formno=1
        c=0
        op=0
        j=0
        
        questions=request.form.getlist('ques[]')
        answertype=request.form.getlist('ans[]')
        no_of_options=request.form.getlist('noofop[]')
        options=request.form.getlist('op[]') 
        require=request.form.getlist('req[]')   
        title=request.form.get('title')
        des=request.form.get('des')
        dl=request.form.get('deadline')
        limit=request.form.get('subusr')

        if dl=="":
            dl='9999-12-31'

        if not limit:
            limit=100000

        for i in range(len(questions)):
            
            if answertype[i]=="checkbox" or answertype[i]=="radio":
                n = int(no_of_options[c])
                c=c+1
                for j in range(op,op+n):
                    query='''INSERT INTO forms VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
                    cur.execute(query, 
                                (title,des,formno,questions[i],answertype[i],options[j],require[i],i+1,dl,limit,session['user']))
                    conn.commit()
                
                op=n
                continue
            query='''INSERT INTO forms VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
            cur.execute(query, 
                             (title,des,formno,questions[i],answertype[i],0,require[i],i+1,dl,limit,session['user'])) 
            conn.commit() 
            
        return redirect(url_for('view',formno=formno))             
    return render_template('createform.html')


@app.route('/view/<formno>')
def view(formno):
    conn=mysql.connect()
    cur=conn.cursor()
    msg=None
    user=session['user']
    q='''SELECT * FROM forms WHERE username=%s AND formno=%s'''
    cur.execute(q,(session['user'],formno))
    data=cur.fetchall()
    q2='''SELECT MAX(quesno) FROM forms WHERE username=%s AND formno=%s'''
    cur.execute(q2,(session['user'],formno))
    nq=cur.fetchone()
    return render_template("view.html",data=data,nques=nq[0],user=user,formno=formno)

@app.route('/response/<user>/<formno>',methods=['GET','POST'])
def response(user,formno):
    conn=mysql.connect()
    cur=conn.cursor()
    msg=None
    sub=[0]
    l=[1]
    q='''SELECT * FROM forms WHERE username=%s AND formno=%s'''
    cur.execute(q,(user,formno))
    data=cur.fetchall()
    q2='''SELECT MAX(quesno) FROM forms WHERE username=%s AND formno=%s'''
    cur.execute(q2,(user,formno))
    nq=cur.fetchone()
    q2='''SELECT DISTINCT deadline FROM forms WHERE username=%s AND formno=%s'''
    cur.execute(q2,(user,formno))
    dt=cur.fetchone()
    if date.today() > dt[0]:
        msg="sorry! form is no more available"
    
        
    if request.method=='POST':
        m="new response for form"+str(formno)
        tup=(m,user)
        global noti
        global notiusr
        noti=[]
        notiusr=""
        notiusr=user
        noti.append(m)
        a=1
        query='''SELECT * FROM forms WHERE username=%s AND formno=%s'''
        cur.execute(query,(user,formno))
        data=cur.fetchall()
        query='''SELECT MAX(resno) FROM responses WHERE username=%s AND formno=%s'''
        cur.execute(query,(user,formno))
        rn=cur.fetchone()
        if rn[0] is None:
            cur_rn=1
        else:
            cur_rn=1+int(rn[0])

        query='''SELECT DISTINCT maxsub FROM forms WHERE username=%s AND formno=%s'''
        cur.execute(query,(user,formno))
        l=cur.fetchone()

        email=request.form.getlist('ans1')

        if len(email):
            q='''SELECT COUNT(answer) FROM responses WHERE formno=%s AND username=%s AND 
                                                                    answer=%s AND answertype=%s'''
            cur.execute(q,(formno,user,email[0],'email'))
            sub=cur.fetchone()

        op=0
        if sub is None or sub[0] < l[0]:
            
            query='''INSERT INTO responses VALUES (%s,%s,%s,%s,%s,%s,%s)'''

            for i in range(nq[0]):
                cur_name='ans'+str(i+1)

                k=0
                while data[k][7]!=(i+1):
                    k=k+1 

                if data[i][4]=="image" or data[i][4]=="file":
                    f=request.files[cur_name]
                    if f:
                        filename=secure_filename(f.filename)
                        basedir = os.path.abspath(os.path.dirname(__file__))
                        f.save(os.path.join(basedir,app.config['UPLOAD_FOLDER'],filename))
                        path=os.path.join(basedir,app.config['UPLOAD_FOLDER'],filename)
                        cur.execute(query,(cur_rn,formno,data[i][7],data[i][3],data[i][4],path,user))
                        conn.commit()

                    else:
                        cur.execute(query,(cur_rn,formno,data[i][7],data[i][3],data[i][4],"NA",user))
                        conn.commit()

                    continue

                cur_ans=request.form.getlist(cur_name)
                
                for j in range(len(cur_ans)):
                    if cur_ans[j]:
                        msg="Your Response has been recorded..thank you!"
                        cur.execute(query,(cur_rn,formno,data[k][7],data[k][3],data[k][4],cur_ans[j],user))
                        conn.commit()
                    else:
                        cur.execute(query,(cur_rn,formno,data[k][7],data[k][3],data[k][4],"NA",user))
                        conn.commit()
            
                    
        else:
            msg="you have reached maximum limit for  number of submission"
        
    return render_template("response.html",data=data,nques=nq[0],msg=msg)


@app.route('/responses/<formno>')
def responses(formno):
    conn=mysql.connect()
    cur=conn.cursor()
    msg=None
    cq={}
    rq={}
    query='''SELECT * FROM responses WHERE username=%s AND formno=%s'''
    cur.execute(query,(session['user'],formno))
    data=cur.fetchall()
    query='''SELECT * FROM forms WHERE username=%s AND formno=%s AND answertype=%s '''
    cur.execute(query,(session['user'],formno,'checkbox'))
    checkdata=cur.fetchall()

    if checkdata is None:
        cq=None
    else:
        for d in checkdata:
            key=d[3]
            if key in cq:
                cq[key][d[5]]=0
            else:
                cq[key]={}
                cq[key][d[5]]=0
    
        query='''SELECT * FROM responses WHERE username=%s AND formno=%s AND answertype=%s '''
        cur.execute(query,(session['user'],formno,'checkbox'))
        ans=cur.fetchall()
        for a in ans:
            if a[5] is not None:
                cq[a[3]][a[5]] += 1
    
    query='''SELECT * FROM forms WHERE username=%s AND formno=%s AND answertype=%s '''
    cur.execute(query,(session['user'],formno,'radio'))
    radiodata=cur.fetchall()
    if radiodata is None:
        rq=None
    else:
        for d in radiodata:
            key=d[3]
            if key in rq:
                rq[key][d[5]]=0
            else:
                rq[key]={}
                rq[key][d[5]]=0
    
        query='''SELECT * FROM responses WHERE username=%s AND formno=%s AND answertype=%s '''
        cur.execute(query,(session['user'],formno,'radio'))
        ans=cur.fetchall()
        for a in ans:
            if a[5] is not None:
                rq[a[3]][a[5]] += 1

    return render_template("submissions.html",data=data,formno=formno,cq=cq,rq=rq)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/display',methods=['GET','POST'])
def display():
    if request.method=='POST':
        path=request.form.get('f_path')
        if os.path.isfile(path):
            f=open(path,'r')
            info=f.read()
            f.close()
            
            return render_template("showinfo.html",info=info,path=path)

@app.route('/explore')
def explore():
    conn=mysql.connect()
    cur=conn.cursor()
    msg=None
    i=1
    trend_forms={}

    cur.execute('''SELECT * FROM users''')
    data=cur.fetchall()

    for d in data:
        query='''SELECT MAX(resno) FROM responses WHERE username=%s'''
        cur.execute(query,d[0])
        m=cur.fetchone()
        if m[0] is not None:
            q2='''SELECT DISTINCT formno FROM responses WHERE username=%s AND resno=%s'''
            cur.execute(q2,(d[0],int(m[0])))
            f=cur.fetchone()
            trend_forms[i]=[d[0],str(f[0])]
            i=i+1

    return render_template("explore.html",trend_forms=trend_forms)

@app.route('/expform/<user>/<formno>')
def expform(user,formno):
    conn=mysql.connect()
    cur=conn.cursor()
    msg=None
    q='''SELECT * FROM forms WHERE username=%s AND formno=%s'''
    cur.execute(q,(user,formno))
    data=cur.fetchall()
    q2='''SELECT MAX(quesno) FROM forms WHERE username=%s AND formno=%s'''
    cur.execute(q2,(user,formno))
    nq=cur.fetchone()
    return render_template("view.html",data=data,nques=nq[0],user=user,formno=formno)

@app.route('/contactinfo',methods=['GET','POST'])
def contactinfo():
    conn=mysql.connect()
    cur=conn.cursor()
    
    if request.method=='POST':
        query='''SELECT MAX(formno) FROM forms WHERE username=%s'''
        cur.execute(query,(session['user']))
        f=cur.fetchone()
        dl=request.form.get('deadline')
        limit=request.form.get('subusr')
        title="Contact Information"
        des="Form for collecting contact deatils"

        if dl=="":
            dl='9999-12-31'

        if not limit:
            limit=100000

        if f[0] is None:
            formno=1
        else:
            formno=int(f[0])+1
        
        query='''INSERT INTO forms VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
        cur.execute(query,(title,des,formno,'Name','text',0,'req',1,dl,limit,session['user']))
        conn.commit()
        cur.execute(query,(title,des,formno,'Email','email',0,'req',2,dl,limit,session['user']))
        conn.commit()
        cur.execute(query,(title,des,formno,'Address','text',0,'req',3,dl,limit,session['user']))
        conn.commit()
        cur.execute(query,(title,des,formno,'Phone Number','number',0,'req',4,dl,limit,session['user']))
        conn.commit()
        cur.execute(query,(title,des,formno,'Comments','text',0,'not req',5,dl,limit,session['user']))
        conn.commit()
        return redirect(url_for('view',formno=formno)) 
        
    return render_template('contactinfo.html')


@app.route('/tshirt',methods=['GET','POST'])
def tshirt():
    conn=mysql.connect()
    cur=conn.cursor()
    
    if request.method=='POST':
        query='''SELECT MAX(formno) FROM forms WHERE username=%s'''
        cur.execute(query,(session['user']))
        f=cur.fetchone()
        dl=request.form.get('deadline')
        limit=request.form.get('subusr')
        title="Contact Information"
        des="Form for collecting contact deatils"

        if dl=="":
            dl='9999-12-31'

        if not limit:
            limit=100000

        if f[0] is None:
            formno=1
        else:
            formno=int(f[0])+1
        
        query='''INSERT INTO forms VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
        cur.execute(query,(title,des,formno,'Name','text',0,'req',1,dl,limit,session['user']))
        conn.commit()
        cur.execute(query,(title,des,formno,'Email','email',0,'req',2,dl,limit,session['user']))
        conn.commit()
        cur.execute(query,(title,des,formno,'t-shirt size','radio','s','not req',3,dl,limit,session['user']))
        conn.commit()
        cur.execute(query,(title,des,formno,'t-shirt size','radio','m','not req',3,dl,limit,session['user']))
        conn.commit()
        cur.execute(query,(title,des,formno,'t-shirt size','radio','l','not req',3,dl,limit,session['user']))
        conn.commit()
        cur.execute(query,(title,des,formno,'comments','text',0,'req',4,dl,limit,session['user']))
        conn.commit()
        return redirect(url_for('view',formno=formno)) 
        
    return render_template('tshirt.html')




