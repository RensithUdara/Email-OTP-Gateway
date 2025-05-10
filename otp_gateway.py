from flask import Flask, request, jsonify
import random
import smtplib
from email.message import EmailMessage
import time

app = Flask(__name__)

# In-memory OTP store: {email: (otp, timestamp)}
otp_store = {}

# Configuration
SENDER_EMAIL = "your@gmail.com"
SENDER_PASSWORD = "your_app_password"  # Use App Password if using Gmail
OTP_EXPIRY_SECONDS = 300  # 5 minutes

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(to_email, otp):
    msg = EmailMessage()
    msg.set_content(f"Your OTP code is: {otp}")
    msg['Subject'] = 'Your OTP Code'
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.send_message(msg)

@app.route("/send-otp", methods=["POST"])
def send_otp():
    data = request.json
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    otp = generate_otp()
    timestamp = int(time.time())

    try:
        send_otp_email(email, otp)
        otp_store[email] = (otp, timestamp)
        return jsonify({"message": "OTP sent successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.json
    email = data.get("email")
    user_otp = data.get("otp")

    if not email or not user_otp:
        return jsonify({"error": "Email and OTP are required"}), 400

    record = otp_store.get(email)

    if not record:
        return jsonify({"error": "No OTP found for this email"}), 404

    stored_otp, timestamp = record
    current_time = int(time.time())

    if current_time - timestamp > OTP_EXPIRY_SECONDS:
        del otp_store[email]
        return jsonify({"error": "OTP expired"}), 400

    if user_otp != stored_otp:
        return jsonify({"error": "Invalid OTP"}), 401

    del otp_store[email]
    return jsonify({"message": "OTP verified successfully!"}), 200

if __name__ == "__main__":
    app.run(debug=True)
