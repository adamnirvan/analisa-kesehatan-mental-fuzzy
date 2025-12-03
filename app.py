import mysql.connector
from datetime import datetime
from flask import Flask, render_template, request, redirect

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="mental_test"
    )

app = Flask(__name__)


def init_db():
    db = get_db()
    cur = db.cursor()

    # results table
    cur.execute("""
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

    # questions table 
    cur.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            question_text VARCHAR(255) NOT NULL,
            domain VARCHAR(20) NOT NULL
        )
    """)

    # rules table 
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category VARCHAR(50) NOT NULL,
            min_value INT NOT NULL,
            max_value INT NOT NULL,
            result_label VARCHAR(100) NOT NULL
        )
    """)

    db.commit()
    cur.close()
    db.close()


init_db()

#get label from rules
def get_label_from_rules(db, category, score):
    cur = db.cursor()

    cur.execute("""
        SELECT result_label FROM rules
        WHERE category = %s
        AND %s BETWEEN min_value AND max_value
        LIMIT 1
    """, (category, score))

    row = cur.fetchone()
    cur.close()

    if row:
        return row[0]
    return "tidak terdefinisi"  # jika rule tidak ditemukan



def final_conclusion(a, d, s):
    domain_vals = [a, d, s]
    high = domain_vals.count("tinggi")
    medium = domain_vals.count("sedang")

    if high >= 2:
        return "Risiko Tinggi"
    if medium >= 2 or (high == 1 and medium == 1):
        return "Perlu Perhatian"
    return "Sehat"



#ROUTE: FORM

@app.route("/")
def index():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM questions ORDER BY id")
    questions = cur.fetchall()

    cur.close()
    db.close()

    return render_template("form.html", questions=questions)



# ROUTE: SUBMIT
@app.route("/submit", methods=["POST"])
def submit():
    nama = request.form.get("nama")
    usia = request.form.get("usia")
    jk = request.form.get("jk")

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Ambil semua pertanyaan + domain-nya
    cur.execute("SELECT id, domain FROM questions ORDER BY id")
    questions = cur.fetchall()

    # Hitung skor per-domain
    domain_scores = {}

    for q in questions:
        domain_scores.setdefault(q["domain"], 0)

        nilai = int(request.form.get(f"q{q['id']}"))
        domain_scores[q["domain"]] += nilai

    # memastikan domain utama selalu ada
    anxiety_score = domain_scores.get("anxiety", 0)
    depression_score = domain_scores.get("depression", 0)
    stress_score = domain_scores.get("stress", 0)

    # Ambil label fuzzy dari rules table
    anxiety_result = get_label_from_rules(db, "anxiety", anxiety_score)
    depression_result = get_label_from_rules(db, "depression", depression_score)
    stress_result = get_label_from_rules(db, "stress", stress_score)

    final = final_conclusion(anxiety_result, depression_result, stress_result)

    # Save survey result
    save = db.cursor()
    save.execute("""
        INSERT INTO results
        (nama, usia, jk, anxiety, depression, stress, anxiety_res, depression_res, stress_res, final_result, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        nama,
        usia,
        jk,
        anxiety_score,
        depression_score,
        stress_score,
        anxiety_result,
        depression_result,
        stress_result,
        final,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    ))

    db.commit()
    save.close()
    cur.close()
    db.close()

    return render_template(
        "result.html",
        nama=nama,
        usia=usia,
        jk=jk,
        anxiety=anxiety_score,
        depression=depression_score,
        stress=stress_score,
        a_res=anxiety_result,
        d_res=depression_result,
        s_res=stress_result,
        conclusion=final
    )


if __name__ == "__main__":
    app.run(debug=True)
