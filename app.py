from flask import Flask, render_template, request
from db_config import get_db_connection

app = Flask(__name__)

# Emission factors
transport_factors = {
    "car": 0.192,
    "bus": 0.105,
    "bike": 0.103
}

@app.route("/")
def home():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM footprint_data ORDER BY id DESC LIMIT 5")
    history = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("index.html", history=history)


@app.route("/calculate", methods=["POST"])
def calculate():

    region = request.form["region"]
    transport = request.form["transport"]
    distance = float(request.form["distance"])
    electricity = float(request.form["electricity"])
    fuel = float(request.form["fuel"])

    # Calculate emissions
    transport_emission = distance * transport_factors[transport]
    electricity_emission = electricity * 0.82
    fuel_emission = fuel * 2.31

    total_emission = transport_emission + electricity_emission + fuel_emission

    # Classification
    if total_emission < 100:
        category = "Low"
        recommendation = "Maintain eco-friendly habits and consider renewable energy."
        score = 90
    elif total_emission < 300:
        category = "Medium"
        recommendation = "Reduce electricity consumption and try public transport."
        score = 60
    else:
        category = "High"
        recommendation = "Reduce fuel usage, shift to renewable energy, and prefer public transport."
        score = 30

    # AI-style output
    ai_output = f"{region} → Sustainability Risk: {category} → Recommendation Generated"

    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """INSERT INTO footprint_data
    (transport_type,distance,electricity,fuel,total_emission,category,recommendation)
    VALUES (%s,%s,%s,%s,%s,%s,%s)"""

    values = (transport,distance,electricity,fuel,total_emission,category,recommendation)

    cursor.execute(sql,values)
    conn.commit()

    cursor.execute("SELECT * FROM footprint_data ORDER BY id DESC LIMIT 5")
    history = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "index.html",
        emission=round(total_emission,2),
        category=category,
        recommendation=recommendation,
        ai_output=ai_output,
        score=score,
        transport_emission=round(transport_emission,2),
        electricity_emission=round(electricity_emission,2),
        fuel_emission=round(fuel_emission,2),
        history=history
    )


if __name__ == "__main__":
    app.run(debug=True)