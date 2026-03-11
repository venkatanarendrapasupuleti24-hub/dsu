from flask import Flask, render_template, request, redirect, session
from db_config import get_db_connection
import random

app = Flask(__name__)
app.secret_key = "carbon_secret"


transport_factors = {
    "car":0.192,
    "bus":0.105,
    "bike":0.103
}

# ---------------- HOME ----------------

@app.route("/")
def home():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM footprint_data
    WHERE user_id=%s
    ORDER BY id DESC LIMIT 5
    """,(session["user_id"],))

    history = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("index.html",history=history)


# ---------------- SIGNUP PAGE ----------------

@app.route("/signup")
def signup():
    return render_template("signup.html")


# ---------------- MOBILE SIGNUP ----------------

@app.route("/signup_mobile",methods=["POST"])
def signup_mobile():

    name=request.form["name"]
    mobile=request.form["mobile"]
    password=request.form["password"]

    otp=str(random.randint(100000,999999))

    conn=get_db_connection()
    cursor=conn.cursor()

    cursor.execute(
    "INSERT INTO otp_verification(mobile,otp) VALUES(%s,%s)",
    (mobile,otp)
    )

    conn.commit()

    session["signup_name"]=name
    session["signup_mobile"]=mobile
    session["signup_password"]=password

    print("OTP:",otp)

    return render_template("verify_otp.html")


# ---------------- VERIFY OTP ----------------

@app.route("/verify_otp",methods=["POST"])
def verify_otp():

    entered_otp=request.form["otp"]
    mobile=session["signup_mobile"]

    conn=get_db_connection()
    cursor=conn.cursor()

    cursor.execute(
    "SELECT otp FROM otp_verification WHERE mobile=%s ORDER BY id DESC LIMIT 1",
    (mobile,)
    )

    db_otp=cursor.fetchone()[0]

    if entered_otp==db_otp:

        cursor.execute("""
        INSERT INTO users(name,mobile,password,signup_method)
        VALUES(%s,%s,%s,'mobile')
        """,
        (
        session["signup_name"],
        mobile,
        session["signup_password"]
        ))

        conn.commit()

        return redirect("/login")

    return "Invalid OTP"


# ---------------- LOGIN PAGE ----------------

@app.route("/login")
def login():
    return render_template("login.html")


# ---------------- LOGIN PROCESS ----------------

@app.route("/login_user",methods=["POST"])
def login_user():

    mobile=request.form["mobile"]
    password=request.form["password"]

    conn=get_db_connection()
    cursor=conn.cursor()

    cursor.execute(
    "SELECT * FROM users WHERE mobile=%s AND password=%s",
    (mobile,password)
    )

    user=cursor.fetchone()

    if user:

        session["user_id"]=user[0]

        cursor.execute("""
        INSERT INTO login_history(user_id,login_method)
        VALUES(%s,'mobile')
        """,(user[0],))

        conn.commit()

        return redirect("/")

    return "Invalid login"


# ---------------- CALCULATE ----------------

@app.route("/calculate",methods=["POST"])
def calculate():

    region=request.form["region"]
    transport=request.form["transport"]
    distance=float(request.form["distance"])
    electricity=float(request.form["electricity"])
    fuel=float(request.form["fuel"])

    transport_emission=distance*transport_factors[transport]
    electricity_emission=electricity*0.82
    fuel_emission=fuel*2.31

    total_emission=transport_emission+electricity_emission+fuel_emission

    if total_emission<100:
        category="Low"
        recommendation="Maintain eco-friendly habits"
        score=90
    elif total_emission<300:
        category="Medium"
        recommendation="Reduce electricity usage"
        score=60
    else:
        category="High"
        recommendation="Use renewable energy"
        score=30


    conn=get_db_connection()
    cursor=conn.cursor()

    cursor.execute("""
    INSERT INTO footprint_data
    (user_id,transport_type,distance,electricity,fuel,total_emission,category,recommendation)
    VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
    """,
    (
    session["user_id"],
    transport,
    distance,
    electricity,
    fuel,
    total_emission,
    category,
    recommendation
    ))

    conn.commit()

    cursor.execute("""
    SELECT * FROM footprint_data
    WHERE user_id=%s
    ORDER BY id DESC LIMIT 5
    """,(session["user_id"],))

    history=cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "index.html",
        emission=round(total_emission,2),
        category=category,
        recommendation=recommendation,
        score=score,
        transport_emission=round(transport_emission,2),
        electricity_emission=round(electricity_emission,2),
        fuel_emission=round(fuel_emission,2),
        history=history
    )


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__=="__main__":
    app.run(debug=True)