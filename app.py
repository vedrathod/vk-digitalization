from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os

app=Flask(__name__)
app.config["SECRET_KEY"]="CHANGE_THIS_SECRET_KEY"
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///"+os.path.join(os.path.dirname(__file__),"vk_digitalization.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False
db=SQLAlchemy(app)

class User(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(120),nullable=False)
    email=db.Column(db.String(160),unique=True,nullable=False)
    password_hash=db.Column(db.String(255),nullable=False)
    role=db.Column(db.String(20),default="customer",nullable=False)
    created_at=db.Column(db.DateTime,default=datetime.utcnow)
    submissions=db.relationship("CustomerDetail",backref="customer",lazy=True)
    def set_password(self,p): self.password_hash=generate_password_hash(p)
    def check_password(self,p): return check_password_hash(self.password_hash,p)

class CustomerDetail(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    customer_id=db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False)
    company_name=db.Column(db.String(160),nullable=False)
    phone=db.Column(db.String(50))
    service=db.Column(db.String(120))
    project_title=db.Column(db.String(200))
    message=db.Column(db.Text,nullable=False)
    status=db.Column(db.String(30),default="New")
    owner_note=db.Column(db.Text,default="")
    created_at=db.Column(db.DateTime,default=datetime.utcnow)

COMPANY={"name":"VK Digitalization","email":"vkdigitalization@gmail.com","phone":"+91 7698697002 , +91 9081716160 ","location":"Ahmedabad, Gujarat, India"}
SERVICES=["Document Digitization","Data Processing","Scanning & OCR","Digital Record Management","Quality Checking","Project Operations"]

def login_required(f):
    @wraps(f)
    def w(*a,**kw):
        if "user_id" not in session: flash("Please login first.","error"); return redirect(url_for("login"))
        return f(*a,**kw)
    return w

def owner_required(f):
    @wraps(f)
    def w(*a,**kw):
        if session.get("role")!="owner": flash("Owner access only.","error"); return redirect(url_for("dashboard"))
        return f(*a,**kw)
    return w

@app.context_processor
def ctx(): return {"current_user":session.get("user_name"),"current_role":session.get("role")}

@app.route("/")
def home(): return render_template("index.html",company=COMPANY,services=SERVICES)

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=User.query.filter_by(email=request.form["email"].strip().lower()).first()
        if u and u.check_password(request.form["password"]):
            session.clear(); session.update(user_id=u.id,user_name=u.name,role=u.role)
            return redirect(url_for("owner_dashboard" if u.role=="owner" else "dashboard"))
        flash("Invalid email or password.","error")
    return render_template("login.html",company=COMPANY)

@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        name=request.form["name"].strip(); email=request.form["email"].strip().lower()
        p=request.form["password"]; cp=request.form["confirm_password"]
        if not name or not email or not p: flash("Fill all required fields.","error")
        elif len(p)<6: flash("Password must be at least 6 characters.","error")
        elif p!=cp: flash("Passwords do not match.","error")
        elif User.query.filter_by(email=email).first(): flash("Email already registered.","error")
        else:
            u=User(name=name,email=email,role="customer"); u.set_password(p); db.session.add(u); db.session.commit()
            flash("Account created. Please login.","success"); return redirect(url_for("login"))
    return render_template("register.html",company=COMPANY)

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    u=db.session.get(User,session["user_id"])
    return render_template("dashboard.html",company=COMPANY,user=u,details=CustomerDetail.query.filter_by(customer_id=u.id).order_by(CustomerDetail.created_at.desc()).all())

@app.route("/submit-details",methods=["GET","POST"])
@login_required
def submit_details():
    if session.get("role")=="owner": return redirect(url_for("owner_dashboard"))
    if request.method=="POST":
        if not request.form["company_name"].strip() or not request.form["message"].strip():
            flash("Company name and details are required.","error")
        else:
            d=CustomerDetail(customer_id=session["user_id"],company_name=request.form["company_name"].strip(),phone=request.form["phone"].strip(),service=request.form["service"],project_title=request.form["project_title"].strip(),message=request.form["message"].strip())
            db.session.add(d); db.session.commit(); flash("Details submitted successfully.","success"); return redirect(url_for("dashboard"))
    return render_template("submit_details.html",company=COMPANY,services=SERVICES)

@app.route("/owner")
@login_required
@owner_required
def owner_dashboard():
    return render_template("owner_dashboard.html",company=COMPANY,customers=User.query.filter_by(role="customer").all(),submissions=CustomerDetail.query.order_by(CustomerDetail.created_at.desc()).all())

@app.route("/owner/submission/<int:i>/update",methods=["POST"])
@login_required
@owner_required
def update_submission(i):
    d=db.session.get(CustomerDetail,i)
    if not d: flash("Submission not found.","error")
    else:
        d.status=request.form["status"] if request.form["status"] in ["New","In Progress","Completed","Closed"] else "New"
        d.owner_note=request.form["owner_note"].strip(); db.session.commit(); flash("Updated.","success")
    return redirect(url_for("owner_dashboard"))

def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email="owner@vkdigitalization.com").first():
            u=User(name="VK Owner",email="owner@vkdigitalization.com",role="owner")
            u.set_password("VKOwner@123"); db.session.add(u); db.session.commit()

init_db()

if __name__=="__main__": app.run(debug=True,host="127.0.0.1",port=5000)
