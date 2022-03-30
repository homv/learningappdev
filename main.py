from flask import Flask, redirect
from flask import render_template
from flask import request
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import datetime as dt
import matplotlib.pyplot as plt
import timeago

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config["CACHE_TYPE"] = "null"
app.config['SECRET_KEY'] = 'olola'
db = SQLAlchemy()
bcrypt = Bcrypt(app)
db.init_app(app)
app.app_context().push()

class user(db.Model):
    __tablename__ = 'user'
    uid = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    trackers = db.relationship('tracker',backref='user',cascade="all,delete")
    logger = db.relationship('logging',backref='user',cascade="all,delete")
    def __init__(self,uname,passw):
        self.username = uname
        self.password = passw

class tracker(db.Model):
    __tablename__ = 'tracker'
    tid = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    ttype = db.Column(db.Text, nullable=False)
    settings = db.Column(db.Text, nullable=True)
    uid = db.Column(db.Integer,  db.ForeignKey("user.uid"), nullable=False)
    logger = db.relationship('logging' ,backref='tracker',cascade="all,delete")
    def __init__(self,name,description,ttype,setting,uid):
        self.name = name
        self.description = description
        self.ttype = ttype
        self.settings = setting
        self.uid = uid
    
class logging(db.Model):
    __tablename__ = 'logging'
    lid = db.Column(db.Integer, autoincrement=True, primary_key=True)
    tid = db.Column(db.Integer,  db.ForeignKey("tracker.tid"), nullable=False)
    uid = db.Column(db.Integer,  db.ForeignKey("user.uid"), nullable=False)
    value = db.Column(db.Text, nullable=False)
    note = db.Column(db.Text, nullable=True)
    logtime = db.Column(db.Text, nullable = False)
    datetime = db.Column(db.Text, nullable=False)
    def __init__(self,tid,uid,value,note,logtime,datetime):
        self.tid = tid
        self.uid = uid
        self.value = value
        self.note = note
        self.logtime = logtime
        self.datetime = datetime

@app.route('/logout',methods=['GET', 'POST'])
def logout(): 
    return redirect('/')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method=="GET":
        return render_template("login.html")
    if request.method =="POST":
        u = user.query.filter_by(username = request.form["uname"]).first()
        if(u):
            if bcrypt.check_password_hash(u.password,request.form["passw"]):
                return redirect("{}/dashboard".format(u.username))
            else:
                error = "Invalid password"
        else:
            error = "User does not exist"
    return render_template("login.html",error = error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method=="GET":
        return render_template("register.html")
    if request.method =="POST":
        u = user.query.filter_by(username = request.form["uname"]).first()
        if(u):
            error = "User exists. Please Login"
        else:
            hpass = bcrypt.generate_password_hash(request.form["passw"])
            u = user(request.form["uname"],hpass)
            db.session.add(u)
            db.session.commit()
            return redirect("{}/dashboard".format(request.form["uname"]))
    return render_template("register.html",error = error)


@app.route('/delete', methods=['GET', 'POST'])
def delete():
    if request.method=="GET":
        return render_template("delete.html")
    if request.method =="POST":
        u = user.query.filter_by(username = request.form["uname"]).first()
        if(u):
            if bcrypt.check_password_hash(u.password,request.form["passw"]):
                db.session.delete(u)
                db.session.commit()
                return redirect("/")
            else:
                error = "Wrong Password"
                return render_template("delete.html",error = error)    
        else:
            error = "User Does Not Exist"
            return render_template("delete.html",error = error)    


@app.route('/<username>/dashboard',methods=['GET', 'POST'])
def dashboard(username):
    if request.method=="GET":
        u = user.query.filter_by(username = username).first()
        tu = tracker.query.filter_by(uid = u.uid).all()
        k = []
        for i in tu:
            tuu = tracker.query.filter_by(name = i.name).first()
            log = logging.query.filter_by(uid = u.uid,tid = tuu.tid).all()
            if log:
                now = datetime.now()
                k.append(timeago.format(datetime.strptime(log[-1].logtime,'%d-%m-%Y %H:%M:%S'),now))
                
            else:
                k.append("No Logs yet")
        return render_template('dashboard.html',username = username,tracker = tu,k=k)

@app.route('/<username>/newtracker',methods=['GET', 'POST'])
def newtrack(username):
    if request.method=="GET":
        return render_template('addtracker.html',username = username)
    if request.method == "POST":
        u = user.query.filter_by(username = username).first()
        nt = tracker(request.form["tname"],request.form["tdes"],request.form["ttype"],str(request.form["settings"]),u.uid)
        db.session.add(nt)
        db.session.commit()
        return redirect("/{}/dashboard".format(u.username))

@app.route('/<username>/<tname>/newlog',methods=['GET', 'POST'])
def addlog(username,tname):
    if request.method=="GET":
        uu = user.query.filter_by(username=username).first()
        tu = tracker.query.filter_by(name = tname,uid = uu.uid).first()
        return render_template('addlog.html',username = username,tracker = tu,choices = str(tu.settings).split(','))
    if request.method=="POST":
        uu = user.query.filter_by(username=username).first()
        tu = tracker.query.filter_by(name = tname,uid = uu.uid).first()
        now = datetime.now()
        dt_string = now.strftime("%d-%m-%Y %H:%M:%S")
        nl = logging(tu.tid,uu.uid,request.form["value"],request.form["notes"],dt_string,request.form["date"])
        db.session.add(nl)
        db.session.commit()
        return redirect("/{}/{}".format(uu.username,tname))


@app.route('/<username>/<tname>',methods=['GET', 'POST'])
def viewlog(username,tname):
    if request.method=="GET":
        uu = user.query.filter_by(username=username).first()
        tu = tracker.query.filter_by(name = tname,uid = uu.uid).first()
        logg = logging.query.filter_by(uid = uu.uid,tid = tu.tid).all()
        if logg:
            dat = [(datetime.strptime(i.datetime,'%Y-%m-%dT%H:%M')) for i in logg]
            val = [(int(i.value) if (i.value).isdigit() else i.value) for i in logg]
            dat,val = zip(*sorted(zip(dat, val)))
            dat = [i.strftime("%Y-%m-%d %H:%M:%S")  for i in dat]
            plt.plot(dat,val)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('./static/images/tracktrend.png')
            plt.close()
        return render_template('track_info.html',username = username,tracker = tname,loggin = logg,tdat = tu)

@app.route('/<username>/<tname>/delete',methods=['GET'])
def deltrack(username,tname):
    if request.method=="GET":
        uu = user.query.filter_by(username = username).first()
        tu = tracker.query.filter_by(uid=uu.uid,name=tname).first()
        db.session.delete(tu)
        db.session.commit()
        return redirect('/{}/dashboard'.format(username))

@app.route('/<username>/<tname>/update',methods=['GET','POST'])
def uptrack(username,tname):
    if request.method=="GET":
        uu = user.query.filter_by(username = username).first()
        tu = tracker.query.filter_by(uid=uu.uid,name=tname).first()
        return render_template('update.html',username = username,tracker = tu,x=1)
    if request.method=="POST":
        uu = user.query.filter_by(username = username).first()
        tu = tracker.query.filter_by(uid=uu.uid,name=tname).first()
        tu.name = request.form["tname"]
        tu.description = request.form["tdes"]    
        db.session.commit()
        return redirect('/{}/dashboard'.format(username))

@app.route('/<username>/<tname>/<lt>/delete',methods=['GET'])
def dellog(username,tname,lt):
    if request.method=="GET":
        uu = user.query.filter_by(username = username).first()
        tu = tracker.query.filter_by(uid=uu.uid,name=tname).first()
        lu = logging.query.filter_by(uid = uu.uid,tid=tu.tid,logtime = lt).first()
        db.session.delete(lu)
        db.session.commit()
        return redirect('/{}/{}'.format(username,tname))

@app.route('/<username>/<tname>/<lt>/update',methods=['GET','POST'])
def uplog(username,tname,lt):
    if request.method=="GET":
        uu = user.query.filter_by(username = username).first()
        tu = tracker.query.filter_by(uid=uu.uid,name=tname).first()
        lu = logging.query.filter_by(uid = uu.uid,tid=tu.tid,logtime = lt).first()
        return render_template('update.html',username = username,tracker = tu,x=2,log = lu)
    if request.method=="POST":
        uu = user.query.filter_by(username = username).first()
        tu = tracker.query.filter_by(uid=uu.uid,name=tname).first()
        lu = logging.query.filter_by(uid = uu.uid,tid=tu.tid,logtime = lt).first()
        lu.datetime = request.form["date"] 
        lu.value = request.form["value"]
        lu.note = request.form["notes"]
        now = datetime.now()
        dt_string = now.strftime("%d-%m-%Y %H:%M:%S")
        lu.logtime = dt_string
        db.session.commit()
        return redirect('/{}/{}'.format(username,tname))

if __name__ == '__main__':
    app.run(host = "0.0.0.0",
            port = 5000)