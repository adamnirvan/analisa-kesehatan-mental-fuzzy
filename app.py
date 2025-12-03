import mysql.connector

from datetime import datetime
from flask import Flask, render_template, request

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  
        database="mental_test"
    )



app = Flask(__name__)


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nama VARCHAR(100),
            usia INT,
            jk VARCHAR(20),
            anxiety INT,
            depression INT,
            stress INT,
            anxiety_res VARCHAR(20),
            depression_res VARCHAR(20),
            stress_res VARCHAR(20),
            final_result VARCHAR(50),
            created_at DATETIME
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
init_db()




# ============================================
# DOMAIN MAPPING (PERTANYAAN → DOMAIN)
# ============================================
DOMAIN_MAP = {
    1: "stress",
    2: "anxiety",
    3: "depression",
    4: "stress",
    5: "depression",
    6: "stress",
    7: "anxiety",
    8: "stress",
    9: "depression",
    10: "depression"
}


# ============================================
# FUZZY MEMBERSHIP FUNCTIONS
# Semua domain memakai skala 0–20
# ============================================
def fuzzy_low(x):
    if x <= 6:
        return 1
    elif 6 < x <= 10:
        return (10 - x) / 4
    return 0


def fuzzy_medium(x):
    if 6 < x < 10:
        return (x - 6) / 4
    elif 10 <= x <= 14:
        return 1
    elif 14 < x < 18:
        return (18 - x) / 4
    return 0


def fuzzy_high(x):
    if x >= 18:
        return 1
    elif 14 <= x < 18:
        return (x - 14) / 4
    return 0


# ============================================
# FUZZY EVALUATION PER DOMAIN
# ============================================
def evaluate_domain(score):
    low = fuzzy_low(score)
    medium = fuzzy_medium(score)
    high = fuzzy_high(score)

    if high >= max(low, medium):
        return "tinggi"
    elif medium >= max(low, high):
        return "sedang"
    else:
        return "rendah"


# ============================================
# FINAL INFERENCE
# ============================================
def final_conclusion(a, d, s):
    domain_values = [a, d, s]

    high_count = domain_values.count("tinggi")
    medium_count = domain_values.count("sedang")

    if high_count >= 2:
        return "Risiko Tinggi"
    if medium_count >= 2 or (high_count == 1 and medium_count == 1):
        return "Perlu Perhatian"
    return "Sehat"


# ============================================
# ROUTES
# ============================================
@app.route("/")
def index():
    return render_template("form.html")


@app.route("/submit", methods=["POST"])
def submit():
    nama = request.form.get("nama")
    usia = request.form.get("usia")
    jk = request.form.get("jk")

    answers = {}
    domain_scores = {"anxiety": 0, "depression": 0, "stress": 0}

    # Ambil nilai tiap pertanyaan
    for i in range(1, 11):
        val = int(request.form.get(f"q{i}"))
        domain = DOMAIN_MAP[i]
        domain_scores[domain] += val

    # Fuzzy evaluation
    anxiety_result = evaluate_domain(domain_scores["anxiety"])
    depression_result = evaluate_domain(domain_scores["depression"])
    stress_result = evaluate_domain(domain_scores["stress"])

    final = final_conclusion(anxiety_result, depression_result, stress_result)

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO results 
        (nama, usia, jk, anxiety, depression, stress, anxiety_res, depression_res, stress_res, final_result, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        nama,
        usia,
        jk,
        domain_scores["anxiety"],
        domain_scores["depression"],
        domain_scores["stress"],
        anxiety_result,
        depression_result,
        stress_result,
        final,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    db.commit()
    cursor.close()
    db.close()


    return render_template(
        "result.html",
        nama=nama,
        usia=usia,
        jk=jk,
        anxiety=domain_scores["anxiety"],
        depression=domain_scores["depression"],
        stress=domain_scores["stress"],
        a_res=anxiety_result,
        d_res=depression_result,
        s_res=stress_result,
        conclusion=final
    )




if __name__ == "__main__":
    app.run(debug=True)
