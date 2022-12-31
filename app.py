from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import cv2
from helpers import apology, login_required
import base64
import numpy as np
import face_recognition

# Configure Flask application
app = Flask(__name__)

# Connect Database
conn1 = sqlite3.connect('attendance.db')
db1 = conn1.cursor()

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.after_request
def after_request(response):
    # Ensure responses aren't cached
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response
    
# Index route
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        conn1 = sqlite3.connect('attendance.db')
        db1 = conn1.cursor()
        db1.execute("SELECT * FROM attendance WHERE id in (SELECT student_id FROM students WHERE class_id in (SELECT class_id FROM classes WHERE teacher in (SELECT teacher_id FROM teachers WHERE teacher_id=?))) AND date=?",[session["user_id"],request.form.get("date")])
        data = db1.fetchall()
        attendance = []
        for i in data:
            record = []
            student_id = i[2]
            db1.execute("SELECT name FROM students WHERE student_id = ?",[student_id])
            name = db1.fetchall()
            record.append(name[0][0])
            record.append(i[0])
            record.append(i[1])
            attendance.append(record)
        return render_template("view.html", attendance=attendance)

    else:
        conn1 = sqlite3.connect('attendance.db')
        db1 = conn1.cursor()
        db1.execute("SELECT date FROM attendance WHERE id in (SELECT student_id FROM students WHERE class_id in (SELECT class_id FROM classes WHERE teacher in (SELECT teacher_id FROM teachers WHERE teacher_id=?)))", [session["user_id"]])
        dates = []
        data = db1.fetchall()
        for i in data:
            date = i[0]
            if date not in dates:
                dates.append(date)
        return render_template("index.html", dates=dates)

# Logout route
@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Successfully Logged Out")
    return redirect("/")

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        conn1 = sqlite3.connect('attendance.db')
        db1 = conn1.cursor()
        db1.execute("SELECT * FROM teachers WHERE teacher = ?", [request.form.get("username")])
        # Ensure username exists and password is correct
        rows = db1.fetchall()
        for row in rows:
            if not row[1] or not check_password_hash(row[2], request.form.get("password")):
                return apology("invalid username and/or password", 403)
        # Remember which user has logged in
        for row in rows:
            session["user_id"] = row[0]

        message = "Successfully Logged In. Your teacher ID is " + str(session["user_id"])
        flash(message)

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


# Register route
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Register User if POST is used:
    if request.method == "POST":
        # Ensure Username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure class was submitted
        if not request.form.get("class"):
            return apology("must provide class", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Validating password
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords do not match", 400)

        # Register user into database
        hash = generate_password_hash(request.form.get("password"))
        conn1 = sqlite3.connect('attendance.db')
        db1 = conn1.cursor()
        db1.execute("INSERT INTO teachers (teacher, hash_password) VALUES (?,?)", [request.form.get("username"), hash])
        conn1.commit()
        db1.execute("SELECT MAX(teacher_id) FROM teachers")
        teacherid = db1.fetchall()
        db1.execute("INSERT INTO classes (class,teacher) VALUES (?,?)",[request.form.get("class"),teacherid[0][0]])
        conn1.commit()
        flash("Succesfully Registered!")
        return redirect(url_for("login"))
    else:
        return render_template("register.html")

# Route to register a new student into the database
@app.route("/registerstudent", methods=["GET", "POST"])
@login_required
def registerstudent():
    if request.method == "POST":
        conn1 = sqlite3.connect('attendance.db')
        db1 = conn1.cursor()
        if not request.form.get("name"):
            return apology("must provide name", 400)
        name = request.form.get("name")
        db1.execute("SELECT class_id FROM classes WHERE teacher = ?",[session["user_id"]])
        a = db1.fetchall()
        class1 = a[0][0]
        db1.execute("INSERT INTO students (name,class_id) VALUES (?,?)",[name,class1])
        conn1.commit()
        db1.execute("SELECT MAX(student_id) FROM students WHERE name=?",[request.form.get("name")])
        a = db1.fetchall()
        session["latest_student"] = a[0][0]
        flash("success")
        return render_template("registerstudentimage.html")
    else:
        return render_template("registerstudent.html")

# Route to register new student's image into the database after entering name
@app.route("/registerstudentimage", methods=["GET", "POST"])
@login_required
def registerstudentimage():
    if request.method == "POST":
        # Setting up connection
        conn1 = sqlite3.connect('attendance.db')
        db1 = conn1.cursor()
        
        # Retrieving base64 png image from https packet and converting into cv2 readable
        image1 = request.json['imageData']
        b64_string = base64.b64decode(image1)
        im_arr = np.frombuffer(b64_string, dtype=np.uint8)
        img = cv2.imdecode(im_arr, flags=cv2.IMREAD_COLOR)

        # Generating face encodings
        rgb_img2 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        cv2.imwrite("test.jpeg", rgb_img2)
        x = cv2.imread("test.jpeg")
        img2_encoding = face_recognition.face_encodings(rgb_img2)
        face_detected = True

        # Check if face detected in image
        if len(img2_encoding) == 0:
            face_detected = False

        if (face_detected):
            a, im_buf_arr = cv2.imencode('.jpeg', x)
            array = np.array(im_buf_arr)
            upload =  array.tobytes()
            db1.execute("INSERT INTO images VALUES (?,?)", [session["latest_student"],upload])
            conn1.commit()
            flash("Successfully Registered!")
            img2_encoding.clear()
            return jsonify(status="success")
        else:
            flash("Registration Unsuccessful! No Face Detected. Please try again.")
            db1.execute("DELETE FROM students WHERE student_id = ?", [session["latest_student"]])
            conn1.commit()
            return jsonify(status="failed")
    else:
        return jsonify(status="failed")