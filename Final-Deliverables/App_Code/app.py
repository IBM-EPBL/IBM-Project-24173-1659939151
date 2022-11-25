from flask import Flask, render_template, redirect, url_for, session
from flask_session import Session
import ibm_db
import json
from flask import request

app = Flask(__name__, static_folder="static")
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=b1bc1829-6f45-4cd4-bef4-10cf081900bf.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=32304;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=frb18707;PWD=GhfEkngvfCdiA9Y9",'','')
print("duc")

@app.route('/')    
def base():
    return render_template('login.html')


@app.route('/redirect/<page>',methods=['GET'])
def redirect(page):
    if(page == 'login'):
        session["msg"] = "Logout"
        return render_template("login.html",msg='success')
    else:
        return render_template(page+".html")


def updatenotification():
    stmt = ibm_db.exec_immediate(conn, "Select * from notification from where to_user = '"+session["email"]+"' and status='Pending' ;")
    result = ibm_db.fetch_assoc(stmt)
    data = []
    while result != False: 
        data.append([result["NOTIFICATIONID"],result["FROM_USER"],result["TO_USER"],result["BODY"],result["MESSAGE"],result["STATUS"]])
        result = ibm_db.fetch_assoc(stmt)
    session["notification"] = data

@app.route('/login',methods=['POST'])
def login():
    if request.method == 'POST':
        global conn
        username = request.form.get('email')
        password = request.form.get('password')
        stmt = ibm_db.exec_immediate(
            conn, "Select * from login where email = '"+username+"' and password = '"+password+"' ")
        result = ibm_db.fetch_assoc(stmt)
        if (result):
            session["name"] = result["NAME"]
            session["password"] = result["PASSWORD"]
            session["bloodgroup"] = result["BLOODGROUP"]
            session["phonenumber"] = result["PHONENUMBER"]
            session["email"] = result["EMAIL"]
            session["address"] = result["ADDRESS"]
            session["msg"] = "Login"
            updaterequests()
            updatenotification()
            return render_template('home page.html', msg='success')
        else:
            session["msg"] = "Login"
            return render_template('login.html', msg='error')
    else:
        return render_template('login.html')


@app.route('/signup',methods=['POST','GET'])
def signup():
    if request.method == 'POST':
        global conn
        name = request.form['name']
        password = request.form['password']
        email =  request.form['email']
        bloodgroup = request.form['bloodgroup']
        phonenumber = request.form['phno']
        address = request.form['address']
        city = request.form['city']
        stmt = ibm_db.exec_immediate(conn,"insert into  login (name,password,email,bloodgroup,phonenumber,address,city) values ('"+name+"','"+password+"','"+email+"','"+bloodgroup+"',"+phonenumber+",'"+address+"','"+city+"');")
        if (ibm_db.num_rows(stmt) > 0):
                session["msg"] = "aign up completed"
                return render_template('login.html',msg='success')
        else:
            session["msg"] = "email already exist"
            return render_template('signup.html',msg='error')
    else:
        return render_template('signup.html') 
        

def updaterequests():
    stmt = ibm_db.exec_immediate(conn, "Select * from requests from where status='Pending' order by requestdate desc;")
    result = ibm_db.fetch_assoc(stmt)
    data = []
    while result != False: 
        data.append([result["REQUESTID"],result["REQUESTER"],result["EMAIL"],result["PHONENUMBER"],result["BLOODGROUP"],result["CITY"],result["STATUS"]])
        result = ibm_db.fetch_assoc(stmt)
    session["requests"] = data

@app.route('/donation/<id>',methods=['GET'])
def makedonation(id):
    stmt = ibm_db.exec_immediate(conn, "Select * from requests where requestid = "+id+";")
    result = ibm_db.fetch_assoc(stmt)
    if(result):
        session["requestor"] = result["REQUESTER"]
        return render_template("details.html",email=result["EMAIL"],name=result["REQUESTER"],bloodgroup=result["BLOODGROUP"],requestdate=result["REQUESTDATE"])

@app.route('/accept/<id>',methods=['GET'])
def accept(id):
    stmt = ibm_db.exec_immediate(conn, "Select * from notification where notificationid = "+id+";")
    result = ibm_db.fetch_assoc(stmt)
    if(result):
        stmt = ibm_db.exec_immediate(conn, "update notification set status='Accepted' where notificationid = "+id+";")
        if (ibm_db.num_rows(stmt) > 0):
            return render_template("contact.html",from_user=result["FROM_USER"],to_user=result["TO_USER"])


@app.route('/decline/<id>',methods=['GET'])
def decline(id):
    stmt = ibm_db.exec_immediate(conn, "update notification set status='Declined' where notificationid = "+id+";")
    if (ibm_db.num_rows(stmt) > 0):
        updatenotification()
        session["msg"] = "notification declined"
        return render_template("home page.html",msg='error')

@app.route('/donate/<email>',methods=['GET'])
def notification(email):
        requestor = email
        donar = session["email"]
        message = "A person sent notification for donation"
        stmt = ibm_db.exec_immediate(conn,"insert into  notification (from_user,to_user,body,message) values ('"+donar+"','"+requestor+"','Blood request reviewed','"+message+"');")
        if (ibm_db.num_rows(stmt) > 0):
                updatenotification()
                session["msg"] = "User notified"
                return render_template('home page.html',msg='success')
        else:
            session["msg"] = "notify user"
            return render_template('home page.html',msg='error')

@app.route('/request',methods=['POST'])
def makerequest():
    if request.method == 'POST':
        global conn
        name = session["name"]
        email =  session["email"]
        bloodgroup = request.form["bloodgroup"]
        phonenumber = str(session["phonenumber"])
        city = request.form["city"]
        print(phonenumber)
        print(name)
        print(email)
        print(bloodgroup)
        print(city)
        stmt = ibm_db.exec_immediate(conn,"insert into  requests (requester,email,bloodgroup,phonenumber,city) values ('"+name+"','"+email+"','"+bloodgroup+"','"+phonenumber+"','"+city+"');")
        updaterequests()
        if (ibm_db.num_rows(stmt) > 0):
                session["msg"] = "request posted"
                return render_template('home page.html',msg='success')
        else:
            session["msg"] = "error posting request"
            return render_template('home page.html',msg='error')
    else:
        session["msg"] = "error posting request"
        return render_template('home page.html',msg='error') 

    

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)

