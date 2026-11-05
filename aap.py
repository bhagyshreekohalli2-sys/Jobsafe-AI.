from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)

def create_database():
    conn = sqlite3.connect("jobsafe.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_text TEXT,
            risk_score INTEGER,
            result TEXT,
            date TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.route("/")
def home():
    return jsonify({
        "message": "JobSafe AI Backend is Running!"
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/api/analyze", methods=["POST"])
def analyze():

    data = request.get_json()

    job_text = data.get("job_text", "").strip()
    job_url = data.get("job_url", "").strip()

    if not job_text and not job_url:
        return jsonify({"error": "Enter job details"}), 400

    content = (job_text + " " + job_url).lower()

    patterns = [
        (r"registration fee|processing fee|training fee|security deposit|pay to apply",
         "Possible registration or payment fee"),
        (r"guaranteed income|easy money|unlimited earnings",
         "Unrealistic income promise"),
        (r"urgent|no interview|limited slots|immediate joining",
         "Urgent hiring pressure"),
        (r"\botp\b|upi pin|bank password|cvv",
         "Sensitive financial information requested"),
        (r"whatsapp only|telegram only|gmail\.com|yahoo\.com",
         "Contact details need verification"),
        (r"crypto payment|buy gift card|refundable fee",
         "Suspicious payment method")
    ]

    flags = []

    for pattern, message in patterns:
        if re.search(pattern, content):
            flags.append(message)

    if not re.search(
        r"responsibilit|qualification|requirement|skills|duties",
        content
    ):
        flags.append("Job details are incomplete")

    score = min(95, 8 + len(flags) * 16)

    if score >= 55:
        result = "High Risk"
    elif score >= 30:
        result = "Needs Review"
    else:
        result = "Fewer Warning Signs"

    create_database()

    conn = sqlite3.connect("jobsafe.db")
    conn.execute(
        """INSERT INTO history
        (job_text, risk_score, result, date)
        VALUES (?, ?, ?, ?)""",
        (job_text[:5000], score, result,
         datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    return jsonify({
        "risk_score": score,
        "result": result,
        "warning_signs": flags,
        "message": "Analysis completed successfully",
        "disclaimer": "This is a rule-based prototype, not a trained AI model."
    })

if __name__ == "__main__":
    create_database()
    app.run(debug=False)
